# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MoodbarOptionsPage(object):
    def setupUi(self, MoodbarOptionsPage):
        MoodbarOptionsPage.setObjectName("MoodbarOptionsPage")
        MoodbarOptionsPage.resize(305, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(MoodbarOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.moodbar_group = QtWidgets.QGroupBox(MoodbarOptionsPage)
        self.moodbar_group.setObjectName("moodbar_group")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.moodbar_group)
        self.vboxlayout1.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.label = QtWidgets.QLabel(self.moodbar_group)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)
        self.vorbis_command = QtWidgets.QLineEdit(self.moodbar_group)
        self.vorbis_command.setObjectName("vorbis_command")
        self.vboxlayout1.addWidget(self.vorbis_command)
        self.label_2 = QtWidgets.QLabel(self.moodbar_group)
        self.label_2.setObjectName("label_2")
        self.vboxlayout1.addWidget(self.label_2)
        self.mp3_command = QtWidgets.QLineEdit(self.moodbar_group)
        self.mp3_command.setObjectName("mp3_command")
        self.vboxlayout1.addWidget(self.mp3_command)
        self.label_3 = QtWidgets.QLabel(self.moodbar_group)
        self.label_3.setObjectName("label_3")
        self.vboxlayout1.addWidget(self.label_3)
        self.flac_command = QtWidgets.QLineEdit(self.moodbar_group)
        self.flac_command.setObjectName("flac_command")
        self.vboxlayout1.addWidget(self.flac_command)
        self.label_4 = QtWidgets.QLabel(self.moodbar_group)
        self.label_4.setObjectName("label_4")
        self.vboxlayout1.addWidget(self.label_4)
        self.wav_command = QtWidgets.QLineEdit(self.moodbar_group)
        self.wav_command.setObjectName("wav_command")
        self.vboxlayout1.addWidget(self.wav_command)
        self.vboxlayout.addWidget(self.moodbar_group)
        spacerItem = QtWidgets.QSpacerItem(263, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(MoodbarOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MoodbarOptionsPage)

    def retranslateUi(self, MoodbarOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.moodbar_group.setTitle(_("Moodbar"))
        self.label.setText(_("Path to Ogg Vorbis moodbar tool:"))
        self.label_2.setText(_("Path to MP3 moodbar tool:"))
        self.label_3.setText(_("Path to FLAC moodbar tool:"))
        self.label_4.setText(_("Path to WAV moodbar tool:"))

