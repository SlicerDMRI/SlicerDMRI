include(SlicerMacroBuildScriptedModule)
set(MARKUPS_PYTHON_RESOURCES
   )

# Test fiducials in the neurosurgical planning tutorial
slicerMacroBuildScriptedModule(
  NAME NeurosurgicalPlanningTutorialMarkupsSelfTest
  SCRIPTS NeurosurgicalPlanningTutorialMarkupsSelfTest.py
  RESOURCES ${MARKUPS_PYTHON_RESOURCES}
  )
slicer_add_python_unittest(SCRIPT NeurosurgicalPlanningTutorialMarkupsSelfTest.py)

slicer_add_python_unittest(SCRIPT DTINotReproducibleIssue3977.py)
slicer_add_python_unittest(SCRIPT fiber_visibility_crash2438.py)
slicer_add_python_unittest(SCRIPT test_tractography_display.py)
slicer_add_python_unittest(SCRIPT SlicerMRBTest.py)
