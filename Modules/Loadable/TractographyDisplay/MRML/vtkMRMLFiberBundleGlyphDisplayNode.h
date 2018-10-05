/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLFiberBundleGlyphDisplayNode.h,v $
  Date:      $Date: 2006/03/19 17:12:28 $
  Version:   $Revision: 1.6 $

  =========================================================================auto=*/
///  vtkMRMLFiberBundleGlyphDisplayNode - MRML node to represent display properties for tractography.
///
/// vtkMRMLFiberBundleGlyphDisplayNode nodes store display properties of trajectories
/// from tractography in diffusion MRI data, including color type (by bundle, by fiber,
/// or by scalar invariants), display on/off for tensor glyphs and display of
/// trajectory as a line or tube.
//

#ifndef __vtkMRMLFiberBundleGlyphDisplayNode_h
#define __vtkMRMLFiberBundleGlyphDisplayNode_h

#include "vtkMRMLFiberBundleDisplayNode.h"

class vtkDiffusionTensorGlyph;
class vtkCleanPolyData;
class vtkPolyData;

class VTK_SLICER_TRACTOGRAPHYDISPLAY_MODULE_MRML_EXPORT vtkMRMLFiberBundleGlyphDisplayNode : public vtkMRMLFiberBundleDisplayNode
{
 public:
  static vtkMRMLFiberBundleGlyphDisplayNode *New (  );
  vtkTypeMacro ( vtkMRMLFiberBundleGlyphDisplayNode,vtkMRMLFiberBundleDisplayNode );
  void PrintSelf ( ostream& os, vtkIndent indent ) VTK_OVERRIDE;

  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance (  ) VTK_OVERRIDE;

  ///
  /// Read node attributes from XML (MRML) file
  virtual void ReadXMLAttributes ( const char** atts ) VTK_OVERRIDE;

  ///
  /// Write this node's information to a MRML file in XML format.
  virtual void WriteXML ( ostream& of, int indent ) VTK_OVERRIDE;


  ///
  /// Copy the node's attributes to this object
  virtual void Copy ( vtkMRMLNode *node ) VTK_OVERRIDE;

  ///
  /// Get node XML tag name (like Volume, UnstructuredGrid)
  virtual const char* GetNodeTagName ( )  VTK_OVERRIDE {return "FiberBundleGlyphDisplayNode";};

  ///
  /// Update the pipeline based on this node attributes
  virtual void UpdateAssignedAttribute() VTK_OVERRIDE;

  //--------------------------------------------------------------------------
  /// Display Information: Geometry to display (not mutually exclusive)
  //--------------------------------------------------------------------------

  ///
  /// Turn on/off visibility of glyphs (tensors) along fibers.
  vtkSetMacro ( TwoDimensionalVisibility , int );
  vtkGetMacro ( TwoDimensionalVisibility , int );
  vtkBooleanMacro ( TwoDimensionalVisibility , int );

 protected:
  vtkMRMLFiberBundleGlyphDisplayNode ( );
  ~vtkMRMLFiberBundleGlyphDisplayNode ( );
  vtkMRMLFiberBundleGlyphDisplayNode ( const vtkMRMLFiberBundleGlyphDisplayNode& );
  void operator= ( const vtkMRMLFiberBundleGlyphDisplayNode& );

  /// Gets result in glyph PolyData
  virtual vtkAlgorithmOutput* GetOutputMeshConnection() VTK_OVERRIDE;

  /// Enumerated

  int TwoDimensionalVisibility;


  /// dispaly pipeline
  vtkDiffusionTensorGlyph *DiffusionTensorGlyphFilter;
};

#endif
