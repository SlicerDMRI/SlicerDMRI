"""

path = "/Users/pieper/slicer/latest/SlicerDMRI/Experiments/ReaderProcesses.py"
exec(open(path).read())

"""

import glob
import os
import pickle
from vtk.util.numpy_support import vtk_to_numpy


import Processes


class ReaderProcess(Processes.Process):
  """This is an example of reading fiber bundles in a process"""

  def __init__(self, scriptPath, fiberNode, filePath):
    Processes.Process.__init__(self, scriptPath)
    self.fiberNode = fiberNode
    self.filePath = filePath

  def arrayFromModelPolyIds(self, modelNode):
    from vtk.util.numpy_support import vtk_to_numpy
    arrayVtk = modelNode.GetPolyData().GetPolys().GetData()
    narray = vtk_to_numpy(arrayVtk)
    return narray

  def prepareProcessInput(self):
    input = {}
    input['filePath'] = self.filePath
    return pickle.dumps(input)

  def useProcessOutput(self, processOutput):
    output = pickle.loads(processOutput)
    print(f"Process says: {len(output['lines'])}")
    print(f"Process says: {len(output['points'])}")

    # TODO: build a polydata from scratch based on arrays
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(vtk.vtkPoints())

    lines = vtk.vtkCellArray()
    ids = lines.GetData()
    ids.SetNumberOfValues(len(output['lines']))
    lineArray = vtk_to_numpy(ids)
    lineArray[:] = output['lines']
    polyData.SetLines(lines)

    polyData.GetPoints().GetData().SetNumberOfTuples(len(output['points']))
    pointArray = vtk_to_numpy(polyData.GetPoints().GetData())
    pointArray[:] = output['points']
    polyData.GetPoints().GetData().Modified()
    polyData.GetPoints().Modified()

    self.fiberNode.SetAndObservePolyData(polyData)


    """
    vertexArray = slicer.util.arrayFromModelPoints(self.modelNode)
    vertexArray[:] = output['vertexArray']
    slicer.util.arrayFromModelPointsModified(self.modelNode)
    """



def onProcessesCompleted(testClass):
    print("All fibers loaded")

logic = Processes.ProcessesLogic(completedCallback=lambda : onProcessesCompleted(self))


thisPath = qt.QFileInfo(__file__).path()
#scriptPath = os.path.join(thisPath, "fiberReader.slicer.py")
scriptPath = "/Users/pieper/slicer/latest/SlicerDMRI/Experiments/fiberReader.slicer.py"

tractDirectory = "/opt/data/SlicerDMRI/ABCD-Harmonization/WMA/tar_sub-NDARINV0UA196B6_ses_newPara/AnatomicalTracts"
for filePath in glob.glob(tractDirectory+"/*")[:1]:
    fiberNode = slicer.vtkMRMLFiberBundleNode()
    slicer.mrmlScene.AddNode(fiberNode)
    fiberNode.CreateDefaultDisplayNodes()

    readerProcess = ReaderProcess(scriptPath, fiberNode, filePath)
    logic.addProcess(readerProcess)

logic.run()

