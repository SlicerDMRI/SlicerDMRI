/*=auto=========================================================================

Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

See COPYRIGHT.txt
or http://www.slicer.org/copyright/copyright.txt for details.

Program:   3D Slicer
Module:    $RCSfile: vtkMRMLFiberBundleNode.cxx,v $
Date:      $Date: 2006/03/03 22:26:39 $
Version:   $Revision: 1.3 $

=========================================================================auto=*/

// TractographyMRML includes
#include "vtkMRMLFiberBundleGlyphDisplayNode.h"
#include "vtkMRMLFiberBundleLineDisplayNode.h"
#include "vtkMRMLFiberBundleNode.h"
#include "vtkMRMLFiberBundleStorageNode.h"
#include "vtkMRMLFiberBundleTubeDisplayNode.h"

// MRML includes
#include <vtkMRMLDiffusionTensorDisplayPropertiesNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLAnnotationNode.h>
#include <vtkMRMLAnnotationROINode.h>

// VTK includes
#include <vtkAlgorithmOutput.h>
#include <vtkCommand.h>
#include <vtkExtractPolyDataGeometry.h>
#include <vtkExtractSelectedPolyDataIds.h>
#include <vtkIdTypeArray.h>
#include <vtkInformation.h>
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkPointData.h>
#include <vtkPlanes.h>
#include <vtkPassThrough.h>
#include <vtkSelection.h>
#include <vtkSelectionNode.h>
#include <vtkVersion.h>

// STD includes
#include <algorithm>
#include <cassert>
#include <math.h>
#include <vector>
#include <sstream>

namespace {
vtkPolyData* getAlgorithmPolyData(vtkAlgorithmOutput* output)
{
  if (!output)
    return 0; // TODO nullptr

  vtkAlgorithm* producer = output->GetProducer();
  if (!producer)
    return 0;

  int index = output ? output->GetIndex() : -1;
  return vtkPolyData::SafeDownCast(producer->GetOutputDataObject(index));
}
}; // anonymous namespace

//------------------------------------------------------------------------------
vtkCxxSetReferenceStringMacro(vtkMRMLFiberBundleNode, AnnotationNodeID);

//------------------------------------------------------------------------------
vtkMRMLNodeNewMacro(vtkMRMLFiberBundleNode);

//------------------------------------------------------------------------------
vtkIdType vtkMRMLFiberBundleNode::MaxNumberOfFibersToShowByDefault = 10000;

//-----------------------------------------------------------------------------
vtkMRMLFiberBundleNode::~vtkMRMLFiberBundleNode()
{
  this->SetAndObserveAnnotationNodeID(NULL);

  this->ExtractSubsample->Delete();
  this->ExtractFromROI->Delete();
  this->Planes->Delete();
  this->ShuffledIds->Delete();
  this->LocalPassThrough->Delete();
}

//-----------------------------------------------------------------------------
/* Pipeline:
  *
  * note: this used to have CleanPolyData steps, but they were effectively no-ops.
  *
  * ExtractSubsample ->
  *     ExtractFromROI(this->Planes)
  *
  * Output:
  *
  *   GetFilteredMeshConnection <- LocalPassThrough { SelectWithAnnotation ? ExtractFromROI :
  *                                                                          ExtractSubsample }
*/

//-----------------------------------------------------------------------------
vtkMRMLFiberBundleNode::vtkMRMLFiberBundleNode() :
  ExtractSubsample(vtkExtractSelectedPolyDataIds::New()),
  ExtractFromROI(vtkExtractPolyDataGeometry::New()),
  Planes(vtkPlanes::New()),
  ShuffledIds(vtkIdTypeArray::New()),
  LocalPassThrough(vtkPassThrough::New()),
  AnnotationNode(NULL),
  AnnotationNodeID(NULL)
{
  this->SubsamplingRatio = 1.0;
  this->SelectWithAnnotation = false;
  this->EnableShuffleIDs = true;
  this->AnnotationSelectionMode = vtkMRMLFiberBundleNode::PositiveSelection;

  // set up ExtractFromROI
  this->ExtractFromROI->SetImplicitFunction(this->Planes);
    this->ExtractFromROI->ExtractInsideOn();
    this->ExtractFromROI->ExtractBoundaryCellsOn();

  // set up ExtractSubsample
  vtkNew<vtkSelection> sel;
  vtkNew<vtkIdTypeArray> arr;

  vtkNew<vtkSelectionNode> node;
    node->GetProperties()->Set(vtkSelectionNode::CONTENT_TYPE(), vtkSelectionNode::INDICES);
    node->GetProperties()->Set(vtkSelectionNode::FIELD_TYPE(), vtkSelectionNode::CELL);
    node->SetSelectionList(arr.GetPointer());

  sel->AddNode(node.GetPointer());
  this->ExtractSubsample->SetInputData(1, sel.GetPointer());

  // set up pipeline
  this->ExtractFromROI->SetInputConnection(
    this->ExtractSubsample->GetOutputPort());

  // default mode: produce sub-sampled output
  this->LocalPassThrough->SetInputConnection(
    this->ExtractSubsample->GetOutputPort());
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::WriteXML(ostream& of, int nIndent)
{
  // Write all attributes not equal to their defaults

  Superclass::WriteXML(of, nIndent);

  vtkIndent indent(nIndent);

  if (this->AnnotationNodeID != NULL)
    {
    of << indent << " AnnotationNodeRef=\"" << this->AnnotationNodeID << "\"";
    }
  of << indent << " SelectWithAnnotation=\"" << this->SelectWithAnnotation << "\"";
  of << indent << " AnnotationSelectionMode=\"" << this->AnnotationSelectionMode << "\"";
  of << indent << " SubsamplingRatio=\"" << this->SubsamplingRatio << "\"";
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::ReadXMLAttributes(const char** atts)
{
  int disabledModify = this->StartModify();

  Superclass::ReadXMLAttributes(atts);
  if (this->AnnotationNodeID != NULL)
    {
    delete[] this->AnnotationNodeID;
    }
  this->SelectWithAnnotation = false;

  const char* attName;
  const char* attValue;
  while (*atts != NULL)
    {
    attName = *(atts++);
    attValue = *(atts++);

    if (!strcmp(attName, "AnnotationNodeRef"))
      {
      const size_t n = strlen(attValue) + 1;
      this->AnnotationNodeID = new char[n];
      strcpy(this->AnnotationNodeID, attValue);
      }
    else if (!strcmp(attName, "SelectWithAnnotation"))
      {
      this->SelectWithAnnotation = (bool)atoi(attValue);
      }
    else if (!strcmp(attName, "SelectionWithAnnotationNodeMode"))
      {
      this->AnnotationSelectionMode = (SelectionModeEnum)atoi(attValue);
      }
    else if (!strcmp(attName, "SubsamplingRatio"))
      {
      this->SubsamplingRatio = atof(attValue);
      }
    }

  this->EndModify(disabledModify);
}


//----------------------------------------------------------------------------
// Copy the node's attributes to this object.
// Does NOT copy: ID, FilePrefix, Name, ID
void vtkMRMLFiberBundleNode::Copy(vtkMRMLNode *anode)
{
  int disabledModify = this->StartModify();

  Superclass::Copy(anode);

  vtkMRMLFiberBundleNode *node = vtkMRMLFiberBundleNode::SafeDownCast(anode);

  if (node)
    {
    this->SetSubsamplingRatio(node->SubsamplingRatio);
    this->SetAnnotationNodeID(node->AnnotationNodeID);
    this->SetSelectWithAnnotation(node->SelectWithAnnotation);
    this->SetAnnotationSelectionMode(node->AnnotationSelectionMode);
    }

  this->EndModify(disabledModify);
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::PrintSelf(ostream& os, vtkIndent indent)
{
  Superclass::PrintSelf(os,indent);
}

//---------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::ProcessMRMLEvents (vtkObject *caller,
                                                unsigned long event,
                                                void *callData)
{
  // TODO we should ignore display node events. Fowarding here is silly.
  // but right now we can't, because the  qMRMLTractographyDisplayTreeView only
  // knows how to watch modified events on vtkMRMLFiberBundleNode, so they must
  // be propagated through Superclass.

  if (vtkMRMLAnnotationROINode::SafeDownCast(caller) && (event == vtkCommand::ModifiedEvent))
  {
    vtkDebugMacro("Updating the ROI node");
    this->UpdateROISelection();
  }

  // TODO replace with subsampling filter
  if ((event == vtkCommand::ModifiedEvent) &&
      (this->GetMeshConnection())          &&
      (this->GetMeshConnection()->GetProducer() == caller))
  {
    this->UpdateSubsampling();
  }


  if (vtkMRMLDiffusionTensorDisplayPropertiesNode::SafeDownCast(caller) && event == vtkCommand::ModifiedEvent)
  {
    this->InvokeEvent(vtkMRMLModelNode::DisplayModifiedEvent, NULL);
  }

  Superclass::ProcessMRMLEvents(caller, event, callData);
  return;
}

//-----------------------------------------------------------
void vtkMRMLFiberBundleNode::UpdateReferences()
{
  if (this->AnnotationNodeID != NULL && this->Scene->GetNodeByID(this->AnnotationNodeID) == NULL)
    {
    this->SetAndObserveAnnotationNodeID(NULL);
    }
  this->Superclass::UpdateReferences();
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::UpdateReferenceID(const char *oldID, const char *newID)
{
  this->Superclass::UpdateReferenceID(oldID, newID);
  if (this->AnnotationNodeID && !strcmp(oldID, this->AnnotationNodeID))
    {
    this->SetAnnotationNodeID(newID);
    }
}

//----------------------------------------------------------------------------
vtkAlgorithmOutput* vtkMRMLFiberBundleNode::GetFilteredMeshConnection()
{
  return this->LocalPassThrough->GetOutputPort();
}

//----------------------------------------------------------------------------
vtkPointSet* vtkMRMLFiberBundleNode::GetFilteredPolyData()
{
  this->ExtractSubsample->Update();
  this->ExtractFromROI->Update();
  return getAlgorithmPolyData(this->GetFilteredMeshConnection());
}

//----------------------------------------------------------------------------
vtkMRMLFiberBundleDisplayNode* vtkMRMLFiberBundleNode::GetLineDisplayNode()
{
  int nnodes = this->GetNumberOfDisplayNodes();
  vtkMRMLFiberBundleLineDisplayNode *node = NULL;
  for (int n=0; n<nnodes; n++)
    {
    node = vtkMRMLFiberBundleLineDisplayNode::SafeDownCast(this->GetNthDisplayNode(n));
    if (node)
      {
      break;
      }
    }
  return node;
}

//----------------------------------------------------------------------------
vtkMRMLFiberBundleDisplayNode* vtkMRMLFiberBundleNode::GetTubeDisplayNode()
{
  int nnodes = this->GetNumberOfDisplayNodes();
  vtkMRMLFiberBundleTubeDisplayNode *node = NULL;
  for (int n=0; n<nnodes; n++)
    {
    node = vtkMRMLFiberBundleTubeDisplayNode::SafeDownCast(this->GetNthDisplayNode(n));
    if (node)
      {
      break;
      }
    }
  return node;
}

//----------------------------------------------------------------------------
vtkMRMLFiberBundleDisplayNode* vtkMRMLFiberBundleNode::GetGlyphDisplayNode()
{
  int nnodes = this->GetNumberOfDisplayNodes();
  vtkMRMLFiberBundleGlyphDisplayNode *node = NULL;
  for (int n=0; n<nnodes; n++)
    {
    node = vtkMRMLFiberBundleGlyphDisplayNode::SafeDownCast(this->GetNthDisplayNode(n));
    if (node)
      {
      break;
      }
    }
  return node;
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetMeshToDisplayNode(vtkMRMLModelDisplayNode *modelDisplayNode)
{
  // overload here to make sure the display node gets our filtered output.
  // TODO: vtkMRMLModelNode uses the internally stored connection... change?

  assert(modelDisplayNode);
  this->ExtractSubsample->SetInputConnection(this->MeshConnection);
  modelDisplayNode->SetInputMeshConnection(this->GetFilteredMeshConnection());
}

namespace {
void fixupPolyDataTensors(vtkAlgorithmOutput* inputPort) {
  // we need the raw polydata from the input object
  vtkPolyData* polyData = getAlgorithmPolyData(inputPort);

  // Ensure that tensor arrays are named and set
  if (polyData && polyData->GetPointData())
    {
    for (int i=0; i<polyData->GetPointData()->GetNumberOfArrays(); i++)
      {
      if (polyData->GetPointData()->GetArray(i)->GetNumberOfComponents() == 9)
        {
        if (polyData->GetPointData()->GetArray(i)->GetName() == 0)
          {
          std::stringstream ss;
          ss << "Tensor_" << i;
          polyData->GetPointData()->GetArray(i)->SetName(ss.str().c_str());
          }
        if (!polyData->GetPointData()->GetTensors())
          {
          polyData->GetPointData()->SetTensors(polyData->GetPointData()->GetArray(i));
          }
        }
      }
    }
}
}; // namespace

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetMeshConnection(vtkAlgorithmOutput *inputPort)
{
  this->Superclass::SetMeshConnection(inputPort);
  this->ExtractSubsample->SetInputConnection(inputPort);

  fixupPolyDataTensors(inputPort);

  // we need the raw polydata from the input object
  vtkPolyData* polyData = getAlgorithmPolyData(inputPort);

  if (polyData)
    {
    const vtkIdType numberOfFibers = polyData->GetNumberOfLines();

    float subsamplingRatio = this->SubsamplingRatio;

    if (numberOfFibers > vtkMRMLFiberBundleNode::MaxNumberOfFibersToShowByDefault )
      {
      subsamplingRatio = this->GetMaxNumberOfFibersToShowByDefault() * 1. / numberOfFibers;
      subsamplingRatio = floor(subsamplingRatio * 1e2) / 1e2;
      if (subsamplingRatio < 0.01)
        subsamplingRatio = 0.01;
      }

    this->SetSubsamplingRatio(subsamplingRatio);

    this->UpdateSubsampling();

    if (this->GetSelectWithAnnotation() == true)
      {
      this->UpdateROISelection();
      }
    }
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetSubsamplingRatio (float ratio)
  {
  vtkDebugMacro(<< this->GetClassName() << " (" << this << "): setting subsamplingRatio to " << ratio);
  const float oldSubsampling = this->SubsamplingRatio;
  const float newSubsamplingRatio = vtkMath::ClampValue<float>(ratio, 0.0, 1.0);
  if (oldSubsampling != newSubsamplingRatio)
    {
    this->SubsamplingRatio = newSubsamplingRatio;
    }
    this->UpdateSubsampling();
  }


//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetSelectWithAnnotation(bool state)
{
  if (this->SelectWithAnnotation == state)
    return;

  this->SelectWithAnnotation = state;

  int wasModifying = this->StartModify();
    {
    if (state == true)
      this->LocalPassThrough->SetInputConnection(this->ExtractFromROI->GetOutputPort());
    else
      this->LocalPassThrough->SetInputConnection(this->ExtractSubsample->GetOutputPort());
    }
  this->EndModify(wasModifying);

  this->UpdateROISelection();
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetAnnotationSelectionMode(SelectionModeEnum mode)
{
  if (this->AnnotationSelectionMode == mode)
    return;

  this->AnnotationSelectionMode = mode;

  if (mode == vtkMRMLFiberBundleNode::PositiveSelection)
    {
    this->ExtractFromROI->ExtractInsideOn();
    this->ExtractFromROI->ExtractBoundaryCellsOn();
    }
  else if (mode == vtkMRMLFiberBundleNode::NegativeSelection)
    {
    this->ExtractFromROI->ExtractInsideOff();
    this->ExtractFromROI->ExtractBoundaryCellsOff();
    }
  else
    {
    this->LocalPassThrough->SetInputConnection(this->ExtractSubsample->GetOutputPort());
    }

  this->UpdateROISelection();
}

//----------------------------------------------------------------------------
vtkMRMLAnnotationNode* vtkMRMLFiberBundleNode::GetAnnotationNode()
{
  vtkMRMLAnnotationNode* node = NULL;

  // Find the node corresponding to the ID we have saved.
  if  ( this->GetScene ( ) && this->GetAnnotationNodeID ( ) )
    {
    vtkMRMLNode* cnode = this->GetScene ( ) -> GetNodeByID ( this->AnnotationNodeID );
    node = vtkMRMLAnnotationNode::SafeDownCast ( cnode );
    }

  return node;
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::SetAndObserveAnnotationNodeID(const char *id)
{
  if (id)
    {
    vtkDebugMacro("Observing annotation Node: "<<id);
    }
  // Stop observing any old node
  vtkSetAndObserveMRMLObjectMacro(this->AnnotationNode, NULL);

  // Set the ID. This is the "ground truth" reference to the node.
  this->SetAnnotationNodeID(id);

  // Get the node corresponding to the ID. This pointer is only to observe the object.
  vtkMRMLNode *cnode = this->GetAnnotationNode();

  // Observe the node using the pointer.
  vtkSetAndObserveMRMLObjectMacro(this->AnnotationNode, cnode);

  if (!cnode)
    {
    this->SetSelectWithAnnotation(false);
    }

  this->UpdateROISelection();
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::UpdateSubsampling()
{
  vtkDebugMacro(<< this->GetClassName() << "Updating the subsampling");
  vtkSelection* sel = vtkSelection::SafeDownCast(this->ExtractSubsample->GetInput(1));

  vtkPolyData* polyData = getAlgorithmPolyData(this->Superclass::GetMeshConnection());

  if (!(sel && polyData))
    {
    return;
    }

  vtkSelectionNode* node = sel->GetNode(0);
  vtkIdTypeArray* arr = vtkIdTypeArray::SafeDownCast(node->GetSelectionList());
  vtkIdType numberOfCellsToKeep = vtkIdType(floor(polyData->GetNumberOfLines() * this->SubsamplingRatio));

  if (numberOfCellsToKeep == arr->GetNumberOfTuples())
    {
    // no change, no-op
    return;
    }

  const vtkIdType numberOfFibers = polyData->GetNumberOfLines();
  if (this->ShuffledIds->GetNumberOfTuples() != numberOfFibers)
    {

    std::vector<vtkIdType> idVector;
    idVector.reserve(numberOfFibers);
    for (vtkIdType i = 0;  i < numberOfFibers; i++)
      idVector.push_back(i);

    if (this->EnableShuffleIDs)
      {
      std::random_device randomDevice;
      std::mt19937 randomGenerator(randomDevice());
      std::shuffle(idVector.begin(), idVector.end(), randomGenerator);
      }

    this->ShuffledIds->Initialize();

    /* unsafe block */ {

      // copy must be paired with allocation
      // so that the buffer is sufficient

      this->ShuffledIds->SetNumberOfTuples(numberOfFibers);
      std::copy(idVector.begin(), idVector.end(),
                static_cast<vtkIdType*>(this->ShuffledIds->GetVoidPointer(0)));

    /* end unsafe block */ }

    }

  arr->Initialize();
  arr->SetNumberOfTuples(numberOfCellsToKeep);
  for (vtkIdType i=0; i < numberOfCellsToKeep; i++)
    {
    arr->SetValue(i, this->ShuffledIds->GetValue(i));
    }

  arr->Modified();

  // tell the displaynode to render
  this->InvokeCustomModifiedEvent( vtkMRMLModelNode::MeshModifiedEvent , this);
}

//----------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::UpdateROISelection()
{
  vtkMRMLAnnotationROINode* AnnotationROI =
    vtkMRMLAnnotationROINode::SafeDownCast(this->AnnotationNode);

  if (AnnotationROI && this->GetSelectWithAnnotation() == true)
    {
    AnnotationROI->GetTransformedPlanes(this->Planes);
    this->ExtractFromROI->Modified();
    }

  // tell the displaynode to render
  this->InvokeCustomModifiedEvent( vtkMRMLModelNode::MeshModifiedEvent , this);
}

//---------------------------------------------------------------------------
vtkMRMLStorageNode* vtkMRMLFiberBundleNode::CreateDefaultStorageNode()
{
  vtkDebugMacro("vtkMRMLFiberBundleNode::CreateDefaultStorageNode");
  return vtkMRMLStorageNode::SafeDownCast(vtkMRMLFiberBundleStorageNode::New());
}

//---------------------------------------------------------------------------
std::string vtkMRMLFiberBundleNode:: GetDefaultStorageNodeClassName(const char* filename /* =nullptr */)
{
  vtkDebugMacro("vtkMRMLFiberBundleNode::GetDefaultStorageNodeClassName");
  return "vtkMRMLFiberBundleStorageNode";
}



//---------------------------------------------------------------------------
vtkMRMLFiberBundleDisplayNode* addDisplayNodeAndDTDPN(vtkMRMLFiberBundleNode* fbNode,
                                                      vtkMRMLFiberBundleDisplayNode* node)
{
  if (!fbNode->GetScene())
    return node;

  fbNode->GetScene()->AddNode(node);
  vtkNew<vtkMRMLDiffusionTensorDisplayPropertiesNode> glyphDTDPN;
  fbNode->GetScene()->AddNode(glyphDTDPN.GetPointer());
  node->SetAndObserveDiffusionTensorDisplayPropertiesNodeID(glyphDTDPN->GetID());
  node->SetAndObserveColorNodeID("vtkMRMLColorTableNodeRainbow");

  fbNode->AddAndObserveDisplayNodeID(node->GetID());
  return node;
}

//---------------------------------------------------------------------------
void vtkMRMLFiberBundleNode::CreateDefaultDisplayNodes()
{
  vtkDebugMacro("vtkMRMLFiberBundleNode::CreateDefaultDisplayNodes");
  if (!this->GetScene())
    return;

  if (!this->GetLineDisplayNode())
  {
    vtkNew<vtkMRMLFiberBundleLineDisplayNode> node;
    addDisplayNodeAndDTDPN(this, node.GetPointer());
    node->SetVisibility(1);
  }

  if (!this->GetTubeDisplayNode())
  {
    vtkNew<vtkMRMLFiberBundleTubeDisplayNode> node;
    addDisplayNodeAndDTDPN(this, node.GetPointer());
    node->SetVisibility(0);
  }

  if (!this->GetGlyphDisplayNode())
  {
    vtkNew<vtkMRMLFiberBundleGlyphDisplayNode> node;
    addDisplayNodeAndDTDPN(this, node.GetPointer());
    node->SetVisibility(0);
  }
}
