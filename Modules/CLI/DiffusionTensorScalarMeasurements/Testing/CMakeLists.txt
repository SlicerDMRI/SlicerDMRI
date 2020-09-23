set(CLP ${MODULE_NAME})

add_executable(${CLP}Test ${CLP}Test.cxx)
add_dependencies(${CLP}Test ${CLP})
target_link_libraries(${CLP}Test
  ${CLP}Lib
  ${${MODULE_NAME}_TARGET_LIBRARIES}
  ${SlicerExecutionModel_EXTRA_EXECUTABLE_TARGET_LIBRARIES}
  )
set_target_properties(${CLP}Test PROPERTIES LABELS ${CLP})
set_target_properties(${CLP}Test PROPERTIES FOLDER ${${CLP}_TARGETS_FOLDER})

#-----------------------------------------------------------------------------
get_filename_component(BASELINE ${CMAKE_CURRENT_SOURCE_DIR}/../Data/Baseline ABSOLUTE)
get_filename_component(DATADIR ${CMAKE_CURRENT_SOURCE_DIR}/../../DWIToDTIEstimation/Data/Baseline ABSOLUTE)

#-----------------------------------------------------------------------------
# make sure the data directories exist
foreach(dir_check BASELINE MRML_TEST_DATA TEMP)
  if (NOT IS_DIRECTORY ${${dir_check}})
    message(FATAL_ERROR "${dir_check} data directory: '${${dir_check}}' does not exist!")
  endif()
endforeach()

#-----------------------------------------------------------------------------
set(MeasuresToTest
      Trace
      Determinant
      RelativeAnisotropy
      FractionalAnisotropy
      Mode
      LinearMeasure
      PlanarMeasure
      SphericalMeasure
      MinEigenvalue
      MidEigenvalue
      MaxEigenvalue
      ParallelDiffusivity
      PerpendicularDiffusivity
      MeanDiffusivity)

foreach(measure ${MeasuresToTest})
  set(testname ${CLP}Test${measure})
  add_test(NAME ${testname} COMMAND ${SEM_LAUNCH_COMMAND} $<TARGET_FILE:${CLP}Test>
           --compare "${BASELINE}/helix-DTI-${measure}.nhdr" "${TEMP}/helix-DTI-${measure}.nhdr"
           ${CLP}Test
           --enumeration "${measure}"
           "${DATADIR}/helix-DTI.nhdr"
           "${TEMP}/helix-DTI-${measure}.nhdr"
           )
  set_property(TEST ${testname} PROPERTY LABELS ${CLP})
endforeach()
