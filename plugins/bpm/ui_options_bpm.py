# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_bpm.ui'
#
# Created: Thu Sep 17 16:55:01 2015
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
        BPMOptionsPage.resize(339, 349)
        self.vboxlayout = QtGui.QVBoxLayout(BPMOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.bpm_options = QtGui.QGroupBox(BPMOptionsPage)
        self.bpm_options.setObjectName(_fromUtf8("bpm_options"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.bpm_options)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.label = QtGui.QLabel(self.bpm_options)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout1.addWidget(self.label)
        self.win_s_parameter = QtGui.QLineEdit(self.bpm_options)
        self.win_s_parameter.setObjectName(_fromUtf8("win_s_parameter"))
        self.vboxlayout1.addWidget(self.win_s_parameter)
        self.label_2 = QtGui.QLabel(self.bpm_options)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.vboxlayout1.addWidget(self.label_2)
        self.hop_s_parameter = QtGui.QLineEdit(self.bpm_options)
        self.hop_s_parameter.setObjectName(_fromUtf8("hop_s_parameter"))
        self.vboxlayout1.addWidget(self.hop_s_parameter)
        self.label_3 = QtGui.QLabel(self.bpm_options)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.vboxlayout1.addWidget(self.label_3)
        self.samplerate_parameter = QtGui.QLineEdit(self.bpm_options)
        self.samplerate_parameter.setObjectName(_fromUtf8("samplerate_parameter"))
        self.vboxlayout1.addWidget(self.samplerate_parameter)
        self.vboxlayout.addWidget(self.bpm_options)
        self.label_4 = QtGui.QLabel(BPMOptionsPage)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.vboxlayout.addWidget(self.label_4)
        spacerItem = QtGui.QSpacerItem(263, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(BPMOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(BPMOptionsPage)

    def retranslateUi(self, BPMOptionsPage):
        self.bpm_options.setTitle(_translate("BPMOptionsPage", "BPM Analyze Parameters:", None))
        self.label.setText(_translate("BPMOptionsPage", "win_s:", None))
        self.label_2.setText(_translate("BPMOptionsPage", "hop_s:", None))
        self.label_3.setText(_translate("BPMOptionsPage", "samplerate:", None))
        self.label_4.setText(_translate("BPMOptionsPage", "        # super fast\n"
"        samplerate, win_s, hop_s = 4000, 128, 64 \n"
"        # fast\n"
"        samplerate, win_s, hop_s = 8000, 512, 128\n"
"        # default:\n"
"        samplerate, win_s, hop_s = 44100, 1024, 512", None))

