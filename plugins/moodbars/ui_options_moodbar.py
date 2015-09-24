# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_moodbar.ui'
#
# Created: Thu Sep 24 14:14:45 2015
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

class Ui_MoodbarOptionsPage(object):
    def setupUi(self, MoodbarOptionsPage):
        MoodbarOptionsPage.setObjectName(_fromUtf8("MoodbarOptionsPage"))
        MoodbarOptionsPage.resize(305, 317)
        self.vboxlayout = QtGui.QVBoxLayout(MoodbarOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.moodbar_group = QtGui.QGroupBox(MoodbarOptionsPage)
        self.moodbar_group.setObjectName(_fromUtf8("moodbar_group"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.moodbar_group)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.label = QtGui.QLabel(self.moodbar_group)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout1.addWidget(self.label)
        self.vorbis_command = QtGui.QLineEdit(self.moodbar_group)
        self.vorbis_command.setObjectName(_fromUtf8("vorbis_command"))
        self.vboxlayout1.addWidget(self.vorbis_command)
        self.label_2 = QtGui.QLabel(self.moodbar_group)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.vboxlayout1.addWidget(self.label_2)
        self.mp3_command = QtGui.QLineEdit(self.moodbar_group)
        self.mp3_command.setObjectName(_fromUtf8("mp3_command"))
        self.vboxlayout1.addWidget(self.mp3_command)
        self.label_3 = QtGui.QLabel(self.moodbar_group)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.vboxlayout1.addWidget(self.label_3)
        self.flac_command = QtGui.QLineEdit(self.moodbar_group)
        self.flac_command.setObjectName(_fromUtf8("flac_command"))
        self.vboxlayout1.addWidget(self.flac_command)
        self.label_4 = QtGui.QLabel(self.moodbar_group)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.vboxlayout1.addWidget(self.label_4)
        self.wav_command = QtGui.QLineEdit(self.moodbar_group)
        self.wav_command.setObjectName(_fromUtf8("wav_command"))
        self.vboxlayout1.addWidget(self.wav_command)
        self.vboxlayout.addWidget(self.moodbar_group)
        spacerItem = QtGui.QSpacerItem(263, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(MoodbarOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MoodbarOptionsPage)

    def retranslateUi(self, MoodbarOptionsPage):
        self.moodbar_group.setTitle(_translate("MoodbarOptionsPage", "Moodbar", None))
        self.label.setText(_translate("MoodbarOptionsPage", "Path to Ogg Vorbis moodbar tool:", None))
        self.label_2.setText(_translate("MoodbarOptionsPage", "Path to MP3 moodbar tool:", None))
        self.label_3.setText(_translate("MoodbarOptionsPage", "Path to FLAC moodbar tool:", None))
        self.label_4.setText(_translate("MoodbarOptionsPage", "Path to WAV moodbar tool:", None))

