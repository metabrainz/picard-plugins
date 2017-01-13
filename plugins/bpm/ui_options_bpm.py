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
        BPMOptionsPage.resize(495, 273)
        self.gridLayout_2 = QtGui.QGridLayout(BPMOptionsPage)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.bpm_options = QtGui.QGroupBox(BPMOptionsPage)
        self.bpm_options.setObjectName(_fromUtf8("bpm_options"))
        self.slider_default = QtGui.QLabel(self.bpm_options)
        self.slider_default.setGeometry(QtCore.QRect(8, 80, 43, 19))
        self.slider_default.setToolTip(_fromUtf8(""))
        self.slider_default.setObjectName(_fromUtf8("slider_default"))
        self.slider_parameter = QtGui.QSlider(self.bpm_options)
        self.slider_parameter.setGeometry(QtCore.QRect(20, 51, 391, 23))
        self.slider_parameter.setMinimum(1)
        self.slider_parameter.setMaximum(3)
        self.slider_parameter.setOrientation(QtCore.Qt.Horizontal)
        self.slider_parameter.setTickPosition(QtGui.QSlider.TicksBelow)
        self.slider_parameter.setTickInterval(1)
        self.slider_parameter.setObjectName(_fromUtf8("slider_parameter"))
        self.slider_super_fast = QtGui.QLabel(self.bpm_options)
        self.slider_super_fast.setGeometry(QtCore.QRect(370, 80, 61, 19))
        self.slider_super_fast.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.slider_super_fast.setObjectName(_fromUtf8("slider_super_fast"))
        self.line = QtGui.QFrame(self.bpm_options)
        self.line.setGeometry(QtCore.QRect(10, 120, 471, 20))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.horizontalLayoutWidget = QtGui.QWidget(self.bpm_options)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(6, 140, 471, 91))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.gridLayout = QtGui.QGridLayout(self.horizontalLayoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.samplerate_value = QtGui.QLabel(self.horizontalLayoutWidget)
        self.samplerate_value.setText(_fromUtf8(""))
        self.samplerate_value.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.samplerate_value.setObjectName(_fromUtf8("samplerate_value"))
        self.gridLayout.addWidget(self.samplerate_value, 2, 1, 1, 1)
        self.hop_s_label = QtGui.QLabel(self.horizontalLayoutWidget)
        self.hop_s_label.setObjectName(_fromUtf8("hop_s_label"))
        self.gridLayout.addWidget(self.hop_s_label, 1, 0, 1, 1)
        self.win_s_value = QtGui.QLabel(self.horizontalLayoutWidget)
        self.win_s_value.setText(_fromUtf8(""))
        self.win_s_value.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.win_s_value.setObjectName(_fromUtf8("win_s_value"))
        self.gridLayout.addWidget(self.win_s_value, 0, 1, 1, 1)
        self.hop_s_value = QtGui.QLabel(self.horizontalLayoutWidget)
        self.hop_s_value.setText(_fromUtf8(""))
        self.hop_s_value.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.hop_s_value.setObjectName(_fromUtf8("hop_s_value"))
        self.gridLayout.addWidget(self.hop_s_value, 1, 1, 1, 1)
        self.win_s_label = QtGui.QLabel(self.horizontalLayoutWidget)
        self.win_s_label.setObjectName(_fromUtf8("win_s_label"))
        self.gridLayout.addWidget(self.win_s_label, 0, 0, 1, 1)
        self.samplerate_label = QtGui.QLabel(self.horizontalLayoutWidget)
        self.samplerate_label.setObjectName(_fromUtf8("samplerate_label"))
        self.gridLayout.addWidget(self.samplerate_label, 2, 0, 1, 1)
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout_2.addWidget(self.bpm_options, 0, 0, 1, 1)

        self.retranslateUi(BPMOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(BPMOptionsPage)

    def retranslateUi(self, BPMOptionsPage):
        self.bpm_options.setTitle(_translate("BPMOptionsPage", "BPM Analyze Parameters:", None))
        self.slider_default.setText(_translate("BPMOptionsPage", "Default", None))
        self.slider_super_fast.setText(_translate("BPMOptionsPage", "Super Fast", None))
        self.hop_s_label.setText(_translate("BPMOptionsPage", "Number of frames between two consecutive runs:", None))
        self.win_s_label.setText(_translate("BPMOptionsPage", "Length of FFT:", None))
        self.samplerate_label.setText(_translate("BPMOptionsPage", "Samplerate:", None))

