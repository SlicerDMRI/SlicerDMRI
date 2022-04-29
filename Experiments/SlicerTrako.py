
"""

path = "/Users/pieper/slicer/latest/SlicerDMRI/Experiments/SlicerTrako.py"
exec(open(path).read())

"""


import importlib
import trako
trako = importlib.reload(trako)

tkoURL = "https://raw.githubusercontent.com/bostongfx/TRAKO/master/DATA/example.tko"

tkoFilePath = slicer.app.temporaryPath + "/example.tko"
slicer.util.downloadFile(tkoURL, tkoFilePath)

polyData = trako.gltfi2vtk.convert(tkoFilePath)


fiberBundleNode = slicer.vtkMRMLFiberBundleNode()
fiberBundleNode.SetName("trako")
fiberBundleNode.SetAndObservePolyData(polyData)
slicer.mrmlScene.AddNode(fiberBundleNode)
fiberBundleNode.CreateDefaultDisplayNodes()


fibercluster = trako.vtk2gltfi.convert(polyData)
tko = trako.vtk2gltfi.fibercluster2gltf(fibercluster, draco=True)
tko.save(slicer.app.temporaryPath + "/example-save.tko")



