import csv
import glob
import json
import logging
import math
import numpy
import os
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
    self.logic.abcdTractologyDemo()

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

  def abcdTractologyDemo(self, addElements=False):

    subjects = self.collectABCDSubjectTractStatistics()

    if addElements:
      dictionary,dataBySubject = self.collectABCDData()
      elements = [
        "interview_age",
        "scrn_hr_slowfriend",
        "scrn_hr_liecheat",
        "scrn_hr_fear",
        "scrn_hr_dep",
        "scrn_hr_stress",
        "scrn_hr_destroy",
        "scrn_hr_disobey"]
      elementMins = {}
      elementMaxes = {}
      minMaxSubjects = {}
      for subject in subjects:
        subjectID = subject['id']
        for element in elements:
          if subjectID not in [0, 1]:
            subject[element] = dataBySubject[subjectID][element]
            elementMins[element] = min(subject[element], elementMins[element]) if element in elementMins else subject[element]
            elementMaxes[element] = max(subject[element], elementMaxes[element]) if element in elementMaxes else subject[element]
          else:
            minMaxSubjects[subjectID] = subject
      for element in elements:
        minMaxSubjects[0][element] = elementMins[element]
        minMaxSubjects[1][element] = elementMaxes[element]

    dataToPlotString = json.dumps(subjects)

    modulePath = os.path.dirname(slicer.modules.tractology.path)
    resourceFilePath = os.path.join(modulePath, "Resources", "ABCD-ParCoords-template.html")
    html = open(resourceFilePath).read()
    html = html.replace("%%dataToPlot%%", dataToPlotString)

    self.webWidget = slicer.qSlicerWebWidget()
    self.webWidget.size = qt.QSize(1600,1024)
    self.webWidget.setHtml(html)
    self.webWidget.show()

    # save for debugging
    htmlPath = slicer.app.temporaryPath+'/data.html'
    open(slicer.app.temporaryPath+'/data.html', 'w').write(html)
    print(f"Saved to {htmlPath}")

  def collectABCDData(self):
    dictionaryPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_dictionary.json"
    dataPath = "/opt/data/SlicerDMRI/Test-Dec01-N30/abcd30Subjects_data.json"
    dictionary = json.loads(open(dictionaryPath).read())
    data = json.loads(open(dataPath).read())
    dataBySubject = {}
    for datum in data:
      subjectID = "".join(datum['\ufeffsrc_subject_id'].split("_"))
      dataBySubject[subjectID] = datum
    return dictionary,dataBySubject

  def collectABCDSubjectTractStatistics(self, stat=" FA1.Mean ", statRange=[0,1]):
    #  TODO: make this configurable instead of hard-coded

    statMin, statMax = None, None
    subjects = []
    directoryPattern = "/opt/data/SlicerDMRI/Test-Dec01-N30/WMA/sub-*-dwi_b3000_orig/AnatomicalTracts"
    for directoryPath in glob.glob(directoryPattern):
      directoryName = directoryPath.split("/")[6]
      subjectID = directoryName.split("-")[1]
      self.directoryPathByID[subjectID] = directoryPath
      csvFilePath = directoryPath + "/diffusion_measurements_anatomical_tracts.csv"
      with open(csvFilePath) as csvFile:
        csvReader = csv.reader(csvFile)
        subjectStats = {}
        headers = csvReader.__next__()
        for row in csvReader:
          tractFileName = row[0].split('/')[-1]
          tractName = os.path.splitext(tractFileName)[0]
          tractNameParts = tractName.split('_')
          tractLabel = tractNameParts[1]
          if len(tractNameParts) > 2:
            tractLabel += "-" + tractNameParts[2][0].upper()
          self.tractFileNameByLabel[tractLabel] = tractFileName.strip()
          statValue = row[headers.index(stat)]
          statMin = min(statValue,statMin) if statMin else statValue
          statMax = max(statValue,statMax) if statMax else statValue
          subjectStats[tractLabel] = statValue
        subjectStats['id'] = subjectID
        subjects.append(subjectStats)
    minStats, maxStats = {}, {}
    if statRange is None:
      statRange = [statMin, statMax]
    for key in subjectStats.keys():
      minStats[key] = statRange[0]
      maxStats[key] = statRange[1]
    subjects.append(minStats)
    subjects.append(maxStats)
    return subjects

  def showABCDBrushedTract(self, brushedData):
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
    cameraNode = layoutManager.threeDWidget(0).threeDView().interactorStyle().GetCameraNode()
    print(nodeName)
    if nodeName.endswith("L"):
      print("left")
      cameraNode.RotateTo(slicer.vtkMRMLCameraNode.Left)
    elif nodeName.endswith("R"):
      print("right")
      cameraNode.RotateTo(slicer.vtkMRMLCameraNode.Right)
    else:
      print("anterior")
      cameraNode.RotateTo(slicer.vtkMRMLCameraNode.Anterior)

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
    self.webWidget.setHtml(html)
    self.webWidget.show()

    # save for debugging
    htmlPath = slicer.app.temporaryPath+'/data.html'
    open(slicer.app.temporaryPath+'/data.html', 'w').write(html)
    print(f"Saved to {htmlPath}")

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
