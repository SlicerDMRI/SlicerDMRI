project(vtkIntxSeedingLogic)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_LOGIC_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  ${vtkDMRI_INCLUDE_DIRS}
  )

set(${KIT}_SRCS
  vtkSlicer${MODULE_NAME}Logic.h
  vtkSlicer${MODULE_NAME}Logic.cxx
  vtkMRML${MODULE_NAME}Node.h
  vtkMRML${MODULE_NAME}Node.cxx
  )

set(${KIT}_TARGET_LIBRARIES
  vtkDMRI
  ${ITK_LIBRARIES}
  vtkSlicerMarkupsModuleMRML
  vtkSlicerAnnotationsModuleMRML
  vtkSlicerTractographyDisplayModuleMRML
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleLogic(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )
