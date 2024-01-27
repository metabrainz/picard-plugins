# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'options_enhanced_titles.ui'
##
## Created by: Qt User Interface Compiler version 6.6.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PyQt5.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFrame, QGroupBox,
    QLabel, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_EnhancedTitlesOptions(object):
    def setupUi(self, EnhancedTitlesOptions):
        if not EnhancedTitlesOptions.objectName():
            EnhancedTitlesOptions.setObjectName(u"EnhancedTitlesOptions")
        EnhancedTitlesOptions.setMinimumSize(QSize(100, 0))
        self.verticalLayout = QVBoxLayout(EnhancedTitlesOptions)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(EnhancedTitlesOptions)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 379, 502))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.titles_all_caps = QGroupBox(self.scrollAreaWidgetContents)
        self.titles_all_caps.setObjectName(u"titles_all_caps")
        self.verticalLayout_6 = QVBoxLayout(self.titles_all_caps)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.label_4 = QLabel(self.titles_all_caps)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setMouseTracking(True)
        self.label_4.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.label_4)

        self.check_allcaps = QCheckBox(self.titles_all_caps)
        self.check_allcaps.setObjectName(u"check_allcaps")

        self.verticalLayout_6.addWidget(self.check_allcaps)


        self.verticalLayout_2.addWidget(self.titles_all_caps)

        self.check_for_sort_names = QGroupBox(self.scrollAreaWidgetContents)
        self.check_for_sort_names.setObjectName(u"check_for_sort_names")
        self.verticalLayout_3 = QVBoxLayout(self.check_for_sort_names)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label = QLabel(self.check_for_sort_names)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label)

        self.check_tagging = QCheckBox(self.check_for_sort_names)
        self.check_tagging.setObjectName(u"check_tagging")
        self.check_tagging.setChecked(True)

        self.verticalLayout_3.addWidget(self.check_tagging)

        self.label_2 = QLabel(self.check_for_sort_names)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label_2)

        self.check_album_aliases = QCheckBox(self.check_for_sort_names)
        self.check_album_aliases.setObjectName(u"check_album_aliases")
        self.check_album_aliases.setCheckable(True)
        self.check_album_aliases.setChecked(True)

        self.verticalLayout_3.addWidget(self.check_album_aliases)

        self.check_track_aliases = QCheckBox(self.check_for_sort_names)
        self.check_track_aliases.setObjectName(u"check_track_aliases")

        self.verticalLayout_3.addWidget(self.check_track_aliases)


        self.verticalLayout_2.addWidget(self.check_for_sort_names)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)


        self.retranslateUi(EnhancedTitlesOptions)

        QMetaObject.connectSlotsByName(EnhancedTitlesOptions)
    # setupUi

    def retranslateUi(self, EnhancedTitlesOptions):
        EnhancedTitlesOptions.setWindowTitle(QCoreApplication.translate("EnhancedTitlesOptions", u"Form", None))
        self.titles_all_caps.setTitle(QCoreApplication.translate("EnhancedTitlesOptions", u"Titles in All Caps", None))
        self.label_4.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"If this option is enabled, text in all caps will not be affected by the $title_lang script function.", None))
        self.check_allcaps.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"Ignore titles in all caps.", None))
        self.check_for_sort_names.setTitle(QCoreApplication.translate("EnhancedTitlesOptions", u"Tagging", None))
        self.label.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"<html><head/><body><p>If this option is enabled, the fields albumsort and titlesort will be filled. If you are only interested in the scripting functions, then disable this to reduce the time it takes to load releases.</p></body></html>", None))
        self.check_tagging.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"Tag albumsort and titlesort fields", None))
        self.label_2.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"<html><head/><body><p>If this option is enabled, the plugin will first check if there are any sort names already available in MusicBrainz. Otherwise, it will swap the title's prefix directly. Enabling this option will increase the time it takes to load releases, especially for tracks.</p></body></html>", None))
        self.check_album_aliases.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"Check for album aliases", None))
        self.check_track_aliases.setText(QCoreApplication.translate("EnhancedTitlesOptions", u"Check for track aliases", None))
    # retranslateUi

