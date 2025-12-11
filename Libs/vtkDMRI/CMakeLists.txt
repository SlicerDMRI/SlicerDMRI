project(vtkDMRI)

# define export
add_definitions("-D${PROJECT_NAME}_EXPORTS")

set(BUILD_SHARED_LIBS ON)

set(configure_header_file vtkDMRIConfigure.h)
configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/${configure_header_file}.in
  ${CMAKE_CURRENT_BINARY_DIR}/${configure_header_file}
  )

find_package(Teem REQUIRED NO_MODULE)
include(${Teem_USE_FILE})

find_package(VTK REQUIRED)
if(${VTK_VERSION} VERSION_LESS "8.90.0")
  include(${VTK_USE_FILE})
endif()

# vtkTeem
find_package(vtkTeem REQUIRED)

# define export
#add_definitions("-D${PROJECT_NAME}_EXPORTS")

# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------
set(vtkDMRI_SRCS
  vtkTeemEstimateDiffusionTensor.cxx
  vtkPolyDataTensorToColor.cxx
  vtkPolyDataColorLinesByOrientation.cxx
  vtkBSplineInterpolateImageFunction.cxx
  vtkHyperPointandArray.cxx
  vtkHyperStreamlineDTMRI.cxx
  vtkHyperStreamlineTeem.cxx
  vtkPreciseHyperStreamline.cxx
  vtkPreciseHyperStreamlinePoints.cxx
  vtkSeedTracts.cxx
  vtkTensorImplicitFunctionToFunctionSet.cxx
  vtkTractographyPointAndArray.cxx
  vtkTensorMask.cxx
  vtkTensorRotate.cxx
  )

# Helper classes
set_source_files_properties(
  vtkHyperPointandArray.cxx
  vtkTractographyPointAndArray.cxx
  WRAP_EXCLUDE
  )

add_library(${PROJECT_NAME} SHARED
	${vtkDMRI_SRCS}
)

target_include_directories(${PROJECT_NAME}
    PUBLIC
	${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
	${Teem_INCLUDE_DIRS}
	${vtkTeem_INCLUDE_DIRS}
)

target_link_directories(${PROJECT_NAME}
	PUBLIC 
	${vtkTeem_LIB_DIR}
)

target_link_libraries(${PROJECT_NAME}
	PUBLIC
	teem
	vtkTeem
	${VTK_LIBRARIES}
)

# --------------------------------------------------------------------------
# Export target
# --------------------------------------------------------------------------
if(NOT DEFINED ${PROJECT_NAME}_EXPORT_FILE)
  # set(${PROJECT_NAME}_EXPORT_FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake)
  set(${PROJECT_NAME}_EXPORT_FILE ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake)
endif()
export(TARGETS ${PROJECT_NAME} APPEND FILE ${${PROJECT_NAME}_EXPORT_FILE})


