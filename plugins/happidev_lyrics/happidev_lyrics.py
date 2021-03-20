from functools import partial
from urllib.parse import (
    quote,
    urlencode,
    urlparse,
)

from PyQt5 import QtWidgets
from PyQt5.QtNetwork import QNetworkRequest

from picard import (
    config,
    log,
)
from picard.config import TextOption
from picard.metadata import register_track_metadata_processor
from picard.ui.options import (
    OptionsPage,
    register_options_page,
)
from picard.webservice import ratecontrol

PLUGIN_NAME = 'Happi.dev Lyrics'
PLUGIN_AUTHOR = 'Andrea Avallone, Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Fetch lyrics from Happi.dev Lyrics, which provides millions of lyrics from artist all around the world. ' \
                     'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed.<br /><br />' \
                     'In order to use Happi.dev you need to get a free API key at <a href="https://happi.dev">happi.dev</a>'
PLUGIN_VERSION = '2.0'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6']
PLUGIN_LICENSE = 'MIT'
PLUGIN_LICENSE_URL = 'https://opensource.org/licenses/MIT'


class HappidevLyricsMetadataProcessor:

    happidev_host = 'api.happi.dev'
    happidev_port = 443
    happidev_delay = 60 * 1000 / 100  # 100 requests per minute

    def __init__(self):
        super().__init__()
        ratecontrol.set_minimum_delay(
            (self.happidev_host, self.happidev_port), self.happidev_delay)

    def process_metadata(self, album, metadata, track, release):

        artist = metadata['artist']
        title = metadata['title']
        if not (artist and title):
            log.debug(
                '{}: both artist and title are required to obtain lyrics'.format(PLUGIN_NAME))
            return

        path = '/v1/music'
        queryargs = {
            'q': '"{}" "{}"'.format(artist, title),
            'lyrics': 'true',
            'type': 'track',
        }
        album._requests += 1
        log.debug('{}: GET {}?{}'.format(PLUGIN_NAME, quote(path), urlencode(queryargs)))
        self._request(album.tagger.webservice, path,
            partial(self.process_search_response, album, metadata), queryargs)

    def _request(self, ws, path, callback, queryargs=None, important=False):
        if not queryargs:
            queryargs = {}

        apikey = config.setting['happidev_apikey']
        if not apikey:
            error = 'API key is missing, please provide a valid value'
            log.debug('{}: {}'.format(PLUGIN_NAME, error))
            callback(None, None, error)
            return

        queryargs['apikey'] = apikey
        ws.get(self.happidev_host, self.happidev_port, path, callback,
            parse_response_type='json', priority=True, important=important,
            queryargs=queryargs, cacheloadcontrol=QNetworkRequest.PreferCache)

    def process_search_response(self, album, metadata, response, reply, error):
        if error or (response and (not response.get('success', False) or not response.get('length', 0))):
            log.debug('{}: lyrics NOT found for track "{}" by {}'.format(
                PLUGIN_NAME, metadata['title'], metadata['artist']))
            album._requests -= 1
            album._finalize_loading(None)
            return

        try:
            lyrics_url = response['result'][0]['api_lyrics']
            log.debug('{}: lyrics found for track "{}" by {} at {}'.format(
                PLUGIN_NAME, metadata['title'], metadata['artist'], lyrics_url))
            path = urlparse(lyrics_url).path
            album._requests += 1
            self._request(album.tagger.webservice, path,
                partial(self.process_lyrics_response, album, metadata),
                important=True)

        except (TypeError, KeyError, ValueError):
            log.warn('{}: failed parsing search response for "{}" by {}'.format(
                PLUGIN_NAME, metadata['title'], metadata['artist']), exc_info=True)

        finally:
            album._requests -= 1
            album._finalize_loading(None)

    @staticmethod
    def process_lyrics_response(album, metadata, response, reply, error):
        if error or (response and not response.get('success', False)):
            log.debug('{}: lyrics NOT loaded for track {}'.format(
                PLUGIN_NAME, metadata['title']))
            album._requests -= 1
            album._finalize_loading(None)
            return

        try:
            lyrics = response['result']['lyrics']
            metadata['lyrics'] = lyrics
            log.debug('{}: lyrics loaded for track "{}" by {}'.format(
                PLUGIN_NAME, metadata['title'], metadata['artist']))

        except (TypeError, KeyError):
            log.warn('{}: failed parsing search response for "{}" by {}'.format(
                PLUGIN_NAME, metadata['title'], metadata['artist']), exc_info=True)

        finally:
            album._requests -= 1
            album._finalize_loading(None)


class HappidevLyricsOptionsPage(OptionsPage):

    NAME = 'apiseeds_lyrics'
    TITLE = 'Happi.dev Lyrics'
    PARENT = 'plugins'

    options = [TextOption('setting', 'happidev_apikey', '')]

    def __init__(self, parent=None):

        super().__init__(parent)
        self.box = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.label.setText('Apiseeds API key')
        self.box.addWidget(self.label)

        self.description = QtWidgets.QLabel(self)
        self.description.setText('Happi.dev Music provides millions of lyrics from artist all around the world. '
                                 'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed. '
                                 'In order to use Happi.dev Music you need to get a free API key <a href="https://happi.dev">here</a>.')
        self.description.setOpenExternalLinks(True)
        self.box.addWidget(self.description)

        self.input = QtWidgets.QLineEdit(self)
        self.box.addWidget(self.input)

        self.spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.box.addItem(self.spacer)

    def load(self):
        self.input.setText(config.setting['happidev_apikey'])

    def save(self):
        config.setting['happidev_apikey'] = self.input.text()


register_track_metadata_processor(HappidevLyricsMetadataProcessor().process_metadata)
register_options_page(HappidevLyricsOptionsPage)
