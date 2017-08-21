# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Philipp Wolfer
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

PLUGIN_NAME = 'Paper CD case'
PLUGIN_AUTHOR = 'Philipp Wolfer, Sambhav Kothari'
PLUGIN_DESCRIPTION = 'Create a paper CD case from an album or cluster using http://papercdcase.com'
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from PyQt5.QtCore import QUrl, QUrlQuery
from picard.album import Album
from picard.cluster import Cluster
from picard.ui.itemviews import BaseAction, register_album_action, register_cluster_action
from picard.util import webbrowser2
from picard.util import textencoding


PAPERCDCASE_URL = 'http://papercdcase.com/advanced.php'


def build_papercdcase_url(artist, album, tracks):
    url = QUrl(PAPERCDCASE_URL)
    # papercdcase.com does not deal well with unicode characters :(
    url_query = QUrlQuery()
    url_query.addQueryItem('artist', textencoding.asciipunct(artist))
    url_query.addQueryItem('title', textencoding.asciipunct(album))
    i = 1
    for track in tracks:
        url_query.addQueryItem('track' + str(i), textencoding.asciipunct(track))
        i += 1
    url.setQuery(url_query)
    return url.toString(QUrl.FullyEncoded)


class PaperCdCase(BaseAction):
    NAME = 'Create paper CD case'

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Album) or isinstance(obj, Cluster):
                artist = obj.metadata['albumartist']
                album = obj.metadata['album']
                if isinstance(obj, Album):
                    tracks = [track.metadata['title'] for track in obj.tracks]
                else:
                    tracks = [file.metadata['title'] for file in obj.files]
                url = build_papercdcase_url(artist, album, tracks)
                webbrowser2.open(url)


paperCdCase = PaperCdCase()
register_album_action(paperCdCase)
register_cluster_action(paperCdCase)
