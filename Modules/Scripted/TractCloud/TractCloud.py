import logging
import os

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import numpy as np


class TractCloud(ScriptedLoadableModule):
    """TractCloud: Registration-free tractography parcellation.

    Uses deep learning to classify streamlines from whole-brain tractography
    into 42 anatomical white matter tracts without requiring image registration.

    Reference: Xue et al., "TractCloud: Registration-free tractography
    parcellation with a novel local-global streamline point cloud
    representation", MICCAI 2023.
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "TractCloud"
        self.parent.categories = ["Diffusion.Tractography"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Steve Pieper (Isomics)",
            "Tengfei Xue (University of Sydney)",
            "Fan Zhang (University of Electronic Science and Technology of China)",
            "Lauren J. O'Donnell (BWH / HMS)",
            "SlicerDMRI Team",
        ]
        self.parent.helpText = """
TractCloud parcellates whole-brain tractography into 42 anatomical white matter
tracts using a deep learning point cloud classifier. It operates directly in
subject space without requiring registration to an atlas.

<b>Input:</b> A FiberBundle node containing whole-brain tractography.<br>
<b>Output:</b> A SubjectHierarchy folder containing one FiberBundle per
identified tract (up to 42 tracts).

On first use the module downloads pre-trained model weights (~50 MB) and atlas
data. PyTorch is installed automatically if needed.

The model supports both GPU (CUDA) and CPU inference. GPU is used automatically
when available.
"""
        self.parent.acknowledgementText = """
Based on the TractCloud method: https://github.com/SlicerDMRI/TractCloud

Tengfei Xue, Yuqian Chen, Chaoyi Zhang, Alexandra J. Golby, Nikos Makris,
Yogesh Rathi, Weidong Cai, Fan Zhang, Lauren J. O'Donnell.
MICCAI 2023.

Supported by NIH grants and the SlicerDMRI project (http://dmri.slicer.org).
"""


class TractCloudWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # --- Parameters ---
        parametersCollapsible = ctk.ctkCollapsibleButton()
        parametersCollapsible.text = "Parameters"
        self.layout.addWidget(parametersCollapsible)
        parametersForm = qt.QFormLayout(parametersCollapsible)

        # Input fiber bundle
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLFiberBundleNode"]
        self.inputSelector.selectNodeUponCreation = False
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = True
        self.inputSelector.showHidden = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.setToolTip(
            "Select whole-brain tractography to parcellate.")
        parametersForm.addRow("Input FiberBundle:", self.inputSelector)

        # Include Other tract checkbox
        self.includeOtherCheckBox = qt.QCheckBox()
        self.includeOtherCheckBox.checked = False
        self.includeOtherCheckBox.setToolTip(
            "If checked, include an 'Other' bundle for streamlines not "
            "assigned to any anatomical tract.")
        parametersForm.addRow("Include 'Other' tract:", self.includeOtherCheckBox)

        # --- Advanced ---
        advancedCollapsible = ctk.ctkCollapsibleButton()
        advancedCollapsible.text = "Advanced"
        advancedCollapsible.collapsed = True
        self.layout.addWidget(advancedCollapsible)
        advancedForm = qt.QFormLayout(advancedCollapsible)

        # Device selector
        self.deviceCombo = qt.QComboBox()
        self.deviceCombo.addItem("Auto (GPU if available)")
        self.deviceCombo.addItem("CPU only")
        advancedForm.addRow("Device:", self.deviceCombo)

        # Batch size
        self.batchSizeSpinBox = qt.QSpinBox()
        self.batchSizeSpinBox.minimum = 64
        self.batchSizeSpinBox.maximum = 16384
        self.batchSizeSpinBox.value = 2048
        self.batchSizeSpinBox.setToolTip(
            "Batch size for model inference. Reduce if running out of memory.")
        advancedForm.addRow("Batch size:", self.batchSizeSpinBox)

        # Num points per fiber
        self.numPointsSpinBox = qt.QSpinBox()
        self.numPointsSpinBox.minimum = 5
        self.numPointsSpinBox.maximum = 100
        self.numPointsSpinBox.value = 15
        self.numPointsSpinBox.setToolTip(
            "Number of points to resample each streamline to. "
            "Must match the trained model (default 15).")
        advancedForm.addRow("Points per fiber:", self.numPointsSpinBox)

        # --- Apply ---
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run TractCloud parcellation."
        self.applyButton.enabled = False
        self.layout.addWidget(self.applyButton)

        # Progress bar
        self.progressBar = qt.QProgressBar()
        self.progressBar.visible = False
        self.layout.addWidget(self.progressBar)

        # Status label
        self.statusLabel = qt.QLabel("")
        self.layout.addWidget(self.statusLabel)

        self.layout.addStretch(1)

        # Connections
        self.inputSelector.connect(
            "currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.applyButton.connect("clicked(bool)", self.onApply)

        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.inputSelector.currentNode() is not None

    def onApply(self):
        inputNode = self.inputSelector.currentNode()
        if not inputNode:
            slicer.util.errorDisplay("Please select an input FiberBundle.")
            return

        self.applyButton.enabled = False
        self.progressBar.visible = True
        self.progressBar.setValue(0)
        self.statusLabel.text = ""

        try:
            logic = TractCloudLogic()
            logic.progressCallback = self._updateProgress
            logic.statusCallback = self._updateStatus
            logic.run(
                inputNode,
                includeOther=self.includeOtherCheckBox.checked,
                forceCPU=(self.deviceCombo.currentIndex == 1),
                batchSize=self.batchSizeSpinBox.value,
                numPoints=self.numPointsSpinBox.value,
            )
            self.statusLabel.text = "Parcellation complete."
        except Exception as e:
            slicer.util.errorDisplay(f"TractCloud failed: {e}")
            import traceback
            traceback.print_exc()
            self.statusLabel.text = "Error during parcellation."
        finally:
            self.applyButton.enabled = True
            self.progressBar.visible = False

    def _updateProgress(self, fraction):
        self.progressBar.setValue(int(fraction * 100))
        slicer.app.processEvents()

    def _updateStatus(self, message):
        self.statusLabel.text = message
        logging.info(message)
        slicer.app.processEvents()


class TractCloudLogic(ScriptedLoadableModuleLogic):
    """Orchestrates TractCloud inference and scene output."""

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.progressCallback = None
        self.statusCallback = None

    def _status(self, msg):
        if self.statusCallback:
            self.statusCallback(msg)
        else:
            logging.info(msg)

    def _progress(self, fraction):
        if self.progressCallback:
            self.progressCallback(fraction)

    def run(self, inputNode, includeOther=False, forceCPU=False,
            batchSize=2048, numPoints=15):
        """Run TractCloud parcellation on a FiberBundle node.

        Args:
            inputNode: vtkMRMLFiberBundleNode with whole-brain tractography
            includeOther: whether to create a bundle for unclassified fibers
            forceCPU: force CPU even if GPU is available
            batchSize: inference batch size
            numPoints: points per streamline (must match trained model)

        Returns:
            list of created vtkMRMLFiberBundleNode IDs
        """
        import torch

        self._ensureDependencies()

        from TractCloudLib.inference import (
            ensureModelData, extractRASFeatures, centerTractography,
            RealDataDataset, loadModel, runInference,
        )
        from TractCloudLib.tract_mapping import (
            TRACT_NAMES, cluster2tract_label,
        )

        startTime = __import__("time").time()

        # --- Device ---
        if forceCPU:
            device = torch.device("cpu")
        else:
            device = torch.device(
                "cuda:0" if torch.cuda.is_available() else "cpu")
        self._status(f"Using device: {device}")

        # --- Model data ---
        self._status("Checking model data...")
        weightPath, argsPath, massCenter = ensureModelData(
            progressCallback=self._progress)

        # --- Load model ---
        # Use inference-appropriate defaults (training k_global=500, k_ds_rate=1.0 are too large)
        k = 20
        kGlobal = 80
        kDsRate = 0.1
        numClasses = 1600

        self._status("Loading model...")
        model, argsDict = loadModel(weightPath, argsPath, device,
                                     kOverride=k, kGlobalOverride=kGlobal)

        # --- Extract features ---
        polyData = inputNode.GetPolyData()
        numFibers = polyData.GetNumberOfLines()
        self._status(
            f"Extracting features from {numFibers} streamlines "
            f"(step 1/4)...")
        self._progress(0.0)
        featRAS = extractRASFeatures(polyData, numPoints=numPoints)

        # --- Re-center ---
        self._status("Re-centering tractography to atlas space...")
        centeredFeat = centerTractography(featRAS, massCenter)

        # --- Build dataset ---
        self._status(
            "Computing local/global neighbor features "
            "(step 2/4, this is the slowest step)...")
        dataset = RealDataDataset(
            centeredFeat, k=k, kGlobal=kGlobal, kDsRate=kDsRate,
            progressCallback=self._progress)
        dataLoader = torch.utils.data.DataLoader(
            dataset, batch_size=batchSize, shuffle=False)
        globalFeat = dataset.globalFeat

        # --- Inference ---
        self._status("Running model inference (step 3/4)...")
        clusterPredictions = runInference(
            model, dataLoader, globalFeat, numClasses, device,
            progressCallback=self._progress)

        # --- Map clusters to tracts ---
        tractLabels = cluster2tract_label(clusterPredictions)
        tractLabels = np.array(tractLabels)

        # --- Create output nodes ---
        self._status("Creating output fiber bundles (step 4/4)...")
        self._progress(0.0)
        createdNodeIDs = self._createOutputNodes(
            inputNode, polyData, tractLabels, includeOther)

        elapsed = __import__("time").time() - startTime
        self._status(
            f"Done! Created {len(createdNodeIDs)} tract bundles "
            f"in {elapsed:.1f}s")
        return createdNodeIDs

    def _ensureDependencies(self):
        """Install PyTorch if needed."""
        self._status("Checking dependencies...")

        try:
            import torch
        except ImportError:
            self._status("Installing PyTorch (CPU)...")
            slicer.util.pip_install(
                "torch torchvision torchaudio"
                " --index-url https://download.pytorch.org/whl/cpu")


    def _createOutputNodes(self, inputNode, polyData, tractLabels,
                           includeOther):
        """Create two-level SubjectHierarchy with category and tract folders.

        Structure:
            <inputName>_TractCloud/
                Association/
                    AF, CB, EC, ...
                Projection/
                    CST, CR-F, ...
                Commissural/
                    CC1, CC2, ...
                Cerebellar/
                    CPC, ICP, ...
                Superficial/
                    Sup-F, Sup-FP, ...
                Other/ (optional)
                    Other

        Each tract is assigned a unique solid color from the GenericColors
        color table.

        Args:
            inputNode: source FiberBundle node (for naming)
            polyData: original vtkPolyData
            tractLabels: array of tract label indices per streamline
            includeOther: whether to create a bundle for 'Other'

        Returns:
            list of created node IDs
        """
        from TractCloudLib.tract_mapping import (
            TRACT_NAMES, TRACT_CATEGORIES, TRACT_FULL_NAMES,
        )

        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        sceneItemID = shNode.GetSceneItemID()
        baseName = inputNode.GetName() + "_TractCloud"
        rootFolderID = shNode.CreateFolderItem(sceneItemID, baseName)

        colorNode = slicer.util.getNode("GenericColors")

        createdNodeIDs = []
        colorIndex = 1  # start at 1 (index 0 is black/transparent)
        totalTracts = sum(
            len(tracts) for cat, tracts in TRACT_CATEGORIES.items()
            if cat != "Other" or includeOther)
        tractsDone = 0

        for categoryName, tractNamesInCategory in TRACT_CATEGORIES.items():
            if categoryName == "Other" and not includeOther:
                continue

            # Collect tracts that have fibers before creating the folder
            categoryTracts = []
            for tractName in tractNamesInCategory:
                tractIdx = TRACT_NAMES.index(tractName)
                fiberIndices = np.where(tractLabels == tractIdx)[0]
                if len(fiberIndices) > 0:
                    categoryTracts.append((tractName, fiberIndices))

            if not categoryTracts:
                continue

            # Create category subfolder
            categoryFolderID = shNode.CreateFolderItem(
                rootFolderID, categoryName)

            for tractName, fiberIndices in categoryTracts:
                tractPolyData = self._extractFibers(polyData, fiberIndices)

                fullName = TRACT_FULL_NAMES.get(tractName, tractName)
                nodeName = f"{fullName} ({tractName})"
                node = slicer.mrmlScene.AddNewNodeByClass(
                    "vtkMRMLFiberBundleNode", nodeName)
                node.SetAndObservePolyData(tractPolyData)
                node.CreateDefaultDisplayNodes()

                # Set solid color from GenericColors
                color = [0.0, 0.0, 0.0, 0.0]
                colorNode.GetColor(colorIndex, color)
                lineDisplayNode = node.GetLineDisplayNode()
                if lineDisplayNode:
                    lineDisplayNode.SetColor(color[0], color[1], color[2])
                    lineDisplayNode.SetColorModeToSolid()
                tubeDisplayNode = node.GetTubeDisplayNode()
                if tubeDisplayNode:
                    tubeDisplayNode.SetColor(color[0], color[1], color[2])
                    tubeDisplayNode.SetColorModeToSolid()
                colorIndex += 1

                # Parent under category folder
                itemID = shNode.GetItemByDataNode(node)
                shNode.SetItemParent(itemID, categoryFolderID)
                createdNodeIDs.append(node.GetID())

                tractsDone += 1
                self._progress(tractsDone / totalTracts)

        return createdNodeIDs

    @staticmethod
    def _extractFibers(polyData, fiberIndices):
        """Extract a subset of fibers from polydata by cell index.

        Args:
            polyData: source vtkPolyData with lines
            fiberIndices: array of cell indices to extract

        Returns:
            new vtkPolyData with only the selected fibers
        """
        outPoints = vtk.vtkPoints()
        outLines = vtk.vtkCellArray()
        ptIds = vtk.vtkIdList()
        inPoints = polyData.GetPoints()

        for cellIdx in fiberIndices:
            polyData.GetCellPoints(int(cellIdx), ptIds)
            newPtIds = vtk.vtkIdList()
            for j in range(ptIds.GetNumberOfIds()):
                point = inPoints.GetPoint(ptIds.GetId(j))
                newId = outPoints.InsertNextPoint(point)
                newPtIds.InsertNextId(newId)
            outLines.InsertNextCell(newPtIds)

        outPD = vtk.vtkPolyData()
        outPD.SetPoints(outPoints)
        outPD.SetLines(outLines)
        return outPD


class TractCloudTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        self.test_TractCloud_import()

    def test_TractCloud_import(self):
        """Verify module imports work."""
        self.delayDisplay("Testing TractCloud imports")
        from TractCloudLib.tract_mapping import TRACT_NAMES, TRACT_CLUSTER_MAPPING
        self.assertEqual(len(TRACT_NAMES), 43)
        self.assertEqual(len(TRACT_CLUSTER_MAPPING), 43)
        self.delayDisplay("TractCloud import test passed!")
