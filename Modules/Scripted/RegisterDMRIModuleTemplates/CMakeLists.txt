#-----------------------------------------------------------------------------
set(MODULE_NAME RegisterDMRIModuleTemplates)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME    ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  )

#-----------------------------------------------------------------------------
# Include module templates in the distribution package
install(
  DIRECTORY "${SlicerDMRI_SOURCE_DIR}/DMRIModuleTemplates"
  DESTINATION ${Slicer_INSTALL_ROOT}${Slicer_BUNDLE_EXTENSIONS_LOCATION}
  COMPONENT RuntimeLibraries
  )
