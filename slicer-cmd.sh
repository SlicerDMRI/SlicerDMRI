#!/bin/zsh

# run this from within build tree

#SLICER_BUILD=/opt/s/Slicer-build
SLICER_BUILD=/opt/sr/Slicer-build

ANIMATOR=${HOME}/slicer/latest/SlicerAnimator/Animator
MULTI=${HOME}/slicer/latest/SlicerMultiMapper/MultiMapper
WEBSERVER=${HOME}/slicer/latest/SlicerWeb/WebServer


LIB_PATH=$(pwd)/inner-build/lib/Slicer-4.13

SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk ${SLICER_BUILD}/Slicer $* \
  --additional-module-paths \
    ${ANIMATOR} ${MULTI} ${WEBSERVER} \
    ${LIB_PATH}/cli-modules ${LIB_PATH}/qt-loadable-modules ${LIB_PATH}/qt-scripted-modules \
    |& tee /tmp/log

