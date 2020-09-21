/*=auto=========================================================================

  Portions (c) Copyright 2005 Brigham and Women's Hospital (BWH) All Rights Reserved.

  See COPYRIGHT.txt
  or http://www.slicer.org/copyright/copyright.txt for details.

  Program:   3D Slicer
  Module:    $RCSfile: vtkMRMLFiberBundleNode.h,v $
  Date:      $Date: 2006/03/19 17:12:28 $
  Version:   $Revision: 1.6 $

=========================================================================auto=*/
///  vtkMRMLFiberBundleNode - MRML node to represent a fiber bundle from tractography in DTI data.
///
/// FiberBundle nodes contain trajectories ("fibers") from tractography, internally represented as vtkPolyData.
/// A FiberBundle node contains many fibers and forms the smallest logical unit of tractography
/// that MRML will manage/read/write. Each fiber has accompanying tensor data.
/// Visualization parameters for these nodes are controlled by the vtkMRMLFiberBundleDisplayNode class.
//

#ifndef __vtkMRMLFiberBundleNode_h
#define __vtkMRMLFiberBundleNode_h

#include "vtkMRMLModelNode.h"


// Tractography includes
#include "vtkSlicerTractographyDisplayModuleMRMLExport.h"

class vtkMRMLFiberBundleDisplayNode;
class vtkExtractSelectedPolyDataIds;
class vtkMRMLAnnotationNode;
class vtkIdTypeArray;
class vtkExtractPolyDataGeometry;
class vtkPlanes;
class vtMRMLModelDisplayNode;
class vtkPassThrough;

class VTK_SLICER_TRACTOGRAPHYDISPLAY_MODULE_MRML_EXPORT vtkMRMLFiberBundleNode : public vtkMRMLModelNode
{
public:
  static vtkMRMLFiberBundleNode *New();
  vtkTypeMacro(vtkMRMLFiberBundleNode,vtkMRMLModelNode);
  //vtkTypeMacro(vtkMRMLFiberBundleNode,vtkMRMLTransformableNode);
  void PrintSelf(ostream& os, vtkIndent indent) override;

  //--------------------------------------------------------------------------
  /// MRMLNode methods
  //--------------------------------------------------------------------------

  virtual vtkMRMLNode* CreateNodeInstance() override;

  ///
  /// Read node attributes from XML (MRML) file
  virtual void ReadXMLAttributes ( const char** atts ) override;

  ///
  /// Write this node's information to a MRML file in XML format.
  virtual void WriteXML ( ostream& of, int indent ) override;


  ///
  /// Copy the node's attributes to this object
  virtual void Copy ( vtkMRMLNode *node ) override;

  ///
  /// alternative method to propagate events generated in Display nodes
  virtual void ProcessMRMLEvents ( vtkObject * /*caller*/,
                                   unsigned long /*event*/,
                                   void * /*callData*/ ) override;

  ///
  /// Updates this node if it depends on other nodes
  /// when the node is deleted in the scene
  virtual void UpdateReferences() override;

  ///
  /// Update the stored reference to another node in the scene
  virtual void UpdateReferenceID(const char *oldID, const char *newID) override;

  ///
  /// Get node XML tag name (like Volume, Model)
  virtual const char* GetNodeTagName() override {return "FiberBundle";};

  /// Get the subsampling ratio for the polydata
  vtkGetMacro(SubsamplingRatio, float);

  /// Set the subsampling ratio for the polydata
  //
  virtual void SetSubsamplingRatio(float);
  virtual float GetSubsamplingRatioMinValue()
    {
    return 0.;
    }
  virtual float GetSubsamplingRatioMaxValue()
    {
    return 1.;
    }

  //vtkSetClampMacro(SubsamplingRatio, float, 0, 1);

  ///
  /// Get annotation MRML object.
  vtkMRMLAnnotationNode* GetAnnotationNode ( );


  ///
  /// Set the ID annotation node for interactive selection.
  void SetAndObserveAnnotationNodeID ( const char *ID );

  ///
  /// Get ID of diffusion tensor display MRML object for fiber glyph.
  vtkGetStringMacro(AnnotationNodeID);

  //--------------------------------------------------------------------------
  /// Interactive Selection Support
  //--------------------------------------------------------------------------

  ///
  /// Enable or disable the selection with an annotation node
  virtual void SetSelectWithAnnotation(bool);
  vtkGetMacro(SelectWithAnnotation, bool);

  enum SelectionModeEnum
  {
    NoSelection,
    PositiveSelection,
    NegativeSelection
  };


  ///
  /// Set the mode (positive or negative) of the selection with the annotation node
  vtkGetMacro(AnnotationSelectionMode, SelectionModeEnum);
  virtual void SetAnnotationSelectionMode(SelectionModeEnum);

  ///
  /// Reimplemented from internal reasons
  virtual void SetMeshConnection(vtkAlgorithmOutput* inputPort) override;

  ///
  /// Gets the subsampled PolyData converted from the real data in the node
  virtual vtkPointSet* GetFilteredPolyData();
  virtual vtkAlgorithmOutput* GetFilteredMeshConnection();
  void SetMeshToDisplayNode(vtkMRMLModelDisplayNode*) override;

  ///
  /// get associated line display node or NULL if not set
  vtkMRMLFiberBundleDisplayNode* GetLineDisplayNode();

  ///
  /// get associated tube display node or NULL if not set
  vtkMRMLFiberBundleDisplayNode* GetTubeDisplayNode();

  ///
  /// get associated glyph display node or NULL if not set
  vtkMRMLFiberBundleDisplayNode* GetGlyphDisplayNode();

  ///
  /// Create and return default storage node or NULL if does not have one
  virtual vtkMRMLStorageNode* CreateDefaultStorageNode() override;

  std::string GetDefaultStorageNodeClassName(const char* filename /* =nullptr */) override;

  /// Create default display nodes
  virtual void CreateDefaultDisplayNodes() override;

   // Description:
  // Get the maximum number of fibers to show by default when a new fiber bundle node is set
  vtkGetMacro ( MaxNumberOfFibersToShowByDefault, vtkIdType );

  // Description:
  // Set the maximum number of fibers to show by default when a new fiber bundle node is set
  vtkSetMacro ( MaxNumberOfFibersToShowByDefault, vtkIdType );

  // Description:
  // Get original cell id in the input polydata
  vtkIdType GetUnShuffledFiberID(vtkIdType shuffledIndex)
  {
    return this->ShuffledIds->GetValue(shuffledIndex);
  }

  // Description:
  // Enable, Disable shuffle of IDs
  vtkGetMacro(EnableShuffleIDs, bool);
  vtkSetMacro(EnableShuffleIDs, bool);

protected:
  vtkMRMLFiberBundleNode();
  ~vtkMRMLFiberBundleNode();
  vtkMRMLFiberBundleNode(const vtkMRMLFiberBundleNode&);
  void operator=(const vtkMRMLFiberBundleNode&);

  // Description:
  // Maximum number of fibers to show per bundle when it is loaded.
  static vtkIdType MaxNumberOfFibersToShowByDefault;
  vtkIdTypeArray* ShuffledIds;

  float SubsamplingRatio;


  /// ALL MRML nodes
  bool EnableShuffleIDs;
  bool SelectWithAnnotation;
  SelectionModeEnum AnnotationSelectionMode;

  vtkMRMLAnnotationNode *AnnotationNode;
  char *AnnotationNodeID;

  virtual void SetAnnotationNodeID(const char* id);

private:
  // Pipeline filter objects
  vtkExtractPolyDataGeometry* ExtractFromROI;
  vtkExtractSelectedPolyDataIds* ExtractSubsample;
  vtkPlanes *Planes;
  vtkPassThrough* LocalPassThrough;

  // Internal methods
  void UpdateSubsampling();
  void UpdateROISelection();

  void PrepareROISelection();
  void PrepareSubsampling();
};

#endif
