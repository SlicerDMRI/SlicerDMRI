import json
import logging
import os
import shutil
import tempfile

import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import numpy as np


class TractCloud(ScriptedLoadableModule):
    """TractCloud: Registration-free tractography parcellation.

    Uses the tractcloud pip package to classify streamlines from whole-brain
    tractography into 42 anatomical white matter tracts.
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
identified tract, organized by anatomical category.

On first use the module installs the tractcloud package and downloads
pre-trained model weights (~50 MB). GPU is used automatically when available.
"""
        self.parent.acknowledgementText = """
Based on the TractCloud method: https://github.com/SlicerDMRI/TractCloud

Tengfei Xue, Yuqian Chen, Chaoyi Zhang, Alexandra J. Golby, Nikos Makris,
Yogesh Rathi, Weidong Cai, Fan Zhang, Lauren J. O'Donnell.
MICCAI 2023.
"""


class TractCloudWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # --- Parameters ---
        parametersCollapsible = ctk.ctkCollapsibleButton()
        parametersCollapsible.text = "Parameters"
        self.layout.addWidget(parametersCollapsible)
        parametersForm = qt.QFormLayout(parametersCollapsible)

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

        self.includeOtherCheckBox = qt.QCheckBox()
        self.includeOtherCheckBox.checked = False
        self.includeOtherCheckBox.setToolTip(
            "If checked, include an 'Other' bundle for unclassified "
            "streamlines.")
        parametersForm.addRow("Include 'Other' tract:",
                              self.includeOtherCheckBox)

        # --- Advanced ---
        advancedCollapsible = ctk.ctkCollapsibleButton()
        advancedCollapsible.text = "Advanced"
        advancedCollapsible.collapsed = True
        self.layout.addWidget(advancedCollapsible)
        advancedForm = qt.QFormLayout(advancedCollapsible)

        self.deviceCombo = qt.QComboBox()
        self.deviceCombo.addItem("Auto (GPU if available)")
        self.deviceCombo.addItem("CPU only")
        advancedForm.addRow("Device:", self.deviceCombo)

        self.batchSizeSpinBox = qt.QSpinBox()
        self.batchSizeSpinBox.minimum = 64
        self.batchSizeSpinBox.maximum = 16384
        self.batchSizeSpinBox.value = 2048
        advancedForm.addRow("Batch size:", self.batchSizeSpinBox)

        # --- Apply ---
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run TractCloud parcellation."
        self.applyButton.enabled = False
        self.layout.addWidget(self.applyButton)

        self.progressBar = qt.QProgressBar()
        self.progressBar.visible = False
        self.layout.addWidget(self.progressBar)

        self.statusLabel = qt.QLabel("")
        self.layout.addWidget(self.statusLabel)

        self.layout.addStretch(1)

        self.inputSelector.connect(
            "currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.applyButton.connect("clicked(bool)", self.onApply)
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = (
            self.inputSelector.currentNode() is not None)

    def onApply(self):
        inputNode = self.inputSelector.currentNode()
        if not inputNode:
            slicer.util.errorDisplay(
                "Please select an input FiberBundle.")
            return

        self.applyButton.enabled = False
        self.progressBar.visible = True
        self.progressBar.setValue(0)
        self.statusLabel.text = ""

        logic = TractCloudLogic()
        logic.statusCallback = self._updateStatus
        logic.progressCallback = self._updateProgress
        logic.completionCallback = self._onCompleted

        device = "cpu" if self.deviceCombo.currentIndex == 1 else "auto"
        logic.run(
            inputNode,
            includeOther=self.includeOtherCheckBox.checked,
            device=device,
            batchSize=self.batchSizeSpinBox.value,
        )
        # Keep reference so it isn't garbage collected
        self._logic = logic

    def _updateProgress(self, fraction):
        self.progressBar.setValue(int(fraction * 100))

    def _updateStatus(self, message):
        self.statusLabel.text = message
        logging.info(message)

    def _onCompleted(self, success, message):
        self.applyButton.enabled = True
        self.progressBar.visible = False
        if success:
            self.statusLabel.text = message
        else:
            slicer.util.errorDisplay(f"TractCloud failed: {message}")
            self.statusLabel.text = "Error during parcellation."


class TractCloudLogic(ScriptedLoadableModuleLogic):
    """Runs TractCloud as a QProcess subprocess."""

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.statusCallback = None
        self.progressCallback = None
        self.completionCallback = None
        self._process = None
        self._tempDir = None
        self._inputNode = None

    def _status(self, msg):
        if self.statusCallback:
            self.statusCallback(msg)

    def _progress(self, fraction):
        if self.progressCallback:
            self.progressCallback(fraction)

    def _ensureDependencies(self):
        """Install tractcloud package if needed."""
        try:
            import tractcloud
        except ImportError:
            self._status("Installing tractcloud package...")
            slicer.util.pip_install(
                "git+https://github.com/SlicerDMRI/TractCloud.git@inference-cli")
        # Verify torch is available
        try:
            import torch
        except ImportError:
            self._status("Installing PyTorch...")
            slicer.util.pip_install("torch torchvision torchaudio")

    def run(self, inputNode, includeOther=False, device="auto",
            batchSize=2048):
        """Run TractCloud parcellation via QProcess.

        The computation runs in a subprocess so Slicer remains responsive.
        Results are loaded into the scene when the process completes.
        """
        self._ensureDependencies()

        self._inputNode = inputNode
        self._tempDir = tempfile.mkdtemp(prefix="tractcloud_")

        # Save input polydata to temp file
        inputPath = os.path.join(self._tempDir, "input.vtp")
        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetFileName(inputPath)
        writer.SetInputData(inputNode.GetPolyData())
        writer.SetCompressorTypeToZLib()
        writer.Write()

        outputDir = os.path.join(self._tempDir, "output")
        self._outputDir = outputDir

        # Build command
        import sys
        pythonPath = os.path.join(
            os.path.dirname(os.path.dirname(sys.executable)),
            "bin", "PythonSlicer")
        if not os.path.exists(pythonPath):
            pythonPath = sys.executable

        args = [
            pythonPath,
            "-m", "tractcloud",
            "--input", inputPath,
            "--output-dir", outputDir,
            "--device", device,
            "--batch-size", str(batchSize),
        ]
        if includeOther:
            args.append("--include-other")

        self._status("Starting TractCloud subprocess...")
        logging.info(f"TractCloud command: {' '.join(args)}")

        self._process = qt.QProcess()
        self._process.setProcessChannelMode(
            qt.QProcess.SeparateChannels)

        # Pass environment (ensures TRACTCLOUD_DATA_DIR propagates)
        env = qt.QProcessEnvironment.systemEnvironment()
        self._process.setProcessEnvironment(env)

        self._process.readyReadStandardOutput.connect(self._onStdout)
        self._process.finished.connect(self._onFinished)
        self._process.errorOccurred.connect(self._onError)
        self._process.start(args[0], args[1:])

    def _onError(self, error):
        """Handle QProcess errors (e.g. program not found)."""
        errorMsgs = {0: "Failed to start", 1: "Crashed", 2: "Timed out",
                     4: "Write error", 3: "Read error", 5: "Unknown error"}
        msg = errorMsgs.get(error, f"Error code {error}")
        logging.error(f"TractCloud QProcess error: {msg}")
        if self.completionCallback:
            self.completionCallback(False, msg)

    def _onStdout(self):
        """Parse JSON progress lines from the subprocess."""
        while self._process.canReadLine():
            line = self._process.readLine().data().decode().strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            msgType = msg.get("type")
            if msgType == "status":
                self._status(msg.get("message", ""))
            elif msgType == "progress":
                fraction = msg.get("fraction", 0)
                self._progress(fraction)
                # Show time estimate if available
                remaining = msg.get("estimated_remaining")
                if remaining is not None and remaining > 1:
                    step = msg.get("step", "")
                    self._status(
                        f"Step {step}: {remaining:.0f}s remaining...")
            elif msgType == "result":
                totalTime = msg.get("total_time")
                timeStr = (f" in {totalTime:.1f}s"
                           if totalTime is not None else "")
                self._status(
                    f"Created {msg.get('tracts_created', '?')} tracts"
                    + timeStr)

    def _onFinished(self, exitCode, exitStatus=None):
        """Load output VTP files into the Slicer scene."""
        if exitCode != 0:
            stderr = self._process.readAllStandardError().data().decode()
            if self.completionCallback:
                self.completionCallback(False, stderr[-500:])
            self._cleanup()
            return

        self._status("Loading results into scene...")
        try:
            nodeIDs = self._loadResults()
            msg = f"Parcellation complete: {len(nodeIDs)} tracts"
            if self.completionCallback:
                self.completionCallback(True, msg)
        except Exception as e:
            if self.completionCallback:
                self.completionCallback(False, str(e))

        self._cleanup()

    def _loadResults(self):
        """Load output VTP files into MRML scene with hierarchy and colors."""
        from tractcloud.tract_mapping import TRACT_FULL_NAMES

        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        sceneItemID = shNode.GetSceneItemID()
        baseName = self._inputNode.GetName() + "_TractCloud"
        rootFolderID = shNode.CreateFolderItem(sceneItemID, baseName)

        colorNode = slicer.util.getNode("GenericColors")
        colorIndex = 1
        createdIDs = []

        # Walk the category directories
        for categoryName in sorted(os.listdir(self._outputDir)):
            catDir = os.path.join(self._outputDir, categoryName)
            if not os.path.isdir(catDir):
                continue

            vtpFiles = [f for f in os.listdir(catDir)
                        if f.endswith(".vtp")]
            if not vtpFiles:
                continue

            catFolderID = shNode.CreateFolderItem(
                rootFolderID, categoryName)

            for vtpFile in sorted(vtpFiles):
                filepath = os.path.join(catDir, vtpFile)
                nodeName = os.path.splitext(vtpFile)[0]

                node = slicer.util.loadFiberBundle(filepath)
                if node is None:
                    continue
                node.SetName(nodeName)

                # Set color
                color = [0.0, 0.0, 0.0, 0.0]
                colorNode.GetColor(colorIndex, color)
                lineDisp = node.GetLineDisplayNode()
                if lineDisp:
                    lineDisp.SetColor(color[0], color[1], color[2])
                    lineDisp.SetColorModeToSolid()
                tubeDisp = node.GetTubeDisplayNode()
                if tubeDisp:
                    tubeDisp.SetColor(color[0], color[1], color[2])
                    tubeDisp.SetColorModeToSolid()
                colorIndex += 1

                itemID = shNode.GetItemByDataNode(node)
                shNode.SetItemParent(itemID, catFolderID)
                createdIDs.append(node.GetID())

        return createdIDs

    def _cleanup(self):
        """Remove temporary directory."""
        if self._tempDir and os.path.exists(self._tempDir):
            shutil.rmtree(self._tempDir, ignore_errors=True)
            self._tempDir = None


class TractCloudTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        self.test_TractCloud_import()

    def test_TractCloud_import(self):
        self.delayDisplay("Testing tractcloud package import")
        try:
            from tractcloud.tract_mapping import TRACT_NAMES
            self.assertEqual(len(TRACT_NAMES), 43)
            self.delayDisplay("TractCloud import test passed!")
        except ImportError:
            self.delayDisplay("tractcloud package not installed (expected)")
