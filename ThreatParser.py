from PyQt5 import QtCore, QtGui, QtWidgets, uic
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
from logParser import *

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
        self.logFileDesc.setText("Combatlog file path:")


        self.LogFilePath = QtWidgets.QLineEdit(self.centralwidget)
        self.LogFilePath.setGeometry(QtCore.QRect(10, 35, 160, 20))
        self.LogFilePath.setText("C:\Code\Git\Python\OnyPostHotfix.txt")
        #self.LogFilePath.setPlaceholderText("Combatlog File Path")
        self.LogFilePath.setObjectName("LogFilePath")

        self.mightBonus = QtWidgets.QCheckBox("8/8 Might Bonus", self.centralwidget)
        self.mightBonus.setGeometry(QtCore.QRect(10, 60, 160, 20))
        self.mightBonus.setObjectName("MightCheckBox")

        self.defianceCombo = QtWidgets.QComboBox(self.centralwidget)
        self.defianceCombo.setGeometry(QtCore.QRect(10, 85, 160, 20))
        self.defianceCombo.setObjectName('Defiance Rank')
        self.defianceCombo.addItem("0/5 Defiance")
        self.defianceCombo.addItem("1/5 Defiance")
        self.defianceCombo.addItem("2/5 Defiance")
        self.defianceCombo.addItem("3/5 Defiance")
        self.defianceCombo.addItem("4/5 Defiance")
        self.defianceCombo.addItem("5/5 Defiance")
        self.defianceCombo.setCurrentIndex(5)

        self.stanceCombo = QtWidgets.QComboBox(self.centralwidget)
        self.stanceCombo.setGeometry(QtCore.QRect(10, 110, 160, 20))
        self.stanceCombo.setObjectName('Initial Stance')
        self.stanceCombo.addItem("Battle Stance")
        self.stanceCombo.addItem("Defensive Stance")
        self.stanceCombo.addItem("Berserker Stance")
        self.stanceCombo.setCurrentIndex(1)

        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(110, 150, 60, 24))
        self.pushButton.setObjectName("pushButton")
        self.pushButton.clicked.connect(self.recalc)

        MainWindow.setCentralWidget(self.centralwidget)

        #self.menubar = QtWidgets.QMenuBar(MainWindow)
        #self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 18))
        #self.menubar.setObjectName("menubar")
        #self.menuTest = QtWidgets.QMenu(self.menubar)
        #self.menuTest.setObjectName("menuTest")
        #MainWindow.setMenuBar(self.menubar)

        #self.statusbar = QtWidgets.QStatusBar(MainWindow)
        #self.statusbar.setObjectName("statusbar")
        #MainWindow.setStatusBar(self.statusbar)
        #self.menubar.addAction(self.menuTest.menuAction())

        ### OUTPUT ###
        self.threatGraph = pg.PlotWidget(self.centralwidget)
        self.threatGraph.setBackground(color_palette.alternateBase())
        self.pen = pg.mkPen(color='9a8bb0', width=7)
        self.threatGraph.resize(0,0)
        self.threatGraph.move(0,0)

        def updateSelectedValues(regionItem): ## TODO USE SELECTION FOR THE TABLE INSTEAD
            dmg = 0
            threat = 0
            self.selectedEvents = []
            startPoint, endPoint = regionItem.getRegion()
            for event in self.data.logEvents:
                if event.timestamp > endPoint:
                    break
                if event.timestamp > startPoint:
                    dmg += event.damage
                    threat += event.threat
                    self.selectedEvents.append(event)
            self.selectedTPS.setText("Selected Threat per Second: " + str(round(threat/(endPoint - startPoint), 1)))
            self.selectedDPS.setText("Selected Damage per Second: " + str(round(dmg/(endPoint - startPoint), 1)))
            return

        lr = pg.LinearRegionItem([10, 40])
        lr.setZValue(-10)
        self.threatGraph.addItem(lr)
        lr.sigRegionChangeFinished.connect(updateSelectedValues)

        self.totalTPS = QtWidgets.QLabel(self.centralwidget)
        self.totalTPS.setGeometry(180, 400, 260, 24)

        self.totalDPS = QtWidgets.QLabel(self.centralwidget)
        self.totalDPS.setGeometry(180, 420, 260, 24)

        self.selectedTPS = QtWidgets.QLabel(self.centralwidget)
        self.selectedTPS.setGeometry(680, 400, 260, 24)

        self.selectedDPS = QtWidgets.QLabel(self.centralwidget)
        self.selectedDPS.setGeometry(680, 420, 260, 24)

        #self.abilityTable = pg.TableWidget(self.centralwidget)

        
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
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Yoshi Threat Parser"))
        self.pushButton.setText(_translate("MainWindow", "Calc"))
        #self.menuTest.setTitle(_translate("MainWindow", "Options"))

    # Main function
    def recalc(self):
        logFilePath = self.LogFilePath.text()
        defiance = int(self.defianceCombo.currentText()[0])
        mightBonus = self.mightBonus.isChecked()
        initialStance = self.stanceCombo.currentText()

        config = logConfig()
        config.logFilePath = logFilePath
        config.defiance = defiance
        config.mightBonus = bool(mightBonus)
        config.initialStance = initialStance
        config.playerName = "Quadzet"
        config.server = "Golemagg"

        self.data = logData()
        self.selectedEvents = self.data.logEvents
        parse_combat_log(logFilePath, self.data, config)
        #x, y = generatePlotVectors(self.data.totalTimestamps, self.data.totalThreat)
        x, y = generatePlotVectors(self.data.logEvents)
        self.threatGraph.resize(1010,360)
        self.threatGraph.move(180, 10)
        self.threatGraph.plot(x, y, pen=self.pen)

        self.totalTPS.setText("Threat per Second: " + str(self.data.totalTPS))
        self.totalDPS.setText("Damage per Second: " + str(self.data.totalDPS))

        self.abilityTable.resize(1010, 300)
        abilityTuples = []
        for event in self.selectedEvents:
            if event.spellName in [item[0] for item in abilityTuples]: # use the 'in' keyword?
                abilityTuple = [item for item in abilityTuples if item[0] == event.spellName][0]
                abilityTuple[1] += event.damage
                abilityTuple[2] += event.threat
            else:
                abilityTuples.append([event.spellName, event.damage, event.threat])
        self.abilityTable.setRowCount(len(abilityTuples)+1)
        sorted(abilityTuples, key=lambda abilityTuples: abilityTuples[2])
        ix = 0
        for i in abilityTuples:
            self.abilityTable.setItem(ix, 0, QtWidgets.QTableWidgetItem(i[0]))
            self.abilityTable.setItem(ix, 1, QtWidgets.QTableWidgetItem(str(round(i[1]/self.data.fightLength, 1))))
            self.abilityTable.setItem(ix, 2, QtWidgets.QTableWidgetItem(str(round(i[2]/self.data.fightLength, 1))))
            self.abilityTable.setItem(ix, 3, QtWidgets.QTableWidgetItem(str(round(i[2]*100/(self.data.fightLength*self.data.totalTPS), 1)) + "%"))
            ix += 1
        self.abilityTable.setItem(ix, 0, QtWidgets.QTableWidgetItem("Total"))
        self.abilityTable.setItem(ix, 1, QtWidgets.QTableWidgetItem(str(round(sum([item[1] for item in abilityTuples])/self.data.fightLength, 1))))
        self.abilityTable.setItem(ix, 2, QtWidgets.QTableWidgetItem(str(round(sum([item[2] for item in abilityTuples])/self.data.fightLength, 1))))
        self.abilityTable.setItem(ix, 3, QtWidgets.QTableWidgetItem(str(round(sum([item[2] for item in abilityTuples])*100/(self.data.fightLength*self.data.totalTPS), 1)) + "%"))
            
        self.abilityTable.resizeColumnsToContents()
        size = myGetQTableWidgetSize(self.abilityTable)
        size.setWidth(1010)
        self.abilityTable.setFixedSize(size)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
