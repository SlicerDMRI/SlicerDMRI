import os
import unittest
import vtk, qt, ctk, slicer

import SampleData

#
# MyTest
#

class MyTest(object):
  def __init__(self, parent):
    parent.title = "MyTest"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = []
    parent.contributors = ["Firstname Lastname (Org)"] 
    parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    parent.acknowledgementText = """
    This file was originally developed by Name.
    """
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests["MyTest"] = self.runTest

  def runTest(self):
    tester = MyTestTest()
    tester.runTest()

#
# qMyTestWidget
#

class MyTestWidget(object):
  def __init__(self, parent=None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setUp()
      self.parent.show()

  def setUp(self):
    # Instantiate and connect widgets ...
    pass

#
# MyTestLogic
#

class MyTestLogic(object):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
      self.nodeName = "tract1"
      self.fileName = "tract1.vtk"
      self.uri = "https://github.com/Slicer/slicer.kitware.com-midas3-archive/releases/download/SHA256/06d5b5777915857fbac7b3cbd9c371523d1371f29b0c89eb7a33d86d780d5b2b"
      self.loadFileType = "FiberBundleFile"
      self.tractColor = (0.2, 0.9, 0.3)
      print("__init__")


  def run(self):
    
    self.download_data()
    self.test_setFiberBundleDisplayNode()

  def download_data(self):
      SampleData.downloadFromURL(
          nodeNames=self.nodeName,
          fileNames=self.fileName,
          uris=self.uri,
          loadFileTypes=self.loadFileType
          )
      print("Data downloade")

  def test_setFiberBundleDisplayNode(self):
      print("Testing qSlicerTractographyDisplayWidget methods")
      fiberNode = slicer.util.getNode(self.nodeName)
      tubeDisplay = fiberNode.GetTubeDisplayNode()
      tubeDisplay.SetColor(self.tractColor)
      tubeDisplay.SetColorModeToSolid()

      mesh = fiberNode.GetMesh()
      print(f"Mesh:\n{mesh}")
      # widget = qSlicerTractographyDisplayWidget()
      # widget.setFiberBundleDisplayNode(fiberNode)

      # widget.show()
      # widget.updateWidgetFromMRML()

      module = slicer.moduleNames.TractographyDisplay
      print(f"ModuleName:\n{module}")
      instance = slicer.modules.tractographydisplay
      print(f"Module:\n{instance}")
      # display_widget = slicer.util.findChildren(name="qSlicerTractographyDisplayWidget")[0]
      # print(f"Module found through children search:\n{display_widget}")
      # display_widget.updateWidgetFromMRML()


      m = slicer.util.mainWindow()
      m.moduleSelector().selectModule("TractographyDisplay")
      # display_widget = slicer.util.findChildren(name="LineDisplayWidget")[0]
      # display_widget = slicer.util.findChildren(name="GlyphDisplayWidget")[0]
      display_widget = slicer.util.findChildren(name="qSlicerTractographyDisplayModuleWidget")[0]
      # print(f"Module found through children search:\n{display_widget}")
      # display_widget.updateWidgetFromMRML()
      display_widget.opacity
      print("Called the qSlicerTractographyDisplayModuleWidget::opacity property")
      colorByScalarComboBox = slicer.util.findChildren(name="ColorByScalarComboBox")[0]
      print(colorByScalarComboBox)
      colorByScalarComboBox.setDataSet(bi)
      print("Finished testing qSlicerTractographyDisplayWidget methods")


class MyTestTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """


  def delayDisplay(self, message, msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(f"{message}")
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
    self.test_this()

  def test_this(self):

    self.delayDisplay("Starting the test")

    # start in the welcome module
    m = slicer.util.mainWindow()
    m.moduleSelector().selectModule("Welcome")

    logic = MyTestLogic()
    logic.run()

    self.delayDisplay("Test passed!")

