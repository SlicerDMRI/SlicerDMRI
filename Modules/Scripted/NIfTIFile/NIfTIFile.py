import logging
import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

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

def _NIfTIFileInstallPackage():
  try:
    import conversion
  except ModuleNotFoundError:
    slicer.util.pip_install("git+https://github.com/pnlbwh/conversion.git@v2.3")


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
    # assume yes if it ends in .nii.gz
    # TODO: check for .bval and .bvec in same directory
    return True

  def load(self, properties):
    try:

      _NIfTIFileInstallPackage()
      import conversion
      import nibabel
      import numpy


      filePath = properties['fileName']

      # Get node base name from filename
      if 'name' in properties.keys():
        baseName = properties['name']
      else:
        baseName = os.path.splitext(os.path.basename(filePath))[0]
      baseName = slicer.mrmlScene.GenerateUniqueName(baseName)
      diffusionNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLDiffusionWeightedVolumeNode', baseName)
      measurementFrame = vtk.vtkMatrix4x4()
      measurementFrame.Identity()
      measurementFrame.SetElement(0,0,-1)
      measurementFrame.SetElement(1,1,-1)
      diffusionNode.SetMeasurementFrameMatrix(measurementFrame)

      niftiImage = nibabel.load(filePath)

      affine = niftiImage.affine
      ijkToRAS = vtk.vtkMatrix4x4()
      for row in range(4):
        for column in range(4):
          ijkToRAS.SetElement(row, column, affine[row][column])
      diffusionNode.SetIJKToRASMatrix(ijkToRAS)

      fdata = niftiImage.get_fdata()
      diffusionArray = numpy.transpose(fdata, axes=[2,1,0,3])

      diffusionImage = vtk.vtkImageData()
      dshape = diffusionArray.shape
      diffusionImage.SetDimensions(dshape[2],dshape[1],dshape[0])
      diffusionImage.AllocateScalars(vtk.VTK_FLOAT, dshape[3])
      diffusionNode.SetAndObserveImageData(diffusionImage)

      nodeArray = slicer.util.arrayFromVolume(diffusionNode)
      nodeArray[:] = diffusionArray
      slicer.util.arrayFromVolumeModified(diffusionNode)


      pathBase = filePath[:-len(".nii.gz")]
      bvalPath = f"{pathBase}.bval"
      bvecPath = f"{pathBase}.bvec"
      bval = conversion.bval_bvec_io.read_bvals(bvalPath)
      bvec = conversion.bval_bvec_io.read_bvecs(bvecPath)

      diffusionNode.SetNumberOfGradients(len(bval))
      for index in range(len(bval)):
        diffusionNode.SetBValue(index, bval[index])
        diffusionNode.SetDiffusionGradient(index, bvec[index])

      diffusionNode.CreateDefaultDisplayNodes()

    except Exception as e:
      logging.error('Failed to load file: '+str(e))
      import traceback
      traceback.print_exc()
      return False

    self.parent.loadedNodes = [diffusionNode.GetID()]
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
