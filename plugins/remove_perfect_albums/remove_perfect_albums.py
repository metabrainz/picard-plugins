PLUGIN_NAME = 'Remove Perfect Albums'
PLUGIN_AUTHOR = 'ichneumon, hrglgrmpf'
PLUGIN_DESCRIPTION = '''Remove all perfectly matched albums from the selection.'''
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PyQt5.QtCore import QCoreApplication

from picard.album import Album
from picard.ui.itemviews import BaseAction, register_album_action

class RemovePerfectAlbums(BaseAction):
    NAME = 'Remove perfect albums'

    def callback(self, objs):
        for album in objs:
            if (isinstance(album, Album) and album.loaded and album.is_complete()
              	and album.get_num_unsaved_files() == 0):
                self.tagger.remove_album(album)
            QCoreApplication.processEvents()

register_album_action(RemovePerfectAlbums())
