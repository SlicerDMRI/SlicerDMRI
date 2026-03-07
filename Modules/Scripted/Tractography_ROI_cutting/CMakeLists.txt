cmake_minimum_required(VERSION 3.5)

project(Tractography_ROI_cutting)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/Tractography_ROI_cutting")
set(EXTENSION_CATEGORY "Cutting Module")
set(EXTENSION_CONTRIBUTORS "John Doe (AnyWare Corp.), Huan Luo (Tsinghua University)")
set(EXTENSION_DESCRIPTION "This is a module for tractography ROI cutting")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/Tractography_ROI_cutting.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/Tractography_ROI_cutting/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(Tractography_ROI_cutting)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
