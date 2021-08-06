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

    # Instantiate and connect widgets ...

    #
    # Demos Area
    #
    demosCollapsibleButton = ctk.ctkCollapsibleButton()
    demosCollapsibleButton.text = "Parameters"
    self.layout.addWidget(demosCollapsibleButton)

    # Layout within the dummy collapsible button
    self.demosFormLayout = qt.QFormLayout(demosCollapsibleButton)

    self.abcdTractologyDemoButton = qt.QPushButton("Run ABCD Tract Explorer")
    self.demosFormLayout.addWidget(self.abcdTractologyDemoButton)
    self.abcdTractologyDemoButton.connect('clicked()', self.abcdTractologyDemo)

    self.hcpTractologyDemoButton = qt.QPushButton("Run HCP Tract Explorer")
    self.demosFormLayout.addWidget(self.hcpTractologyDemoButton)
    self.hcpTractologyDemoButton.connect('clicked()', self.hcpTractologyDemo)

    # no UI right now

    # Add vertical spacer
    self.layout.addStretch(1)

    self.logic = TractologyLogic()


  def cleanup(self):
    pass

  def abcdTractologyDemo(self):
    self.logic.abcdDeviceidTractologyDemo(deviceId=4)

  def hcpTractologyDemo(self):
    self.logic.hcpTractologyDemo()

#
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

  def showABCDBrushedTract(self, brushedData):
    print(brushedData)
    allNodes = slicer.util.getNodes('*')
    for node in allNodes.values():
      if node.IsA("vtkMRMLModelNode"):
        node.SetDisplayVisibility(False)
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
      tractNode = slicer.util.loadNodeFromFile(filePath, "FiberBundleFile")
      if tractNode is None:
        print("Oops, no tract file available!")
        return
      tractNode.SetName(nodeName)
    tractNode.GetLineDisplayNode().SetVisibility(True)

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
  break
"""
