##############################################################################
#
#   MVMGUI
#   Copyright (C) 2020 giovanni.organtini@uniroma1.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

import paho.mqtt.client as mqtt

class MVMMqttClient(QtCore.QObject):
    Disconnected = 0
    Connecting = 1
    Connected = 2

    connected = QtCore.pyqtSignal()
    disconnected = QtCore.pyqtSignal()

    stateChanged = QtCore.pyqtSignal(int)

    messageSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MVMMqttClient, self).__init__(parent)

        self.m_state = MVMMqttClient.Disconnected

        self.m_client = mqtt.Client()

        self.m_client.on_connect = self.on_connect
        self.m_client.on_message = self.on_message
        self.m_client.on_disconnect = self.on_disconnect


    @QtCore.pyqtProperty(int, notify=stateChanged)
    def state(self):
        return self.m_state

    @state.setter
    def state(self, state):
        if self.m_state == state:
            return
        self.m_state = state
        self.stateChanged.emit(state) 

    @QtCore.pyqtSlot()
    def connectToHost(self):
        self.m_client.connect("localhost")
        self.state = MVMMqttClient.Connecting
        self.m_client.loop_start()

    @QtCore.pyqtSlot()
    def disconnectFromHost(self):
        self.m_client.disconnect()

    def subscribe(self, path):
        if self.state == MVMMqttClient.Connected:
            self.m_client.subscribe(path)

    def on_message(self, mqttc, obj, msg):
        mstr = msg.payload.decode("ascii")
        print("on_message", mstr, obj, mqttc)
        self.messageSignal.emit(mstr)

    def on_connect(self, *args):
        print("on_connect", args)
        self.state = MVMMqttClient.Connected
        self.connected.emit()

    def on_disconnect(self, *args):
        print("on_disconnect", args)
        self.state = MVMMqttClient.Disconnected
        self.disconnected.emit()

class MVMWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MVMWidget, self).__init__(parent)

        self.layout = QtWidgets.QGridLayout(self)
        newfont = QtGui.QFont("Arial", 48, QtGui.QFont.Bold) 
        self.leftPanel = []
        for i in range(5):
            self.leftPanel.append(QtWidgets.QLabel(str(i)))
            self.leftPanel[-1].setFont(newfont)
        for i in range(5):
            self.layout.addWidget(self.leftPanel[i], i, 0)
        self.create_linechart()
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 40)

        self.client = MVMMqttClient(self)
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)

        self.client.connectToHost()

    def create_linechart(self):
        series = QLineSeries(self)
        series.append(0,6)
        series.append(2, 4)
        series.append(3, 8)
        series.append(7, 4)
        series.append(10, 5)
 
        series << QPointF(11, 1) << QPointF(13, 3) << QPointF(17, 6) << QPointF(18, 3) << QPointF(20, 2)
 
        chart =  QChart()
 
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Line Chart Example")
 
        chart.legend().setVisible(True)
 
        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)
        self.layout.addWidget(chartview, 0, 1, 5, 1)

    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MVMMqttClient.Connected:
            self.client.subscribe("topic/state")

    @QtCore.pyqtSlot(str)
    def on_messageSignal(self, msg): 
        self.leftPanel[0].setText(msg)

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = MVMWidget()
    w.show()
    w.showFullScreen()
    sys.exit(app.exec_())
