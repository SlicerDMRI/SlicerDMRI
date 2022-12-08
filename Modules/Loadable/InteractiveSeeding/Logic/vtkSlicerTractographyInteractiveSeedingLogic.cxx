/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkSlicerTractographyInteractiveSeedingLogic.cxx,v $
  Date:      $Date: 2006/01/06 17:56:48 $
  Version:   $Revision: 1.58 $

=========================================================================auto=*/

#include "vtkSlicerTractographyInteractiveSeedingLogic.h"

// MRML includes
#include <vtkMRMLAnnotationControlPointsNode.h>
#include <vtkMRMLAnnotationFiducialNode.h>
#include <vtkMRMLAnnotationHierarchyNode.h>
#include <vtkMRMLDiffusionTensorVolumeNode.h>
#include <vtkMRMLFiberBundleDisplayNode.h>
#include <vtkMRMLFiberBundleNode.h>
#include <vtkMRMLFiberBundleStorageNode.h>
#include <vtkMRMLMarkupsFiducialNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLScalarVolumeNode.h>
#include <vtkMRMLTransformNode.h>
#include <vtkMRMLSubjectHierarchyNode.h>
#include "vtkMRMLTractographyInteractiveSeedingNode.h"

// vtkTeem includes
#include <vtkDiffusionTensorMathematics.h>

// VTK includes
#include <vtkImageCast.h>
#include <vtkImageChangeInformation.h>
#include <vtkImageThreshold.h>
#include <vtkMaskPoints.h>
#include <vtkMath.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkSeedTracts.h>
#include <vtkSmartPointer.h>
#include <vtkVersion.h>

// STD includes
#include <algorithm>

vtkStandardNewMacro(vtkSlicerTractographyInteractiveSeedingLogic);

//----------------------------------------------------------------------------
vtkSlicerTractographyInteractiveSeedingLogic::vtkSlicerTractographyInteractiveSeedingLogic()
{
  this->MaskPoints = vtkMaskPoints::New();
  this->TractographyInteractiveSeedingNode = NULL;
  this->DiffusionTensorVolumeNode = NULL;
}

//----------------------------------------------------------------------------
vtkSlicerTractographyInteractiveSeedingLogic::~vtkSlicerTractographyInteractiveSeedingLogic()
{
  this->MaskPoints->Delete();
  this->RemoveMRMLNodesObservers();
  vtkSetAndObserveMRMLNodeMacro(this->TractographyInteractiveSeedingNode, NULL);
  vtkSetAndObserveMRMLNodeMacro(this->DiffusionTensorVolumeNode, NULL);
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::RemoveMRMLNodesObservers()
{
  for (unsigned int i=0; i<this->ObservedNodes.size(); i++)
    {
    vtkSetAndObserveMRMLNodeMacro(this->ObservedNodes[i], NULL);
    }
  this->ObservedNodes.clear();
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->vtkObject::PrintSelf(os, indent);
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::SetAndObserveTractographyInteractiveSeedingNode(vtkMRMLTractographyInteractiveSeedingNode *node)
{
  vtkMRMLTractographyInteractiveSeedingNode *oldNode = this->TractographyInteractiveSeedingNode;

  vtkSetAndObserveMRMLNodeMacro(this->TractographyInteractiveSeedingNode, node);

  if (node && node != oldNode)
    {
    this->RemoveMRMLNodesObservers();

    this->AddMRMLNodesObservers();

    return;
    }

  this->ProcessMRMLNodesEvents(this->TractographyInteractiveSeedingNode, vtkCommand::ModifiedEvent, NULL);
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::AddMRMLNodesObservers()
{
  if (this->TractographyInteractiveSeedingNode)
    {
    vtkMRMLNode *seedinNode = this->GetMRMLScene()->GetNodeByID(this->TractographyInteractiveSeedingNode->GetInputFiducialRef());

    vtkMRMLAnnotationHierarchyNode *annotationHierarchyNode = vtkMRMLAnnotationHierarchyNode::SafeDownCast(seedinNode);
    vtkMRMLTransformableNode *transformableNode = vtkMRMLTransformableNode::SafeDownCast(seedinNode);
    vtkMRMLMarkupsFiducialNode *markupsFiducialNode = vtkMRMLMarkupsFiducialNode::SafeDownCast(seedinNode);

    if (annotationHierarchyNode)
      {
      this->ObservedNodes.push_back(NULL);
      vtkNew<vtkIntArray> annotationHierarchyNodeEvents;
      annotationHierarchyNodeEvents->InsertNextValue ( vtkMRMLHierarchyNode::ChildNodeAddedEvent );
      annotationHierarchyNodeEvents->InsertNextValue ( vtkMRMLHierarchyNode::ChildNodeRemovedEvent );
      annotationHierarchyNodeEvents->InsertNextValue ( vtkMRMLNode::HierarchyModifiedEvent );

      vtkSetAndObserveMRMLNodeEventsMacro(
            this->ObservedNodes[this->ObservedNodes.size()-1],
            annotationHierarchyNode,
            annotationHierarchyNodeEvents.GetPointer());

      vtkNew<vtkCollection> annotationNodes;
      annotationHierarchyNode->GetDirectChildren(annotationNodes.GetPointer());
      int nf = annotationNodes->GetNumberOfItems();
      for (int f=0; f<nf; f++)
        {
        vtkMRMLAnnotationControlPointsNode *annotationNode = vtkMRMLAnnotationControlPointsNode::SafeDownCast(
                                                      annotationNodes->GetItemAsObject(f));
        if (annotationNode)
          {
          this->ObservedNodes.push_back(NULL);

          vtkNew<vtkIntArray> annotationNodeEvents;
          annotationNodeEvents->InsertNextValue ( vtkMRMLTransformableNode::TransformModifiedEvent );
          annotationNodeEvents->InsertNextValue ( vtkMRMLModelNode::PolyDataModifiedEvent );
          annotationNodeEvents->InsertNextValue ( vtkCommand::ModifiedEvent );

          vtkSetAndObserveMRMLNodeEventsMacro(
                this->ObservedNodes[this->ObservedNodes.size()-1],
                annotationNode,
                annotationNodeEvents.GetPointer());
          }
        }
      }
    else if (markupsFiducialNode)
      {
      this->ObservedNodes.push_back(NULL);
      vtkNew<vtkIntArray> markupEvents;
      markupEvents->InsertNextValue ( vtkMRMLTransformableNode::TransformModifiedEvent );
      markupEvents->InsertNextValue ( vtkMRMLMarkupsNode::PointModifiedEvent );
      markupEvents->InsertNextValue ( vtkMRMLMarkupsNode::PointAddedEvent );
      markupEvents->InsertNextValue ( vtkMRMLMarkupsNode::PointRemovedEvent );
      vtkSetAndObserveMRMLNodeEventsMacro(this->ObservedNodes[this->ObservedNodes.size()-1],
                                          markupsFiducialNode, markupEvents.GetPointer());
      }
    else if (transformableNode)
      {
      this->ObservedNodes.push_back(NULL);
      vtkNew<vtkIntArray> events;
      events->InsertNextValue ( vtkMRMLTransformableNode::TransformModifiedEvent );
      events->InsertNextValue ( vtkMRMLModelNode::PolyDataModifiedEvent );
      events->InsertNextValue ( vtkMRMLVolumeNode::ImageDataModifiedEvent );
      events->InsertNextValue ( vtkCommand::ModifiedEvent );
      vtkSetAndObserveMRMLNodeEventsMacro(this->ObservedNodes[this->ObservedNodes.size()-1],
                                          transformableNode, events.GetPointer());
      }
    }
  else
    {
    vtkSetAndObserveMRMLNodeMacro(this->DiffusionTensorVolumeNode, NULL);
    }
  return;
}

//----------------------------------------------------------------------------
int vtkSlicerTractographyInteractiveSeedingLogic::IsObservedNode(vtkMRMLNode *node)
{
  std::vector<vtkMRMLTransformableNode *>::const_iterator observedNodeIt =
    std::find(this->ObservedNodes.begin(), this->ObservedNodes.end(),node);
  return observedNodeIt != this->ObservedNodes.end();
}

//----------------------------------------------------------------------------
// DRY local helper function
void setStreamerThresholdMode(vtkSmartPointer<vtkHyperStreamlineDTMRI> streamer,
                              int thresholdMode)
{
  if ( thresholdMode == vtkMRMLTractographyInteractiveSeedingNode::LinearMeasure )
    {
     streamer->SetThresholdModeToLinearMeasure();
    }
  else if ( thresholdMode == vtkMRMLTractographyInteractiveSeedingNode::FractionalAnisotropy )
    {
    streamer->SetThresholdModeToFractionalAnisotropy();
    }
  else if ( thresholdMode == vtkMRMLTractographyInteractiveSeedingNode::PlanarMeasure )
    {
    streamer->SetThresholdModeToPlanarMeasure();
    }
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::CreateTractsForOneSeed(vtkSeedTracts *seed,
                                                            vtkMRMLDiffusionTensorVolumeNode *volumeNode,
                                                            vtkMRMLTransformableNode *transformableNode,
                                                            int thresholdMode,
                                                            double stoppingValue,
                                                            double stoppingCurvature,
                                                            double integrationStepLength,
                                                            double minPathLength,
                                                            double regionSize, double sampleStep,
                                                            int maxNumberOfSeeds,
                                                            int seedSelectedFiducials)
{
  double sp[3];
  volumeNode->GetSpacing(sp);

  //2. Set Up matrices
  vtkMRMLTransformNode* vxformNode = volumeNode->GetParentTransformNode();
  vtkMRMLTransformNode* fxformNode = transformableNode->GetParentTransformNode();
  vtkNew<vtkMatrix4x4> transformVolumeToFiducial;
  transformVolumeToFiducial->Identity();
  if (fxformNode != NULL )
    {
    fxformNode->GetMatrixTransformToNode(vxformNode, transformVolumeToFiducial.GetPointer());
    }
  else if (vxformNode != NULL )
    {
    vxformNode->GetMatrixTransformToNode(fxformNode, transformVolumeToFiducial.GetPointer());
    transformVolumeToFiducial->Invert();
    }
  vtkNew<vtkTransform> transFiducial;
  transFiducial->Identity();
  transFiducial->PreMultiply();
  transFiducial->SetMatrix(transformVolumeToFiducial.GetPointer());

  vtkNew<vtkMatrix4x4> mat;
  volumeNode->GetRASToIJKMatrix(mat.GetPointer());

  vtkNew<vtkMatrix4x4> tensorRASToIJK;
  tensorRASToIJK->DeepCopy(mat.GetPointer());

  vtkNew<vtkTransform> trans;
  trans->Identity();
  trans->PreMultiply();
  trans->SetMatrix(tensorRASToIJK.GetPointer());
  // Trans from IJK to RAS
  trans->Inverse();
  // Take into account spacing to compute Scaled IJK
  trans->Scale(1/sp[0],1/sp[1],1/sp[2]);
  trans->Inverse();

  //Set Transformation to seeding class
  seed->SetWorldToTensorScaledIJK(trans.GetPointer());

  vtkNew<vtkMatrix4x4> tensorRASToIJKRotation;
  tensorRASToIJKRotation->DeepCopy(tensorRASToIJK.GetPointer());

  //Set Translation to zero
  for (int i=0;i<3;i++)
    {
    tensorRASToIJKRotation->SetElement(i,3,0);
    }
  //Remove scaling in rasToIjk to make a real roation matrix
  double col[3];
  for (int jjj = 0; jjj < 3; jjj++)
    {
    for (int iii = 0; iii < 3; iii++)
      {
      col[iii]=tensorRASToIJKRotation->GetElement(iii,jjj);
      }
    vtkMath::Normalize(col);
    for (int iii = 0; iii < 3; iii++)
      {
      tensorRASToIJKRotation->SetElement(iii,jjj,col[iii]);
     }
  }
  tensorRASToIJKRotation->Invert();
  seed->SetTensorRotationMatrix(tensorRASToIJKRotation.GetPointer());

  //ROI comes from tensor, IJKToRAS is the same
  // as the tensor
  vtkNew<vtkTransform> trans2;
  trans2->Identity();
  trans2->SetMatrix(tensorRASToIJK.GetPointer());
  trans2->Inverse();
  seed->SetROIToWorld(trans2.GetPointer());

  seed->UseVtkHyperStreamlinePoints();

  vtkNew<vtkHyperStreamlineDTMRI> streamer;
  seed->SetVtkHyperStreamlinePointsSettings(streamer.GetPointer());
  seed->SetMinimumPathLength(minPathLength);

  setStreamerThresholdMode(streamer.GetPointer(), thresholdMode);

  //streamer->SetMaximumPropagationDistance(this->MaximumPropagationDistance);
  streamer->SetStoppingThreshold(stoppingValue);
  streamer->SetRadiusOfCurvature(stoppingCurvature);
  streamer->SetIntegrationStepLength(integrationStepLength);

  // Temp fix to provide a scalar
  vtkImageData* inputTensorField = vtkImageData::SafeDownCast(
        seed->GetInputTensorFieldConnection()->GetProducer()->GetOutputDataObject(0));
  inputTensorField->GetPointData()->SetScalars(volumeNode->GetImageData()->GetPointData()->GetScalars());

  vtkMRMLAnnotationControlPointsNode *annotationNode = vtkMRMLAnnotationControlPointsNode::SafeDownCast(transformableNode);
  vtkMRMLMarkupsFiducialNode *markupsFiducialNode = vtkMRMLMarkupsFiducialNode::SafeDownCast(transformableNode);
  vtkMRMLModelNode *modelNode = vtkMRMLModelNode::SafeDownCast(transformableNode);

  // if annotation
  if (annotationNode && annotationNode->GetNumberOfControlPoints() &&
     (!seedSelectedFiducials || (seedSelectedFiducials && annotationNode->GetSelected())) )
    {
    for (int i=0; i < annotationNode->GetNumberOfControlPoints(); i++)
      {
      double *xyzf = annotationNode->GetControlPointCoordinates(i);
      for (double x = -regionSize/2.0; x <= regionSize/2.0; x+=sampleStep)
        {
        for (double y = -regionSize/2.0; y <= regionSize/2.0; y+=sampleStep)
          {
          for (double z = -regionSize/2.0; z <= regionSize/2.0; z+=sampleStep)
            {
            float newXYZ[3];
            newXYZ[0] = xyzf[0] + x;
            newXYZ[1] = xyzf[1] + y;
            newXYZ[2] = xyzf[2] + z;
            float *xyz = transFiducial->TransformFloatPoint(newXYZ);
            //Run the thing
            seed->SeedStreamlineFromPoint(xyz[0], xyz[1], xyz[2]);
            }
          }
        }
      }
    }
  else if (markupsFiducialNode && markupsFiducialNode->GetNumberOfControlPoints())
    {
    int numberOfFiducials = markupsFiducialNode->GetNumberOfMarkups();
    for (int i = 0; i < numberOfFiducials; ++i)
      {
      if (!seedSelectedFiducials ||
          (seedSelectedFiducials && markupsFiducialNode->GetNthControlPointSelected(i)))
        {
        double *xyzf;
        xyzf = markupsFiducialNode->GetNthControlPointPosition(i);
        for (double x = -regionSize/2.0; x <= regionSize/2.0; x+=sampleStep)
          {
          for (double y = -regionSize/2.0; y <= regionSize/2.0; y+=sampleStep)
            {
            for (double z = -regionSize/2.0; z <= regionSize/2.0; z+=sampleStep)
              {
              float newXYZ[3];
              newXYZ[0] = xyzf[0] + x;
              newXYZ[1] = xyzf[1] + y;
              newXYZ[2] = xyzf[2] + z;
              float *xyz = transFiducial->TransformFloatPoint(newXYZ);
              //Run the thing
              seed->SeedStreamlineFromPoint(xyz[0], xyz[1], xyz[2]);
              }
            }
          }
        }
      }
    }
  else if (modelNode)
    {
    this->MaskPoints->SetInputData(modelNode->GetPolyData());
    this->MaskPoints->SetRandomMode(1);
    this->MaskPoints->SetMaximumNumberOfPoints(maxNumberOfSeeds);
    this->MaskPoints->Update();
    vtkPolyData *mpoly = this->MaskPoints->GetOutput();

    int nf = mpoly->GetNumberOfPoints();
    for (int f=0; f<nf; f++)
      {
      double *xyzf = mpoly->GetPoint(f);

      double *xyz = transFiducial->TransformDoublePoint(xyzf);

      //Run the thing
      seed->SeedStreamlineFromPoint(xyz[0], xyz[1], xyz[2]);
      }
    }
}

//----------------------------------------------------------------------------
int vtkSlicerTractographyInteractiveSeedingLogic::CreateTracts(vtkMRMLTractographyInteractiveSeedingNode *parametersNode,
                                                            vtkMRMLDiffusionTensorVolumeNode *volumeNode,
                                                            vtkMRMLNode *seedingNode,
                                                            vtkMRMLFiberBundleNode *fiberNode,
                                                            int thresholdMode,
                                                            double stoppingValue,
                                                            double stoppingCurvature,
                                                            double integrationStepLength,
                                                            double minPathLength,
                                                            double regionSize, double sampleStep,
                                                            int maxNumberOfSeeds,
                                                            int seedSelectedFiducials,
                                                            int vtkNotUsed(displayMode))
{
  // 0. check inputs
  if (volumeNode == NULL || seedingNode == NULL || fiberNode == NULL ||
      volumeNode->GetImageData() == NULL)
    {
    if (fiberNode && fiberNode->GetPolyData())
      {
      fiberNode->GetPolyData()->Reset();
      }
    return 0;
    }

  vtkNew<vtkSeedTracts> seed;

  //1. Set Input

  vtkMRMLAnnotationHierarchyNode *annotationListNode = vtkMRMLAnnotationHierarchyNode::SafeDownCast(seedingNode);
  vtkMRMLAnnotationControlPointsNode *annotationNode = vtkMRMLAnnotationControlPointsNode::SafeDownCast(seedingNode);
  vtkMRMLMarkupsFiducialNode *markupsFiducialNode = vtkMRMLMarkupsFiducialNode::SafeDownCast(seedingNode);
  vtkMRMLModelNode *modelNode = vtkMRMLModelNode::SafeDownCast(seedingNode);
  vtkMRMLScalarVolumeNode *labelMapNode = vtkMRMLScalarVolumeNode::SafeDownCast(seedingNode);

   if( parametersNode->GetWriteToFile() )
    {
    seed->SetFileDirectoryName(parametersNode->GetFileDirectoryName());
    if( parametersNode->GetFilePrefix() != 0 )
      {
      seed->SetFilePrefix(parametersNode->GetFilePrefix() );
      }
    }

  //Do scale IJK
  double sp[3];
  volumeNode->GetSpacing(sp);
  vtkNew<vtkImageChangeInformation> ici;
  ici->SetOutputSpacing(sp);
  ici->SetInputConnection(volumeNode->GetImageDataConnection());
  seed->SetInputTensorFieldConnection(ici->GetOutputPort());

  if ( labelMapNode && parametersNode->GetROILabels() )
    {
    double range[2];
    range[0]=-1;
    range[1]=1e10;
    labelMapNode->GetImageData()->GetScalarRange(range);

    for (int i=0; i<parametersNode->GetROILabels()->GetNumberOfTuples(); i++)
      {
      // check if label is in the range
      int label = parametersNode->GetROILabels()->GetValue(i);
      if (range[0] > label || label > range[1])
        {
        continue;
        }

      this->CreateTractsForLabelMap(seed.GetPointer(), volumeNode, labelMapNode,
                                    parametersNode->GetROILabels()->GetValue(i),
                                    parametersNode->GetUseIndexSpace(),
                                    parametersNode->GetSeedSpacing(),
                                    parametersNode->GetRandomGrid(),
                                    parametersNode->GetStartThreshold(),
                                    parametersNode->GetThresholdMode(),
                                    parametersNode->GetStoppingValue(),
                                    parametersNode->GetStoppingCurvature(),
                                    parametersNode->GetIntegrationStep(),
                                    parametersNode->GetMinimumPathLength(),
                                    parametersNode->GetMaximumPathLength());
      }
    }
  else if (annotationListNode) // loop over annotation nodes
    {
    vtkNew<vtkCollection> annotationNodes;
    annotationListNode->GetDirectChildren(annotationNodes.GetPointer());
    int nf = annotationNodes->GetNumberOfItems();
    for (int f=0; f<nf; f++)
      {
      vtkMRMLAnnotationControlPointsNode *annotationNode = vtkMRMLAnnotationControlPointsNode::SafeDownCast(
                                                    annotationNodes->GetItemAsObject(f));
      if (!annotationNode || (seedSelectedFiducials && !annotationNode->GetSelected()))
        {
        continue;
        }

      this->CreateTractsForOneSeed(seed.GetPointer(), volumeNode, annotationNode,
                                   thresholdMode, stoppingValue, stoppingCurvature,
                                   integrationStepLength, minPathLength, regionSize,
                                   sampleStep, maxNumberOfSeeds, seedSelectedFiducials);
      }
    }
  else if (annotationNode) // loop over points in the models
    {
    this->CreateTractsForOneSeed(seed.GetPointer(), volumeNode, annotationNode,
                                 thresholdMode, stoppingValue, stoppingCurvature,
                                 integrationStepLength, minPathLength, regionSize,
                                 sampleStep, maxNumberOfSeeds, seedSelectedFiducials);
    }
  else if (markupsFiducialNode) // loop over points in the markup
    {
    this->CreateTractsForOneSeed(seed.GetPointer(), volumeNode, markupsFiducialNode,
                                 thresholdMode, stoppingValue, stoppingCurvature,
                                 integrationStepLength, minPathLength, regionSize,
                                 sampleStep, maxNumberOfSeeds, seedSelectedFiducials);
    }
  else if (modelNode) // loop over points in the models
    {
    this->CreateTractsForOneSeed(seed.GetPointer(), volumeNode, modelNode,
                                 thresholdMode, stoppingValue, stoppingCurvature,
                                 integrationStepLength, minPathLength, regionSize,
                                 sampleStep, maxNumberOfSeeds, seedSelectedFiducials);
    }

  //6. Extract PolyData in RAS
  vtkNew<vtkPolyData> outFibers;

  seed->TransformStreamlinesToRASAndAppendToPolyData(outFibers.GetPointer());
  fiberNode->SetAndObservePolyData(outFibers.GetPointer());

  return 1;
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::ProcessMRMLNodesEvents(vtkObject *caller,
                                                                      unsigned long event,
                                                                      void *callData)
{
  vtkMRMLScene* scene = this->GetMRMLScene();
  if (!scene)
    {
    return;
    }

  vtkMRMLTractographyInteractiveSeedingNode* snode = this->TractographyInteractiveSeedingNode;

  if (snode == NULL || snode->GetEnableSeeding() == 0)
    {
    return;
    }

  if (event == vtkMRMLModelNode::PolyDataModifiedEvent ||
      event == vtkMRMLMarkupsNode::PointModifiedEvent)
    {
    this->UpdateOnce();
    }
  else if (event == vtkMRMLHierarchyNode::ChildNodeAddedEvent ||
      event == vtkMRMLHierarchyNode::ChildNodeRemovedEvent ||
      event == vtkMRMLNode::HierarchyModifiedEvent ||
      event == vtkMRMLTransformableNode::TransformModifiedEvent ||
      event == vtkMRMLMarkupsNode::PointAddedEvent ||
      event == vtkMRMLMarkupsNode::PointRemovedEvent)
    {
    this->OnMRMLNodeModified(NULL);
    }
  else
    {
    Superclass::ProcessMRMLNodesEvents(caller, event, callData);
    }
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::SelectFirstParameterNode()
{
  // if we have a parameter node select it
  vtkMRMLTractographyInteractiveSeedingNode *tnode = 0;
  vtkMRMLNode *node = this->GetMRMLScene()->GetNthNodeByClass(0, "vtkMRMLTractographyInteractiveSeedingNode");
  if (node)
    {
    tnode = vtkMRMLTractographyInteractiveSeedingNode::SafeDownCast(node);
    vtkSetAndObserveMRMLNodeMacro(this->TractographyInteractiveSeedingNode, tnode);
    //this->RemoveMRMLNodesObservers();
    //this->AddMRMLNodesObservers();
    // trigger an update to the tracts if seeding is enabled
    // (this method calls remove and add mrml nodes observers)
    this->OnMRMLNodeModified(node);
    }
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::OnMRMLSceneEndImport()
{
  this->SelectFirstParameterNode();
  this->InvokeEvent(vtkMRMLScene::EndImportEvent);
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::OnMRMLSceneEndRestore()
{
  this->SelectFirstParameterNode();
  this->InvokeEvent(vtkMRMLScene::EndRestoreEvent);
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic
::OnMRMLSceneNodeRemoved(vtkMRMLNode* node)
{
  if (node == NULL || !this->IsObservedNode(node))
    {
    return;
    }
  this->OnMRMLNodeModified(node);
}

//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic
::OnMRMLNodeModified(vtkMRMLNode* vtkNotUsed(node))
{
  vtkMRMLTractographyInteractiveSeedingNode* snode = this->TractographyInteractiveSeedingNode;

  if (snode == NULL || snode->GetEnableSeeding() == 0)
    {
    return;
    }

  this->RemoveMRMLNodesObservers();

  this->AddMRMLNodesObservers();

  this->UpdateOnce();
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic
::UpdateOnce()
{
  vtkMRMLTractographyInteractiveSeedingNode* snode = this->TractographyInteractiveSeedingNode;

  if (snode == NULL)
    {
    return;
    }

  vtkMRMLDiffusionTensorVolumeNode *volumeNode =
    vtkMRMLDiffusionTensorVolumeNode::SafeDownCast(
      this->GetMRMLScene()->GetNodeByID(snode->GetInputVolumeRef()));
  vtkMRMLNode *seedingNode = this->GetMRMLScene()->GetNodeByID(snode->GetInputFiducialRef());
  vtkMRMLFiberBundleNode *fiberNode =
    vtkMRMLFiberBundleNode::SafeDownCast(
      this->GetMRMLScene()->GetNodeByID(snode->GetOutputFiberRef()));

  if(volumeNode == NULL || seedingNode == NULL || fiberNode == NULL)
    {
    return;
    }

  this->CreateTracts(snode, volumeNode, seedingNode, fiberNode,
                     snode->GetThresholdMode(),
                     snode->GetStoppingValue(),
                     snode->GetStoppingCurvature(),
                     snode->GetIntegrationStep(),
                     snode->GetMinimumPathLength(),
                     snode->GetSeedingRegionSize(),
                     snode->GetSeedingRegionStep(),
                     snode->GetMaxNumberOfSeeds(),
                     snode->GetSeedSelectedFiducials(),
                     snode->GetDisplayMode()
                     );

  // Make sure output fiber node is under the DTI volume in subject hierarchy
  vtkMRMLSubjectHierarchyNode* shNode =
    vtkMRMLSubjectHierarchyNode::GetSubjectHierarchyNode(this->GetMRMLScene());
  if (shNode)
    {
    shNode->CreateItem(shNode->GetItemByDataNode(volumeNode), fiberNode);
    }
}

//----------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::RegisterNodes()
{
  vtkMRMLScene* scene = this->GetMRMLScene();
  if (!scene)
    {
    return;
    }
  scene->RegisterNodeClass(vtkSmartPointer<vtkMRMLTractographyInteractiveSeedingNode>::New());
}

//---------------------------------------------------------------------------
// Set the internal mrml scene and observe events on it
//---------------------------------------------------------------------------
void vtkSlicerTractographyInteractiveSeedingLogic::SetMRMLSceneInternal(vtkMRMLScene * newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  events->InsertNextValue(vtkMRMLScene::EndImportEvent);
  events->InsertNextValue(vtkMRMLScene::EndRestoreEvent);
  this->SetAndObserveMRMLSceneEventsInternal(newScene, events.GetPointer());
}

//----------------------------------------------------------------------------
int vtkSlicerTractographyInteractiveSeedingLogic::CreateTractsForLabelMap(
                                                            vtkSeedTracts *seed,
                                                            vtkMRMLDiffusionTensorVolumeNode *volumeNode,
                                                            vtkMRMLScalarVolumeNode *seedingNode,
                                                            int ROIlabel,
                                                            int useIndexSpace,
                                                            double seedSpacing,
                                                            int randomGrid,
                                                            double linearMeasureStart,
                                                            int thresholdMode,
                                                            double stoppingValue,
                                                            double stoppingCurvature,
                                                            double integrationStepLength,
                                                            double minPathLength,
                                                            double maxPathLength)
{
  if( volumeNode->GetImageData()->GetPointData()->GetTensors() == NULL )
    {
    vtkErrorMacro("No tensor data");
    return 0;
    }

  if( seedingNode->GetImageData()->GetPointData()->GetScalars() == NULL )
    {
    vtkErrorMacro("No label data");
    return 0;
    }

  vtkSmartPointer<vtkAlgorithmOutput> ROIConnection;
  vtkNew<vtkImageCast> imageCast;
  vtkNew<vtkDiffusionTensorMathematics> math;
  vtkNew<vtkImageThreshold> th;
  vtkNew<vtkMatrix4x4> ROIRASToIJK;

  // 1. Set Input

  if (seedingNode->GetImageData())
    {
    // cast roi to short data type
    imageCast->SetOutputScalarTypeToShort();
    imageCast->SetInputConnection(seedingNode->GetImageDataConnection() );

    //Do scale IJK
    double sp[3];
    seedingNode->GetSpacing(sp);
    vtkImageChangeInformation *ici = vtkImageChangeInformation::New();
    ici->SetOutputSpacing(sp);
    imageCast->Update();
    ici->SetInputConnection(imageCast->GetOutputPort());
    ici->Update();
    ROIConnection = ici->GetOutputPort();

    // Set up the matrix that will take points in ROI
    // to RAS space.  Code assumes this is world space
    // since  we have no access to external transforms.
    // This will only work if no transform is applied to
    // ROI and tensor volumes.
    //
    seedingNode->GetRASToIJKMatrix(ROIRASToIJK.GetPointer()) ;
    }
  else
    {
    math->SetInputConnection(volumeNode->GetImageDataConnection());
    if ( thresholdMode ==
         vtkMRMLTractographyInteractiveSeedingNode::LinearMeasure )
      {
      math->SetOperationToLinearMeasure();
      }
    else
      {
      math->SetOperationToFractionalAnisotropy();
      }

    th->SetInputConnection(math->GetOutputPort());
    th->ThresholdBetween(linearMeasureStart,1);
    th->SetInValue(ROIlabel);
    th->SetOutValue(0);
    th->ReplaceInOn();
    th->ReplaceOutOn();
    th->SetOutputScalarTypeToShort();
    th->Update();
    ROIConnection = th->GetOutputPort();

    // Set up the matrix that will take points in ROI
    // to RAS space.  Code assumes this is world space
    // since  we have no access to external transforms.
    // This will only work if no transform is applied to
    // ROI and tensor volumes.
    volumeNode->GetRASToIJKMatrix(ROIRASToIJK.GetPointer()) ;
  }

  // 2. Set Up matrices
  vtkNew<vtkMatrix4x4> tensorRASToIJK;

  volumeNode->GetRASToIJKMatrix(tensorRASToIJK.GetPointer());

  // VTK seeding is in ijk space with voxel scale included.
  // Calculate the matrix that goes from tensor "scaled IJK",
  // the array with voxels that know their size (what vtk sees for tract seeding)
  // to our RAS.
  double sp[3];
  volumeNode->GetSpacing(sp);
  vtkNew<vtkTransform> trans;
  trans->Identity();
  trans->PreMultiply();
  trans->SetMatrix(tensorRASToIJK.GetPointer());
  // Trans from IJK to RAS
  trans->Inverse();
  // Take into account spacing (remove from matrix) to compute Scaled IJK to RAS matrix
  trans->Scale(1 / sp[0], 1 / sp[1], 1 / sp[2]);
  trans->Inverse();

  // Set Transformation to seeding class
  seed->SetWorldToTensorScaledIJK(trans.GetPointer());

  // Rotation part of matrix is only thing tensor is transformed by.
  // This is to transform output tensors into RAS space.
  // Tensors are output along the fibers.
  // This matrix is not used for calculating tractography.
  // The following should be replaced with finite strain method
  // rather than assuming rotation part of the matrix according to
  // slicer convention.
  vtkNew<vtkMatrix4x4> tensorRASToIJKRotation;
  tensorRASToIJKRotation->DeepCopy(tensorRASToIJK.GetPointer());
  // Set Translation to zero
  for( int i = 0; i < 3; i++ )
    {
    tensorRASToIJKRotation->SetElement(i, 3, 0);
    }
  // Remove scaling in rasToIjk to make a real rotation matrix
  double col[3];
  for( int jjj = 0; jjj < 3; jjj++ )
    {
    for( int iii = 0; iii < 3; iii++ )
      {
      col[iii] = tensorRASToIJKRotation->GetElement(iii, jjj);
      }
    vtkMath::Normalize(col);
    for( int iii = 0; iii < 3; iii++ )
      {
      tensorRASToIJKRotation->SetElement(iii, jjj, col[iii]);
      }
    }
  tensorRASToIJKRotation->Invert();
  seed->SetTensorRotationMatrix(tensorRASToIJKRotation.GetPointer());

  // vtkNew<vtkTeemNRRDWriter> iwriter;

  // 3. Set up ROI (not based on Cl mask), from input now

  // Create Cl mask
  /**
  iwriter->SetInput(imageCast->GetOutput());
  iwriter->SetFileName("C:/Temp/cast.nhdr");
  iwriter->Write();

  vtkNew<vtkDiffusionTensorMathematicsSimple> math;
  math->SetInputData(0, volumeNode->GetImageData());
  // math->SetInputData(1, volumeNode->GetImageData());
  math->SetScalarMask(imageCast->GetOutput());
  math->MaskWithScalarsOn();
  math->SetMaskLabelValue(ROIlabel);
  math->SetOperationToLinearMeasure();
  math->Update();

  iwriter->SetInput(math->GetOutput());
  iwriter->SetFileName("C:/Temp/math.nhdr");
  iwriter->Write();

  vtkNew<vtkImageThreshold> th;
  th->SetInput(math->GetOutput());
  th->ThresholdBetween(linearMeasureStart,1);
  th->SetInValue(1);
  th->SetOutValue(0);
  th->ReplaceInOn();
  th->ReplaceOutOn();
  th->SetOutputScalarTypeToShort();
  th->Update();

  iwriter->SetInput(th->GetOutput());
  iwriter->SetFileName("C:/Temp/th.nhdr");
  iwriter->Write();
  **/

  vtkNew<vtkTransform> trans2;
  trans2->Identity();
  trans2->PreMultiply();

  // no longer assume this ROI is in tensor space
  // trans2->SetMatrix(tensorRASToIJK.GetPointer());
  trans2->SetMatrix(ROIRASToIJK.GetPointer());
  trans2->Inverse();
  seed->SetROIToWorld(trans2.GetPointer());

  // PENDING: Do merging with input ROI

  seed->SetInputROIConnection(ROIConnection);
  seed->SetInputROIValue(ROIlabel);
  seed->UseStartingThresholdOn();
  seed->SetStartingThreshold(linearMeasureStart);

  // 4. Set Tractography specific parameters

  if( useIndexSpace )
    {
    seed->SetIsotropicSeeding(0);
    }
  else
    {
    seed->SetIsotropicSeeding(1);
    }

  seed->SetRandomGrid(randomGrid);

  seed->SetIsotropicSeedingResolution(seedSpacing);
  seed->SetMinimumPathLength(minPathLength);
  seed->UseVtkHyperStreamlinePoints();
  vtkNew<vtkHyperStreamlineDTMRI> streamer;
  seed->SetVtkHyperStreamlinePointsSettings(streamer.GetPointer());

  setStreamerThresholdMode(streamer.GetPointer(), thresholdMode);

  streamer->SetStoppingThreshold(stoppingValue);
  streamer->SetMaximumPropagationDistance(maxPathLength);
  streamer->SetRadiusOfCurvature(stoppingCurvature);
  streamer->SetIntegrationStepLength(integrationStepLength);

  // Temp fix to provide a scalar
  // seed->GetInputTensorField()->GetPointData()->SetScalars(math->GetOutput()->GetPointData()->GetScalars());

  // 5. Run the thing
  seed->SeedStreamlinesInROI();

  return 1;
}
