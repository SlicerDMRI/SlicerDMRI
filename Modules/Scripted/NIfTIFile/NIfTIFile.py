import logging
import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import nifti

class NIfTIFile(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = 'NIfTIFile'
    parent.categories = ['Testing.TestCases']
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)", ]
    parent.helpText = '''
    This module is used to implement diffusion nifti reading and writing using the conversion tool from PNL at BWH.
    '''
    parent.acknowledgementText = '''
    Thanks to:

    Billah, Tashrif; Bouix; Sylvain; Rathi, Yogesh; Various MRI Conversion Tools, https://github.com/pnlbwh/conversion, 2019, DOI: 10.5281/zenodo.2584003

    Supported by NIH Grant 5R01MH119222
    '''
    self.parent = parent

class NIfTIFileWidget(ScriptedLoadableModuleWidget):
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Default reload&test widgets are enough.
    # Note that reader and writer is not reloaded.

class NIfTIFileFileReader(object):

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return 'NIfTI Diffusion'

  def fileType(self):
    return 'NIfTI'

  def extensions(self):
    return ['NIfTI (*.nii.gz)']

  def canLoadFile(self, filePath):
    # assume yes if it ends in .tko
    # TODO: check for .bval and .bvec in same directory
    return True

  def load(self, properties):
    try:
      filePath = properties['fileName']

      # Get node base name from filename
      if 'name' in properties.keys():
        baseName = properties['name']
      else:
        baseName = os.path.splitext(os.path.basename(filePath))[0]
      baseName = slicer.mrmlScene.GenerateUniqueName(baseName)

      polyData = nifti.gltfi2vtk.convert(filePath)

      fiberBundleNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLFiberBundleNode', baseName)
      fiberBundleNode.SetAndObservePolyData(polyData)
      fiberBundleNode.CreateDefaultDisplayNodes()

    except Exception as e:
      logging.error('Failed to load file: '+str(e))
      import traceback
      traceback.print_exc()
      return False

    self.parent.loadedNodes = [fiberBundleNode.GetID()]
    return True


class NIfTIFileFileWriter(object):

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return 'NIfTI Diffusion'

  def fileType(self):
    return 'NIfTI'

  def extensions(self, obj):
    return ['NIfTI (*.nii.gz)']

  def canWriteObject(self, obj):
    # Only enable this writer in testing mode
    if not slicer.app.testingEnabled():
      return False

    return bool(obj.IsA("vtkMRMLDiffusionWeightedVolumeNode"))

  def write(self, properties):
    # TODO: expose more compression options
    try:

      # Get node
      fiberBundleNode = slicer.mrmlScene.GetNodeByID(properties["nodeID"])
      polyData = fiberBundleNode.GetPolyData()

      # Write node content to file
      filePath = properties['fileName']
      fibercluster = nifti.vtk2gltfi.convert(polyData)
      tko = nifti.vtk2gltfi.fibercluster2gltf(fibercluster, draco=True)
      tko.save(filePath)

    except Exception as e:
      logging.error('Failed to write file: '+str(e))
      import traceback
      traceback.print_exc()
      return False

    self.parent.writtenNodes = [fiberBundleNode.GetID()]
    return True


class NIfTIFileTest(ScriptedLoadableModuleTest):
  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_Writer()
    self.test_Reader()
    self.tearDown()
    self.delayDisplay('Testing complete')

  def setUp(self):
    self.tempDir = slicer.util.tempDirectory()
    logging.info("tempDir: " + self.tempDir)
    self.textInNode = "This is\nsome example test"
    self.validFilename = self.tempDir + "/tempNIfTIFileValid.tko"
    self.invalidFilename = self.tempDir + "/tempNIfTIFileInvalid.tko"
    slicer.mrmlScene.Clear()

  def tearDown(self):
    import shutil
    shutil.rmtree(self.tempDir, True)

  def test_WriterReader(self):
    # Writer and reader tests are put in the same function to ensure
    # that writing is done before reading (it generates input data for reading).

    # TODO: rewrite this for NIfTI

    self.delayDisplay('Testing node writer')
    slicer.mrmlScene.Clear()
    textNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTextNode')
    textNode.SetText(self.textInNode)
    self.assertTrue(slicer.util.saveNode(textNode, self.validFilename, {'fileType': 'MyFileType'}))

    self.delayDisplay('Testing node reader')
    slicer.mrmlScene.Clear()
    loadedNode = slicer.util.loadNodeFromFile(self.validFilename, 'MyFileType')
    self.assertIsNotNone(loadedNode)
    self.assertTrue(loadedNode.IsA('vtkMRMLTextNode'))
    self.assertEqual(loadedNode.GetText(), self.textInNode)
