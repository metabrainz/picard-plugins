# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtWidgets


class Ui_FanartTvOptionsPage(object):
    def setupUi(self, FanartTvOptionsPage):
        FanartTvOptionsPage.setObjectName("FanartTvOptionsPage")
        FanartTvOptionsPage.resize(340, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(FanartTvOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.groupBox = QtWidgets.QGroupBox(FanartTvOptionsPage)
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
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout1.addItem(spacerItem)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.vboxlayout1.addWidget(self.label_2)
        self.fanarttv_client_key = QtWidgets.QLineEdit(self.groupBox)
        self.fanarttv_client_key.setObjectName("fanarttv_client_key")
        self.vboxlayout1.addWidget(self.fanarttv_client_key)
        self.vboxlayout.addWidget(self.groupBox)
        self.verticalGroupBox = QtWidgets.QGroupBox(FanartTvOptionsPage)
        self.verticalGroupBox.setObjectName("verticalGroupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalGroupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.fanarttv_cdart_use_always = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_always.setObjectName("fanarttv_cdart_use_always")
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_always)
        self.fanarttv_cdart_use_if_no_albumcover = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_if_no_albumcover.setObjectName("fanarttv_cdart_use_if_no_albumcover")
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_if_no_albumcover)
        self.fanarttv_cdart_use_never = QtWidgets.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_never.setObjectName("fanarttv_cdart_use_never")
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_never)
        self.vboxlayout.addWidget(self.verticalGroupBox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem2)

        self.retranslateUi(FanartTvOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(FanartTvOptionsPage)

    def retranslateUi(self, FanartTvOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.groupBox.setTitle(_("fanart.tv cover art"))
        self.label.setText(_translate("FanartTvOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This plugin loads cover art from <a href=\"http://fanart.tv/\"><span style=\" text-decoration: underline; color:#0000ff;\">fanart.tv</span></a>. If you want to improve the results of this plugin please contribute.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">In order to use this plugin you have to register a personal API key on<br /><a href=\"https://fanart.tv/get-an-api-key/\"><span style=\" text-decoration: underline; color:#0000ff;\">https://fanart.tv/get-an-api-key/</span></a></p></body></html>"))
        self.label_2.setText(_("Enter your personal API key here:"))
        self.verticalGroupBox.setTitle(_("Medium images"))
        self.fanarttv_cdart_use_always.setText(_("Always load medium images"))
        self.fanarttv_cdart_use_if_no_albumcover.setText(_("Load only if no front cover is available"))
        self.fanarttv_cdart_use_never.setText(_("Never load medium images"))

