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
#include <vtkFloatArray.h>
#include <vtkMath.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPolyData.h>
#include <vtkXMLPolyDataWriter.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>

// DCMTK includes
#include "dcmtk/dcmtract/trctrack.h"
#include "dcmtk/dcmtract/trctrackset.h"
#include "dcmtk/dcmtract/trcmeasurement.h"
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

// Shared ptr aliases
#define SP OFshared_ptr
#define vtkSP vtkSmartPointer

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

  static double lps_to_ras[16] = { -1,  0, 0, 0,
                                    0, -1, 0, 0,
                                    0,  0, 1, 0,
                                    0,  0, 0, 1 };
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
    }
  return points;
  }

std::vector< vtkSmartPointer<vtkPolyData> >
extract_tracks(TrcTractographyResults *trackdataset)
  {
  std::vector< vtkSmartPointer<vtkPolyData> > results;

  // roughly equivalent to vtkPolyData - can have multiple per DICOM file
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
  //std::cout << "number of tracks: " << trackset->getNumberOfTracks() << std::endl;
  //std::cout << trackset->getTrackingAlgorithmIdentification()[0]->toString() << std::endl;

  if (tracks.size() < 1) // TODO coverage
    return result_pd; // no tracks in trackset

  // pre-allocate output
  size_t total_pts = count_points(tracks);
  vtkSmartPointer<vtkPoints> result_pts = vtkSmartPointer<vtkPoints>::New();
  result_pd->SetPoints(result_pts);
  result_pts->SetNumberOfPoints(total_pts);

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

  /****
   * get along-track Measurements (pointwise scalars)
   *
   * each measurement is stored in a TrcMeasurement object in the trackset
   *   - measurement id is stored as CodeSequenceMacro
   *   - values can be queried directly with TrcMeasurement::get
   *     or by taking the vector of TrcMeasurement::Values (method used below)
   *
   * one quirk to be aware of: faulty writers *could* write measurement without
   * specifying the value for each point. DCMTK debug mode will only *warn* about
   * this, and will return the smaller number in case of a mismatch
   *
   *   see "trcmeasurement.cc/TrcMeasurement::Values::get" in DCMTK
   *
   * to avoid problems, we use TrcMeasurement::checkValuesComplete and ignore any
   * incomplete measurement.
   ****/

  for (size_t i = 0; i < trackset->getNumberOfMeasurements(); i++)
    {
    TrcMeasurement* measurement;
    OFCondition res = trackset->getMeasurement(i, measurement);

    if (!measurement->checkValuesComplete())
      {
      // NOTE: THIS INVARIANT IS IMPORTANT! Many assumptions below
      //       based on the fact that the measurement data is complete.
      continue;
      }

    CodeSequenceMacro type = measurement->getType();

    // this is the name of the measurement, e.g. "Fractional Anisotropy"
    OFString meaning;
    if (type.getCodeMeaning(meaning).bad())
      {
      // skip this measurement if unnamed or incomplete
      // TODO debug output
      continue;
      }

    // create and pre-allocate VTK array to hold output point scalars
    vtkSP<vtkFloatArray> data = vtkSP<vtkFloatArray>::New();
    data->SetNumberOfComponents(1);

    // because checkValuesComplete passed above, we know total number is
    // equal to number of points in the TrcTrack count from above.
    data->SetNumberOfValues(total_pts);
    data->SetName(meaning.c_str());

    size_t insert_idx = 0;

    OFVector<TrcMeasurement::Values*> values = measurement->getValues();
    OFVector<TrcMeasurement::Values*>::iterator values_iter = values.begin();
    for (; values_iter != values.end(); values_iter++)
      {
      const float* dataValues = OFnullptr;
      unsigned long numValues = 0;
      const Uint32* trackPointIndices = OFnullptr;

      res = (*values_iter)->get(dataValues, numValues, trackPointIndices);

      if (res.bad())
        {
        // panic TODO refactor
        std::cerr << "failed reading measurement from track" << std::endl;
        exit(1);
        }

      for (size_t i = 0; i < numValues; i++)
        {
        // note: we are again using the invariant that checkValuesComplete
        //       passed above, because that means the indices are linear
        data->SetValue(insert_idx + i, dataValues[i]);
        }
      insert_idx += numValues;

      }

    // add point scalars to polydata
    result_pd->GetPointData()->AddArray(data);
    }

  return result_pd;
  }