import glob
import json
import os
import shutil
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
    self.batchPath.currentPath = "/Volumes/SSD2T/data/pedistroke/converted-eddy"

    self.batchTractButton = qt.QPushButton("Run Batch Tract")
    self.parametersFormLayout.addWidget(self.batchTractButton)
    self.batchTractButton.connect('clicked()', self.batchTract)

    self.reviewButton = qt.QPushButton("Review")
    self.parametersFormLayout.addWidget(self.reviewButton)
    self.reviewButton.connect('clicked()', self.review)

    self.screenshotsButton = qt.QPushButton("Make screenshots")
    self.parametersFormLayout.addWidget(self.screenshotsButton)
    self.screenshotsButton.connect('clicked()', self.screenshots)

    self.pediTractButton = qt.QPushButton("Pedi tract")
    self.parametersFormLayout.addWidget(self.pediTractButton)
    self.pediTractButton.connect('clicked()', self.pediTract)

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

  def pediTract(self):
    self.logic.pediTract(self.batchPath.currentPath)

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
    exitCode = subprocess.Popen(command, stdout=outFP, stderr=errFP).wait()
    outFP.close()
    errFP.close()
    if exitCode != 0:
        print(f"command exited with {exitCode}")
        print(command)
        print(f"outputs in {outputBasePath}")
    return(exitCode)

  def tractsFromNRRD(self, nrrdPath, tractsPath):
    return #TODO
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


  def eddyCorrect(self, niiPath, outputPath):
    print(f"eddy correcting {niiPath} to {outputPath}")

    bvecPath = glob.glob(f"{niiPath}/*.bvec")[0]
    gradients = open(bvecPath).read()
    gradientCount = len(gradients.split()) / 3
    if gradientCount <= 3 or gradientCount != int(gradientCount):
      print("bad gradients or 3 or fewer gradients, not worth correcting")
      return

    fp = open(f"{niiPath}/index.txt", "w")
    fp.write("1 "*int(gradientCount))
    fp.close()
    fp = open(f"{niiPath}/acqparams.txt", "w")
    fp.write("0 1 0 0.095\n") # TODO compute from json
    fp.close()

    print("copying run-eddy.sh")
    shutil.copy(f"{os.path.dirname(slicer.modules.batchtract.path)}/Resources/run-eddy.sh", niiPath)

    outFP = open(os.path.join(outputPath, "eddy.stdout.txt"), 'w')
    errFP = open(os.path.join(outputPath, "eddy.stderr.txt"), 'w')

    print("deleting")
    cmd = "gcloud --project project-7519307760985532298 compute ssh freesurfer-synth --command".split()
    cmd.append('rm -rf /usr/local/data/eddy-subject/dcm2niix-nii')
    process = slicer.util.launchConsoleProcess(cmd)
    process.wait()
    outFP.write(str(process.communicate()))

    print("copying data")
    cmd = "gcloud --project project-7519307760985532298 compute scp --recurse "
    cmd += f"{niiPath} freesurfer-synth:/usr/local/data/eddy-subject"
    process = slicer.util.launchConsoleProcess(cmd.split())
    process.wait()
    outFP.write(str(process.communicate()))

    print("changing permissions")
    cmd = "gcloud --project project-7519307760985532298 compute ssh freesurfer-synth --command".split()
    cmd.append("sudo chmod -R a+rw /usr/local/data/eddy-subject")
    process = slicer.util.launchConsoleProcess(cmd)
    process.wait()
    outFP.write(str(process.communicate()))

    print("running run-eddy.sh")
    cmd = "gcloud --project project-7519307760985532298 compute ssh freesurfer-synth --command".split()
    cmd.append("sudo su - pieper -c '/bin/bash /usr/local/data/eddy-subject/dcm2niix-nii/run-eddy.sh'")
    process = slicer.util.launchConsoleProcess(cmd)
    process.wait()
    outFP.write(str(process.communicate()))

    print("copying results")
    cmd = f"gcloud --project project-7519307760985532298 compute scp --recurse freesurfer-synth:/usr/local/data/eddy-subject/dcm2niix-nii/ {outputPath}"
    process = slicer.util.launchConsoleProcess(cmd.split())
    process.wait()
    outFP.write(str(process.communicate()))

    print(f"Eddy corrected data in {outputPath}")

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
          # if series != "1.3.12.2.1107.5.2.32.35288.2013022319050913362263496.0.0.0":
            # print(f"skipping {series}")
            # continue
          for instanceUID in db.instancesForSeries(series):
            qt.QFile.copy(db.fileForInstance(instanceUID), temporaryDir.path()+f"/{instanceUID}.dcm")
          patientID = slicer.dicomDatabase.instanceValue(instanceUID, '0010,0020')
          # DWIConvert
          outputPath = os.path.join(convertedPath, patientID, study, series, "DWIConvert")
          if not os.path.exists(outputPath):
            os.makedirs(outputPath)
          nrrdPath = os.path.join(outputPath, series+".nrrd")
          if not os.path.exists(nrrdPath):
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
          if len(glob.glob(f"{outputPath}/*")) == 0:
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
              self.tractsFromNRRD(nrrdFile, tractsPath)

          # dcm2niix nifti
          outputPath = os.path.join(convertedPath, patientID, study, series, "dcm2niix-nii")
          if not os.path.exists(outputPath):
            os.makedirs(outputPath)
          if len(glob.glob(f"{outputPath}/*")) == 0:
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

          if len(glob.glob(f"{outputPath}/*.bvec")) > 0:
            eddyPath = os.path.join(convertedPath, patientID, study, series, "eddy")
            if not os.path.exists(eddyPath):
              os.makedirs(eddyPath)
            if len(glob.glob(f"{eddyPath}/*")) == 0:
              print('Running eddy current correction to ' + eddyPath)
              self.eddyCorrect(outputPath, eddyPath)
          else:
            print(f"No bval for {outputPath}")

      # break
    print("done")

  def tractResultsCompareConverters(self, path):
    """ load tract results to compare dcm2niix vs DWIConvert
    """
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

  def tractResults(self, path):
    """ load results from eddy corrected files
    """
    dirIt = qt.QDirIterator(path, ["*backscaled*",], qt.QDir.Dirs, qt.QDirIterator.Subdirectories)
    tractResults = []
    while dirIt.hasNext():
      backscalePath = dirIt.next()
      parts = backscalePath.split('/')
      result = {
        "tractPath": backscalePath,
        "method": parts[-3],
        "seriesUID": parts[-5],
        "studyUID": parts[-6],
        "patientID": parts[-7],
      }
      tractResults.append(result)
    return tractResults

  def loadResultCompareConverters(self,result):
    slicer.mrmlScene.Clear()
    slicer.util.loadFiberBundle(result['tractPath'])
    dtiPath = f"{os.path.dirname(result['tractPath'])}/dti.nrrd"
    slicer.util.loadVolume(dtiPath)

  def loadResult(self,result):
    path = result['tractPath']
    slicer.mrmlScene.Clear()
    fiberIt = qt.QDirIterator(path, ["*.vtp",], qt.QDir.Files, qt.QDirIterator.Subdirectories)
    while fiberIt.hasNext():
        slicer.util.loadFiberBundle(fiberIt.next())
    noeddyPath = glob.glob(f"{path}/../../*-noeddy.nii.gz.nhdr")[0]
    slicer.util.loadVolume(noeddyPath)

  def screenshots(self,results):
    for result in results:
        self.loadResult(result)
        slicer.util.delayDisplay(result['tractPath'], 100)
        savePath = f"{os.path.dirname(result['tractPath'])}/screenshot.png"
        slicer.util.mainWindow().centralWidget().grab().toImage().save(savePath)
        print(savePath)

  def _NIfTIFileInstallPackage():
    try:
      import conversion
    except ModuleNotFoundError:
      slicer.util.pip_install("git+https://github.com/pnlbwh/conversion.git@v2.3")

  def find_files(self, directory, pattern):
    """ https://stackoverflow.com/questions/2186525/how-to-use-glob-to-find-files-recursively
    faster for testing than: rotatedBvecs = glob.glob(f"{dataPath}/**/*rotated*", recursive=True)
    """
    import os, fnmatch
    for root, dirs, files in os.walk(directory):
      for basename in files:
        if fnmatch.fnmatch(basename, pattern):
          filename = os.path.join(root, basename)
          yield filename

  def pediTract(self, dataPath):
    self._NIfTIFileInstallPackage
    import conversion
    import os
    count = 0
    for rotatedBvecPath in self.find_files(dataPath, '*rotated*'):
        slicer.mrmlScene.Clear()

        # make nhdr file
        correctedNIIPath = rotatedBvecPath[:-1 * len(".eddy_rotated_bvecs")]
        bvalPath = correctedNIIPath[:-1 * len("-noeddy.nii.gz")] + ".bval"
        nhdrPath = correctedNIIPath + ".nhdr"
        conversion.nhdr_write(correctedNIIPath, bvalPath, rotatedBvecPath, nhdrPath)
        niiDirPath = os.path.dirname(correctedNIIPath)

        # perform tractography
        print("tractography...")
        tractsPath = os.path.join(niiDirPath, "tracts")
        if not os.path.exists(tractsPath):
            os.makedirs(tractsPath)
        maskNode = slicer.util.loadVolume(f'{niiDirPath}/bet-mask.nii.gz')
        castFilter = vtk.vtkImageCast()
        castFilter.SetInputData(maskNode.GetImageData())
        castFilter.SetOutputScalarTypeToShort()
        castFilter.Update()
        maskNode.SetAndObserveImageData(castFilter.GetOutputDataObject(0))
        slicer.util.saveNode(maskNode, f'{niiDirPath}/bet-mask.nrrd')
        command = [slicer.modules.ukftractography.path,
                     '--stoppingThreshold', '0.06',
                     '--stoppingFA', '0.08',
                     '--seedingThreshold', '0.10',
                     '--seedsPerVoxel', '1',
                     '--dwiFile', nhdrPath,
                     '--maskFile', f'{niiDirPath}/bet-mask.nrrd',
                     '--labels', '1',
                     '--numTensor', '1',
                     '--freeWater',
                     '--tracts',
                     f'{tractsPath}/tracts.vtk',
                  ]
        self.runCommand(command, tractsPath)

        # scale to adult size
        print("scale...")
        tfmPath = os.path.join(os.path.dirname(slicer.modules.batchtract.path),
                    "Resources/dHCP_enlarge1.5.tfm")
        tractsScaledPath = f'{tractsPath}/tracts-scaled'
        if not os.path.exists(tractsScaledPath):
            os.makedirs(tractsScaledPath)
        command = ['wm_harden_transform.py',
                '-t', tfmPath,
                f'{tractsPath}',
                f'{tractsScaledPath}',
                f'{slicer.app.slicerHome}/Slicer',
                ]
        print(command)
        self.runCommand(command, tractsScaledPath)

        # apply white matter analysis
        print("WMA...")
        command = ['wm_apply_ORG_atlas_to_subject.sh',
                '-n', '20',
                '-i', f'{tractsScaledPath}/tracts.vtk',
                '-o', f'{tractsScaledPath}',
                '-a', f'/Volumes/SSD2T/data/pedistroke/scratch/ORG-Atlases-1.1.1',
                '-s', f'{slicer.app.slicerHome}/Slicer',
                '-d',
                '-m', '/Users/pieper/slicer/latest/SlicerDMRI-build/inner-build/lib/Slicer-5.1/cli-modules/FiberTractMeasurements',
                ]
        print(command)
        self.runCommand(command, tractsScaledPath+"_WMA")

        # scale back to baby space
        print("backscale...")
        tractsBackscaledPath = f'{tractsPath}/tracts-backscaled'
        if not os.path.exists(tractsBackscaledPath):
            os.makedirs(tractsBackscaledPath)
        command = ['wm_harden_transform.py',
                '-i',
                '-t', tfmPath,
                f'{tractsScaledPath}/tracts/AnatomicalTracts',
                f'{tractsBackscaledPath}',
                f'{slicer.app.slicerHome}/Slicer',
                ]
        print(command)
        self.runCommand(command, tractsBackscaledPath)

        count += 1
        print(f"Finished {count}")
        print(f"ooO*Ooo")
        # break


        #diffusionNode - slicer.util.loadVolume(nhdrPath)
    print("done")


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
