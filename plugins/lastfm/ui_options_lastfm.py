# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options_lastfm.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
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

class Ui_LastfmOptionsPage(object):
    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName(_fromUtf8("LastfmOptionsPage"))
        LastfmOptionsPage.resize(305, 317)
        self.vboxlayout = QtGui.QVBoxLayout(LastfmOptionsPage)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.rename_files = QtGui.QGroupBox(LastfmOptionsPage)
        self.rename_files.setObjectName(_fromUtf8("rename_files"))
        self.vboxlayout1 = QtGui.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setMargin(9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName(_fromUtf8("vboxlayout1"))
        self.use_track_tags = QtGui.QCheckBox(self.rename_files)
        self.use_track_tags.setObjectName(_fromUtf8("use_track_tags"))
        self.vboxlayout1.addWidget(self.use_track_tags)
        self.use_artist_tags = QtGui.QCheckBox(self.rename_files)
        self.use_artist_tags.setObjectName(_fromUtf8("use_artist_tags"))
        self.vboxlayout1.addWidget(self.use_artist_tags)
        self.vboxlayout.addWidget(self.rename_files)
        self.rename_files_2 = QtGui.QGroupBox(LastfmOptionsPage)
        self.rename_files_2.setObjectName(_fromUtf8("rename_files_2"))
        self.vboxlayout2 = QtGui.QVBoxLayout(self.rename_files_2)
        self.vboxlayout2.setMargin(9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName(_fromUtf8("vboxlayout2"))
        self.ignore_tags_2 = QtGui.QLabel(self.rename_files_2)
        self.ignore_tags_2.setObjectName(_fromUtf8("ignore_tags_2"))
        self.vboxlayout2.addWidget(self.ignore_tags_2)
        self.ignore_tags = QtGui.QLineEdit(self.rename_files_2)
        self.ignore_tags.setObjectName(_fromUtf8("ignore_tags"))
        self.vboxlayout2.addWidget(self.ignore_tags)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.ignore_tags_4 = QtGui.QLabel(self.rename_files_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5), QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ignore_tags_4.sizePolicy().hasHeightForWidth())
        self.ignore_tags_4.setSizePolicy(sizePolicy)
        self.ignore_tags_4.setObjectName(_fromUtf8("ignore_tags_4"))
        self.hboxlayout.addWidget(self.ignore_tags_4)
        self.join_tags = QtGui.QComboBox(self.rename_files_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(5), QtGui.QSizePolicy.Policy(0))
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.join_tags.sizePolicy().hasHeightForWidth())
        self.join_tags.setSizePolicy(sizePolicy)
        self.join_tags.setEditable(True)
        self.join_tags.setObjectName(_fromUtf8("join_tags"))
        self.join_tags.addItem(_fromUtf8(""))
        self.join_tags.setItemText(0, _fromUtf8(""))
        self.join_tags.addItem(_fromUtf8(""))
        self.join_tags.addItem(_fromUtf8(""))
        self.hboxlayout.addWidget(self.join_tags)
        self.vboxlayout2.addLayout(self.hboxlayout)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.label_4 = QtGui.QLabel(self.rename_files_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7), QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.hboxlayout1.addWidget(self.label_4)
        self.min_tag_usage = QtGui.QSpinBox(self.rename_files_2)
        self.min_tag_usage.setMaximum(100)
        self.min_tag_usage.setObjectName(_fromUtf8("min_tag_usage"))
        self.hboxlayout1.addWidget(self.min_tag_usage)
        self.vboxlayout2.addLayout(self.hboxlayout1)
        self.hboxlayout2 = QtGui.QHBoxLayout()
        self.hboxlayout2.setMargin(0)
        self.hboxlayout2.setSpacing(6)
        self.hboxlayout2.setObjectName(_fromUtf8("hboxlayout2"))
        self.label_5 = QtGui.QLabel(self.rename_files_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Policy(7), QtGui.QSizePolicy.Policy(5))
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.hboxlayout2.addWidget(self.label_5)
        self.api_key = QtGui.QLineEdit(self.rename_files_2)
        self.api_key.setObjectName(_fromUtf8("api_key"))
        self.hboxlayout2.addWidget(self.api_key)
        self.vboxlayout2.addLayout(self.hboxlayout2)
        self.vboxlayout.addWidget(self.rename_files_2)
        spacerItem = QtGui.QSpacerItem(263, 21, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.min_tag_usage)
        self.label_5.setBuddy(self.api_key)

        self.retranslateUi(LastfmOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.use_track_tags, self.ignore_tags)

    def retranslateUi(self, LastfmOptionsPage):
        self.rename_files.setTitle(_translate("LastfmOptionsPage", "Last.fm", None))
        self.use_track_tags.setText(_translate("LastfmOptionsPage", "Use track tags", None))
        self.use_artist_tags.setText(_translate("LastfmOptionsPage", "Use artist tags", None))
        self.rename_files_2.setTitle(_translate("LastfmOptionsPage", "Tags", None))
        self.ignore_tags_2.setText(_translate("LastfmOptionsPage", "Ignore tags:", None))
        self.ignore_tags_4.setText(_translate("LastfmOptionsPage", "Join multiple tags with:", None))
        self.join_tags.setItemText(1, _translate("LastfmOptionsPage", " / ", None))
        self.join_tags.setItemText(2, _translate("LastfmOptionsPage", ", ", None))
        self.label_4.setText(_translate("LastfmOptionsPage", "Minimal tag usage:", None))
        self.min_tag_usage.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.label_5.setText(_translate("LastfmOptionsPage", "Last.fm API key:", None))

