import csv
import glob
import json
import logging
import math
import numpy
import os
import pandas
import pickle
import random
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

#
# Tractology
#

class Tractology(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Tractology"
    self.parent.categories = ["Diffusion"]
    self.parent.dependencies = []
    self.parent.contributors = ["Steve Pieper (Isomics Inc.)"]
    self.parent.helpText = """
This module is used to study tracts.
See more information in <a href="https://github.com/SlicerDMRI/SlicerDMRI#Tractology">module documentation</a>.
"""
    self.parent.acknowledgementText = """
Developed as part of "HARMONIZING MULTI-SITE DIFFUSION MRI ACQUISITIONS FOR NEUROSCIENTIFIC ANALYSIS ACROSS AGES AND BRAIN DISORDERS" 5R01MH119222.
This file is based on a template originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab, and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""


#
# TractologyWidget
#

class TractologyWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = TractologyLogic()

    # Instantiate and connect widgets ...

    #
    # Explorers Area
    #
    explorersCollapsibleButton = ctk.ctkCollapsibleButton()
    explorersCollapsibleButton.text = "Explorers"
    self.layout.addWidget(explorersCollapsibleButton)

    # Layout within the dummy collapsible button
    self.explorersFormLayout = qt.QFormLayout(explorersCollapsibleButton)

    self.abcdTractologyDemoButton = qt.QPushButton("Run ABCD Tract Explorer")
    self.explorersFormLayout.addWidget(self.abcdTractologyDemoButton)
    self.abcdTractologyDemoButton.connect('clicked()', self.abcdTractologyDemo)

    self.hcpTractologyDemoButton = qt.QPushButton("Run HCP Tract Explorer")
    self.explorersFormLayout.addWidget(self.hcpTractologyDemoButton)
    self.hcpTractologyDemoButton.connect('clicked()', self.hcpTractologyDemo)

    #
    # Networks Area
    #
    networksCollapsibleButton = ctk.ctkCollapsibleButton()
    networksCollapsibleButton.text = "Networks"
    self.layout.addWidget(networksCollapsibleButton)

    # Layout within the dummy collapsible button
    self.networksFormLayout = qt.QFormLayout(networksCollapsibleButton)

    self.useFullFibersCheckBox = qt.QCheckBox()
    self.useFullFibersCheckBox.checked = False
    self.useFullFibersCheckBox.toolTip = "When checked, visualize the full resolution fiber bundle files with scalar overlay options (slower)"
    self.networksFormLayout.addRow("Use full fibers", self.useFullFibersCheckBox)


    subjectID = "NDARINVTPCLKWJ5"
    self.subjectIDEdit = qt.QLineEdit()
    self.subjectIDEdit.text = subjectID
    self.networksFormLayout.addRow("Subject ID", self.subjectIDEdit)

    modulePath = os.path.dirname(slicer.modules.tractology.path)
    networksFilePath = os.path.join(modulePath, "Resources", "PUTATIVE_NETWORKS_TRACTS - Steve_format_revised-2022-03-10.csv")

    self.tractNames,self.tractColors,self.networks = self.logic.loadNetworks(networksFilePath)

    print(self.tractNames,self.networks)
    for networkName in self.networks.keys():
      button = qt.QPushButton(f"{networkName} - {len(self.networks[networkName])} tracts")
      toolTip = ""
      for tract in self.networks[networkName]:
        toolTip += self.tractNames[tract] + ", "
      button.toolTip = toolTip[:-2]
      self.networksFormLayout.addWidget(button)
      button.connect("clicked()", lambda networkName=networkName: self.onNetworkClicked(networkName))


    # Add vertical spacer
    self.layout.addStretch(1)

    self.logic.setCustomOrientationMarker()
    slicer.app.layoutManager().threeDWidget(0).viewLogic().GetViewNode().SetBackgroundColor((0,0,0))
    slicer.app.layoutManager().threeDWidget(0).viewLogic().GetViewNode().SetBackgroundColor2((0,0,0))
    slicer.app.layoutManager().threeDWidget(0).viewLogic().GetViewNode().SetBoxVisible(False)
    slicer.app.layoutManager().threeDWidget(0).viewLogic().GetViewNode().SetAxisLabelsVisible(False)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)

    try:
        import Lights
        lightsLogic = Lights.LightsLogic()
        viewNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLViewNode')
        for viewNodeIndex in range(viewNodes.GetNumberOfItems()):
            viewNode = viewNodes.GetItemAsObject(viewNodeIndex)
            lightsLogic.addManagedView(viewNode)
            lightsLogic.setUseSSAO(True)
            lightsLogic.setSSAOSizeScaleLog(0.7)
    except ModuleNotFoundError:
        print("Lights not available - install Sandbox extension")

  def cleanup(self):
    pass

  def abcdTractologyDemo(self):
    self.logic.abcdDeviceidTractologyDemo(deviceId=4)

  def hcpTractologyDemo(self):
    self.logic.hcpTractologyDemo()

  def onNetworkClicked(self, networkName):
    print(f"Showing {networkName}, with {self.networks[networkName]}")
    self.logic.showNetwork(self.subjectIDEdit.text, self.networks[networkName], self.tractNames, self.tractColors, self.useFullFibersCheckBox.checked)
    print(f"done showing {networkName}")


# TractologyLogic
#

class TractologyLogic(ScriptedLoadableModuleLogic):
  """
  Use parallel axes to explore tract statistics space

  See: http://syntagmatic.github.io/parallel-coordinates/
  https://github.com/BigFatDog/parcoords-es

  Note also experimented with vtk version, but it has fewer features
  and performance is not any better in practice.

  https://vtk.org/Wiki/VTK/Examples/Python/Infovis/ParallelCoordinatesExtraction
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)

    self.directoryPathByID = {}
    self.tractFileNameByLabel = {}
    self.subjects = []
    self.categoricals = []

  def abcdTractologyDemo(self, addElements=True):
    """To be restored from backup"""
    pass

  def abcdDeviceidTractologyDemo(self, deviceId=4, addElements=True):

    directoryPattern = f"/home/ubuntu/data/abcd/Deviceid_{deviceId}/harmonized*"
    directoryPattern = f"/s3/abcdRelease3_WMA/Deviceid_{deviceId}/Target_harmonization/harmonized*"
    print(directoryPattern)
    pickleFile = f"/home/ubuntu/data/abcd/tractology-Deviceid_{deviceId}.pickle"
    if os.path.exists(pickleFile):
      [self.subjects, self.tractFileNameByLabel, self.directoryPathByID] = pickle.load(open(pickleFile, "rb"))
    else:
      self.subjects,self.tractFileNameByLabel = self.collectABCDSubjectTractStatistics(directoryPattern)
      pickle.dump([self.subjects,self.tractFileNameByLabel, self.directoryPathByID], open(pickleFile, "wb"))

    if addElements:
      dataPath = "/home/ubuntu/data/abcd/abcdRelease3_merged_DWI_withoutPhilips.csv"
      elementDataFrame = pandas.read_csv(dataPath)
      slicer.modules.elementDataFrame = elementDataFrame
      elements = [
        "nihtbx_totalcomp_fc",
        "scrn_hr_slowfriend",
        "scrn_hr_liecheat",
        "scrn_hr_fear",
        "scrn_hr_dep",
        "scrn_hr_stress",
        "scrn_hr_destroy",
        "scrn_hr_disobey",
        "interview_age",
        "sex_x",
      ]
      elementMins = {}
      elementMaxes = {}
      minMaxSubjects = {}
      for subject in self.subjects:
        subjectID = subject['id']
        if not isinstance(subjectID, int):
          elementSubjectID = subjectID.replace("_ses", "").replace("NDAR", "NDAR_")
          row = elementDataFrame[elementDataFrame['src_subject_id'] == elementSubjectID]
        for element in elements:
          if subjectID not in [0, 1]:
            subject[element] = row[element].values[0]
            if isinstance(subject[element], numpy.int64):
              subject[element] = int(subject[element])
            elementMins[element] = min(subject[element], elementMins[element]) if element in elementMins else subject[element]
            elementMaxes[element] = max(subject[element], elementMaxes[element]) if element in elementMaxes else subject[element]
          else:
            minMaxSubjects[subjectID] = subject
      for element in elements:
        minMaxSubjects[0][element] = elementMins[element]
        minMaxSubjects[1][element] = elementMaxes[element]

    self.categoricals = {}
    categories = [
      "scrn_hr_slowfriend",
      "scrn_hr_liecheat",
      "scrn_hr_fear",
      "scrn_hr_dep",
      "scrn_hr_stress",
      "scrn_hr_destroy",
      "scrn_hr_disobey",
      "sex_x",
    ]
    for category in categories:
      self.categoricals[category] = []
      print(elementDataFrame[elementDataFrame["device_id"] == deviceId])
      valueCounts = elementDataFrame[elementDataFrame["device_id"] == deviceId][category].value_counts()
      for index in valueCounts.index:
        value = valueCounts[index]
        if isinstance(value, numpy.int64):
          value = int(value)
        self.categoricals[category].append((index, value))

    dataToPlotString = json.dumps(self.subjects)
    categoricalsString = json.dumps(self.categoricals)

    modulePath = os.path.dirname(slicer.modules.tractology.path)
    resourceFilePath = os.path.join(modulePath, "Resources", "ABCD-ParCoords-template.html")
    html = open(resourceFilePath).read()
    html = html.replace("%%dataToPlot%%", dataToPlotString)
    html = html.replace("%%categoricals%%", categoricalsString)

    self.webWidget = slicer.qSlicerWebWidget()
    self.webWidget.size = qt.QSize(1600,1024)
    # self.webWidget.setHtml(html)
    self.webWidget.show()

    # save for debugging
    htmlPath = slicer.app.temporaryPath+'/data.html'
    open(slicer.app.temporaryPath+'/data.html', 'w').write(html)
    print(f"Saved to {htmlPath}")
    tractImagePath = slicer.app.temporaryPath+"/TractImages"
    if not os.path.exists(tractImagePath):
      os.symlink("/home/ubuntu/data/abcd/TractImages", slicer.app.temporaryPath+"/TractImages")
    self.webWidget.url = "file://"+htmlPath

  def collectABCDJSONSubjectData(self):
    dictionaryPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_dictionary.json"
    dataPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_data.json"
    dictionary = json.loads(open(dictionaryPath).read())
    data = json.loads(open(dataPath).read())
    dataBySubject = {}
    for datum in data:
      subjectID = "".join(datum['\ufeffsrc_subject_id'].split("_"))
      dataBySubject[subjectID] = datum
    return dictionary,dataBySubject

  def collectABCDSubjectTractStatistics(self, directoryPattern, stat=" FA1.Mean ", statRange=[0,1]):
    #  TODO: make this configurable instead of hard-coded

    statMin, statMax = None, None
    subjects = []
    for directoryPath in glob.glob(directoryPattern):
      print(directoryPath)
      directoryName = directoryPath.split("/")[-1]
      subjectID = directoryName.split("-")[1]
      directoryPath += "/AnatomicalTracts"
      self.directoryPathByID[subjectID] = directoryPath
      csvFilePath = directoryPath + "/diffusion_measurements_anatomical_tracts.csv"
      tractFileNameByLabel = {}
      try:
        with open(csvFilePath) as csvFile:
          csvReader = csv.reader(csvFile)
          subjectStats = {}
          subjectStats['id'] = subjectID
          headers = csvReader.__next__()
          for row in csvReader:
            tractFileName = row[0].split('/')[-1]
            tractName = os.path.splitext(tractFileName)[0]
            tractNameParts = tractName.split('_')
            tractLabel = tractNameParts[1]
            if len(tractNameParts) > 2:
              tractLabel += "-" + tractNameParts[2][0].upper()
            tractFileNameByLabel[tractLabel] = tractFileName.strip()
            statValue = row[headers.index(stat)]
            statMin = min(statValue,statMin) if statMin else statValue
            statMax = max(statValue,statMax) if statMax else statValue
            subjectStats[tractLabel] = statValue
          subjects.append(subjectStats)
      except FileNotFoundError:
        print(f"Skipping {csvFilePath}")
    minStats, maxStats = {}, {}
    if statRange is None:
      statRange = [statMin, statMax]
    for key in subjectStats.keys():
      minStats[key] = statRange[0]
      maxStats[key] = statRange[1]
    subjects.append(minStats)
    subjects.append(maxStats)
    return subjects,tractFileNameByLabel

  def showTractsOnly(self, tracts):
    allNodes = slicer.util.getNodes('*')
    for node in allNodes.values():
      if node.IsA("vtkMRMLModelNode"):
        node.SetDisplayVisibility(False)
      if node.IsA("vtkMRMLFiberBundleNode") and node.GetTubeDisplayNode():
        node.GetTubeDisplayNode().SetVisibility(node in tracts)

  def showABCDBrushedTract(self, brushedData):
    print(brushedData)
    if len(brushedData['brushedTracts']) == 0:
      return
    tractLabel = brushedData['brushedTracts'][0]
    subjectID = brushedData['brushedSubjectID']
    fileName = self.tractFileNameByLabel[tractLabel]
    directoryPath = self.directoryPathByID[subjectID]
    filePath = directoryPath + '/' + fileName
    nodeName = str(subjectID) + "-" + tractLabel
    try:
      tractNode = slicer.util.getNode(nodeName)
    except slicer.util.MRMLNodeNotFoundException:
      print(f"Loading {filePath}")
      tractNode = slicer.util.loadNodeFromFile(filePath, "FiberBundleFile")
      if tractNode is None:
        print("Oops, no tract file available!")
        return
      tractNode.SetName(nodeName)
    tractNode.GetLineDisplayNode().SetVisibility(True)
    self.showTractsOnly([tractNode])

    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDController = threeDWidget.threeDController()
    if nodeName.endswith("L"):
      threeDController.lookFromAxis(ctk.ctkAxesWidget.Left)
    elif nodeName.endswith("R"):
      threeDController.lookFromAxis(ctk.ctkAxesWidget.Right)
    else:
      threeDController.lookFromAxis(ctk.ctkAxesWidget.Anterior)
    threeDWidget.threeDView().resetFocalPoint()
    renderer = threeDWidget.threeDView().renderWindow().GetRenderers().GetItemAsObject(0)
    cameraNode = threeDWidget.threeDView().cameraNode()
    cameraNode.Reset(True, True, True, renderer)
    return tractNode

  def loadVolumeForVisibleTract(self):
    for node in allNodes.values():
      if node.IsA("vtkMRMLModelNode"):
        if node.GetDisplayVisibility():
          slicer.util.loadVolume("/s3/abcdRelease3_Harmonization/Deviceid_4/Target_harmonization/sub-NDARINVWM1W0UPC_ses-baselineYear1Arm1_run-01_dwi_b500_mapped_cs.nii.gz")

  def hpcTractologyDemo(self):
    """Use parallel axes to explore tract statistics space
    """

    subjects = self.collectHCPSubjectTractStatistics()

    dataToPlotString = json.dumps(subjects)

    modulePath = os.path.dirname(slicer.modules.tractology.path)
    resourceFilePath = os.path.join(modulePath, "Resources", "ABCD-ParCoords-template.html")
    html = open(resourceFilePath).read()
    html = html.replace("%%dataToPlot%%", dataToPlotString)

    self.webWidget = slicer.qSlicerWebWidget()
    self.webWidget.size = qt.QSize(1600,1024)
    # self.webWidget.setHtml(html)
    self.webWidget.show()

    # save for debugging
    htmlPath = slicer.app.temporaryPath+'/data.html'
    open(slicer.app.temporaryPath+'/data.html', 'w').write(html)
    print(f"Saved to {htmlPath}")

    self.webWidget.url = "file://"+htmlPath
    print(f"Serving from {htmlPath}")

  def loadNetworks(self,csvFilePath):
    tractNames = {}
    tractColors = {}
    networks = {}
    with open(csvFilePath) as csvFile:
      csvReader = csv.reader(csvFile)
      headers = csvReader.__next__()
      for header in headers[3:]:
        networkName = header.split("_")[0]
        networks[networkName] = []
      networkKeys = list(networks.keys())
      for row in csvReader:
        tractNames[row[0]] = row[1]
        tractColors[row[0]] = row[2]
        for networkIndex in range(3, len(row)):
          if row[networkIndex] != "":
           networks[networkKeys[networkIndex-3]].append(row[0])
    return tractNames,tractColors,networks

  def showNetwork(self, subjectID, tracts, tractNames, tractColors, useFullFibers):
    if useFullFibers:
      pathPrefix = "/s3/abcdRelease3_WMA/Deviceid_4/Target_harmonization/harmonized_sub-"
    else:
      pathPrefix = "/mnt/extra/pieper/data/abcd/batchTracts/Deviceid_4/Target_harmonization/harmonized_sub-"
    pathPostfix = "_ses-baselineYear1Arm1_run-01_dwi_b3000_UKF2T/AnatomicalTracts/"
    tractNodes = []
    for tract in tracts:
      colorString = tractColors[tract].lstrip("#")
      tractColor = tuple((int(colorString[i:i+2], 16)/255 for i in (0, 2, 4)))
      tractName = f"{subjectID}-{tractNames[tract]}"
      print(tractName, tractColor)
      try:
        tractNode = slicer.util.getNode(tractName)
      except slicer.util.MRMLNodeNotFoundException:
        filePath = f"{pathPrefix}{subjectID}{pathPostfix}{tract}"
        logging.info(f"Loading {filePath}")
        #filePath = f"/mnt/extra/pieper/data/abcd/batchTracts/{tract}"
        tractNode = slicer.util.loadFiberBundle(filePath)
      tractNode.SetName(tractName)
      tractNode.GetTubeDisplayNode().SetColor(*tractColor)
      tractNode.GetLineDisplayNode().SetColor(*tractColor)
      tractNode.GetGlyphDisplayNode().SetColor(*tractColor)
      tractNode.GetTubeDisplayNode().SetVisibility(True)
      tractNode.GetLineDisplayNode().SetVisibility(False)
      tractNode.GetGlyphDisplayNode().SetVisibility(False)
      tractNode.GetLineDisplayNode().SetOpacity(1)
      tractNode.GetTubeDisplayNode().SetOpacity(1)
      tractNode.GetLineDisplayNode().SetColorModeToSolid()
      tractNode.GetTubeDisplayNode().SetColorModeToSolid()
      tractNode.GetTubeDisplayNode().SetTubeRadius(0.2)
      tractNode.SetSubsamplingRatio(.5)
      tractNode.GetTubeDisplayNode().SetAmbient(0.15)
      tractNode.GetTubeDisplayNode().SetDiffuse(0.95)
      tractNode.GetTubeDisplayNode().SetSpecular(0.0)
      tractNode.GetTubeDisplayNode().SetPower(0.15)
      tractNode.GetTubeDisplayNode().SetPower(0.05)
      tractNode.GetTubeDisplayNode().SetMetallic(0.75)
      tractNode.GetTubeDisplayNode().SetRoughness(0.1)
      tractNodes.append(tractNode)
    self.showTractsOnly(tractNodes)
    return(tractNodes)

  def setCustomOrientationMarker(self):
    modulePath = os.path.dirname(slicer.modules.tractology.path)
    markerFilePath = os.path.join(modulePath, "Resources", "mrHeadSeg.vtk")
    mrHeadName = "MRHeadOrientationMarker"
    try:
      headModel = slicer.util.getNode(mrHeadName)
    except slicer.util.MRMLNodeNotFoundException:
      headModel = slicer.util.loadModel(markerFilePath)
      headModel.SetName(mrHeadName)
    headModel.GetDisplayNode().SetVisibility(False)
    viewNodes = slicer.util.getNodesByClass("vtkMRMLAbstractViewNode")
    for viewNode in viewNodes:
      viewNode.SetOrientationMarkerType(slicer.vtkMRMLAbstractViewNode.OrientationMarkerTypeHuman)
      viewNode.SetOrientationMarkerHumanModelNodeID(headModel.GetID())


#
# TractologyTest
#

class TractologyTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Tractology1()

  def test_Tractology1(self):
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

    self.delayDisplay('Test passed')


#
# helper utilities
#

"""
paste script below then run this:

import os; generateABCDTractImages("/home/ubuntu/data/abcd/TractImages")

"""

def generateABCDTractImages(targetDirectoryPath):
  layoutManager = slicer.app.layoutManager()
  oldLayout = layoutManager.layout
  threeDWidget = layoutManager.threeDWidget(0)
  threeDWidget.setParent(None)
  threeDWidget.show()
  geometry = threeDWidget.geometry
  threeDWidget.threeDController().visible = False
  threeDWidget.setGeometry(geometry.x(), geometry.y(), 512, 512)
  logic = slicer.modules.TractologyWidget.logic
  for subject in logic.subjects:
    subjectID = subject['id']
    if subjectID in [0,1]:
      continue; # skip the fake entries created for plotting
    subjectDirectoryPath = targetDirectoryPath + "/" + subjectID
    if not os.path.exists(subjectDirectoryPath):
      os.mkdir(subjectDirectoryPath)
    for tract in subject.keys():
      if tract in logic.tractFileNameByLabel:
        imageFilePath = subjectDirectoryPath + "/" + tract + ".jpg"
        if os.path.exists(imageFilePath):
          print(f"skipped {imageFilePath}")
          continue
        try:
          tractNode = logic.showABCDBrushedTract({"brushedTracts": [tract], "brushedSubjectID": subjectID})
          slicer.util.delayDisplay(f"{subjectID} {tract}", 10)
          pixmap = threeDWidget.grab()
          pixmap.save(imageFilePath)
          print(f"saved {imageFilePath}")
          slicer.mrmlScene.RemoveNode(tractNode)
        except Exception as e:
          print(f"Failed to read a subject tract: {subjectID} {tract}")
          import traceback
          traceback.print_exc()
  # reset the view
  threeDWidget.threeDController().visible = True
  layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFinalView) ;# force change
  layoutManager.setLayout(oldLayout)


"""
paste script below then run this:

import os; generateABCD_WMA("/home/ubuntu/data/abcd/abcdRelease3_WMA")

"""

"""
generateABCD_WMA(filePrefix):

import pandas
dataPath = "/home/ubuntu/data/abcd/abcdRelease3_merged_DWI_withoutPhilips.csv"
resultPath = "/home/ubuntu/data/abcd/abcdRelease3_merged_DWI_withoutPhilips+WMA.csv"
elementDataFrame = pandas.read_csv(dataPath)
filesNotFound = []
emptyFiles = []
for index in range(len(elementDataFrame)):
  print(index)
  subjectID = elementDataFrame.iloc[index]['src_subject_id']
  subjectID = subjectID.replace("NDAR_", "NDAR")
  deviceID = elementDataFrame.iloc[index]['device_id']
  csvPath = f"/s3/abcdRelease3_WMA/Deviceid_{deviceID}/Target_harmonization/harmonized_sub-{subjectID}_ses-baselineYear1Arm1_run-01_dwi_b3000_UKF2T/AnatomicalTracts/diffusion_measurements_anatomical_tracts.csv"
  print(csvPath)
  subjectDataFrame = None
  try:
    subjectDataFrame = pandas.read_csv(csvPath)
  except FileNotFoundError:
    print(f"NotFound: {subjectID}")
    filesNotFound.append(csvPath)
  except pandas.errors.EmptyDataError:
    print(f"EmptyFile: {subjectID}")
    emptyFiles.append(csvPath)
  if subjectDataFrame is None:
    continue
  for tractIndex in range(len(subjectDataFrame)):
    tractName = subjectDataFrame.iloc[tractIndex]['Name '].split("/")[-1].split('.')[0]
    for measureIndex in range(1, len(subjectDataFrame.columns)):
      column = subjectDataFrame.columns[measureIndex]
      measureName = tractName + "." + column.strip()
      if measureName not in elementDataFrame.columns:
        elementDataFrame[measureName] = None ;# create the empty column
      elementDataFrame.loc[index, measureName] = subjectDataFrame.iloc[tractIndex][column]
elementDataFrame.to_csv(resultPath)
"""


"""

import glob
import os

def refreshMount():
    print(slicer.util.launchConsoleProcess("umount /s3".split()).communicate())
    print(slicer.util.launchConsoleProcess("python3 /home/ubuntu/nda_aws_token_generator/python/get_token.py".split()).communicate())
    print(slicer.util.launchConsoleProcess("s3fs nda-enclave-c3371:/ /s3 -o profile=NDA".split()).communicate())


filePath = f"{os.path.dirname(slicer.modules.tractology.path)}/Resources/abcd-subjects.txt"
subjectPaths = open(filePath).read().strip().split("\n")

import TractographyDownsample
downsampleLogic = TractographyDownsample.TractographyDownsampleLogic()
for subjectPath in subjectPaths:
    subjectPath += "/ses-baselineYear1Arm1/tractography"
    print(subjectPath)
    refreshMount()
    #subjectPath = "/mnt/extra/pieper/data/tract-test/tractography/"
    sourceDirectory = f"{subjectPath}/AnatomicalTracts"
    destinationDirectory = f"{subjectPath}/AnatomicalTracts_downsampled"
    if len(glob.glob(f"{sourceDirectory}/*.vtp")) == len(glob.glob(f"{destinationDirectory}/*.vtp")):
        print("subject already processed, skipping")
        continue
    parameters = downsampleLogic.parameterDefaults()
    try:
        downsampleLogic.runBatch(sourceDirectory, destinationDirectory, parameters)
    except RuntimeError:
        print(f"FAILED for {subjectPath}")



"""
