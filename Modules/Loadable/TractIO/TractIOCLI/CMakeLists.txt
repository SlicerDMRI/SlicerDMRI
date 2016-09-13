#-----------------------------------------------------------------------------
set(MODULE_NAME TractIOCLI)

#-----------------------------------------------------------------------------

# SlicerExecutionModel
find_package(SlicerExecutionModel REQUIRED)
include(${SlicerExecutionModel_USE_FILE})

# DCMTK
find_package(DCMTK REQUIRED)

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME VTK_to_DICOMTract
  LOGO_HEADER ${Slicer_SOURCE_DIR}/Resources/NAMICLogo.h
  TARGET_LIBRARIES
    ModuleDescriptionParser ${ITK_LIBRARIES} MRMLCore ${VTK_LIBRARIES}
  INCLUDE_DIRECTORIES
    ${DCMTK_INCLUDE_DIRS}
    ${MRMLCore_INCLUDE_DIRS}
    ${vtkITK_INCLUDE_DIRS}
    ${SlicerBaseCLI_SOURCE_DIR} ${SlicerBaseCLI_BINARY_DIR}
  )

#-----------------------------------------------------------------------------
SEMMacroBuildCLI(
  NAME DICOMTract_to_VTK
  LOGO_HEADER ${Slicer_SOURCE_DIR}/Resources/NAMICLogo.h
  TARGET_LIBRARIES
    ModuleDescriptionParser ${ITK_LIBRARIES} MRMLCore ${VTK_LIBRARIES}
  INCLUDE_DIRECTORIES
    ${DCMTK_INCLUDE_DIRS}
    ${MRMLCore_INCLUDE_DIRS}
    ${vtkITK_INCLUDE_DIRS}
    ${SlicerBaseCLI_SOURCE_DIR} ${SlicerBaseCLI_BINARY_DIR}
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
    # TODO  add_subdirectory(Testing)
endif()
