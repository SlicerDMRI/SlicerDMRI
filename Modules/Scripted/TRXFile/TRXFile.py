import json
import logging
import os
import unittest

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import numpy as np


class TRXFile(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = "TRXFile"
    parent.categories = ["Diffusion.Import and Export"]
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)", "SlicerDMRI Team"]
    parent.helpText = """
    Reader and writer for the TRX tractography file format.
    Uses the trx-python package (https://github.com/tee-ar-ex/trx-python).
    TRX files are loaded as FiberBundle nodes. TRX groups become separate
    FiberBundle nodes organized under a SubjectHierarchy folder.
    Per-vertex data maps to VTK point data arrays, per-streamline data maps
    to cell data arrays. Both TRX and Slicer use RAS coordinates for
    tractography, so no coordinate conversion is needed.
    """
    parent.acknowledgementText = """
    TRX format: https://github.com/tee-ar-ex/trx-spec
    trx-python: https://github.com/tee-ar-ex/trx-python
    """
    self.parent = parent


def _ensureTrxPython():
  """Install trx-python if not available."""
  try:
    import trx.trx_file_memmap
  except ModuleNotFoundError:
    slicer.util.pip_install("trx-python")


class TRXFileWidget(ScriptedLoadableModuleWidget):
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

class TRXFileFileReader:

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return "TRX Tractography"

  def fileType(self):
    return "TRXFile"

  def extensions(self):
    return ["TRX Tractography (*.trx)", "VTK Tractography (*.vtk)"]

  def canLoadFileConfidence(self, filePath):
    lower = filePath.lower()
    if lower.endswith(".trx"):
      return 0.6
    if lower.endswith(".vtk"):
      return self._vtkFiberConfidence(filePath)
    return 0.0

  @staticmethod
  def _vtkFiberConfidence(filePath):
    """Return >0 confidence if a VTK file looks like it contains fibers.

    Performs a lightweight scan of the VTK legacy header without reading
    the full geometry.  The format places ASCII keyword lines (POINTS,
    LINES, POLYGONS, …) between data blocks even in binary files, so we
    parse just enough to find them.
    """
    try:
      hasLines = False
      hasPolys = False
      with open(filePath, "rb") as f:
        # Validate VTK header (first 4 lines are always ASCII)
        magic = f.readline()
        if b"vtk DataFile" not in magic:
          return 0.0
        _title = f.readline()              # title line
        formatLine = f.readline().strip()  # ASCII or BINARY
        isBinary = formatLine.upper() == b"BINARY"
        datasetLine = f.readline().strip()
        if b"POLYDATA" not in datasetLine.upper():
          return 0.0

        # Scan through keyword/data blocks until we know enough
        _DTYPE_SIZES = {
          b"bit": 1, b"unsigned_char": 1, b"char": 1,
          b"unsigned_short": 2, b"short": 2,
          b"unsigned_int": 4, b"int": 4,
          b"unsigned_long": 8, b"long": 8,
          b"float": 4, b"double": 8,
        }

        while True:
          line = f.readline()
          if not line:
            break
          parts = line.strip().split()
          if not parts:
            continue
          keyword = parts[0].upper()

          if keyword == b"POINTS" and len(parts) >= 3:
            nPoints = int(parts[1])
            dtype = parts[2].lower()
            if isBinary:
              f.seek(nPoints * 3 * _DTYPE_SIZES.get(dtype, 4), 1)
              f.readline()  # consume trailing newline

          elif keyword == b"LINES":
            hasLines = True
            if hasPolys:
              break
            # skip past the data
            if len(parts) >= 3 and isBinary:
              nInts = int(parts[2])
              f.seek(nInts * 4, 1)
              f.readline()

          elif keyword in (b"POLYGONS", b"TRIANGLE_STRIPS"):
            hasPolys = True
            break  # fibers wouldn't have these

          elif keyword == b"VERTICES" and len(parts) >= 3 and isBinary:
            nInts = int(parts[2])
            f.seek(nInts * 4, 1)
            f.readline()

          elif keyword in (b"POINT_DATA", b"CELL_DATA"):
            break  # past geometry section

      if hasLines and not hasPolys:
        # Header scan confirmed this is polydata with lines and no
        # polygons, so it is almost certainly a fiber bundle.  Return
        # higher than the default model/fiber-bundle reader confidence
        # (0.5 + 0.01 * len(ext) ≈ 0.53) so we win the reader selection.
        return 0.8
    except Exception:
      pass
    return 0.0

  def load(self, properties):
    try:
      filePath = properties["fileName"]
      if "name" in properties:
        baseName = properties["name"]
      else:
        baseName = os.path.splitext(os.path.basename(filePath))[0]
      baseName = slicer.mrmlScene.GenerateUniqueName(baseName)

      lower = filePath.lower()
      if lower.endswith(".trx"):
        _ensureTrxPython()
        from trx.trx_file_memmap import load as trx_load
        trx = trx_load(filePath)
        trx = trx.to_memory()
        loadedNodeIDs = _trxToScene(trx, baseName)
      elif lower.endswith(".vtk"):
        loadedNodeIDs = _vtkFiberToScene(filePath, baseName)
      else:
        logging.error(f"TRX reader: unsupported extension for {filePath}")
        return False

      self.parent.loadedNodes = loadedNodeIDs
      return True

    except Exception as e:
      logging.error("Failed to load file: " + str(e))
      import traceback
      traceback.print_exc()
      return False


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

class TRXFileFileWriter:

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return "TRX Tractography"

  def fileType(self):
    return "TRXFile"

  def extensions(self, obj):
    return ["TRX Tractography (.trx)"]

  def canWriteObject(self, obj):
    return bool(obj.IsA("vtkMRMLFiberBundleNode"))

  def canWriteObjectConfidence(self, obj):
    if obj.IsA("vtkMRMLFiberBundleNode"):
      return 0.6
    return 0.0

  def write(self, properties):
    try:
      _ensureTrxPython()
      from trx.trx_file_memmap import save as trx_save

      filePath = properties["fileName"]
      nodeID = properties["nodeID"]
      node = slicer.mrmlScene.GetNodeByID(nodeID)

      if not node or not node.IsA("vtkMRMLFiberBundleNode"):
        logging.error("TRX writer: invalid node")
        return False

      trx = _sceneToTrx(node)
      trx_save(trx, filePath)

      self.parent.writtenNodes = [nodeID]
      return True

    except Exception as e:
      logging.error("Failed to write TRX file: " + str(e))
      import traceback
      traceback.print_exc()
      return False


# ---------------------------------------------------------------------------
# VTK fiber -> Slicer scene
# ---------------------------------------------------------------------------

def _vtkFiberToScene(filePath, baseName):
  """Load a VTK polydata file containing fiber lines as a FiberBundleNode.

  VTK tractography files store polylines in RAS (Slicer convention), so
  the polydata is used directly.  Any point/cell data arrays in the file
  are preserved.
  """
  reader = vtk.vtkPolyDataReader()
  reader.SetFileName(filePath)
  reader.Update()
  polyData = reader.GetOutput()

  if not polyData or polyData.GetNumberOfLines() == 0:
    raise ValueError(f"VTK file has no line data: {filePath}")

  node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLFiberBundleNode", baseName)
  node.SetAndObservePolyData(polyData)
  node.CreateDefaultDisplayNodes()
  return [node.GetID()]


# ---------------------------------------------------------------------------
# TRX -> Slicer scene
# ---------------------------------------------------------------------------

def _trxToScene(trx, baseName):
  """Import a TrxFile into the Slicer scene.

  If the TRX file has groups, a SubjectHierarchy folder is created with
  one FiberBundleNode per group. data_per_group values are stored as
  node attributes on the SH folder item. The complete tractogram is also
  created as a FiberBundleNode named "<baseName>_all".

  If there are no groups, a single FiberBundleNode is created.

  Returns a list of MRML node IDs that were created.
  """
  positions = np.array(trx.streamlines._data, dtype=np.float64)
  offsets = np.array(trx.streamlines._offsets, dtype=np.int64)
  lengths = np.array(trx.streamlines._lengths, dtype=np.int64)
  nbStreamlines = len(offsets)

  # Prepare TRX header metadata (stored as node attribute for round-trip)
  headerJSON = json.dumps({
    "VOXEL_TO_RASMM": np.array(trx.header.get("VOXEL_TO_RASMM", np.eye(4))).tolist(),
    "DIMENSIONS": np.array(trx.header.get("DIMENSIONS", [1, 1, 1])).tolist(),
  })

  hasGroups = len(trx.groups) > 0
  loadedNodeIDs = []

  if hasGroups:
    shNode = slicer.mrmlScene.GetSubjectHierarchyNode()

    # Create folder
    sceneItemID = shNode.GetSceneItemID()
    folderItemID = shNode.CreateFolderItem(sceneItemID, baseName)
    shNode.SetItemAttribute(folderItemID, "TRX.Header", headerJSON)

    # Store data_per_group as folder attributes
    for groupName, dpgDict in trx.data_per_group.items():
      for attrName, attrVal in dpgDict.items():
        key = f"TRX.dpg.{groupName}.{attrName}"
        shNode.SetItemAttribute(folderItemID, key, json.dumps(np.array(attrVal).tolist()))

    # Create complete tractogram node
    allNode = _buildFiberBundleNode(
      baseName + "_all", positions, offsets, lengths,
      trx.data_per_vertex, trx.data_per_streamline
    )
    allNode.SetAttribute("TRX.Header", headerJSON)
    allNode.SetAttribute("TRX.Role", "all")
    shNode.SetItemParent(shNode.GetItemByDataNode(allNode), folderItemID)
    loadedNodeIDs.append(allNode.GetID())

    # Create one node per group
    for groupName, groupIndices in trx.groups.items():
      groupIndices = np.array(groupIndices, dtype=np.int64)
      gNode = _extractGroupFiberBundle(
        groupName, positions, offsets, lengths,
        trx.data_per_vertex, trx.data_per_streamline,
        groupIndices
      )
      gNode.SetAttribute("TRX.Header", headerJSON)
      gNode.SetAttribute("TRX.Role", "group")
      gNode.SetAttribute("TRX.GroupName", groupName)

      # Store per-group data as node attributes
      if groupName in trx.data_per_group:
        for attrName, attrVal in trx.data_per_group[groupName].items():
          gNode.SetAttribute(
            f"TRX.dpg.{attrName}",
            json.dumps(np.array(attrVal).tolist())
          )

      shNode.SetItemParent(shNode.GetItemByDataNode(gNode), folderItemID)
      loadedNodeIDs.append(gNode.GetID())
  else:
    # No groups: single FiberBundleNode
    fbNode = _buildFiberBundleNode(
      baseName, positions, offsets, lengths,
      trx.data_per_vertex, trx.data_per_streamline
    )
    fbNode.SetAttribute("TRX.Header", headerJSON)
    loadedNodeIDs.append(fbNode.GetID())

  return loadedNodeIDs


def _buildFiberBundleNode(name, positions, offsets, lengths,
                          data_per_vertex, data_per_streamline):
  """Build a vtkMRMLFiberBundleNode from raw numpy arrays.

  TRX positions are in RASMM which matches Slicer's RAS fiber bundle
  coordinate system directly -- no flip needed.
  """
  from vtk.util.numpy_support import numpy_to_vtk

  polyData = vtk.vtkPolyData()

  # Points — bulk set from numpy
  posF64 = np.ascontiguousarray(positions, dtype=np.float64)
  vtkPts = vtk.vtkPoints()
  vtkPts.SetData(numpy_to_vtk(posF64, deep=True))
  polyData.SetPoints(vtkPts)

  # Lines — build VTK cell array from offsets/lengths.
  # VTK 9+ CellArray uses (cumulative_offsets, connectivity) format.
  cumOffsets = np.empty(len(offsets) + 1, dtype=np.int64)
  cumOffsets[0] = 0
  np.cumsum(lengths, out=cumOffsets[1:])
  totalPts = int(cumOffsets[-1])

  # Check if points are already contiguous (typical for TRX data)
  expectedOffsets = cumOffsets[:-1]
  if np.array_equal(offsets, expectedOffsets):
    connectivity = np.arange(totalPts, dtype=np.int64)
  else:
    # Non-contiguous: build connectivity with vectorized repeat+arange
    connectivity = np.empty(totalPts, dtype=np.int64)
    starts = np.asarray(offsets, dtype=np.int64)
    lens = np.asarray(lengths, dtype=np.int64)
    base = np.repeat(starts, lens)
    within = np.arange(totalPts, dtype=np.int64) - np.repeat(cumOffsets[:-1], lens)
    connectivity = base + within

  vtkLines = vtk.vtkCellArray()
  vtkLines.SetData(
    numpy_to_vtk(cumOffsets, deep=True, array_type=vtk.VTK_ID_TYPE),
    numpy_to_vtk(connectivity, deep=True, array_type=vtk.VTK_ID_TYPE),
  )
  polyData.SetLines(vtkLines)

  # Data per vertex -> point data
  pointData = polyData.GetPointData()
  for arrName, arraySeq in data_per_vertex.items():
    data = np.ascontiguousarray(arraySeq._data, dtype=np.float64)
    pointData.AddArray(_numpyToVtkArray(data, arrName))

  # Data per streamline -> cell data
  cellData = polyData.GetCellData()
  for arrName, arr in data_per_streamline.items():
    data = np.ascontiguousarray(arr, dtype=np.float64)
    cellData.AddArray(_numpyToVtkArray(data, arrName))

  node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLFiberBundleNode", name)
  node.SetAndObservePolyData(polyData)
  node.CreateDefaultDisplayNodes()
  return node


def _extractGroupFiberBundle(groupName, allPositions, allOffsets, allLengths,
                             allDpv, allDps, groupIndices):
  """Extract a subset of streamlines (by index) into a new FiberBundleNode."""
  # Gather the subset of streamlines
  newPositions = []
  newOffsets = []
  newLengths = []
  currentOffset = 0
  for idx in groupIndices:
    start = int(allOffsets[idx])
    length = int(allLengths[idx])
    newPositions.append(allPositions[start:start + length])
    newOffsets.append(currentOffset)
    newLengths.append(length)
    currentOffset += length

  if len(newPositions) > 0:
    positions = np.concatenate(newPositions, axis=0)
  else:
    positions = np.zeros((0, 3), dtype=np.float64)
  offsets = np.array(newOffsets, dtype=np.int64)
  lengths = np.array(newLengths, dtype=np.int64)

  # Extract dpv subset
  from nibabel.streamlines import ArraySequence
  subDpv = {}
  for arrName, arraySeq in allDpv.items():
    allData = np.array(arraySeq._data, dtype=np.float64)
    subSeq = ArraySequence()
    subData = []
    for idx in groupIndices:
      start = int(allOffsets[idx])
      length = int(allLengths[idx])
      subData.append(allData[start:start + length])
    if len(subData) > 0:
      concatData = np.concatenate(subData, axis=0)
    else:
      concatData = np.zeros((0, allData.shape[1] if allData.ndim > 1 else 1), dtype=np.float64)
    subSeq._data = concatData
    subSeq._offsets = offsets.copy()
    subSeq._lengths = lengths.copy()
    subDpv[arrName] = subSeq

  # Extract dps subset
  subDps = {}
  for arrName, arr in allDps.items():
    data = np.array(arr, dtype=np.float64)
    subDps[arrName] = data[groupIndices]

  return _buildFiberBundleNode(groupName, positions, offsets, lengths, subDpv, subDps)


# ---------------------------------------------------------------------------
# Slicer scene -> TRX
# ---------------------------------------------------------------------------

def _sceneToTrx(node):
  """Convert a FiberBundleNode (and optionally its SH siblings) to a TrxFile.

  If the node has a TRX.Role="all" attribute and is in a SH folder with
  group nodes, the full structure (groups, dpg) is reconstructed.
  Otherwise, a simple single-bundle TRX is created.
  """
  from trx.trx_file_memmap import TrxFile
  from nibabel.streamlines import ArraySequence

  role = node.GetAttribute("TRX.Role") or ""

  if role == "all":
    return _sceneToTrxWithGroups(node)

  # Simple case: single fiber bundle
  polyData = node.GetPolyData()
  if not polyData or polyData.GetNumberOfLines() == 0:
    raise ValueError("FiberBundle node has no streamline data")

  nbStreamlines = polyData.GetNumberOfLines()
  nbPoints = polyData.GetNumberOfPoints()
  positions, offsets, lengths = _extractPolyDataGeometry(polyData)

  # Header
  headerJSON = node.GetAttribute("TRX.Header")
  if headerJSON:
    hdr = json.loads(headerJSON)
    affine = np.array(hdr["VOXEL_TO_RASMM"], dtype=np.float32)
    dimensions = np.array(hdr["DIMENSIONS"], dtype=np.uint16)
  else:
    affine = np.eye(4, dtype=np.float32)
    dimensions = np.array([1, 1, 1], dtype=np.uint16)

  trx = TrxFile(nb_vertices=nbPoints, nb_streamlines=nbStreamlines)
  trx.streamlines._data[:] = positions.astype(np.float16)
  trx.streamlines._offsets[:] = offsets
  trx.streamlines._lengths[:] = lengths
  trx.header["VOXEL_TO_RASMM"] = affine
  trx.header["DIMENSIONS"] = dimensions

  # dpv
  pointData = polyData.GetPointData()
  for i in range(pointData.GetNumberOfArrays()):
    arr = pointData.GetArray(i)
    arrName = arr.GetName()
    if not arrName:
      continue
    data = _vtkArrayToNumpy(arr).astype(np.float16)
    dpv = ArraySequence()
    dpv._data = data
    dpv._offsets = offsets.copy()
    dpv._lengths = lengths.copy()
    trx.data_per_vertex[arrName] = dpv

  # dps
  cellData = polyData.GetCellData()
  for i in range(cellData.GetNumberOfArrays()):
    arr = cellData.GetArray(i)
    arrName = arr.GetName()
    if not arrName:
      continue
    trx.data_per_streamline[arrName] = _vtkArrayToNumpy(arr).astype(np.float32)

  return trx


def _sceneToTrxWithGroups(allNode):
  """Build a TrxFile from an 'all' node and its sibling group nodes."""
  from trx.trx_file_memmap import TrxFile
  from nibabel.streamlines import ArraySequence

  polyData = allNode.GetPolyData()
  nbStreamlines = polyData.GetNumberOfLines()
  nbPoints = polyData.GetNumberOfPoints()
  positions, offsets, lengths = _extractPolyDataGeometry(polyData)

  headerJSON = allNode.GetAttribute("TRX.Header")
  if headerJSON:
    hdr = json.loads(headerJSON)
    affine = np.array(hdr["VOXEL_TO_RASMM"], dtype=np.float32)
    dimensions = np.array(hdr["DIMENSIONS"], dtype=np.uint16)
  else:
    affine = np.eye(4, dtype=np.float32)
    dimensions = np.array([1, 1, 1], dtype=np.uint16)

  trx = TrxFile(nb_vertices=nbPoints, nb_streamlines=nbStreamlines)
  trx.streamlines._data[:] = positions.astype(np.float16)
  trx.streamlines._offsets[:] = offsets
  trx.streamlines._lengths[:] = lengths
  trx.header["VOXEL_TO_RASMM"] = affine
  trx.header["DIMENSIONS"] = dimensions

  # dpv from all node
  pointData = polyData.GetPointData()
  for i in range(pointData.GetNumberOfArrays()):
    arr = pointData.GetArray(i)
    arrName = arr.GetName()
    if not arrName:
      continue
    data = _vtkArrayToNumpy(arr).astype(np.float16)
    dpv = ArraySequence()
    dpv._data = data
    dpv._offsets = offsets.copy()
    dpv._lengths = lengths.copy()
    trx.data_per_vertex[arrName] = dpv

  # dps from all node
  cellData = polyData.GetCellData()
  for i in range(cellData.GetNumberOfArrays()):
    arr = cellData.GetArray(i)
    arrName = arr.GetName()
    if not arrName:
      continue
    trx.data_per_streamline[arrName] = _vtkArrayToNumpy(arr).astype(np.float32)

  # Find sibling group nodes via SubjectHierarchy
  shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
  allItemID = shNode.GetItemByDataNode(allNode)
  folderItemID = shNode.GetItemParent(allItemID)

  childIDs = vtk.vtkIdList()
  shNode.GetItemChildren(folderItemID, childIDs)
  allPositions = positions

  for ci in range(childIDs.GetNumberOfIds()):
    childItemID = childIDs.GetId(ci)
    childNode = shNode.GetItemDataNode(childItemID)
    if not childNode or childNode is allNode:
      continue
    if not childNode.IsA("vtkMRMLFiberBundleNode"):
      continue
    groupRole = childNode.GetAttribute("TRX.Role")
    if groupRole != "group":
      continue
    groupName = childNode.GetAttribute("TRX.GroupName") or childNode.GetName()

    # Match group streamlines back to all-node streamlines by first-point coords
    groupPD = childNode.GetPolyData()
    if not groupPD or groupPD.GetNumberOfLines() == 0:
      continue

    groupIndices = _matchStreamlines(polyData, groupPD)
    if len(groupIndices) > 0:
      trx.groups[groupName] = np.array(groupIndices, dtype=np.uint32)

    # Reconstruct data_per_group from node attributes
    dpgDict = {}
    attrNames = childNode.GetAttributeNames()
    if attrNames:
      for attr in attrNames.split(";") if isinstance(attrNames, str) else []:
        if attr.startswith("TRX.dpg."):
          dpgKey = attr[len("TRX.dpg."):]
          dpgDict[dpgKey] = np.array(json.loads(childNode.GetAttribute(attr)))
    if dpgDict:
      trx.data_per_group[groupName] = dpgDict

  return trx


def _matchStreamlines(allPD, groupPD):
  """Find indices in allPD that match streamlines in groupPD by first+last point."""
  # Build lookup from (first_point, last_point) -> index for allPD
  allLines = allPD.GetLines()
  allLines.InitTraversal()
  idList = vtk.vtkIdList()
  allPts = allPD.GetPoints()

  lookup = {}
  for i in range(allPD.GetNumberOfLines()):
    allLines.GetNextCell(idList)
    nPts = idList.GetNumberOfIds()
    if nPts == 0:
      continue
    firstPt = allPts.GetPoint(idList.GetId(0))
    lastPt = allPts.GetPoint(idList.GetId(nPts - 1))
    key = (round(firstPt[0], 3), round(firstPt[1], 3), round(firstPt[2], 3),
           round(lastPt[0], 3), round(lastPt[1], 3), round(lastPt[2], 3))
    lookup[key] = i

  # Match group streamlines
  groupLines = groupPD.GetLines()
  groupLines.InitTraversal()
  groupPts = groupPD.GetPoints()
  indices = []

  for _ in range(groupPD.GetNumberOfLines()):
    groupLines.GetNextCell(idList)
    nPts = idList.GetNumberOfIds()
    if nPts == 0:
      continue
    firstPt = groupPts.GetPoint(idList.GetId(0))
    lastPt = groupPts.GetPoint(idList.GetId(nPts - 1))
    key = (round(firstPt[0], 3), round(firstPt[1], 3), round(firstPt[2], 3),
           round(lastPt[0], 3), round(lastPt[1], 3), round(lastPt[2], 3))
    if key in lookup:
      indices.append(lookup[key])

  return indices


# ---------------------------------------------------------------------------
# Geometry extraction helpers
# ---------------------------------------------------------------------------

def _extractPolyDataGeometry(polyData):
  """Extract positions, offsets, lengths from a fiber bundle polydata."""
  from vtk.util.numpy_support import vtk_to_numpy

  # Points — bulk extract
  positions = vtk_to_numpy(polyData.GetPoints().GetData()).astype(np.float64)
  if positions.ndim == 1:
    positions = positions.reshape(-1, 3)

  # Lines — extract from VTK cell array's internal arrays
  lines = polyData.GetLines()
  cumOffsets = vtk_to_numpy(lines.GetOffsetsArray()).astype(np.int64)
  connectivity = vtk_to_numpy(lines.GetConnectivityArray()).astype(np.int64)

  lengths = np.diff(cumOffsets)
  # The "offset" into the positions array for each streamline is the
  # first point ID in the connectivity for that cell.
  offsets = connectivity[cumOffsets[:-1]]

  return positions, offsets, lengths


# ---------------------------------------------------------------------------
# VTK <-> numpy helpers
# ---------------------------------------------------------------------------

def _numpyToVtkArray(npArr, name):
  """Convert a numpy array to a named vtkDoubleArray (zero-copy path)."""
  from vtk.util.numpy_support import numpy_to_vtk
  npArr = np.ascontiguousarray(npArr, dtype=np.float64)
  if npArr.ndim == 1:
    npArr = npArr.reshape(-1, 1)
  vtkArr = numpy_to_vtk(npArr, deep=True)
  vtkArr.SetName(name)
  return vtkArr


def _vtkArrayToNumpy(vtkArr):
  """Convert a vtkDataArray to a numpy array (zero-copy path)."""
  from vtk.util.numpy_support import vtk_to_numpy
  npArr = vtk_to_numpy(vtkArr).astype(np.float64)
  nComponents = vtkArr.GetNumberOfComponents()
  if nComponents > 1:
    npArr = npArr.reshape(-1, nComponents)
  else:
    npArr = npArr.reshape(-1, 1)
  return npArr


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

class TRXFileTest(ScriptedLoadableModuleTest):
  """Self-test that loads gold standard TRX test data, verifies it,
  writes it back out, reloads, and compares for round-trip fidelity."""

  def runTest(self):
    self.setUp()
    self.test_ReadGoldStandard()
    self.test_RoundTrip()
    self.tearDown()
    self.delayDisplay("TRXFile testing complete")

  def setUp(self):
    _ensureTrxPython()
    self.tempDir = slicer.util.tempDirectory()
    slicer.mrmlScene.Clear()

  def tearDown(self):
    import shutil
    shutil.rmtree(self.tempDir, True)

  def _getGoldStandardPath(self):
    """Download and return path to gold standard TRX file."""
    from trx.fetcher import get_testing_files_dict, fetch_data, get_home
    fetch_data(get_testing_files_dict(), keys=["gold_standard.zip"])
    gsPath = os.path.join(get_home(), "gold_standard", "gs.trx")
    if not os.path.exists(gsPath):
      raise RuntimeError(f"Gold standard file not found at {gsPath}")
    return gsPath

  def test_ReadGoldStandard(self):
    """Load the gold standard TRX file and verify basic properties."""
    self.delayDisplay("Loading gold standard TRX file...")

    from trx.trx_file_memmap import load as trx_load

    gsPath = self._getGoldStandardPath()
    trxRef = trx_load(gsPath).to_memory()

    refNbStreamlines = int(trxRef.header["NB_STREAMLINES"])
    refNbVertices = int(trxRef.header["NB_VERTICES"])

    # Load via our conversion
    nodeIDs = _trxToScene(trxRef, "GoldStandard")
    self.assertTrue(len(nodeIDs) > 0, "No nodes were created")

    node = slicer.mrmlScene.GetNodeByID(nodeIDs[0])
    polyData = node.GetPolyData()

    # Verify counts
    self.assertEqual(polyData.GetNumberOfLines(), refNbStreamlines,
      f"Expected {refNbStreamlines} streamlines, got {polyData.GetNumberOfLines()}")
    self.assertEqual(polyData.GetNumberOfPoints(), refNbVertices,
      f"Expected {refNbVertices} points, got {polyData.GetNumberOfPoints()}")

    # Verify first streamline coordinates
    refFirst = np.array(trxRef.streamlines[0], dtype=np.float64)
    vtkPts = polyData.GetPoints()
    lines = polyData.GetLines()
    lines.InitTraversal()
    idList = vtk.vtkIdList()
    lines.GetNextCell(idList)
    nPts = idList.GetNumberOfIds()
    self.assertEqual(nPts, len(refFirst))

    for j in range(nPts):
      pt = np.array(vtkPts.GetPoint(idList.GetId(j)))
      np.testing.assert_allclose(pt, refFirst[j], atol=1e-3,
        err_msg=f"Point mismatch at streamline 0, point {j}")

    # Verify per-vertex arrays
    for dpvName in trxRef.data_per_vertex:
      arr = polyData.GetPointData().GetArray(dpvName)
      self.assertIsNotNone(arr, f"Missing point data array: {dpvName}")
      self.assertEqual(arr.GetNumberOfTuples(), refNbVertices)

    # Verify per-streamline arrays
    for dpsName in trxRef.data_per_streamline:
      arr = polyData.GetCellData().GetArray(dpsName)
      self.assertIsNotNone(arr, f"Missing cell data array: {dpsName}")
      self.assertEqual(arr.GetNumberOfTuples(), refNbStreamlines)

    # Verify header attribute preserved
    headerAttr = node.GetAttribute("TRX.Header")
    self.assertIsNotNone(headerAttr, "TRX.Header attribute missing")
    hdr = json.loads(headerAttr)
    self.assertIn("VOXEL_TO_RASMM", hdr)
    self.assertIn("DIMENSIONS", hdr)

    self.delayDisplay(
      f"Read {refNbStreamlines} streamlines, {refNbVertices} vertices, "
      f"{polyData.GetPointData().GetNumberOfArrays()} dpv, "
      f"{polyData.GetCellData().GetNumberOfArrays()} dps -- PASSED")

  def test_RoundTrip(self):
    """Write a fiber bundle to TRX and read it back, comparing."""
    self.delayDisplay("Testing round-trip write/read...")
    slicer.mrmlScene.Clear()

    from trx.trx_file_memmap import load as trx_load, save as trx_save

    gsPath = self._getGoldStandardPath()
    trxRef = trx_load(gsPath).to_memory()

    # Load into scene
    nodeIDs = _trxToScene(trxRef, "RTOriginal")
    originalNode = slicer.mrmlScene.GetNodeByID(nodeIDs[0])

    # Write back to TRX
    outPath = os.path.join(self.tempDir, "roundtrip.trx")
    trxOut = _sceneToTrx(originalNode)
    trx_save(trxOut, outPath)
    self.assertTrue(os.path.exists(outPath), "Output file not created")

    # Reload
    trxReloaded = trx_load(outPath).to_memory()

    # Compare counts
    self.assertEqual(
      int(trxRef.header["NB_STREAMLINES"]),
      int(trxReloaded.header["NB_STREAMLINES"]),
      "Streamline count mismatch")
    self.assertEqual(
      int(trxRef.header["NB_VERTICES"]),
      int(trxReloaded.header["NB_VERTICES"]),
      "Vertex count mismatch")

    # Compare coordinates (float16 precision)
    origPts = np.array(trxRef.streamlines._data, dtype=np.float64)
    reloadPts = np.array(trxReloaded.streamlines._data, dtype=np.float64)
    maxDiff = np.abs(origPts - reloadPts).max()
    self.assertLess(maxDiff, 0.1,
      f"Coordinate difference too large: {maxDiff}")

    # Compare dpv/dps key sets
    self.assertEqual(
      set(trxRef.data_per_vertex.keys()),
      set(trxReloaded.data_per_vertex.keys()),
      "data_per_vertex key mismatch")
    self.assertEqual(
      set(trxRef.data_per_streamline.keys()),
      set(trxReloaded.data_per_streamline.keys()),
      "data_per_streamline key mismatch")

    # Compare header affine
    origAffine = np.array(trxRef.header["VOXEL_TO_RASMM"], dtype=np.float64)
    reloadAffine = np.array(trxReloaded.header["VOXEL_TO_RASMM"], dtype=np.float64)
    np.testing.assert_allclose(origAffine, reloadAffine, atol=1e-5,
      err_msg="Affine mismatch after round-trip")

    self.delayDisplay(
      f"Round-trip: max coord diff = {maxDiff:.4f} (float16 expected) -- PASSED")
