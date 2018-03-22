import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging


# helper class for cleaner multi-operation blocks on a single node.
class It():
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
    # output file selector
    #
    with It(ctk.ctkPathLineEdit()) as w:
      self.outputFileSelector = w
      # make a file-only, save dialog
      w.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Writable
      w.connect('currentPathChanged(const QString&)', self.reset)
      parametersFormLayout.addRow("Output File: ", self.outputFileSelector)

    with It(qt.QPushButton("Export")) as w:
      w.toolTip = "Run Export"
      w.connect('clicked(bool)', self.onExport)
      parametersFormLayout.addRow("", w)

    with It(qt.QStatusBar()) as w:
      self.statusLabel = w
      w.styleSheet = "background: lightgray"
      parametersFormLayout.addRow(w)

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
                                             self.outputFileSelector.currentPath)
      self.statusLabel.showMessage("Export succeeded!")
    except Exception as err:
      self.statusLabel.showMessage("ExportFailed: {}".format(err))
      # note: use `raise` alone here, *not* `raise err` in order to
      #       get the full trace in the log and Python interactor.
      raise

#
# TractographyExportPLYLogic
#

class TractographyExportPLYLogic(ScriptedLoadableModuleLogic):

  def exportFiberBundleToPLYPath(self, inputFiberBundle, outputFilePath):
    """
    Do the actual export
    """

    lineDisplayNode = inputFiberBundle.GetLineDisplayNode()

    if lineDisplayNode is None:
      raise Exception("No vtkMRMLFiberBundleLineDisplayNode found for node: {}".format(inputFiberBundle.GetName()))

    outputDir = os.path.dirname(outputFilePath)
    if not os.path.isdir(outputDir):
      raise Exception("Selected output directory does not exist: {}".format(outputDir))

    tuber = vtk.vtkTubeFilter()
    tuber.SetNumberOfSides(6)
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
    lookupTable.SetTableRange(0,1)

    plyWriter = vtk.vtkPLYWriter()
    plyWriter.SetInputData(triangles.GetOutput())
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
    import urllib
    downloads = (
        ('https://github.com/SlicerDMRI/DMRITestData/blob/master/Tractography/fiber_ply_export_test.vtk?raw=true', 'fiber_ply_export_test.vtk', slicer.util.loadFiberBundle),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)

    self.delayDisplay('Finished with download and loading')

    fiberNode = slicer.util.getNode(pattern="fiber_ply_export_test")
    logic = TractographyExportPLYLogic()
    logic.exportFiberBundleToPLYPath(fiberNode, os.path.join(slicer.app.temporaryPath, "fiber.ply"))

    # If it doesn't throw, it passes...
    self.delayDisplay('Test passed!')
