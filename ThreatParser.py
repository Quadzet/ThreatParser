from PyQt5 import QtCore, QtGui, QtWidgets, uic
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
from logParser import *

VERSION="1.0.0"

# TODO MOVE THIS
def myGetQTableWidgetSize(t):
    w = t.verticalHeader().width() + 4
    for i in range(0, t.columnCount()):
        w += t.columnWidth(i)
    h = t.horizontalHeader().height() + 2
    for i in range(0, t.rowCount()):
        h += t.rowHeight(i)
    return QtCore.QSize(w, h)

class Ui_MainWindow(object):
    # Updates the selected TPS/DPS as well as the table values
    def updateSelectedValues(self):
        if (len(self.selectedEvents) == 0):
            return
        threat = sum([item.threat for item in self.selectedEvents])
        damage = sum([item.damage for item in self.selectedEvents])
        startPoint, endPoint = self.lr.getRegion()
        time = endPoint - startPoint
        self.selectedTPS.setText("Selected Threat per Second: " + str(round(threat/time, 1)))
        self.selectedDPS.setText("Selected Damage per Second: " + str(round(damage/time, 1)))

        self.abilityTable.resize(1010, 300)
        abilityTuples = []
        totalThreat = 0
        for event in self.selectedEvents:
            if event.spellName in [item[0] for item in abilityTuples]:
                abilityTuple = [item for item in abilityTuples if item[0] == event.spellName][0]
                abilityTuple[1] += event.damage
                abilityTuple[2] += event.threat
                totalThreat += event.threat
            else:
                abilityTuples.append([event.spellName, event.damage, event.threat])
                totalThreat += event.threat
        self.abilityTable.setRowCount(len(abilityTuples)+1)
        sorted(abilityTuples, key=lambda abilityTuples: abilityTuples[2])
        ix = 0
        for i in abilityTuples:
            self.abilityTable.setItem(ix, 0, QtWidgets.QTableWidgetItem(i[0]))
            self.abilityTable.setItem(ix, 1, QtWidgets.QTableWidgetItem(str(round(i[1]/time, 1))))
            self.abilityTable.setItem(ix, 2, QtWidgets.QTableWidgetItem(str(round(i[2]/time, 1))))
            self.abilityTable.setItem(ix, 3, QtWidgets.QTableWidgetItem(str(round(i[2]*100/totalThreat, 1)) + "%"))
            ix += 1
        self.abilityTable.setItem(ix, 0, QtWidgets.QTableWidgetItem("Total"))
        self.abilityTable.setItem(ix, 1, QtWidgets.QTableWidgetItem(str(round(sum([item[1] for item in abilityTuples])/time, 1))))
        self.abilityTable.setItem(ix, 2, QtWidgets.QTableWidgetItem(str(round(sum([item[2] for item in abilityTuples])/time, 1))))
        self.abilityTable.setItem(ix, 3, QtWidgets.QTableWidgetItem(str(round(sum([item[2] for item in abilityTuples])*100/totalThreat, 1)) + "%"))
            
        self.abilityTable.resizeColumnsToContents()
        size = myGetQTableWidgetSize(self.abilityTable)
        size.setWidth(1010)
        self.abilityTable.setFixedSize(size)
        return

    def updateSelectedEvents(self, regionItem):
        self.selectedEvents = []
        startPoint, endPoint = regionItem.getRegion()
        for event in self.data.logEvents:
            if event.timestamp - self.config.startTime > endPoint:
                break
            if event.timestamp - self.config.startTime > startPoint:
                self.selectedEvents.append(event)
        self.updateSelectedValues()
        return

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 800)

        '''lightBackgroundColor = QtGui.QColor()
        lightBackgroundColor.setNamedColor("#ebecdd")
        backgroundColor = QtGui.QColor()
        backgroundColor.setNamedColor("#ebe2bb")'''

        #MainWindow.setPalette(backgroundColor)
        color_palette = MainWindow.palette()

        '''color_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        color_palette.setColor(QtGui.QPalette.Base, lightBackgroundColor)
        color_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.black)
        color_palette.setColor(QtGui.QPalette.Window, backgroundColor)
        MainWindow.setPalette(color_palette)'''

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.logFileDesc = QtWidgets.QLabel(self.centralwidget)
        self.logFileDesc.setGeometry(QtCore.QRect(10, 10, 160, 20))
        self.logFileDesc.setText("Warcraftlogs Report ID:")


        self.reportID = QtWidgets.QLineEdit(self.centralwidget)
        self.reportID.setGeometry(QtCore.QRect(10, 35, 160, 20))
        self.reportID.setText("tTyGkAbDdjLFJPwn") #tTyGkAbDdjLFJPwn QKnRY3gjtCpZWrMm
        self.reportID.setObjectName("reportID")

        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(110, 60, 60, 24))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.fetchShowInfo)
        self.pushButton.setText("Fetch")#_translate("MainWindow", "Fetch"))

        MainWindow.setCentralWidget(self.centralwidget)
        self.data = logData()
        self.config = ""

        ### EXTRA FIGHT CONFIG ###
        self.playerCombo = QtWidgets.QComboBox(self.centralwidget)
        self.playerCombo.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.playerCombo.setObjectName('Player Name')

        self.fightCombo = QtWidgets.QComboBox(self.centralwidget)
        self.fightCombo.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.fightCombo.setObjectName('Boss Name')

        self.mightBonus = QtWidgets.QCheckBox("8/8 Might Bonus", self.centralwidget)
        self.mightBonus.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.mightBonus.setObjectName("MightCheckBox")

        self.defianceCombo = QtWidgets.QComboBox(self.centralwidget)
        self.defianceCombo.setGeometry(QtCore.QRect(0, 0, 0, 0))

        self.stanceDesc = QtWidgets.QLabel(self.centralwidget)
        self.stanceDesc.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.stanceDesc.setText("Initial Stance:")

        self.stanceCombo = QtWidgets.QComboBox(self.centralwidget)
        self.stanceCombo.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.stanceCombo.setObjectName('Initial Stance')

        self.fightButton = QtWidgets.QPushButton(self.centralwidget)
        self.fightButton.setGeometry(QtCore.QRect(0, 0, 0, 0))
        self.fightButton.setObjectName("fightButton")
        self.fightButton.clicked.connect(self.recalc)
        self.fightButton.setText("Calc")

        ### OUTPUT ###
        self.threatGraph = pg.PlotWidget(self.centralwidget)
        self.threatGraph.setBackground(color_palette.alternateBase())
        self.pen = pg.mkPen(color='9a8bb0', width=7)
        self.threatGraph.resize(0,0)
        self.threatGraph.move(0,0)
        self.plot = self.threatGraph.plot([0], [0], pen=self.pen)



        self.lr = pg.LinearRegionItem([0, 10])
        self.lr.setZValue(-10)
        self.threatGraph.addItem(self.lr)
        self.lr.sigRegionChangeFinished.connect(self.updateSelectedEvents)

        self.totalTPS = QtWidgets.QLabel(self.centralwidget)
        self.totalTPS.setGeometry(180, 400, 260, 24)

        self.totalDPS = QtWidgets.QLabel(self.centralwidget)
        self.totalDPS.setGeometry(180, 420, 260, 24)

        self.selectedTPS = QtWidgets.QLabel(self.centralwidget)
        self.selectedTPS.setGeometry(680, 400, 260, 24)

        self.selectedDPS = QtWidgets.QLabel(self.centralwidget)
        self.selectedDPS.setGeometry(680, 420, 260, 24)

        self.abilityTable = QtWidgets.QTableWidget(self.centralwidget)
        self.abilityTable.setRowCount(0)
        self.abilityTable.setColumnCount(4)
        self.abilityTable.setHorizontalHeaderLabels(["Ability", "DPS", "TPS", "TPS %"])
        self.abilityTable.resize(0,0)
        self.abilityTable.move(180, 450)

        ### FINISHING TOUCHES ###
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        #_translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle("Quadzet Threat Parser " + VERSION)#_translate("MainWindow", "Quadzet Threat Parser"))

    def addFightOptions(self, reportData):
        self.mightBonus.setGeometry(QtCore.QRect(10, 90, 160, 20))

        self.defianceCombo.clear()
        self.defianceCombo.setGeometry(QtCore.QRect(10, 115, 160, 20))
        self.defianceCombo.setObjectName('Defiance Rank')
        self.defianceCombo.addItem("0/5 Defiance")
        self.defianceCombo.addItem("1/5 Defiance")
        self.defianceCombo.addItem("2/5 Defiance")
        self.defianceCombo.addItem("3/5 Defiance")
        self.defianceCombo.addItem("4/5 Defiance")
        self.defianceCombo.addItem("5/5 Defiance")
        self.defianceCombo.setCurrentIndex(5)

        self.stanceDesc.setGeometry(QtCore.QRect(10, 140, 160, 20))

        self.stanceCombo.clear()
        self.stanceCombo.setGeometry(QtCore.QRect(10, 165, 160, 20))
        self.stanceCombo.setObjectName('Initial Stance')
        self.stanceCombo.addItem("Battle Stance")
        self.stanceCombo.addItem("Defensive Stance")
        self.stanceCombo.addItem("Berserker Stance")
        self.stanceCombo.setCurrentIndex(1)

        self.playerCombo.clear()
        self.playerCombo.setGeometry(QtCore.QRect(10, 190, 160, 20))
        self.playerCombo.addItem("Choose Tank") # todo, filter by role
        for name in reportData.players:
            self.playerCombo.addItem(name)
        self.playerCombo.setCurrentIndex(0)

        self.fightCombo.clear()
        self.fightCombo.setGeometry(QtCore.QRect(10, 215, 160, 20))
        self.fightCombo.addItem("Choose Fight")
        for boss in reportData.bosses:
            self.fightCombo.addItem(boss)
        self.fightCombo.setCurrentIndex(0)

        self.fightButton.setGeometry(QtCore.QRect(110, 240, 60, 24))

    # Fetch fight info (players, bosses etc) and show additional options
    def fetchShowInfo(self):
        reportID = self.reportID.text()
        self.config = fightData(reportID)# bool(mightBonus), initialStance, "Quadzet", "Golemagg")
        fetchFightInfo(self.config)
        self.addFightOptions(self.config.reportData)

    # Main function
    def recalc(self):
        bossIX = self.fightCombo.currentIndex()
        playerIX = self.playerCombo.currentIndex()
        if bossIX == 0 or playerIX == 0: # First index is "choose XYZ"
            return

        self.config.fightID = self.config.reportData.fightIDs[bossIX-1]
        self.config.playerID = self.config.reportData.playerIDs[playerIX-1]
        self.config.bossID = self.config.reportData.bossIDs[bossIX-1]
        self.config.fightLength = self.config.reportData.fightLengths[bossIX-1]
        self.config.startTime = self.config.reportData.fightStartTimes[bossIX-1]
        self.config.defiance = int(self.defianceCombo.currentText()[0])
        self.config.mightBonus = self.mightBonus.isChecked()
        self.config.stance = self.stanceCombo.currentText()

        fetchEvents(self.data, self.config)
        x, y = generatePlotVectors(self.data.logEvents, self.config)
        self.lr.setRegion([0,self.config.fightLength])
        self.threatGraph.resize(1010,360)
        self.threatGraph.move(180, 10)
        self.plot.setData(x, y)
        self.totalTPS.setText("Threat per Second: " + str(self.data.totalTPS))
        self.totalDPS.setText("Damage per Second: " + str(self.data.totalDPS))
        self.updateSelectedEvents(self.lr)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
