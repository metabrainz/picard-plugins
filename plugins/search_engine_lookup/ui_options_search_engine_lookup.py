# -*- coding: utf-8 -*-

# Automatically generated - don't edit.
# Use `python devtools.py ui --compile` to update it.
#
# Form implementation generated from reading ui file 'ui\options_search_engine_lookup.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets


class Ui_SearchEngineLookupOptionsPage(object):
    def setupUi(self, SearchEngineLookupOptionsPage):
        SearchEngineLookupOptionsPage.setObjectName("SearchEngineLookupOptionsPage")
        SearchEngineLookupOptionsPage.resize(561, 802)
        SearchEngineLookupOptionsPage.setMinimumSize(QtCore.QSize(360, 0))
        self.verticalLayout = QtWidgets.QVBoxLayout(SearchEngineLookupOptionsPage)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(SearchEngineLookupOptionsPage)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 543, 784))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gb_description = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.gb_description.setObjectName("gb_description")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.gb_description)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.format_description = QtWidgets.QLabel(self.gb_description)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.format_description.sizePolicy().hasHeightForWidth())
        self.format_description.setSizePolicy(sizePolicy)
        self.format_description.setWordWrap(True)
        self.format_description.setObjectName("format_description")
        self.verticalLayout_3.addWidget(self.format_description)
        self.verticalLayout_2.addWidget(self.gb_description)
        self.gb_search_engine = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.gb_search_engine.setMinimumSize(QtCore.QSize(0, 0))
        self.gb_search_engine.setObjectName("gb_search_engine")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.gb_search_engine)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.rb_google = QtWidgets.QRadioButton(self.gb_search_engine)
        self.rb_google.setChecked(True)
        self.rb_google.setObjectName("rb_google")
        self.verticalLayout_4.addWidget(self.rb_google)
        self.rb_bing = QtWidgets.QRadioButton(self.gb_search_engine)
        self.rb_bing.setObjectName("rb_bing")
        self.verticalLayout_4.addWidget(self.rb_bing)
        self.rb_duckduckgo = QtWidgets.QRadioButton(self.gb_search_engine)
        self.rb_duckduckgo.setObjectName("rb_duckduckgo")
        self.verticalLayout_4.addWidget(self.rb_duckduckgo)
        self.verticalLayout_2.addWidget(self.gb_search_engine)
        self.groupBox = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout_5.addWidget(self.label)
        self.le_additional_words = QtWidgets.QLineEdit(self.groupBox)
        self.le_additional_words.setObjectName("le_additional_words")
        self.verticalLayout_5.addWidget(self.le_additional_words)
        self.verticalLayout_2.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)

        self.retranslateUi(SearchEngineLookupOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(SearchEngineLookupOptionsPage)

    def retranslateUi(self, SearchEngineLookupOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        SearchEngineLookupOptionsPage.setWindowTitle(_translate("SearchEngineLookupOptionsPage", "Form"))
        self.gb_description.setTitle(_translate("SearchEngineLookupOptionsPage", "Search Engine Lookup"))
        self.format_description.setText(_translate("SearchEngineLookupOptionsPage", "<html><head/><body><p>The Search Engine Lookup plugin allows you to initiate a search engine lookup in your browser for a cluster from the menue displayed when right-clicking the cluster.</p><p>These settings allow you select which search engine to use for the lookup.</p></body></html>"))
        self.gb_search_engine.setTitle(_translate("SearchEngineLookupOptionsPage", "Search Engine Provider"))
        self.rb_google.setText(_translate("SearchEngineLookupOptionsPage", "Google"))
        self.rb_bing.setText(_translate("SearchEngineLookupOptionsPage", "Bing"))
        self.rb_duckduckgo.setText(_translate("SearchEngineLookupOptionsPage", "DuckDuckGo"))
        self.groupBox.setTitle(_translate("SearchEngineLookupOptionsPage", "Additional Search Words"))
        self.label.setText(_translate("SearchEngineLookupOptionsPage", "<html><head/><body><p>By default, the search parameters used are the artist name and album name if they are available in the metadata. You have the option of specifying additional words to be added to the search parameters (e.g.: album).</p><p>Additional words are entered below and should be separated by spaces.</p></body></html>"))
