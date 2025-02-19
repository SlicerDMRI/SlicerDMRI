cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerDMRI)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://dmri.slicer.org/")
set(EXTENSION_CATEGORY "Diffusion")
set(EXTENSION_CONTRIBUTORS "Lauren O'Donnell (Brigham & Women's Hospital), Isaiah Norton (Brigham & Women's Hospital), Fan Zhang (Brigham & Women's Hospital), Alex Yarmarkovich (Brigham & Women's Hospital), Jon Haitz Legarreta Gorroño (Brigham & Women's Hospital)")
set(EXTENSION_DESCRIPTION "SlicerDMRI provides tools to load diffusion MRI image data, perform tractography, and quantify results.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/SlicerDMRI/slicerdmri.github.io/master/images/DMRI_3D_SLICER-icon.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/SlicerDMRI/slicerdmri.github.io/master/images/DMRI_3D_SLICER.jpg")
set(EXTENSION_DEPENDS "UKFTractography", "SlicerDcm2nii") # Specified as a space separated list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)


#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer COMPONENTS ConfigurePrerequisites REQUIRED)
project(SlicerDMRI)
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

# Required to include "Slicer/Resources/*Logo.h" files
get_filename_component(Slicer_ACTUAL_SOURCE_DIR "${Slicer_CMAKE_DIR}/../" ABSOLUTE CACHE)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

# Sanity checks
if(NOT ${Slicer_USE_vtkTeem})
  message(FATAL_ERROR "SlicerDMRI requires Slicer_USE_vtkTeem")
endif()

#-----------------------------------------------------------------------------
# Options
option(SlicerDMRI_ENABLE_TRACTIO "Enable TractIO module" ON)
mark_as_advanced(SlicerDMRI_ENABLE_TRACTIO)
mark_as_superbuild(SlicerDMRI_ENABLE_TRACTIO)

option(SlicerDMRI_ENABLE_RegisterDMRIModuleTemplates "Enable RegisterDMRIModuleTemplates module" ON)
mark_as_advanced(SlicerDMRI_ENABLE_RegisterDMRIModuleTemplates)
mark_as_superbuild(SlicerDMRI_ENABLE_RegisterDMRIModuleTemplates)

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
if(NOT DEFINED TEMP)
  set(TEMP "${CMAKE_BINARY_DIR}/Testing/Temporary")
endif()
if(NOT DEFINED MRML_TEST_DATA)
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
add_subdirectory("Modules/CLI/ExtractDWIShells")

add_subdirectory("Modules/Scripted/DICOM2FullBrainTractography")
add_subdirectory("Modules/Scripted/FiberBundleToLabelMap")
add_subdirectory("Modules/Scripted/DMRIPlugins")
if(SlicerDMRI_ENABLE_RegisterDMRIModuleTemplates)
  add_subdirectory("Modules/Scripted/RegisterDMRIModuleTemplates")
endif()
add_subdirectory("Modules/Scripted/TractographyExportPLY")
add_subdirectory("Modules/Scripted/TractographyDownsample")
add_subdirectory("Modules/Scripted/NIfTIFile")

if (${SlicerDMRI_ENABLE_TRACTIO})
  add_subdirectory("Modules/Loadable/TractIO")
endif()

#-----------------------------------------------------------------------------
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
#set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${Foo_DIR};Foo;RuntimeLibraries;/")
include(${Slicer_EXTENSION_CPACK})
