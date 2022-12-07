#-----------------------------------------------------------------------------
set(MODULE_NAME DMRIPlugins)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  DICOMDiffusionVolumePlugin.py
  RegisterDMRIModuleTemplates.py
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  )
