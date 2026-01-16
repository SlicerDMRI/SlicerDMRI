import os
import unittest
import vtk, qt, ctk, slicer, numpy
from slicer.ScriptedLoadableModule import *
import logging

#
# Tractography_ROI_cutting
#

class Tractography_ROI_cutting(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Tractography_ROI_cutting" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# Tractography_ROI_cuttingWidget
#

class Tractography_ROI_cuttingWidget(ScriptedLoadableModuleWidget):
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
    self.fiberSelector = slicer.qMRMLNodeComboBox()
    self.fiberSelector.nodeTypes = ["vtkMRMLFiberBundleNode"]
    self.fiberSelector.selectNodeUponCreation = True
    self.fiberSelector.addEnabled = False
    self.fiberSelector.removeEnabled = False
    self.fiberSelector.noneEnabled = False
    self.fiberSelector.showHidden = False
    self.fiberSelector.showChildNodeTypes = False
    self.fiberSelector.setMRMLScene( slicer.mrmlScene )
    self.fiberSelector.setToolTip( "Pick the fiber bundle to be converted." )
    parametersFormLayout.addRow("Input Fiber Bundle:", self.fiberSelector)

    #
    # input region label map selector
    #
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.labelSelector.selectNodeUponCreation = True
    self.labelSelector.addEnabled = False
    self.labelSelector.removeEnabled = False
    self.labelSelector.noneEnabled = False
    self.labelSelector.showHidden = False
    self.labelSelector.showChildNodeTypes = False
    self.labelSelector.setMRMLScene( slicer.mrmlScene )
    self.labelSelector.setToolTip( "Pick the mask to be converted." )
    parametersFormLayout.addRow("Selection Region Label Map: ", self.labelSelector)

    #
    # inclusion label1
    #
    self.labelValue1 = qt.QSpinBox(parametersCollapsibleButton)
    self.labelValue1.setToolTip( "The numerical value for the rasterized fiber label." )
    self.labelValue1.setValue(1)
    parametersFormLayout.addRow("inclusion label1", self.labelValue1)

    #
    # inclusion label2
    #
    self.labelValue2 = qt.QSpinBox(parametersCollapsibleButton)
    self.labelValue2.setToolTip( "The numerical value for the rasterized fiber label." )
    self.labelValue2.setValue(2)
    parametersFormLayout.addRow("inclusion label2", self.labelValue2)

    #
    # output fiber bundle selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLFiberBundleNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output Fiber Bundle: ", self.outputSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)
    
    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.labelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # 'Advanced' collapsible button
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    advancedCollapsibleButton.collapsed = True
    self.layout.addWidget(advancedCollapsibleButton)
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)

    self.samplingDistance = ctk.ctkDoubleSpinBox()
    self.samplingDistance.minimum = 0.01
    self.samplingDistance.maximum = 5.0
    self.samplingDistance.decimals = 2
    self.samplingDistance.singleStep = 0.1
    self.samplingDistance.value = 0.1
    self.samplingDistance.decimalsOption = (ctk.ctkDoubleSpinBox.ReplaceDecimals |
                                                    ctk.ctkDoubleSpinBox.DecimalsByKey)
    advancedFormLayout.addRow("Sampling distance (mm)", self.samplingDistance)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.labelSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    labelNode = self.labelSelector.currentNode()
    fiberNode = self.fiberSelector.currentNode()
    outputNode = self.outputSelector.currentNode()

    logic = Tractography_ROI_cuttingLogic()
    #enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    #imageThreshold = self.imageThresholdSliderWidget.value
    logic.run(labelNode, fiberNode, outputNode, self.labelValue1.value, self.labelValue2.value, self.samplingDistance.value)

#
# Tractography_ROI_cuttingLogic
#

class Tractography_ROI_cuttingLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
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

  def run(self, labelNode, fiberNode, outputNode, labelValue1, labelValue2, samplingDistance = 0.1):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(fiberNode, outputNode):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # load region label map
    rasToIJK = vtk.vtkMatrix4x4()
    labelNode.GetRASToIJKMatrix(rasToIJK)
    labelArray = slicer.util.array(labelNode.GetID())

    # load input fiber bundle
    inpd = fiberNode.GetPolyData()
    inpoints = inpd.GetPoints()
    inpointdata = inpd.GetPointData()
    incelldata = inpd.GetCellData()

    # create output fiber bundle
    outpd = vtk.vtkPolyData()
    outlines = vtk.vtkCellArray()
    outpoints = vtk.vtkPoints()
    
    resampler = vtk.vtkPolyDataPointSampler()
    resampler.GenerateEdgePointsOn()
    resampler.GenerateVertexPointsOff()
    resampler.GenerateInteriorPointsOff()
    resampler.GenerateVerticesOff()
    resampler.SetDistance(samplingDistance)

    if incelldata.GetNumberOfArrays() > 0:
      cell_data_array_indices = range(incelldata.GetNumberOfArrays())
      for idx in cell_data_array_indices:
          array = incelldata.GetArray(idx)
          dtype = array.GetDataType()

          if dtype == 10:
             out_array = vtk.vtkFloatArray()
          elif dtype == 6:
             out_array = vtk.vtkIntArray()
          elif dtype == 3:
             out_array = vtk.vtkUnsignedCharArray()
          else:
             out_array = vtk.vtkFloatArray()
          out_array.SetNumberOfComponents(array.GetNumberOfComponents())
          out_array.SetName(array.GetName())

          outpd.GetCellData().AddArray(out_array)

    if inpointdata.GetNumberOfArrays() > 0:
        point_data_array_indices = range(inpointdata.GetNumberOfArrays())
        for idx in point_data_array_indices:
            array = inpointdata.GetArray(idx)
            out_array = vtk.vtkFloatArray()
            out_array.SetNumberOfComponents(array.GetNumberOfComponents())
            out_array.SetName(array.GetName())

            outpd.GetPointData().AddArray(out_array)

    inpd.GetLines().InitTraversal()
    outlines.InitTraversal()

    for lidx in range(0, inpd.GetNumberOfLines()):
      ptids = vtk.vtkIdList()
      inpd.GetLines().GetNextCell(ptids)

      cellptids = vtk.vtkIdList()

      switch1 = 0
      switch2 = 0

      #load the infomation after resample
      tmpPd = vtk.vtkPolyData()
      tmpPoints = vtk.vtkPoints()
      tmpCellPtIds = vtk.vtkIdList()
      tmpLines =  vtk.vtkCellArray()
      
      for pidx in range(0, ptids.GetNumberOfIds()):
        point = inpoints.GetPoint(ptids.GetId(pidx))
        idx_ = tmpPoints.InsertNextPoint(point)
        tmpCellPtIds.InsertNextId(idx_)

      tmpLines.InsertNextCell(tmpCellPtIds)

      tmpPd.SetLines(tmpLines)
      tmpPd.SetPoints(tmpPoints)

      if (vtk.vtkVersion().GetVTKMajorVersion() >= 6.0):
          resampler.SetInputData(tmpPd)
      else:
          resampler.SetInput(tmpPd)

      resampler.Update()

      sampledCellPts = resampler.GetOutput().GetPoints()
      sampledNpts = resampler.GetOutput().GetNumberOfPoints()

      #judge weather the fiber go through both ROI
      for pidx in range(0, sampledNpts):
        point = sampledCellPts.GetPoint(pidx)
        point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
        ijk = [int(round(element)) for element in point_ijk]
        ijk.reverse()
        if labelArray[tuple(ijk)] == labelValue1:
          switch1 = 1
        if labelArray[tuple(ijk)] == labelValue2:
          switch2 = 1

      #In each fiber that needs to be kept, find the first and 
      #the last point that need to kept in the resampled data.
      if (switch1 ==1 and switch2 == 1):
        for pidx in range(0, sampledNpts):
          point = sampledCellPts.GetPoint(pidx)
          point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
          ijk = [int(round(element)) for element in point_ijk]
          ijk.reverse()
          if (labelArray[tuple(ijk)] == labelValue1 or labelArray[tuple(ijk)] == labelValue2):
            line_RASbegin = point
            break

        for pidx in range(sampledNpts - 1, -1, -1):
          point = sampledCellPts.GetPoint(pidx)
          point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
          ijk = [int(round(element)) for element in point_ijk]
          ijk.reverse()
          if (labelArray[tuple(ijk)] == labelValue1 or labelArray[tuple(ijk)] == labelValue2):
            line_RASend = point
            break

        origin_RAS = numpy.zeros([ptids.GetNumberOfIds(),3])
        for pidx in range(0, ptids.GetNumberOfIds()):
          origin_RAS[pidx, :] = inpoints.GetPoint(ptids.GetId(pidx))
        
        distance_square1 = numpy.sum(numpy.asarray(line_RASbegin - origin_RAS)**2, axis=1)
        distance_square2 = numpy.sum(numpy.asarray(line_RASend - origin_RAS)**2, axis=1)

        #In the original data, find the two points which are cloest to the 
        #first and the end point found in resampled data. Then keep the
        #points between them.
        line_begin = numpy.argmin(distance_square1)
        line_end = numpy.argmin(distance_square2)

        for pidx in range(0, ptids.GetNumberOfIds()):
          point = inpoints.GetPoint(ptids.GetId(pidx))
          if (pidx >= line_begin and pidx <= line_end):
            idx_ = outpoints.InsertNextPoint(point)
            cellptids.InsertNextId(idx_)
            if inpointdata.GetNumberOfArrays() > 0:
              for idx in point_data_array_indices:
                array = inpointdata.GetArray(idx)
                outpd.GetPointData().GetArray(idx).InsertNextTuple(array.GetTuple(ptids.GetId(pidx)))

        outlines.InsertNextCell(cellptids)

      if incelldata.GetNumberOfArrays() > 0:
        for idx in cell_data_array_indices:
          array = incelldata.GetArray(idx)
          out_array = outpd.GetCellData().GetArray(idx)
          out_array.InsertNextTuple(array.GetTuple(lidx))
    
    outpd.SetLines(outlines)
    outpd.SetPoints(outpoints)

    outputNode.SetAndObservePolyData(outpd)

    print 'Line before removal:', inpd.GetNumberOfLines(), ', after removal:', outpd.GetNumberOfLines()

    logging.info('Done!')

    return True


class Tractography_ROI_cuttingTest(ScriptedLoadableModuleTest):
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
    self.test_Tractography_ROI_cutting1()

  def test_Tractography_ROI_cutting1(self):
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
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
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

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = Tractography_ROI_cuttingLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
