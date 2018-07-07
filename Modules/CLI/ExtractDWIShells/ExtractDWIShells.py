#!/usr/bin/env python-real

from __future__ import print_function
import sys
import argparse

import slicer, slicer.util, mrml
import numpy as np
import vtk
from vtk.util import numpy_support


def main(sysargs):
  # handle arguments
  parser = argparse.ArgumentParser('Process args')
  parser.add_argument('--inputDWI', required=True, type=str)
  parser.add_argument('--bvalues', required=True, type=str)
  parser.add_argument('--tolerance', required=True, type=float)
  parser.add_argument('--outputDWI', required=True, type=str)
  args = parser.parse_args(sysargs)

  dwifile = args.inputDWI
  outfile = args.outputDWI
  target_bvals = map(float, args.bvalues.split(','))
  bval_tolerance = args.tolerance

  # load data
  sn = slicer.vtkMRMLNRRDStorageNode()
  sn.SetFileName(dwifile)
  node_in = mrml.vtkMRMLDiffusionWeightedVolumeNode()
  print("loading: ", dwifile)
  sn.ReadData(node_in)
  dwi_in = slicer.util.arrayFromVolume(node_in)

  # sanity check that the last axis is volumes
  assert (node_in.GetNumberOfGradients() == dwi_in.shape[-1]), "Number of gradients do not match the size of last image axis!"

  bvals_in = numpy_support.vtk_to_numpy(node_in.GetBValues())
  grads_in = numpy_support.vtk_to_numpy(node_in.GetDiffusionGradients())
  for (i, g) in enumerate(grads_in):
    norm = np.linalg.norm(g)
    if norm > 1e-6: grads_in[i] = g * 1/norm

  print("  input gradients: ")
  print(grads_in)
  print("  input bvals: ")
  print(bvals_in)

  # select the indices to keep based on b value
  indices = []
  for (i, bval) in enumerate(bvals_in):
    for check_bval in target_bvals:
      if abs(bval - check_bval) < bval_tolerance:
        indices.append(i)

  print("selected indices: ", indices)

  # output shape: (3d_vol_shape..., num_indices)
  num_indices = len(indices)
  shape_out = dwi_in.shape[:-1] + (num_indices,)
  print("input shape: ", dwi_in.shape)
  print("output shape: ", shape_out)

  # construct output subset
  vol_out = np.zeros(shape_out, dtype=dwi_in.dtype)
  grads_out = np.zeros((num_indices, 3))
  bvals_out = np.zeros(num_indices)

  for (new_i, index) in enumerate(indices):
    vol_out[:,:,:,new_i] = dwi_in[:,:,:,index]
    grads_out[new_i, :]  = grads_in[index,:]
    bvals_out[new_i]     = bvals_in[index]

  print("selected bvals: ", bvals_out)
  print("  grads_out shape:  ", grads_out.shape)
  print("  vol_out shape:    ", vol_out.shape)
  print("  output gradients: ", grads_out)

  # write output
  sn_out = slicer.vtkMRMLNRRDStorageNode()
  sn_out.SetFileName(outfile)
  node_out = mrml.vtkMRMLDiffusionWeightedVolumeNode()

  # copy image information
  node_out.Copy(node_in)
  # reset the attribute dictionary, otherwise it will be transferred over
  attrs = vtk.vtkStringArray()
  node_out.GetAttributeNames(attrs)
  for i in xrange(0, attrs.GetNumberOfValues()):
    node_out.SetAttribute(attrs.GetValue(i), None)

  # reset the data array to force resizing, otherwise we will just keep the old data too
  node_out.SetAndObserveImageData(None)
  slicer.util.updateVolumeFromArray(node_out, vol_out)
  node_out.SetNumberOfGradients(num_indices)
  node_out.SetBValues(numpy_support.numpy_to_vtk(bvals_out))
  node_out.SetDiffusionGradients(numpy_support.numpy_to_vtk(grads_out))
  node_out.Modified()

  sn_out.WriteData(node_out)

if __name__ == '__main__':
  main(sys.argv[1:])
