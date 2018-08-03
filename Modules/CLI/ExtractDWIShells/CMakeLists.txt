set(CLI_DEST "${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_BIN_DIR}")
set(CLI_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}")

add_custom_command(
  DEPENDS "${CLI_SOURCE}/ExtractDWIShells.xml" "${CLI_SOURCE}/ExtractDWIShells.py"
  OUTPUT "${CLI_DEST}/ExtractDWIShells.py" "${CLI_DEST}/ExtractDWIShells.xml"
  COMMAND cmake -E copy "${CLI_SOURCE}/ExtractDWIShells.py" "${CLI_DEST}"
  COMMAND cmake -E copy "${CLI_SOURCE}/ExtractDWIShells.xml" "${CLI_DEST}"
)
add_custom_target(ExtractDWIShells ALL
  DEPENDS ${CLI_DEST}/ExtractDWIShells.py ${CLI_DEST}/ExtractDWIShells.py)

install(FILES ExtractDWIShells.py ExtractDWIShells.xml
  DESTINATION "${Slicer_INSTALL_CLIMODULES_BIN_DIR}")

set(TESTDATA "${SlicerDMRI_SOURCE_DIR}/Testdata/")
add_test(NAME ExtractDWIShells_Test
  COMMAND "${PYTHON_EXECUTABLE}" "${CLI_DEST}/ExtractDWIShells.py" --test "${TESTDATA}"
  )
