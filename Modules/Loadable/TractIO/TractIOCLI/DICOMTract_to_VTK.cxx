/*=========================================================================

  Program:   Realign Volumes
  Module:    $HeadURL$
  Language:  C++
  Date:      $Date$
  Version:   $Revision$

  Copyright (c) Brigham and Women's Hospital (BWH) All Rights Reserved.

  See License.txt or http://www.slicer.org/copyright/copyright.txt for details.

==========================================================================*/
#include "vtkPluginFilterWatcher.h"

// MRML includes
#include <vtkMRMLLinearTransformNode.h>
#include <vtkMRMLScene.h>

// VTK includes
#include <vtkMath.h>
#include <vtkNew.h>
#include <vtkPolyData.h>
#include <vtkXMLPolyDataWriter.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>

// DCMTK includes
#include "dcmtk/dcmtract/trctrack.h"
#include "dcmtk/dcmtract/trctrackset.h"
#include "dcmtk/dcmtract/trctractographyresults.h"

#ifndef NDEBUG
  #define DBGOUT std::cout
#else
  #define DBGOUT if(false) std::cout
#endif

// SlicerSEM includes
#ifdef HAVE_SSTREAM
#undef HAVE_SSTREAM // no guards in dcmtk or SEM...
#endif
#include "DICOMTract_to_VTKCLP.h"


#define vtkSP vtkSmartPointer

// Use an anonymous namespace to keep class types and function names
// from colliding when module is used as shared object module.  Every
// thing should be in an anonymous namespace except for the module
// entry point, e.g. main()
//
namespace
{

} // end of anonymous namespace

std::vector<vtkSmartPointer< vtkPolyData> > extract_tracks(TrcTractographyResults*);
vtkSmartPointer<vtkPolyData> trackset_to_vtk(TrcTrackSet*);

//-----------------------------------------------------------------------------
int main(int argc, char * argv[])
{
  PARSE_ARGS;
  // defines:
  //   std::string input_track_dicom
  //   std::string output_vtk

  OFCondition result;
  TrcTractographyResults *track_dataset = NULL;
  std::vector< vtkSmartPointer<vtkPolyData> > pdtracks;

  result = TrcTractographyResults::loadFile(input_track_dicom.c_str(), track_dataset);
  if (result.bad())
    {
    std::cerr << "Tractography file import failed due to error: " << result.text();
    }
  if (result.good())
    {
    pdtracks = extract_tracks(track_dataset);
    }

  static double lps_to_ras[16] = { -1, 0, 0, 0,
                                  0,-1, 0, 0,
                                  0, 0, 1, 0,
                                  0, 0, 0, 1 };
  vtkSP<vtkTransform> lps_to_ras_xfm = vtkSP<vtkTransform>::New();
  lps_to_ras_xfm->SetMatrix(lps_to_ras);
  vtkSP<vtkTransformPolyDataFilter> pd_xfm = vtkSP<vtkTransformPolyDataFilter>::New();
  pd_xfm->SetInputData(pdtracks[0]);
  pd_xfm->SetTransform(lps_to_ras_xfm);
  pd_xfm->Update();
  vtkSP<vtkPolyData> polydata = vtkSP<vtkPolyData>(pd_xfm->GetOutput());

  // TODO
  vtkXMLPolyDataWriter* writer = vtkXMLPolyDataWriter::New();
  writer->SetInputData(polydata);
  writer->SetFileName(output_vtk.c_str());
  writer->Update();
  writer->Delete();

  return EXIT_SUCCESS;
}

size_t count_points(OFVector<TrcTrack*> tracks)
  {
  size_t points = 0;
  size_t count = 0;
  for (OFVector<TrcTrack*>::iterator iter = tracks.begin();
       iter != tracks.end(); iter++)
    {
    points += (*iter)->getNumDataPoints();
    if (count > 10)
      exit(1);
    }

  return points;
  }

std::vector< vtkSmartPointer<vtkPolyData> >
extract_tracks(TrcTractographyResults *trackdataset)
  {
  std::vector< vtkSmartPointer<vtkPolyData> > results;

  OFVector<TrcTrackSet*> tracksets = trackdataset->getTrackSets();
  if (tracksets.size() < 1)
    {
    std::cerr << "No tracksets in DICOM tractography results!" << std::endl;
    return results;
    }

  DBGOUT << "Found: " << tracksets.size() << " tracksets" << std::endl;

  OFVector<TrcTrackSet*>::iterator iter = tracksets.begin();
  for (; iter != tracksets.end(); iter++)
    {
    vtkSmartPointer<vtkPolyData> track = trackset_to_vtk(*iter);
    if (track.Get() == NULL)
      {
      std::cerr << "no track found" << std::endl;
      continue;
      }

    results.push_back(track);
    }

  return results;
  }

vtkSmartPointer<vtkPolyData> trackset_to_vtk(TrcTrackSet* trackset)
  {
  vtkSmartPointer<vtkPolyData> result_pd = vtkSmartPointer<vtkPolyData>::New();

  OFVector<TrcTrack*> tracks = trackset->getTracks();

  std::cout << trackset->getTrackingAlgorithmIdentification()[0]->toString() << std::endl;

  if (tracks.size() < 1) // TODO coverage
    return result_pd; // no tracks in trackset

  // pre-allocate output
  vtkSmartPointer<vtkPoints> result_pts = vtkSmartPointer<vtkPoints>::New();
  result_pd->SetPoints(result_pts);
  result_pts->SetNumberOfPoints(count_points(tracks));

  vtkSmartPointer<vtkCellArray> result_lines = vtkSmartPointer<vtkCellArray>::New();
  result_pd->SetLines(result_lines);

  // cell id number
  size_t cur_cell_id = 0;
  OFVector<TrcTrack*>::iterator track_iter = tracks.begin();
  for (; track_iter != tracks.end(); track_iter++)
    {
    const float* data;
    size_t num_pts = (*track_iter)->getTrackData(data);
    result_lines->InsertNextCell(num_pts);

    for (size_t i = 0; i < num_pts; i++)
      {
      result_pts->SetPoint(cur_cell_id, (data + i*3));
      result_lines->InsertCellPoint(cur_cell_id);
      cur_cell_id++;
      }
    }

  return result_pd;
  }
