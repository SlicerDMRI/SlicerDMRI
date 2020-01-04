#ifndef __qSlicerTractographyInteractiveSeedingModule_h
#define __qSlicerTractographyInteractiveSeedingModule_h

/// SlicerQT includes
#include "qSlicerLoadableModule.h"

#include "qSlicerTractographyInteractiveSeedingModuleExport.h"

class qSlicerTractographyInteractiveSeedingModulePrivate;
class qSlicerTractographyInteractiveSeedingModuleWidget;

/// \ingroup Slicer_QtModules_TractographyInteractiveSeeding
class Q_SLICER_QTMODULES_TRACTOGRAPHYINTERACTIVESEEDING_EXPORT qSlicerTractographyInteractiveSeedingModule : public qSlicerLoadableModule
{
  Q_OBJECT
#ifdef Slicer_HAVE_QT5
  Q_PLUGIN_METADATA(IID "org.slicer.modules.loadable.qSlicerLoadableModule/1.0");
#endif
  Q_INTERFACES(qSlicerLoadableModule);
public:
  typedef qSlicerLoadableModule Superclass;

  qSlicerTractographyInteractiveSeedingModule(QObject *_parent = 0);

  /// Category of the module
  virtual QStringList categories() const override;

  qSlicerGetTitleMacro(QTMODULE_TITLE);

  virtual QString helpText() const override;
  virtual QString acknowledgementText() const override;
  virtual QStringList contributors() const override;

protected:
  /// Create and return a widget representation of the object
  virtual qSlicerAbstractModuleRepresentation* createWidgetRepresentation() override;
  virtual vtkMRMLAbstractLogic* createLogic() override;

private:
  //  Q_DECLARE_PRIVATE(qSlicerTractographyInteractiveSeedingModule);
  Q_DISABLE_COPY(qSlicerTractographyInteractiveSeedingModule);

};
#endif

