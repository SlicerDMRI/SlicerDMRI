/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkSlicerFiberBundleLogic.cxx,v $
  Date:      $Date: 2006/01/06 17:56:48 $
  Version:   $Revision: 1.58 $

=========================================================================auto=*/

#include "vtkSlicerFiberBundleLogic.h"

// MRML includes
#include <vtkMRMLConfigure.h>
#ifdef MRML_USE_vtkTeem
#include "vtkMRMLDiffusionTensorDisplayPropertiesNode.h"
#include "vtkMRMLFiberBundleNode.h"
#include "vtkMRMLFiberBundleDisplayNode.h"
#include "vtkMRMLFiberBundleStorageNode.h"
#include "vtkMRMLFiberBundleLineDisplayNode.h"
#include "vtkMRMLFiberBundleTubeDisplayNode.h"
#include "vtkMRMLFiberBundleGlyphDisplayNode.h"
#endif
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkNew.h>
#include <vtkObjectFactory.h>
#include <vtkPolyData.h>
#include <vtkPointData.h>
#include <vtkCellData.h>
#include <vtkDataArray.h>

#include <itksys/SystemTools.hxx>
#include <itksys/Directory.hxx>

vtkStandardNewMacro(vtkSlicerFiberBundleLogic);

//----------------------------------------------------------------------------
vtkSlicerFiberBundleLogic::vtkSlicerFiberBundleLogic()
{
}

//----------------------------------------------------------------------------
vtkSlicerFiberBundleLogic::~vtkSlicerFiberBundleLogic()
{
}

//----------------------------------------------------------------------------
int vtkSlicerFiberBundleLogic::AddFiberBundles (const char* dirname, const char* suffix )
{
  std::string ssuf = suffix;
  itksys::Directory dir;
  dir.Load(dirname);

  int nfiles = dir.GetNumberOfFiles();
  int res = 1;
  for (int i=0; i<nfiles; i++) {
    const char* filename = dir.GetFile(i);
    std::string sname = filename;
    if (!itksys::SystemTools::FileIsDirectory(filename))
      {
      if ( sname.find(ssuf) != std::string::npos )
        {
        std::string fullPath = std::string(dir.GetPath())
            + "/" + filename;
        if (this->AddFiberBundle(fullPath.c_str()) == NULL)
          {
          res = 0;
          }
        }
      }
  }
  return res;
}

//----------------------------------------------------------------------------
int vtkSlicerFiberBundleLogic::AddFiberBundles (const char* dirname, std::vector< std::string > suffix )
{
  itksys::Directory dir;
  dir.Load(dirname);

  int nfiles = dir.GetNumberOfFiles();
  int res = 1;
  for (int i=0; i<nfiles; i++) {
    const char* filename = dir.GetFile(i);
    std::string sname = filename;
    if (!itksys::SystemTools::FileIsDirectory(filename))
      {
      for (unsigned int s=0; s<suffix.size(); s++)
        {
        std::string ssuf = suffix[s];
        if ( sname.find(ssuf) != std::string::npos )
          {
          std::string fullPath = std::string(dir.GetPath())
              + "/" + filename;
          if (this->AddFiberBundle(fullPath.c_str()) == NULL)
            {
            res = 0;
            }
          } //if (sname
        } // for (int s=0;
      }
  }
  return res;
}

//----------------------------------------------------------------------------
vtkMRMLFiberBundleNode* vtkSlicerFiberBundleLogic::AddFiberBundle (const char* filename, const char* volname)
{
  vtkDebugMacro("Adding fiber bundle from filename " << filename);

  vtkSmartPointer<vtkMRMLFiberBundleNode> fiberBundleNode =
    vtkSmartPointer<vtkMRMLFiberBundleNode>::New();
  vtkSmartPointer<vtkMRMLFiberBundleStorageNode> storageNode =
    vtkSmartPointer<vtkMRMLFiberBundleStorageNode>::New();

  storageNode->SetFileName(filename);

  if (storageNode->ReadData(fiberBundleNode) != 0)
    {
    // Compute volume name
    std::string volumeName = volname != nullptr ? volname : itksys::SystemTools::GetFilenameWithoutExtension(filename);
    volumeName = this->GetMRMLScene()->GenerateUniqueName(volumeName);
    fiberBundleNode->SetName(volumeName.c_str());

    fiberBundleNode->SetScene(this->GetMRMLScene());
    fiberBundleNode->SetAndObserveStorageNodeID(storageNode->GetID());
    this->GetMRMLScene()->AddNode(fiberBundleNode);
    fiberBundleNode->CreateDefaultDisplayNodes();
    }
  else
    {
    vtkErrorMacro("Couldn't read file, returning null fiberBundle node: " << filename);
    }

  return fiberBundleNode;
}
//----------------------------------------------------------------------------
int vtkSlicerFiberBundleLogic::SaveFiberBundle (const char* filename, vtkMRMLFiberBundleNode *fiberBundleNode)
{
   if (fiberBundleNode == NULL || filename == NULL)
    {
    return 0;
    }

  vtkMRMLFiberBundleStorageNode *storageNode = NULL;
  vtkMRMLStorageNode *snode = fiberBundleNode->GetStorageNode();
  if (snode != NULL)
    {
    storageNode = vtkMRMLFiberBundleStorageNode::SafeDownCast(snode);
    }
  if (storageNode == NULL)
    {
    storageNode = vtkMRMLFiberBundleStorageNode::New();
    storageNode->SetScene(this->GetMRMLScene());
    this->GetMRMLScene()->AddNode(storageNode);
    fiberBundleNode->SetAndObserveStorageNodeID(storageNode->GetID());
    storageNode->Delete();
    }

  storageNode->SetFileName(filename);

  int res = storageNode->WriteData(fiberBundleNode);

  return res;
}

//----------------------------------------------------------------------------
void vtkSlicerFiberBundleLogic::PrintSelf(ostream& os, vtkIndent indent)
{
  this->vtkObject::PrintSelf(os, indent);

  os << indent << "vtkSlicerFiberBundleLogic:             " << this->GetClassName() << "\n";
}

//---------------------------------------------------------------------------
void vtkSlicerFiberBundleLogic::SetMRMLSceneInternal(vtkMRMLScene* newScene)
{
  vtkNew<vtkIntArray> events;
  events->InsertNextValue(vtkMRMLScene::NodeAddedEvent);
  events->InsertNextValue(vtkMRMLScene::NodeRemovedEvent);
  this->SetAndObserveMRMLSceneEvents(newScene, events.GetPointer());
}

//-----------------------------------------------------------------------------
void vtkSlicerFiberBundleLogic::RegisterNodes()
{
  if(!this->GetMRMLScene())
    {
    return;
    }
#ifdef MRML_USE_vtkTeem
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleLineDisplayNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleTubeDisplayNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleGlyphDisplayNode>().GetPointer());
  this->GetMRMLScene()->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleStorageNode>().GetPointer());
#endif
}

//---------------------------------------------------------------------------
void vtkSlicerFiberBundleLogic::OnMRMLSceneNodeAdded(vtkMRMLNode* node)
{
  if ((!node) || (!node->IsA("vtkMRMLFiberBundleNode")))
    {
    return;
    }
  if (this->GetMRMLScene() &&
      (this->GetMRMLScene()->IsImporting() ||
       this->GetMRMLScene()->IsRestoring() ||
       this->GetMRMLScene()->IsBatchProcessing()))
    {
    return;
    }

  vtkMRMLFiberBundleNode *fbNode = vtkMRMLFiberBundleNode::SafeDownCast(node);
  if (!fbNode)
    {
    return;
    }
  if (fbNode->GetDisplayNode() == NULL)
    {
    fbNode->CreateDefaultDisplayNodes();
    }
}
