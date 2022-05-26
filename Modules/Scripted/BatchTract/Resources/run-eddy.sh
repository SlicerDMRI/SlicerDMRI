#!/bin/bash

# meant to be used on the freesurfer-synth vm with FSL installed
# This can be an example for other potential users.

SUBJPATH=/usr/local/data/eddy-subject/dcm2niix-nii
SUBJDWI=$(echo ${SUBJPATH}/*[0-9].nii.gz)
SUBJBASEPATH=${SUBJPATH}/$(basename ${SUBJDWI} .nii.gz)

echo SUBJPATH ${SUBJPATH}
echo SUBJDWI ${SUBJDWI}
echo SUBJBASEPATH ${SUBJBASEPATH}

echo "Running bet"
bet ${SUBJDWI} ${SUBJPATH}/bet-mask.nii.gz

echo "Running eddy"
eddy_openmp \
  --imain=${SUBJDWI} \
  --mask=${SUBJPATH}/bet-mask.nii.gz \
  --bvecs=${SUBJBASEPATH}.bvec \
  --bvals=${SUBJBASEPATH}.bval \
  --acqp=${SUBJPATH}/acqparams.txt \
  --index=${SUBJPATH}/index.txt \
  --out=${SUBJBASEPATH}-noeddy.nii.gz

