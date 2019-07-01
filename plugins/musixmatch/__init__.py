PLUGIN_NAME = 'Musixmatch Lyrics'
PLUGIN_AUTHOR = 'm-yn, Sambhav Kothari, Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Fetch first 30% of lyrics from Musixmatch'
PLUGIN_VERSION = '1.1'
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from functools import partial
from picard import config, log
from picard.metadata import register_track_metadata_processor
from picard.ui.options import register_options_page, OptionsPage
from .ui_options_musixmatch import Ui_MusixmatchOptionsPage


MUSIXMATCH_HOST = 'api.musixmatch.com'
MUSIXMATCH_PORT = 80


def handle_result(album, metadata, data, reply, error):
    try:
        if error:
            log.error(error)
            return
        message = data.get('message', {})
        header = message.get('header')
        if header.get('status_code') != 200:
            log.warning('MusixMatch: Server returned no result: %s', data)
            return
        result = message.get('body', {}).get('lyrics')
        if result:
            lyrics = result.get('lyrics_body')
            if lyrics:
                metadata['lyrics:description'] = lyrics
    except AttributeError:
        log.error('MusixMatch: Error handling server response %s',
                  data, exc_info=True)
    finally:
        album._requests -= 1
        album._finalize_loading(error)


def process_track(album, metadata, release, track):
    apikey = config.setting['musixmatch_api_key']
    if not apikey:
        log.warning('MusixMatch: No API key configured')
        return
    if metadata['language'] == 'zxx':
        log.debug('MusixMatch: Track %s has no lyrics, skipping query',
                  metadata['musicbrainz_recordingid'])
        return
    queryargs = {
        'apikey': apikey,
        'track_mbid': metadata['musicbrainz_recordingid']
    }
    album.tagger.webservice.get(
        MUSIXMATCH_HOST,
        MUSIXMATCH_PORT,
        "/ws/1.1/track.lyrics.get",
        partial(handle_result, album, metadata),
        parse_response_type='json',
        queryargs=queryargs
    )
    album._requests += 1


class MusixmatchOptionsPage(OptionsPage):
    NAME = 'musixmatch'
    TITLE = 'Musixmatch API Key'
    PARENT = "plugins"
    options = [
        config.TextOption("setting", "musixmatch_api_key", "")
    ]

    def __init__(self, parent=None):
        super(MusixmatchOptionsPage, self).__init__(parent)
        self.ui = Ui_MusixmatchOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.api_key.setText(config.setting["musixmatch_api_key"])

    def save(self):
        self.config.setting["musixmatch_api_key"] = self.ui.api_key.text()


register_track_metadata_processor(process_track)
register_options_page(MusixmatchOptionsPage)
