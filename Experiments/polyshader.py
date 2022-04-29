
rw = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()

actors = rw.GetRenderers().GetItemAsObject(0).GetActors()

for actorIndex in range(actors.GetNumberOfItems()):
    a = actors.GetItemAsObject(actorIndex)
    a.GetShaderProperty().ClearAllShaderReplacements()
    alpha = 0.1 if actorIndex == 10 else .9
    a.GetShaderProperty().AddFragmentShaderReplacement(
          "//VTK::Light::Impl",  # replace the normal block
          True,                  # before the standard replacements
          f"""
            //VTK::Light::Impl 
            // actor {actorIndex}
            fragOutput0.a = {alpha};\n
          """,
          False) # only do it once

