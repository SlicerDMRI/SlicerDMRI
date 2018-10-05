/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH)
  All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer

=========================================================================auto=*/

// MRML includes
#include "vtkMRMLCoreTestingMacros.h"
#include "vtkMRMLFiberBundleDisplayNode.h"

// VTK includes
#include <vtkObjectFactory.h>

//---------------------------------------------------------------------------
class vtkMRMLFiberBundleDisplayNodeTestHelper1 : public vtkMRMLFiberBundleDisplayNode
{
public:
  // Provide a concrete New.
  static vtkMRMLFiberBundleDisplayNodeTestHelper1 *New();

  vtkTypeMacro(vtkMRMLFiberBundleDisplayNodeTestHelper1,vtkMRMLFiberBundleDisplayNode);

  virtual vtkMRMLNode* CreateNodeInstance() VTK_OVERRIDE
    {
    return vtkMRMLFiberBundleDisplayNodeTestHelper1::New();
    }

  const char * GetTypeAsString()
    {
    return "vtkMRMLFiberBundleDisplayNodeTestHelper1";
    }

  int ReadFile()
    {
    std::cout << "vtkMRMLFiberBundleDisplayNodeTestHelper1 pretending to read a file " << std::endl;
    return EXIT_SUCCESS;
    }

  virtual const char* GetNodeTagName() VTK_OVERRIDE
    {
    return "Testing is good";
    }
};
vtkStandardNewMacro(vtkMRMLFiberBundleDisplayNodeTestHelper1);

//---------------------------------------------------------------------------
int vtkMRMLFiberBundleDisplayNodeTest1(int , char * [] )
{
  vtkNew<vtkMRMLFiberBundleDisplayNodeTestHelper1> node1;
  EXERCISE_ALL_BASIC_MRML_METHODS(node1.GetPointer());
  return EXIT_SUCCESS;
}
