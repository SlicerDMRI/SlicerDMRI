#-----------------------------------------------------------------------------
set(MODULE_NAME DiffusionWeightedVolumeMasking)

# Avoid vtkNRRDReader/vtkNrrdReader filename confusion on case insensitive file systems
include_directories(BEFORE ${vtkTeem_INCLUDE_DIRS})

#-----------------------------------------------------------------------------

#
# SlicerExecutionModel
#
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

#-----------------------------------------------------------------------------
set(${MODULE_NAME}_TARGET_LIBRARIES
  MRMLCore vtkTeem ${VTK_LIBRARIES}
  )

#-----------------------------------------------------------------------------
# NOTE: this must be changed for future ITK versions
set(ITK_SOURCE_PATH ${Slicer_HOME}/../ITKv4/)

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  LOGO_HEADER ${Slicer_ACTUAL_SOURCE_DIR}/Resources/ITKLogo.h
  INCLUDE_DIRECTORIES
    ${Slicer_ACTUAL_SOURCE_DIR}
    ${ITK_SOURCE_PATH}/Modules/Bridge/VTK/include
    ${ITK_SOURCE_PATH}/Modules/Bridge/VtkGlue/include
    ${vtkITK_INCLUDE_DIRS}
    ${MRMLCore_INCLUDE_DIRS}
    ${vtkTeem_INCLUDE_DIRS}
    ${vtkSlicerEditorLibModuleLogic_INCLUDE_DIRS}
  TARGET_LIBRARIES ${${MODULE_NAME}_TARGET_LIBRARIES}
  EXECUTABLE_ONLY
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()
