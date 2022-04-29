import numpy
import pickle
import sys
import time
import vtk
from vtk.util.numpy_support import vtk_to_numpy


pickledInput = sys.stdin.buffer.read()
input = pickle.loads(pickledInput)
filePath = input['filePath']

polyData = None
if filePath.endswith(".vtp"):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(filePath)
    reader.Update()
    polyData = reader.GetOutput()

"""
elif filePath.endswith(".vtk"):
    reader = vtk.vtkPolyDataReader()
    reader.ReadAllScalarsOn()
    reader.ReadAllVectorsOn()
    reader.ReadAllNormalsOn()
    reader.ReadAllTensorsOn()
    reader.ReadAllColorScalarsOn()
    reader.ReadAllTCoordsOn()
    reader.ReadAllFieldsOn()
    reader.Update()
    polyData = reader.GetOutput()
"""

def arrayFromLines(polyData):
    arrayVtk = polyData.GetLines().GetData()
    narray = vtk_to_numpy(arrayVtk)
    return narray

def arrayFromPoints(polyData):
    arrayVtk = polyData.GetPoints().GetData()
    narray = vtk_to_numpy(arrayVtk)
    return narray

output = {}
output['lines'] = arrayFromLines(polyData)
output['points'] = arrayFromPoints(polyData)

sys.stdout.buffer.write(pickle.dumps(output))
