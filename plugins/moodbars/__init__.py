# -*- coding: utf-8 -*-

# Changelog:
#   [2015-09-24] Initial version with support for Ogg Vorbis, FLAC, WAV and MP3, tested MP3 and FLAC

PLUGIN_NAME = "Moodbars"
PLUGIN_AUTHOR = "Len Joubert, Sambhav Kothari"
PLUGIN_DESCRIPTION = """Calculate Moodbars for selected files and albums."""
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["2.0"]
#PLUGIN_INCOMPATIBLE_PLATFORMS = [
#    'win32', 'cygwyn', 'darwin', 'os2', 'os2emx', 'riscos', 'atheos']

import os.path
from collections import defaultdict
from subprocess import check_call
from picard.album import Album, NatAlbum
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, partial, thread
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
    file_list = ['%s' % encode_filename(f.filename) for f in files]
    for mood_file in file_list:
        new_filename = os.path.join(os.path.dirname(
            mood_file), '.' + os.path.splitext(os.path.basename(mood_file))[0] + '.mood')
        # file format to make it compaitble with Amarok and hidden in linux
        file_list_mood = ['%s' % new_filename]

    if format in MOODBAR_COMMANDS \
            and tagger.config.setting[MOODBAR_COMMANDS[format][0]]:
        command = tagger.config.setting[MOODBAR_COMMANDS[format][0]]
        options = tagger.config.setting[
            MOODBAR_COMMANDS[format][1]].split(' ')
#        tagger.log.debug('My debug >>>  %s' % (file_list_mood))
        tagger.log.debug(
            '%s %s %s %s' % (command, decode_filename(' '.join(file_list)), ' '.join(options), decode_filename(' '.join(file_list_mood))))
        check_call([command] + file_list + options + file_list_mood)
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
        generate_moodbar_for_files([file], file.NAME, self.tagger)

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
        self.config.setting["moodbar_vorbis_command"] = string_(
            self.ui.vorbis_command.text())
        self.config.setting["moodbar_mp3_command"] = string_(
            self.ui.mp3_command.text())
        self.config.setting["moodbar_flac_command"] = string_(
            self.ui.flac_command.text())
        self.config.setting["moodbar_wav_command"] = string_(
            self.ui.wav_command.text())

register_file_action(MoodBar())
register_options_page(MoodbarOptionsPage)
