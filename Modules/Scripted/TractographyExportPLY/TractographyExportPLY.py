import os
import unittest
import vtk, qt, ctk, slicer
import numpy as np
from slicer.ScriptedLoadableModule import *
import logging


# helper class for cleaner multi-operation blocks on a single node.
class It(object):
  def __init__(self, node): self.node = node
  def __enter__(self): return self.node
  def __exit__(self, type, value, traceback): return False

#
# TractographyExportPLY
#

class TractographyExportPLY(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Export tractography to PLY (mesh)"
    self.parent.categories = ["Diffusion.Import and Export"]
    self.parent.dependencies = []
    self.parent.contributors = ["Steve Pieper (Isomics, Inc.), Andras Lasso (Queen's University), Isaiah Norton (BWH)"]
    self.parent.helpText = """
This module allows to export a tractography FiberBundleNode to an PLY or OBJ file for use with mesh editing/printing software.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
Code updates and modularization by Andras Lasso and Isaiah Norton.
"""

#
# TractographyExportPLYWidget
#

class TractographyExportPLYWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    with It(slicer.qMRMLNodeComboBox()) as w:
      self.inputSelector = w
      w.nodeTypes = ["vtkMRMLFiberBundleNode"]
      w.selectNodeUponCreation = True
      w.addEnabled = False
      w.removeEnabled = False
      w.noneEnabled = False
      w.showHidden = False
      w.showChildNodeTypes = False
      w.setMRMLScene( slicer.mrmlScene )
      w.setToolTip( "Pick the fiber bundle to export." )
      parametersFormLayout.addRow("Input FiberBundleNode: ", self.inputSelector)


    #
    # tube radius controller
    #
    with It(ctk.ctkSliderWidget()) as w:
      self.radiusSelector = w
      w.minimum = 0.1
      w.maximum = 20.0
      w.singleStep = 0.1
      w.setToolTip("Select radius for output tubes")
      parametersFormLayout.addRow("Tube radius: ", self.radiusSelector)


    with It(ctk.ctkSliderWidget()) as w:
      self.numSidesSelector = w
      w.value = 6
      w.decimals = 0
      w.minimum = 3
      w.maximum = 20
      w.singleStep = 1
      w.pageStep = 1
      w.setToolTip("Select number of sides for output tube: higher number will look nicer, but will take more memory and time to export.")
      parametersFormLayout.addRow("Number of sides: ", self.numSidesSelector)

    #
    # use native scalar range 
    #
    with It(qt.QCheckBox()) as w:
      self.nativeRangeCheckbox = w
      w.checked = True
      w.setToolTip("Checked: set the scalar range of the exported color table to match the scalar range of the selected node. Otherwise, the range will be set to [0,1].")
      parametersFormLayout.addRow("Restrict scalar range", w)

    #
    # output file selector, export button, and status frame
    #
    with It(ctk.ctkPathLineEdit()) as w:
      self.outputFileSelector = w
      # make a file-only, save dialog
      w.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Writable
      w.connect('currentPathChanged(const QString&)', self.reset)
      parametersFormLayout.addRow("Output File: ", self.outputFileSelector)

    with It(qt.QPushButton("Export")) as w:
      self.exportButton = w
      w.toolTip = "Run Export"
      w.styleSheet = "background: lightgray"
      w.connect('clicked(bool)', self.onExport)
      parametersFormLayout.addRow("", w)

    with It(qt.QStatusBar()) as w:
      self.statusLabel = w
      w.setToolTip("CLI status")
      w.styleSheet = "background: lightgray"
      parametersFormLayout.addRow("Status: ", w)

    # Add vertical spacer
    self.layout.addStretch(1)

  def reset(self, _msg):
    self.statusLabel.showMessage("")

  def onExport(self):
    self.statusLabel.showMessage("")
    logic = TractographyExportPLYLogic()

    res = False
    try:
      res = logic.exportFiberBundleToPLYPath(self.inputSelector.currentNode(),
                                             self.outputFileSelector.currentPath,
                                             radius = self.radiusSelector.value,
                                             number_of_sides = self.numSidesSelector.value,
                                             native_scalar_range = self.nativeRangeCheckbox.checked)
      self.statusLabel.showMessage("Export succeeded!")
    except Exception as err:
      self.statusLabel.showMessage(f"ExportFailed: {err}")
      # note: use `raise` alone here, *not* `raise err` in order to
      #       get the full trace in the log and Python interactor.
      raise

#
# TractographyExportPLYLogic
#

class TractographyExportPLYLogic(ScriptedLoadableModuleLogic):

  def exportFiberBundleToPLYPath(self, inputFiberBundle, outputFilePath, radius = 0.5, number_of_sides = 6, native_scalar_range = False, outputCoordinateSystem = None):
    """
    Export fiber bundle as colored tubes into PLY file.
    outputCoordinateSystem: LPS or RAS. Default is LPS to match the most commonly image coordinate system.
    """

    if outputCoordinateSystem is None:
        outputCoordinateSystem = "LPS"

    if not float(number_of_sides).is_integer():
        import warnings
        warnings.warn(f"Attempted inexact conversion for non-integer number_of_sides {number_of_sides}. This should never happen.")

    lineDisplayNode = inputFiberBundle.GetLineDisplayNode()

    if lineDisplayNode is None:
      raise Exception(f"No vtkMRMLFiberBundleLineDisplayNode found for node: {inputFiberBundle.GetName()}")

    outputDir = os.path.dirname(outputFilePath)
    if not os.path.isdir(outputDir):
      raise Exception(f"Selected output directory does not exist: {outputDir}")

    tuber = vtk.vtkTubeFilter()
    tuber.SetNumberOfSides(int(number_of_sides))
    tuber.SetRadius(radius)
    tuber.SetInputData(lineDisplayNode.GetOutputPolyData())
    tuber.Update()
    tubes = tuber.GetOutputDataObject(0)
    scalars = tubes.GetPointData().GetArray(0)
    scalars.SetName("scalars")

    triangles = vtk.vtkTriangleFilter()
    triangles.SetInputData(tubes)
    triangles.Update()

    colorNode = lineDisplayNode.GetColorNode()
    lookupTable = vtk.vtkLookupTable()
    lookupTable.DeepCopy(colorNode.GetLookupTable())
    if native_scalar_range:
      scalarRange = lineDisplayNode.GetScalarRange()
      lookupTable.SetTableRange(scalarRange[0], scalarRange[1])
    else:
      lookupTable.SetTableRange(0,1)

    plyWriter = vtk.vtkPLYWriter()
    if outputCoordinateSystem == "RAS":
        plyWriter.SetInputData(triangles.GetOutput())
    elif outputCoordinateSystem == "LPS":
        transformRasToLps = vtk.vtkTransformPolyDataFilter()
        rasToLps = vtk.vtkTransform()
        rasToLps.Scale(-1, -1, 1)
        transformRasToLps.SetTransform(rasToLps)
        transformRasToLps.SetInputData(triangles.GetOutput())
        plyWriter.SetInputConnection(transformRasToLps.GetOutputPort())
    else:
        raise RuntimeError("Invalid output coordinate system")

    # Save coordinate system information in the file header
    # (It allows reading of the 
    plyWriter.AddComment(f"3D Slicer output. SPACE={outputCoordinateSystem}")

    if lineDisplayNode.GetColorMode() == lineDisplayNode.colorModeSolid:
        # for solid colors we need to set uniform mode in the exporter,
        # to avoid coloring by the last-used scalar array
        plyWriter.SetColorModeToUniformPointColor()
        color = np.array(np.multiply(lineDisplayNode.GetColor(), 255),
                         dtype=np.uint8) # range clamp
        plyWriter.SetColor(color[0], color[1], color[2])
    else:
        plyWriter.SetLookupTable(lookupTable)
        plyWriter.SetArrayName("scalars")

    plyWriter.SetFileName(outputFilePath)

    if (plyWriter.Write() == 0):
      raise Exception("vtkPLYWriter return status: failed")

    return True


class TractographyExportPLYTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_TractographyExportPLY1()

  def test_TractographyExportPLY1(self):
    self.delayDisplay("Starting the test")
    try:
      downloads = (
          ('fiber_ply_export_test', 'fiber_ply_export_test.vtk', 'https://github.com/SlicerDMRI/DMRITestData/blob/master/Tractography/fiber_ply_export_test.vtk?raw=true', 'FiberBundleFile'),
          )

      import SampleData
      for nodeNames, fileNames, uris, loadFileTypes  in downloads:
        SampleData.downloadFromURL(
          nodeNames=nodeNames,
          fileNames=fileNames,
          uris=uris,
          loadFileTypes=loadFileTypes
          )
        self.delayDisplay(f'Finished with download and loading of {fileNames}')

      # logic
      outputPath = os.path.join(slicer.app.temporaryPath, "fiber.ply")
      fiberNode = slicer.util.getNode(pattern="fiber_ply_export_test")
      logic = TractographyExportPLYLogic()
      logic.exportFiberBundleToPLYPath(fiberNode, outputPath, )

      if not slicer.util.loadModel(outputPath):
        raise Exception(f"Failed to load expected output PLY file: {outputPath}")

      # gui
      outputPath2 = os.path.join(slicer.app.temporaryPath, "fiber2.ply")
      widget = slicer.modules.TractographyExportPLYWidget
      widget.inputSelector.setCurrentNode(fiberNode)
      widget.outputFileSelector.currentPath = outputPath2
      widget.exportButton.click()

      if not slicer.util.loadModel(outputPath2):
        raise Exception(f"Failed to load expected output PLY file: {outputPath2}")

      # If it doesn't throw, it passes...
      self.delayDisplay('Test passed!')

    except Exception as e:
      import traceback
      traceback.print_exc()
      self.delayDisplay(f"Test caused exception!\n"{str(e)}")


