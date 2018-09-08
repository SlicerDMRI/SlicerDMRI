import os
import vtk, qt, ctk, slicer

from slicer.ScriptedLoadableModule import *

class RegisterDMRIModuleTemplates:
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
                import warnings, textwrap
                warnings.warn(textwrap.dedent(
                    """SlicerDMRI template module path '{}' is missing.
                       Templates will not be auto-registered""").format(dmri_template_path))
                return

        import ExtensionWizardLib
        # add the *installed* template path to the wizard lookup paths.
        # TODO handle case of local build tree
        settings = qt.QSettings()
        
        userkey = ExtensionWizardLib.TemplatePathUtilities.userTemplatePathKey()
        modules_key = userkey + "/modules"
        updated_value = settings.value(modules_key) + (dmri_template_path,)
        settings.setValue(modules_key, updated_value)