# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2019 Philipp Wolfer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = 'TheAudioDB cover art'
PLUGIN_AUTHOR = 'Philipp Wolfer'
PLUGIN_DESCRIPTION = 'Use cover art from TheAudioDB.'
PLUGIN_VERSION = "1.0.1"
PLUGIN_API_VERSIONS = ["2.0", "2.1"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply
from picard import config, log
from picard.coverart.providers import CoverArtProvider, register_cover_art_provider
from picard.coverart.image import CoverArtImage
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption
from picard.plugins.theaudiodb.ui_options_theaudiodb import Ui_TheAudioDbOptionsPage

THEAUDIODB_HOST = "www.theaudiodb.com"
THEAUDIODB_PORT = 443
THEAUDIODB_APIKEY = "195003"

OPTION_CDART_ALWAYS = "always"
OPTION_CDART_NEVER = "never"
OPTION_CDART_NOALBUMART = "noalbumart"


class TheAudioDbCoverArtImage(CoverArtImage):

    """Image from The Audio DB"""

    support_types = True
    sourceprefix = "AUDIODB"

    def parse_url(self, url):
        super().parse_url(url)
        # Workaround for Picard always returning port 80 regardless of the scheme
        self.port = self.url.port(443 if self.url.scheme() == 'https' else 80)


class CoverArtProviderTheAudioDb(CoverArtProvider):

    """Use TheAudioDB to get cover art"""

    NAME = "TheAudioDB"

    def enabled(self):
        return super().enabled() and not self.coverart.front_image_found

    def queue_images(self):
        release_group_id = self.metadata["musicbrainz_releasegroupid"]
        path = "/api/v1/json/%s/album-mb.php" % (THEAUDIODB_APIKEY, )
        queryargs = {
            "i": bytes(QUrl.toPercentEncoding(release_group_id)).decode()
        }
        log.debug("CoverArtProviderTheAudioDb.queue_downloads: %s?i=%s" % (path, queryargs["i"]))
        self.album.tagger.webservice.get(
            THEAUDIODB_HOST,
            THEAUDIODB_PORT,
            path,
            self._json_downloaded,
            priority=True,
            important=False,
            parse_response_type='json',
            queryargs=queryargs)
        self.album._requests += 1
        return CoverArtProvider.WAIT

    def _json_downloaded(self, data, reply, error):
        self.album._requests -= 1

        if error:
            if error != QNetworkReply.ContentNotFoundError:
                error_level = log.error
            else:
                error_level = log.debug
            error_level("Problem requesting metadata in TheAudioDB plugin: %s", error)
        else:
            try:
                releases = data.get("album")
                if not releases:
                    log.info("No cover art found on TheAudioDB for %s", reply.url().url())
                    return
                release = releases[0]
                albumArtUrl = release.get("strAlbumThumb")
                cdArtUrl = release.get("strAlbumCDart")

                if albumArtUrl:
                    self._select_and_add_cover_art(albumArtUrl, ["front"])

                if cdArtUrl and \
                    (config.setting["theaudiodb_use_cdart"] == OPTION_CDART_ALWAYS
                        or (config.setting["theaudiodb_use_cdart"] == OPTION_CDART_NOALBUMART
                            and not albumArtUrl)):
                    types = ["medium"]
                    if not albumArtUrl:
                        types.append("front")
                    self._select_and_add_cover_art(cdArtUrl, types)
            except (TypeError):
                log.error("Problem processing downloaded metadata in TheAudioDB plugin: %s", exc_info=True)
            finally:
                self.next_in_queue()

    def _select_and_add_cover_art(self, url, types):
        log.debug("CoverArtProviderTheAudioDb found artwork %s" % url)
        self.queue_put(TheAudioDbCoverArtImage(url, types=types))


class TheAudioDbOptionsPage(OptionsPage):

    NAME = "theaudiodb"
    TITLE = "TheAudioDB"
    PARENT = "plugins"

    options = [
        TextOption("setting", "theaudiodb_use_cdart", OPTION_CDART_NOALBUMART),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_TheAudioDbOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        if config.setting["theaudiodb_use_cdart"] == OPTION_CDART_ALWAYS:
            self.ui.theaudiodb_cdart_use_always.setChecked(True)
        elif config.setting["theaudiodb_use_cdart"] == OPTION_CDART_NEVER:
            self.ui.theaudiodb_cdart_use_never.setChecked(True)
        elif config.setting["theaudiodb_use_cdart"] == OPTION_CDART_NOALBUMART:
            self.ui.theaudiodb_cdart_use_if_no_albumcover.setChecked(True)

    def save(self):
        if self.ui.theaudiodb_cdart_use_always.isChecked():
            config.setting["theaudiodb_use_cdart"] = OPTION_CDART_ALWAYS
        elif self.ui.theaudiodb_cdart_use_never.isChecked():
            config.setting["theaudiodb_use_cdart"] = OPTION_CDART_NEVER
        elif self.ui.theaudiodb_cdart_use_if_no_albumcover.isChecked():
            config.setting["theaudiodb_use_cdart"] = OPTION_CDART_NOALBUMART


register_cover_art_provider(CoverArtProviderTheAudioDb)
register_options_page(TheAudioDbOptionsPage)
