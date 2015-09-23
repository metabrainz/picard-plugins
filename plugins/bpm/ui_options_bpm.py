# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_bpm2.ui'
#
# Created: Wed Sep 23 09:41:53 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_BPMOptionsPage(object):
    def setupUi(self, BPMOptionsPage):
        BPMOptionsPage.setObjectName(_fromUtf8("BPMOptionsPage"))
        BPMOptionsPage.resize(465, 279)
        self.gridLayout_2 = QtGui.QGridLayout(BPMOptionsPage)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.bpm_options = QtGui.QGroupBox(BPMOptionsPage)
        self.bpm_options.setObjectName(_fromUtf8("bpm_options"))
        self.label_3 = QtGui.QLabel(self.bpm_options)
        self.label_3.setGeometry(QtCore.QRect(8, 219, 69, 19))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.samplerate_parameter = QtGui.QLineEdit(self.bpm_options)
        self.samplerate_parameter.setGeometry(QtCore.QRect(297, 219, 135, 33))
        self.samplerate_parameter.setReadOnly(True)
        self.samplerate_parameter.setObjectName(_fromUtf8("samplerate_parameter"))
        self.label = QtGui.QLabel(self.bpm_options)
        self.label.setGeometry(QtCore.QRect(8, 141, 81, 19))
        self.label.setObjectName(_fromUtf8("label"))
        self.win_s_parameter = QtGui.QLineEdit(self.bpm_options)
        self.win_s_parameter.setEnabled(True)
        self.win_s_parameter.setGeometry(QtCore.QRect(297, 141, 135, 33))
        self.win_s_parameter.setReadOnly(True)
        self.win_s_parameter.setObjectName(_fromUtf8("win_s_parameter"))
        self.label_2 = QtGui.QLabel(self.bpm_options)
        self.label_2.setGeometry(QtCore.QRect(8, 180, 283, 19))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.hop_s_parameter = QtGui.QLineEdit(self.bpm_options)
        self.hop_s_parameter.setGeometry(QtCore.QRect(297, 180, 135, 33))
        self.hop_s_parameter.setReadOnly(True)
        self.hop_s_parameter.setObjectName(_fromUtf8("hop_s_parameter"))
        self.label_5 = QtGui.QLabel(self.bpm_options)
        self.label_5.setGeometry(QtCore.QRect(8, 80, 43, 19))
        self.label_5.setToolTip(_fromUtf8(""))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.slider_parameter = QtGui.QSlider(self.bpm_options)
        self.slider_parameter.setGeometry(QtCore.QRect(20, 51, 391, 23))
        self.slider_parameter.setMinimum(1)
        self.slider_parameter.setMaximum(3)
        self.slider_parameter.setOrientation(QtCore.Qt.Horizontal)
        self.slider_parameter.setTickPosition(QtGui.QSlider.TicksBelow)
        self.slider_parameter.setTickInterval(1)
        self.slider_parameter.setObjectName(_fromUtf8("slider_parameter"))
        self.label_7 = QtGui.QLabel(self.bpm_options)
        self.label_7.setGeometry(QtCore.QRect(370, 80, 61, 19))
        self.label_7.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.line = QtGui.QFrame(self.bpm_options)
        self.line.setGeometry(QtCore.QRect(10, 120, 471, 20))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.gridLayout_2.addWidget(self.bpm_options, 0, 0, 1, 1)

        self.retranslateUi(BPMOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(BPMOptionsPage)

    def retranslateUi(self, BPMOptionsPage):
        self.bpm_options.setTitle(_translate("BPMOptionsPage", "BPM Analyze Parameters:", None))
        self.label_3.setText(_translate("BPMOptionsPage", "samplerate:", None))
        self.label.setText(_translate("BPMOptionsPage", "Length of FFT:", None))
        self.label_2.setText(_translate("BPMOptionsPage", "Number of frames between two consecutive runs:", None))
        self.label_5.setText(_translate("BPMOptionsPage", "Default", None))
        self.label_7.setText(_translate("BPMOptionsPage", "Super Fast", None))

