project(vtkSlicer${MODULE_NAME}ModuleMRML)

set(KIT ${PROJECT_NAME})

set(${KIT}_EXPORT_DIRECTIVE "VTK_SLICER_${MODULE_NAME_UPPER}_MODULE_MRML_EXPORT")

set(${KIT}_INCLUDE_DIRECTORIES
  )

list(APPEND ${KIT}_INCLUDE_DIRECTORIES ${vtkTeem_INCLUDE_DIRS} ${vtkDMRI_INCLUDE_DIRS})

set(${KIT}_SRCS
  vtkMRMLFiberBundleDisplayNode.cxx
  vtkMRMLFiberBundleDisplayNode.h
  vtkMRMLFiberBundleGlyphDisplayNode.cxx
  vtkMRMLFiberBundleGlyphDisplayNode.h
  vtkMRMLFiberBundleLineDisplayNode.cxx
  vtkMRMLFiberBundleLineDisplayNode.h
  vtkMRMLFiberBundleNode.cxx
  vtkMRMLFiberBundleNode.h
  vtkMRMLFiberBundleStorageNode.cxx
  vtkMRMLFiberBundleStorageNode.h
  vtkMRMLFiberBundleTubeDisplayNode.cxx
  vtkMRMLFiberBundleTubeDisplayNode.h
  )

set(${KIT}_TARGET_LIBRARIES
  vtkDMRI
  ${MRML_LIBRARIES}
  ${VTK_LIBRARIES}
  vtkSlicerMarkupsModuleMRML
  vtkTeem
  )

#-----------------------------------------------------------------------------
SlicerMacroBuildModuleMRML(
  NAME ${KIT}
  EXPORT_DIRECTIVE ${${KIT}_EXPORT_DIRECTIVE}
  INCLUDE_DIRECTORIES ${${KIT}_INCLUDE_DIRECTORIES}
  SRCS ${${KIT}_SRCS}
  TARGET_LIBRARIES ${${KIT}_TARGET_LIBRARIES}
  )
