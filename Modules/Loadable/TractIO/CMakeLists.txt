
#-----------------------------------------------------------------------------
set(MODULE_NAME TractIO)
set(MODULE_TITLE "Tractography Input and Output")

string(TOUPPER ${MODULE_NAME} MODULE_NAME_UPPER)


#-----------------------------------------------------------------------------
# DICOM Browser Tractography Plugin
if(false)
    set(MODULE_PYTHON_SCRIPTS
      DICOMTractographyPlugin.py
    )


    slicerMacroBuildScriptedModule(
      NAME ${MODULE_NAME}
      SCRIPTS ${MODULE_PYTHON_SCRIPTS}
      RESOURCES ${MODULE_PYTHON_RESOURCES}
    )
endif()

#-----------------------------------------------------------------------------
if(Slicer_BUILD_CLI_SUPPORT AND Slicer_BUILD_CLI)
  add_subdirectory(TractIOCLI)
endif()

