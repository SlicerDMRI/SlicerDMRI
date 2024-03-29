// Tractography Logic includes
#include "vtkSlicerTractographyInteractiveSeedingLogic.h"

// Tractography QTModule includes
#include "qSlicerTractographyInteractiveSeedingModule.h"
#include "qSlicerTractographyInteractiveSeedingModuleWidget.h"

//-----------------------------------------------------------------------------
qSlicerTractographyInteractiveSeedingModule::
qSlicerTractographyInteractiveSeedingModule(QObject* _parent):Superclass(_parent)
{
}

//-----------------------------------------------------------------------------
qSlicerAbstractModuleRepresentation* qSlicerTractographyInteractiveSeedingModule::createWidgetRepresentation()
{
  return new qSlicerTractographyInteractiveSeedingModuleWidget;
}
//-----------------------------------------------------------------------------
//
vtkMRMLAbstractLogic* qSlicerTractographyInteractiveSeedingModule::createLogic()
{
  return vtkSlicerTractographyInteractiveSeedingLogic::New();
}

//-----------------------------------------------------------------------------
QStringList qSlicerTractographyInteractiveSeedingModule::categories()const
{
  return QStringList() << "Diffusion.Tractography";
}

//-----------------------------------------------------------------------------
QString qSlicerTractographyInteractiveSeedingModule::helpText()const
{
  QString help =
    "The Tractography Interactive Seeding Module creates fiber tracts at specified seeding location. \n"
    "<a href=http://dmri.slicer.org/docs</a>";
  return help;
}

//-----------------------------------------------------------------------------
QString qSlicerTractographyInteractiveSeedingModule::acknowledgementText()const
{
  QString acknowledgement =
    "This work was supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer Community. "
    "See <a href=\"http://www.slicer.org\">http://www.slicer.org</a> for details.\n"
    "The InteractiveSeeding module was contributed by Alex Yarmarkovich, Isomics Inc. with "
    "help from others at SPL, BWH (Ron Kikinis)";
  return acknowledgement;
}

//-----------------------------------------------------------------------------
QStringList qSlicerTractographyInteractiveSeedingModule::contributors()const
{
  QStringList moduleContributors;
  moduleContributors << QString("Alex Yarmakovich (Isomics)");
  return moduleContributors;
}
