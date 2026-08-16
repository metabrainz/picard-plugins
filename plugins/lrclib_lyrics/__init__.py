# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Giorgio Fontanive (twodoorcoupe)
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

PLUGIN_NAME = "Lrclib Lyrics"
PLUGIN_AUTHOR = "Giorgio Fontanive"
PLUGIN_DESCRIPTION = """
Fetches lyrics from lrclib.net

Also allows to export lyrics to an .lrc file or import them from one.
"""
PLUGIN_VERSION = "0.5"
PLUGIN_API_VERSIONS = ["2.12"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import os
import re
from functools import partial

from picard import config, log
from picard.album import register_album_post_removal_processor
from picard.file import (
    register_file_post_removal_from_track_processor,
    register_file_post_save_processor,
    register_file_post_addition_to_track_processor
)
from picard.track import Track
from picard.ui.itemviews import BaseAction, register_track_action
from picard.ui.options import OptionsPage, register_options_page
from picard.webservice import ratecontrol

from .option_lrclib_lyrics import Ui_OptionLrclibLyrics


URL = "https://lrclib.net/api/get"
REQUESTS_DELAY = 100

# Options
ADD_UNSYNCED_LYRICS = "add_unsynced_lyrics"
ADD_SYNCED_LYRICS = "add_synced_lyrics"
NEVER_REPLACE_LYRICS = "never_replace_lyrics"
LRC_FILENAME = "exported_lrc_filename"
TXT_FILENAME = "exported_txt_filename"
LRC_AS_SIDECAR = "lrc_as_sidecar"
EXPORT_LRC = "exported_lrc"
NEVER_REPLACE_LRC = "never_replace_lrc"


class LyricsCache:
    def __init__(self):
        self.cache = {}

    def set(self, orig_metadata, lyrics, synced):
        key = self._key_from_metadata(orig_metadata)
        # do not overwrite synchronized lyrics with unsynchronized
        if not synced and key in self.cache and self.cache[key][1]:
            return
        self.cache[key] = (lyrics, synced)

    def pop(self, orig_metadata):
        return self.cache.pop(self._key_from_metadata(orig_metadata), False) or None

    @staticmethod
    def _key_from_metadata(orig_metadata):
        return (orig_metadata["~dirname"], orig_metadata["~filename"], orig_metadata["~extension"])


lyrics_cache = LyricsCache()
synced_lyrics_pattern = re.compile(r"(\[\d\d:\d\d\.\d\d\d]|<\d\d:\d\d\.\d\d\d>)")
tags_pattern = re.compile(r"%(\w+)%")
extra_file_variables = {
    "filepath": lambda file: file,
    "folderpath": lambda file: os.path.dirname(file),  # pylint: disable=unnecessary-lambda
    "filename": lambda file: os.path.splitext(os.path.basename(file))[0],
    "filename_ext": lambda file: os.path.basename(file),  # pylint: disable=unnecessary-lambda
    "directory": lambda file: os.path.basename(os.path.dirname(file))
}


def get_lyrics(track, file):
    album = track.album
    metadata = file.metadata
    if not (config.setting[ADD_UNSYNCED_LYRICS] or config.setting[ADD_SYNCED_LYRICS]):
        return
    if not (metadata.get("title") and metadata.get("artist")):
        log.debug(f"Skipping fetching lyrics for track in {album} as both title and artist are required")
        return
    if config.setting[NEVER_REPLACE_LYRICS] and metadata.get("lyrics"):
        log.debug(f"Skipping fetching lyrics for {metadata['title']} as lyrics are already embedded")
        return
    args = {
        "track_name": metadata["title"],
        "artist_name": metadata["artist"],
    }
    if metadata.get("album"):
        args["album_name"] = metadata["album"]
    handler = partial(response_handler, metadata, file.orig_metadata)
    album.tagger.webservice.get_url(
        method="GET",
        handler=handler,
        parse_response_type='json',
        url=URL,
        unencoded_queryargs=args
    )


def response_handler(metadata, orig_metadata, document, reply, error):
    if document and not error:
        unsynced_lyrics = document.get("plainLyrics")
        synced_lyrics = document.get("syncedLyrics")
        if unsynced_lyrics:
            lyrics_cache.set(orig_metadata, unsynced_lyrics, False)
            if ((not config.setting[ADD_UNSYNCED_LYRICS]) or
                    (config.setting[NEVER_REPLACE_LYRICS] and metadata.get("lyrics"))):
                return
            metadata["lyrics"] = unsynced_lyrics
        if synced_lyrics:
            lyrics_cache.set(orig_metadata, synced_lyrics, True)
            # Support for the syncedlyrics tag is not available yet
            # if (not config.setting[ADD_SYNCED_LYRICS] or
            #         (config.setting[NEVER_REPLACE_LYRICS] and metadata.get("syncedlyrics"))):
            #     return
            # metadata["syncedlyrics"] = syncedlyrics
    else:
        log.debug(f"Could not fetch lyrics for {metadata['title']}")


def get_lrc_file_name(file, synced):
    conf_filename = config.setting[LRC_FILENAME if synced else TXT_FILENAME]
    filename = f"{tags_pattern.sub('{}', conf_filename)}"
    # If sidecar option is selected, override any pattern
    if config.setting[LRC_AS_SIDECAR]:
        ext = "lrc" if synced else "txt"
        filename = f"{os.path.splitext(file.filename)[0]}.{ext}"
        log.debug(f"LRC sidecar filename for {file.metadata['title']}: {filename}")
        return filename
    # Otherwise, parse the pattern
    tags = tags_pattern.findall(conf_filename)
    values = []
    for tag in tags:
        if tag in extra_file_variables:
            values.append(extra_file_variables[tag](file.filename))
        else:
            values.append(file.metadata.get(tag, f"%{tag}%"))
    return filename.format(*values)


def export_lrc_file(file):
    if config.setting[EXPORT_LRC]:
        metadata = file.metadata
        # If no lyrics were downloaded, try to export the lyrics already embedded
        cache = lyrics_cache.pop(file.orig_metadata)
        lyrics, synced = cache if cache else (metadata.get("lyrics"), False)
        if lyrics:
            filename = get_lrc_file_name(file, synced)
            if config.setting[NEVER_REPLACE_LRC] and os.path.exists(filename):
                return
            try:
                with open(filename, 'w') as file:
                    file.write(lyrics)
                log.debug(f"Created new lyrics file at {filename}")
            except OSError:
                log.debug(f"Could not create the lrc file for {metadata['title']}")
        else:
            log.debug(f"Could not export any lyrics for {metadata['title']}")


def remove_files_from_cache(files):
    for file in files:
        lyrics_cache.pop(file.orig_metadata)


class ImportLrc(BaseAction):
    NAME = 'Import lyrics from lrc files'

    def callback(self, objs):
        for track in objs:
            if isinstance(track, Track):
                file = track.files[0]
                found = False

                for synced in [True, False]:
                    try:
                        with open(get_lrc_file_name(file, synced), 'r') as lyrics_file:
                            lyrics = lyrics_file.read()
                            if synced_lyrics_pattern.search(lyrics):
                                # Support for syncedlyrics is not available yet
                                # file.metadata["syncedlyrics"] = lyrics
                                pass
                            else:
                                file.metadata["lyrics"] = lyrics
                        found = True
                        break
                    except FileNotFoundError:
                        pass

                if not found:
                    log.debug(f"Could not find matching lrc file for {file.metadata['title']}")


class LrclibLyricsOptions(OptionsPage):

    NAME = "lrclib_lyrics"
    TITLE = "Lrclib Lyrics"
    PARENT = "plugins"

    # By default, use a path for the LRC file in the same folder as
    # the music file so as not to store the LRC files "somewhere"
    __default_naming = f"%folderpath%{os.sep}%filename%"

    options = [
        config.BoolOption("setting", ADD_UNSYNCED_LYRICS, True),
        config.BoolOption("setting", ADD_SYNCED_LYRICS, False),
        config.BoolOption("setting", NEVER_REPLACE_LYRICS, False),
        config.BoolOption("setting", LRC_AS_SIDECAR, True),
        config.TextOption("setting", LRC_FILENAME, __default_naming + ".lrc"),
        config.TextOption("setting", TXT_FILENAME, __default_naming + ".txt"),
        config.BoolOption("setting", EXPORT_LRC, False),
        config.BoolOption("setting", NEVER_REPLACE_LRC, False),
    ]

    def __init__(self, parent=None):
        super(LrclibLyricsOptions, self).__init__(parent)
        self.ui = Ui_OptionLrclibLyrics()
        self.ui.setupUi(self)

    def load(self):
        self.ui.lyrics.setChecked(config.setting[ADD_UNSYNCED_LYRICS])
        self.ui.syncedlyrics.setChecked(config.setting[ADD_SYNCED_LYRICS])
        self.ui.replace_embedded.setChecked(config.setting[NEVER_REPLACE_LYRICS])
        self.ui.lrc_name.setText(config.setting[LRC_FILENAME])
        self.ui.txt_name.setText(config.setting[TXT_FILENAME])
        self.ui.lrc_as_sidecar.setChecked(config.setting[LRC_AS_SIDECAR])
        self.ui.export_lyrics.setChecked(config.setting[EXPORT_LRC])
        self.ui.replace_exported.setChecked(config.setting[NEVER_REPLACE_LRC])

        # Initialize the LRC filename field state
        self.update_lrc_name_field_state()
        # Connect the sidecar checkbox to update the filename field state
        self.ui.lrc_as_sidecar.toggled.connect(self.update_lrc_name_field_state)

    def save(self):
        config.setting[ADD_UNSYNCED_LYRICS] = self.ui.lyrics.isChecked()
        config.setting[ADD_SYNCED_LYRICS] = self.ui.syncedlyrics.isChecked()
        config.setting[NEVER_REPLACE_LYRICS] = self.ui.replace_embedded.isChecked()
        config.setting[LRC_FILENAME] = self.ui.lrc_name.text()
        config.setting[TXT_FILENAME] = self.ui.txt_name.text()
        config.setting[LRC_AS_SIDECAR] = self.ui.lrc_as_sidecar.isChecked()
        config.setting[EXPORT_LRC] = self.ui.export_lyrics.isChecked()
        config.setting[NEVER_REPLACE_LRC] = self.ui.replace_exported.isChecked()

    def update_lrc_name_field_state(self):
        """Enable or disable the LRC filename field based on the sidecar option."""
        enable = not self.ui.lrc_as_sidecar.isChecked()
        self.ui.lrc_name.setEnabled(enable)
        self.ui.txt_name.setEnabled(enable)


ratecontrol.set_minimum_delay_for_url(URL, REQUESTS_DELAY)
register_file_post_addition_to_track_processor(get_lyrics)
register_file_post_save_processor(export_lrc_file)
register_file_post_removal_from_track_processor(lambda _track, file: remove_files_from_cache([file]))
register_album_post_removal_processor(
    lambda album: remove_files_from_cache([file for track in album.tracks for file in track.files])
)
register_track_action(ImportLrc())
register_options_page(LrclibLyricsOptions)
