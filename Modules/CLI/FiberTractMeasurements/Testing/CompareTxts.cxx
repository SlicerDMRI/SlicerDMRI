#if defined(_MSC_VER)
#pragma warning ( disable : 4786 )
#endif

#ifdef __BORLANDC__
#define ITK_LEAN_AND_MEAN
#endif

// STD includes
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

int main( int argc, char * argv[] )
{
  if( argc < 3 )
    {
    std::cerr << "Both output and baseline txt files are required!" << std::endl;
    return EXIT_FAILURE;
    }

  std::string resultTxtPath = argv[1];
  std::string baselineTxtPath = argv[2];
  std::ifstream resultTxt(resultTxtPath);
  std::ifstream baselineTxt(baselineTxtPath);

  std::string resultLine;
  std::string baselineLine;
  std::string resultMeasure;
  std::string baselineMeasure;
  int c = 1;
  while (std::getline(resultTxt, resultLine) && std::getline(baselineTxt, baselineLine))
   {
      if (c > 1)
        {
          std::string delimiter = "fiber";
          resultMeasure = resultLine.substr(resultLine.find(delimiter));
          baselineMeasure = baselineLine.substr(baselineLine.find(delimiter));
        }
      else
        {
          resultMeasure = resultLine;
          baselineMeasure = baselineLine;
        }

      if (resultMeasure.compare(baselineMeasure) != 0)
        {
          std::cerr << "Measurements are not the same!" << std::endl;
          return EXIT_FAILURE;
        }

      c++;
   }

  std::cerr << "Same content!!!" << std::endl; 
  return EXIT_SUCCESS;
}





