# run this from within build tree

#SLICER_BUILD=/opt/s/Slicer-build
SLICER_BUILD=/opt/sr/Slicer-build

cmake \
	-DCMAKE_BUILD_TYPE:STRING=Debug \
	-DSlicer_DIR:PATH=${SLICER_BUILD} \
	-DCMAKE_OSX_DEPLOYMENT_TARGET:STRING=10.15 \
	../SlicerDMRI

