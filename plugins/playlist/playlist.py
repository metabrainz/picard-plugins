#!/usr/bin/python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

PLUGIN_NAME = "Generate M3U playlist"
PLUGIN_AUTHOR = "Francis Chin, Sambhav Kothari"
PLUGIN_DESCRIPTION = """Generate an Extended M3U playlist (.m3u8 file, UTF8
encoded text). Relative pathnames are used where audio files are in the same
directory as the playlist, otherwise absolute (full) pathnames are used."""
PLUGIN_VERSION = "1.2"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import os.path

from PyQt5 import QtCore, QtWidgets
from picard import log
from picard.const import VARIOUS_ARTISTS_ID
from picard.util import find_existing_path, encode_filename
from picard.ui.itemviews import BaseAction, register_album_action


_debug_level = 0

def get_safe_filename(filename):
    _valid_chars = " .,_-:+&!()"
    _safe_filename = "".join(
        c if (c.isalnum() or c in _valid_chars) else "_" for c in filename
    ).rstrip()
    return _safe_filename


class PlaylistEntry(list):

    def __init__(self, playlist, index):
        list.__init__(self)
        self.playlist = playlist
        self.index = index

    def add(self, entry_row):
        self.append(entry_row + "\n")


class Playlist(object):

    def __init__(self, filename):
        self.filename = filename
        self.entries = []
        self.headers = []

    def add_header(self, header):
        self.headers.append(header + "\n")

    def write(self):
        b_lines = []
        for header in self.headers:
            b_lines.append(header.encode("utf-8"))
        for entry in self.entries:
            for row in entry:
                b_lines.append(row.encode("utf-8"))
        with open(encode_filename(self.filename), "wb") as f:
            f.writelines(b_lines)


class GeneratePlaylist(BaseAction):
    NAME = "Generate &Playlist..."

    def callback(self, objs):
        current_directory = (self.config.persist["current_directory"]
                             or QtCore.QDir.homePath())
        current_directory = find_existing_path(current_directory)
        # Default playlist filename set as "%albumartist% - %album%.m3u8",
        # except where "Various Artists" is suppressed
        if _debug_level > 1:
            log.debug("{}: VARIOUS_ARTISTS_ID is {}, musicbrainz_albumartistid is {}".format(
                    PLUGIN_NAME, VARIOUS_ARTISTS_ID,
                    objs[0].metadata["musicbrainz_albumartistid"]))
        if objs[0].metadata["musicbrainz_albumartistid"] != VARIOUS_ARTISTS_ID:
            default_filename = get_safe_filename(
                objs[0].metadata["albumartist"] + " - "
                + objs[0].metadata["album"] + ".m3u8"
            )
        else:
            default_filename = get_safe_filename(
                objs[0].metadata["album"] + ".m3u8"
            )
        if _debug_level > 1:
            log.debug("{}: default playlist filename sanitized to {}".format(
                    PLUGIN_NAME, default_filename))
        filename, selected_format = QtWidgets.QFileDialog.getSaveFileName(
            None, "Save new playlist",
            os.path.join(current_directory, default_filename),
            "Playlist (*.m3u8 *.m3u)"
        )
        if filename:
            playlist = Playlist(filename)
            playlist.add_header("#EXTM3U")

            for album in objs:
                for track in album.tracks:
                    if track.linked_files:
                        entry = PlaylistEntry(playlist, len(playlist.entries))
                        playlist.entries.append(entry)

                        # M3U EXTINF row
                        track_length_seconds = int(round(track.metadata.length / 1000.0))
                        # EXTINF format assumed to be fixed as follows:
                        entry.add("#EXTINF:{duration:d},{artist} - {title}".format(
                            duration=track_length_seconds,
                            artist=track.metadata["artist"],
                            title=track.metadata["title"]
                            )
                        )

                        # M3U URL row - assumes only one file per track
                        audio_filename = track.linked_files[0].filename
                        if _debug_level > 1:
                            for i, file in enumerate(track.linked_files):
                                log.debug("{}: linked_file {}: {}".format(
                                    PLUGIN_NAME, i, str(file)))
                        # If playlist is in same directory as audio files, then use
                        # local (relative) pathname, otherwise use absolute pathname
                        if _debug_level > 1:
                            log.debug("{}: audio_filename: {}, selected dir: {}".format(
                                    PLUGIN_NAME, audio_filename, os.path.dirname(filename)))

                        audio_filename = os.path.relpath(audio_filename, os.path.dirname(filename))
                        entry.add(str(audio_filename))

            playlist.write()


register_album_action(GeneratePlaylist())
