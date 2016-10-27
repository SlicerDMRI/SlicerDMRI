include(SlicerMacroBuildScriptedModule)


# Test fiducials in the neurosurgical planning tutorial
slicerMacroBuildScriptedModule(
  NAME NsgPlanTracto.py
  SCRIPTS NsgPlanTracto.py
  RESOURCES ""
  )

# temp: unncessary after https://github.com/Slicer/Slicer/pull/610
set(UNITTEST_LIB_PATHS "--additional-module-paths;${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR};${CMAKE_BINARY_DIR}/${Slicer_CLIMODULES_LIB_DIR};${CMAKE_BINARY_DIR}/${Slicer_QTLOADBLEMODULES_LIB_DIR}")

slicer_add_python_unittest(SCRIPT NsgPlanTracto.py
                           SLICER_ARGS ${UNITTEST_LIB_PATHS})

slicer_add_python_unittest(SCRIPT DTINotReproducibleIssue3977.py)
slicer_add_python_unittest(SCRIPT fiber_visibility_crash2438.py)
slicer_add_python_unittest(SCRIPT test_tractography_display.py)
slicer_add_python_unittest(SCRIPT SlicerMRBTest.py)
