
#-----------------------------------------------------------------------------
set(MODULE_NAME TractographyLabelMapSeeding)

#-----------------------------------------------------------------------------

#
# SlicerExecutionModel
#
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME ${MODULE_NAME}
  LOGO_HEADER ${Slicer_ACTUAL_SOURCE_DIR}/Resources/ITKLogo.h
  TARGET_LIBRARIES vtkDMRI vtkTeem SlicerBaseLogic ${VTK_LIBRARIES}
  INCLUDE_DIRECTORIES
    ${vtkDMRI_INCLUDE_DIRS}
    ${vtkITK_INCLUDE_DIRS}
    ${vtkTeem_INCLUDE_DIRS}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  if(NOT WIN32)
    add_subdirectory(Testing)
  endif()
endif()
