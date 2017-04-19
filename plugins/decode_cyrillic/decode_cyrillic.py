# -*- coding: utf-8 -*-

# This is the Decode Cyrillic plugin for MusicBrainz Picard.
# Copyright (C) 2015 aeontech
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import print_function
PLUGIN_NAME = "Decode Cyrillic"
PLUGIN_AUTHOR = "aeontech"
PLUGIN_DESCRIPTION = '''
This plugin helps you quickly convert mis-encoded cyrillic Windows-1251 tags 
to proper UTF-8 encoded strings. If your track/album names look something like
"Àëèñà â ñò›àíå ÷óäåñ", run this plugin from the context menu
before running the "Lookup" or "Scan" tools
'''
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["1.0", "2.0"]
PLUGIN_LICENSE = "MIT"
PLUGIN_LICENSE_URL = "https://opensource.org/licenses/MIT"

from picard import log
from picard.cluster import Cluster
from picard.ui.itemviews import BaseAction, register_cluster_action

_decode_tags = [
    'title', 
    'albumartist', 
    'artist', 
    'album', 
    'artistsort'
]
# _from_encoding = "latin1"
# _to_encoding   = "cp1251"


# TODO:
# - extend to support multiple codepage decoding, not just cp1251->latin1
#   instead, try the common variations, and show a dialog to the user, 
#   allowing him to select the correct transcoding. See 2cyr.com for example.
# - also see http://stackoverflow.com/questions/23326531/how-to-decode-cp1252-string

class DecodeCyrillic(BaseAction):
    NAME = "Unmangle cyrillic metadata"

    def unmangle(self, tag, value):
        try:
            unmangled_value = value.encode('latin1').decode('cp1251')
        except UnicodeEncodeError:
            unmangled_value = value
            log.debug("%s: could not unmangle tag %s; original value: %s" % (PLUGIN_NAME, tag, value))
        return unmangled_value

    def callback(self, objs):
        for cluster in objs:
            if not isinstance(cluster, Cluster):
                continue

            for tag in _decode_tags:
                if not (tag in cluster.metadata):
                    continue

                cluster.metadata[tag] = self.unmangle(tag, cluster.metadata[tag])

            log.debug("cluster name is %s by %s" % (cluster.metadata['album'], cluster.metadata['albumartist']))

            for i, file in enumerate(cluster.files):

                log.debug("%s: Trying to unmangle file - original metadata %s" % (PLUGIN_NAME, file.orig_metadata))

                for tag in _decode_tags:    

                    if not (tag in file.metadata):
                        continue

                    unmangled_tag = self.unmangle(tag, file.metadata[tag])

                    file.orig_metadata[tag] = unmangled_tag
                    file.metadata[tag] = unmangled_tag

                    file.orig_metadata.changed = True
                    file.metadata.changed = True
                    file.update(signal=True)

            cluster.update()

register_cluster_action(DecodeCyrillic())
