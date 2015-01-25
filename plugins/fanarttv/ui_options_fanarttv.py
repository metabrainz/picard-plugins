# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

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

class Ui_FanartTvOptionsPage(object):
    def setupUi(self, FanartTvOptionsPage):
        FanartTvOptionsPage.setObjectName(_fromUtf8("FanartTvOptionsPage"))
        FanartTvOptionsPage.resize(340, 317)
        self.vboxlayout = QtGui.QVBoxLayout(FanartTvOptionsPage)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.groupBox = QtGui.QGroupBox(FanartTvOptionsPage)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.groupBox)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setAutoFillBackground(False)
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.vboxlayout1.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout1.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.vboxlayout1.addWidget(self.label_2)
        self.fanarttv_client_key = QtGui.QLineEdit(self.groupBox)
        self.fanarttv_client_key.setObjectName(_fromUtf8("fanarttv_client_key"))
        self.vboxlayout1.addWidget(self.fanarttv_client_key)
        self.vboxlayout.addWidget(self.groupBox)
        self.verticalGroupBox = QtGui.QGroupBox(FanartTvOptionsPage)
        self.verticalGroupBox.setObjectName(_fromUtf8("verticalGroupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalGroupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.fanarttv_cdart_use_always = QtGui.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_always.setObjectName(_fromUtf8("fanarttv_cdart_use_always"))
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_always)
        self.fanarttv_cdart_use_if_no_albumcover = QtGui.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_if_no_albumcover.setObjectName(_fromUtf8("fanarttv_cdart_use_if_no_albumcover"))
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_if_no_albumcover)
        self.fanarttv_cdart_use_never = QtGui.QRadioButton(self.verticalGroupBox)
        self.fanarttv_cdart_use_never.setObjectName(_fromUtf8("fanarttv_cdart_use_never"))
        self.verticalLayout.addWidget(self.fanarttv_cdart_use_never)
        self.vboxlayout.addWidget(self.verticalGroupBox)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem2)

        self.retranslateUi(FanartTvOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(FanartTvOptionsPage)

    def retranslateUi(self, FanartTvOptionsPage):
        self.groupBox.setTitle(_("fanart.tv cover art"))
        self.label.setText(_translate("FanartTvOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Cantarell\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">This plugin loads cover art from <a href=\"http://fanart.tv/\"><span style=\" text-decoration: underline; color:#0000ff;\">fanart.tv</span></a>. If you want to improve the results of this plugin please contribute.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">In order to use this plugin you have to register a personal API key on<br /><a href=\"https://fanart.tv/get-an-api-key/\"><span style=\" text-decoration: underline; color:#0000ff;\">https://fanart.tv/get-an-api-key/</span></a></p></body></html>", None))
        self.label_2.setText(_("Enter your personal API key here:"))
        self.verticalGroupBox.setTitle(_("Medium images"))
        self.fanarttv_cdart_use_always.setText(_("Always load medium images"))
        self.fanarttv_cdart_use_if_no_albumcover.setText(_("Load only if no front cover is available"))
        self.fanarttv_cdart_use_never.setText(_("Never load medium images"))

