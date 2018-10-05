/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkPreciseHyperStreamlinePoints.h,v $
  Date:      $Date: 2006/01/06 17:58:06 $
  Version:   $Revision: 1.3 $

=========================================================================auto=*/

#ifndef __vtkPreciseHyperStreamlinePoints_h
#define __vtkPreciseHyperStreamlinePoints_h

#include <vtkVersion.h>

#include "vtkDMRIConfigure.h"

#include "vtkPreciseHyperStreamline.h"
#include "vtkPoints.h"

class vtkDMRI_EXPORT vtkPreciseHyperStreamlinePoints : public vtkPreciseHyperStreamline
{
public:
  static vtkPreciseHyperStreamlinePoints *New();
  vtkTypeMacro(vtkPreciseHyperStreamlinePoints,vtkPolyDataAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent) VTK_OVERRIDE;

  vtkGetObjectMacro(PreciseHyperStreamline0,vtkPoints);
  vtkGetObjectMacro(PreciseHyperStreamline1,vtkPoints);

protected:
  vtkPreciseHyperStreamlinePoints();
  ~vtkPreciseHyperStreamlinePoints();

  virtual int RequestData(vtkInformation *, vtkInformationVector **, vtkInformationVector *) VTK_OVERRIDE;

  /// convenient pointers to PreciseHyperStreamline1 and PreciseHyperStreamline2
  vtkPoints *PreciseHyperStreamlines[2];

  /// points calculated for first hyperstreamline
  vtkPoints *PreciseHyperStreamline0;
  /// points calculated for optional second hyperstreamline
  vtkPoints *PreciseHyperStreamline1;

private:
  vtkPreciseHyperStreamlinePoints(const vtkPreciseHyperStreamlinePoints&);  /// Not implemented.
  void operator=(const vtkPreciseHyperStreamlinePoints&);  /// Not implemented.
};

#endif
