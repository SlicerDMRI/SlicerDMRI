import logging
import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import trako

class TRAKOFile(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = 'TRAKOFile'
    parent.categories = ['Testing.TestCases']
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)", "Daniel Haehn (UMass Boston)", "Jean-Christophe Fillion-Robin (Kitware)", "Andras Lasso (PerkLab, Queen's)"]
    parent.helpText = '''
    This module is used to implement trako reading and writing
    '''
    parent.acknowledgementText = '''
    Supported by NIH Grant 5R01MH119222
    '''
    self.parent = parent

class TRAKOFileWidget(ScriptedLoadableModuleWidget):
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Default reload&test widgets are enough.
    # Note that reader and writer is not reloaded.

class TRAKOFileFileReader(object):

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return 'TRAKO FiberBundle'

  def fileType(self):
    return 'TRAKO'

  def extensions(self):
    return ['TRAKO (*.tko)']

  def canLoadFile(self, filePath):
    # assume yes if it ends in .tko
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

      polyData = trako.gltfi2vtk.convert(filePath)

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


class TRAKOFileFileWriter(object):

  def __init__(self, parent):
    self.parent = parent

  def description(self):
    return 'TRAKO FiberBundle'

  def fileType(self):
    return 'TRAKO'

  def extensions(self, obj):
    return ['TRAKO (*.tko)']

  def canWriteObject(self, obj):
    # Only enable this writer in testing mode
    if not slicer.app.testingEnabled():
      return False

    return bool(obj.IsA("vtkMRMLTextNode"))

  def write(self, properties):
    # TODO: expose more compression options
    try:

      # Get node
      fiberBundleNode = slicer.mrmlScene.GetNodeByID(properties["nodeID"])
      polyData = fiberBundleNode.GetPolyData()

      # Write node content to file
      filePath = properties['fileName']
      fibercluster = trako.vtk2gltfi.convert(polyData)
      tko = trako.vtk2gltfi.fibercluster2gltf(fibercluster, draco=True)
      tko.save(filePath)

    except Exception as e:
      logging.error('Failed to write file: '+str(e))
      import traceback
      traceback.print_exc()
      return False

    self.parent.writtenNodes = [fiberBundleNode.GetID()]
    return True


class TRAKOFileTest(ScriptedLoadableModuleTest):
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
    self.validFilename = self.tempDir + "/tempTRAKOFileValid.tko"
    self.invalidFilename = self.tempDir + "/tempTRAKOFileInvalid.tko"
    slicer.mrmlScene.Clear()

  def tearDown(self):
    import shutil
    shutil.rmtree(self.tempDir, True)

  def test_WriterReader(self):
    # Writer and reader tests are put in the same function to ensure
    # that writing is done before reading (it generates input data for reading).

    # TODO: rewrite this for TRAKO

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
