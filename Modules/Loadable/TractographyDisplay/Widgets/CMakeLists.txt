project(qSlicer${MODULE_NAME}ModuleWidgets)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "Q_SLICER_MODULE_${MODULE_NAME_UPPER}_WIDGETS_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  ${CMAKE_BUILD_DIR}
  ${vtkSlicerTractographyDisplayModuleMRML_SOURCE_DIR}
  ${vtkSlicerTractographyDisplayModuleMRML_BINARY_DIR}
  ${qSlicerColorsModuleWidgets_INCLUDE_DIRS}
  ${vtkSlicerColorsModuleMRML_INCLUDE_DIRS}
  ${vtkSlicerColorsModuleLogic_INCLUDE_DIRS}
  ${vtkSlicerTractographyDisplayModuleLogic_INCLUDE_DIRS}
  )

set(${KIT}_SRCS
  qMRMLTractographyDisplayTreeView.h
  qMRMLTractographyDisplayTreeView.cxx
  qMRMLSceneTractographyDisplayModel.h
  qMRMLSceneTractographyDisplayModel.cxx
  qSlicerTractographyDisplayModuleWidget.cxx
  qSlicerTractographyDisplayModuleWidget.h
  qSlicerTractographyDisplayBasicWidget.cxx
  qSlicerTractographyDisplayBasicWidget.h
  qSlicerTractographyEditorROIWidget.cxx
  qSlicerTractographyEditorROIWidget.h
  qSlicerTractographyDisplayGlyphWidget.cxx
  qSlicerTractographyDisplayGlyphWidget.h
  qSlicerTractographyDisplayWidget.cxx
  qSlicerTractographyDisplayWidget.h
  )

set(${KIT}_MOC_SRCS
  qSlicerTractographyDisplayModuleWidget.h
  qSlicerTractographyDisplayBasicWidget.h  
  qSlicerTractographyEditorROIWidget.h
  qSlicerTractographyDisplayGlyphWidget.h
  qSlicerTractographyDisplayWidget.h
  qMRMLTractographyDisplayTreeView.h
  qMRMLSceneTractographyDisplayModel.h
  )

set(${KIT}_UI_SRCS
  Resources/UI/qSlicerTractographyDisplayModuleWidget.ui
  Resources/UI/qSlicerTractographyDisplayBasicWidget.ui
  Resources/UI/qSlicerTractographyEditorROIWidget.ui
  Resources/UI/qSlicerTractographyDisplayGlyphWidget.ui
  Resources/UI/qSlicerTractographyDisplayWidget.ui
  )

set(${KIT}_RESOURCES
  )

set(${KIT}_TARGET_LIBRARIES
  vtkSlicerTractographyDisplayModuleLogic
  ${MRML_LIBRARIES}
  vtkSlicerMarkupsModuleMRML
  qSlicerColorsModuleWidgets
  vtkSlicerColorsModuleLogic
  vtkSlicerColorsModuleMRML
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleWidgets(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  MOC_SRCS ${${KIT}_MOC_SRCS}
  UI_SRCS ${${KIT}_UI_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  RESOURCES ${${KIT}_RESOURCES}
  WRAP_PYTHONQT
  )

# Plugin
#add_subdirectory(Plugins)
