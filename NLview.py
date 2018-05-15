import sys
import os
from optparse import OptionParser
import re
from PySide import QtCore, QtGui
from NLView_gui import Ui_mWinNLView

if sys.version_info[:3] < (2,7,5): sys.exit("-E-: Require Python 2.7.5 atleast!")

class NLViewC_subCkt(object): # subckt class - represents each hierarchy of netlist
  def __init__(self, name, ports, xports={}, hier={}):
    self.name = name     # subckt name
    self.ports = ports   # ports
    self.xports = {}     # x mapped ports hash
    self.hier = {}       # hierarchy hash

class NLViewC_NetlistViewer(QtGui.QMainWindow): # qt application class
  def __init__(self, parent=None):
    self.__version__ = "NLView"
    super(NLViewC_NetlistViewer, self).__init__(parent)
    self.ui = Ui_mWinNLView()
    self.ui.setupUi(self)

    # configuring some gui options
    self.ui.tableWidgetPinMap.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
    self.ui.treeViewCDLTree.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

    # data
    self.treeViewCDLTreeModel = None # standard model used to model the treeview
    self.subCktHierData = {} # hierarchical database of cdl data
    self.selectedTopCellItem = None # selectitem on the hierarchy tree
    self.selectedTopCell = None # selected top cell on the hierarchy tree
    self.selectedSubCkts = [] # selected subcircuits on the listwidget
    self.selectedPort = None # selected ports on the listwidget
    self.traceNet = None # trace this net

    # some inits based on command line arguments
    parser = OptionParser()
    parser.add_option("-c", "--topCell", dest = "topCellName", help = "cell name(required)")
    parser.add_option("-n", "--netlist", dest = "cdlNetlist", help = "cdl netlist(required)")
    (self.options, args) = parser.parse_args()
    sys.exit("Missing mandatory -c/--topCell argument!") if self.options.topCellName is None else ""
    sys.exit("No such cdl file!") if not os.path.isfile(self.options.cdlNetlist) else ""
    sys.exit("Missing mandatory -n/--netlist argument!") if self.options.cdlNetlist is None else ""

    # parsing the cdl and pushing to the tree view
    self.NLViewM_parseCDL()
    self.NLViewM_populateCDLTreeView()

    # appending the cell name to the title
    self.setWindowTitle(self.__version__ + ": " + self.options.cdlNetlist)

    # connects
    selmodel = self.ui.treeViewCDLTree.selectionModel()
    selmodel.selectionChanged.connect(self.NLViewM_treeViewCDLTree_SelectionChanged)
    self.ui.listWidgetSubCircuits.itemSelectionChanged.connect( \
      self.NLViewM_listWidgetSubCircuits_SelectionChanged)
    self.ui.listWidgetPorts.itemSelectionChanged.connect( \
      self.NLViewM_listWidgetPorts_SelectionChanged)

    self.ui.lineEditFilterSubCircuits.textChanged.connect( \
      self.NLViewM_lineEditFilterSubCircuits_Changed)
    self.ui.lineEditFilterPorts.textChanged.connect( \
      self.NLViewM_lineEditFilterPorts_Changed)

    self.ui.listWidgetSubCircuits.itemDoubleClicked.connect( \
      self.NLViewM_listWidgetSubCircuits_DoubleClick)
    self.ui.listWidgetPorts.itemDoubleClicked.connect( \
      self.NLViewM_listWidgetPorts_DoubleClick)

    self.ui.listWidgetPorts.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
    self.actionTraceNet = QtGui.QAction("Trace Net", self.ui.listWidgetPorts)
    self.ui.listWidgetPorts.addAction(self.actionTraceNet)
    self.connect(self.actionTraceNet, QtCore.SIGNAL("triggered()"), \
      self.NLViewM_listWidgetPorts_actionTraceNet)

    self.ui.pushButtonReloadNetlist.clicked.connect( \
      self.NLViewM_pushButtonReloadNetlist_Clicker)
    self.ui.checkBoxShowInternalNets.stateChanged.connect( \
      self.NLViewM_checkBoxShowInternalNets_StateChanged)

    # status
    self.ui.statusBarNLView.showMessage("> Ready")

  # core linear parsing functions
  def NLViewM_parseCDL(self): # parse cdl into the hierarchical hash of objects
    cdlArray = []
    f = open(self.options.cdlNetlist)
    for line in f: # read valid lines into an array
      if not (re.match(r'^\s*\*', line) or re.match(r'^\s*$', line)):
        rexp = re.match(r'^\s*\+ (.*)', line.strip("\n"))
        if rexp:
          cdlArray.append(cdlArray.pop() + " " + rexp.group(1))
        else:
          cdlArray.append(line.strip("\n"))
    f.close()

    inSub = False
    for line in cdlArray: # create subckt level hash of objects
      if re.match(r'^\s*\.ends', line, re.M|re.I):
        inSub = False
      else:
        rexp = re.match(r'^\s*\.subckt\s+([0-9a-z_:]+)\s+(.*)', line, re.M|re.I)
        if rexp:
          inSub = True
          subCktName = rexp.group(1)
          ports = filter(None, \
            [port for port in re.split(r"\s+", rexp.group(2)) if not re.match(r'=', port)])
          self.subCktHierData[subCktName] = NLViewC_subCkt(subCktName, ports)
          # print ">> %s" % (subCktName)
        elif inSub:
          rexp = re.match(r'^\s*(x[a-z0-9_\[\]<>:]+)\s+(.*)$', line, re.M|re.I)
          if rexp:
            xCallName = rexp.group(1)
            xRestOfIt = rexp.group(2)
            if re.search(r'/', xRestOfIt):
              xports = filter(None, re.split(r'\s+', re.split(r'/', xRestOfIt)[0]))
              xInstName = filter(None, re.split(r'\s+', re.split(r'/', xRestOfIt)[-1]))[0]
            else:
              xports = filter(None, re.split(r'\s+', xRestOfIt))
              xInstName = xports.pop()
            # print "  %s - %s - %s" % (xCallName, xInstName, xports)
            self.subCktHierData[subCktName].hier[xCallName + ":" + xInstName] = []
            self.subCktHierData[subCktName].xports[xCallName + ":" + xInstName] = xports

    # re-iteration to fill the hier data
    for subCktName in self.subCktHierData:
      for xCallName in self.subCktHierData[subCktName].hier:
        xInstName = re.split(r':', xCallName)[1]
        self.subCktHierData[subCktName].hier[xCallName] = self.subCktHierData[xInstName]

    # self.NLViewM_dumpDict(self.subCktHierData[self.options.topCellName].hier)

  def NLViewM_dumpDict(self, obj, nested_level=0, output=sys.stdout): # to dump dictionary
    spacing = '   '
    if type(obj) == dict:
      for k, v in obj.items():
        if hasattr(v, '__iter__'):
          print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
          self.NLViewM_dumpDict(v, nested_level + 1, output)
        else:
          print >> output, '%s%s' % ((nested_level + 1) * spacing, k)
          self.NLViewM_dumpDict(v.hier, nested_level + 1, output)

  # graphics functions and callbacks
  def NLViewM_populateCDLTreeView(self): # populate the cdl tree view with the cdl hash
    model = QtGui.QStandardItemModel()
    node = self.NLViewM_pushToCDLTreeView(self.subCktHierData, self.options.topCellName)
    model.setItem(0, 0, node)
    model.setHorizontalHeaderItem(0, QtGui.QStandardItem("Circuit Hierarchy"))
    self.ui.treeViewCDLTree.setModel(model)
    self.ui.treeViewCDLTree.setExpanded(node.index(), True)
    self.treeViewCDLTreeModel = model

  def NLViewM_pushToCDLTreeView(self, subCktHierData, cellName="", node=False): # recursive pushing
    # of hierarchical netlist into tree view
    if cellName and cellName in subCktHierData:
      item = QtGui.QStandardItem(cellName)
      if node: node.appendRow(item)
      for subCktName in sorted(subCktHierData[cellName].hier):
        self.NLViewM_pushToCDLTreeView(subCktHierData[cellName].hier, subCktName, item)
      return(item)

  def NLViewM_treeViewCDLTree_SelectionChanged(self, selectedSubCkt): # show ports and subcircuits
    self.ui.tableWidgetPinMap.clearContents()
    self.ui.tableWidgetPinMap.setRowCount(0)
    self.selectedTopCellItem = selectedSubCkt
    selectedSubCkt = selectedSubCkt.indexes()[0].data()
    self.selectedTopCell = selectedSubCkt
    if selectedSubCkt not in self.subCktHierData: selectedSubCkt = re.split(r':', selectedSubCkt)[1]
    if selectedSubCkt in self.subCktHierData:
      # ports
      self.ui.listWidgetPorts.clear()
      ports = self.subCktHierData[selectedSubCkt].ports
      if self.ui.checkBoxShowInternalNets.isChecked(): # show internal nets
        for subCktName in self.subCktHierData[selectedSubCkt].xports:
          ports = list(set(ports + self.subCktHierData[selectedSubCkt].xports[subCktName]))
      ports.sort(self.NLViewM_alphanum) # custom alphanum sorting
      for port in ports:
        item = QtGui.QListWidgetItem(port)
        self.ui.listWidgetPorts.addItem(item)

      # # auto completion for ports
      # portCompletor = QtGui.QCompleter(ports, self.ui.lineEditFilterPorts)
      # self.ui.lineEditFilterPorts.setCompleter(portCompletor)
      # portCompletor.setCompletionMode(QtGui.QCompleter.InlineCompletion)
      # portCompletor.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

      # subckts
      self.ui.listWidgetSubCircuits.clear()
      subckts = self.subCktHierData[selectedSubCkt].hier.keys()
      for subckt in sorted(subckts):
        item = QtGui.QListWidgetItem(subckt)
        self.ui.listWidgetSubCircuits.addItem(item)

      # # auto completion for subckts
      # subcktCompletor = QtGui.QCompleter(subckts, self.ui.lineEditFilterSubCircuits)
      # self.ui.lineEditFilterSubCircuits.setCompleter(subcktCompletor)
      # subcktCompletor.setCompletionMode(QtGui.QCompleter.InlineCompletion)
      # subcktCompletor.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    self.ui.statusBarNLView.showMessage("> Ready")

  def NLViewM_listWidgetSubCircuits_SelectionChanged(self): # show port mapping
    self.ui.tableWidgetPinMap.clear()
    self.ui.tableWidgetPinMap.setColumnCount(2)
    self.ui.tableWidgetPinMap.setRowCount(0)
    self.ui.tableWidgetPinMap.setHorizontalHeaderLabels(["Mapped Ports (Top Level Nets)", \
      "Sub Circuit Ports"])
    xports = []

    selectedTopCell = self.selectedTopCell
    if selectedTopCell not in self.subCktHierData:
      selectedTopCell = re.split(r':', selectedTopCell)[1]

    self.selectedSubCkts = [item.text() for item in self.ui.listWidgetSubCircuits.selectedItems()]
    if len(self.selectedSubCkts) == 1: # connectivity to top level mode
      selectedSubCkt = self.selectedSubCkts[0]
      if selectedTopCell in self.subCktHierData:
        xports = self.subCktHierData[selectedTopCell].xports[selectedSubCkt]
        self.ui.tableWidgetPinMap.setRowCount(len(xports))
        self.ui.tableWidgetPinMap.setColumnCount(2)

        for index in range(0, len(xports)):
          item0 = QtGui.QTableWidgetItem(xports[index]) # top level nets
          item0.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
          self.ui.tableWidgetPinMap.setItem(index, 0, item0)
          item1 = QtGui.QTableWidgetItem(self.subCktHierData[re.split(r':', \
            selectedSubCkt)[1]].ports[index]) # subckt ports
          item1.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
          self.ui.tableWidgetPinMap.setItem(index, 1, item1)
          # color it blue, if it's a mapped port rather than a port connection by name
          if xports[index] != self.subCktHierData[re.split(r':', selectedSubCkt)[1]].ports[index]:
            item0.setBackground(QtGui.QColor(0, 0, 255, 127))
            item1.setBackground(QtGui.QColor(0, 0, 255, 127))

        if len(xports) != len(self.subCktHierData[re.split(r':', selectedSubCkt)[1]].ports):
          self.ui.statusBarNLView.showMessage("> Port length mismatch!")

      self.ui.tableWidgetPinMap.setVisible(False) # auto resize for full view
      self.ui.tableWidgetPinMap.resizeColumnsToContents()
      self.ui.tableWidgetPinMap.setVisible(True)
      self.ui.tableWidgetPinMap.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)

      self.ui.statusBarNLView.showMessage("> " + str(len(self.selectedSubCkts)) + \
        " SubCircuit selected")

    elif len(self.selectedSubCkts) >= 1: # inter-block connectivity mode
      # re-format the table to suit the selected subcircuits
      self.ui.tableWidgetPinMap.clear()
      self.ui.tableWidgetPinMap.setColumnCount(len(self.selectedSubCkts))
      self.ui.tableWidgetPinMap.setRowCount(0)
      self.ui.tableWidgetPinMap.setHorizontalHeaderLabels([re.split(r':', ckt)[0] for ckt in \
        self.selectedSubCkts])

      # ports which are used for interconnection between selected subcircuits
      xports = self.subCktHierData[selectedTopCell].xports[self.selectedSubCkts[0]]
      for selectedSubCkt in self.selectedSubCkts:
        xports = [port for port in xports \
          if port in self.subCktHierData[selectedTopCell].xports[selectedSubCkt]]

      # # xport to actual port connection hash - just for the display
      # dictPortMap = {}
      # for selectedSubCkt in self.selectedSubCkts:
      #   dictPortMap[selectedSubCkt] = {}
      #   for xport in xports:
      #     indices = [i for i, x in \
      #       enumerate(self.subCktHierData[selectedTopCell].xports[selectedSubCkt]) if x == xport]
      #     dictPortMap[selectedSubCkt][xport] = [self.subCktHierData[re.split(r':', \
      #       selectedSubCkt)[1]].ports[index] for index in indices]

      # publishing the table with mapping
      self.ui.tableWidgetPinMap.setRowCount(len(xports))
      for column in range(0, len(self.selectedSubCkts)):
        for index in range(0, len(xports)):
          item = QtGui.QTableWidgetItem(xports[index]) # top level nets
          item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
          self.ui.tableWidgetPinMap.setItem(index, column, item)
          item.setBackground(QtGui.QColor(0, 255, 0, 127))

      # unused ports from each selected subcircuits
      curRowCount = self.ui.tableWidgetPinMap.rowCount()
      for column in range(0, len(self.selectedSubCkts)):
        selectedSubCkt = self.selectedSubCkts[column]
        oports = [port for port in self.subCktHierData[selectedTopCell].xports[selectedSubCkt] \
          if port not in xports]
        self.ui.tableWidgetPinMap.setRowCount(curRowCount + len(oports))
        for index in range(curRowCount, curRowCount + len(oports)):
          item = QtGui.QTableWidgetItem(oports[index - curRowCount])
          item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
          self.ui.tableWidgetPinMap.setItem(index, column, item)
          item.setBackground(QtGui.QColor(255, 0, 0, 127))

      self.ui.tableWidgetPinMap.setVisible(False) # auto resize for full view
      self.ui.tableWidgetPinMap.resizeColumnsToContents()
      self.ui.tableWidgetPinMap.setVisible(True)
      self.ui.tableWidgetPinMap.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)

      self.ui.statusBarNLView.showMessage("> " + str(len(self.selectedSubCkts)) + \
        " SubCircuits selected")

    else:
      self.ui.statusBarNLView.showMessage("> Ready")

    # highlight the nets back in ports list
    for portItem in [self.ui.listWidgetPorts.item(index) for index in \
      range(0, self.ui.listWidgetPorts.count())]: portItem.setBackground(QtGui.QColor(1, 0, 0, 0))
    for index in range(0, self.ui.listWidgetPorts.count()):
      portItem = self.ui.listWidgetPorts.item(index)
      if portItem.text() in xports:
        portItem.setBackground(QtGui.QColor(0, 255, 0, 127))

  def NLViewM_listWidgetPorts_SelectionChanged(self): # highlight connected subcircuits
    countOfConnectedCircuits = 0
    self.ui.listWidgetSubCircuits.clearSelection()
    self.ui.tableWidgetPinMap.clearContents()
    self.ui.tableWidgetPinMap.setRowCount(0)
    selectedTopCell = self.selectedTopCell
    if selectedTopCell not in self.subCktHierData:
      selectedTopCell = re.split(r':', selectedTopCell)[1]
    self.selectedPort = self.ui.listWidgetPorts.currentItem().text()
    for index in range(0, self.ui.listWidgetSubCircuits.count()):
      subCktItem = self.ui.listWidgetSubCircuits.item(index)
      if selectedTopCell in self.subCktHierData and \
        subCktItem.text() in self.subCktHierData[selectedTopCell].xports:
        subCktPorts = self.subCktHierData[selectedTopCell].xports[subCktItem.text()]
        subCktItem.setBackground(QtGui.QColor(1, 0, 0, 0))
        if self.selectedPort in subCktPorts:
          subCktItem.setBackground(QtGui.QColor(255, 0, 0, 127))
          countOfConnectedCircuits += 1
    self.ui.statusBarNLView.showMessage("> Net: " + self.selectedPort + ": " + \
      str(countOfConnectedCircuits) + " connected SubCircuits found")

  def NLViewM_lineEditFilterSubCircuits_Changed(self, expr): # apply filter
    try:
      filterRegex = re.compile(".*" + expr, re.M|re.I)
      is_valid = True
    except re.error:
      is_valid = False

    if is_valid and self.selectedTopCell:
      selectedTopCell = self.selectedTopCell
      if selectedTopCell not in self.subCktHierData:
        selectedTopCell = re.split(r':', selectedTopCell)[1]
      subckts = filter(filterRegex.match, self.subCktHierData[selectedTopCell].hier.keys())
      if subckts:
        selectedSubCkts = self.selectedSubCkts
        self.ui.listWidgetSubCircuits.clear()
        for subckt in sorted(subckts):
          item = QtGui.QListWidgetItem(subckt)
          self.ui.listWidgetSubCircuits.addItem(item)
          if subckt in selectedSubCkts:
            self.ui.listWidgetSubCircuits.setCurrentItem(item)

  def NLViewM_lineEditFilterPorts_Changed(self, expr): # apply filter
    try:
      filterRegex = re.compile(".*" + expr, re.M|re.I)
      is_valid = True
    except re.error:
      is_valid = False

    if is_valid and self.selectedTopCell:
      selectedTopCell = self.selectedTopCell
      if selectedTopCell not in self.subCktHierData:
        selectedTopCell = re.split(r':', selectedTopCell)[1]

      if self.ui.checkBoxShowInternalNets.isChecked(): # show internal nets
        ports = self.subCktHierData[selectedTopCell].ports
        for subCktName in self.subCktHierData[selectedTopCell].xports:
          ports = list(set(ports + self.subCktHierData[selectedTopCell].xports[subCktName]))
        ports = filter(filterRegex.match, ports)
      else: # do not show internal nets
        ports = filter(filterRegex.match, self.subCktHierData[selectedTopCell].ports)

      if ports:
        self.ui.listWidgetPorts.clear()
        ports.sort(self.NLViewM_alphanum) # custom alphanum sorting
        for port in ports:
          item = QtGui.QListWidgetItem(port)
          self.ui.listWidgetPorts.addItem(item)
          if port == self.selectedPort:
            self.ui.listWidgetPorts.setCurrentItem(item)

  def NLViewM_listWidgetSubCircuits_DoubleClick(self, item): # select the child on the tree
    searchText = item.text()
    treeViewParent = self.treeViewCDLTreeModel.itemFromIndex(self.selectedTopCellItem.indexes()[0])
    for row in range(0, treeViewParent.rowCount()):
      if searchText == treeViewParent.child(row, 0).text():
        self.ui.treeViewCDLTree.setCurrentIndex(treeViewParent.child(row, 0).index())

  def NLViewM_listWidgetPorts_DoubleClick(self, item): # trace the net callback
    print "\n-I-: Tracing %s net.." % (item.text())
    self.ui.statusBarNLView.showMessage("> Tracing Net..")
    selectedNet = item.text()
    selectedTopCell = self.selectedTopCell
    self.NLViewM_traceNet(selectedNet, selectedTopCell, "  ")
    self.ui.statusBarNLView.showMessage("> Tracing Done - Check the terminal.")
    print "-I-: Tracing Complete."

  def NLViewM_traceNet(self, selectedNet, selectedTopCell, intend): # recursive trace net
    print intend + "Net: %s Circuit: %s" % (selectedNet, selectedTopCell)
    if selectedTopCell not in self.subCktHierData:
      selectedTopCell = re.split(r':', selectedTopCell)[1]
    for subCktName in self.subCktHierData[selectedTopCell].xports:
      if selectedNet in self.subCktHierData[selectedTopCell].xports[subCktName]:
        self.NLViewM_traceNet(selectedNet, subCktName, intend + "  ")

  def NLViewM_listWidgetPorts_actionTraceNet(self): # right click trace net
    self.NLViewM_listWidgetPorts_DoubleClick(self.ui.listWidgetPorts.currentItem())

  def NLViewM_checkBoxShowInternalNets_StateChanged(self): # show internal nets checkbox callback
    selectedTopCell = self.selectedTopCell
    if selectedTopCell not in self.subCktHierData:
      selectedTopCell = re.split(r':', selectedTopCell)[1]
    if selectedTopCell and selectedTopCell in self.subCktHierData:
      if self.ui.checkBoxShowInternalNets.isChecked(): # show internal nets
        self.ui.listWidgetPorts.clear()
        ports = self.subCktHierData[selectedTopCell].ports
        for subCktName in self.subCktHierData[selectedTopCell].xports:
          ports = list(set(ports + self.subCktHierData[selectedTopCell].xports[subCktName]))
      else: # do not show internal nets
        self.ui.listWidgetPorts.clear()
        ports = self.subCktHierData[selectedTopCell].ports
      ports.sort(self.NLViewM_alphanum) # custom alphanum sorting
      for port in ports:
        item = QtGui.QListWidgetItem(port)
        self.ui.listWidgetPorts.addItem(item)
    else:
      print "-W-: %s not found in self.subCktHierData" % (selectedTopCell)

  def NLViewM_pushButtonReloadNetlist_Clicker(self): # reload netlist
    self.ui.statusBarNLView.showMessage("> Re-loading the netlist..")
    self.NLViewM_parseCDL()
    self.NLViewM_populateCDLTreeView()
    selmodel = self.ui.treeViewCDLTree.selectionModel()
    selmodel.selectionChanged.connect(self.NLViewM_treeViewCDLTree_SelectionChanged)
    self.ui.listWidgetPorts.clear()
    self.ui.listWidgetSubCircuits.clear()
    self.ui.tableWidgetPinMap.clearContents()
    self.ui.statusBarNLView.showMessage("> Ready")

  # helper functions
  def NLViewM_chunkify(self, str): # return a list of numbers and non-numeric substrings of str -
    # the numeric substrings are converted to integer, non-numeric are left as is
    chunks = re.findall("(\d+|\D+)",str)
    chunks = [int(x) if re.match('\d', x) else x for x in chunks] # numeric strings to numbers
    return chunks

  def NLViewM_alphanum(self, a, b): # breaks a & b into pieces and returns left-to-right comparison
    aChunks = self.NLViewM_chunkify(a)
    bChunks = self.NLViewM_chunkify(b)
    return cmp(aChunks, bChunks)

if __name__ == "__main__":
  NLViewQTApp = QtGui.QApplication(sys.argv)
  NLViewMainWindow = NLViewC_NetlistViewer()
  NLViewMainWindow.showMaximized()
  NLViewMainWindow.show()
  sys.exit(NLViewQTApp.exec_())
