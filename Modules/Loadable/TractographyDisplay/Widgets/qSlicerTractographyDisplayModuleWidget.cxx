/*==============================================================================

  Program: 3D Slicer

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

==============================================================================*/

// Qt includes
#include <QtConcurrent/QtConcurrent>
#include <QDir>
#include <QFileDialog>
#include <QFuture>
#include <QFutureSynchronizer>
#include <QFutureWatcher>

// VTK includes
#include <vtkPolyData.h>
#include <vtkXMLPolyDataReader.h>

// CTK includes
//#include <ctkModelTester.h>

#include "qSlicerTractographyDisplayModuleWidget.h"
#include "ui_qSlicerTractographyDisplayModuleWidget.h"
#include "qMRMLSceneTractographyDisplayModel.h"
// MRML includes

#include <vtkMRMLDiffusionTensorDisplayPropertiesNode.h>
#include "vtkMRMLNode.h"
#include "vtkMRMLFiberBundleNode.h"
#include "vtkMRMLFiberBundleDisplayNode.h"
#include "vtkMRMLFiberBundleStorageNode.h"
#include "vtkMRMLFiberBundleTubeDisplayNode.h"
#include "vtkMRMLFiberBundleLineDisplayNode.h"
#include "vtkMRMLInteractionNode.h"
#include "vtkMRMLScene.h"

//-----------------------------------------------------------------------------
/// \ingroup Slicer_QtModules_TractographyDisplay
class qSlicerTractographyDisplayModuleWidgetPrivate: public Ui_qSlicerTractographyDisplayModuleWidget
{
  Q_DECLARE_PUBLIC(qSlicerTractographyDisplayModuleWidget);

protected:
  qSlicerTractographyDisplayModuleWidget* const q_ptr;

public:
  qSlicerTractographyDisplayModuleWidgetPrivate(qSlicerTractographyDisplayModuleWidget& object);
  void init();

  vtkMRMLFiberBundleNode* fiberBundleNode;
  double PercentageOfFibersShown;
};

//-----------------------------------------------------------------------------
qSlicerTractographyDisplayModuleWidgetPrivate
::qSlicerTractographyDisplayModuleWidgetPrivate(qSlicerTractographyDisplayModuleWidget& object)
  :q_ptr(&object)
{
  this->fiberBundleNode = NULL;
}

//-----------------------------------------------------------------------------
void qSlicerTractographyDisplayModuleWidgetPrivate::init()
{
  Q_Q(qSlicerTractographyDisplayModuleWidget);

  this->setupUi(q);

  this->percentageOfFibersShown->setTracking(false);

  QObject::connect(this->addDirectory, SIGNAL(clicked()),
                   q, SLOT(onAddDirectory()));
  QObject::connect(this->percentageOfFibersShown, SIGNAL(valueChanged(double)),
                   q, SLOT(setPercentageOfFibersShown(double)));
  QObject::connect(q, SIGNAL(percentageOfFibersShownChanged(double)),
                   this->percentageOfFibersShown, SLOT(setValue(double)));
  QObject::connect(this->SolidTubeColorCheckbox, SIGNAL(clicked(bool)),
                   q, SLOT(setSolidTubeColor(bool)));

  QObject::connect(this->TractographyDisplayTreeView, SIGNAL(visibilityChanged(int)),
                   this->TractDisplayModesTabWidget, SLOT(setCurrentIndex (int)));
}

//-----------------------------------------------------------------------------
qSlicerTractographyDisplayModuleWidget::qSlicerTractographyDisplayModuleWidget(QWidget* _parent)
  : Superclass(_parent)
  , d_ptr(new qSlicerTractographyDisplayModuleWidgetPrivate(*this))
{
  Q_D(qSlicerTractographyDisplayModuleWidget);
  d->init();
}

//-----------------------------------------------------------------------------
qSlicerTractographyDisplayModuleWidget::~qSlicerTractographyDisplayModuleWidget()
{
}

//-----------------------------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::setup()
{
//  Q_D(qSlicerTractographyDisplayModuleWidget);
//  d->setupUi(this);
}

//-----------------------------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::exit()
{
  vtkMRMLInteractionNode *interactionNode =
    vtkMRMLInteractionNode::SafeDownCast(
        this->mrmlScene()->GetNthNodeByClass(0, "vtkMRMLInteractionNode"));
  if (interactionNode)
  {
    interactionNode->SetEnableFiberEdit(0);
  }

  this->Superclass::exit();
}

//-----------------------------------------------------------
bool qSlicerTractographyDisplayModuleWidget::setEditedNode(vtkMRMLNode* node,
                                                        QString role /* = QString()*/,
                                                        QString context /* = QString() */)
{
  Q_UNUSED(role);
  Q_UNUSED(context);
  this->setFiberBundleNode(node);
  return true;
}

//-----------------------------------------------------------
double qSlicerTractographyDisplayModuleWidget::nodeEditable(vtkMRMLNode* node)
{
  if (node->IsA("vtkMRMLFiberBundleNode"))
    {
    return 1.0;
    }
  return 0.1;
}

//-----------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::setFiberBundleNode(vtkMRMLNode* inputNode)
{
  this->setFiberBundleNode(vtkMRMLFiberBundleNode::SafeDownCast(inputNode));
}

//-----------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::setFiberBundleNode(vtkMRMLFiberBundleNode* fiberBundleNode)
{
  Q_D(qSlicerTractographyDisplayModuleWidget);

  if (fiberBundleNode == nullptr)
    {
    d->TractDisplayModesTabWidget->setEnabled(false);
    d->ROIEditorWidget->setEnabled(false);
    d->percentageWidget->setEnabled(false);
    d->SolidTubeColorCheckbox->setEnabled(false);
    }
  else
    {
    d->TractDisplayModesTabWidget->setEnabled(true);
    d->ROIEditorWidget->setEnabled(true);
    d->percentageWidget->setEnabled(true);
    d->SolidTubeColorCheckbox->setEnabled(true);
    }

  if (d->fiberBundleNode == fiberBundleNode)
    return;

  d->fiberBundleNode = fiberBundleNode;

  d->LineDisplayWidget->setFiberBundleNode(fiberBundleNode);
  d->TubeDisplayWidget->setFiberBundleNode(fiberBundleNode);
  d->GlyphDisplayWidget->setFiberBundleNode(fiberBundleNode);
  d->TractographyDisplayTreeView->setCurrentNode(fiberBundleNode);

  if (fiberBundleNode)
  {
    d->LineDisplayWidget->setFiberBundleDisplayNode(fiberBundleNode->GetLineDisplayNode());
    d->TubeDisplayWidget->setFiberBundleDisplayNode(fiberBundleNode->GetTubeDisplayNode());
    d->GlyphDisplayWidget->setFiberBundleDisplayNode(fiberBundleNode->GetGlyphDisplayNode());
    d->GlyphPropertiesWidget->setFiberBundleDisplayNode(fiberBundleNode->GetGlyphDisplayNode());
    d->PercentageOfFibersShown = fiberBundleNode->GetSubsamplingRatio() * 100.;
  }

  emit currentNodeChanged(d->fiberBundleNode);
  emit percentageOfFibersShownChanged(d->PercentageOfFibersShown);
}

//-----------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::setPercentageOfFibersShown(double percentage)
{
  Q_D(qSlicerTractographyDisplayModuleWidget);
  if (vtkMRMLFiberBundleNode::SafeDownCast(d->fiberBundleNode))
    {
    d->PercentageOfFibersShown = percentage;
    d->fiberBundleNode->SetSubsamplingRatio(d->PercentageOfFibersShown / 100.);
    emit percentageOfFibersShownChanged(d->PercentageOfFibersShown);
    }
}

//-----------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::setSolidTubeColor(bool solid)
{
  std::vector<vtkMRMLNode *> nodes;
  this->mrmlScene()->GetNodesByClass("vtkMRMLFiberBundleTubeDisplayNode", nodes);

  vtkMRMLFiberBundleTubeDisplayNode *node = 0;
  for (unsigned int i=0; i<nodes.size(); i++)
    {
    node = vtkMRMLFiberBundleTubeDisplayNode::SafeDownCast(nodes[i]);
    if (solid)
      {
      node->SetColorMode(vtkMRMLFiberBundleDisplayNode::colorModeSolid);
      }
    else
      {
      node->SetColorMode(vtkMRMLFiberBundleDisplayNode::colorModeScalar);
      }
    }
}

//-----------------------------------------------------------
void qSlicerTractographyDisplayModuleWidget::onAddDirectory()
{
  QString directoryPath = QFileDialog::getExistingDirectory(this, "Directory to add");
  if (directoryPath != "")
    {
    this->loadThreaded(directoryPath);
    }
}


//-----------------------------------------------------------

typedef void ReaderType;

class FiberReader : public QObject
{

public:

  QFuture<ReaderType> read(vtkMRMLScene * miniScene, const QString& filePath)
    {
    auto fiberReaderWorker = [](vtkMRMLScene *miniScene, const QString& filePath)
      {
      qDebug() << "inside worker with " << filePath;

      vtkNew<vtkXMLPolyDataReader> reader;
      reader->SetFileName(filePath.toStdString().c_str());
      reader->Update();
      vtkPolyData *polyData = reader->GetOutput();

      vtkNew<vtkMRMLFiberBundleNode> fiberBundleNode;
      QString nodeName = QFileInfo(filePath).baseName();
      fiberBundleNode->SetName(nodeName.toStdString().c_str());

      fiberBundleNode->SetAndObservePolyData(polyData);
      miniScene->AddNode(fiberBundleNode);
      fiberBundleNode->CreateDefaultDisplayNodes();

      };
    return QtConcurrent::run(fiberReaderWorker, miniScene, filePath);
    }
};


//-----------------------------------------------------------
bool qSlicerTractographyDisplayModuleWidget::loadThreaded(QString directoryPath)
{
  this->mrmlScene()->StartState(vtkMRMLScene::ImportState);

  QFutureSynchronizer<void> futureSynchrnonizer;

  QDir dir(directoryPath);
  QStringList nameFilter;
  nameFilter << "*.vtp";
  foreach(QString fileName, dir.entryList(nameFilter)) {

    vtkMRMLScene *miniScene = vtkMRMLScene::New();
    miniScene->CopyRegisteredNodesToScene(this->mrmlScene());

    FiberReader reader;

    QFuture<ReaderType> future = reader.read(miniScene, directoryPath+"/"+fileName);
    futureSynchrnonizer.addFuture(future);

    QFutureWatcher<ReaderType> *watcher = new QFutureWatcher<ReaderType>();

    connect(watcher, &QFutureWatcher<ReaderType>::finished,
      [=]() {
        qDebug() << "Got back scene with " << miniScene->GetNumberOfNodes();

        vtkMRMLNode *node = miniScene->GetNthNodeByClass(0, "vtkMRMLFiberBundleNode");
        vtkMRMLFiberBundleNode *fiberBundleNode = vtkMRMLFiberBundleNode::SafeDownCast(node);
        std::vector<vtkMRMLFiberBundleDisplayNode *> fiberDisplayNodes;
        int displayNodeCount = fiberBundleNode->GetNumberOfDisplayNodes();
        for (int displayNodeIndex = 0; displayNodeIndex < displayNodeCount; displayNodeIndex++)
          {
          vtkMRMLDisplayNode *displayNode = fiberBundleNode->GetNthDisplayNode(displayNodeIndex);
          vtkMRMLFiberBundleDisplayNode *fiberDisplayNode = vtkMRMLFiberBundleDisplayNode::SafeDownCast(displayNode);
          fiberDisplayNodes.push_back(fiberDisplayNode);
          }
        fiberBundleNode->RemoveAllDisplayNodeIDs();
        fiberBundleNode->Register(fiberBundleNode);
        miniScene->RemoveNode(fiberBundleNode);
        for(auto fiberDisplayNode : fiberDisplayNodes)
          {
          vtkMRMLDiffusionTensorDisplayPropertiesNode *propertiesNode;
          propertiesNode = fiberDisplayNode->GetDiffusionTensorDisplayPropertiesNode();
          propertiesNode->Register(fiberBundleNode);
          miniScene->RemoveNode(propertiesNode);
          this->mrmlScene()->AddNode(propertiesNode);
          propertiesNode->Delete();
          fiberDisplayNode->Register(fiberBundleNode);
          miniScene->RemoveNode(fiberDisplayNode);
          this->mrmlScene()->AddNode(fiberDisplayNode);
          fiberDisplayNode->Delete();
          fiberDisplayNode->SetAndObserveDiffusionTensorDisplayPropertiesNodeID(propertiesNode->GetID());
          fiberDisplayNode->SetAndObserveColorNodeID("vtkMRMLColorTableNodeRainbow");
          fiberBundleNode->AddAndObserveDisplayNodeID(fiberDisplayNode->GetID());
          }
        this->mrmlScene()->AddNode(fiberBundleNode);
        fiberBundleNode->Delete();
        miniScene->Delete();
      }
    );
    watcher->setFuture(future);
  }

  futureSynchrnonizer.waitForFinished();

  this->mrmlScene()->EndState(vtkMRMLScene::ImportState);

  return true;
}
