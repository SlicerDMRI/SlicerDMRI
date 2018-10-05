/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkHyperStreamlineDTMRI.h,v $
  Date:      $Date: 2007/02/23 19:06:47 $
  Version:   $Revision: 1.13 $

=========================================================================auto=*/

#ifndef __vtkHyperStreamlineDTMRI_h
#define __vtkHyperStreamlineDTMRI_h

#include "vtkDMRIConfigure.h"
#include "vtkHyperStreamline.h"
#include "vtkDiffusionTensorMathematics.h" /// for VTK_TENS_FRACTIONAL_ANISOTROPY
#include "vtkTractographyPointAndArray.h"

/// \brief Generate hyperstreamline in arbitrary dataset.
///
/// vtkHyperStreamlineDTMRI is a filter that integrates through a tensor field to
/// generate a hyperstreamline. The integration is along the maximum eigenvector
/// and the cross section of the hyperstreamline is defined by the two other
/// eigenvectors. Thus the shape of the hyperstreamline is "tube-like", with
/// the cross section being elliptical. Hyperstreamlines are used to visualize
/// tensor fields.
///
/// The starting point of a hyperstreamline can be defined in one of two ways.
/// First, you may specify an initial position. This is a x-y-z global
/// coordinate. The second option is to specify a starting location. This is
/// cellId, subId, and  cell parametric coordinates.
///
/// The integration of the hyperstreamline occurs through the major eigenvector
/// field. IntegrationStepLength controls the step length within each cell
/// (this is in mm). The length of the
/// hyperstreamline is controlled by MaximumPropagationDistance. This parameter
/// is the length of the hyperstreamline in units of distance.
///
/// \sa vtkTensorGlyph
/// \sa vtkStreamer

class vtkDMRI_EXPORT vtkHyperStreamlineDTMRI : public vtkHyperStreamline
{
public:
  vtkTypeMacro(vtkHyperStreamlineDTMRI,vtkHyperStreamline);
  void PrintSelf(ostream& os, vtkIndent indent) VTK_OVERRIDE;

  ///
  /// Construct object with initial starting position (0,0,0); integration
  /// step length 0.5; both directions of integration; terminal
  /// eigenvalue 0.0
  static vtkHyperStreamlineDTMRI *New();

  ///
  /// If radius of curvature becomes smaller than this number, tracking stops.
  /// This is how tight of a turn is allowed.
  /// The units are degrees per mm. (Actually per units of measurement
  /// in your data).
  vtkGetMacro(RadiusOfCurvature, double);
  vtkSetMacro(RadiusOfCurvature, double);

  ///
  /// This is in mm, unlike superclass value which is a fraction of a cell.
  /// Implement here instead of vtkSetMacro to use VTK_OVERRIDE
  void SetIntegrationStepLength(double length) VTK_OVERRIDE {
    if (this->IntegrationStepLength != length) {
      this->IntegrationStepLength = length;
      this->Modified();
    }
  }

  ///
  /// Type of anisotropy used to stop tractography.
  vtkGetMacro(ThresholdMode,int);
  vtkSetMacro(ThresholdMode,int);
  void SetThresholdModeToFractionalAnisotropy()
    {this->SetThresholdMode(vtkDiffusionTensorMathematics::VTK_TENS_FRACTIONAL_ANISOTROPY);};
  void SetThresholdModeToLinearMeasure()
    {this->SetThresholdMode(vtkDiffusionTensorMathematics::VTK_TENS_LINEAR_MEASURE);};
  void SetThresholdModeToPlanarMeasure()
    {this->SetThresholdMode(vtkDiffusionTensorMathematics::VTK_TENS_PLANAR_MEASURE);};
  void SetThresholdModeToSphericalMeasure()
    {this->SetThresholdMode(vtkDiffusionTensorMathematics::VTK_TENS_SPHERICAL_MEASURE);};


  /// If ThresholdMode criterion becomes smaller than this number,
  /// tracking stops.
  vtkGetMacro(StoppingThreshold,double);
  vtkSetMacro(StoppingThreshold,double);

  ///
  /// Whether to output the interpolated tensor at each point
  /// of the output streamline
  vtkGetMacro(OutputTensors, int);
  vtkSetMacro(OutputTensors, int);
  vtkBooleanMacro(OutputTensors, int);

  ///
  /// Whether to produce one polyline per integration direction
  /// (so two per seed point), or one polyline per seed point.
  /// Superclass behavior would be two per seed point.
  vtkGetMacro(OneTrajectoryPerSeedPoint, int);
  vtkSetMacro(OneTrajectoryPerSeedPoint, int);
  vtkBooleanMacro(OneTrajectoryPerSeedPoint, int);

protected:
  vtkHyperStreamlineDTMRI();
  ~vtkHyperStreamlineDTMRI();

  /// Integrate data
  virtual int RequestData(vtkInformation *,vtkInformationVector**, vtkInformationVector *) VTK_OVERRIDE;
  void BuildLines(vtkDataSet *input, vtkPolyData *output);
  void BuildLinesForSingleTrajectory(vtkDataSet *input, vtkPolyData *output);
  void BuildLinesForTwoTrajectories(vtkDataSet *input, vtkPolyData *output);

  double RadiusOfCurvature;
  int ThresholdMode;
  double StoppingThreshold;

  int OutputTensors;

  int OneTrajectoryPerSeedPoint;

  vtkTractographyArray *Streamers;

private:
  vtkHyperStreamlineDTMRI(const vtkHyperStreamlineDTMRI&);  /// Not implemented.
  void operator=(const vtkHyperStreamlineDTMRI&);  /// Not implemented.
};

#endif
