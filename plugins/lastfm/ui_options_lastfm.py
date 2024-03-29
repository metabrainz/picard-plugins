# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plugins/lastfm/ui_options_lastfm.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LastfmOptionsPage(object):
    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName("LastfmOptionsPage")
        LastfmOptionsPage.resize(305, 317)
        self.vboxlayout = QtWidgets.QVBoxLayout(LastfmOptionsPage)
        self.vboxlayout.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.rename_files = QtWidgets.QGroupBox(LastfmOptionsPage)
        self.rename_files.setObjectName("rename_files")
        self.vboxlayout1 = QtWidgets.QVBoxLayout(self.rename_files)
        self.vboxlayout1.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout1.setSpacing(2)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.use_track_tags = QtWidgets.QCheckBox(self.rename_files)
        self.use_track_tags.setObjectName("use_track_tags")
        self.vboxlayout1.addWidget(self.use_track_tags)
        self.use_artist_tags = QtWidgets.QCheckBox(self.rename_files)
        self.use_artist_tags.setObjectName("use_artist_tags")
        self.vboxlayout1.addWidget(self.use_artist_tags)
        self.vboxlayout.addWidget(self.rename_files)
        self.rename_files_2 = QtWidgets.QGroupBox(LastfmOptionsPage)
        self.rename_files_2.setObjectName("rename_files_2")
        self.vboxlayout2 = QtWidgets.QVBoxLayout(self.rename_files_2)
        self.vboxlayout2.setContentsMargins(9, 9, 9, 9)
        self.vboxlayout2.setSpacing(2)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.ignore_tags_2 = QtWidgets.QLabel(self.rename_files_2)
        self.ignore_tags_2.setObjectName("ignore_tags_2")
        self.vboxlayout2.addWidget(self.ignore_tags_2)
        self.ignore_tags = QtWidgets.QLineEdit(self.rename_files_2)
        self.ignore_tags.setObjectName("ignore_tags")
        self.vboxlayout2.addWidget(self.ignore_tags)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.ignore_tags_4 = QtWidgets.QLabel(self.rename_files_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(4)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ignore_tags_4.sizePolicy().hasHeightForWidth())
        self.ignore_tags_4.setSizePolicy(sizePolicy)
        self.ignore_tags_4.setObjectName("ignore_tags_4")
        self.hboxlayout.addWidget(self.ignore_tags_4)
        self.join_tags = QtWidgets.QComboBox(self.rename_files_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.join_tags.sizePolicy().hasHeightForWidth())
        self.join_tags.setSizePolicy(sizePolicy)
        self.join_tags.setEditable(True)
        self.join_tags.setObjectName("join_tags")
        self.join_tags.addItem("")
        self.join_tags.setItemText(0, "")
        self.join_tags.addItem("")
        self.join_tags.addItem("")
        self.hboxlayout.addWidget(self.join_tags)
        self.vboxlayout2.addLayout(self.hboxlayout)
        self.hboxlayout1 = QtWidgets.QHBoxLayout()
        self.hboxlayout1.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.label_4 = QtWidgets.QLabel(self.rename_files_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.hboxlayout1.addWidget(self.label_4)
        self.min_tag_usage = QtWidgets.QSpinBox(self.rename_files_2)
        self.min_tag_usage.setMaximum(100)
        self.min_tag_usage.setObjectName("min_tag_usage")
        self.hboxlayout1.addWidget(self.min_tag_usage)
        self.vboxlayout2.addLayout(self.hboxlayout1)
        self.vboxlayout.addWidget(self.rename_files_2)
        spacerItem = QtWidgets.QSpacerItem(263, 21, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.label_4.setBuddy(self.min_tag_usage)

        self.retranslateUi(LastfmOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.use_track_tags, self.ignore_tags)

    def retranslateUi(self, LastfmOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        self.rename_files.setTitle(_translate("LastfmOptionsPage", "Last.fm"))
        self.use_track_tags.setText(_translate("LastfmOptionsPage", "Use track tags"))
        self.use_artist_tags.setText(_translate("LastfmOptionsPage", "Use artist tags"))
        self.rename_files_2.setTitle(_translate("LastfmOptionsPage", "Tags"))
        self.ignore_tags_2.setText(_translate("LastfmOptionsPage", "Ignore tags:"))
        self.ignore_tags_4.setText(_translate("LastfmOptionsPage", "Join multiple tags with:"))
        self.join_tags.setItemText(1, _translate("LastfmOptionsPage", " / "))
        self.join_tags.setItemText(2, _translate("LastfmOptionsPage", ", "))
        self.label_4.setText(_translate("LastfmOptionsPage", "Minimal tag usage:"))
        self.min_tag_usage.setSuffix(_translate("LastfmOptionsPage", " %"))
