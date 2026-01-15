#if defined(_MSC_VER)
#pragma warning ( disable : 4786 )
#endif

#ifdef __BORLANDC__
#define ITK_LEAN_AND_MEAN
#endif

// STD includes
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>


namespace {

bool isFileEmpty(const std::string& fname)
{
  if (std::filesystem::file_size(fname) == 0)
    {
      std::cerr << fname << " is empty." << std::endl;
      return true;
    }

  return false;
}

bool doesFileExist(const std::string& fname)
{
  if (!std::filesystem::exists(fname))
    {
      std::cerr << fname << " does not exist." << std::endl;
      return false;
    }

  return true;
}

}

int main( int argc, char * argv[] )
{
  if( argc < 3 )
    {
    std::cerr << "Both output and baseline txt files are required!" << std::endl;
    return EXIT_FAILURE;
    }

  std::string resultTxtPath = argv[1];
  std::string baselineTxtPath = argv[2];
  std::ifstream resultTxt(resultTxtPath.c_str());
  std::ifstream baselineTxt(baselineTxtPath.c_str());

  auto fileExists = doesFileExist(baselineTxtPath);
  fileExists &= doesFileExist(resultTxtPath);
  if (!fileExists)
    {
      std::cerr << "Test failed." << std::endl;
      return EXIT_FAILURE;
    }

  auto isEmpty = isFileEmpty(baselineTxtPath);
  isEmpty += isFileEmpty(resultTxtPath);
  if (isEmpty)
    {
      std::cerr << "Test failed." << std::endl;
      return EXIT_FAILURE;
    }

  int diff_count = 0;

  int testResult = EXIT_FAILURE;

  if (resultTxt.is_open() && baselineTxt.is_open())
    {
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
              std::cerr << "Expected: " << baselineMeasure << std::endl;
              std::cerr << "Obtained: " << resultMeasure << std::endl;
              diff_count += 1;
            }

          c++;
        }

      resultTxt.close();
      baselineTxt.close();

      if (diff_count > 0)
        {
          std::cerr << "Test failed." << std::endl;
          testResult = EXIT_FAILURE;
        }
      else
        {
          std::cerr << "Same content!!!" << std::endl;
          testResult = EXIT_SUCCESS;
        }
    }
  else
    {
      std::cerr << "Could not open file." << std::endl;
      std::cerr << "Test failed." << std::endl;
      testResult = EXIT_FAILURE;
    }


  return testResult;
}





