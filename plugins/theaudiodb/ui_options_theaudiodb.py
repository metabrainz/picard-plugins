# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_theaudiodb.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_TheAudioDbOptionsPage(object):
    def setupUi(self, TheAudioDbOptionsPage):
        TheAudioDbOptionsPage.setObjectName("TheAudioDbOptionsPage")
        TheAudioDbOptionsPage.resize(442, 364)
        self.vboxlayout = QtWidgets.QVBoxLayout(TheAudioDbOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox = QtWidgets.QGroupBox(TheAudioDbOptionsPage)
        self.groupBox.setObjectName("groupBox")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setObjectName("label")
        self.vboxlayout1.addWidget(self.label)
        self.vboxlayout.addWidget(self.groupBox)
        self.verticalGroupBox = QtWidgets.QGroupBox(TheAudioDbOptionsPage)
        self.verticalGroupBox.setObjectName("verticalGroupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalGroupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.theaudiodb_cdart_use_always = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.theaudiodb_cdart_use_always.setObjectName("theaudiodb_cdart_use_always")
        self.verticalLayout.addWidget(self.theaudiodb_cdart_use_always)
        self.theaudiodb_cdart_use_if_no_albumcover = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.theaudiodb_cdart_use_if_no_albumcover.setObjectName("theaudiodb_cdart_use_if_no_albumcover")
        self.verticalLayout.addWidget(self.theaudiodb_cdart_use_if_no_albumcover)
        self.theaudiodb_cdart_use_never = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.theaudiodb_cdart_use_never.setObjectName("theaudiodb_cdart_use_never")
        self.verticalLayout.addWidget(self.theaudiodb_cdart_use_never)
        self.vboxlayout.addWidget(self.verticalGroupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)

        self.retranslateUi(TheAudioDbOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(TheAudioDbOptionsPage)

    def retranslateUi(self, TheAudioDbOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox.setTitle(_translate("TheAudioDbOptionsPage", "TheAudioDB cover art"))
        self.label.setText(_translate("TheAudioDbOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This plugin loads cover art from <a href=\"https://www.theaudiodb.com\"><span style=\" text-decoration: underline; color:#1b6acb;\">TheAudioDB</span></a>. TheAudioDB is a community Database of audio artwork and data. Their content is only possible thanks to the hard work of volunteer editors. If you like this plugin, please consider <a href=\"https://www.theaudiodb.com/forum-new/ucp.php?mode=register\"><span style=\" text-decoration: underline; color:#1b6acb;\">registering</span></a> as an editor or supporting the TheAudioDB <a href=\"https://www.patreon.com/thedatadb\"><span style=\" text-decoration: underline; color:#1b6acb;\">patreon campaign</span></a>.</p></body></html>"))
        self.verticalGroupBox.setTitle(_translate("TheAudioDbOptionsPage", "Medium images"))
        self.theaudiodb_cdart_use_always.setText(_translate("TheAudioDbOptionsPage", "Always load medium images"))
        self.theaudiodb_cdart_use_if_no_albumcover.setText(_translate("TheAudioDbOptionsPage", "Load only if no front cover is available"))
        self.theaudiodb_cdart_use_never.setText(_translate("TheAudioDbOptionsPage", "Never load medium images"))
