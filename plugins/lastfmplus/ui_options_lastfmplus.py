# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_LastfmOptionsPage(object):

    def setupUi(self, LastfmOptionsPage):
        LastfmOptionsPage.setObjectName("LastfmOptionsPage")
        LastfmOptionsPage.resize(414, 493)
        self.horizontalLayout = QtWidgets.QHBoxLayout(LastfmOptionsPage)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(LastfmOptionsPage)
        self.tabWidget.setMinimumSize(QtCore.QSize(330, 475))
        self.tabWidget.setElideMode(QtCore.Qt.ElideNone)
        self.tabWidget.setUsesScrollButtons(False)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_general_options = QtWidgets.QWidget()
        self.tab_general_options.setObjectName("tab_general_options")
        self.gridlayout_tag_general_options = QtWidgets.QGridLayout(self.tab_general_options)
        self.gridlayout_tag_general_options.setObjectName("gridlayout_tag_general_options")
        self.groupbox_max_tags_written = QtWidgets.QGroupBox(self.tab_general_options)
        self.groupbox_max_tags_written.setMinimumSize(QtCore.QSize(0, 0))
        self.groupbox_max_tags_written.setBaseSize(QtCore.QSize(0, 0))
        self.groupbox_max_tags_written.setObjectName("groupbox_max_tags_written")
        self.gridlayout_max_tags_written = QtWidgets.QGridLayout(self.groupbox_max_tags_written)
        self.gridlayout_max_tags_written.setObjectName("gridlayout_max_tags_written")
        self.label_general_major_tags_group = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_general_major_tags_group.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_major_tags_group.setObjectName("label_general_major_tags_group")
        self.gridlayout_max_tags_written.addWidget(self.label_general_major_tags_group, 0, 0, 1, 1)
        self.max_group_tags = QtWidgets.QSpinBox(self.groupbox_max_tags_written)
        self.max_group_tags.setObjectName("max_group_tags")
        self.gridlayout_max_tags_written.addWidget(self.max_group_tags, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 95, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout_max_tags_written.addItem(spacerItem, 0, 2, 4, 1)
        self.label_general_max_mood_tags = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_general_max_mood_tags.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_max_mood_tags.setObjectName("label_general_max_mood_tags")
        self.gridlayout_max_tags_written.addWidget(self.label_general_max_mood_tags, 0, 3, 1, 1)
        self.max_mood_tags = QtWidgets.QSpinBox(self.groupbox_max_tags_written)
        self.max_mood_tags.setObjectName("max_mood_tags")
        self.gridlayout_max_tags_written.addWidget(self.max_mood_tags, 0, 4, 1, 1)
        self.label_general_minor_tags_genre = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_general_minor_tags_genre.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_minor_tags_genre.setObjectName("label_general_minor_tags_genre")
        self.gridlayout_max_tags_written.addWidget(self.label_general_minor_tags_genre, 1, 0, 1, 1)
        self.max_minor_tags = QtWidgets.QSpinBox(self.groupbox_max_tags_written)
        self.max_minor_tags.setObjectName("max_minor_tags")
        self.gridlayout_max_tags_written.addWidget(self.max_minor_tags, 1, 1, 1, 1)
        self.label_general_max_occasion_tags = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_general_max_occasion_tags.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_max_occasion_tags.setObjectName("label_general_max_occasion_tags")
        self.gridlayout_max_tags_written.addWidget(self.label_general_max_occasion_tags, 1, 3, 1, 1)
        self.max_occasion_tags = QtWidgets.QSpinBox(self.groupbox_max_tags_written)
        self.max_occasion_tags.setObjectName("max_occasion_tags")
        self.gridlayout_max_tags_written.addWidget(self.max_occasion_tags, 1, 4, 1, 1)
        self.label_general_max_category_tags = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_general_max_category_tags.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_max_category_tags.setObjectName("label_general_max_category_tags")
        self.gridlayout_max_tags_written.addWidget(self.label_general_max_category_tags, 2, 3, 1, 1)
        self.max_category_tags = QtWidgets.QSpinBox(self.groupbox_max_tags_written)
        self.max_category_tags.setObjectName("max_category_tags")
        self.gridlayout_max_tags_written.addWidget(self.max_category_tags, 2, 4, 1, 1)
        self.app_major2minor_tag = QtWidgets.QCheckBox(self.groupbox_max_tags_written)
        self.app_major2minor_tag.setObjectName("app_major2minor_tag")
        self.gridlayout_max_tags_written.addWidget(self.app_major2minor_tag, 3, 0, 1, 2)
        self.label_tag_filter_list_genres6 = QtWidgets.QLabel(self.groupbox_max_tags_written)
        self.label_tag_filter_list_genres6.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_tag_filter_list_genres6.setObjectName("label_tag_filter_list_genres6")
        self.gridlayout_max_tags_written.addWidget(self.label_tag_filter_list_genres6, 3, 3, 1, 1)
        self.join_tags_sign = QtWidgets.QLineEdit(self.groupbox_max_tags_written)
        self.join_tags_sign.setObjectName("join_tags_sign")
        self.gridlayout_max_tags_written.addWidget(self.join_tags_sign, 3, 4, 1, 1)
        self.gridlayout_tag_general_options.addWidget(self.groupbox_max_tags_written, 0, 0, 1, 1)
        self.groupbox_other_tags = QtWidgets.QGroupBox(self.tab_general_options)
        self.groupbox_other_tags.setObjectName("groupbox_other_tags")
        self.gridlayout_other_tags = QtWidgets.QGridLayout(self.groupbox_other_tags)
        self.gridlayout_other_tags.setObjectName("gridlayout_other_tags")
        self.use_country_tag = QtWidgets.QCheckBox(self.groupbox_other_tags)
        self.use_country_tag.setObjectName("use_country_tag")
        self.gridlayout_other_tags.addWidget(self.use_country_tag, 0, 0, 1, 1)
        self.use_city_tag = QtWidgets.QCheckBox(self.groupbox_other_tags)
        self.use_city_tag.setTristate(False)
        self.use_city_tag.setObjectName("use_city_tag")
        self.gridlayout_other_tags.addWidget(self.use_city_tag, 1, 0, 1, 1)
        self.use_year_tag = QtWidgets.QCheckBox(self.groupbox_other_tags)
        self.use_year_tag.setObjectName("use_year_tag")
        self.gridlayout_other_tags.addWidget(self.use_year_tag, 0, 1, 1, 1)
        self.use_decade_tag = QtWidgets.QCheckBox(self.groupbox_other_tags)
        self.use_decade_tag.setObjectName("use_decade_tag")
        self.gridlayout_other_tags.addWidget(self.use_decade_tag, 1, 1, 1, 1)
        self.gridlayout_tag_general_options.addWidget(self.groupbox_other_tags, 1, 0, 1, 1)
        self.groupbox_track_based_tags = QtWidgets.QGroupBox(self.tab_general_options)
        self.groupbox_track_based_tags.setObjectName("groupbox_track_based_tags")
        self.gridlayout_track_based_tags = QtWidgets.QGridLayout(self.groupbox_track_based_tags)
        self.gridlayout_track_based_tags.setObjectName("gridlayout_track_based_tags")
        self.use_track_tags = QtWidgets.QCheckBox(self.groupbox_track_based_tags)
        self.use_track_tags.setChecked(False)
        self.use_track_tags.setObjectName("use_track_tags")
        self.gridlayout_track_based_tags.addWidget(self.use_track_tags, 0, 0, 1, 1)
        self.label_general_minimum_tag_weight = QtWidgets.QLabel(self.groupbox_track_based_tags)
        self.label_general_minimum_tag_weight.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_general_minimum_tag_weight.setObjectName("label_general_minimum_tag_weight")
        self.gridlayout_track_based_tags.addWidget(self.label_general_minimum_tag_weight, 0, 2, 1, 1)
        self.min_tracktag_weight = QtWidgets.QSpinBox(self.groupbox_track_based_tags)
        self.min_tracktag_weight.setObjectName("min_tracktag_weight")
        self.gridlayout_track_based_tags.addWidget(self.min_tracktag_weight, 0, 3, 1, 1)
        self.label_tag_filter_list_genres0 = QtWidgets.QLabel(self.groupbox_track_based_tags)
        self.label_tag_filter_list_genres0.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_tag_filter_list_genres0.setObjectName("label_tag_filter_list_genres0")
        self.gridlayout_track_based_tags.addWidget(self.label_tag_filter_list_genres0, 1, 2, 1, 1)
        self.max_tracktag_drop = QtWidgets.QSpinBox(self.groupbox_track_based_tags)
        self.max_tracktag_drop.setObjectName("max_tracktag_drop")
        self.gridlayout_track_based_tags.addWidget(self.max_tracktag_drop, 1, 3, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout_track_based_tags.addItem(spacerItem1, 0, 1, 2, 1)
        self.gridlayout_tag_general_options.addWidget(self.groupbox_track_based_tags, 2, 0, 1, 1)
        self.groupbox_artist_based_tags = QtWidgets.QGroupBox(self.tab_general_options)
        self.groupbox_artist_based_tags.setObjectName("groupbox_artist_based_tags")
        self.gridlayout_artist_based_tags = QtWidgets.QGridLayout(self.groupbox_artist_based_tags)
        self.gridlayout_artist_based_tags.setObjectName("gridlayout_artist_based_tags")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridlayout_artist_based_tags.addItem(spacerItem2, 0, 1, 3, 1)
        self.artist_tag_us_no = QtWidgets.QRadioButton(self.groupbox_artist_based_tags)
        self.artist_tag_us_no.setObjectName("artist_tag_us_no")
        self.gridlayout_artist_based_tags.addWidget(self.artist_tag_us_no, 0, 0, 1, 1)
        self.label_tag_filter_list_genres1 = QtWidgets.QLabel(self.groupbox_artist_based_tags)
        self.label_tag_filter_list_genres1.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_tag_filter_list_genres1.setObjectName("label_tag_filter_list_genres1")
        self.gridlayout_artist_based_tags.addWidget(self.label_tag_filter_list_genres1, 0, 2, 1, 1)
        self.artist_tags_weight = QtWidgets.QSpinBox(self.groupbox_artist_based_tags)
        self.artist_tags_weight.setObjectName("artist_tags_weight")
        self.gridlayout_artist_based_tags.addWidget(self.artist_tags_weight, 0, 3, 1, 1)
        self.artist_tag_us_ex = QtWidgets.QRadioButton(self.groupbox_artist_based_tags)
        self.artist_tag_us_ex.setObjectName("artist_tag_us_ex")
        self.gridlayout_artist_based_tags.addWidget(self.artist_tag_us_ex, 1, 0, 1, 1)
        self.label_tag_filter_list_genres2 = QtWidgets.QLabel(self.groupbox_artist_based_tags)
        self.label_tag_filter_list_genres2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_tag_filter_list_genres2.setObjectName("label_tag_filter_list_genres2")
        self.gridlayout_artist_based_tags.addWidget(self.label_tag_filter_list_genres2, 1, 2, 1, 1)
        self.min_artisttag_weight = QtWidgets.QSpinBox(self.groupbox_artist_based_tags)
        self.min_artisttag_weight.setObjectName("min_artisttag_weight")
        self.gridlayout_artist_based_tags.addWidget(self.min_artisttag_weight, 1, 3, 1, 1)
        self.artist_tag_us_yes = QtWidgets.QRadioButton(self.groupbox_artist_based_tags)
        self.artist_tag_us_yes.setObjectName("artist_tag_us_yes")
        self.gridlayout_artist_based_tags.addWidget(self.artist_tag_us_yes, 2, 0, 1, 1)
        self.label_tag_filter_list_genres3 = QtWidgets.QLabel(self.groupbox_artist_based_tags)
        self.label_tag_filter_list_genres3.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.label_tag_filter_list_genres3.setObjectName("label_tag_filter_list_genres3")
        self.gridlayout_artist_based_tags.addWidget(self.label_tag_filter_list_genres3, 2, 2, 1, 1)
        self.max_artisttag_drop = QtWidgets.QSpinBox(self.groupbox_artist_based_tags)
        self.max_artisttag_drop.setObjectName("max_artisttag_drop")
        self.gridlayout_artist_based_tags.addWidget(self.max_artisttag_drop, 2, 3, 1, 1)
        self.gridlayout_tag_general_options.addWidget(self.groupbox_artist_based_tags, 3, 0, 1, 1)
        self.tabWidget.addTab(self.tab_general_options, "")
        self.tab_tag_filter_lists = QtWidgets.QWidget()
        self.tab_tag_filter_lists.setObjectName("tab_tag_filter_lists")
        self.gridlayout_tab_tag_filter_list = QtWidgets.QGridLayout(self.tab_tag_filter_lists)
        self.gridlayout_tab_tag_filter_list.setObjectName("gridlayout_tab_tag_filter_list")
        self.groupbox_tag_lists = QtWidgets.QGroupBox(self.tab_tag_filter_lists)
        self.groupbox_tag_lists.setObjectName("groupbox_tag_lists")
        self.gridLayout = QtWidgets.QGridLayout(self.groupbox_tag_lists)
        self.gridLayout.setObjectName("gridLayout")
        self.label_tag_filter_list_grouping = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_grouping.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_grouping.setObjectName("label_tag_filter_list_grouping")
        self.gridLayout.addWidget(self.label_tag_filter_list_grouping, 0, 0, 1, 1)
        self.genre_major = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_major.setObjectName("genre_major")
        self.gridLayout.addWidget(self.genre_major, 0, 1, 1, 1)
        self.label_tag_filter_list_genres = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_genres.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_genres.setObjectName("label_tag_filter_list_genres")
        self.gridLayout.addWidget(self.label_tag_filter_list_genres, 1, 0, 1, 1)
        self.genre_minor = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_minor.setObjectName("genre_minor")
        self.gridLayout.addWidget(self.genre_minor, 1, 1, 1, 1)
        self.label_tag_filter_list_mood = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_mood.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_mood.setObjectName("label_tag_filter_list_mood")
        self.gridLayout.addWidget(self.label_tag_filter_list_mood, 2, 0, 1, 1)
        self.genre_mood = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_mood.setObjectName("genre_mood")
        self.gridLayout.addWidget(self.genre_mood, 2, 1, 1, 1)
        self.label_tag_filter_list_years = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_years.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_years.setObjectName("label_tag_filter_list_years")
        self.gridLayout.addWidget(self.label_tag_filter_list_years, 3, 0, 1, 1)
        self.genre_year = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_year.setObjectName("genre_year")
        self.gridLayout.addWidget(self.genre_year, 3, 1, 1, 1)
        self.label_tag_filter_list_occasion = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_occasion.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_occasion.setObjectName("label_tag_filter_list_occasion")
        self.gridLayout.addWidget(self.label_tag_filter_list_occasion, 4, 0, 1, 1)
        self.genre_occasion = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_occasion.setObjectName("genre_occasion")
        self.gridLayout.addWidget(self.genre_occasion, 4, 1, 1, 1)
        self.label_tag_filter_list_decades = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_decades.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_decades.setObjectName("label_tag_filter_list_decades")
        self.gridLayout.addWidget(self.label_tag_filter_list_decades, 5, 0, 1, 1)
        self.genre_decade = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_decade.setObjectName("genre_decade")
        self.gridLayout.addWidget(self.genre_decade, 5, 1, 1, 1)
        self.label_tag_filter_list_country = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_country.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_country.setObjectName("label_tag_filter_list_country")
        self.gridLayout.addWidget(self.label_tag_filter_list_country, 6, 0, 1, 1)
        self.genre_country = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_country.setObjectName("genre_country")
        self.gridLayout.addWidget(self.genre_country, 6, 1, 1, 1)
        self.label_tag_filter_list_cities = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_cities.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_cities.setObjectName("label_tag_filter_list_cities")
        self.gridLayout.addWidget(self.label_tag_filter_list_cities, 7, 0, 1, 1)
        self.genre_city = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_city.setObjectName("genre_city")
        self.gridLayout.addWidget(self.genre_city, 7, 1, 1, 1)
        self.label_tag_filter_list_category = QtWidgets.QLabel(self.groupbox_tag_lists)
        self.label_tag_filter_list_category.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_tag_filter_list_category.setObjectName("label_tag_filter_list_category")
        self.gridLayout.addWidget(self.label_tag_filter_list_category, 8, 0, 1, 1)
        self.genre_category = QtWidgets.QLineEdit(self.groupbox_tag_lists)
        self.genre_category.setObjectName("genre_category")
        self.gridLayout.addWidget(self.genre_category, 8, 1, 1, 1)
        self.gridlayout_tab_tag_filter_list.addWidget(self.groupbox_tag_lists, 0, 0, 1, 2)
        self.groupbox_tag_translations = QtWidgets.QGroupBox(self.tab_tag_filter_lists)
        self.groupbox_tag_translations.setObjectName("groupbox_tag_translations")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.groupbox_tag_translations)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.genre_translations = QtWidgets.QTextEdit(self.groupbox_tag_translations)
        self.genre_translations.setObjectName("genre_translations")
        self.horizontalLayout_4.addWidget(self.genre_translations)
        self.gridlayout_tab_tag_filter_list.addWidget(self.groupbox_tag_translations, 1, 0, 1, 1)
        self.groupbox_tools = QtWidgets.QGroupBox(self.tab_tag_filter_lists)
        self.groupbox_tools.setObjectName("groupbox_tools")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupbox_tools)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filter_report = QtWidgets.QPushButton(self.groupbox_tools)
        self.filter_report.setObjectName("filter_report")
        self.verticalLayout.addWidget(self.filter_report)
        self.check_word_lists = QtWidgets.QPushButton(self.groupbox_tools)
        self.check_word_lists.setObjectName("check_word_lists")
        self.verticalLayout.addWidget(self.check_word_lists)
        self.check_translation_list = QtWidgets.QPushButton(self.groupbox_tools)
        self.check_translation_list.setEnabled(False)
        self.check_translation_list.setObjectName("check_translation_list")
        self.verticalLayout.addWidget(self.check_translation_list)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.load_default_lists = QtWidgets.QPushButton(self.groupbox_tools)
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.load_default_lists.setFont(font)
        self.load_default_lists.setObjectName("load_default_lists")
        self.verticalLayout.addWidget(self.load_default_lists)
        self.gridlayout_tab_tag_filter_list.addWidget(self.groupbox_tools, 1, 1, 1, 1)
        self.tabWidget.addTab(self.tab_tag_filter_lists, "")
        self.horizontalLayout.addWidget(self.tabWidget)


        self.groupbox_api_key = QtWidgets.QGroupBox(self.tab_general_options)
        self.groupbox_api_key.setObjectName("groupbox_api_key")

        self.gridlayout_api_key = QtWidgets.QGridLayout(self.groupbox_api_key)
        self.gridlayout_api_key.setObjectName("gridlayout_api_key")

        self.label_api_key = QtWidgets.QLabel(self.groupbox_api_key)
        self.label_api_key.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label_api_key.setObjectName("label_api_key")
        self.gridlayout_api_key.addWidget(self.label_api_key, 0, 0, 1, 1)

        self.api_key = QtWidgets.QLineEdit(self.groupbox_api_key)
        self.api_key.setObjectName("api_key")
        self.gridlayout_api_key.addWidget(self.api_key, 0, 1, 1, 1)

        self.gridlayout_tag_general_options.addWidget(self.groupbox_api_key)


        self.retranslateUi(LastfmOptionsPage)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(LastfmOptionsPage)
        LastfmOptionsPage.setTabOrder(self.max_group_tags, self.max_minor_tags)
        LastfmOptionsPage.setTabOrder(self.max_minor_tags, self.use_track_tags)
        LastfmOptionsPage.setTabOrder(self.use_track_tags, self.min_tracktag_weight)
        LastfmOptionsPage.setTabOrder(self.min_tracktag_weight, self.max_tracktag_drop)
        LastfmOptionsPage.setTabOrder(self.max_tracktag_drop, self.artist_tag_us_no)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_no, self.artist_tag_us_ex)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_ex, self.artist_tag_us_yes)
        LastfmOptionsPage.setTabOrder(self.artist_tag_us_yes, self.artist_tags_weight)
        LastfmOptionsPage.setTabOrder(self.artist_tags_weight, self.min_artisttag_weight)
        LastfmOptionsPage.setTabOrder(self.min_artisttag_weight, self.max_artisttag_drop)
        LastfmOptionsPage.setTabOrder(self.max_artisttag_drop, self.genre_major)
        LastfmOptionsPage.setTabOrder(self.genre_major, self.genre_minor)
        LastfmOptionsPage.setTabOrder(self.genre_minor, self.genre_mood)
        LastfmOptionsPage.setTabOrder(self.genre_mood, self.genre_year)
        LastfmOptionsPage.setTabOrder(self.genre_year, self.genre_occasion)
        LastfmOptionsPage.setTabOrder(self.genre_occasion, self.genre_decade)
        LastfmOptionsPage.setTabOrder(self.genre_decade, self.genre_country)
        LastfmOptionsPage.setTabOrder(self.genre_country, self.genre_category)
        LastfmOptionsPage.setTabOrder(self.genre_category, self.genre_translations)
        LastfmOptionsPage.setTabOrder(self.genre_translations, self.filter_report)
        LastfmOptionsPage.setTabOrder(self.filter_report, self.check_word_lists)
        LastfmOptionsPage.setTabOrder(self.check_word_lists, self.check_translation_list)
        LastfmOptionsPage.setTabOrder(self.check_translation_list, self.load_default_lists)

    def retranslateUi(self, LastfmOptionsPage):
        _translate = QtCore.QCoreApplication.translate
        LastfmOptionsPage.setWindowTitle(_translate("LastfmOptionsPage", "Form", None))
        self.tabWidget.setWindowTitle(_translate("LastfmOptionsPage", "LastfmOptionsPage", None))
        self.groupbox_max_tags_written.setTitle(_translate("LastfmOptionsPage", "Max Tags Written   0=Disabled  1=One Tag  2+= Multiple Tags", None))
        self.label_general_major_tags_group.setText(_translate("LastfmOptionsPage", "Major Tags - Group", None))
        self.max_group_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Grouping (Major Genres) Tags</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GROUPING%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Top-level genres ex: <span style=\" font-style:italic;\">Classical, Rock, Soundtracks  </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Grouping tag. Can also be appended to    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Genre tag if \'Append Major\' box (below) is checked.  </p></body></html>", None))
        self.label_general_max_mood_tags.setText(_translate("LastfmOptionsPage", "Max Mood Tags", None))
        self.max_mood_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Mood Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">ID3v2.4+ Only!    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %MOOD%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">How a track \'feels\'. ex:<span style=\" font-style:italic;\"> Happy, Introspective, Drunk</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: <span style=\" color:#dd3a3a;\">The TMOO frame is only standard in ID3v2.4 tags.    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">For all other tags, Moods will be saved as a Comment.</p></body></html>", None))
        self.label_general_minor_tags_genre.setText(_translate("LastfmOptionsPage", "Minor Tags - Genre", None))
        self.max_minor_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Genre Tags</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %GENRE%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">These are specific, detailed genres. ex:<span style=\" font-style:italic;\"> Baroque, Classic Rock, Delta Blues   </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Set this to 1 if using this tag for file naming, </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">or if your player doesn\'t support multi-value tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"> </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Consider setting this to 3+ if you use Genre</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for searching in your music library.</p></body></html>", None))
        self.label_general_max_occasion_tags.setText(_translate("LastfmOptionsPage", "Max Occasion Tags", None))
        self.max_occasion_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Occasion Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Occasion%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Good situations to play a track, ex: Driving<span style=\" font-style:italic;\">, Love, Party    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Set to 2+ to increase this tag\'s usefulness.</p></body></html>", None))
        self.label_general_max_category_tags.setText(_translate("LastfmOptionsPage", "Max Category Tags", None))
        self.max_category_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Max Category Tags   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Another Top-level grouping tag.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Contains tags like: <span style=\" font-style:italic;\">Female Vocalists, Singer-Songwriter</span></p></body></html>", None))
        self.app_major2minor_tag.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Append Major to Minor Tags       </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This will prepend any Grouping tags   </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">onto the Genre tag at tagging time. The effect is</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">that the Grouping Tag which is also the Major Genre</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Becomes the First Genre in the List of Minor Genres</p></body></html>", None))
        self.app_major2minor_tag.setText(_translate("LastfmOptionsPage", "Prepend Major to Minor Tags", None))
        self.label_tag_filter_list_genres6.setText(_translate("LastfmOptionsPage", "Join Tags With", None))
        self.join_tags_sign.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The Separator to use for <span style=\" font-weight:600;\">Multi-Value</span> tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">You may want to add a trailing space to</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">help with readability.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">To use <span style=\" font-weight:600;\">Separate Tags</span> rather than a single</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">multi-value tag leave this field blank ie. no space at all.</p></body></html>", None))
        self.join_tags_sign.setText(_translate("LastfmOptionsPage", ";", None))
        self.groupbox_other_tags.setTitle(_translate("LastfmOptionsPage", "Enable (Selected) or Disable (Not Selected) other Tags", None))
        self.use_country_tag.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The country the artist or track is most </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">associated with. Will retrieve results using the Country</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag list on Tag Filter List Page</p></body></html>", None))
        self.use_country_tag.setText(_translate("LastfmOptionsPage", "Country", None))
        self.use_city_tag.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The city or region the artist or track is most </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">associated with. If Enabled will use the most popular</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag in the City list on Tag Filter Options page.  If </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Country option has been selected as well the City tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">will be displayed second in the tag list.</p></body></html>", None))
        self.use_city_tag.setText(_translate("LastfmOptionsPage", "City", None))
        self.use_year_tag.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Original Year   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %ID3:TDOR% or </span><span style=\" font-weight:600;\">%ID3:TORY%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The year the song was created or most popular in. Quite often</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this is the correct original release year of the track. The tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">written to is determined by the settings you have selected</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">in Picard Tag options. Ie. if ID3v2.3 is selected the original year tag</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">will be ID3:TORY rather than the default of ID3:TDOR</p></body></html>", None))
        self.use_year_tag.setText(_translate("LastfmOptionsPage", "Original Year", None))
        self.use_decade_tag.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Decade   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag:   %Comment:Songs-db_Custom1%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The decade the song was created, ex: 1970s</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This is based on the last fm tags first, if none found then </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">the originalyear tag, and then the release date of the album.</p></body></html>", None))
        self.use_decade_tag.setText(_translate("LastfmOptionsPage", "Decade", None))
        self.groupbox_track_based_tags.setTitle(_translate("LastfmOptionsPage", "Track Based Tags: Tags based on Track Title and Artist", None))
        self.use_track_tags.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Check this to use <span style=\" font-weight:600;\">Track-based tags. </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">These are tags relevant to the <span style=\" font-weight:600; font-style:italic;\">song</span></p></body></html>", None))
        self.use_track_tags.setText(_translate("LastfmOptionsPage", "Use Track Based Tags", None))
        self.label_general_minimum_tag_weight.setText(_translate("LastfmOptionsPage", "Minimum Tag Weight", None))
        self.min_tracktag_weight.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">The minimum weight track-based tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">to use, in terms of popularity</p></body></html>", None))
        self.min_tracktag_weight.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.label_tag_filter_list_genres0.setText(_translate("LastfmOptionsPage", "Maximum Inter-Tag Drop", None))
        self.max_tracktag_drop.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">The maximum allowed drop in relevance</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for the tag to still be a match</p></body></html>", None))
        self.max_tracktag_drop.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.groupbox_artist_based_tags.setTitle(_translate("LastfmOptionsPage", "Artist Based Tags: Based on the Artist, not the Track Title.", None))
        self.artist_tag_us_no.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Select this to Never use Artist based tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Be sure you have Use Track-Based Tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">checked, though.</p></body></html>", None))
        self.artist_tag_us_no.setText(_translate("LastfmOptionsPage", "Don\'t use Artist Tags", None))
        self.label_tag_filter_list_genres1.setText(_translate("LastfmOptionsPage", "Artist-Tags Weight", None))
        self.artist_tags_weight.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">How strongly Artist-based tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">are considered for inclusion</p></body></html>", None))
        self.artist_tags_weight.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.artist_tag_us_ex.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Enabling this uses Artist-based tags only  </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">if there aren\'t enough Track-based tags.   </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Default: Enabled</span></p></body></html>", None))
        self.artist_tag_us_ex.setText(_translate("LastfmOptionsPage", "Extend Track-Tags", None))
        self.label_tag_filter_list_genres2.setText(_translate("LastfmOptionsPage", "Minimum Tag Weight", None))
        self.min_artisttag_weight.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The minimum weight Artist-based tag    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">to use, in terms of popularity    </p></body></html>", None))
        self.min_artisttag_weight.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.artist_tag_us_yes.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Enable this to <span style=\" font-weight:600;\">Always</span> use Artist-based tags</p></body></html>", None))
        self.artist_tag_us_yes.setText(_translate("LastfmOptionsPage", "Use Artist-Tags", None))
        self.label_tag_filter_list_genres3.setText(_translate("LastfmOptionsPage", "Maximum Inter-Tag Drop", None))
        self.max_artisttag_drop.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">The maximum allowed drop in relevance    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">for the tag to still be a match    </p></body></html>", None))
        self.max_artisttag_drop.setSuffix(_translate("LastfmOptionsPage", " %", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_general_options), _translate("LastfmOptionsPage", "General Options", None))
        self.groupbox_tag_lists.setTitle(_translate("LastfmOptionsPage", "Tag Lists", None))
        self.label_tag_filter_list_grouping.setText(_translate("LastfmOptionsPage", "Grouping", None))
        self.genre_major.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Major Genres</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Top-level genres ex: <span style=\" font-style:italic;\">Classical, Rock, Soundtracks</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Grouping tag. Can also be appended to</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Genre tag if enabled in General Options.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GROUPING%   ID3 Frame:   TIT1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     CONTENT GROUP</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GROUPING</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GROUPING</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     CONTENTGROUP</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MUSIC CATEGORY DESCRIPTION</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None))
        self.label_tag_filter_list_genres.setText(_translate("LastfmOptionsPage", "Genres", None))
        self.genre_minor.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Minor Genres</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">More specific genres. ex:<span style=\" font-style:italic;\"> Baroque, Classic Rock, Delta Blues</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to Genre tag.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %GENRE%    ID3 Frame:   TCON</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC, Ape, Wav</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     GENRE</span></p></body></html>", None))
        self.label_tag_filter_list_mood.setText(_translate("LastfmOptionsPage", "Mood", None))
        self.genre_mood.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Mood   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">ID3v2.4+ Only!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">How a track \'feels\'. ex:<span style=\" font-style:italic;\"> Happy, Introspective, Drunk</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: The TMOO frame is only standard in ID3v2.4 tags.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">For all other tags, Moods are saved as a Comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %MOOD%    ID3 Frame:   TMOO</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">      ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MOOD</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     MOOD</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     WM/MOOD</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None))
        self.label_tag_filter_list_years.setText(_translate("LastfmOptionsPage", "Years", None))
        self.genre_year.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Original Year </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The year the track was first <span style=\" font-style:italic;\">recorded</span>.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Note: This tag is often missing or wrong.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">If Blank, the album release date is used.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %ORIGINALDATE%   </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame: V2.3: TORY   v2.4: TDOR</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac, Wma, AAC</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGINAL RELEASE DATE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGINAL DATE</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">    ORIGYEAR</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP        </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">    ---</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:7pt; font-weight:600;\"></p></body></html>", None))
        self.label_tag_filter_list_occasion.setText(_translate("LastfmOptionsPage", "Occasion", None))
        self.genre_occasion.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Occasions   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Good times to play the track, ex: Driving<span style=\" font-style:italic;\">, Love, Party</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Written to the Comment tag. Has very limited support.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Occasion%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Occasion</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Occasion</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p align=\"justify\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP       </span><span style=\" font-size:7pt; font-weight:600; color:#707070;\">UNK</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None))
        self.label_tag_filter_list_decades.setText(_translate("LastfmOptionsPage", "Decades", None))
        self.genre_decade.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Decade   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">The decade the song was created. Based on</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">originalyear, so will frequently be wrong.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app can map Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom1%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom1</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None))
        self.label_tag_filter_list_country.setText(_translate("LastfmOptionsPage", "Country", None))
        self.genre_country.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Artist country/location info, ex: America, New York, NYC</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Allowing more tags will usually give more detailed info.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app maps Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom3%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None))
        self.label_tag_filter_list_cities.setText(_translate("LastfmOptionsPage", "Cities", None))
        self.genre_city.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Country   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Artist country/location info, ex: America, New York, NYC</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Allowing more tags will usually give more detailed info.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app maps Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom3%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom3</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None))
        self.label_tag_filter_list_category.setText(_translate("LastfmOptionsPage", "Category", None))
        self.genre_category.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Category   </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">Nonstandard!</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Another Top-level grouping tag.</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Returns terms like Female Vocalists, Singer-Songwriter</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Unless your app can map Comment subvalues</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">this tag will show as part of any existing comment.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Tag Name:   %Comment:Songs-db_Custom2%</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">ID3 Frame:   COMM:Songs-db_Custom2</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Supported:   </span><span style=\" font-weight:600; color:#3852b0;\">Mp3, Ogg, Flac</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt; font-weight:600; color:#3852b0;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Compatibility                     Tag Mapping</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" vertical-align:super;\">______________________________________________________</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Foobar         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">iTunes         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MediaMonkey        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Custom tag</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">MP3Tag        </span><span style=\" font-size:7pt; font-weight:600; color:#75e101;\">YES</span><span style=\" font-size:7pt; font-weight:600;\">     Comment:Songs-db_Custom2</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">Winamp         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">WMP         </span><span style=\" font-size:7pt; font-weight:600; color:#dd3a3a;\">NO</span><span style=\" font-size:7pt; font-weight:600;\">     ---</span></p></body></html>", None))
        self.groupbox_tag_translations.setTitle(_translate("LastfmOptionsPage", "Tag Translations", None))
        self.genre_translations.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Tag Translations</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This list lets you change how matches from the</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">tag lists are actually written into your tags.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Typical Uses:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Standardize spellings,   ex: rock-n-roll , rock and roll , rock \'n roll  --&gt; rock &amp; roll</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Clean formatting,          ex: lovesongs --&gt; love songs</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-style:italic;\">- Condense related tags, ex: heavy metal, hair metal, power metal  --&gt; metal</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Usage:   Old Name, New Name  </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600;\">One Rule per line:</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Death Metal, Metal</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Sunshine-Pop, Pop</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-size:7pt; font-weight:600; color:#4659cf;\">Super-awesome-musics, Nice</span></p></body></html>", None))
        self.groupbox_tools.setTitle(_translate("LastfmOptionsPage", "Tools", None))
        self.filter_report.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Filter Report    </span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Tells you how many tags and    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">translations you have in each list.    </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p></body></html>", None))
        self.filter_report.setText(_translate("LastfmOptionsPage", "Filter Report", None))
        self.check_word_lists.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:600;\">Check Tag Lists</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Each tag may appear only <span style=\" font-weight:600;\">once</span> across all lists.    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">This scans all the lists for duplicated tags</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">so you can easily remove them.    </p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" font-weight:600;\">Run this whenever you add tags to a list!</span>    </p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"></p></body></html>", None))
        self.check_word_lists.setText(_translate("LastfmOptionsPage", "Check Tag Lists", None))
        self.check_translation_list.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:7pt;\">Not implemented yet.</span></p></body></html>", None))
        self.check_translation_list.setText(_translate("LastfmOptionsPage", "Translations", None))
        self.load_default_lists.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:600; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#dd3a3a;\">WARNING!</span></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#000000;\">This will overwrite all current</span></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\"><span style=\" color:#000000;\">Tag Lists and Translations!</span></p></body></html>", None))
        self.load_default_lists.setText(_translate("LastfmOptionsPage", "Load Defaults", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_tag_filter_lists), _translate("LastfmOptionsPage", "Tag Filter Lists", None))

        self.label_api_key.setText(_translate("LastfmOptionsPage", "Last.fm API key"))
        self.groupbox_api_key.setTitle(_translate("LastfmOptionsPage", "Last.fm API key", None))
        self.api_key.setToolTip(_translate("LastfmOptionsPage", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Last.fm API key</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:8pt;\">Create a <a href=\"https://www.last.fm/api/account/create\">Last.fm API account</a>, and paste the API key here.</p></body></html>", None))


