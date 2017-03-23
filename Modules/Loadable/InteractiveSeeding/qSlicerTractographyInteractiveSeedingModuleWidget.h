#ifndef __qSlicerTractographyInteractiveSeedingModuleWidget_h
#define __qSlicerTractographyInteractiveSeedingModuleWidget_h

// CTK includes
#include <ctkPimpl.h>

// SlicerQt includes
#include "qSlicerAbstractModuleWidget.h"

#include "qSlicerTractographyInteractiveSeedingModuleExport.h"

class qSlicerTractographyInteractiveSeedingModuleWidgetPrivate;
class vtkMRMLNode;
class vtkMRMLFiberBundleNode;
class vtkMRMLDiffusionTensorVolumeNode;
class vtkMRMLTractographyInteractiveSeedingNode;
class vtkIntArray;

/// \ingroup Slicer_QtModules_TractographyInteractiveSeeding
class Q_SLICER_QTMODULES_TRACTOGRAPHYINTERACTIVESEEDING_EXPORT qSlicerTractographyInteractiveSeedingModuleWidget :  public qSlicerAbstractModuleWidget
{
  Q_OBJECT
  QVTK_OBJECT

public:
  typedef qSlicerAbstractModuleWidget Superclass;
  qSlicerTractographyInteractiveSeedingModuleWidget(QWidget *_parent=0);
  virtual ~qSlicerTractographyInteractiveSeedingModuleWidget();

  /// Get current parameter node
  vtkMRMLTractographyInteractiveSeedingNode* tractographyInteractiveSeedingNode() {
    return this->TractographyInteractiveSeedingNode;
  };

  /// Get current seeding node
  vtkMRMLNode* seedingNode();

  /// Get current DTI volume node
  vtkMRMLDiffusionTensorVolumeNode* diffusionTensorVolumeNode();

  /// Get current fiber bundle node
  vtkMRMLFiberBundleNode* fiberBundleNode();

  /// Support of node editing. Select node in GUI that the user wants to edit.
  /// No need for roles, as node type unambiguously determines role in this module
  virtual bool setEditedNode(
    vtkMRMLNode* node, QString role=QString(), QString context=QString() );
  /// Return confidence value for nodes based on how suitable they are to edit
  virtual double nodeEditable(vtkMRMLNode* node);

  virtual void enter();

public slots:

  /// Set the current MRML scene to the widget
  virtual void setMRMLScene(vtkMRMLScene*);

  /// Process loaded scene
  void onSceneImportedEvent();
  /// Process restored scene
  void onSceneRestoredEvent();

  /// Set parameter node to one of resets:
  /// 0 - Slicer4
  /// 1 - Slicer3 FiducialSeeding module
  /// 2 - Slicer3 LabelMap Seeding module
  void setParametersPreset(int index);

  /// Set current parameter node
  void setTractographyInteractiveSeedingNode(vtkMRMLNode *node);

  /// Set current seeding node
  void setSeedingNode(vtkMRMLNode *node);

  /// Set current DTI volume node
  void setDiffusionTensorVolumeNode(vtkMRMLNode *node);

  /// Set current fiber bundlde node
  void setFiberBundleNode(vtkMRMLNode *node);

  /// Set stopping criteria 0-Linear Measure, 1 - FA
  void setStoppingCriteria(int value);

  /// Set display mode 0-line 1-tube
  void setTrackDisplayMode(int value);

  /// Set stopping curvature
  void setStoppingCurvature(double value);

  /// Set stopping curvature
  void setStoppingValue(double value);

  /// Set integration step length, mm
  void setIntegrationStep(double value);

  /// Set minimum path length, mm
  void setMinimumPath(double value);

  /// Set maximum path length, mm
  void setMaximumPath(double value);

  /// Set the size of fiducial region, mm
  void setFiducialRegion(double value);

  /// Set the step of fiducial region, mm
  void setFiducialRegionStep(double value);

  /// Set seed only selected fiducails
  void setSeedSelectedFiducials(int value);

  /// Set enable/disable seeding
  void setEnableSeeding(int value);

  /// Set max number of seeds
  void setMaxNumberSeeds(int value);

  /// Set [ThresholdMode] start threshold
  void setStartThreshold(double value);

  /// Set RPO label from Qt widget
  void setROILabels();

  /// Set RPO label from string
  void setROILabels(const QString &labels);

  /// Set random grid
  void setRandomGrid(int value);

  /// Set seed spacing
  void setSeedSpacing(double value);

  /// Set use index space
  void setUseIndexSpace(int value);

  /// Update widget GUI from parameter node
  void updateWidgetFromMRML();

  /// Apply one-shot update
  void updateOnce();

  /// Click interactive checkbox button
  void clickEnableInteractiveSeeding();

  /// Set interactive enable checkbox
  void toggleEnableInteractiveSeeding(Qt::CheckState);

protected:

  virtual void setup();
  void onEnter();

  vtkMRMLTractographyInteractiveSeedingNode* TractographyInteractiveSeedingNode;

  bool settingFiberBundleNode;

  bool settingMRMLScene;

protected:
  QScopedPointer<qSlicerTractographyInteractiveSeedingModuleWidgetPrivate> d_ptr;

private:
  Q_DECLARE_PRIVATE(qSlicerTractographyInteractiveSeedingModuleWidget);
  Q_DISABLE_COPY(qSlicerTractographyInteractiveSeedingModuleWidget);
};

#endif
