
#-----------------------------------------------------------------------------
set(BASELINE ${CMAKE_CURRENT_SOURCE_DIR}/../Data/Baseline)
set(CLP ${MODULE_NAME})

#-----------------------------------------------------------------------------
add_executable(${CLP}Test ${CLP}Test.cxx)
add_dependencies(${CLP}Test ${CLP})
target_link_libraries(${CLP}Test
  ${${MODULE_NAME}_TARGET_LIBRARIES}
  ${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES}
  )
set_target_properties(${CLP}Test PROPERTIES LABELS ${CLP})
set_target_properties(${CLP}Test PROPERTIES FOLDER ${${CLP}_TARGETS_FOLDER})

set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})



set(name Trace)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name Determinant)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name RelativeAnisotropy)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name FractionalAnisotropy)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name Mode)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name LinearMeasure)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name PlanarMeasure)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name SphericalMeasure)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MinEigenvalue)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MidEigenvalue)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvalue)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvalueProjectionX)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvalueProjectionY)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvalueProjectionZ)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name RAIMaxEigenvecX)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name RAIMaxEigenvecY)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name RAIMaxEigenvecZ)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvecX)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvecY)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name MaxEigenvecZ)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name D11)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name D22)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name D33)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name ParallelDiffusivity)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

set(name PerpendicularDiffusivity)
set(testname ${CLP}Test${name})
add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
 --compare ${BASELINE}/helix-DTI-${name}.nhdr ${TEMP}/helix-DTI-${name}.nhdr
  ${CLP}Test
    --enumeration ${name}
    ${MRML_TEST_DATA}/helix-DTI.nhdr
    ${TEMP}/helix-DTI-${name}.nhdr
  )
set_property(TEST ${testname} PROPERTY LABELS ${CLP})

