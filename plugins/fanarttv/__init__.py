# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Philipp Wolfer
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

PLUGIN_NAME = 'fanart.tv cover art'
PLUGIN_AUTHOR = 'Philipp Wolfer, Sambhav Kothari'
PLUGIN_DESCRIPTION = ('Use cover art from fanart.tv. To use this plugin you '
                      'have to register a personal API key on '
                      'https://fanart.tv/get-an-api-key/')
PLUGIN_VERSION = "1.5.2"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from functools import partial
from PyQt5.QtCore import QUrl
from PyQt5.QtNetwork import QNetworkReply
from picard import config, log
from picard.coverart.providers import (
    CoverArtProvider,
    register_cover_art_provider,
)
from picard.coverart.image import CoverArtImage
from picard.ui.options import (
    register_options_page,
    OptionsPage,
)
from picard.config import TextOption
from .ui_options_fanarttv import Ui_FanartTvOptionsPage

FANART_HOST = "webservice.fanart.tv"
FANART_PORT = 80
FANART_APIKEY = "21305dd1589766f4d544535ad4df12f4"

OPTION_CDART_ALWAYS = "always"
OPTION_CDART_NEVER = "never"
OPTION_CDART_NOALBUMART = "noalbumart"


def cover_sort_key(cover):
    """For sorting a list of cover arts by likes."""
    try:
        return int(cover["likes"]) if "likes" in cover else 0
    except ValueError:
        return 0


def encode_queryarg(arg):
    return bytes(QUrl.toPercentEncoding(arg)).decode()


class FanartTvCoverArtImage(CoverArtImage):

    """Image from fanart.tv"""

    support_types = True
    sourceprefix = "FATV"


class CoverArtProviderFanartTv(CoverArtProvider):

    """Use fanart.tv to get cover art"""

    NAME = "fanart.tv"

    def enabled(self):
        return (self._client_key and super().enabled()
                and not self.coverart.front_image_found)

    def queue_images(self):
        release_group_id = self.metadata["musicbrainz_releasegroupid"]
        path = "/v3/music/albums/%s" % (release_group_id, )
        queryargs = {
            "api_key": encode_queryarg(FANART_APIKEY),
            "client_key": encode_queryarg(self._client_key),
        }
        log.debug("CoverArtProviderFanartTv.queue_downloads: %s" % path)
        self.album.tagger.webservice.get(
            FANART_HOST,
            FANART_PORT,
            path,
            partial(self._json_downloaded, release_group_id),
            priority=True,
            important=False,
            parse_response_type='json',
            queryargs=queryargs)
        self.album._requests += 1
        return CoverArtProvider.WAIT

    @property
    def _client_key(self):
        return config.setting["fanarttv_client_key"]

    def _json_downloaded(self, release_group_id, data, reply, error):
        self.album._requests -= 1

        if error:
            if error != QNetworkReply.ContentNotFoundError:
                error_level = log.error
            else:
                error_level = log.debug
            error_level("Problem requesting metadata in fanart.tv plugin: %s",
                        error)
        else:
            try:
                release = data["albums"][release_group_id]
                has_cover = "albumcover" in release
                has_cdart = "cdart" in release
                use_cdart = config.setting["fanarttv_use_cdart"]

                if has_cover:
                    covers = release["albumcover"]
                    types = ["front"]
                    self._select_and_add_cover_art(covers, types)

                if has_cdart and (use_cdart == OPTION_CDART_ALWAYS
                                  or (use_cdart == OPTION_CDART_NOALBUMART
                                      and not has_cover)):
                    covers = release["cdart"]
                    types = ["medium"]
                    if not has_cover:
                        types.append("front")
                    self._select_and_add_cover_art(covers, types)
            except (AttributeError, KeyError, TypeError):
                log.error("Problem processing downloaded metadata in fanart.tv plugin", exc_info=True)

        self.next_in_queue()

    def _select_and_add_cover_art(self, covers, types):
        covers = sorted(covers, key=cover_sort_key, reverse=True)
        url = covers[0]["url"]
        log.debug("CoverArtProviderFanartTv found artwork %s" % url)
        self.queue_put(FanartTvCoverArtImage(url, types=types))


class FanartTvOptionsPage(OptionsPage):

    NAME = "fanarttv"
    TITLE = "fanart.tv"
    PARENT = "plugins"

    options = [
        TextOption("setting", "fanarttv_client_key", ""),
        TextOption("setting", "fanarttv_use_cdart", OPTION_CDART_NOALBUMART),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_FanartTvOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        setting = config.setting
        self.ui.fanarttv_client_key.setText(setting["fanarttv_client_key"])
        if setting["fanarttv_use_cdart"] == OPTION_CDART_ALWAYS:
            self.ui.fanarttv_cdart_use_always.setChecked(True)
        elif setting["fanarttv_use_cdart"] == OPTION_CDART_NEVER:
            self.ui.fanarttv_cdart_use_never.setChecked(True)
        elif setting["fanarttv_use_cdart"] == OPTION_CDART_NOALBUMART:
            self.ui.fanarttv_cdart_use_if_no_albumcover.setChecked(True)

    def save(self):
        setting = config.setting
        setting["fanarttv_client_key"] = self.ui.fanarttv_client_key.text()
        if self.ui.fanarttv_cdart_use_always.isChecked():
            setting["fanarttv_use_cdart"] = OPTION_CDART_ALWAYS
        elif self.ui.fanarttv_cdart_use_never.isChecked():
            setting["fanarttv_use_cdart"] = OPTION_CDART_NEVER
        elif self.ui.fanarttv_cdart_use_if_no_albumcover.isChecked():
            setting["fanarttv_use_cdart"] = OPTION_CDART_NOALBUMART


register_cover_art_provider(CoverArtProviderFanartTv)
register_options_page(FanartTvOptionsPage)
