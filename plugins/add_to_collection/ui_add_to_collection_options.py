from PyQt5 import QtCore, QtWidgets


class Ui_AddToCollectionOptions(object):
    def setupUi(self, AddToCollectionOptions):
        AddToCollectionOptions.setObjectName("AddToCollectionOptions")
        AddToCollectionOptions.resize(472, 215)
        self.verticalLayout = QtWidgets.QVBoxLayout(AddToCollectionOptions)
        self.verticalLayout.setObjectName("verticalLayout")
        self.collection_label = QtWidgets.QLabel(AddToCollectionOptions)
        self.collection_label.setObjectName("collection_label")
        self.verticalLayout.addWidget(self.collection_label)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed
        )
        self.collection_name = QtWidgets.QComboBox(AddToCollectionOptions)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.collection_name.sizePolicy().hasHeightForWidth()
        )
        self.collection_name.setSizePolicy(sizePolicy)
        self.collection_name.setEditable(False)
        self.collection_name.setObjectName("collection_name")
        self.verticalLayout.addWidget(self.collection_name)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(AddToCollectionOptions)
        QtCore.QMetaObject.connectSlotsByName(AddToCollectionOptions)

    def retranslateUi(self, AddToCollectionOptions):
        _translate = QtCore.QCoreApplication.translate
        AddToCollectionOptions.setWindowTitle(_("Form"))
        self.collection_label.setText(_("Collection to add releases to:"))
