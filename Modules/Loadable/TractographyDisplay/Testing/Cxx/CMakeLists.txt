set(KIT qSlicer${MODULE_NAME}Module)

set(INPUT ${CMAKE_CURRENT_SOURCE_DIR}/../Data/Input)

# Download test data into build directory
foreach(hash_and_filename IN ITEMS
    "06d5b5777915857fbac7b3cbd9c371523d1371f29b0c89eb7a33d86d780d5b2b:tract1.vtk"
    )
  string(REPLACE ":" ";" hash_and_filename ${hash_and_filename})
  list(GET hash_and_filename 0 _hash)
  list(GET hash_and_filename 1 _filename)
  file(DOWNLOAD
    https://github.com/Slicer/slicer.kitware.com-midas3-archive/releases/download/SHA256/${_hash}
    ${INPUT}/${_filename}
    EXPECTED_HASH SHA256=${_hash}
    )
endforeach()

#-----------------------------------------------------------------------------
set(KIT_TEST_SRCS
  qSlicerTractographyDisplayGlyphWidgetTest1.cxx
  vtkMRMLFiberBundleDisplayNodeTest1.cxx
  vtkMRMLFiberBundleGlyphDisplayNodeTest1.cxx
  vtkMRMLFiberBundleLineDisplayNodeTest1.cxx
  vtkMRMLFiberBundleNodeTest1.cxx
  vtkMRMLFiberBundleStorageNodeTest1.cxx
  vtkMRMLFiberBundleTubeDisplayNodeTest1.cxx
  vtkSlicerFiberBundleLogicTest.cxx
  )

#-----------------------------------------------------------------------------
slicerMacroConfigureModuleCxxTestDriver(
  NAME ${KIT}
  SOURCES ${KIT_TEST_SRCS}
  WITH_VTK_DEBUG_LEAKS_CHECK
  WITH_VTK_ERROR_OUTPUT_CHECK
  )

#-----------------------------------------------------------------------------
simple_test(qSlicerTractographyDisplayGlyphWidgetTest1)
simple_test(vtkMRMLFiberBundleDisplayNodeTest1)
simple_test(vtkMRMLFiberBundleGlyphDisplayNodeTest1)
simple_test(vtkMRMLFiberBundleLineDisplayNodeTest1)
simple_test(vtkMRMLFiberBundleNodeTest1 ${INPUT}/helix_roi_tract.mrml)
simple_test(vtkMRMLFiberBundleStorageNodeTest1)
simple_test(vtkMRMLFiberBundleTubeDisplayNodeTest1)
simple_test(vtkSlicerFiberBundleLogicTest ${INPUT}/tract1.vtk ${INPUT}/tract1_out.vtk)
