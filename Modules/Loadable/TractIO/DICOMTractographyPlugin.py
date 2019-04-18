import os
import vtk, qt, ctk, slicer
from DICOMLib import DICOMPlugin
from DICOMLib import DICOMLoadable

#
# This is the plugin to handle translation of diffusion volumes
# from DICOM files into MRML nodes.  It follows the DICOM module's
# plugin architecture.
#

class DICOMTractographyPluginClass(DICOMPlugin):
  """ DiffusionVolume specific interpretation code
  """

  def __init__(self):
    super(DICOMTractographyPluginClass,self).__init__()
    self.loadType = "DICOM Tractography"
    self.tags = dict(enumerate(
            [
            "0066,0101", # TrackSetSequence
            "0066,0102"  # TrackSequence, at least one
            ]
            ))

    # note: the tags here are organized by vendor above, but
    # for the tag caching, we create a compatible tags
    # array for use by the application
    tagIndex = 0
    self.tags['seriesDescription'] = "0008,103e"

  def examineForImport(self,fileLists):
    """ Returns a list of DICOMLoadable instances
    corresponding to ways of interpreting the
    fileLists parameter.
    """
    loadables = []
    for files in fileLists:
      loadables += self.examineFiles(files)
    return loadables

  def examineFiles(self,files):
    """ Returns a list of DICOMLoadable instances
    corresponding to ways of interpreting the
    files parameter.
    Process is to look for 'known' private tags corresponding
    to the types of diffusion datasets that the DicomToNrrd utility
    should be able to process.  Only need to look at one header
    in the series since all should be the same with respect
    to this check.

    For testing:
    dv = slicer.modules.dicomPlugins['DICOMTractographyPlugin']()
    dv.examineForImport([['/media/extra650/data/DWI-examples/SiemensTrioTimB17-DWI/63000-000025-000001.dcm']])
    """

    # get the series description to use as base for volume name
    name = slicer.dicomDatabase.fileValue(files[0], self.tags['seriesDescription'])
    if name == "":
      name = "Unknown"

    validTractObject = False
    for tag in self.tags.keys():
      value = slicer.dicomDatabase.fileValue(files[0], tag)
      hasTag = (value != "")
      validTractObject = True

    vendorName = slicer.dicomDatabase.fileValue(files[0], "0008,0070")

    loadables = []
    if validTractObject:
      # default loadable includes all files for series
      loadable = DICOMLoadable()
      loadable.files = files
      loadable.name = name + ' - as DWI Volume'
      loadable.selected = False
      loadable.tooltip = "Appears to be DWI from vendor %s" % vendorName
      loadable.confidence = 0.75
      loadables = [loadable]
    return loadables

  def load(self,loadable):
    """Load the selection as a diffusion volume
    using the dicom to nrrd converter module
    """

    if not hasattr(slicermodules, 'tractiocli'):
      raise Exception("No TractIOCLI module available to perform load operation!")

    # create an output diffusion node as a target
    nodeFactory = slicer.qMRMLNodeFactory()
    nodeFactory.setMRMLScene(slicer.mrmlScene)
    diffusionNode = nodeFactory.createNode('vtkMRMLFiberBundleNode')
    diffusionNode.SetName(loadable.name)
    # set up the parameters
    parameters = {}
    tempDir = slicer.util.tempDirectory()
    import shutil
    for filePath in loadable.files:
      base = os.path.basename(filePath)
      shutil.copy(filePath, os.path.join(tempDir, base))
    parameters['inputDicomDirectory'] = tempDir
    parameters['outputDirectory'] = slicer.app.temporaryPath
    parameters['outputVolume'] = diffusionNode.GetID()
    # run the module
    tractIOCLI = slicer.modules.tractiocli
    cliNode = slicer.cli.run(dicomDWIConverter, None, parameters, wait_for_completion = True)
    success = False
    if cliNode.GetStatusString() == "Completing" or cliNode.GetStatusString() == "Completed":
      if diffusionNode.GetImageData():
        success = True

    # create Subject Hierarchy nodes for the loaded series
    self.addSeriesInSubjectHierarchy(loadable,diffusionNode)

    # remove temp directory of dwi series
    shutil.rmtree(tempDir)

    return success


#
# DICOMTractographyPlugin
#

class DICOMTractographyPlugin:
  """
  This class is the 'hook' for slicer to detect and recognize the plugin
  as a loadable scripted module
  """
  def __init__(self, parent):
    parent.title = "DICOM Tractography Object Plugin"
    parent.categories = ["Developer Tools.DICOM Plugins"]
    parent.contributors = ["Isaiah Norton (BWH), Steve Pieper (Isomics, Inc.)"]
    parent.helpText = """
    Plugin to the DICOM Module to parse and load diffusion tractography
    from DICOM files.
    No module interface here, only in the DICOM module
    """
    parent.acknowledgementText = """
    The to DICOM Tractography plugin was developed by
    Isaiah Norton, Brigham & Women's Hospital,
    partially funded by NIH grant U01 CA199459.
      based on:
    The DICOM Volume Plugin developed by
    Steve Pieper, Isomics, Inc.
    and was partially funded by NIH grant 3P41RR013218,
    """

    # Add this extension to the DICOM module's list for discovery when the module
    # is created.  Since this module may be discovered before DICOM itself,
    # create the list if it doesn't already exist.
    try:
      slicer.modules.dicomPlugins
    except AttributeError:
      slicer.modules.dicomPlugins = {}
    slicer.modules.dicomPlugins['DICOMTractographyPlugin'] = DICOMTractographyPluginClass
