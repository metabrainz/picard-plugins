# -*- coding: utf-8 -*-

# Copyright © 2015 Samir Benmendil <me@rmz.io>
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

PLUGIN_NAME = 'Soundtrack'
PLUGIN_AUTHOR = 'Samir Benmendil'
PLUGIN_LICENSE = 'WTFPL'
PLUGIN_LICENSE_URL = 'http://www.wtfpl.net/'
PLUGIN_DESCRIPTION = '''Sets the albumartist to "Soundtrack" if releasetype is a soundtrack.'''
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.0"]

from picard.metadata import register_album_metadata_processor


def soundtrack(tagger, metadata, release):
    if "soundtrack" in metadata["releasetype"]:
        metadata["albumartist"] = "Soundtrack"
        metadata["albumartistsort"] = "Soundtrack"

register_album_metadata_processor(soundtrack)
