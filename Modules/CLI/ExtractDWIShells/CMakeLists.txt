set(CLI_DEST "${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_LIB_DIR}")

ctkMacroCompilePythonScript(
  TARGET_NAME ExtractDWIShells 
  SCRIPTS ExtractDWIShells.py
  RESOURCES ExtractDWIShells.xml
  DESTINATION_DIR ${CLI_DEST}
  INSTALL_DIR ${Slicer_INSTALL_CLIMODULES_BIN_DIR}
  )

set(TESTDATA "${SlicerDMRI_SOURCE_DIR}/Testdata/")
add_test(NAME ExtractDWIShells_Test
         COMMAND "${PYTHON_EXECUTABLE}" "${CLI_DEST}/ExtractDWIShells.py" --test "${TESTDATA}"
        )
