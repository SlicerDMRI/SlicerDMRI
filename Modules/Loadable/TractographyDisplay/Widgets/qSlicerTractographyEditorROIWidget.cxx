// QT includes
#include <QDebug>
#include <QColor>
#include <QMessageBox>

// qMRML includes
#include "qSlicerTractographyEditorROIWidget.h"
#include "ui_qSlicerTractographyEditorROIWidget.h"

// MRML includes
#include "vtkMRMLMarkupsNode.h"
#include "vtkMRMLMarkupsROINode.h"
#include <vtkMRMLLabelMapVolumeDisplayNode.h>
#include <vtkMRMLScalarVolumeDisplayNode.h>
#include <vtkMRMLStorageNode.h>
#include <vtkMRMLFiberBundleNode.h>
#include <vtkMRMLFiberBundleDisplayNode.h>
#include <vtkMRMLInteractionNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include "vtkPolyData.h"
#include <vtkMatrix4x4.h>
#include <vtkSmartPointer.h>

//------------------------------------------------------------------------------
class qSlicerTractographyEditorROIWidgetPrivate:
  public Ui_qSlicerTractographyEditorROIWidget
{
  Q_DECLARE_PUBLIC(qSlicerTractographyEditorROIWidget);

protected:
  qSlicerTractographyEditorROIWidget* const q_ptr;

public:
  qSlicerTractographyEditorROIWidgetPrivate(qSlicerTractographyEditorROIWidget& object);
  void init();

  vtkMRMLFiberBundleNode* FiberBundleNode;
  vtkMRMLMarkupsNode* MarkupsMRMLNodeForFiberSelection;
};

//------------------------------------------------------------------------------
qSlicerTractographyEditorROIWidgetPrivate::qSlicerTractographyEditorROIWidgetPrivate
                                      (qSlicerTractographyEditorROIWidget& object)
  : q_ptr(&object)
{
  this->FiberBundleNode = 0;
  this->MarkupsMRMLNodeForFiberSelection = NULL;
}

//------------------------------------------------------------------------------
void qSlicerTractographyEditorROIWidgetPrivate::init()
{
  Q_Q(qSlicerTractographyEditorROIWidget);
  this->setupUi(q);

  this->ROIForFiberSelectionMRMLNodeSelector->setBaseName(QString::fromUtf8("ROI Node"));

  this->EnableFiberEdit->setToolTip(QString("Click in 3D view to focus\n s: toggle select/unselect individual fibers\n x: unselect all selected fibers\n d: delete selected fibers or an individual fiber, if none is selected"));

#ifndef ENABLE_FIBER_EDIT
  // This feature stopped working sometime during the evolution of Slicer 4/5.
  // Rather than remove all the code, we hide it away with the idea that it
  // can be re-enabled and debugged in the future if needed.
  this->EnableFiberEdit->hide();
#endif

  QObject::connect(this->ROIForFiberSelectionMRMLNodeSelector, SIGNAL(currentNodeChanged(vtkMRMLNode*)),
                   q, SLOT(setMarkupsMRMLNodeForFiberSelection(vtkMRMLNode*)));
  QObject::connect(this->ROIForFiberSelectionMRMLNodeSelector, SIGNAL(nodeAddedByUser(vtkMRMLNode*)),
                   q, SLOT(setMarkupsROIMRMLNodeToFiberBundleEnvelope(vtkMRMLNode*)));
  QObject::connect(this->CreateNewFiberBundle, SIGNAL(clicked()),
                   q, SLOT(createNewBundleFromSelection()));
  QObject::connect(this->UpdateBundleFromSelection, SIGNAL(clicked()),
                   q, SLOT(updateBundleFromSelection()));
  QObject::connect(this->DisableROI, SIGNAL(toggled(bool)),
                   q, SLOT(disableROISelection(bool)));
  QObject::connect(this->PositiveROI, SIGNAL(toggled(bool)),
                   q, SLOT(positiveROISelection(bool)));
  QObject::connect(this->NegativeROI, SIGNAL(toggled(bool)),
                   q, SLOT(negativeROISelection(bool)));
  QObject::connect(this->ROIVisibility, SIGNAL(clicked(bool)),
                   q, SLOT(setROIVisibility(bool)));
  QObject::connect(this->EnableFiberEdit, SIGNAL(clicked(bool)),
                   q, SLOT(setInteractiveFiberEdit(bool)));

}


//------------------------------------------------------------------------------
qSlicerTractographyEditorROIWidget::qSlicerTractographyEditorROIWidget(QWidget *_parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerTractographyEditorROIWidgetPrivate(*this))
{
  Q_D(qSlicerTractographyEditorROIWidget);
  d->init();
}

//------------------------------------------------------------------------------
qSlicerTractographyEditorROIWidget::~qSlicerTractographyEditorROIWidget()
{
}

//------------------------------------------------------------------------------
vtkMRMLFiberBundleNode* qSlicerTractographyEditorROIWidget::fiberBundleNode()const
{
  Q_D(const qSlicerTractographyEditorROIWidget);
  return d->FiberBundleNode;
}

//------------------------------------------------------------------------------
void qSlicerTractographyEditorROIWidget::setFiberBundleNode(vtkMRMLNode* node)
{
  this->setFiberBundleNode(vtkMRMLFiberBundleNode::SafeDownCast(node));
}

//------------------------------------------------------------------------------
void qSlicerTractographyEditorROIWidget::
  setFiberBundleNode
  (vtkMRMLFiberBundleNode* fiberBundleNode)
{
  Q_D(qSlicerTractographyEditorROIWidget);

  if (d->FiberBundleNode == fiberBundleNode)
    return;

  d->FiberBundleNode = fiberBundleNode;

  if (fiberBundleNode && fiberBundleNode->GetNumberOfDisplayNodes() > 0)
  {
    d->MarkupsMRMLNodeForFiberSelection = fiberBundleNode->GetMarkupsNode();
    d->ROIForFiberSelectionMRMLNodeSelector->setCurrentNode(d->MarkupsMRMLNodeForFiberSelection);
  }

  this->updateWidgetFromMRML();
}

//------------------------------------------------------------------------------
void qSlicerTractographyEditorROIWidget::
  updateWidgetFromMRML()
{
  Q_D(qSlicerTractographyEditorROIWidget);

  // make edit widgets active/inactive based on node selection
  if ( !d->FiberBundleNode || !d->MarkupsMRMLNodeForFiberSelection)
  {
    d->ConfirmFiberBundleUpdate->setEnabled(false);
    d->CreateNewFiberBundle->setEnabled(false);
    d->DisableROI->setEnabled(false);
    d->FiberBundleFromSelection->setEnabled(false);
    d->NegativeROI->setEnabled(false);
    d->PositiveROI->setEnabled(false);
    d->ROIVisibility->setEnabled(false);
    d->UpdateBundleFromSelection->setEnabled(false);
  }
  else
  {
    d->ConfirmFiberBundleUpdate->setEnabled(true);
    d->CreateNewFiberBundle->setEnabled(true);
    d->DisableROI->setEnabled(true);
    d->FiberBundleFromSelection->setEnabled(true);
    d->NegativeROI->setEnabled(true);
    d->PositiveROI->setEnabled(true);
    d->ROIVisibility->setEnabled(true);
    d->UpdateBundleFromSelection->setEnabled(true);
  }

  if (!d->FiberBundleNode)
    {
    // turn off editing if there is no selection
    this->setInteractiveFiberEdit(false);
    d->EnableFiberEdit->setEnabled(false);

    return;
    }
  else
    {
    d->EnableFiberEdit->setEnabled(true);
    }

  if (d->FiberBundleNode->GetNumberOfDisplayNodes() > 0)
  {
    if (d->MarkupsMRMLNodeForFiberSelection != d->FiberBundleNode->GetMarkupsNode())
    {
      d->MarkupsMRMLNodeForFiberSelection = d->FiberBundleNode->GetMarkupsNode();
      d->ROIForFiberSelectionMRMLNodeSelector->setCurrentNode(d->MarkupsMRMLNodeForFiberSelection);
    }
    if (!d->FiberBundleNode->GetSelectWithMarkups())
    {
      d->DisableROI->setChecked(true);
    }
    else if (d->FiberBundleNode->GetMarkupsSelectionMode() == vtkMRMLFiberBundleNode::PositiveSelection)
    {
      d->PositiveROI->setChecked(true);
    }
    else if (d->FiberBundleNode->GetMarkupsSelectionMode() == vtkMRMLFiberBundleNode::NegativeSelection)
    {
      d->NegativeROI->setChecked(true);
    }

    std::string fiberName = std::string("Update ") + std::string(d->FiberBundleNode->GetName()) +
                            std::string(" From ROI");

    d->UpdateBundleFromSelection->setText(QApplication::translate("qSlicerTractographyEditorROIWidget",
                            fiberName.c_str(), 0));
  }

  if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
  {
    d->ROIVisibility->setChecked((bool)d->MarkupsMRMLNodeForFiberSelection->GetDisplayVisibility());
  }

}

void qSlicerTractographyEditorROIWidget::setMarkupsMRMLNodeForFiberSelection(vtkMRMLNode* MarkupsMRMLNodeForFiberSelection)
{
  Q_D(qSlicerTractographyEditorROIWidget);
  if (d->FiberBundleNode)
  {
    vtkMRMLMarkupsNode* MarkupsNode = vtkMRMLMarkupsNode::SafeDownCast(MarkupsMRMLNodeForFiberSelection);
    if (MarkupsNode)
      {
      d->MarkupsMRMLNodeForFiberSelection = MarkupsNode;
      d->FiberBundleNode->SetAndObserveMarkupsNodeID(d->MarkupsMRMLNodeForFiberSelection->GetID());
      }
    else
      {
      d->FiberBundleNode->SetAndObserveMarkupsNodeID(NULL); // TODO nullptr
      }
    this->updateWidgetFromMRML();
  }
}

void qSlicerTractographyEditorROIWidget::setMarkupsROIMRMLNodeToFiberBundleEnvelope(vtkMRMLNode* MarkupsMRMLNodeForFiberSelection)
{
  Q_D(qSlicerTractographyEditorROIWidget);
  if (d->FiberBundleNode)
  {
    vtkMRMLMarkupsROINode* MarkupsNode = vtkMRMLMarkupsROINode::SafeDownCast(MarkupsMRMLNodeForFiberSelection);
    if (MarkupsNode)
      {
      double xyz[3];
      double bounds[6];
      double radius[3];
      vtkPolyData *PolyData = d->FiberBundleNode->GetPolyData();

      PolyData->ComputeBounds();
      PolyData->GetCenter(xyz);
      PolyData->GetBounds(bounds);

      radius[0] = (bounds[1] - bounds[0]) / 2.;
      radius[1] = (bounds[3] - bounds[2]) / 2.;
      radius[2] = (bounds[5] - bounds[4]) / 2.;

      MarkupsNode->SetXYZ(xyz);
      MarkupsNode->SetRadiusXYZ(radius);
      MarkupsNode->UpdateReferences();

      d->ROIForFiberSelectionMRMLNodeSelector->setCurrentNode(MarkupsNode);

      d->PositiveROI->setChecked(true);
      }
    this->updateWidgetFromMRML();
  }
}



void qSlicerTractographyEditorROIWidget::setInteractiveROI(bool arg)
{
  Q_D(qSlicerTractographyEditorROIWidget);
  if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
  {
    if (arg && d->FiberBundleFromSelection->currentNode())
    {
      vtkMRMLFiberBundleNode* fbn =
        vtkMRMLFiberBundleNode::SafeDownCast(d->FiberBundleFromSelection->currentNode());
      fbn->SetMeshConnection(d->FiberBundleNode->GetMeshConnection());
    }
  }
}

void qSlicerTractographyEditorROIWidget::setInteractiveFiberEdit(bool arg)
{
  Q_D(qSlicerTractographyEditorROIWidget);
  if (d->FiberBundleNode)
  {
    vtkMRMLInteractionNode *interactionNode =
      vtkMRMLInteractionNode::SafeDownCast(
          this->mrmlScene()->GetSingletonNode("Singleton", "vtkMRMLInteractionNode"));
    if (interactionNode)
    {
      interactionNode->SetEnableFiberEdit((int)arg);
    }
  }
}
void qSlicerTractographyEditorROIWidget::setROIVisibility(bool arg)
{
  Q_D(qSlicerTractographyEditorROIWidget);
  if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
  {
    d->MarkupsMRMLNodeForFiberSelection->SetDisplayVisibility((int)arg);
  }
}

void qSlicerTractographyEditorROIWidget::disableROISelection(bool arg)
{
  if (arg)
  {
    Q_D(qSlicerTractographyEditorROIWidget);
    if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
    {
      d->FiberBundleNode->SetSelectWithMarkups(false);
    }
  }
}

void qSlicerTractographyEditorROIWidget::positiveROISelection(bool arg)
{
  if (arg)
  {
    Q_D(qSlicerTractographyEditorROIWidget);
    if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
    {
      d->FiberBundleNode->SetSelectWithMarkups(true);
      d->FiberBundleNode->SetMarkupsSelectionMode(vtkMRMLFiberBundleNode::PositiveSelection);
    }
  }
}

void qSlicerTractographyEditorROIWidget::negativeROISelection(bool arg)
{
  if (arg)
  {
    Q_D(qSlicerTractographyEditorROIWidget);
    if (d->FiberBundleNode && d->MarkupsMRMLNodeForFiberSelection)
    {
      d->FiberBundleNode->SetSelectWithMarkups(true);
      d->FiberBundleNode->SetMarkupsSelectionMode(vtkMRMLFiberBundleNode::NegativeSelection);
    }
  }
}


void qSlicerTractographyEditorROIWidget::createNewBundleFromSelection()
{
  Q_D(qSlicerTractographyEditorROIWidget);

  vtkMRMLFiberBundleNode *fiberBundleFromSelection = vtkMRMLFiberBundleNode::SafeDownCast(d->FiberBundleFromSelection->currentNode());
  if (d->FiberBundleNode && fiberBundleFromSelection && (d->FiberBundleNode != fiberBundleFromSelection))
  {
    // Detach polydata from pipeline
    vtkPolyData *filteredPolyData = vtkPolyData::New();
    filteredPolyData->DeepCopy(d->FiberBundleNode->GetFilteredPolyData());
    fiberBundleFromSelection->SetAndObservePolyData(filteredPolyData);
    filteredPolyData->Delete();

    if (!fiberBundleFromSelection->GetDisplayNode())
    {
      fiberBundleFromSelection->CreateDefaultDisplayNodes();

      if (fiberBundleFromSelection->GetStorageNode() == NULL)
        {
          fiberBundleFromSelection->CreateDefaultStorageNode();
        }

      fiberBundleFromSelection->SetAndObserveTransformNodeID(d->FiberBundleNode->GetTransformNodeID());
      fiberBundleFromSelection->InvokeEvent(vtkMRMLFiberBundleNode::PolyDataModifiedEvent, NULL);
    }

    fiberBundleFromSelection->GetLineDisplayNode()->SetOpacity(0.7);

  } else {
     QMessageBox::warning(this, tr("Create Bundle From ROI"),
                                  tr("You can not use the source Fiber Bundle\n"
                                     "as destination fiber bundle.\n"
                                     "Use Update Bundle From ROI for this."
                                     ),
                                  QMessageBox::Ok);

  }
}

void qSlicerTractographyEditorROIWidget::updateBundleFromSelection()
{
  Q_D(qSlicerTractographyEditorROIWidget);
  int proceedWithUpdate = 0;

  if (d->FiberBundleNode)
  {
    if (d->ConfirmFiberBundleUpdate->checkState() == Qt::Checked)
    {
     int ret = QMessageBox::warning(this, tr("Update Bundle From ROI"),
                                    tr("This will replace the actual fiber bundle\n"
                                       "with the results of the selection.\n"
                                       "Are you sure this is what you want?"
                                       ),
                                    QMessageBox::Ok | QMessageBox::Cancel);
     if (ret == QMessageBox::Ok)
        proceedWithUpdate = 1;
     } else {
        proceedWithUpdate = 0;
     }
    }

    if (proceedWithUpdate || (d->ConfirmFiberBundleUpdate->checkState() != Qt::Checked))
    {
      d->FiberBundleNode->GetScene()->SaveStateForUndo();
      // Detach polydata from pipeline
      vtkPolyData *filteredPolyData = vtkPolyData::New();
      filteredPolyData->DeepCopy(d->FiberBundleNode->GetFilteredPolyData());
      d->FiberBundleNode->SetAndObservePolyData(filteredPolyData);
      filteredPolyData->Delete();
      d->FiberBundleNode->SetSubsamplingRatio(1);
    }
}

