#include <algorithm>
#include <iostream>

// vtkTeem includes
#include <vtkDiffusionTensorMathematics.h>
#include <Libs/vtkTeem/vtkTeemNRRDReader.h>
#include <Libs/vtkTeem/vtkTeemNRRDWriter.h>

// vnl includes
#include <vnl/vnl_math.h>
#include <vnl/vnl_double_3.h>

// VTK includes
#include <vtkAssignAttribute.h>
#include <vtkGlobFileNames.h>
#include <vtkImageData.h>
#include <vtkMath.h>
#include <vtkNew.h>
#include <vtkPointData.h>
#include <vtkPolyDataTensorToColor.h>
#include <vtkPolyDataReader.h>
#include <vtkStringArray.h>
#include <vtkXMLPolyDataReader.h>
#include <vtkSortDataArray.h>
#include <vtkDoubleArray.h>
// VTKsys includes
#include <vtksys/SystemTools.hxx>

// MRML
#include <vtkMRMLModelHierarchyNode.h>
#include <vtkMRMLModelNode.h>
#include <vtkMRMLModelStorageNode.h>
#include <vtkMRMLScene.h>
#include <vtkMRMLFiberBundleNode.h>
#include <vtkMRMLFiberBundleLineDisplayNode.h>
#include <vtkMRMLFiberBundleTubeDisplayNode.h>
#include <vtkMRMLFiberBundleGlyphDisplayNode.h>
#include <vtkMRMLFiberBundleStorageNode.h>
#include <vtkMRMLSceneViewNode.h>
#include <vtkMRMLSceneViewStorageNode.h>
#include <vtkMRMLCommandLineModuleNode.h>

// ITK includes
#include <itkFloatingPointExceptions.h>

// Auto-generated CLP include
#include "FiberTractMeasurementsCLP.h"

//=============================================================================
// Maps to hold results
std::map< std::string, std::map<std::string, double> > OutTable;
std::map< std::string, std::string> ClusterNames;
std::map< std::string, std::map<std::string, double> > Clusters;

#define INVALID_NUMBER_PRINT std::string("NAN")
#define EXCLUDED_NUMBER_PRINT std::string("Num_Clamp_Excluded")
#define MEAN_PRINT std::string("Mean")
#define MAX_PRINT std::string("Max")
#define MIN_PRINT std::string("Min")
#define MEDIAN_PRINT std::string("Median")
#define VARIANCE_PRINT std::string("Variance")

std::string SEPARATOR;

typedef std::pair<size_t, size_t> Range;
typedef std::map<std::string, Range> ClampedOp_t;
static ClampedOp_t clamped_ops;

typedef std::vector<std::string> AggNames_t;
AggNames_t aggregate_names;

// BUG, TODO: this is global because FA calc doesn't work (no scalars) when
//      the PDTensorToColor is allocated inside function.
vtkNew<vtkPolyDataTensorToColor> math;

//=============================================================================
// Function declarations
void computeFiberStats(vtkSmartPointer<vtkPolyData> input,
                       std::string &id);

void computeScalarMeasurements(vtkSmartPointer<vtkPolyData> input,
                               std::string &id,
                               std::string &operation,
                               bool moreStatistics);

int computeTensorMeasurement(vtkSmartPointer<vtkPolyData> input,
                             std::string &id,
                             std::string &operation,
                             bool moreStatistics);

void getPathFromParentToChild(vtkMRMLHierarchyNode *parent,
                              vtkMRMLHierarchyNode *child,
                              std::string &path);

bool setTensors(vtkPolyData *poly);

void printTable(std::ostream &ofs, bool printHeader,
                std::map< std::string, std::map<std::string, double> > &output);

std::string getNthTensorName(int n, vtkPolyData *poly);

bool isInCluster(const std::string &id, const std::string &clusterName);

int getNumberOfTensors(vtkPolyData *poly);

int addClusters();

void printFlat(std::ostream &ofs, bool printAllStatistics=false);

void printCluster(const std::string &id,
                  std::map< std::string, std::map<std::string, double> > &output,
                  std::map<std::string, std::string> &names,
                  std::stringstream &ids,
                  std::stringstream &measureNames,
                  std::stringstream &measureValues);

namespace {
  double median_of_sorted(vtkDoubleArray* d)
  {
    size_t n = d->GetNumberOfValues();
    double mid_floorth = d->GetComponent(n/2, 0);
    if (n % 2 != 0) // odd number of points
      return mid_floorth;
    else
      return (mid_floorth + d->GetComponent(n/2 - 1, 0)) / 2;
  }
};

//=============================================================================
// Function definitions
void getPathFromParentToChild(vtkMRMLHierarchyNode *parent,
                              vtkMRMLHierarchyNode *child,
                              std::string &path)
{
  vtkMRMLHierarchyNode *immediateParent = child->GetParentNode();
  if (immediateParent)
    {
    std::string parentName = immediateParent->GetName() ? immediateParent->GetName() : immediateParent->GetID();
    std::string childName = child->GetName() ? child->GetName() : child->GetID();
    std::map<std::string, std::string>::iterator it = ClusterNames.find(childName);
    if (it != ClusterNames.end())
      {
      ClusterNames[childName] = parentName + std::string(":") + it->second;
      }
    path = parentName + std::string(":") + path;
    ClusterNames[parentName] = parentName;

    if (strcmp(immediateParent->GetID(), parent->GetID()) != 0)
      {
      getPathFromParentToChild(parent, immediateParent, path);
      }
    }
}

double computeMeanLineLength(vtkSmartPointer<vtkPolyData> poly)
{
  size_t total_measured_lines = 0;
  double total_length = 0.0;
  vnl_double_3 prev, next;
  vtkNew<vtkIdList> pointIds;

  poly->GetLines()->InitTraversal();

  while(poly->GetLines()->GetNextCell(pointIds.GetPointer()))
    {
    // get first point
    poly->GetPoints()->GetPoint(pointIds->GetId(0), prev.data_block());

    // count by segments
    size_t n = 1;

    for ( ; n < pointIds->GetNumberOfIds(); n++)
      {
      // get next point
      poly->GetPoints()->GetPoint(pointIds->GetId(n), next.data_block());

      // add segment length to total
      total_length += (next - prev).two_norm();
      prev = next;
      }

    // only count line if actually measured
    if (n > 1) { total_measured_lines++; }
    }

  return total_length / total_measured_lines;
}

void computeFiberStats(vtkSmartPointer<vtkPolyData> poly,
                       std::string &id)
{
  if (!poly) {
    std::cerr << "computeFiberStats: missing polydata input for id: " << id << std::endl;
    return;
  }

  size_t npoints = poly->GetNumberOfPoints();
  size_t npolys = poly->GetNumberOfCells();
  double mean_length = computeMeanLineLength(poly);

  //if (npoints > 0 && npolys > 0)
  //  {
    std::map< std::string, std::map<std::string, double> >::iterator it = OutTable.find(id);
    if (it == OutTable.end())
      {
      OutTable[id] = std::map<std::string, double>();
      it = OutTable.find(id);
      }
    it->second["Num_Points"] = npoints;
    it->second["Num_Fibers"] = npolys;
    it->second["Mean_Length"] = mean_length;
   // }
}

void computeScalarMeasurements(vtkSmartPointer<vtkPolyData> poly,
                               std::string &id,
                               std::string &operation,
                               bool moreStatistics)
{
  vtkIdType npoints = poly->GetNumberOfPoints();
  vtkIdType npoints_final = npoints;
  vtkIdType npoints_excluded = 0;
  vtkIdType npolys = poly->GetNumberOfCells();

  if (npoints == 0 || npolys == 0)
    {
    //return;
    }

  // average measurement for each scalar array
  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    vtkDataArray *arr = poly->GetPointData()->GetArray(i);
    if (arr->GetNumberOfComponents() > 1)
      {
      continue;
      }

    std::string name = operation;
    if (arr->GetName())
      {
      name = std::string(arr->GetName());
      }

    // check whether this measurement should be clamped to specific range.
    bool measuring_clamped = false;
    double op_max = 0.0;
    double op_min = 0.0;
    ClampedOp_t::iterator op_iter;
    for (op_iter = clamped_ops.begin(); op_iter != clamped_ops.end(); op_iter++)
      {
      if (name.find(op_iter->first) != std::string::npos)
        {
        measuring_clamped = true;
        op_min = op_iter->second.first;
        op_max = op_iter->second.second;
        }
      }

    vtkDoubleArray *vals = vtkDoubleArray::New();
    double val;
    double sum = 0;
    for (int n=0; n < npoints; n++)
      {
      arr->GetTuple(n, &val);

      if (vtkMath::IsNan(val))
        {
        npoints_final -= 1;
        continue;
        }
      if (measuring_clamped && (val < op_min || val > op_max))
        {
        npoints_final -= 1;
        npoints_excluded += 1;
        continue;
        }
      vals->InsertNextValue(val);
      sum += val;
      }

    vtkSortDataArray::Sort(vals);

    double sortval = 0;
    double median  = 0;
    double mean = 0;
    double max = 0;
    double min = 0;
    double variance = 0;

    if (npoints_final > 0)
      {
      mean = sum / npoints_final;

      if (moreStatistics)
        {
        min = (double) vals->GetComponent(0, 0);
        max = (double) vals->GetComponent(npoints_final - 1, 0);
        median = median_of_sorted(vals);

        for (int n = 0; n < npoints_final; n++)
          {
          sortval = (double) vals->GetComponent(n, 0);
          variance += (sortval - mean) * (sortval - mean);
          }
        variance /= npoints_final - 1;
        }
      }
    else
      {
      mean = vtkMath::Nan();
      if (moreStatistics)
        {
        min = vtkMath::Nan();
        max = vtkMath::Nan();
        median = vtkMath::Nan();
        variance = vtkMath::Nan();
        }
      }

    vals->Delete();

    std::map< std::string, std::map<std::string, double> >::iterator it = OutTable.find(id);
    if (it == OutTable.end())
      {
      OutTable[id] = std::map<std::string, double>();
      it = OutTable.find(id);
      }

    std::string name_mean = name + "." + MEAN_PRINT;
    it->second[name_mean] = mean;

    if (moreStatistics)
      {
      std::string name_min = name + "." + MIN_PRINT;
      std::string name_max = name + "." + MAX_PRINT;
      std::string name_median = name + "." + MEDIAN_PRINT;
      std::string name_variance = name + "." + VARIANCE_PRINT;
      std::string nanid = name + "." + INVALID_NUMBER_PRINT;

      it->second[name_min] = min;
      it->second[name_max] = max;
      it->second[name_median] = median;
      it->second[name_variance] = variance;
      it->second[nanid] = npoints - npoints_final; // record the number of NaNs for this measurement

      if (measuring_clamped)
      {
        // record aggregate count of excluded points outside of clamped range
        std::string excluded_id = EXCLUDED_NUMBER_PRINT;
        it->second[excluded_id] += npoints_excluded;
        }
      }
    } //for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
}

int computeTensorMeasurement(vtkSmartPointer<vtkPolyData> poly,
                             std::string &id,
                             std::string &operation,
                             bool moreStatistics)
{
  //TODO loop over all tensors, use ExtractTensor
  vtkNew<vtkAssignAttribute> assignAttribute;
  assignAttribute->SetInputData(poly);
  math->SetInputConnection(assignAttribute->GetOutputPort());

  for (int i=0; i < getNumberOfTensors(poly); i++)
    {
    std::string name = getNthTensorName(i, poly);

    assignAttribute->Assign(
      name.c_str(),
      name.c_str() ? vtkDataSetAttributes::TENSORS : -1,
      vtkAssignAttribute::POINT_DATA);

    assignAttribute->Update();

    if( operation == std::string("Trace") )
      {
      math->ColorGlyphsByTrace();
      }
    else if( operation == "MeanDiffusivity")
      {
      math->ColorGlyphsByMeanDiffusivity();
      }
    else if( operation == std::string("RelativeAnisotropy") )
      {
      math->ColorGlyphsByRelativeAnisotropy();
      }
    else if( operation == std::string("FractionalAnisotropy") )
      {
      math->ColorGlyphsByFractionalAnisotropy();
      }
    else if( operation == std::string("LinearMeasure") )
      {
      math->ColorGlyphsByLinearMeasure();
      }
    else if( operation == std::string("PlanarMeasure") )
      {
      math->ColorGlyphsByPlanarMeasure();
      }
    else if( operation == std::string("SphericalMeasure") )
      {
      math->ColorGlyphsBySphericalMeasure();
      }
    else if( operation == std::string("MinEigenvalue") )
      {
      math->ColorGlyphsByMinEigenvalue();
      }
    else if( operation == std::string("MidEigenvalue") )
      {
      math->ColorGlyphsByMidEigenvalue();
      }
    else if( operation == std::string("MaxEigenvalue") )
      {
      math->ColorGlyphsByMaxEigenvalue();
      }
    else
      {
      std::cerr << operation << ": Operation " << operation << "not supported" << std::endl;
      return EXIT_FAILURE;
      }

    math->Update();

    if (!math->GetOutput()->GetPointData() || !math->GetOutput()->GetPointData()->GetScalars())
      {
      std::cout << "no scalars computed for cluster: \"" << id << "\" and op: \"" << operation << "\"" << std::endl;
      }
    std::string scalarName = name + std::string(".") + operation;
    computeScalarMeasurements(math->GetOutput(), id, scalarName, moreStatistics);
    }

  return EXIT_SUCCESS;
}

int computeAllTensorMeasurements(vtkSmartPointer<vtkPolyData> input,
                                 std::string &id,
                                 std::vector<std::string> operations,
                                 bool moreStatistics)
{
  int result = EXIT_SUCCESS;
  std::vector<std::string>::iterator op_iter = operations.begin();
  for (; op_iter != operations.end(); op_iter++)
    result = result & computeTensorMeasurement(input, id, *op_iter, moreStatistics);

  return result;
}

bool setTensors(vtkPolyData *poly)
{
  bool hasTensors = false;
  if (poly)
    {
    if (poly->GetPointData()->GetTensors())
      {
      hasTensors = true;
      }
    else
      {
      for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
        {
        vtkDataArray *arr = poly->GetPointData()->GetArray(i);
        if (arr->GetNumberOfComponents() == 9)
          {
          poly->GetPointData()->SetTensors(arr);
          hasTensors = true;
          }
        }
      }
    }
  return hasTensors;
}

int getNumberOfTensors(vtkPolyData *poly)
{
  int count = 0;
  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    vtkDataArray *arr = poly->GetPointData()->GetArray(i);
    if (arr->GetNumberOfComponents() == 9)
      {
        count++;
      }
    }
  return count;
}

std::string getNthTensorName(int n, vtkPolyData *poly)
{
  int count = 0;
  for (int i=0; i<poly->GetPointData()->GetNumberOfArrays(); i++)
    {
    vtkDataArray *arr = poly->GetPointData()->GetArray(i);
    if (arr->GetNumberOfComponents() == 9)
      {
      if (count == n)
        {
          return arr->GetName() ? std::string(arr->GetName()) : std::string();
        }
      count++;
      }
    }
  return std::string();
}

std::map<std::string, std::string> getMeasureNames()
{
  std::map<std::string, std::string> names;
  std::map< std::string, std::map<std::string, double> >::iterator it;
  std::map<std::string, double>::iterator it1;

  for(it = OutTable.begin(); it != OutTable.end(); it++)
    {
    for (it1 = it->second.begin(); it1 != it->second.end(); it1++)
      {
      names[it1->first] = it1->first;
      }
    }
  return names;
}

void printTable(std::ostream &ofs, bool printHeader,
                std::map< std::string, std::map<std::string, double> > &output)
{
  std::map<std::string, std::string> names = getMeasureNames();

  std::map< std::string, std::map<std::string, double> >::iterator it;
  std::map<std::string, double>::iterator it1;
  std::map<std::string, std::string>::iterator it2;

  // print header, if necessary
  if (printHeader)
    {
    ofs << "Name";

    for (AggNames_t::iterator agg_iter  = aggregate_names.begin();
                              agg_iter != aggregate_names.end();
                              agg_iter++)
      {
      it2 = names.find(*agg_iter);
      if (it2 != names.end())
        {
        ofs       << " " << SEPARATOR << " " << it2->second;
        }
      }

    for (it2 = names.begin(); it2 != names.end(); it2++)
      {
      if (std::find(aggregate_names.begin(), aggregate_names.end(), it2->first) == aggregate_names.end())
        {
        ofs       << " " << SEPARATOR << " " << it2->second;
        }
      }
    ofs << std::endl;
    } // if (printHeader)

  // print output measured values
  for(it = output.begin(); it != output.end(); it++)
    {

    // find if this cluster in any other cluster
    bool topCluster = true;
    std::map<std::string, std::string>::iterator itClusterNames1;
    for (itClusterNames1 = ClusterNames.begin(); itClusterNames1!= ClusterNames.end(); itClusterNames1++)
      {
      if (isInCluster(it->first, itClusterNames1->first) )
        {
        topCluster = false;
        break;
        }
      }

    ofs << it->first;

    // print metadata (# points, etc.)
    for (AggNames_t::iterator agg_iter  = aggregate_names.begin();
                              agg_iter != aggregate_names.end();
                              agg_iter++)
      {
      it2 = names.find(*agg_iter);
      if (it2 != names.end())
        {
        ofs << " " << SEPARATOR << " ";
        it1 = it->second.find(*agg_iter);
        if (it1 != it->second.end())
          {
          if (vtkMath::IsNan(it1->second))
            {
            ofs << INVALID_NUMBER_PRINT;
            }
          else
            {
            ofs << std::fixed << it1->second;
            }
          }
        }
      }

    // print actual values
    for (it2 = names.begin(); it2 != names.end(); it2++)
      {
      if (std::find(aggregate_names.begin(), aggregate_names.end(), it2->first) == aggregate_names.end())
        {
        ofs << " " << SEPARATOR << " ";

        it1 = it->second.find(it2->second);
        if (it1 != it->second.end() &&
            vtkMath::IsNan(it1->second) == false)
          {
            ofs << std::fixed << it1->second;
          }
        else
        // if value is missing or NAN, print NAN
          {
            ofs << INVALID_NUMBER_PRINT;
          }
        }
      }
    ofs << std::endl;
    }
}

bool isInCluster(const std::string &id, const std::string &clusterName)
{
  std::string s = id;
  std::string delimiter = ":";
  size_t pos = 0;
  std::string token;
  while ((pos = s.find(delimiter)) != std::string::npos)
    {
    token = s.substr(0, pos);
    if (clusterName == token)
      {
      return true;
      }
    s.erase(0, pos + delimiter.length());
    }
  return false;
}

int addClusters()
{
  std::map< std::string, std::map<std::string, double> >::iterator itOutput;
  std::map<std::string, double>::iterator itValues;
  std::map<std::string, double>::iterator itClusterValues;
  std::map<std::string, std::string>::iterator itClusterNames;
  std::map<std::string, std::string>::iterator itNames;

  std::map<std::string, std::string> names = getMeasureNames();

  for (itClusterNames = ClusterNames.begin(); itClusterNames!= ClusterNames.end(); itClusterNames++)
    {
    Clusters[itClusterNames->second] = std::map<std::string, double>();
    std::map< std::string, std::map<std::string, double> >::iterator itCluster = Clusters.find(itClusterNames->second);

    int npoints = 0;
    int npointsCluster = 0;
    for(itOutput = OutTable.begin(); itOutput != OutTable.end(); itOutput++)
      {
      if (isInCluster(itOutput->first, itClusterNames->first))
        {
        itValues = itOutput->second.find(std::string("Num_Points"));
        if (itValues != itOutput->second.end())
          {
          npoints = itValues->second;
          }
        npointsCluster += npoints;

        for (itNames = names.begin(); itNames != names.end(); itNames++)
          {
          itValues = itOutput->second.find(itNames->second);
          if (itValues == itOutput->second.end())
            {
            std::cerr << "Fibers contain different number of scalars, name: " << itNames->second << std::endl;
            return 0;
            }

          itClusterValues = itCluster->second.find(itNames->second);
          if (itClusterValues == itCluster->second.end())
            {
            itCluster->second[itNames->second] = 0;
            itClusterValues = itCluster->second.find(itNames->second);
            }
          double clusterValue = itClusterValues->second;
          if (itValues != itOutput->second.end() &&
              (std::find(aggregate_names.begin(), aggregate_names.end(), itNames->second) == aggregate_names.end()) &&
              itNames->second.find("NAN") == std::string::npos)
            {
            if (!vtkMath::IsNan(itValues->second))
              {
              clusterValue += npoints * itValues->second;
              }
            }
          else
            {
            clusterValue += itValues->second;
            }

          itCluster->second[itNames->second] = clusterValue;
          } ////for (itNames = names.begin(); itNames != names.end(); itNames++)
        } // if (isInCluster(itOutput->first, itClusterNames->first)
      } // for(itOutput = OutTable.begin(); itOutput != OutTable.end(); itOutput++)

      // second pass divide by npoints
      for (itNames = names.begin(); itNames != names.end(); itNames++)
        {
        itClusterValues = itCluster->second.find(itNames->second);
        if (itClusterValues != itCluster->second.end() &&
            (std::find(aggregate_names.begin(), aggregate_names.end(), itNames->second) == aggregate_names.end()) &&
            (itNames->second.find("NAN") == std::string::npos) &&
            npointsCluster)
          {
          double clusterValue = itClusterValues->second;
          itCluster->second[itNames->second] = clusterValue/npointsCluster;
          }
        }
    } //  for (itClusterNames = ClusterNames.begin(); itClusterNames!= ClusterNames.end(); itClusterNames++)
  return 1;
}

void printFlat(std::ostream &ofs, bool printAllStatistics) {
  std::stringstream ids;
  std::stringstream measureNames;
  std::stringstream measureValues;
  std::map<std::string, std::string>::iterator itClusterNames;

  std::map<std::string, std::string> names = getMeasureNames();

  for (itClusterNames = ClusterNames.begin(); itClusterNames!= ClusterNames.end(); itClusterNames++)
    {
    // find if this cluster in any other cluster
    bool topCluster = true;
    std::map<std::string, std::string>::iterator itClusterNames1;
    for (itClusterNames1 = ClusterNames.begin(); itClusterNames1!= ClusterNames.end(); itClusterNames1++)
      {
      if (isInCluster(itClusterNames->second, itClusterNames1->first) )
        {
        topCluster = false;
        break;
        }
      }

    if (topCluster)
    {
      // print it
      printCluster(itClusterNames->first, Clusters, names,
                   ids, measureNames, measureValues);

      // print all children clusters
      for (itClusterNames1 = ClusterNames.begin(); itClusterNames1!= ClusterNames.end(); itClusterNames1++)
        {
        if (isInCluster(itClusterNames1->second, itClusterNames->first) )
          {
          printCluster(itClusterNames1->first, Clusters, names,
                       ids, measureNames, measureValues);
          // print all fibers in this clusters
          if (printAllStatistics)
            {
            std::map< std::string, std::map<std::string, double> >::iterator it;
            for(it = OutTable.begin(); it != OutTable.end(); it++)
              {
              if (isInCluster(it->first, itClusterNames1->first) )
                {
                  printCluster(it->first, OutTable, names,
                               ids, measureNames, measureValues);
                }
              } //for(it = OutTable.begin(); it != OutTable.end(); it++)
            }
          }
        }
      } // if (topCluster)
    } //   for (itClusterNames = ClusterNames.begin(); itClusterNames!= ClusterNames.end(); itClusterNames++)

  // if no clusters print fibers
  //if (ClusterNames.empty())
  //  {
    std::map< std::string, std::map<std::string, double> >::iterator it;
    for(it = OutTable.begin(); it != OutTable.end(); it++)
      {
      printCluster(it->first, OutTable, names,
                   ids, measureNames, measureValues);
      }
  //  }

  if (!ids.str().empty())
    {
    ofs << ids.str() << std::endl;
    ofs << measureNames.str() << std::endl;
    ofs << measureValues.str() << std::endl;
    }
}

void printCluster(const std::string &id,
                  std::map< std::string, std::map<std::string, double> > &output,
                  std::map<std::string, std::string> &names,
                  std::stringstream &ids,
                  std::stringstream &measureNames,
                  std::stringstream &measureValues)
{
  std::map< std::string, std::map<std::string, double> >::iterator it;
  std::map<std::string, double>::iterator it1;
  std::map<std::string, std::string>::iterator it2;

  it = output.find(id);
  if (it != output.end())
    {
    for (AggNames_t::iterator aggnames_iter  = aggregate_names.begin();
                              aggnames_iter != aggregate_names.end();
                              aggnames_iter++)
      {
      std::string aggname = *aggnames_iter;
      it2 = names.find(aggname);
      if (it2 != names.end())
        {
        it1 = it->second.find(aggname);
        if (it1 != it->second.end())
          {
          if (!ids.str().empty())
            {
            ids << SEPARATOR;
            measureNames << SEPARATOR;
            measureValues << SEPARATOR;
            }
          ids << id;
          measureNames << it2->second;
        }

        if (vtkMath::IsNan(it1->second))
          {
          measureValues << INVALID_NUMBER_PRINT;
          }
        else
          {
          measureValues << std::fixed << it1->second;
          }
        }
      }

    for (it2 = names.begin(); it2 != names.end(); it2++)
      {
      if (std::find(aggregate_names.begin(), aggregate_names.end(), it2->first) == aggregate_names.end())
        {
        it1 = it->second.find(it2->second);
        if (it1 != it->second.end())
          {
          if (!ids.str().empty())
            {
            ids <<  SEPARATOR;
            measureNames <<  SEPARATOR;
            measureValues <<  SEPARATOR;
            }
          ids << id;
          measureNames << it2->second;

          if (vtkMath::IsNan(it1->second))
            {
            measureValues << INVALID_NUMBER_PRINT;
            }
          else
            {
            measureValues << std::fixed << it1->second;
            }
          }
        }
      }
    }
}

int main( int argc, char * argv[] )
{
  itk::FloatingPointExceptions::Disable();

  PARSE_ARGS;

  std::ostringstream ofs;
  std::ofstream outputfilestream(outputFile.c_str());
  if (outputfilestream.fail())
    {
    std::cerr << "Unable to output file, or base path doesn't exist: " <<  outputFile << std::endl;
    return EXIT_FAILURE;
    }

  vtkNew<vtkPolyDataTensorToColor> math;
  std::vector<std::string> operations;
  operations.push_back(std::string("Trace"));
  operations.push_back(std::string("MeanDiffusivity"));
  operations.push_back(std::string("RelativeAnisotropy"));
  operations.push_back(std::string("FractionalAnisotropy"));
  operations.push_back(std::string("LinearMeasure"));
  operations.push_back(std::string("PlanarMeasure"));
  operations.push_back(std::string("SphericalMeasure"));
  operations.push_back(std::string("MinEigenvalue"));
  operations.push_back(std::string("MidEigenvalue"));
  operations.push_back(std::string("MaxEigenvalue"));
  std::string EMPTY_OP("");

  clamped_ops["FractionalAnisotropy"] = Range(0.0, 1.0);
  clamped_ops["RelativeAnisotropy"]   = Range(0.0, std::sqrt(2));
  clamped_ops["LinearMeasurement"]    = Range(0.0, 1.0);
  clamped_ops["PlanarMeasurement"]    = Range(0.0, 1.0);
  clamped_ops["SphericalMeasurement"] = Range(0.0, 1.0);

  aggregate_names.push_back("Num_Points");
  aggregate_names.push_back("Num_Fibers");
  aggregate_names.push_back("Mean_Length");
  aggregate_names.push_back(EXCLUDED_NUMBER_PRINT);

  if (inputType == std::string("Fibers_Hierarchy") )
    {
    // get the model hierarchy id from the scene file
    std::string::size_type loc;
    std::string            inputFilename;
    std::string            inputNodeID;

    std::string sceneFilename;
    std::string filename = FiberHierarchyNode[0];
    loc = filename.find_last_of("#");
    if (loc != std::string::npos)
      {
      sceneFilename = std::string(filename.begin(),
                                  filename.begin() + loc);
      loc++;

      inputNodeID = std::string(filename.begin() + loc, filename.end());
      }

    // check for the model mrml file
    if (sceneFilename.empty())
      {
      std::cerr << "No MRML scene file specified." << std::endl;
      return EXIT_FAILURE;
      }

    // get the directory of the scene file
    std::string rootDir
      = vtksys::SystemTools::GetParentDirectory(sceneFilename.c_str());

    vtkNew <vtkMRMLScene> modelScene;
    // load the scene that Slicer will re-read
    modelScene->SetURL(sceneFilename.c_str());

    modelScene->RegisterNodeClass(vtkNew<vtkMRMLSceneViewNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLSceneViewStorageNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLCommandLineModuleNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleLineDisplayNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleTubeDisplayNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleGlyphDisplayNode>().GetPointer());
    modelScene->RegisterNodeClass(vtkNew<vtkMRMLFiberBundleStorageNode>().GetPointer());

    // only try importing if the scene file exists
    if (vtksys::SystemTools::FileExists(sceneFilename.c_str()))
      {
      modelScene->Import();
      }
    else
      {
      std::cout << "Model scene file doesn't exist: " <<  sceneFilename.c_str() << std::endl;
      }

    if (inputType == std::string("Fibers_Hierarchy"))
      {
      // make sure we have a model hierarchy node
      vtkMRMLNode *node = modelScene->GetNodeByID(inputNodeID);
      vtkSmartPointer<vtkMRMLModelHierarchyNode> topHierNode =
         vtkMRMLModelHierarchyNode::SafeDownCast(node);
      if (!topHierNode)
        {
        std::cerr << "Model hierachy node doesn't exist: " <<  inputNodeID.c_str() << std::endl;
        return EXIT_FAILURE;
        }

      // get all the children nodes
      std::vector< vtkMRMLHierarchyNode *> allChildren;
      topHierNode->GetAllChildrenNodes(allChildren);

      // and loop over them
      for (unsigned int i = 0; i < allChildren.size(); ++i)
        {
        vtkMRMLDisplayableHierarchyNode *dispHierarchyNode = vtkMRMLDisplayableHierarchyNode::SafeDownCast(allChildren[i]);
        if (dispHierarchyNode)
          {
          // get any associated node
          vtkMRMLFiberBundleNode *fiberNode = vtkMRMLFiberBundleNode::SafeDownCast(
              dispHierarchyNode->GetAssociatedNode());

          if (fiberNode)
            {
            std::string id = std::string(fiberNode->GetName());
            // concat hierarchy path to id
            getPathFromParentToChild(topHierNode, dispHierarchyNode, id);
            vtkSmartPointer<vtkPolyData> data = fiberNode->GetPolyData();
            computeFiberStats(data, id);
            computeScalarMeasurements(data, id, EMPTY_OP, moreStatistics);
            computeAllTensorMeasurements(data, id, operations, moreStatistics);
            } // if (fiberNode)
          } // if (dispHierarchyNode)
        } // for (unsigned int i = 0; i < allChildren.size(); ++i)
      } // if (inputType == std::string("Fibers_Hierarchy"))
    } //if (inputType == ... || ... )
  else if (inputType == std::string("Fibers_File_Folder"))
    {
    // File based
    if (InputDirectory.size() == 0)
      {
      std::cerr << "Input directory doesn't exist: " << std::endl;
      return EXIT_FAILURE;
      }

    // override here, because we must always print individual statistics for folders
    printAllStatistics = true;

    vtkNew<vtkGlobFileNames> glob;
    glob->SetDirectory(InputDirectory.c_str());

    // Loop over .vtk files
    glob->AddFileNames("*.vtk");
    vtkStringArray *fileNamesVTK = glob->GetFileNames();
    for (vtkIdType i = 0; i < fileNamesVTK->GetNumberOfValues(); i++)
      {
      vtkNew<vtkPolyDataReader> reader;
      std::string fileName = fileNamesVTK->GetValue(i);
      reader->SetFileName(fileNamesVTK->GetValue(i));
      reader->Update();

      vtkSmartPointer<vtkPolyData> data = reader->GetOutput();
      computeFiberStats(data, fileName);
      computeScalarMeasurements(data, fileName, EMPTY_OP, moreStatistics);

      if( !setTensors(data) )
        {
        std::cout << argv[0] << " : No tensor data for file " << fileName << std::endl;
        continue;
        }

      computeAllTensorMeasurements(data, fileName, operations, moreStatistics);
      }

    // Loop over .vtp files
    glob->Reset();
    glob->AddFileNames("*.vtp");
    vtkStringArray *fileNamesVTP = glob->GetFileNames();
    for (vtkIdType i = 0; i < fileNamesVTP->GetNumberOfValues(); i++)
      {
      vtkNew<vtkXMLPolyDataReader> reader;
      std::string fileName = fileNamesVTP->GetValue(i);
      reader->SetFileName(fileName.c_str());
      reader->Update();

      vtkSmartPointer<vtkPolyData> data = reader->GetOutput();
      computeFiberStats(data, fileName);
      computeScalarMeasurements(data, fileName, EMPTY_OP, moreStatistics);
      if( !setTensors(data) )
        {
        std::cout << argv[0] << " : No tensor data for file " << fileName << std::endl;
        continue;
        }

      computeAllTensorMeasurements(data, fileName, operations, moreStatistics);
      }
    } //if (inputType == std::string("Fibers File Folder") )

  if (addClusters() == 0)
    {
    return EXIT_FAILURE;
    }

  if (outputSeparator == std::string("Tab"))
    {
    SEPARATOR = "\t";
    }
  else if (outputSeparator == std::string("Comma"))
    {
    SEPARATOR = ",";
    }
  else if (outputSeparator == std::string("Space"))
    {
    SEPARATOR = " ";
    }

  if (outputFormat == std::string("Row_Hierarchy"))
    {
    printFlat(ofs, printAllStatistics);
    }
  else
    {
    // By default we only print the cluster(s)
    if (printAllStatistics)
      printTable(ofs, true, OutTable);
    printTable(ofs, !printAllStatistics, Clusters);
    }

  ofs.flush();

  // print to stdout
  std::cout << ofs.str();
  // print to file
  outputfilestream << ofs.str();
  outputfilestream.flush();
  outputfilestream.close();

  return EXIT_SUCCESS;
}
