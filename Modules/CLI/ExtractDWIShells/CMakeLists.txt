set(CLI_DEST "${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_BIN_DIR}")
set(CLI_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}")

add_custom_command(
  OUTPUT "${CLI_DEST}/ExtractDWIShells.py" "${CLI_DEST}/ExtractDWIShells.xml"
  COMMAND "${CMAKE_COMMAND}" -E copy "${CLI_SOURCE}/ExtractDWIShells.py" "${CLI_DEST}"
  COMMAND "${CMAKE_COMMAND}" -E copy "${CLI_SOURCE}/ExtractDWIShells.xml" "${CLI_DEST}"
  DEPENDS "${CLI_SOURCE}/ExtractDWIShells.xml" "${CLI_SOURCE}/ExtractDWIShells.py"
  COMMENT ""
)
add_custom_target(ExtractDWIShells ALL
  SOURCES "${CLI_SOURCE}/ExtractDWIShells.py" "${CLI_SOURCE}/ExtractDWIShells.py"
  DEPENDS "${CLI_DEST}/ExtractDWIShells.py" "${CLI_DEST}/ExtractDWIShells.py")

install(FILES ExtractDWIShells.py ExtractDWIShells.xml
  DESTINATION "${Slicer_INSTALL_CLIMODULES_BIN_DIR}")

set(TESTDATA "${SlicerDMRI_SOURCE_DIR}/Testdata/")
add_test(NAME ExtractDWIShells_Test
  COMMAND "${PYTHON_EXECUTABLE}" "${CLI_DEST}/ExtractDWIShells.py" --test "${TESTDATA}"
  )
