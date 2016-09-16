cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerDMRI)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicerdmri.github.io")
set(EXTENSION_CATEGORY "Diffusion")
set(EXTENSION_CONTRIBUTORS "Isaiah Norton, Lauren O'Donnell (Brigham & Women's Hospital)")
set(EXTENSION_DESCRIPTION "SlicerDMRI is an umbrella extension for Slicer Diffusion MRI functionality.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SlicerDMRI.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SlicerDMRI/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer COMPONENTS ConfigurePrerequisites REQUIRED)
project(SlicerDMRI)
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

if(NOT ${Slicer_USE_vtkTeem})
  message(FATAL_ERROR "SlicerDMRI requires Slicer_USE_vtkTeem")
endif()
#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory("Modules/Loadable/TractographyDisplay")
add_subdirectory("Modules/Loadable/TractographyInteractiveSeeding")

add_subdirectory("Modules/CLI/DWIToDTIEstimation")
add_subdirectory("Modules/CLI/DiffusionWeightedVolumeMasking")
add_subdirectory("Modules/CLI/DiffusionTensorScalarMeasurements")
add_subdirectory("Modules/CLI/FiberTractMeasurements")
add_subdirectory("Modules/CLI/TractographyLabelMapSeeding")
add_subdirectory("Modules/CLI/FiberBundleLabelSelect")

add_subdirectory("Modules/Scripted/DICOM2FullBrainTractography")
add_subdirectory("Modules/Scripted/FiberBundleToLabelMap")

if (${SlicerDMRI_ENABLE_TRACTIO})
  add_subdirectory("Modules/Loadable/TractIO")
endif()

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
#set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${Foo_DIR};Foo;RuntimeLibraries;/")
include(${Slicer_EXTENSION_CPACK})
