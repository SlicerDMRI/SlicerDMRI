/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkTensorRotate.h,v $
  Date:      $Date: 2006/06/27 20:53:19 $
  Version:   $Revision: 1.6 $

=========================================================================auto=*/

#ifndef __vtkTensorRotate_h
#define __vtkTensorRotate_h

#include "vtkDMRIConfigure.h"
#include "vtkThreadedImageAlgorithm.h"
#include "vtkTransform.h"
#include <vtkVersion.h>

class vtkFloatArray;
class vtkImageData;

/// \brief  flip Y axis and negate xy and zy terms.
///
/// Make tend estim generated vtk files compatible with slicer
///
/// \warning The filter will always output floating point (loose precision)
/// explicit use of vtkFloatArray.
class vtkDMRI_EXPORT vtkTensorRotate : public vtkThreadedImageAlgorithm
{
public:
  static vtkTensorRotate *New();
  vtkTypeMacro(vtkTensorRotate,vtkThreadedImageAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent) VTK_OVERRIDE;

  /// Set the tensor type for the filter
  void SetTensorTypeToFloat(){this->SetTensorType(VTK_FLOAT);};
  void SetTensorTypeToDouble(){this->SetTensorType(VTK_DOUBLE);};
  vtkSetMacro(TensorType, int);
  vtkGetMacro(TensorType, int);

  /// Set/Get transformation to use to rotate the tensor
  vtkSetObjectMacro(Transform,vtkTransform);
  vtkGetObjectMacro(Transform,vtkTransform);

protected:
  vtkTensorRotate();
  ~vtkTensorRotate();
  vtkTensorRotate(const vtkTensorRotate&);
  void operator=(const vtkTensorRotate&);

  virtual int RequestInformation(vtkInformation *, vtkInformationVector **, vtkInformationVector *) VTK_OVERRIDE;
  void ThreadedExecute(vtkImageData *inData, vtkImageData *outData,
        int extent[6], int id) VTK_OVERRIDE;

  /// This also copies other arrays from point and cell data from input to output.
  virtual void AllocateOutputData(vtkImageData *out, vtkInformation* outInfo, int *uExtent) VTK_OVERRIDE {
      vtkThreadedImageAlgorithm::AllocateOutputData(out, outInfo, uExtent);};
  virtual vtkImageData *AllocateOutputData(vtkDataObject *out, vtkInformation* outInfo) VTK_OVERRIDE;
  void AllocateTensors(vtkImageData *data);

  int TensorType;

  vtkTransform *Transform;

};

#endif
