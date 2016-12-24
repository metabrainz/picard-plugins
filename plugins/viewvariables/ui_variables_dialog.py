# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python setup.py build_ui` to update it.

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_VariablesDialog(object):
    def setupUi(self, VariablesDialog):
        VariablesDialog.setObjectName("VariablesDialog")
        VariablesDialog.resize(600, 450)
        self.verticalLayout = QtWidgets.QVBoxLayout(VariablesDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.metadata_table = QtWidgets.QTableWidget(VariablesDialog)
        self.metadata_table.setAutoFillBackground(False)
        self.metadata_table.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.metadata_table.setRowCount(1)
        self.metadata_table.setColumnCount(2)
        self.metadata_table.setObjectName("metadata_table")
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.metadata_table.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.metadata_table.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
        self.metadata_table.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
        self.metadata_table.setItem(0, 1, item)
        self.metadata_table.horizontalHeader().setDefaultSectionSize(150)
        self.metadata_table.horizontalHeader().setSortIndicatorShown(False)
        self.metadata_table.horizontalHeader().setStretchLastSection(True)
        self.metadata_table.verticalHeader().setVisible(False)
        self.metadata_table.verticalHeader().setDefaultSectionSize(20)
        self.metadata_table.verticalHeader().setMinimumSectionSize(20)
        self.verticalLayout.addWidget(self.metadata_table)
        self.buttonBox = QtWidgets.QDialogButtonBox(VariablesDialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(VariablesDialog)
        QtCore.QMetaObject.connectSlotsByName(VariablesDialog)

    def retranslateUi(self, VariablesDialog):
        _translate = QtCore.QCoreApplication.translate
        item = self.metadata_table.horizontalHeaderItem(0)
        item.setText(_("Variable"))
        item = self.metadata_table.horizontalHeaderItem(1)
        item.setText(_("Value"))
        __sortingEnabled = self.metadata_table.isSortingEnabled()
        self.metadata_table.setSortingEnabled(False)
        self.metadata_table.setSortingEnabled(__sortingEnabled)
