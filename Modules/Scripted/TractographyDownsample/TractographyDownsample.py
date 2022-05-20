from __future__ import division
import os
import sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

if sys.version_info[0] == 2:
  range = xrange

#
# TractographyDownsample
#

class TractographyDownsample(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Tractography Downsample"
    self.parent.categories = ["Diffusion.Utilities"]
    self.parent.dependencies = []
    self.parent.contributors = ["Lauren O'Donnell (BWH / HMS)"]
    self.parent.helpText = """
This module downsamples large tractography datasets by removing excess points or fibers (polylines) as requested.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Lauren O'Donnell, BWH/HMS, and was partially funded by NIH grant U01-CA199459.
""" # replace with organization, grant and thanks.

#
# TractographyDownsampleWidget
#

class TractographyDownsampleWidget(ScriptedLoadableModuleWidget):
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
    # input fiber bundle selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLFiberBundleNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the tractography data to use for input." )
    parametersFormLayout.addRow("Input FiberBundle: ", self.inputSelector)

    #
    # output fiber bundle selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLFiberBundleNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.renameEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output FiberBundle: ", self.outputSelector)

    #
    # step size value
    #
    #self.fiberStepSizeSliderWidget = ctk.ctkSliderWidget()
    #self.fiberStepSizeSliderWidget.singleStep = 0.1
    #self.fiberStepSizeSliderWidget.minimum = 0
    #self.fiberStepSizeSliderWidget.maximum = 100
    #self.fiberStepSizeSliderWidget.value = 2
    #self.fiberStepSizeSliderWidget.setToolTip("Set step size value (in mm) for the output tractography. Points will be removed along the fiber such that the output step size is approximately this value (max possible step less than or equal to this value).")
    #parametersFormLayout.addRow("Output step size", self.fiberStepSizeSliderWidget)

    # step size output goal value
    self.fiberStepSizeWidget = qt.QDoubleSpinBox()
    self.fiberStepSizeWidget.singleStep = 0.1
    self.fiberStepSizeWidget.setValue(2.0)
    self.fiberStepSizeWidget.setToolTip("Set step size value (in mm) for the output tractography. Points will be removed along the fiber such that the output step size is approximately this value (max possible step less than or equal to this value).")
    parametersFormLayout.addRow("Output step size (mm):", self.fiberStepSizeWidget)

    # fiber percentage output value
    self.fiberPercentageWidget = qt.QDoubleSpinBox()
    self.fiberPercentageWidget.singleStep = 0.1
    self.fiberPercentageWidget.maximum = 100.0
    self.fiberPercentageWidget.minimum = 0.01
    self.fiberPercentageWidget.setValue(50)
    self.fiberPercentageWidget.setToolTip("Set percentage of input fibers to retain in output.")
    parametersFormLayout.addRow("Output fiber percent:", self.fiberPercentageWidget)

    # fiber minimum points to keep the fiber output value
    self.fiberMinimumPointsWidget = qt.QSpinBox()
    self.fiberMinimumPointsWidget.singleStep = 0.1
    self.fiberMinimumPointsWidget.setValue(3)
    self.fiberMinimumPointsWidget.setToolTip("Set minimum length of input fibers (in points) to retain in output. This is best used as a sanity check to remove any very short fibers where the algorithm was not successful in tracing. For example, a minimum length of 3 points means that any spurious fibers with only 1 or 2 points will be removed.")
    parametersFormLayout.addRow("Output min points:", self.fiberMinimumPointsWidget)

    # fiber minimum length to keep the fiber
    self.fiberMinimumLengthWidget = qt.QDoubleSpinBox()
    self.fiberMinimumLengthWidget.singleStep = 1
    self.fiberMinimumLengthWidget.maximum = 250.0
    self.fiberMinimumLengthWidget.minimum = 0.01
    self.fiberMinimumLengthWidget.setValue(10)
    self.fiberMinimumLengthWidget.setToolTip("Set minimum length of input fibers (in mm) to retain in output. For example, a minimum length of 10mm means that any fibers under 10mm in length will be removed.")
    parametersFormLayout.addRow("Output min length (mm):", self.fiberMinimumLengthWidget)

    # fiber maximum length to keep the fiber
    self.fiberMaximumLengthWidget = qt.QDoubleSpinBox()
    self.fiberMaximumLengthWidget.singleStep = 0.1
    self.fiberMaximumLengthWidget.maximum = 250.0
    self.fiberMaximumLengthWidget.minimum = 0.01
    self.fiberMaximumLengthWidget.setValue(200)
    self.fiberMaximumLengthWidget.setToolTip("Set maximum length of input fibers (in mm) to retain in output. For example, a maximum length of 35mm means that any fibers over 35mm in length will be removed. This is useful to clean any long artifactual fibers from a particular bundle.")
    parametersFormLayout.addRow("Output max length (mm):", self.fiberMaximumLengthWidget)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

    #
    # Advanced Area
    #
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    advancedCollapsibleButton.collapsed = True
    self.layout.addWidget(advancedCollapsibleButton)

    # Layout within the dummy collapsible button
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)

    #
    # Apply Button
    #
    self.advancedApplyButton = qt.QPushButton("Apply to ALL tractography (fiber bundles)")
    self.advancedApplyButton.toolTip = "Downsample ALL fiber bundles in the Slicer scene. Be careful when saving the scene to choose a NEW directory to avoid over-writing your input data."
    self.advancedApplyButton.enabled = True
    advancedFormLayout.addRow(self.advancedApplyButton)

    # connections
    self.advancedApplyButton.connect('clicked(bool)', self.onAdvancedApplyButton)


  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = TractographyDownsampleLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    fiberStepSize = self.fiberStepSizeWidget.value
    fiberPercentage = self.fiberPercentageWidget.value
    fiberMinPoints = self.fiberMinimumPointsWidget.value
    fiberMinLength = self.fiberMinimumLengthWidget.value
    fiberMaxLength = self.fiberMaximumLengthWidget.value
    logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode(), fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength, enableScreenshotsFlag)

  def onAdvancedApplyButton(self):
    logic = TractographyDownsampleLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    fiberStepSize = self.fiberStepSizeWidget.value
    fiberPercentage = self.fiberPercentageWidget.value
    fiberMinPoints = self.fiberMinimumPointsWidget.value
    fiberMinLength = self.fiberMinimumLengthWidget.value
    fiberMaxLength = self.fiberMaximumLengthWidget.value
    logic.runAdvanced(fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength, enableScreenshotsFlag)

#
# TractographyDownsampleLogic
#

class TractographyDownsampleLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasFiberBundleData(self,fiberBundleNode):
    """This is an example logic method that
    returns true if the passed in fiberBundle
    node has valid image data
    """
    if not fiberBundleNode:
      logging.debug('hasFiberBundleData failed: no fiberBundle node')
      return False
    if fiberBundleNode.GetPolyData() is None:
      logging.debug('hasFiberBundleData failed: no polydata in fiberBundle node')
      return False
    return True

  def isValidInputOutputData(self, inputFiberBundleNode, outputFiberBundleNode):
    """Validates if the output is not the same as input
    """
    if not inputFiberBundleNode:
      logging.debug('isValidInputOutputData failed: no input fiberBundle node defined')
      return False
    if not outputFiberBundleNode:
      logging.debug('isValidInputOutputData failed: no output fiberBundle node defined')
      return False
    if inputFiberBundleNode.GetID()==outputFiberBundleNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output fiberBundle is the same. Create a new fiberBundle for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qimage = ctk.ctkWidgetsUtils.grabWidget(widget)
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def computeStepSize(self, inpd, minpts=5):
    """
    Estimate step size between consecutive points along fiber.
    """

    # measure step size (using first fiber (polyline) that has >=5 points)
    # minpts threshold is for robust estimation if polydata has some
    # very short lines.
    cell_idx = 0
    ptids = vtk.vtkIdList()
    inpoints = inpd.GetPoints()
    inpd.GetLines().InitTraversal()
    while (ptids.GetNumberOfIds() < minpts) & (cell_idx < inpd.GetNumberOfLines()):
        inpd.GetLines().GetNextCell(ptids)
        ##    inpd.GetLines().GetCell(cell_idx, ptids)
        ## the GetCell function is not wrapped in Canopy python-vtk
        cell_idx += 1
    # make sure we have some points along this fiber
    # In case all fibers in the brain are really short, treat it the same as no fibers.
    if ptids.GetNumberOfIds() < 5:
        return 0

    # Use points from the middle of the fiber to estimate step length.
    # This is because the step size may vary near endpoints (in order to include
    # endpoints when downsampling the fiber to reduce file size).
    step_size = 0.0
    count = 0.0
    for ptidx in range(1, ptids.GetNumberOfIds()-1):
        point0 = inpoints.GetPoint(ptids.GetId(ptidx))
        point1 = inpoints.GetPoint(ptids.GetId(ptidx + 1))
        step_size += np.sqrt(np.sum(np.power(np.subtract(point0, point1), 2)))
        count += 1
    step_size = step_size / count
    return step_size

  def downsampleFibers(self, inpd, outpd, outstep, outpercent, outminpts, outminlen, outmaxlen):
    """
    Remove points from inpd to create outpd with step size approximately outstep.
    Output step size will be the greatest multiple of input fiber
    step size that is less than outstep. So if input step size is 1 and output
    requested step size is 2.5, then final output step size will be 2.
    All endpoints are retained.
    """
    # compute input step size
    instep = self.computeStepSize(inpd)
    logging.info('Input Step Size:')
    logging.info(instep)

    # keep every nth point
    n = np.floor(outstep/instep)
    # No interpolation of points: if outstep is smaller than
    # instep keep all points
    if outstep < instep:
      n = 1

    # keep a random sample of outpercent of fibers
    # all possible fiber indices
    findices = list(range(0, inpd.GetNumberOfLines()))
    # now find the size of the desired subset of these indices
    outpercent = np.divide(outpercent,100.0)
    nkeep = int(np.multiply(inpd.GetNumberOfLines(), outpercent))
    # randomly permute instead of selecting, so that below we can
    # try to keep say the desired random 50% of fibers even though
    # we remove some based on length or number of points
    findices = np.random.permutation(findices)
    #findices = np.random.choice(findices, nkeep, replace=False)
    # sort this so the order corresponds to the original in case desired
    #findices = np.sort(findices)

    # figure out minimum number of points to keep
    # two input variables affect this as users may want to set this
    # in number of points, for sanity check, or in mm to actually
    # modify tract according to anatomical length knowledge
    minpts = int(np.floor(np.maximum(outminpts, np.divide(outminlen, instep))))
    logging.info('Minimum points to retain fiber:')
    logging.info(minpts)
    # figure out maximum number of points to keep
    maxpts = int(np.divide(outmaxlen, instep))
    logging.info('Maximum points to retain fiber:')
    logging.info(maxpts)

    # output and temporary objects
    outlines = vtk.vtkCellArray()
    outlines.InitTraversal()
    outpoints = vtk.vtkPoints()
    ptids = vtk.vtkIdList()

    # loop over all lines, inserting into output only
    # the lines (fibers) and points to be kept
    kept = 0
    for lidx in findices:
        # here we assume this is a fiber bundle in Slicer and only has polylines
        inpd.GetCellPoints(lidx, ptids)
        num_points = ptids.GetNumberOfIds()
        # if we keep this line (fiber)
        if (num_points >= minpts) & (num_points <= maxpts):
            # insert kept points into point array and into line array
            keptptids = vtk.vtkIdList()
            for pidx in range(0, num_points):
                # we keep this point if it is the nth or the endpoint
                if (np.mod(pidx,n) == 0) | (pidx == num_points -1):
                    point = inpd.GetPoints().GetPoint(ptids.GetId(pidx))
                    idx = outpoints.InsertNextPoint(point)
                    keptptids.InsertNextId(idx)
            outlines.InsertNextCell(keptptids)
            kept = kept + 1
            # If we have reached the desired percentage of fibers stop adding more.
            if kept == nkeep:
              break

    # put data into output polydata
    outpd.SetLines(outlines)
    outpd.SetPoints(outpoints)

  def run(self, inputFiberBundle, outputFiberBundle, fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength, enableScreenshots=0, advanced=0):
    """
    Run the actual algorithm
    """

    if not advanced:
      if not self.isValidInputOutputData(inputFiberBundle, outputFiberBundle):
        slicer.util.errorDisplay('Input fiberBundle is the same as output fiberBundle. Choose a different output fiberBundle.')
        return False

    logging.info('Processing started')

    # Compute the thresholded output fiberBundle using the Threshold Scalar FiberBundle CLI module
    #cliParams = {'InputFiberBundle': inputFiberBundle.GetID(), 'OutputFiberBundle': outputFiberBundle.GetID(), 'ThresholdValue' : fiberStepSize, 'ThresholdType' : 'Above'}
    #cliNode = slicer.cli.run(slicer.modules.thresholdscalarfiberBundle, None, cliParams, wait_for_completion=True)

    # access input data object
    pd = inputFiberBundle.GetPolyData()
    # create a new polydata to hold the output
    outpd = vtk.vtkPolyData()

    # log information about input
    logging.info('Input Fiber Bundle Stats:')
    logging.info(inputFiberBundle.GetName())
    logging.info('Input Number of Fibers:')
    logging.info(pd.GetNumberOfLines())
    logging.info('Input Number of Points:')
    logging.info(pd.GetNumberOfPoints())

    # call the main function that does the processing
    self.downsampleFibers(pd, outpd, fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength)

    # log information about output
    logging.info('Output Fiber Bundle Stats:')
    logging.info(outputFiberBundle.GetName())
    logging.info('Output Number of Fibers:')
    logging.info(outpd.GetNumberOfLines())
    logging.info('Output Number of Points:')
    logging.info(outpd.GetNumberOfPoints())
    logging.info('Output Step Size:')
    logging.info(self.computeStepSize(outpd))

    # register the output data with the scene node to view it
    # and to increment reference count to preserve output
    outputFiberBundle.SetAndObservePolyData(outpd)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('TractographyDownsampleTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True

  def runAdvanced(self, fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    nodeCollection = slicer.mrmlScene.GetNodesByClass("vtkMRMLFiberBundleNode")
    nodes = [nodeCollection.GetItemAsObject(i) for i in range(0, nodeCollection.GetNumberOfItems())]

    if not nodes:
      slicer.util.errorDisplay('No input fiberBundles in scene. Please load fiber bundles first.')
      return False

    logging.info('ADVANCED Processing started. Downsampling all fiber bundles in Slicer scene.')
    logging.info(nodes)
    for node in nodes:
      self.run(node, node, fiberStepSize, fiberPercentage, fiberMinPoints, fiberMinLength, fiberMaxLength, enableScreenshots=0, advanced=1)
    logging.info('ADVANCED Processing completed')

    return True

class TractographyDownsampleTest(ScriptedLoadableModuleTest):
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
    # Uncomment when we have test data for download and this function is done
    self.test_TractographyDownsample1()
    self.test_TractographyDownsample2()

  def test_TractographyDownsample1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
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
      self.delayDisplay('Finished with download and loading of %s' % str(fileNames))

    fiberBundleNode = slicer.util.getNode(pattern="fiber_ply_export_test")
    logic = TractographyDownsampleLogic()
    self.assertIsNotNone( logic.hasFiberBundleData(fiberBundleNode) )
    self.delayDisplay('Test test_TractographyDownsample1 passed!')

  def test_TractographyDownsample2(self):
    logging.info('Running test_TractographyDownsample2')
    # create some polydata with some lines in it
    pd = vtk.vtkPolyData()
    self.makeTestData(pd)
    # create a new polydata to hold the output
    outpd = vtk.vtkPolyData()
    logic = TractographyDownsampleLogic()
    # this should not change this particular pd
    logging.info('TEST1')
    logic.downsampleFibers(pd, outpd, 1, 100, 1, 1, 300)
    l1 = pd.GetNumberOfLines()
    l2 = outpd.GetNumberOfLines()
    p1 = pd.GetNumberOfPoints()
    p2 = outpd.GetNumberOfPoints()
    logging.info('Input/Output numbers of lines %d / %d' % (l1,l2))
    logging.info('Input/Output numbers of points %d / %d' % (p1,p2))
    if l1 == l2:
      logging.info('TEST 1 synthetic data passed, number of lines is equal')
    else:
      logging.info('TEST 1 synthetic data failed, number of lines not equal')
    # this*should* change this particular pd by making step size larger
    # to have fewer output points
    logging.info('TEST2')
    logic.downsampleFibers(pd, outpd, 20, 100, 1, 1, 300)
    l1 = pd.GetNumberOfLines()
    l2 = outpd.GetNumberOfLines()
    p1 = pd.GetNumberOfPoints()
    p2 = outpd.GetNumberOfPoints()
    logging.info('Input/Output numbers of lines %d / %d' % (l1,l2))
    logging.info('Input/Output numbers of points %d / %d' % (p1,p2))
    if p1 > p2:
      logging.info('TEST2 synthetic data passed, number of points is reduced')
    else:
      logging.info('TEST 2 synthetic data failed, number of points is not reduced')

    logging.info('Finished test_TractographyDownsample2')

  def makeTestData(self, pd):
    delta = [3, 3, 3]
    start = [0, 20, 40, 60]

    data = list()
    for lidx in range(4):
          pts = list()
          for pidx in range(5):
            pts.append([start[lidx]+delta[0]*pidx, start[lidx]+delta[1]*pidx, start[lidx]+delta[2]*pidx])
          data.append(pts)

    lines = vtk.vtkCellArray()
    lines.InitTraversal()
    points = vtk.vtkPoints()

    for lidx in range(4):
            ptids = vtk.vtkIdList()
            for pidx in range(5):
                idx = points.InsertNextPoint(data[lidx][pidx])
                ptids.InsertNextId(idx)
            lines.InsertNextCell(ptids)

    #pd = vtk.vtkPolyData()
    pd.SetLines(lines)
    pd.SetPoints(points)

    #w=vtk.vtkPolyDataWriter()
    #w.SetInputDataObject(pd)
    #w.SetFileName('TEST1234.vtk')
    #w.Write()
    #return pd
