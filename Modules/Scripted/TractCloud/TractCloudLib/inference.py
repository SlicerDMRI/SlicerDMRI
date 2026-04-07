"""TractCloud inference pipeline.

Provides feature extraction, neighbor computation, dataset creation, and
model inference for tractography parcellation.

Adapted from https://github.com/SlicerDMRI/TractCloud
"""

import json
import logging
import os
import tarfile
import time
import urllib.request

import numpy as np
import vtk
import torch
import torch.utils.data as data

from .models import TractDGCNN, PointNetCls
from .tract_mapping import TRACT_NAMES, cluster2tract_label

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model data management
# ---------------------------------------------------------------------------

_GITHUB_RELEASE = "https://github.com/SlicerDMRI/TractCloud/releases/download/v1.0.0"
_MODEL_ARCHIVE = "TrainedModel.tar.gz"
_TRAIN_DATA_ARCHIVE = "TrainData_800clu800ol.tar.gz"


def _dataDir():
    """Return the directory where TractCloud model data is stored."""
    import slicer
    dataDir = os.path.join(
        slicer.app.cachePath, "TractCloud"
    )
    os.makedirs(dataDir, exist_ok=True)
    return dataDir


def _downloadFile(url, destPath, progressCallback=None):
    """Download a file with optional progress reporting."""
    def _reporthook(blocknum, blocksize, totalsize):
        if progressCallback and totalsize > 0:
            fraction = min(blocknum * blocksize / totalsize, 1.0)
            progressCallback(fraction)
    urllib.request.urlretrieve(url, destPath, reporthook=_reporthook)


def ensureModelData(progressCallback=None):
    """Download and extract model weights and atlas data if not present.

    Returns:
        tuple: (weightPath, massCenter) where weightPath is the path to the
            model .pth file and massCenter is the (15, 3) HCP atlas center array.
    """
    dataDir = _dataDir()

    # Trained model
    modelDir = os.path.join(dataDir, "TrainedModel")
    weightPath = os.path.join(modelDir, "best_tract_f1_model.pth")
    argsPath = os.path.join(modelDir, "cli_args.txt")

    if not os.path.exists(weightPath):
        logger.info("Downloading TractCloud trained model...")
        archivePath = os.path.join(dataDir, _MODEL_ARCHIVE)
        _downloadFile(f"{_GITHUB_RELEASE}/{_MODEL_ARCHIVE}", archivePath,
                      progressCallback)
        with tarfile.open(archivePath, "r:gz") as tar:
            tar.extractall(path=dataDir)
        os.remove(archivePath)
        logger.info(f"Model extracted to {modelDir}")

    # HCP mass center (needed for re-centering)
    massCenterPath = os.path.join(dataDir, "TrainData_800clu800ol",
                                  "HCP_mass_center.npy")
    if not os.path.exists(massCenterPath):
        logger.info("Downloading HCP atlas data (for mass center)...")
        archivePath = os.path.join(dataDir, _TRAIN_DATA_ARCHIVE)
        _downloadFile(f"{_GITHUB_RELEASE}/{_TRAIN_DATA_ARCHIVE}", archivePath,
                      progressCallback)
        with tarfile.open(archivePath, "r:gz") as tar:
            # Only extract the mass center file to save space
            members = [m for m in tar.getmembers()
                       if "HCP_mass_center.npy" in m.name]
            if members:
                tar.extractall(path=dataDir, members=members)
            else:
                # Fall back to full extraction
                tar.extractall(path=dataDir)
        os.remove(archivePath)
        logger.info(f"Atlas data extracted")

    massCenter = np.load(massCenterPath)
    return weightPath, argsPath, massCenter


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extractRASFeatures(polyData, numPoints=15):
    """Extract RAS coordinate features from VTK polydata.

    Resamples each streamline to a fixed number of equally-spaced points
    and returns RAS coordinates. Vectorized VTK/numpy implementation.

    Args:
        polyData: vtkPolyData with lines (streamlines)
        numPoints: number of points to resample each streamline to

    Returns:
        feat: array of shape (num_fibers, numPoints, 3)
    """
    from vtk.util.numpy_support import vtk_to_numpy

    numFibers = polyData.GetNumberOfLines()
    allPoints = vtk_to_numpy(polyData.GetPoints().GetData())  # (totalPts, 3)

    # Build offsets and lengths arrays from cell array
    cellArray = polyData.GetLines()
    if hasattr(cellArray, 'GetOffsetsArray') and cellArray.GetOffsetsArray():
        offsets = vtk_to_numpy(cellArray.GetOffsetsArray())
        lengths = np.diff(offsets)
    else:
        # Legacy cell array format: traverse to build offsets/lengths
        lengths = np.zeros(numFibers, dtype=np.int64)
        offsets = np.zeros(numFibers, dtype=np.int64)
        cellArray.InitTraversal()
        ptIds = vtk.vtkIdList()
        cumOffset = 0
        for i in range(numFibers):
            cellArray.GetNextCell(ptIds)
            n = ptIds.GetNumberOfIds()
            lengths[i] = n
            offsets[i] = ptIds.GetId(0) if n > 0 else 0

    # Build connectivity array (point indices per cell)
    if hasattr(cellArray, 'GetConnectivityArray') and cellArray.GetConnectivityArray():
        connectivity = vtk_to_numpy(cellArray.GetConnectivityArray())
    else:
        connectivity = None

    feat = np.zeros((numFibers, numPoints, 3), dtype=np.float64)

    # Group fibers by length for batch resampling
    uniqueLengths = np.unique(lengths)
    for nPts in uniqueLengths:
        if nPts < 2:
            continue
        fiberMask = (lengths == nPts)
        fiberIndices = np.where(fiberMask)[0]
        batchSize = len(fiberIndices)

        # Gather coordinates for all fibers of this length
        coords = np.zeros((batchSize, nPts, 3), dtype=np.float64)
        if connectivity is not None:
            if hasattr(cellArray, 'GetOffsetsArray') and cellArray.GetOffsetsArray():
                cellOffsets = vtk_to_numpy(cellArray.GetOffsetsArray())
                for bi, fi in enumerate(fiberIndices):
                    start = cellOffsets[fi]
                    ptIndices = connectivity[start:start + nPts]
                    coords[bi] = allPoints[ptIndices]
            else:
                for bi, fi in enumerate(fiberIndices):
                    coords[bi] = allPoints[offsets[fi]:offsets[fi] + nPts]
        else:
            ptIdList = vtk.vtkIdList()
            for bi, fi in enumerate(fiberIndices):
                polyData.GetCellPoints(fi, ptIdList)
                for j in range(nPts):
                    coords[bi, j] = allPoints[ptIdList.GetId(j)]

        # Vectorized arc-length resampling for the whole batch
        diffs = np.diff(coords, axis=1)  # (batch, nPts-1, 3)
        segLens = np.sqrt(np.sum(diffs ** 2, axis=2))  # (batch, nPts-1)
        cumLen = np.zeros((batchSize, nPts), dtype=np.float64)
        cumLen[:, 1:] = np.cumsum(segLens, axis=1)
        totalLen = cumLen[:, -1]  # (batch,)

        # Handle degenerate fibers
        degenerate = totalLen < 1e-12
        if np.any(degenerate):
            degIdx = fiberIndices[degenerate]
            feat[degIdx, :, :] = coords[degenerate, 0:1, :]

        valid = ~degenerate
        if not np.any(valid):
            continue

        validCoords = coords[valid]
        validCumLen = cumLen[valid]
        validTotalLen = totalLen[valid]
        validFiberIdx = fiberIndices[valid]
        nValid = validCoords.shape[0]

        # Target arc lengths: (nValid, numPoints)
        t = np.linspace(0, 1, numPoints)[None, :] * validTotalLen[:, None]

        # Batch interpolation: searchsorted per row, then vectorized lerp
        nValid = len(validFiberIdx)
        nSourcePts = validCoords.shape[1]
        idx = np.empty_like(t, dtype=np.intp)
        for bi in range(nValid):
            idx[bi] = np.searchsorted(validCumLen[bi], t[bi], side='right') - 1
        idx = np.clip(idx, 0, nSourcePts - 2)

        # Gather lower and upper cumulative lengths
        rowIdx = np.arange(nValid)[:, None]
        cumLo = validCumLen[rowIdx, idx]
        cumHi = validCumLen[rowIdx, idx + 1]
        segLen = cumHi - cumLo
        segLen = np.where(segLen < 1e-12, 1.0, segLen)
        frac = ((t - cumLo) / segLen)[:, :, None]  # (nValid, numPoints, 1)

        # Gather coordinates at lower and upper indices
        coordsLo = np.take_along_axis(
            validCoords, idx[:, :, None].repeat(3, axis=2), axis=1)
        coordsHi = np.take_along_axis(
            validCoords, (idx + 1)[:, :, None].repeat(3, axis=2), axis=1)

        # Linear interpolation
        resampled = coordsLo + frac * (coordsHi - coordsLo)
        feat[validFiberIdx] = resampled

    return feat


def centerTractography(feat, massCenter):
    """Re-center tractography features to match the HCP atlas center.

    Args:
        feat: (N_fiber, N_point, 3) RAS features
        massCenter: (N_point, 3) HCP atlas mass center

    Returns:
        centered features of same shape
    """
    subjectCenter = np.mean(feat, axis=0)
    displacement = massCenter - subjectCenter
    return feat + displacement


# ---------------------------------------------------------------------------
# Fiber distance and neighbor computation
# ---------------------------------------------------------------------------

def _fiberDistanceEfficient(set1, set2, numPoints=15):
    """Compute pairwise distances between two sets of streamlines.

    Uses quadratic expansion for efficiency.

    Args:
        set1: (N, 3, numPoints) tensor
        set2: (M, 3, numPoints) tensor
    Returns:
        mean distance matrix (N, M)
    """
    s1 = set1.reshape(set1.shape[0], -1)
    s2 = set2.reshape(set2.shape[0], -1)
    s1_sq = (s1 ** 2).sum(1).view(-1, 1)
    s2_t = s2.t()
    s2_sq = (s2 ** 2).sum(1).view(1, -1)
    dist = s1_sq + s2_sq - 2.0 * torch.mm(s1, s2_t)
    dist = torch.sqrt(torch.clamp(dist, 0.0, float("inf")))
    return dist / numPoints


def _computeLocalFeatures(feat, k, kDsRate=0.1):
    """Compute local (k-nearest neighbor) features for streamlines.

    Only computes forward distance (no flip), matching the trained model's
    cal_equiv_dist=False setting. This halves the distance computation.

    Args:
        feat: (N_fiber, 3, N_point) tensor
        k: number of nearest neighbors
        kDsRate: downsample rate for distance matrix computation

    Returns:
        localFeat: (N_fiber * k, 3, N_point) neighbor features
    """
    if 0 < kDsRate < 1:
        numDs = int(feat.shape[0] * kDsRate)
        dsIndices = np.random.choice(feat.shape[0], size=numDs, replace=False)
        dsFeat = feat[dsIndices, :, :]
    else:
        dsFeat = feat

    distMat = _fiberDistanceEfficient(feat, dsFeat)
    topkIdx = distMat.topk(k=k, largest=False, dim=-1)[1]
    localFeat = dsFeat[topkIdx.reshape(-1), ...]

    return localFeat


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class RealDataDataset(data.Dataset):
    """Dataset for inference on real (unregistered) tractography."""

    def __init__(self, feat, k=20, kGlobal=80, kDsRate=0.1,
                 roughNumFiberPerIter=10000, progressCallback=None):
        """
        Args:
            feat: (N_fiber, N_point, 3) float32 RAS features
            k: number of local neighbor streamlines
            kGlobal: number of global randomly sampled streamlines
            kDsRate: downsample rate for distance computation
            roughNumFiberPerIter: chunk size for iterative processing
            progressCallback: callable(fraction) for progress updates
        """
        self.feat = feat.astype(np.float32)
        self.k = k
        self.kGlobal = kGlobal

        numFiber = self.feat.shape[0]
        numPoint = self.feat.shape[1]
        numFeatPerPoint = self.feat.shape[2]

        # Global features (random sample)
        if self.kGlobal == 0:
            self.globalFeat = np.zeros(
                (1, numPoint, numFeatPerPoint, 1), dtype=np.float32)
        else:
            randomIdx = np.random.randint(0, numFiber, self.kGlobal)
            self.globalFeat = self.feat[randomIdx, ...]
            self.globalFeat = (self.globalFeat
                               .transpose(1, 2, 0)[None, :, :, :]
                               .astype(np.float32))

        # Local features (k-nearest neighbors)
        if self.k == 0:
            self.localFeat = np.zeros(
                (numFiber, numPoint, numFeatPerPoint, 1), dtype=np.float32)
        else:
            self.localFeat = np.zeros(
                (numFiber, numPoint, numFeatPerPoint, self.k),
                dtype=np.float32)
            numIter = max(numFiber // roughNumFiberPerIter, 1)
            numFiberPerIter = (numFiber // numIter) + 1

            for iIter in range(numIter):
                start = iIter * numFiberPerIter
                end = min((iIter + 1) * numFiberPerIter, numFiber)
                curFeat = self.feat[start:end, ...]
                curFeat = np.transpose(curFeat, (0, 2, 1))
                curLocalFeat = _computeLocalFeatures(
                    torch.from_numpy(curFeat), self.k, kDsRate).numpy()
                curLocalFeat = curLocalFeat.reshape(
                    end - start, self.k, numFeatPerPoint, numPoint)
                curLocalFeat = np.transpose(curLocalFeat, (0, 3, 2, 1))
                self.localFeat[start:end, ...] = curLocalFeat
                if progressCallback:
                    progressCallback((iIter + 1) / numIter)

    def __getitem__(self, index):
        pointSet = torch.from_numpy(self.feat[index])
        klocalPointSet = torch.from_numpy(self.localFeat[index])
        return pointSet, klocalPointSet

    def __len__(self):
        return self.feat.shape[0]


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def loadModel(weightPath, argsPath, device, kOverride=None, kGlobalOverride=None):
    """Load a TractCloud model from saved weights and args.

    Args:
        weightPath: path to .pth weights file
        argsPath: path to cli_args.txt JSON file
        device: torch device
        kOverride: override k (local neighbors) from training args
        kGlobalOverride: override k_global from training args

    Returns:
        (model, args_dict) tuple
    """
    with open(argsPath, "r") as f:
        argsDict = json.load(f)

    modelName = argsDict.get("model_name", "dgcnn")
    numClasses = argsDict.get("num_classes", 1600)
    k = kOverride if kOverride is not None else argsDict.get("k", 20)
    kGlobal = kGlobalOverride if kGlobalOverride is not None else argsDict.get("k_global", 80)
    kPointLevel = argsDict.get("k_point_level", 5)
    embDims = argsDict.get("emb_dims", 1024)
    dropout = argsDict.get("dropout", 0.5)

    if modelName == "dgcnn":
        model = TractDGCNN(
            num_classes=numClasses, k=k, k_global=kGlobal,
            k_point_level=kPointLevel, emb_dims=embDims,
            dropout=dropout, device=device)
    elif modelName == "pointnet":
        model = PointNetCls(
            k=k, k_global=kGlobal, num_classes=numClasses,
            feature_transform=False, first_feature_transform=False)
    else:
        raise ValueError(f"Unknown model: {modelName}")

    weights = torch.load(weightPath, map_location=device, weights_only=True)
    model.load_state_dict(weights)
    model.to(device)
    model.eval()
    return model, argsDict


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def runInference(model, dataLoader, globalFeat, numClasses, device,
                 progressCallback=None):
    """Run model inference on a DataLoader.

    Args:
        model: loaded TractCloud model
        dataLoader: DataLoader wrapping RealDataDataset
        globalFeat: (1, N_point, 3, k_global) global context features
        numClasses: number of output classes
        device: torch device
        progressCallback: callable(fraction) for progress updates

    Returns:
        list of predicted cluster indices (one per streamline)
    """
    predictedList = []
    totalBatches = len(dataLoader)

    with torch.no_grad():
        for batchIdx, (points, klocalFeatSet) in enumerate(dataLoader):
            numFiber = points.shape[0]

            # Transpose to (B, 3, N_point)
            points = points.transpose(2, 1)
            klocalFeatSet = klocalFeatSet.transpose(2, 1)  # (B, 3, N_point, k)

            # Global features replicated for batch
            kglobalFeat = (torch.from_numpy(globalFeat)
                           .repeat(numFiber, 1, 1, 1)
                           .transpose(2, 1))  # (B, 3, N_point, k_global)

            # Concatenate local and global
            infoPointSet = torch.cat(
                (klocalFeatSet, kglobalFeat), dim=3)

            points = points.to(device)
            infoPointSet = infoPointSet.to(device)

            pred = model(points, infoPointSet)
            pred = pred.view(-1, numClasses)
            predChoice = pred.data.max(1)[1].cpu().numpy().tolist()
            predictedList.extend(predChoice)

            if progressCallback:
                progressCallback((batchIdx + 1) / totalBatches)

    return predictedList
