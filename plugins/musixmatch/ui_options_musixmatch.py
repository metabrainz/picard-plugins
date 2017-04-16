from PyQt5 import QtCore, QtWidgets


class Ui_MusixmatchOptionsPage(object):

    def setupUi(self, MusixmatchOptionsPage):
        MusixmatchOptionsPage.setObjectName("MusixmatchOptionsPage")
        MusixmatchOptionsPage.resize(305, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(MusixmatchOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.api_key_group = QtWidgets.QGroupBox(MusixmatchOptionsPage)
        self.api_key_group.setObjectName("api_key_group")
        self.vboxlayout2 = QtWidgets.QVBoxLayout(self.api_key_group)
        self.vboxlayout2.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.api_key_label = QtWidgets.QLabel(self.api_key_group)
        self.api_key_label.setObjectName("api_key_label")
        self.vboxlayout2.addWidget(self.api_key_label)
        self.api_key = QtWidgets.QLineEdit(self.api_key_group)
        self.api_key.setObjectName("api_key")
        self.vboxlayout2.addWidget(self.api_key)
        self.vboxlayout.addWidget(self.api_key_group)
        spacerItem = QtWidgets.QSpacerItem(263, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(MusixmatchOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MusixmatchOptionsPage)

    def retranslateUi(self, MusixmatchOptionsPage):
        self.api_key_label.setText(_("Musixmatch API Key"))
