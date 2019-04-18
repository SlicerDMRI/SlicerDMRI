import os
import time
import unittest
import vtk, qt, ctk, slicer
import EditorLib
from EditorLib.EditUtil import EditUtil

#
# NeurosurgicalPlanningTutorialTractographySelfTest
#

class NeurosurgicalPlanningTutorialTractographySelfTest(object):
  def __init__(self, parent):
    parent.title = "NeurosurgicalPlanningTutorialTractographySelfTest"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = []
    parent.contributors = ["Nicole Aucoin (BWH)"]
    parent.helpText = """
    This is a test case that exercises the fiducials used in the Neurosurgical Planning tutorial.
    """
    parent.acknowledgementText = """
    This file was originally developed by Nicole Aucoin, BWH and was partially funded by NIH grant 3P41RR013218-12S1.
"""
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['NeurosurgicalPlanningTutorialTractographySelfTest'] = self.runTest

  def runTest(self):
    tester = NeurosurgicalPlanningTutorialTractographySelfTestTest()
    tester.runTest()

#
# qNeurosurgicalPlanningTutorialTractographySelfTestWidget
#

class NeurosurgicalPlanningTutorialTractographySelfTestWidget(object):
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "NeurosurgicalPlanningTutorialTractographySelfTest Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    reloadFormLayout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)

    #
    # scale factor for screen shots
    #
    self.screenshotScaleFactorSliderWidget = ctk.ctkSliderWidget()
    self.screenshotScaleFactorSliderWidget.singleStep = 1.0
    self.screenshotScaleFactorSliderWidget.minimum = 1.0
    self.screenshotScaleFactorSliderWidget.maximum = 50.0
    self.screenshotScaleFactorSliderWidget.value = 1.0
    self.screenshotScaleFactorSliderWidget.setToolTip("Set scale factor for the screen shots.")
    parametersFormLayout.addRow("Screenshot scale factor", self.screenshotScaleFactorSliderWidget)

    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onApplyButton(self):
    logic = NeurosurgicalPlanningTutorialTractographySelfTestLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    screenshotScaleFactor = int(self.screenshotScaleFactorSliderWidget.value)
    print("Run the logic method, enable screen shots = %s" % enableScreenshotsFlag)
    logic.run(enableScreenshotsFlag,screenshotScaleFactor)

  def onReload(self,moduleName="NeurosurgicalPlanningTutorialTractographySelfTest"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onReloadAndTest(self,moduleName="NeurosurgicalPlanningTutorialTractographySelfTest"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception as e:
      import traceback
      traceback.print_exc()
      slicer.util.warningDisplay('Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace",
                                 windowTitle="Reload and Test")


#
# NeurosurgicalPlanningTutorialTractographySelfTestLogic
#

class NeurosurgicalPlanningTutorialTractographySelfTestLogic(object):

  def __init__(self):
    pass

  def delayDisplay(self,message,msec=1000):
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    self.delayDisplay(description)

    if self.enableScreenshots == 0:
      return

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
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, self.screenshotScaleFactor, imageData)

  #
  # for the red slice widget, convert the background volume's RAS
  # coordinates to display coordinates for painting
  #
  def rasToDisplay(self, r, a, s):
    displayCoords = [0, 0, 0, 1]

    # get the slice node
    lm = slicer.app.layoutManager()
    sliceWidget = lm.sliceWidget('Red')
    sliceLogic = sliceWidget.sliceLogic()
    sliceNode = sliceLogic.GetSliceNode()

    xyToRASMatrix = sliceNode.GetXYToRAS()
    rasToXyMatrix = vtk.vtkMatrix4x4()
    rasToXyMatrix.Invert(xyToRASMatrix, rasToXyMatrix)

    worldCoords = [r, a, s, 1.0]
    rasToXyMatrix.MultiplyPoint(worldCoords, displayCoords)

    return displayCoords

  def run(self,enableScreenshots=0,screenshotScaleFactor=1):
    """
    Run the actual algorithm
    """
    self.delayDisplay('Running test of the Neurosurgical Planning tutorial')

    self.enableScreenshots = enableScreenshots
    self.screenshotScaleFactor = screenshotScaleFactor

    # conventional layout
    lm = slicer.app.layoutManager()
    lm.setLayout(2)

    moduleSelector = slicer.util.mainWindow().moduleSelector()
    #
    # first load the data
    #
    if self.enableScreenshots == 1:
      # for the tutorial, do it through the welcome module
      moduleSelector.selectModule('Welcome')
      self.delayDisplay("Screenshot")
      self.takeScreenshot('NeurosurgicalPlanning-Welcome','Welcome module',-1)
    else:
      # otherwise show the sample data module
      moduleSelector.selectModule('SampleData')

    # use the sample data module logic to load data for the self test
    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()

    self.delayDisplay("Getting Baseline volume")
    baselineVolume = sampleDataLogic.downloadWhiteMatterExplorationBaselineVolume()

    self.delayDisplay("Getting DTI volume")
    dtiVolume = sampleDataLogic.downloadWhiteMatterExplorationDTIVolume()

    self.takeScreenshot('NeurosurgicalPlanning-Loaded','Data loaded',-1)

    #
    # create a label map and set it for editing
    #
    volumesLogic = slicer.modules.volumes.logic()
    baselineVolumeLabel =  volumesLogic.CreateAndAddLabelVolume( slicer.mrmlScene, baselineVolume, baselineVolume.GetName() + '-label' )
    baselineDisplayNode = baselineVolumeLabel.GetDisplayNode()
    baselineDisplayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(baselineVolume.GetID())
    selectionNode.SetReferenceActiveLabelVolumeID(baselineVolumeLabel.GetID())
    slicer.app.applicationLogic().PropagateVolumeSelection(0)

    data = slicer.util.array(baselineVolume.GetName() + "-label")
    data[6:15, 110:140, 130:160] = 293

    #
    # link the viewers
    #

    if self.enableScreenshots == 1:
      # for the tutorial, pop up the linking control
      sliceController = slicer.app.layoutManager().sliceWidget("Red").sliceController()
      popupWidget = sliceController.findChild("ctkPopupWidget")
      if popupWidget is not None:
        popupWidget.pinPopup(1)
        self.takeScreenshot('NeurosurgicalPlanning-Link','Link slice viewers',-1)
        popupWidget.pinPopup(0)

    #
    # Tractography Label Map Seeding module
    #
    moduleSelector.selectModule('TractographyLabelMapSeeding')
    self.takeScreenshot('NeurosurgicalPlanning-LabelMapSeedingModule','Showing Tractography Label Seeding Module',-1)
    tractographyLabelSeeding = slicer.modules.tractographylabelmapseeding
    parameters = {}
    parameters['InputVolume'] = dtiVolume.GetID()
    baselinelabel293 = slicer.mrmlScene.GetFirstNodeByName("BaselineVolume-label")
# VTK6 TODO - set 'InputROIPipelineInfo'
    parameters['InputROI'] = baselinelabel293.GetID()
    fibers = slicer.vtkMRMLFiberBundleNode()
    slicer.mrmlScene.AddNode(fibers)
    parameters['OutputFibers'] = fibers.GetID()
    parameters['UseIndexSpace'] = 1
    parameters['StoppingValue'] = 0.15
    parameters['ROIlabel'] = 293
    parameters['ThresholdMode'] = 'FractionalAnisotropy'
    # defaults
    # parameters['ClTh'] = 0.3
    # parameters['MinimumLength'] = 20
    # parameters['MaximumLength'] = 800
    # parameters['StoppingCurvature'] = 0.7
    # parameters['IntegrationStepLength'] = 0.5
    # parameters['SeedSpacing'] = 2
    # and run it
    slicer.cli.run(tractographyLabelSeeding, None, parameters)
    self.takeScreenshot('NeurosurgicalPlanning-LabelMapSeeding','Showing Tractography Label Seeding Results',-1)

    #
    # tractography fiducial seeding
    #
    moduleSelector.selectModule('TractographyInteractiveSeeding')
    self.takeScreenshot('NeurosurgicalPlanning-TIS','Showing Tractography Interactive Seeding Module',-1)

    # DTI in background
    sliceLogic = slicer.app.layoutManager().sliceWidget('Red').sliceLogic()
    sliceLogic.StartSliceCompositeNodeInteraction(1)
    compositeNode = sliceLogic.GetSliceCompositeNode()
    compositeNode.SetBackgroundVolumeID(dtiVolume.GetID())
    sliceLogic.EndSliceCompositeNodeInteraction()

    # DTI visible in 3D
    sliceNode = sliceLogic.GetSliceNode()
    sliceLogic.StartSliceNodeInteraction(128)
    sliceNode.SetSliceVisible(1)
    sliceLogic.EndSliceNodeInteraction()

    self.takeScreenshot('NeurosurgicalPlanning-TIS-DTI','DTI volume with Tractography Interactive Seeding Module',-1)

    # place a fiducial
    displayNode = slicer.vtkMRMLMarkupsDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    fidNode = slicer.vtkMRMLMarkupsFiducialNode()
    fidNode.SetName('F')
    slicer.mrmlScene.AddNode(fidNode)
    fidNode.SetAndObserveDisplayNodeID(displayNode.GetID())
    r = 28.338526
    a = 34.064367
    sliceOffset = 58.7
    s = sliceOffset
    fidNode.AddFiducial(r,a,s)

    # make it active
    selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
    if (selectionNode is not None):
      selectionNode.SetReferenceActivePlaceNodeID(fidNode.GetID())

    self.takeScreenshot('NeurosurgicalPlanning-TIS-Fid1','Fiducial in Tractography Interactive Seeding Module',-1)


    # set up the arguments
    wr = slicer.modules.tractographyinteractiveseeding.widgetRepresentation()
    wr.setDiffusionTensorVolumeNode(dtiVolume)
    # create a fiber bundle
    fiducialFibers = slicer.vtkMRMLFiberBundleNode()
    slicer.mrmlScene.AddNode(fiducialFibers)
    wr.setFiberBundleNode(fiducialFibers)
    wr.setSeedingNode(fidNode)
    wr.setMinimumPath(10)
    wr.setStoppingValue(0.15)

    self.takeScreenshot('NeurosurgicalPlanning-TIS-Args','Tractography Interactive Seeding arguments',-1)

    self.delayDisplay("Moving the fiducial")
    for y in range(-20, 100, 5):
      msg = "Moving the fiducial to y = " + str(y)
      self.delayDisplay(msg,250)
      fidNode.SetNthFiducialPosition(0, r, y, s)

    self.takeScreenshot('NeurosurgicalPlanning-TIS-Moved','Moved fiducial and did Tractography Interactive Seeding',-1)
    
    return True


class NeurosurgicalPlanningTutorialTractographySelfTestTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)
    # reset to conventional layout
    lm = slicer.app.layoutManager()
    lm.setLayout(2)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_NeurosurgicalPlanningTutorialTractographySelfTest1()

  def test_NeurosurgicalPlanningTutorialTractographySelfTest1(self):

    self.delayDisplay("Starting the Neurosurgical Planning Tutorial Markups test")

    # start in the welcome module
    m = slicer.util.mainWindow()
    m.moduleSelector().selectModule('Welcome')

    logic = NeurosurgicalPlanningTutorialTractographySelfTestLogic()
    logic.run()

    self.delayDisplay('Test passed!')

#
# We had to make the filename shorter, so make alias here to desired classname
#
NsgPlanTracto = NeurosurgicalPlanningTutorialTractographySelfTest
NsgPlanTractoWidget = NeurosurgicalPlanningTutorialTractographySelfTestWidget
NsgPlanTractoLogic = NeurosurgicalPlanningTutorialTractographySelfTestLogic
