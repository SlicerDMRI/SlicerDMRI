import json
import os
import subprocess
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

#
# BatchTract
#

class BatchTract(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "BatchTract"
    self.parent.categories = ["Diffusion"]
    self.parent.dependencies = []
    self.parent.contributors = ["Steve Pieper (Isomics Inc.)"]
    self.parent.helpText = """
This module is used to study tracts.
See more information in <a href="https://github.com/SlicerDMRI/SlicerDMRI#BatchTract">module documentation</a>.
"""
    self.parent.acknowledgementText = """
Developed as part of "HARMONIZING MULTI-SITE DIFFUSION MRI ACQUISITIONS FOR NEUROSCIENTIFIC ANALYSIS ACROSS AGES AND BRAIN DISORDERS" 5R01MH119222.
This file is based on a template originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab, and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""


#
# BatchTractWidget
#

class BatchTractWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.resultScreenshotLabel = None
    self.resultScreenshotPixmap = None

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)
    # Layout within the collapsible button
    self.parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.batchPath = ctk.ctkPathLineEdit()
    self.parametersFormLayout.addRow("Target path", self.batchPath)
    self.batchPath.currentPath = "/Volumes/SSD2T/data/pedistroke/converted"

    self.batchTractButton = qt.QPushButton("Run Batch Tract")
    self.parametersFormLayout.addWidget(self.batchTractButton)
    self.batchTractButton.connect('clicked()', self.batchTract)

    self.reviewButton = qt.QPushButton("Review")
    self.parametersFormLayout.addWidget(self.reviewButton)
    self.reviewButton.connect('clicked()', self.review)

    self.screenshotsButton = qt.QPushButton("Make screenshots")
    self.parametersFormLayout.addWidget(self.screenshotsButton)
    self.screenshotsButton.connect('clicked()', self.screenshots)

    #
    # Results Area
    #
    resultsCollapsibleButton = ctk.ctkCollapsibleButton()
    resultsCollapsibleButton.text = "Results"
    self.layout.addWidget(resultsCollapsibleButton)
    # Layout within the collapsible button
    self.resultsLayout = qt.QVBoxLayout(resultsCollapsibleButton)

    self.resultsList = qt.QListWidget()
    self.resultsLayout.addWidget(self.resultsList)


    # Add vertical spacer
    self.layout.addStretch(1)

    self.logic = BatchTractLogic()

  def cleanup(self):
    pass

  def batchTract(self):
    self.logic.batchTract(self.batchPath.currentPath)

  def review(self):
    self.results = self.logic.tractResults(self.batchPath.currentPath)
    listModel = self.resultsList.model()
    self.resultsList.clear()
    for result in self.results:
      self.resultsList.addItem(f"{result['patientID']} - {result['method']}")
      item = self.resultsList.item(listModel.rowCount()-1)
      item.setData(qt.Qt.ToolTipRole, json.dumps(result))
    self.resultsList.connect('itemSelectionChanged()', self.onResultItemChanged)
    self.resultsList.connect('itemDoubleClicked(QListWidgetItem*)', self.onResultItemDoubleClicked)

  def onResultItemChanged(self):
    item = self.resultsList.currentItem()
    result = json.loads(item.data(qt.Qt.ToolTipRole))
    self.showResultScreenshot(result)

  def onResultItemDoubleClicked(self,item):
    result = json.loads(item.data(qt.Qt.ToolTipRole))
    self.logic.loadResult(result)

  def showResultScreenshot(self, result):
    if self.resultScreenshotLabel is None:
      self.resultScreenshotLabel = qt.QLabel()
      self.resultScreenshotPixmap = qt.QPixmap()
    screenshotPath = f"{os.path.dirname(result['tractPath'])}/screenshot.png"
    self.resultScreenshotPixmap.load(screenshotPath)
    self.resultScreenshotLabel.setPixmap(self.resultScreenshotPixmap)
    self.resultScreenshotLabel.show()

  def screenshots(self):
    self.logic.screenshots(self.results)

#
# BatchTractLogic
#

class BatchTractLogic(ScriptedLoadableModuleLogic):
  """
  Iterate through dicom database making tracts for everything
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)

  def runCommand(self, command, outputBasePath):
    outFP = open(outputBasePath + "stdout.txt", 'w')
    errFP = open(outputBasePath + "stderr.txt", 'w')
    subprocess.Popen(command, stdout=outFP, stderr=errFP).wait()
    outFP.close()
    errFP.close()

  def tractsFromNRRD(self, nrrdPath, tractsPath):
    return
    if not os.path.exists(tractsPath):
      os.makedirs(tractsPath)
    baselinePath = os.path.join(tractsPath, "baseline.nrrd")
    maskPath = os.path.join(tractsPath, "mask.nrrd")
    self.runCommand([slicer.modules.dwitodtiestimation.path,
                       nrrdPath,
                       os.path.join(tractsPath, "dti.nrrd"),
                       baselinePath],
                    os.path.join(tractsPath, "dwitodtiestimation"))
    if qt.QFileInfo(baselinePath).exists():
      print("calculating mask")
      maskBelowThreshold = "100"
      maskAboveThreshold = "99"
      self.runCommand([slicer.modules.thresholdscalarvolume.path,
                       "--thresholdtype", "Below",
                       "--threshold", maskBelowThreshold,
                       "--outsidevalue", "0",
                       baselinePath,
                       maskPath,
                       ],
                    os.path.join(tractsPath, "maskBelow"))
      self.runCommand([slicer.modules.thresholdscalarvolume.path,
                       "--thresholdtype", "Above",
                       "--threshold", maskAboveThreshold,
                       "--outsidevalue", "1",
                       maskPath,
                       maskPath,
                       ],
                    os.path.join(tractsPath, "maskAbove"))
      print("running ukf")
      """
      # This is what Banu was using:
      /neuro/users/banu.ahtam/Documents/Slicer-4.13.0-2020-12-13-linux-amd64/Slicer --launch UKFTractography \
              --dwiFile Subject01/DWI_Subject01_QCed.nrrd \
              --maskFile Subject01/DWI_Subject01_QCed_brainmask_edited.nrrd \
              --tracts Subject01/UKF_tractography_Subject01.vtk \
              --stoppingThreshold 0.06 \
              --stoppingFA 0.08 \
              --seedingThreshold 0.10 \
              --seedsPerVoxel 1 \
              --numThreads 4 \
              --numTensor 1 \
              --recordFA \
              --recordTrace \
              --freeWater \
              --recordFreeWater \
              —recordTensors
      """
      command = [slicer.modules.ukftractography.path,]
      scenario = 'neonate'
      if scenario == 'neonate':
        command.extend(['--stoppingThreshold 0.06',
                        '--stoppingFA 0.08',
                        '--seedingThreshold 0.10',
                        '--seedsPerVoxel 1'])
      command.extend(['--dwiFile', nrrdPath,
                      '--maskFile', maskPath,
                      '--labels 1',
                      '--numTensor 1',
                      '--freeWater',
                      '--tracts', os.path.join(tractsPath, "tracts.vtk")])
      self.runCommand(command, os.path.join(tractsPath, "ukftractography"))

    else:
      print("No baseline, so no tracts")


  def batchTract(self, convertedPath):
    ""
    db = slicer.dicomDatabase
    patients = db.patients()
    patientCount = 0 
    for patient in patients:
      patientCount += 1
      print(f"Patient {patient} ({patientCount} of {len(patients)})")
      for study in db.studiesForPatient(patient):
        print(f"Study {study}")
        for series in db.seriesForStudy(study):
          print(f"Series {series}")
          temporaryDir = qt.QTemporaryDir()
          for instanceUID in db.instancesForSeries(series):
            qt.QFile.copy(db.fileForInstance(instanceUID), temporaryDir.path()+f"/{instanceUID}.dcm")
          patientID = slicer.dicomDatabase.instanceValue(instanceUID, '0010,0020')
          # DWIConvert
          outputPath = os.path.join(convertedPath, patientID, study, series, "DWIConvert")
          if not os.path.exists(outputPath):
            os.makedirs(outputPath)
          nrrdPath = os.path.join(outputPath, series+".nrrd")
          outFP = open(os.path.join(outputPath, series+".stdout.txt"), 'w')
          errFP = open(os.path.join(outputPath, series+".stderr.txt"), 'w')
          dwiConvertProcess = subprocess.Popen([slicer.modules.dwiconvert.path,
                                                '-i', temporaryDir.path(),
                                                '-o', nrrdPath],
                                                stdout=outFP, stderr=errFP)
          dwiConvertProcess.wait()
          outFP.close()
          errFP.close()
          print('converted to ' + outputPath)
          if qt.QFileInfo(nrrdPath).exists():
            tractsPath = os.path.join(outputPath, "tracts")
            self.tractsFromNRRD(nrrdPath, tractsPath)

          # dcm2niix
          outputPath = os.path.join(convertedPath, patientID, study, series, "dcm2niix")
          if not os.path.exists(outputPath):
            os.makedirs(outputPath)
          outFP = open(os.path.join(outputPath, series+".stdout.txt"), 'w')
          errFP = open(os.path.join(outputPath, series+".stderr.txt"), 'w')
          dcm2niixPath = os.path.join(qt.QFileInfo(slicer.modules.dcm2niixgui.path).path(), "Resources/bin/dcm2niix")
          dcm2niixProcess = subprocess.Popen([dcm2niixPath,
                                                '-o', outputPath,
                                                '-f', series,
                                                '-e', 'y', # for nrrd
                                                '-z', 'o',
                                                temporaryDir.path()],
                                                stdout=outFP, stderr=errFP)
          dcm2niixProcess.wait()
          outFP.close()
          errFP.close()
          print('converted to ' + outputPath)
          for nrrdFile in qt.QDir(outputPath).entryList(["*.nhdr"]):
            tractsPath = os.path.join(outputPath, "tracts")
            self.tractsFromNRRD(nrrdPath, tractsPath)

          # dcm2niix nifti
          outputPath = os.path.join(convertedPath, patientID, study, series, "dcm2niix-nii")
          if not os.path.exists(outputPath):
            os.makedirs(outputPath)
          outFP = open(os.path.join(outputPath, series+".stdout.txt"), 'w')
          errFP = open(os.path.join(outputPath, series+".stderr.txt"), 'w')
          dcm2niixPath = os.path.join(qt.QFileInfo(slicer.modules.dcm2niixgui.path).path(), "Resources/bin/dcm2niix")
          dcm2niixProcess = subprocess.Popen([dcm2niixPath,
                                                '-o', outputPath,
                                                '-f', series,
                                                '-z', 'o',
                                                temporaryDir.path()],
                                                stdout=outFP, stderr=errFP)
          dcm2niixProcess.wait()
          outFP.close()
          errFP.close()
          print('converted to ' + outputPath)
      # break
    print("done")

  def tractResults(self, path):
    dirIt = qt.QDirIterator(path, ["*.vtk",], qt.QDir.Files, qt.QDirIterator.Subdirectories)
    tractResults = []
    while dirIt.hasNext():
      vtkPath = dirIt.next()
      parts = vtkPath.split('/')
      result = {
        "tractPath": vtkPath,
        "method": parts[-3],
        "seriesUID": parts[-4],
        "studyUID": parts[-5],
        "patientID": parts[-6],
      }
      tractResults.append(result)
    return tractResults

  def loadResult(self,result):
    slicer.mrmlScene.Clear()
    slicer.util.loadFiberBundle(result['tractPath'])
    dtiPath = f"{os.path.dirname(result['tractPath'])}/dti.nrrd"
    slicer.util.loadVolume(dtiPath)

  def screenshots(self,results):
    for result in results:
        self.loadResult(result)
        slicer.util.delayDisplay(result['tractPath'], 100)
        savePath = f"{os.path.dirname(result['tractPath'])}/screenshot.png"
        slicer.util.mainWindow().centralWidget().grab().toImage().save(savePath)
        print(savePath)



#
# BatchTractTest
#

class BatchTractTest(ScriptedLoadableModuleTest):
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
    self.test_BatchTract1()

  def test_BatchTract1(self):
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
