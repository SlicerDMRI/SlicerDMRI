include(SlicerMacroBuildScriptedModule)


# Test fiducials in the neurosurgical planning tutorial
slicerMacroBuildScriptedModule(
  NAME NsgPlanTracto.py
  SCRIPTS NsgPlanTracto.py
  RESOURCES ""
  )

slicer_add_python_unittest(SCRIPT NsgPlanTracto.py)
slicer_add_python_unittest(SCRIPT DTINotReproducibleIssue3977.py)
slicer_add_python_unittest(SCRIPT fiber_visibility_crash2438.py)
slicer_add_python_unittest(SCRIPT test_tractography_display.py)
slicer_add_python_unittest(SCRIPT SlicerMRBTest.py)
slicer_add_python_unittest(SCRIPT qSlicerTractographyDisplayWidgetTest.py)
