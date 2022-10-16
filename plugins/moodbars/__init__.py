# -*- coding: utf-8 -*-

# Changelog:
# [2015-09-24] Initial version with support for Ogg Vorbis, FLAC, WAV and MP3, tested MP3 and FLAC
# [2017-11-21] Amended to Python3 & Qt5
# [2017-11-21] removed unicode, replaced str with string_ and untrusted input on check_call addressed

PLUGIN_NAME = "Moodbars"
PLUGIN_AUTHOR = "Len Joubert, Sambhav Kothari"
PLUGIN_DESCRIPTION = """Calculate Moodbars for selected files and albums.<br /><br />
According to <a href="http://en.wikipedia.org/wiki/Moodbar">WikiPedia</a>
a "Moodbar is a computer visualization used for navigating within a piece of music or any other recording on a digital audio track.
This is done with a commonly horizontal bar that is divided into vertical stripes.
Each stripe has a colour combination showing the "mood" within a short part of the audio track."<br /><br />
To use this plugin you will need to download special executables to create the moodbars -
at the time of writing, executables are only available for various Linux distributions
(see the <a href="http://userbase.kde.org/Amarok/Manual/Various/Moodbar">Amarok Moodbar page<a> for details).
"""
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_VERSION = "2.3.3"
PLUGIN_API_VERSIONS = ["2.0"]
# PLUGIN_INCOMPATIBLE_PLATFORMS = [
#    'win32', 'cygwyn', 'darwin', 'os2', 'os2emx', 'riscos', 'atheos']

import os.path
from functools import partial
from collections import defaultdict
from subprocess import check_call
from picard.album import Album, NatAlbum
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, thread
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.moodbars.ui_options_moodbar import Ui_MoodbarOptionsPage

# Path to various moodbar tools. There must be a tool for every supported
# audio file format.
MOODBAR_COMMANDS = {
    "Ogg Vorbis": ("moodbar_vorbis_command", "moodbar_vorbis_options"),
    "MPEG-1 Audio": ("moodbar_mp3_command", "moodbar_mp3_options"),
    "FLAC": ("moodbar_flac_command", "moodbar_flac_options"),
    "WavPack": ("moodbar_wav_command", "moodbar_wav_options"),
}


def generate_moodbar_for_files(files, format, tagger):
    """Generate the moodfiles for a list of files in album mode."""
    # python3 list for subprocess
    command_to_execute = []
    file_list = [files]
    for mood_file in file_list:
        new_filename = os.path.join(os.path.dirname(
            mood_file), '.' + os.path.splitext(os.path.basename(mood_file))[0] + '.mood')
        # file format to make it compaitble with Amarok and hidden in linux
        file_list_mood = ['%s' % new_filename]
        file_list_music = ['%s' % file_list[0]]

    if format in MOODBAR_COMMANDS \
            and tagger.config.setting[MOODBAR_COMMANDS[format][0]]:
        command = tagger.config.setting[MOODBAR_COMMANDS[format][0]]
        options = tagger.config.setting[
            MOODBAR_COMMANDS[format][1]].split(' ')
        # tagger.log.debug('My debug file_list_mood >>>  %s' %
        #    (file_list_mood))
        #tagger.log.debug('My debug file_list >>>  %s' % (file_list_music))
        #tagger.log.debug('My debug command >>>  %s' % (command))
        #tagger.log.debug('My debug options >>>  %s' % (options))
        # tagger.log.debug(
        #    '%s %s %s %s' % (command, decode_filename(' '.join(file_list)), ' '.join(options), decode_filename(' '.join(file_list_mood))))
        # command args order corrected for new moodbar
        command_to_execute.append(command)
        command_to_execute = command_to_execute + options
        # need to decode the file string and appand to the list
        command_to_execute.append(file_list_mood[0])
        command_to_execute = command_to_execute + file_list_music
        tagger.log.debug('My debug command to execute >>>  %s' %
                         (command_to_execute))
        check_call(command_to_execute, shell=False)
        # check_call([command] + options + file_list_mood + file_list)
    else:
        raise Exception('Moodbar: Unsupported format %s' % (format))


class MoodBar(BaseAction):
    NAME = N_("Generate Moodbar &file...")

    def _add_file_to_queue(self, file):
        thread.run_task(
            partial(self._generate_moodbar, file),
            partial(self._moodbar_callback, file))

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track):
                for file_ in obj.linked_files:
                    self._add_file_to_queue(file_)
            elif isinstance(obj, File):
                self._add_file_to_queue(obj)

    def _generate_moodbar(self, file):
        self.tagger.window.set_statusbar_message(
            N_('Calculating moodbar for "%(filename)s"...'),
            {'filename': file.filename}
        )
        generate_moodbar_for_files(file.filename, file.NAME, self.tagger)

    def _moodbar_callback(self, file, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(
                N_('Moodbar for "%(filename)s" successfully generated.'),
                {'filename': file.filename}
            )
        else:
            self.tagger.window.set_statusbar_message(
                N_('Could not generate moodbar for "%(filename)s".'),
                {'filename': file.filename}
            )


class MoodbarOptionsPage(OptionsPage):

    NAME = "Moodbars"
    TITLE = "Moodbars"
    PARENT = "plugins"

    options = [
        TextOption("setting", "moodbar_vorbis_command", "moodbar"),
        TextOption("setting", "moodbar_vorbis_options", "-o"),
        TextOption("setting", "moodbar_mp3_command", "moodbar"),
        TextOption("setting", "moodbar_mp3_options", "-o"),
        TextOption("setting", "moodbar_flac_command", "moodbar"),
        TextOption("setting", "moodbar_flac_options", "-o"),
        TextOption("setting", "moodbar_wav_command", "moodbar"),
        TextOption("setting", "moodbar_wav_options", "-o")
    ]

    def __init__(self, parent=None):
        super(MoodbarOptionsPage, self).__init__(parent)
        self.ui = Ui_MoodbarOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.vorbis_command.setText(
            self.config.setting["moodbar_vorbis_command"])
        self.ui.mp3_command.setText(
            self.config.setting["moodbar_mp3_command"])
        self.ui.flac_command.setText(
            self.config.setting["moodbar_flac_command"])
        self.ui.wav_command.setText(
            self.config.setting["moodbar_wav_command"])

    def save(self):
        self.config.setting["moodbar_vorbis_command"] = self.ui.vorbis_command.text()
        self.config.setting["moodbar_mp3_command"] = self.ui.mp3_command.text()
        self.config.setting["moodbar_flac_command"] = self.ui.flac_command.text()
        self.config.setting["moodbar_wav_command"] = self.ui.wav_command.text()

register_file_action(MoodBar())
register_options_page(MoodbarOptionsPage)
