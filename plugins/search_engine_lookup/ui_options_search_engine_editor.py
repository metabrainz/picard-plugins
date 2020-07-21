# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python devtools.py ui --compile` to update it.
#
# Form implementation generated from reading ui file 'ui\options_search_engine_editor.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_SearchEngineEditorDialog(object):
    def setupUi(self, SearchEngineEditorDialog):
        SearchEngineEditorDialog.setObjectName("SearchEngineEditorDialog")
        SearchEngineEditorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SearchEngineEditorDialog.resize(560, 261)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SearchEngineEditorDialog.sizePolicy().hasHeightForWidth())
        SearchEngineEditorDialog.setSizePolicy(sizePolicy)
        SearchEngineEditorDialog.setMinimumSize(QtCore.QSize(360, 0))
        self.verticalLayout = QtWidgets.QVBoxLayout(SearchEngineEditorDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(SearchEngineEditorDialog)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 542, 243))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_4 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_2.addWidget(self.label_4)
        spacerItem = QtWidgets.QSpacerItem(20, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setContentsMargins(-1, -1, -1, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.le_title = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.le_title.setFont(font)
        self.le_title.setToolTipDuration(-1)
        self.le_title.setObjectName("le_title")
        self.gridLayout.addWidget(self.le_title, 0, 1, 1, 1)
        self.le_url = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.le_url.setFont(font)
        self.le_url.setObjectName("le_url")
        self.gridLayout.addWidget(self.le_url, 1, 1, 1, 1)
        self.img_valid_title = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.img_valid_title.setMinimumSize(QtCore.QSize(16, 16))
        self.img_valid_title.setText("")
        self.img_valid_title.setObjectName("img_valid_title")
        self.gridLayout.addWidget(self.img_valid_title, 0, 2, 1, 1)
        self.img_valid_url = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.img_valid_url.setMinimumSize(QtCore.QSize(16, 16))
        self.img_valid_url.setText("")
        self.img_valid_url.setObjectName("img_valid_url")
        self.gridLayout.addWidget(self.img_valid_url, 1, 2, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pb_save = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pb_save.setObjectName("pb_save")
        self.horizontalLayout.addWidget(self.pb_save)
        self.pb_cancel = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pb_cancel.setObjectName("pb_cancel")
        self.horizontalLayout.addWidget(self.pb_cancel)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(SearchEngineEditorDialog)
        QtCore.QMetaObject.connectSlotsByName(SearchEngineEditorDialog)

    def retranslateUi(self, SearchEngineEditorDialog):
        _translate = QtCore.QCoreApplication.translate
        SearchEngineEditorDialog.setWindowTitle(_translate("SearchEngineEditorDialog", "Edit Search Engine Provider"))
        self.label_4.setText(_translate("SearchEngineEditorDialog", "<html><head/><body><p>Enter the title and URL for the search engine provider. Titles must be at least two non-space characters long, and must not be the same as the title of an existing provider.</p><p>When entering the URL the macro <span style=\"font-weight:600;\">%search%</span> must be included. This will be replaced by the list of search words separated by plus signs when the url is sent to your browser for display.</p></body></html>"))
        self.label_2.setText(_translate("SearchEngineEditorDialog", "Title:"))
        self.label_3.setText(_translate("SearchEngineEditorDialog", "URL:"))
        self.le_title.setToolTip(_translate("SearchEngineEditorDialog", "The title to show in the list for the search engine provider"))
        self.le_url.setToolTip(_translate("SearchEngineEditorDialog", "The URL to use for the search engine provider"))
        self.pb_save.setText(_translate("SearchEngineEditorDialog", "Save"))
        self.pb_cancel.setText(_translate("SearchEngineEditorDialog", "Cancel"))
