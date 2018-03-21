cmake_minimum_required(VERSION 3.5)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerDMRI)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicerdmri.github.io")
set(EXTENSION_CATEGORY "Diffusion")
set(EXTENSION_CONTRIBUTORS "Isaiah Norton, Lauren O'Donnell (Brigham & Women's Hospital)")
set(EXTENSION_DESCRIPTION "SlicerDMRI is an umbrella extension for Slicer Diffusion MRI functionality.")
set(EXTENSION_ICONURL "http://raw.githubusercontent.com/SlicerDMRI/slicerdmri.github.io/master/images/DMRI_3D_SLICER-icon.png")
set(EXTENSION_SCREENSHOTURLS "https://www.slicer.org/slicerWiki/images/0/09/SlicerDMRIScreenshot.jpg")
set(EXTENSION_DEPENDS "UKFTractography") # Specified as a space separated list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

option(SlicerDMRI_ENABLE_TRACTIO "Enable TractIO module" ON)
mark_as_advanced(SlicerDMRI_ENABLE_TRACTIO)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer COMPONENTS ConfigurePrerequisites REQUIRED)
project(SlicerDMRI)
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

if(NOT ${Slicer_USE_vtkTeem})
  message(FATAL_ERROR "SlicerDMRI requires Slicer_USE_vtkTeem")
endif()

get_filename_component(Slicer_ACTUAL_SOURCE_DIR "${Slicer_CMAKE_DIR}/../"
                       ABSOLUTE CACHE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Set variables for testing local build, if not defined
if (NOT DEFINED TEMP)
  set(TEMP "${CMAKE_BINARY_DIR}/Testing/Temporary")
endif()
if (NOT DEFINED MRML_TEST_DATA)
  set(MRML_TEST_DATA "${Slicer_CMAKE_DIR}/../Libs/MRML/Core/Testing/TestData")
endif()

#-----------------------------------------------------------------------------
# Common library
add_subdirectory("Libs/vtkDMRI")

# Extension modules
add_subdirectory("Modules/Loadable/TractographyDisplay")
add_subdirectory("Modules/Loadable/InteractiveSeeding")

add_subdirectory("Modules/CLI/DWIToDTIEstimation")
add_subdirectory("Modules/CLI/DiffusionWeightedVolumeMasking")
add_subdirectory("Modules/CLI/DiffusionTensorScalarMeasurements")
add_subdirectory("Modules/CLI/FiberTractMeasurements")
add_subdirectory("Modules/CLI/TractographyLabelMapSeeding")
add_subdirectory("Modules/CLI/FiberBundleLabelSelect")

add_subdirectory("Modules/Scripted/DICOM2FullBrainTractography")
add_subdirectory("Modules/Scripted/FiberBundleToLabelMap")
add_subdirectory("Modules/Scripted/DICOMPlugins")
  add_subdirectory("Modules/Scripted/TractographyExportPLY")

if (${SlicerDMRI_ENABLE_TRACTIO})
  add_subdirectory("Modules/Loadable/TractIO")
endif()

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
#set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${Foo_DIR};Foo;RuntimeLibraries;/")
include(${Slicer_EXTENSION_CPACK})
