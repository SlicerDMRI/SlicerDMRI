#!/usr/bin/env python-real

from __future__ import print_function
from __future__ import division
import sys
import argparse

import vtk, slicer, slicer.util, mrml
import numpy as np
from vtk.util import numpy_support

if sys.version_info[0] == 2:
  range = xrange

def runtests(testdata_path):
  # - runs this script again with test arguments and data
  # - validates the results

  import subprocess, tempfile, os
  from subprocess import PIPE
  import numpy.testing
  if sys.hexversion < 0x03030000:
    from pipes import quote as shlex_quote
  else:
    from shlex import quote as shlex_quote

  def run_extract_to_bvals(tempdata, args):
    """
    returns array of bvalues
    """
    print("ExtractDWIShell runtests, running: " + repr(args))

    proc = subprocess.Popen(args)
    proc.wait()

    if proc.returncode != 0:
      print("ExtractDWIShells failed!")
      sys.exit(-1)

    # load NRRD into Slicer
    sn = slicer.vtkMRMLNRRDStorageNode()
    sn.SetFileName(tempdata)
    dw_node = slicer.vtkMRMLDiffusionWeightedVolumeNode()
    sn.ReadData(dw_node)

    bvals = vtk.util.numpy_support.vtk_to_numpy(dw_node.GetBValues())
    return bvals

  def test1():
    testdata = os.path.join(testdata_path, "3x3x3_13_b1000_b3000.nrrd")
    tmp_nrrd_out = shlex_quote(tempfile.mkstemp(suffix=".nrrd")[1])

    call_args = ["--inputDWI", testdata,
                 "--outputDWI", tmp_nrrd_out,
                 "--bvalues", "0,1000",
                 "--tolerance", "50"]

    args = [sys.executable, sys.argv[0]] + call_args

    bvals = run_extract_to_bvals(tmp_nrrd_out, args)
    bvals_expected = np.array([0, 1000, 1000, 1000, 1000, 1000, 1000], dtype=np.float64)

    numpy.testing.assert_allclose(bvals, bvals_expected, rtol=1e-05)

  def test2_clamp_grads():
    """
    Test force-to-zero argument '--baseline_clamp'
    """

    testdata = os.path.join(testdata_path, "3x3x3_13_b1000_b3000.nrrd")
    tmp_nrrd_out = shlex_quote(tempfile.mkstemp(suffix=".nrrd")[1])

    call_args = ["--inputDWI", testdata,
                 "--outputDWI", tmp_nrrd_out,
                 "--bvalues", "0,1000,3000",
                 "--tolerance", "50",
                 "--baseline_clamp", "1005"]

    args = [sys.executable, sys.argv[0]] + call_args

    bvals = run_extract_to_bvals(tmp_nrrd_out, args)
    bvals_expected = np.array([0, 0,0,0,0,0,0, 3000,3000,3000,3000,3000,3000], dtype=np.float64)

    numpy.testing.assert_allclose(bvals, bvals_expected, rtol=1e-5)

  #############################################################################
  # end of test harness definitions
  try:
    test1()
    test2_clamp_grads()
    sys.exit(0) # success
  except:
    raise

  # default fail
  sys.exit(-1)


def main():
  if "--test" in sys.argv:
    runtests(sys.argv[2])
    sys.exit(-1) # default fail, runtests must exit(0)

  # handle arguments
  parser = argparse.ArgumentParser('Process args')
  parser.add_argument('--inputDWI', required=True, type=str)
  parser.add_argument('--bvalues', required=True, type=str)
  parser.add_argument('--tolerance', required=True, type=float)
  parser.add_argument('--outputDWI', required=True, type=str)
  parser.add_argument('--baseline_clamp', required=False, type=str)
  parser.add_argument('--test')
  args = parser.parse_args(sys.argv[1:])

  dwifile = args.inputDWI
  outfile = args.outputDWI
  target_bvals = [float(bvalue) for bvalue in args.bvalues.split(',')]
  if args.baseline_clamp:
    bval_clamp = float(args.baseline_clamp)
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

  print("  raw input gradients: ")
  print(grads_in)
  print("  raw input bvals: ")
  print(bvals_in)

  for (i, g) in enumerate(grads_in):
    norm = np.linalg.norm(g)
    if norm > 1e-6: grads_in[i] = g * 1/norm

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

  if args.baseline_clamp:
    for (i, bval) in enumerate(bvals_out):
      if bval < bval_clamp:
        print("  clamping baseline {} (gradient {}) to zero".format(bval, grads_out[i, :]))
        bvals_out[i] = 0
        grads_out[i, :] = np.array([0.,0.,0.])


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
  for i in range(0, attrs.GetNumberOfValues()):
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
  main()
