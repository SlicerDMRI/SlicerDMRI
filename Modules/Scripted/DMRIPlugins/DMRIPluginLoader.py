import os
import vtk, qt, ctk, slicer
import warnings
from slicer.ScriptedLoadableModule import *

from SubjectHierarchyPlugins import AbstractScriptedSubjectHierarchyPlugin

class DMRIPluginLoader(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "DMRI Subject Hierarchy Plugin Loader"
        parent.categories = [""]
        parent.contributors = ["Steve Pieper, Isomics, Inc."]
        parent.helpText = ""
        parent.hidden = not slicer.util.settingsValue('Developer/DeveloperMode', False, converter=slicer.util.toBool)

        #
        # register subject hierarchy plugin once app is initialized
        #
        def onStartupCompleted():
            import SubjectHierarchyPlugins
            from DMRIPluginLoader import DMRIPluginLoaderSubjectHierarchyPlugin
            scriptedPlugin = slicer.qSlicerSubjectHierarchyScriptedPlugin(None)
            scriptedPlugin.setPythonSource(DMRIPluginLoaderSubjectHierarchyPlugin.filePath)
            print('DMRIPluginLoaderWidget loaded')
        slicer.app.connect("startupCompleted()", onStartupCompleted)


class DMRIPluginLoaderWidget(ScriptedLoadableModuleWidget):
  """
  dummy module widget to allow reloading in developer mode
  """
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

# debug helper
def whoami(  ):
    import sys
    return "DMRI: " + sys._getframe(1).f_code.co_name


class DMRIPluginLoaderSubjectHierarchyPlugin(AbstractScriptedSubjectHierarchyPlugin):
  """ Scripted subject hierarchy plugin for the DMRI extension.
  The seemingly redundant name of this class is because the SubjectHierarchyPlugin code
  looks for a class which is the module name plus the postfix SubjectHierarchyPlugin.
  By following this convention we can have the full plugin in one source file.
  """

  # Necessary static member to be able to set python source to scripted subject hierarchy plugin
  filePath = __file__

  def __init__(self, scriptedPlugin):
    print(whoami())
    print('DMRIPluginLoaderWidget calling superclass')
    AbstractScriptedSubjectHierarchyPlugin.__init__(self, scriptedPlugin)

    self.viewActions = [None] * 4
    for index in range(len(self.viewActions)):
        print('DMRIPluginLoaderWidget creating action')
        self.viewActions[index] = qt.QAction(f"FiberBundle {index}...", scriptedPlugin)
        self.viewActions[index].objectName = f"ViewAction{index}"
        print(f'DMRIPluginLoaderWidget connecting action {index}')
        self.viewActions[index].connect("triggered()", lambda i=index : self.onViewAction(i))

    self.contextSubMenu = qt.QMenu("Plugin Menu")
    self.contextSubMenu.addAction("test action")
    self.viewActions[0].setMenu(self.contextSubMenu)

    self.displayActions = FiberBundleDisplayActions(scriptedPlugin)

    print('DMRIPluginLoaderWidget created')

  def onViewAction(self, index):
    print(whoami())
    print(f"VIEW ACTION {index}")

  def canAddNodeToSubjectHierarchy(self, node, parentItemID):
    print(whoami(), node.GetName(), parentItemID)
    # for now, DMRI does not have designated child nodes,
    # but it could, for example, create a fiducial node for seeding
    # in this method and the one below.
    #
    # This plugin cannot own any items (it's not a role but a function plugin),
    # but the it can be decided the following way:
    # if node is not None and node.IsA("vtkMRMLMyNode"):
    #   return 1.0
    return 0.0

  #
  # checks if this plugin can "own" an item - we want to own fiber bundles
  #
  def canOwnSubjectHierarchyItem(self, itemID):
    print(whoami(), itemID)
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shNode = pluginHandlerSingleton.subjectHierarchyNode()
    associatedNode = shNode.GetItemDataNode(itemID)
    if associatedNode is not None and associatedNode.IsA("vtkMRMLFiberBundleNode"):
      print(f'can own {associatedNode.GetName()}')
      return 1.0
    return 0.0

  def roleForPlugin(self):
    # As this plugin cannot own any items, it doesn't have a role either
    print(whoami())
    return "N/A"

  def helpText(self):
    print(whoami())
    return ("""
        <p style=" margin-top:4px; margin-bottom:1px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
          <span style=" font-family:'sans-serif'; font-size:9pt; font-weight:600; color:#000000;">
              DMRI module subject hierarchy help text
          </span>
        </p>
        <p style=" margin-top:0px; margin-bottom:11px; margin-left:26px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">
          <span style=" font-family:'sans-serif'; font-size:9pt; color:#000000;">
            This is how you can add help text to the subject hierarchy module help box via a python scripted plugin.
      </span>
      </p>\n""")
    return ""

  def icon(self, itemID):
    # As this plugin cannot own any items, it doesn't have an icon eitherimport os
    import os
    print(whoami(), itemID)
    iconPath = os.path.join(os.path.dirname(__file__), 'Resources/FiberBundle-icon.png')
    if self.canOwnSubjectHierarchyItem(itemID) > 0.0 and os.path.exists(iconPath):
      return qt.QIcon(iconPath)
    return qt.QIcon()

  def visibilityIcon(self, visible):
    print(whoami(), visible)
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    return pluginHandlerSingleton.pluginByName('Default').visibilityIcon(visible)

  def editProperties(self, itemID):
    print(whoami(), itemID)
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    pluginHandlerSingleton.pluginByName('Default').editProperties(itemID)

  def sceneContextMenuActions(self):
    """ this gets when clicking on the background of the tree, not an item"""
    print(whoami(), "action 1")
    return [self.viewActions[1]]

  #
  # item context menus are what happens when you right click on a selected line
  #
  def itemContextMenuActions(self):
    """the actions that could be shown for any of this plugins items"""
    print(whoami(), "action 0")
    return [self.viewActions[0]]

  def showContextMenuActionsForItem(self, itemID):
    """Set actions visible that are valid for this itemID"""
    print(whoami(), itemID)

    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shNode = pluginHandlerSingleton.subjectHierarchyNode()
    self.viewActions[0].visible = True
    self.viewActions[0].enabled = False
    self.contextSubMenu.clear()
    associatedNode = shNode.GetItemDataNode(itemID)
    print("associatedNode", associatedNode)
    if associatedNode is not None and associatedNode.IsA("vtkMRMLFiberBundleNode"):
        self.viewActions[0].enabled = True
        print(f"I got {associatedNode.GetName()}!")
        self.displayActions.selectedFiberBundle = associatedNode
        for action in self.displayActions.actions:
          self.contextSubMenu.addAction(action)

  def export(self, node, writeType):
    qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(),
            "Export As...", node.GetName(), writeType)

  def showVisibilityMenuActionsForItem(self, itemID):
    print(whoami(), itemID)
    self.viewActions[1].visible = True
    for viewAction in self.viewActions:
        viewAction.visible = True

  #
  # view - means slice or threeD views
  #
  def viewContextMenuActions(self):
    print(whoami(), "action 2")
    print("returning [self.viewActions[2]]")
    return [self.viewActions[2]]

  def showViewContextMenuActionsForItem(self, itemID, eventData=None):
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shNode = pluginHandlerSingleton.subjectHierarchyNode()
    associatedNode = shNode.GetItemDataNode(itemID)
    print(whoami(), itemID, associatedNode.GetID(), eventData)
    viewNode = slicer.mrmlScene.GetNodeByID(eventData['ViewNodeID'])
    if (associatedNode is not None and
        associatedNode.IsA("vtkMRMLFiberBundleNode")):
      pluginHandler = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
      pluginLogic = pluginHandler.pluginLogic()
      menuActions = list(pluginLogic.availableViewMenuActionNames())
      for viewAction in self.viewActions:
        menuActions.append(viewAction.objectName)
        viewAction.visible = True
      pluginLogic.setDisplayedViewMenuActionNames(menuActions)

  #
  # only used for subject hierarchy containers
  #
  def tooltip(self, itemID):
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shNode = pluginHandlerSingleton.subjectHierarchyNode()
    associatedNode = shNode.GetItemDataNode(itemID)
    if associatedNode is not None and associatedNode.IsA("vtkMRMLFiberBundleNode"):
      numberOfCells = "no"
      if associatedNode.GetPolyData():
        numberOfCells = associatedNode.GetPolyData().GetNumberOfCells()
      return f"Fiber bundle with {numberOfCells} fibers"

  def setDisplayVisibility(self, itemID, visible):
    print(whoami())
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    shNode = pluginHandlerSingleton.subjectHierarchyNode()
    associatedNode = shNode.GetItemDataNode(itemID)
    if associatedNode is not None and associatedNode.IsA("vtkMRMLFiberBundleNode"):
      print(f"I got {associatedNode.GetName()}!")
    else:
      print(f"I got nothing")
      pluginHandlerSingleton.pluginByName('Default').setDisplayVisibility(itemID, visible)

  def getDisplayVisibility(self, itemID):
    print(whoami())
    pluginHandlerSingleton = slicer.qSlicerSubjectHierarchyPluginHandler.instance()
    return pluginHandlerSingleton.pluginByName('Default').getDisplayVisibility(itemID)

  def visibilityContextMenuActions(self):
    print(whoami())
    return [self.viewActions[1]]


class FiberBundleDisplayActions:
  """Collection of QActions and corresponding display mode methods"""

  def __init__(self, scriptedPlugin):
    self.selectedFiberBundle = None

    self.displayMappings = [
        ["Show only this FiberBundle", self.showOnly],
        ["Show only this FiberBundle in tract", self.showOnlyInTract],
        ["Show all FiberBundles", self.showAll],
        ["Show all FiberBundles in tract", self.showAllInTract],
        ["Show FiberBundle as tubes", self.showAsTubes],
        ["Show Tract as tubes", self.showTractAsTubes],
        ["Show All as tubes", self.showAllAsTubes],
        ["Show FiberBundle by MeanOrientation", self.showByMeanOrientation],
        ["Show FiberBundle by LocalOrientation", self.showByLocalOrientation],
        ["Show FiberBundle by SolidColor", self.showByLocalOrientation],
        ["Show Tract by MeanOrientation", self.showTractByMeanOrientation],
        ["Show Tract by LocalOrientation", self.showTractByLocalOrientation],
        ["Show Tract by SolidColor", self.showTractByLocalOrientation],
        ["Show All by MeanOrientation", self.showTractByMeanOrientation],
        ["Show All by LocalOrientation", self.showTractByLocalOrientation],
        ["Show All by SolidColor", self.showTractByLocalOrientation],
    ]

    self.actions = []
    for text,method in self.displayMappings:
      action = qt.QAction(text, scriptedPlugin)
      action.objectName = text
      action.connect("triggered()", method)
      self.actions.append(action)

  @staticmethod
  def generateFiberBundleDisplayNodes():
    fibers = slicer.util.getNodes("vtkMRMLFiberBundleNode*")
    for node in fibers.values():
      displayNodeCount = node.GetNumberOfDisplayNodes()
      for displayNodeIndex in range(displayNodeCount):
        displayNode = node.GetNthDisplayNode(displayNodeIndex)
        yield node,displayNode

  def showOnly(self,displayClass="vtkMRMLFiberBundleLineDisplayNode"):
    for fiberBundleNode,fiberBundleDisplayNode in self.generateFiberBundleDisplayNodes():
      fiberBundleDisplayNode.SetVisibility(False)
      if (fiberBundleDisplayNode.IsA(displayClass) 
          and fiberBundleNode == self.selectedFiberBundle):
        fiberBundleDisplayNode.SetVisibility(True)

  def showOnlyInTract(self):
    pass

  def showAllInTract(self):
    pass

  def showAll(self,displayClass="vtkMRMLFiberBundleLineDisplayNode"):
    for fiberBundleNode,fiberBundleDisplayNode in self.generateFiberBundleDisplayNodes():
      fiberBundleDisplayNode.SetVisibility(False)
      if fiberBundleDisplayNode.IsA(displayClass):
        fiberBundleDisplayNode.SetVisibility(True)

  def showAsTubes(self):
    self.showOnly(displayClass="vtkMRMLFiberBundleTubeDisplayNode")

  def showTractAsTubes(self):
    pass

  def showAllAsTubes(self):
    self.showAll(displayClass="vtkMRMLFiberBundleTubeDisplayNode")

  def showByMeanOrientation(self):
    pass

  def showByLocalOrientation(self):
    pass

  def showSolidColor(self):
    pass

  def showTractByMeanOrientation(self):
    pass

  def showTractByLocalOrientation(self):
    pass

  def showTractSolidColor(self):
    pass

  def showAllByMeanOrientation(self):
    pass

  def showAllByLocalOrientation(self):
    pass

  def showAllSolidColor(self):
    pass

