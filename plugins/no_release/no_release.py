# -*- coding: utf-8 -*-

PLUGIN_NAME = 'No release'
PLUGIN_AUTHOR = 'Johannes Weißl, Philipp Wolfer'
PLUGIN_DESCRIPTION = '''Do not store specific release information in releases of unknown origin.'''
PLUGIN_VERSION = '0.2'
PLUGIN_API_VERSIONS = ['2.0']

from PyQt5 import QtCore, QtGui, QtWidgets

from picard import config
from picard.album import Album
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.ui.itemviews import BaseAction, register_album_action
from picard.config import BoolOption, TextOption


class Ui_NoReleaseOptionsPage(object):

    def setupUi(self, NoReleaseOptionsPage):
        NoReleaseOptionsPage.setObjectName('NoReleaseOptionsPage')
        NoReleaseOptionsPage.resize(394, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(NoReleaseOptionsPage)
        self.verticalLayout.setObjectName('verticalLayout')
        self.groupBox = QtWidgets.QGroupBox(NoReleaseOptionsPage)
        self.groupBox.setObjectName('groupBox')
        self.vboxlayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.vboxlayout.setObjectName('vboxlayout')
        self.norelease_enable = QtWidgets.QCheckBox(self.groupBox)
        self.norelease_enable.setObjectName('norelease_enable')
        self.vboxlayout.addWidget(self.norelease_enable)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName('label')
        self.vboxlayout.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName('horizontalLayout')
        self.norelease_strip_tags = QtWidgets.QLineEdit(self.groupBox)
        self.norelease_strip_tags.setObjectName('norelease_strip_tags')
        self.horizontalLayout.addWidget(self.norelease_strip_tags)
        self.vboxlayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(368, 187, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(NoReleaseOptionsPage)
        QtCore.QMetaObject.connectSlotsByName(NoReleaseOptionsPage)

    def retranslateUi(self, NoReleaseOptionsPage):
        self.groupBox.setTitle(QtWidgets.QApplication.translate('NoReleaseOptionsPage', 'No release'))
        self.norelease_enable.setText(QtWidgets.QApplication.translate('NoReleaseOptionsPage', _('Enable plugin for all releases by default')))
        self.label.setText(QtWidgets.QApplication.translate('NoReleaseOptionsPage', _('Tags to strip (comma-separated)')))


def strip_release_specific_metadata(metadata):
    strip_tags = config.setting['norelease_strip_tags']
    strip_tags = [tag.strip() for tag in strip_tags.split(',')]
    for tag in strip_tags:
        metadata.delete(tag)


class NoReleaseAction(BaseAction):
    NAME = _('Remove specific release information...')

    def callback(self, objs):
        for album in objs:
            if isinstance(album, Album):
                strip_release_specific_metadata(album.metadata)
                for track in album.tracks:
                    strip_release_specific_metadata(track.metadata)
                    for file in track.linked_files:
                        track.update_file_metadata(file)
                album.update()


class NoReleaseOptionsPage(OptionsPage):
    NAME = 'norelease'
    TITLE = 'No release'
    PARENT = 'plugins'

    options = [
        BoolOption('setting', 'norelease_enable', False),
        TextOption('setting', 'norelease_strip_tags', 'asin,barcode,catalognumber,date,label,media,releasecountry,releasestatus'),
    ]

    def __init__(self, parent=None):
        super(NoReleaseOptionsPage, self).__init__(parent)
        self.ui = Ui_NoReleaseOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.norelease_strip_tags.setText(config.setting['norelease_strip_tags'])
        self.ui.norelease_enable.setChecked(config.setting['norelease_enable'])

    def save(self):
        config.setting['norelease_strip_tags'] = str(self.ui.norelease_strip_tags.text())
        config.setting['norelease_enable'] = self.ui.norelease_enable.isChecked()


def NoReleaseAlbumProcessor(tagger, metadata, release):
    if config.setting['norelease_enable']:
        strip_release_specific_metadata(metadata)


def NoReleaseTrackProcessor(tagger, metadata, track, release):
    if config.setting['norelease_enable']:
        strip_release_specific_metadata(metadata)


register_album_metadata_processor(NoReleaseAlbumProcessor)
register_track_metadata_processor(NoReleaseTrackProcessor)
register_album_action(NoReleaseAction())
register_options_page(NoReleaseOptionsPage)
