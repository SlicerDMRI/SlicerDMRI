/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH)
  All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer

=========================================================================auto=*/

#include <itksys/SystemTools.hxx>
#include <vtkNew.h>

#include "vtkSlicerFiberBundleLogic.h"


int vtkSlicerFiberBundleLogicTest(int argc, char * argv[])
{
  if (argc != 3)
  {
    std::cout << "Missing parameters." << std::endl;
    std::cout << "Usage: vtkSlicerFiberBundleLogicTest inputFileName outputFileName" << std::endl;
    return EXIT_FAILURE;
  }

  const char* inputFileName = argv[1];
  std::string volumeName = itksys::SystemTools::GetFilenameWithoutExtension(inputFileName);

  vtkNew<vtkSlicerFiberBundleLogic> fiberBundleLogic;

  auto fiberBundleNode = fiberBundleLogic->AddFiberBundle(argv[1], volumeName.c_str());
  auto res = fiberBundleLogic->SaveFiberBundle(argv[2], fiberBundleNode);

  // ToDo
  // Print or do sth with res
  return EXIT_SUCCESS;
}
