PLUGIN_NAME = "Deezer cover art"
PLUGIN_AUTHOR = "Fabio Forni <livingsilver94>"
PLUGIN_DESCRIPTION = "Fetch cover arts from Deezer"
PLUGIN_VERSION = '1.1.0'
PLUGIN_API_VERSIONS = ['2.5']
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

from difflib import SequenceMatcher
from typing import Any, List, Optional
from urllib.parse import urlsplit

import picard
from picard import config
from picard.coverart import providers
from picard.coverart.image import CoverArtImage
from PyQt5 import QtNetwork as QtNet

from .deezer import Client, SearchOptions, obj
from .options import Ui_Form

__version__ = PLUGIN_VERSION


def is_similar(str1: str, str2: str) -> bool:
    if str1 in str2:
        return True
    # Python doc considers a ratio equal to 0.6 a good match.
    return SequenceMatcher(None, str1, str2).quick_ratio() >= 0.65


def is_deezer_url(url: str) -> bool:
    return 'deezer.com' in urlsplit(url).netloc


class OptionsPage(providers.ProviderOptions):
    NAME = 'Deezer'
    TITLE = 'Deezer'
    options = [config.TextOption('setting', 'deezerart_size', obj.CoverSize.BIG.value)]
    _options_ui = Ui_Form

    def load(self):
        for s in obj.CoverSize:
            self.ui.size.addItem(str(s.name).title(), userData=s.value)
        self.ui.size.setCurrentIndex(self.ui.size.findData(config.setting['deezerart_size']))

    def save(self):
        config.setting['deezerart_size'] = self.ui.size.currentData()


class Provider(providers.CoverArtProvider):
    NAME = 'Deezer'
    OPTIONS = OptionsPage
    _log_prefix = 'Deezerart: '

    def __init__(self, coverart):
        super().__init__(coverart)
        self.client = Client(self.album.tagger.webservice)
        self._has_url_relation = False
        self._retry_search = False

    # Override.
    def queue_images(self):
        self.match_url_relations(['free streaming'], self._url_callback)
        if not self._has_url_relation:
            if not self._retry_search:
                search_opts = SearchOptions(artist=self._artist(), album=self.metadata['album'])
            else:
                try:
                    track = self.release['media'][0]['tracks'][1]['title']
                except (IndexError, KeyError):
                    self.error('cannot find a track name to retry a search. No cover found')
                    return self.FINISHED
                else:
                    search_opts = SearchOptions(artist=self._artist(), track=track)
            self.client.advanced_search(search_opts, self._queue_from_search)
        self.album._requests += 1
        return self.WAIT

    # Override.
    def error(self, msg):
        super().error(self._log_prefix + msg)

    def log_debug(self, msg: Any):
        picard.log.debug('%s%s', self._log_prefix, msg)

    def _url_callback(self, url: str):
        if is_deezer_url(url):
            self._has_url_relation = True
            self.client.obj_from_url(url, self._queue_from_url)

    def _queue_from_url(self, album: obj.Object, error: QtNet.QNetworkReply.NetworkError):
        self.album._requests -= 1
        try:
            if error:
                self.error('could not get Deezer API object: {}'.format(error))
                return
            if not isinstance(album, obj.Album):
                self.error('API object is not an album')
                return
            cover_url = album.cover_url(obj.CoverSize(config.setting['deezerart_size']))
            self.queue_put(CoverArtImage(cover_url))
            self.log_debug('queued cover using an URL relation')
        finally:
            self.next_in_queue()

    def _queue_from_search(self, results: List[obj.Object], error: Optional[QtNet.QNetworkReply.NetworkError]):
        self.album._requests -= 1
        try:
            if error:
                self.error('could not fetch search results: {}'.format(error))
                return
            if len(results) == 0:
                if self._retry_search:
                    self.error('no results found')
                    return
                self._retry_search = True
                self.queue_images()
                return
            artist = self._artist()
            album = self.metadata['album']
            for result in results:
                if not isinstance(result, obj.Track):
                    continue
                if not is_similar(artist, result.artist.name) or not is_similar(album, result.album.title):
                    continue
                cover_url = result.album.cover_url(obj.CoverSize(config.setting['deezerart_size']))
                self.queue_put(CoverArtImage(cover_url))
                self.log_debug('queued cover using a Deezer search')
                return
            self.error('no result matched the criteria')
        finally:
            self.next_in_queue()

    def _artist(self) -> str:
        # If there are many artists, we want to search
        # the album in Deezer with just one as keyword.
        # Deezerart may not specify all the artists
        # MusicBrainz does, or it may use different separators.
        return self.metadata.getraw('~albumartists')[0]


providers.register_cover_art_provider(Provider)
