set(TEMP "${CMAKE_BINARY_DIR}/Testing/Temporary")

#-----------------------------------------------------------------------------
set(BASELINE ${CMAKE_CURRENT_SOURCE_DIR}/../Data/Baseline)
set(TEST_DATA ${CMAKE_CURRENT_SOURCE_DIR}/../Data/Input)

set(CLP ${MODULE_NAME})

add_executable(${CLP}Test ${CLP}Test.cxx)
add_dependencies(${CLP}Test ${CLP})
target_link_libraries(${CLP}Test ${CLP}Lib ${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES})
set_target_properties(${CLP}Test PROPERTIES LABELS ${CLP})
set_target_properties(${CLP}Test PROPERTIES FOLDER ${${CLP}_TARGETS_FOLDER})

#-----------------------------------------------------------------------------
set(testname ${CLP}TestFolder)
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
  ${CLP}Test
    --inputtype Fibers_File_Folder
    --inputdirectory ${TEST_DATA}
    --outputfile ${TEMP}/fibermeasurementstestingoutputfolder.txt
    --format Column_Hierarchy
    --separator Tab
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(testname ${CLP}TestHierarchy)
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
  ${CLP}Test
    --inputtype Fibers_Hierarchy
    --fiberHierarchy ${TEST_DATA}/fibers_hierarchy.mrml\#vtkMRMLModelHierarchyNode1
    --outputfile ${TEMP}/fibermeasurementstestingoutputhierarchy.txt
    --format Column_Hierarchy
    --separator Tab
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

#-----------------------------------------------------------------------------
add_executable(CompareTxtsMeasures CompareTxts.cxx)
target_link_libraries(CompareTxtsMeasures ${CLP}Lib ${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES})
set_target_properties(CompareTxtsMeasures PROPERTIES LABELS ${CLP})
set_target_properties(CompareTxtsMeasures PROPERTIES FOLDER ${${CLP}_TARGETS_FOLDER})

set(testname ${CLP}CompareTxtsFolder)
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:CompareTxtsMeasures>
  ${TEMP}/fibermeasurementstestingoutputfolder.txt
  ${BASELINE}/baseline_measurements_folder.txt
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})
set_property(TEST ${testname} PROPERTY DEPENDS ${CLP}TestFolder)

set(testname ${CLP}CompareTxtsHierarchy)
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:CompareTxtsMeasures>
  ${TEMP}/fibermeasurementstestingoutputhierarchy.txt
  ${BASELINE}/baseline_measurements_hierarchy.txt
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})
set_property(TEST ${testname} PROPERTY DEPENDS ${CLP}TestHierarchy)
