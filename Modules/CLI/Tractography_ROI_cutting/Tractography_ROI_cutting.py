#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 17:28:30 2018

@author: lh
"""

import argparse
import os, vtk
import slicer, mrml, slicer.util, numpy

def main():
    parser = argparse.ArgumentParser(
        description="Remove endpoints that are outside the provided brain mask or freesurfer label",
        epilog="Written by Huan Luo and Fan Zhang")
    parser.add_argument("-v", "--version",
        action="version", default=argparse.SUPPRESS,
        version='1.0',
        help="Show program's version number and exit")
    
    parser.add_argument(
        'inputfiber',
        help='Path of input VTK file that are going to be cutted, e.g. /Users/Desktop/xxx.vtk')
    parser.add_argument(
        'label_map_file',
        help='Label map file in nifti (default for freesurfer result), e.g. /Users/Desktop/xxx.nii.gz')
    parser.add_argument(
        'outputDirectory',
        help='Directory of cutting results.')
    parser.add_argument(
        'labelValue1', type=int,
        help='labelValue1 of ROI, e.g. 1')
    parser.add_argument(
        'labelValue2', type=int,
        help='labelValue2 of ROI(different from labelValue1)')
    parser.add_argument(
        'samplingDistance', type=float,
        help='simplingDistance e.g. 0.1')
    
    args = parser.parse_args()  
    
    if not os.path.exists(args.inputfiber):
        print "Error: Input", args.inputfiber, "does not exist."
        exit()
    else:
        basename, extension = os.path.splitext(args.inputfiber)
        if(extension != '.vtk'):
            print 'Cannot recognize model file format'
            exit()
    
    outdir = os.path.abspath(args.outputDirectory)
    if not os.path.exists(args.outputDirectory):
        print "Output directory", args.outputDirectory, "does not exist, creating it."
        os.makedirs(outdir)
    
    if not os.path.exists(args.label_map_file):
        print "Label map", args.label_map_file, "does not exist."
        exit()

    # load region label map file
    labelmapfile =  args.label_map_file
    sn = slicer.vtkMRMLNRRDStorageNode()
    sn.SetFileName(labelmapfile)
    node_in = mrml.vtkMRMLLabelMapVolumeNode()
    sn.ReadData(node_in)
    labelArray = slicer.util.arrayFromVolume(node_in)
    
    rasToIJK = vtk.vtkMatrix4x4()
    node_in.GetRASToIJKMatrix(rasToIJK)
    
    #load input fiber bundle
    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(args.inputfiber)
    reader.Update()
    inpd = reader.GetOutput()
    del reader
    
    inpoints = inpd.GetPoints()
    inpointdata = inpd.GetPointData()
    incelldata = inpd.GetCellData()
    
    #creat output fiber bundle
    outpd = vtk.vtkPolyData()
    outlines = vtk.vtkCellArray()
    outpoints = vtk.vtkPoints()
    
    resampler = vtk.vtkPolyDataPointSampler()
    resampler.GenerateEdgePointsOn()
    resampler.GenerateVertexPointsOff()
    resampler.GenerateInteriorPointsOff()
    resampler.GenerateVerticesOff()
    resampler.SetDistance(args.samplingDistance)
    
    if incelldata.GetNumberOfArrays() > 0:
      cell_data_array_indices = range(incelldata.GetNumberOfArrays())
      for idx in cell_data_array_indices:
          array = incelldata.GetArray(idx)
          dtype = array.GetDataType()

          if dtype == 10:
             out_array = vtk.vtkFloatArray()
          elif dtype == 6:
             out_array = vtk.vtkIntArray()
          elif dtype == 3:
             out_array = vtk.vtkUnsignedCharArray()
          else:
             out_array = vtk.vtkFloatArray()
          out_array.SetNumberOfComponents(array.GetNumberOfComponents())
          out_array.SetName(array.GetName())

          outpd.GetCellData().AddArray(out_array)

    if inpointdata.GetNumberOfArrays() > 0:
        point_data_array_indices = range(inpointdata.GetNumberOfArrays())
        for idx in point_data_array_indices:
            array = inpointdata.GetArray(idx)
            out_array = vtk.vtkFloatArray()
            out_array.SetNumberOfComponents(array.GetNumberOfComponents())
            out_array.SetName(array.GetName())

            outpd.GetPointData().AddArray(out_array)

    inpd.GetLines().InitTraversal()
    outlines.InitTraversal()
    
    for lidx in range(0, inpd.GetNumberOfLines()):
        ptids = vtk.vtkIdList()
        inpd.GetLines().GetNextCell(ptids)

        cellptids = vtk.vtkIdList()

        switch1 = 0
        switch2 = 0
        
        #load the information after resample
        tmpPd = vtk.vtkPolyData()
        tmpPoints = vtk.vtkPoints()
        tmpCellPtIds = vtk.vtkIdList()
        tmpLines =  vtk.vtkCellArray()
        
        for pidx in range(0, ptids.GetNumberOfIds()):
            point = inpoints.GetPoint(ptids.GetId(pidx))
            idx_ = tmpPoints.InsertNextPoint(point)
            tmpCellPtIds.InsertNextId(idx_)
            
        tmpLines.InsertNextCell(tmpCellPtIds)

        tmpPd.SetLines(tmpLines)
        tmpPd.SetPoints(tmpPoints)
        
        if (vtk.vtkVersion().GetVTKMajorVersion() >= 6.0):
            resampler.SetInputData(tmpPd)
        else:
            resampler.SetInput(tmpPd)

        resampler.Update()

        sampledCellPts = resampler.GetOutput().GetPoints()
        sampledNpts = resampler.GetOutput().GetNumberOfPoints()
        
        #judge weather the fiber go through both ROI
        for pidx in range(0, sampledNpts):
            point = sampledCellPts.GetPoint(pidx)
            point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
            ijk = [int(round(element)) for element in point_ijk]
            ijk.reverse()
            if labelArray[tuple(ijk)] == args.labelValue1:
              switch1 = 1
            if labelArray[tuple(ijk)] == args.labelValue2:
              switch2 = 1

        #In each fiber that needs to be kept, find the first and the last point that need to kept in the resampled data.
        if (switch1 ==1 and switch2 == 1):
          for pidx in range(0, sampledNpts):
            point = sampledCellPts.GetPoint(pidx)
            point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
            ijk = [int(round(element)) for element in point_ijk]
            ijk.reverse()
            if (labelArray[tuple(ijk)] == args.labelValue1 or labelArray[tuple(ijk)] == args.labelValue2):
              line_RASbegin = point
              break

          for pidx in range(sampledNpts - 1, -1, -1):
            point = inpoints.GetPoint(pidx)
            point_ijk = rasToIJK.MultiplyPoint(point+(1,))[:3]
            ijk = [int(round(element)) for element in point_ijk]
            ijk.reverse()
            if (labelArray[tuple(ijk)] == args.labelValue1 or labelArray[tuple(ijk)] == args.labelValue2):
              line_RASend = pidx
              break
          
          origin_RAS = numpy.zeros([ptids.GetNumberOfIds(),3])
          for pidx in range(0, ptids.GetNumberOfIds()):
              origin_RAS[pidx, :] = inpoints.GetPoint(ptids.GetId(pidx))
        
          distance_square1 = numpy.sum(numpy.asarray(line_RASbegin - origin_RAS)**2, axis=1)
          distance_square2 = numpy.sum(numpy.asarray(line_RASend - origin_RAS)**2, axis=1)

          #In the original data, find the two points which are cloest to the 
          #first and the end point found in resampled data. Then keep the
          #points between them.
          line_begin = numpy.argmin(distance_square1)
          line_end = numpy.argmin(distance_square2)


          for pidx in range(0, ptids.GetNumberOfIds()):
            point = inpoints.GetPoint(ptids.GetId(pidx))
            if (pidx >= line_begin and pidx <= line_end):
              idx_ = outpoints.InsertNextPoint(point)
              cellptids.InsertNextId(idx_)
              for idx in point_data_array_indices:
                array = inpointdata.GetArray(idx)
                outpd.GetPointData().GetArray(idx).InsertNextTuple(array.GetTuple(ptids.GetId(pidx)))

          outlines.InsertNextCell(cellptids)

        if incelldata.GetNumberOfArrays() > 0:
          for idx in cell_data_array_indices:
            array = incelldata.GetArray(idx)
            out_array = outpd.GetCellData().GetArray(idx)
            out_array.InsertNextTuple(array.GetTuple(lidx))
    outpd.SetLines(outlines)
    outpd.SetPoints(outpoints)
    
    cluster_file_name = os.path.split(args.inputfiber)[1]
    basename, extension = os.path.splitext(cluster_file_name)
    output_file_name = basename + '_cut_' + str(args.labelValue1) + '_' + str(args.labelValue2) + '.vtk'
    
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileTypeToBinary()
    writer.SetFileName(os.path.join(outdir, output_file_name))
    writer.SetInputData(outpd)
    writer.Update()
    del writer
    print 'Line before removal:', inpd.GetNumberOfLines(), ', after removal:', outpd.GetNumberOfLines()

if __name__ == '__main__':
  main()
