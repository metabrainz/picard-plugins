#!/usr/bin/python
# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Generate M3U playlist"
PLUGIN_AUTHOR = u"Francis Chin"
PLUGIN_DESCRIPTION = u"Generate an Extended M3U playlist (.m3u8 utf_8 \
encoded file). Relative pathnames are used if saving to the directory \
containing the audio files, otherwise absolute pathnames are used."
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.10", "0.15"]

import os.path

from PyQt4 import QtCore, QtGui
from picard.util import find_existing_path, encode_filename
from picard.ui.itemviews import BaseAction, register_album_action


class PlaylistEntry(list):

    def __init__(self, playlist, index):
        list.__init__(self)
        self.playlist = playlist
        self.index = index

    def add(self, unicode):
        self.append(unicode + "\n")


class Playlist(object):

    def __init__(self, filename):
        self.filename = filename
        self.entries = []
        self.headers = []

    def add_header(self, unicode):
        self.headers.append(unicode + "\n")

    def write(self):
        b_lines = []
        for header in self.headers:
            b_lines.append(header.encode("utf-8"))
        for entry in self.entries:
            for row in entry:
                b_lines.append(unicode(row).encode("utf-8"))
        with open(encode_filename(self.filename), "wt") as f:
            f.writelines(b_lines)


class GeneratePlaylist(BaseAction):
    NAME = "Generate &Playlist..."

    def callback(self, objs):
        current_directory = (self.config.persist["current_directory"]
                             or QtCore.QDir.homePath())
        current_directory = find_existing_path(unicode(current_directory))
        # Default playlist filename set as "%albumartist% - %album%.m3u8"
        # To do: make configurable
        default_filename = (objs[0].metadata["albumartist"] + " - "
                            + objs[0].metadata["album"] + ".m3u8")
        b_filename, b_selected_format = QtGui.QFileDialog.getSaveFileNameAndFilter(
            None, "Save new playlist",
            os.path.join(current_directory, default_filename),
            "Playlist (*.m3u8 *.m3u)"
        )
        if b_filename:
            filename = unicode(b_filename)
            playlist = Playlist(filename)
            playlist.add_header(u"#EXTM3U")
            
            for album in objs:
                for track in album.tracks:
                    if track.linked_files:
                        entry = PlaylistEntry(playlist, len(playlist.entries))
                        playlist.entries.append(entry)
                        
                        # M3U EXTINF row
                        track_length_seconds = int(round(track.metadata.length / 1000.0))
                        # EXTINF format assumed to be fixed as follows:
                        entry.add(u"#EXTINF:{duration:d},{artist} - {title}".format(
                            duration=track_length_seconds,
                            artist=track.metadata["artist"],
                            title=track.metadata["title"]
                            )
                        )
                        
                        # M3U media file row - assumes only one file per track
                        audio_filename = track.linked_files[0].filename
                        # If playlist is in same directory as audio files, then use
                        # local (relative) pathname, otherwise use absolute pathname
                        if os.path.dirname(filename) == os.path.dirname(audio_filename):
                            audio_filename = os.path.basename(audio_filename)
                        entry.add(unicode(audio_filename))
            
            playlist.write()


register_album_action(GeneratePlaylist())
