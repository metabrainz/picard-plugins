# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2007 Oliver Charles
# Copyright (C) 2007-2011, 2019, 2021 Philipp Wolfer
# Copyright (C) 2007, 2010, 2011 Lukáš Lalinský
# Copyright (C) 2011 Michael Wiencek
# Copyright (C) 2011-2012 Wieland Hoffmann
# Copyright (C) 2013-2016 Laurent Monin
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

PLUGIN_NAME = 'Amazon cover art'
PLUGIN_AUTHOR = 'MusicBrainz Picard developers'
PLUGIN_DESCRIPTION = 'Use cover art from Amazon.'
PLUGIN_VERSION = "1.1"
PLUGIN_API_VERSIONS = ["2.2", "2.3", "2.4", "2.5", "2.6", "2.7"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import (
    CoverArtProvider,
    register_cover_art_provider,
)
from picard.util import parse_amazon_url

# amazon image file names are unique on all servers and constructed like
# <ASIN>.<ServerNumber>.[SML]ZZZZZZZ.jpg
# A release sold on amazon.de has always <ServerNumber> = 03, for example.
# Releases not sold on amazon.com, don't have a "01"-version of the image,
# so we need to make sure we grab an existing image.
AMAZON_SERVER = {
    "amazon.com": {
        "server": "ec1.images-amazon.com",
        "id": "01",
    },
    "amazon.jp": {
        "server": "ec1.images-amazon.com",
        "id": "09",
    },
    "amazon.co.jp": {
        "server": "ec1.images-amazon.com",
        "id": "09",
    },
    "amazon.co.uk": {
        "server": "ec1.images-amazon.com",
        "id": "02",
    },
    "amazon.de": {
        "server": "ec2.images-amazon.com",
        "id": "03",
    },
    "amazon.ca": {
        "server": "ec1.images-amazon.com",
        "id": "01",  # .com and .ca are identical
    },
    "amazon.fr": {
        "server": "ec1.images-amazon.com",
        "id": "08"
    },
}

AMAZON_IMAGE_PATH = '/images/P/%(asin)s.%(serverid)s.%(size)s.jpg'

# First item in the list will be tried first
AMAZON_SIZES = (
    # huge size option is only available for items
    # that have a ZOOMing picture on its amazon web page
    # and it doesn't work for all of the domain names
    # '_SCRM_',        # huge size
    'LZZZZZZZ',      # large size, option format 1
    # '_SCLZZZZZZZ_',  # large size, option format 3
    'MZZZZZZZ',      # default image size, format 1
    # '_SCMZZZZZZZ_',  # medium size, option format 3
    # 'TZZZZZZZ',      # medium image size, option format 1
    # '_SCTZZZZZZZ_',  # small size, option format 3
    # 'THUMBZZZ',      # small size, option format 1
)


class CoverArtProviderAmazon(CoverArtProvider):

    """Use Amazon ASIN Musicbrainz relationships to get cover art"""

    NAME = "Amazon"
    TITLE = N_('Amazon')

    def __init__(self, coverart):
        super().__init__(coverart)
        self._has_url_relation = False

    def enabled(self):
        return (super().enabled()
                and not self.coverart.front_image_found)

    def queue_images(self):
        self.match_url_relations(('amazon asin', 'has_Amazon_ASIN'),
                                 self._queue_from_asin_relation)
        # No URL relationships loaded, try by ASIN
        if not self._has_url_relation:
            self._queue_from_asin()
        return CoverArtProvider.FINISHED

    def _queue_from_asin_relation(self, url):
        """Queue cover art images from Amazon"""
        amz = parse_amazon_url(url)
        if amz is None:
            return
        log.debug("Found ASIN relation : %s %s", amz['host'], amz['asin'])
        self._has_url_relation = True
        if amz['host'] in AMAZON_SERVER:
            server_info = AMAZON_SERVER[amz['host']]
        else:
            server_info = AMAZON_SERVER['amazon.com']
        self._queue_asin(server_info, amz['asin'])

    def _queue_from_asin(self):
        asin = self.release.get('asin')
        if asin:
            log.debug("Found ASIN : %s", asin)
            for server_info in AMAZON_SERVER.values():
               self._queue_asin(server_info, asin)

    def _queue_asin(self, server_info, asin):
        host = server_info['server']
        for size in AMAZON_SIZES:
            path = AMAZON_IMAGE_PATH % {
                'asin': asin,
                'serverid': server_info['id'],
                'size': size
            }
            self.queue_put(CoverArtImage("http://%s%s" % (host, path)))


register_cover_art_provider(CoverArtProviderAmazon)
