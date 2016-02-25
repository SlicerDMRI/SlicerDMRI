#include <iostream>
#include "itkTestMain.h"

void RegisterTests()
{
  REGISTER_TEST(FiberTractMeasurementsTest);
}

#undef main
#define main FiberTractMeasurementsTest
#include "../FiberTractMeasurements.cxx"
