import os
import vtk, qt, ctk, slicer
import warnings
from slicer.ScriptedLoadableModule import *

class RegisterDMRIModuleTemplates(object):
    def __init__(self, parent):
        parent.title = "DMRI Template auto-Registration Plugin"
        parent.categories = [""]
        parent.contributors = ["Isaiah Norton (Brigham & Women's Hospital)"]
        parent.helpText = ""
        parent.hidden = True

        dmri_template_path = os.path.join(slicer.app.extensionsInstallPath,
                                          "SlicerDMRI", "DMRIModuleTemplates")

        if not os.path.isdir(dmri_template_path):
            # TODO fix capability to use build directory
            build_template_path = os.path.join(os.path.dirname(__file__), "../../../DMRIModuleTemplates")

            if os.path.isdir(build_template_path):
                dmri_template_path = build_template_path

            else:
                import textwrap
                warnings.warn(textwrap.dedent(
                    """SlicerDMRI template module path '{}' is missing.
                       Templates will not be auto-registered""").format(dmri_template_path))
                return

        # wrap in a try block to reduce risk of messing up startup
        try:
            import ExtensionWizardLib
            # add the *installed* template path to the wizard lookup paths
            # TODO handle case of local build tree
            settings = qt.QSettings()

            userkey = ExtensionWizardLib.TemplatePathUtilities.userTemplatePathKey()
            modules_key = userkey + "/modules"
            existing_value = settings.value(modules_key)
            if existing_value:
              updated_value = existing_value + (dmri_template_path,)
            else:
              updated_value = (dmri_template_path,)
            settings.setValue(modules_key, updated_value)
        except Exception as exc:
            warnings.warn("Exception during attempt to register DMRI module templates: " + str(exc))
