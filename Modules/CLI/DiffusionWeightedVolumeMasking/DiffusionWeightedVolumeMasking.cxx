// MRMLCore includes
#include <vtkMRMLNRRDStorageNode.h>

// vtkTeem includes
#include <Libs/vtkTeem/vtkTeemNRRDReader.h>
#include <Libs/vtkTeem/vtkTeemNRRDWriter.h>

// VTK includes
#include <vtkNew.h>
#include <vtkVersion.h>
#include <vtkPoints.h>
#include <vtkImageCast.h>
#include <vtkImageExtractComponents.h>
#include <vtkImageMedian3D.h>
#include <vtkImageSeedConnectivity.h>
#include <vtkImageThresholdConnectivity.h>
#include <vtkImageWeightedSum.h>

// ITK includes
#include <itkFloatingPointExceptions.h>
#include <itkBinaryFillholeImageFilter.h>
#include <itkBinaryThresholdImageFilter.h>
#include <itkConnectedComponentImageFilter.h>
#include <itkMedianImageFilter.h>
#include <itkOtsuMultipleThresholdsImageFilter.h>
#include <itkRelabelComponentImageFilter.h>
#include <itkSliceBySliceImageFilter.h>

// ITKVtkGlue
#include "itkVTKImageToImageFilter.h"
#include "itkImageToVTKImageFilter.h"

// XXX # Workaround bug in packaging of DCMTK 3.6.0 on Debian.
//     # See http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=637687
#ifdef HAVE_CONFIG_H
#undef HAVE_CONFIG_H
#endif

#include "DiffusionWeightedVolumeMaskingCLP.h"

int main( int argc, char * argv[] )
{

  itk::FloatingPointExceptions::Disable();

  PARSE_ARGS;
    {
    vtkNew<vtkTeemNRRDReader> reader;
    reader->SetFileName(inputVolume.c_str() );
    reader->Update();
    if( reader->GetReadStatus() )
      {
      std::cerr << argv[0] << ": Error reading Diffusion file" << std::endl;
      return EXIT_FAILURE;
      }

    vtkNew<vtkDoubleArray> bValues;
    vtkNew<vtkDoubleArray> grads;
    vtkNew<vtkMRMLNRRDStorageNode> helper;

    if( !helper->ParseDiffusionInformation(reader.GetPointer(), grads.GetPointer(), bValues.GetPointer()) )
      {
      std::cerr << argv[0] << ": Error parsing Diffusion information" << std::endl;
      return EXIT_FAILURE;
      }

    // Compute the mean baseline image
    vtkNew<vtkImageWeightedSum> imageWeightedSum;
    imageWeightedSum->NormalizeByWeightOn();

    int b0_count = 0;
    for( int bval_n = 0; bval_n < bValues->GetNumberOfTuples(); bval_n++ )
      {
      double bvalue = bValues->GetTuple1(bval_n);
      if( bvalue <= baselineBValueThreshold )
        {
        vtkNew<vtkImageExtractComponents> extractComponents;
        extractComponents->SetInputConnection(reader->GetOutputPort() );
        extractComponents->SetComponents(bval_n);
        extractComponents->Update();

        imageWeightedSum->AddInputConnection(extractComponents->GetOutputPort() );
        imageWeightedSum->SetWeight(b0_count++, 1.);
        }
      }
    imageWeightedSum->Update();

    if( b0_count == 0 )
      {
      std::cerr << argv[0] << ": Error parsing Diffusion information, no B0 images" << std::endl;
      return EXIT_FAILURE;
      }

    vtkNew<vtkImageCast> inputCast;
    inputCast->SetOutputScalarTypeToShort();
    inputCast->SetInputConnection(imageWeightedSum->GetOutputPort());
    inputCast->Update();

    typedef itk::Image<short, 3> ImageType;
    typedef itk::VTKImageToImageFilter<ImageType> VTKImageToImageType;

    VTKImageToImageType::Pointer vtkToITK = VTKImageToImageType::New();
    vtkToITK->SetInput(inputCast->GetOutput());

    typedef itk::MedianImageFilter<ImageType, ImageType> medianType;
    medianType::Pointer median = medianType::New();
    median->SetInput(vtkToITK->GetOutput());
    median->Update();

    typedef itk::OtsuMultipleThresholdsImageFilter<ImageType, ImageType> otsuType;
    otsuType::Pointer otsu = otsuType::New();
    otsu->SetInput(median->GetOutput());
    otsu->SetNumberOfThresholds(2);
    otsu->SetNumberOfHistogramBins(128);
    // To request old ITK4 bin behavior, if needed in future.
    //otsu->ReturnBinMidpointOn();
    otsu->Update();

    typedef itk::ConnectedComponentImageFilter<ImageType, ImageType> ccType;
    ccType::Pointer cc = ccType::New();
    cc->SetInput(otsu->GetOutput());
    cc->Update();

    typedef itk::RelabelComponentImageFilter<ImageType, ImageType> rlType;
    rlType::Pointer rl = rlType::New();
    rl->SetMinimumObjectSize(10000);
    rl->SetInput(cc->GetOutput());
    rl->Update();

    std::cout << "number of objects ";
    std::cout << rl->GetNumberOfObjects();

    typedef itk::BinaryThresholdImageFilter<ImageType, ImageType> threshType;
    threshType::Pointer thresh = threshType::New();
    thresh->SetLowerThreshold(1);
    thresh->SetUpperThreshold(1);
    thresh->SetOutsideValue(0);
    thresh->SetInsideValue(1);
    thresh->SetInput(rl->GetOutput());
    thresh->Update();

    typedef itk::Image<short, 2> BinImageType;
    typedef itk::BinaryFillholeImageFilter<BinImageType> binfillType;
    binfillType::Pointer binFiller = binfillType::New();
    binFiller->SetForegroundValue(1);

    typedef itk::SliceBySliceImageFilter<ImageType, ImageType> sbsType;
    sbsType::Pointer sbsFilter = sbsType::New();
    sbsFilter->SetFilter(binFiller);
    sbsFilter->SetInput(thresh->GetOutput());
    sbsFilter->Update();

    typedef itk::ImageToVTKImageFilter<ImageType> ITKOutType;
    ITKOutType::Pointer itkToVTK = ITKOutType::New();

    vtkNew<vtkImageCast> cast2;
    cast2->SetOutputScalarTypeToUnsignedChar();

    if( removeIslands )
      {
      itkToVTK->SetInput(sbsFilter->GetOutput());
      cast2->SetInputData(itkToVTK->GetOutput());
      }
    else
      {
      itkToVTK->SetInput(thresh->GetOutput());
      cast2->SetInputData(itkToVTK->GetOutput() );
      }
    itkToVTK->Update();

    vtkMatrix4x4* ijkToRasMatrix = reader->GetRasToIjkMatrix();
    ijkToRasMatrix->Invert();

    // Save baseline
    vtkNew<vtkTeemNRRDWriter> writer;
    writer->SetInputConnection(imageWeightedSum->GetOutputPort() );
    writer->SetFileName( outputBaseline.c_str() );
    writer->UseCompressionOn();
    writer->SetIJKToRASMatrix( ijkToRasMatrix );
    writer->Write();

    // Save mask
    vtkNew<vtkTeemNRRDWriter> writer2;
    writer2->SetInputConnection(cast2->GetOutputPort() );

    writer2->SetFileName( thresholdMask.c_str() );
    writer2->UseCompressionOn();
    writer2->SetIJKToRASMatrix( ijkToRasMatrix );
    writer2->Write();

    }

  return EXIT_SUCCESS;
}
