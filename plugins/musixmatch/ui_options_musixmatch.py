from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MusixmatchOptionsPage(object):
    def setupUi(self, MusixmatchOptionsPage):
        MusixmatchOptionsPage.setObjectName(_fromUtf8("MusixmatchOptionsPage"))
        MusixmatchOptionsPage.resize(305, 317)
        self.vboxlayout = QtGui.QVBoxLayout(MusixmatchOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.api_key_group = QtGui.QGroupBox(MusixmatchOptionsPage)
        self.api_key_group.setObjectName(_fromUtf8("api_key_group"))
        self.vboxlayout2 = QtGui.QVBoxLayout(self.api_key_group)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName(_fromUtf8("vboxlayout2"))
        self.api_key_label = QtGui.QLabel(self.api_key_group)
        self.api_key_label.setObjectName(_fromUtf8("api_key_label"))
        self.vboxlayout2.addWidget(self.api_key_label)
        self.api_key = QtGui.QLineEdit(self.api_key_group)
        self.api_key.setObjectName(_fromUtf8("api_key"))
        self.vboxlayout2.addWidget(self.api_key)
        self.vboxlayout.addWidget(self.api_key_group)
        spacerItem = QtGui.QSpacerItem(263, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(MusixmatchOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(MusixmatchOptionsPage)




    def retranslateUi(self, MusixmatchOptionsPage):
        self.api_key_label.setText(_("Musixmatch API Key"))
