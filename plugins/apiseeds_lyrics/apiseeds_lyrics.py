from functools import partial
from urllib.parse import quote, urlencode

from PyQt5 import QtWidgets
from picard import config, log
from picard.config import TextOption
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from picard.webservice import ratecontrol

PLUGIN_NAME = 'Apiseeds Lyrics'
PLUGIN_AUTHOR = 'Andrea Avallone'
PLUGIN_DESCRIPTION = 'Fetch lyrics from Apiseeds Lyrics, which provides millions of lyrics from artist all around the world. ' \
                     'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed. ' \
                     'In order to use Apiseeds you need to get a free API key at <em>https://apiseeds.com</em>. ' \
                     'Want to contribute? Check out the project page at <em>https://github.com/avalloneandrea/apiseeds-lyrics</em>!'
PLUGIN_VERSION = '1.0.5'
PLUGIN_API_VERSIONS = ['2.0']
PLUGIN_LICENSE = 'MIT'
PLUGIN_LICENSE_URL = 'https://opensource.org/licenses/MIT'


class ApiseedsLyricsMetadataProcessor(object):

    apiseeds_host = 'orion.apiseeds.com'
    apiseeds_port = 443
    apiseeds_delay = 60 * 1000 / 100  # 100 requests per minute

    def __init__(self):
        super(ApiseedsLyricsMetadataProcessor, self).__init__()
        ratecontrol.set_minimum_delay((self.apiseeds_host, self.apiseeds_port), self.apiseeds_delay)

    def process_metadata(self, album, metadata, track, release):

        apikey = config.setting['apiseeds_apikey']
        if not apikey:
            log.debug('{}: API key is missing, please provide a valid value'.format(PLUGIN_NAME))
            return

        artist = metadata['artist']
        if not artist:
            log.debug('{}: artist is missing, please provide a valid value'.format(PLUGIN_NAME))
            return

        title = metadata['title']
        if not title:
            log.debug('{}: title is missing, please provide a valid value'.format(PLUGIN_NAME))
            return

        apiseeds_path = '/api/music/lyric/{}/{}'.format(quote(artist, ''), quote(title, ''))
        apiseeds_params = {'apikey': apikey}
        album._requests += 1
        log.debug('{}: GET {}?{}'.format(PLUGIN_NAME, quote(apiseeds_path), urlencode(apiseeds_params)))

        album.tagger.webservice.get(
            self.apiseeds_host,
            self.apiseeds_port,
            apiseeds_path,
            partial(self.process_response, album, metadata),
            parse_response_type='json',
            priority=True,
            queryargs=apiseeds_params)

    @staticmethod
    def process_response(album, metadata, response, reply, error):

        try:
            lyrics = response['result']['track']['text']
            metadata['lyrics'] = lyrics
            log.debug('{}: lyrics found for track {}'.format(PLUGIN_NAME, metadata['title']))

        except (TypeError, KeyError):
            log.debug('{}: lyrics NOT found for track {}'.format(PLUGIN_NAME, metadata['title']))

        finally:
            album._requests -= 1
            album._finalize_loading(None)


class ApiseedsLyricsOptionsPage(OptionsPage):

    NAME = 'apiseeds_lyrics'
    TITLE = 'Apiseeds Lyrics'
    PARENT = 'plugins'

    options = [TextOption('setting', 'apiseeds_apikey', '')]

    def __init__(self, parent=None):

        super(ApiseedsLyricsOptionsPage, self).__init__(parent)
        self.box = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel(self)
        self.label.setText('Apiseeds API key')
        self.box.addWidget(self.label)

        self.description = QtWidgets.QLabel(self)
        self.description.setText('Apiseeds Lyrics provides millions of lyrics from artist all around the world. '
                                 'Lyrics provided are for educational purposes and personal use only. Commercial use is not allowed. '
                                 'In order to use Apiseeds Lyrics you need to get a free API key <a href="https://apiseeds.com">here</a>.')
        self.description.setOpenExternalLinks(True)
        self.box.addWidget(self.description)

        self.input = QtWidgets.QLineEdit(self)
        self.box.addWidget(self.input)

        self.contribute = QtWidgets.QLabel(self)
        self.contribute.setText('Want to contribute? Check out the <a href="https://github.com/avalloneandrea/apiseeds-lyrics">project page</a>!')
        self.contribute.setOpenExternalLinks(True)
        self.box.addWidget(self.contribute)

        self.spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.box.addItem(self.spacer)

    def load(self):
        self.input.setText(config.setting['apiseeds_apikey'])

    def save(self):
        config.setting['apiseeds_apikey'] = self.input.text()


register_track_metadata_processor(ApiseedsLyricsMetadataProcessor().process_metadata)
register_options_page(ApiseedsLyricsOptionsPage)
