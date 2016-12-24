# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtWidgets


class Ui_ReplayGainOptionsPage(object):
    def setupUi(self, ReplayGainOptionsPage):
        ReplayGainOptionsPage.setObjectName("ReplayGainOptionsPage")
        ReplayGainOptionsPage.resize(305, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(ReplayGainOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.replay_gain = QtWidgets.QGroupBox(ReplayGainOptionsPage)
        self.replay_gain.setObjectName("replay_gain")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.replay_gain)
        self.vboxlayout1.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.label = QtWidgets.QLabel(self.replay_gain)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)
        self.vorbisgain_command = QtWidgets.QLineEdit(self.replay_gain)
        self.vorbisgain_command.setObjectName("vorbisgain_command")
        self.vboxlayout1.addWidget(self.vorbisgain_command)
        self.label_2 = QtWidgets.QLabel(self.replay_gain)
        self.label_2.setObjectName("label_2")
        self.vboxlayout1.addWidget(self.label_2)
        self.mp3gain_command = QtWidgets.QLineEdit(self.replay_gain)
        self.mp3gain_command.setObjectName("mp3gain_command")
        self.vboxlayout1.addWidget(self.mp3gain_command)
        self.label_3 = QtWidgets.QLabel(self.replay_gain)
        self.label_3.setObjectName("label_3")
        self.vboxlayout1.addWidget(self.label_3)
        self.metaflac_command = QtWidgets.QLineEdit(self.replay_gain)
        self.metaflac_command.setObjectName("metaflac_command")
        self.vboxlayout1.addWidget(self.metaflac_command)
        self.label_4 = QtWidgets.QLabel(self.replay_gain)
        self.label_4.setObjectName("label_4")
        self.vboxlayout1.addWidget(self.label_4)
        self.wvgain_command = QtWidgets.QLineEdit(self.replay_gain)
        self.wvgain_command.setObjectName("wvgain_command")
        self.vboxlayout1.addWidget(self.wvgain_command)
        self.vboxlayout.addWidget(self.replay_gain)
        spacerItem = QtWidgets.QSpacerItem(263, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(ReplayGainOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(ReplayGainOptionsPage)

    def retranslateUi(self, ReplayGainOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.replay_gain.setTitle(_("Replay Gain"))
        self.label.setText(_("Path to VorbisGain:"))
        self.label_2.setText(_("Path to MP3Gain:"))
        self.label_3.setText(_("Path to metaflac:"))
        self.label_4.setText(_("Path to wvgain:"))
