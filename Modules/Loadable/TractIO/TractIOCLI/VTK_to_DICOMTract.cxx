// std includes
#include <algorithm>
#include <iterator>
#include <memory>
#include <sstream>
using std::string;

// VTK includes
#include <vtkPolyData.h>
#include <vtkCell.h>
#include <vtkCellData.h>
#include <vtkPoints.h>
#include <vtkPointData.h>
#include <vtkFloatArray.h>
#include <vtkDataArray.h>
#include <vtkTransform.h>
#include <vtkTransformPolyDataFilter.h>
#include <vtkXMLPolyDataReader.h>

// DCMTK includes
#include "dcmtk/config/osconfig.h"    /* make sure OS specific configuration is included first */

#define INCLUDE_CMATH
#include "dcmtk/dcmsr/codes/dcm.h"
#include "dcmtk/ofstd/ofstdinc.h"
#include "dcmtk/ofstd/ofcond.h"
#include "dcmtk/dcmiod/iodreferences.h"
#include "dcmtk/dcmiod/iodcontentitemmacro.h"
#include "dcmtk/dcmtract/trctractographyresults.h"
#include "dcmtk/dcmtract/trctrackset.h"
#include "dcmtk/dcmtract/trcmeasurement.h"
#include "dcmtk/dcmtract/trctrack.h"
#include "dcmtk/dcmtract/trctypes.h"

// Slicer includes
#ifdef HAVE_SSTREAM
#undef HAVE_SSTREAM // no guards in dcmtk or SEM...
#endif
#include "VTK_to_DICOMTractCLP.h"

// Shared ptr aliases
#define SP OFshared_ptr
#define vtkSP vtkSmartPointer

#define TIO_MANUFACTURER "libTractIO";
#define TIO_MANUFACTURER_MODELNAME "vtktodicom";
#define TIO_DEVICESERIALNUMBER "0000";
#define TIO_SOFTWAREVERSIONS "TractIO 0.1\\DCMTK 3.6.1";

// Derived from Isaiah's Medical Connections UID root
#define SLICERDMRI_UID_SERIES_ROOT "1.2.826.0.1.3680043.9.7239.2.1"

// Mapping from text keys to Supplement 181 family codes in DCMTK dictionary
std::map<string, DSRBasicCodedEntry> algorithmFamily_keys = {
  { "Deterministic", CODE_DCM_DeterministicTrackingAlgorithm },
  { "Probabilistic", CODE_DCM_ProbabilisticTrackingAlgorithm },
  { "Global", CODE_DCM_GlobalTrackingAlgorithm },
  { "FACT", CODE_DCM_FACT },
  { "Streamline", CODE_DCM_Streamline },
  { "TEND", CODE_DCM_TEND },
  { "Bootstrap", CODE_DCM_BootstrapTrackingAlgorithm },
  { "Euler", CODE_DCM_Euler },
  { "RungeKutta", CODE_DCM_RungeKutta }
};

std::map<string, DSRBasicCodedEntry> diffusionValue_keys = {
  { "Trace", CODE_DCM_Trace },
  { "MeanDiffusivity", CODE_DCM_MeanDiffusivity },
  { "ApparentDiffusionCoefficient", CODE_DCM_ApparentDiffusionCoefficient },
  { "FractionalAnisotropy", CODE_DCM_FractionalAnisotropy },
  { "RelativeAnisotropy", CODE_DCM_RelativeAnisotropy },
  { "RadialDiffusivity", CODE_DCM_RadialDiffusivity },
  { "AxialDiffusivity", CODE_DCM_AxialDiffusivity },
  { "MeanKurtosis", CODE_DCM_MeanKurtosis },
  { "ApparentKurtosisCoefficient", CODE_DCM_ApparentKurtosisCoefficient },
  { "RadialKurtosis", CODE_DCM_RadialKurtosis },
  { "AxialKurtosis", CODE_DCM_AxialKurtosis },
  { "FractionalKurtosisAnisotropy", CODE_DCM_FractionalKurtosisAnisotropy },
  { "VolumetricDiffusionDxxComponent", CODE_DCM_VolumetricDiffusionDxxComponent },
  { "VolumetricDiffusionDxyComponent", CODE_DCM_VolumetricDiffusionDxyComponent },
  { "VolumetricDiffusionDxzComponent", CODE_DCM_VolumetricDiffusionDxzComponent },
  { "VolumetricDiffusionDyyComponent", CODE_DCM_VolumetricDiffusionDyyComponent },
  { "VolumetricDiffusionDyzComponent", CODE_DCM_VolumetricDiffusionDyzComponent },
  { "VolumetricDiffusionDzzComponent", CODE_DCM_VolumetricDiffusionDzzComponent }
};

std::map<string, TrcTypes::E_TrackSetLaterality> laterality_keys = {
  {"Unknown", TrcTypes::LAT_UNKNOWN },
  {"Left", TrcTypes::LAT_LEFT },
  {"Right", TrcTypes::LAT_RIGHT },
  {"RightAndLeft", TrcTypes::LAT_RIGHT_AND_LEFT },
  {"Unilateral", TrcTypes::LAT_UNILATERAL }
};

typedef struct {
  std::string label;
  DSRBasicCodedEntry AlgorithmFamily;
  std::string AlgorithmVersion;
  std::string AlgorithmName;
  std::string Laterality;
} TrackInfo;

// Forward declaration
SP<TrcTractographyResults> create_dicom(std::vector<std::string> files);
int add_tracts(SP<TrcTractographyResults> dcmtract,
               vtkSP<vtkPolyData> polydata,
               TrackInfo info);
vtkSP<vtkPolyData> load_polydata(std::string polydata_file);

int main(int argc, char *argv[])
{
  PARSE_ARGS;
  // defines:
  //   std::string vtk_fiberbundle reference_dicom output_directory output_filename
  //   bool ras_to_lps

  std::string polydata_file = vtk_fiberbundle;

  std::stringstream output_tmp;
  output_tmp << output_directory << "/" << output_filename;
  std::string output_file = output_tmp.str();

  std::vector<std::string> ref_files = reference_dicom;

  // validate the algorithmFamily and set corresponding code
  auto findAlgoFamily = algorithmFamily_keys.find(AlgorithmFamily);
  if (findAlgoFamily == algorithmFamily_keys.end())
    {
    std::cerr << "Invalid or missing 'algorithmFamily', please see value enumeration in --help." << std::endl;
    return EXIT_FAILURE;
    }
  DSRBasicCodedEntry AlgorithmFamilyCode = findAlgoFamily->second;

  if (AlgorithmVersion.empty())
    {
    std::cerr << "Missing required 'AlgorithmVersion' argument";
    return EXIT_FAILURE;
    }

  TrackInfo info{
    "TRACKSET" /*TODO*/,
    AlgorithmFamilyCode,
    AlgorithmVersion,
    AlgorithmName,
    Laterality
  };

  // read polydata file
  vtkSP<vtkPolyData> polydata = load_polydata(polydata_file);

  if (!polydata)
    {
    std::cerr << "Error: failed to load polydata" << std::endl;
    return EXIT_FAILURE;
    }

  // TODO
  static double rastolps[16] = { -1, 0, 0, 0,
                                  0,-1, 0, 0,
                                  0, 0, 1, 0,
                                  0, 0, 0, 1 };
  vtkSP<vtkTransform> raslps_xfm = vtkSP<vtkTransform>::New();
  raslps_xfm->SetMatrix(rastolps);
  vtkSP<vtkTransformPolyDataFilter> pd_xfm = vtkSP<vtkTransformPolyDataFilter>::New();
  pd_xfm->SetInputData(polydata);
  pd_xfm->SetTransform(raslps_xfm);
  pd_xfm->Update();
  polydata = pd_xfm->GetOutput();

  OFLog::configure(OFLogger::TRACE_LOG_LEVEL);

  // create DICOM object associated to reference files
  SP<TrcTractographyResults> dicom = create_dicom(ref_files);
  if (!dicom)
    {
    std::cerr << "Error: Tract DICOM object creation failed!" << std::endl;
    return EXIT_FAILURE;
    }

  // rewrite the SeriesInstanceUID to be unique
  IODGeneralSeriesModule series_mod = dicom->getSeries();
  char uid[65];
  series_mod.setSeriesInstanceUID(dcmGenerateUniqueIdentifier(uid, SLICERDMRI_UID_SERIES_ROOT));

  // add tracks from polydata
  if ( add_tracts(dicom, polydata, info) != 0)
    {
    std::cerr << "Error: Failed to add tracks from polydata." << std::endl;
    return EXIT_FAILURE;
    }



  // write DICOM to disk
  OFCondition ofresult;
  ofresult = dicom->saveFile(output_file.c_str());
  if (ofresult.bad())
    {
    std::cerr << "Error: Failed to save tractography DICOM file." << std::endl;
    return EXIT_FAILURE;
    }

  return EXIT_SUCCESS;
}

/* ------------------------------------------------------------------------- */

SP<TrcTractographyResults> create_dicom(std::vector<std::string> files)
{
  OFCondition result;
  SP<TrcTractographyResults> tract;

  ContentIdentificationMacro* contentID = NULL;
  result = ContentIdentificationMacro::create("1", "TRACT_TEST_LABEL",
                                              "Tractography from VTK file",
                                              "TractIO^Library",
                                              contentID);

  if (result.bad())
    return tract;

  // TODO: auto-convert
  std::vector<std::string>::iterator files_iter = files.begin();
  OFVector<OFString> of_files;
  for (; files_iter != files.end(); files_iter++)
    of_files.push_back( files_iter->c_str());

  std::cout << "Reference file: " << of_files[0] << std::endl;
  IODReferences references;
  if ( references.addFromFiles(of_files) != files.size() )
    return tract;

  IODEnhGeneralEquipmentModule::EquipmentInfo eq;
  eq.m_Manufacturer           = TIO_MANUFACTURER;
  eq.m_ManufacturerModelName  = TIO_MANUFACTURER_MODELNAME;
  eq.m_DeviceSerialNumber     = TIO_DEVICESERIALNUMBER;
  eq.m_SoftwareVersions       = TIO_SOFTWAREVERSIONS;

  TrcTractographyResults *p_tract = NULL;
  result = TrcTractographyResults::create(
             *contentID,
             "20160329", // TODO actual date
             "124200",   // TODO actual time
             eq,
             references,
             p_tract);


  if (result.good())
    {
    result = p_tract->importHierarchy(files[0].c_str(),
                                            true, /* usePatient*/
                                            true, /* useStudy */
                                            true, /* useSeries */
                                            true  /* useFoR = use Frame of Reference */
                                            );    /*          i.e. patient space     */
    }

  if (result.good())
    {
    // take pointer
    tract.reset(p_tract);
    }
  else
    {
    delete contentID;
    contentID = NULL;
    delete p_tract;
    p_tract = NULL;
    }

  return tract;
}

vtkSP<vtkPolyData> load_polydata(std::string polydata_file)
{
  // TODO: handle traditional .vtk files
  vtkSP<vtkXMLPolyDataReader> reader = vtkSP<vtkXMLPolyDataReader>::New();

  reader->SetFileName(polydata_file.c_str());
  reader->Update();

  if (!reader->GetOutput())
    {
    std::cerr << "Error: failed to read VTK file \"" << polydata_file << "\"" << std::endl;
    return vtkSP<vtkPolyData>();
    }

  return vtkSP<vtkPolyData>(reader->GetOutput());
}

int insert_polydata_tracts(TrcTrackSet *trackset,
                           vtkSP<vtkPolyData> polydata)
{
  OFCondition result;
  vtkPoints *points = polydata->GetPoints();

  if (!points)
    {
    std::cerr << "PolyData fibertrack missing points!" << std::endl;
    return 1;
    }

  vtkSP<vtkFloatArray> pointdata = vtkSP<vtkFloatArray>::New();

  // ShallowCopy will do a type-correct conversion if types do match.
  pointdata->ShallowCopy(points->GetData());

  if (pointdata->GetNumberOfTuples() < 1)
    {
    std::cerr << "PolyData fibertrack missing point data!" << std::endl;
    return 1;
    }


  /* add points for each track */
  for (vtkIdType i = 0; i < polydata->GetNumberOfCells(); i++)
    {
    vtkCell *cell = polydata->GetCell(i);
    vtkIdType numPoints   = cell->GetNumberOfPoints();
    vtkIdType cellStartIdx = cell->GetPointId(0);
    TrcTrack *track_dontcare = NULL;

    // TODO: verify contiguity assumption is correct in general.
    float *cellPointData = (float*)pointdata->GetVoidPointer(cellStartIdx * 3);
    result = trackset->addTrack(cellPointData,
                                numPoints,
                                NULL, 0,
                                track_dontcare);

    if (result.bad())
      {
      std::cerr << "Error adding polydata track to trackset." << std::endl;
      return 1;
      }
    }

  return 0;
}


int insert_polydata_scalars(TrcTrackSet* trackset,
                            vtkSP<vtkPolyData> polydata)
  {
  /* add measurements (scalars) for each track, if any */
  vtkSP<vtkCellData> cells(polydata->GetCellData());
  vtkSP<vtkPointData> pointdata = vtkSP<vtkPointData>(polydata->GetPointData());
  std::vector<float> tmp_float;

  size_t numarrays = pointdata->GetNumberOfArrays();
  if (numarrays < 1)
    return -1;

  for (size_t scalar_idx = 0;
       scalar_idx < numarrays;
       scalar_idx++)
    {
    vtkCellArray* lines = polydata->GetLines();
    vtkDataArray* array = pointdata->GetArray(scalar_idx);
    std::string arrayName(pointdata->GetArrayName(scalar_idx));
    size_t numtracks = polydata->GetNumberOfLines();

    if ((lines == nullptr) || (numtracks < 1))
      continue;

    std::map<string, DSRBasicCodedEntry>::iterator msrmap_iter =
      diffusionValue_keys.find(arrayName);

    if (msrmap_iter == diffusionValue_keys.end())
      {
      // HACK/TODO: also check without whitespace until we regularize VTK output names
      std::string arrayName_no_ws;
      arrayName_no_ws.reserve(arrayName.size());
      std::remove_copy_if(
        begin(arrayName), end(arrayName),
        std::back_inserter(arrayName_no_ws),
        [](char ch) { return ch == ' '; }
      );

      std::cout << "Trying array name without whitespace: " << arrayName_no_ws << std::endl;

      msrmap_iter = diffusionValue_keys.find(arrayName_no_ws);

      if (msrmap_iter == diffusionValue_keys.end())
        {
        std::cerr << "Skipping array due to no measurement code mapping available for array name: " << arrayName << std::endl;
        continue;
        }
      }

    // convert the DSRBasicCodedEntry to a CodeSequenceMacro
    //   see https://github.com/QIICR/dcmqi/issues/343#issuecomment-381430240
    DSRBasicCodedEntry codedEntry(msrmap_iter->second);
    CodeSequenceMacro typeCode(codedEntry.CodeValue, codedEntry.CodingSchemeDesignator, codedEntry.CodeMeaning);
    // TODO some of these do have units
    CodeSequenceMacro unitCode;

    if ((arrayName == "Trace") ||
        (arrayName.find("Diffusivity") != std::string::npos))
      {
      unitCode = CodeSequenceMacro("mm2/s", "UCUM", "mm2/s");
      }
    else
      {
      unitCode = CodeSequenceMacro("1", "UCUM", "no units");
      }

    TrcMeasurement* measurement;
    //OFCondition res = TrcMeasurement::create(typeCode, unitCode, measurement);
    OFCondition res = trackset->addMeasurement(typeCode, unitCode, measurement);

#if VTK_MAJOR_VERSION >= 9 || (VTK_MAJOR_VERSION >= 8 && VTK_MINOR_VERSION >= 90)
    const vtkIdType* ptids;
#else
    vtkIdType* ptids;
#endif
    vtkIdType numpts;
    lines->InitTraversal();
    size_t track_idx = 0;

    while (lines->GetNextCell(numpts, ptids))
      {
      //= ptids->GetNumberOfIds();
      tmp_float.reserve(numpts);

      // copy the measures to tmp array. (no contiguity assumption for cells)
      for (vtkIdType pt_idx = 0; pt_idx < numpts; pt_idx++)
        tmp_float.push_back(*array->GetTuple(pt_idx));

      // copy the data into the TrcMeasurement
      measurement->setTrackValues(track_idx, tmp_float.data(), numpts);

      track_idx++;
      }

    }

  return 0;
  }


int add_tracts(SP<TrcTractographyResults> dcmtract,
               vtkSP<vtkPolyData> polydata,
               TrackInfo info)
{
  assert(polydata);

  OFCondition result;

  CodeWithModifiers anatomyCode("3");
    anatomyCode.set("T-A0095", "SRT", "White matter of brain and spinal cord");

  CodeSequenceMacro diffusionModelCode("113231", "DCM", "Single Tensor");

  AlgorithmIdentificationMacro algorithmId;
  algorithmId.getAlgorithmFamilyCode().set("113211", "DCM", "Deterministic");
  algorithmId.setAlgorithmName(info.AlgorithmName.c_str());
  algorithmId.setAlgorithmVersion(info.AlgorithmVersion.c_str());
  algorithmId.setAlgorithmParameters("");
  algorithmId.setAlgorithmSource("");

  char buf_label[100];
  snprintf(buf_label, sizeof(buf_label), "%s", info.label.c_str());

  TrcTrackSet *trackset = NULL;
  result = dcmtract->addTrackSet(
    buf_label,
    buf_label,
    anatomyCode,
    diffusionModelCode,
    algorithmId,
    trackset);

  trackset->setLaterality(laterality_keys[info.Laterality], false);

  if (result.bad())
    return 1;

  /* required by standard */
  trackset->setRecommendedDisplayCIELabValue(1,1,1);

  // TODO check error
  insert_polydata_tracts(trackset, polydata);

  return insert_polydata_scalars(trackset, polydata);
}

