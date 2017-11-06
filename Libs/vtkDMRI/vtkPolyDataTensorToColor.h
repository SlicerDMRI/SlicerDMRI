/*=========================================================================

  Program:   Visualization Toolkit
  Module:    $RCSfile: vtkPolyDataTensorToColor.h,v $

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/

#ifndef __vtkPolyDataTensorToColor_h
#define __vtkPolyDataTensorToColor_h

#include "vtkPolyDataAlgorithm.h"
#include "vtkDMRIConfigure.h"

#include "vtkTensorGlyph.h"

/// \brief Calculates scalar values from vtkPolyData tensors.

class vtkDMRI_EXPORT vtkPolyDataTensorToColor : public vtkPolyDataAlgorithm
{
public:
  static vtkPolyDataTensorToColor *New();
  vtkTypeMacro(vtkPolyDataTensorToColor,vtkPolyDataAlgorithm);
  void PrintSelf(ostream& os, vtkIndent indent);

  vtkSetClampMacro(ColorMode, int, vtkTensorGlyph::COLOR_BY_SCALARS, vtkTensorGlyph::COLOR_BY_EIGENVALUES);
  vtkGetMacro(ColorMode, int);
  void SetColorModeToScalars()
    {this->SetColorMode(vtkTensorGlyph::COLOR_BY_SCALARS);};
  void SetColorModeToEigenvalues()
    {this->SetColorMode(vtkTensorGlyph::COLOR_BY_EIGENVALUES);};

  ///
  /// Turn on/off extraction of eigenvalues from tensor.
  vtkSetMacro(ExtractEigenvalues,int);
  vtkBooleanMacro(ExtractEigenvalues,int);
  vtkGetMacro(ExtractEigenvalues,int);

  ///
  /// Turn on/off extraction of scalars for color.
  vtkSetMacro(ExtractScalar,int);
  vtkBooleanMacro(ExtractScalar,int);
  vtkGetMacro(ExtractScalar,int);

  /// TO DO: make more of these

  ///
  /// Output one component scalars according to scalar invariants
  void ColorGlyphsByLinearMeasure();
  void ColorGlyphsBySphericalMeasure();
  void ColorGlyphsByPlanarMeasure();
  void ColorGlyphsByParallelDiffusivity();
  void ColorGlyphsByPerpendicularDiffusivity();
  void ColorGlyphsByMaxEigenvalue();
  void ColorGlyphsByMidEigenvalue();
  void ColorGlyphsByMinEigenvalue();
  void ColorGlyphsByRelativeAnisotropy();
  void ColorGlyphsByFractionalAnisotropy();
  void ColorGlyphsByTrace();
  void ColorGlyphsByOrientation();

protected:
  vtkPolyDataTensorToColor();
  ~vtkPolyDataTensorToColor() {};

  /// Usual data generation method
  virtual int RequestData(vtkInformation *, vtkInformationVector **, vtkInformationVector *);

  virtual int FillInputPortInformation(int port, vtkInformation *info);

  void ColorGlyphsBy(int measure);
  int ColorMode; /// The coloring mode to use for the glyphs.
  int ExtractEigenvalues; /// Boolean controls eigenfunction extraction

  int ExtractScalar;

  int ScalarInvariant;  /// which function of eigenvalues to use for coloring

private:
  vtkPolyDataTensorToColor(const vtkPolyDataTensorToColor&);  /// Not implemented.
  void operator=(const vtkPolyDataTensorToColor&);  /// Not implemented.
};

#endif
