# -*- coding: utf-8 -*-
PLUGIN_NAME = "ReplayGain"
PLUGIN_AUTHOR = "Philipp Wolfer, Sophist"
PLUGIN_DESCRIPTION = """<h2>Calculate ReplayGain for selected files and albums.</h2>
<p>
This plugin calculates the ReplayGain values for Albums and / or Tracks.
These values are stored in tags and music players use this information
to adjust the played volume so that all tracks have a similar volume
and you don't get tracks that you can barely hear and need to turn up the volume for
followed by tracks with a mucg louder volume so that you are then deafened.
</p><p>
This plugin needs separate external executables to be run to calculate the replay gains.
You need to download these executables and then configure the ReplayGain plugin in
Options / Plugins / ReplayGain with the path and filename of the executable.
</p><p>
As executables, they are probably best stored in a directory which is normally read-only for normal users
and requires administrative write access to store the executable (e.g. the Picard executable directory),
but you can store them in the plugins directory if you wish.
</p><hr/>
<p>Whilst this version works, it has some issues:</p>
<ul>
<li>It doesn't work with file paths / names containing unicode characters</li>
<li>On Windows it opens an empty window whilst processing</li>
<li>Tags are stored directly in the files, are not displayed in Picard until the files are reloaded and will be overwritten if Picard saves the files</li>
<li>You need to add the replay gain tags to Options / Tags / Preserve these tags from being overwritten with MusicBrainz data (because Musicbrainz does not provide this data)</li>
<li>The tags written to the file may be non-standard (depending on the ReplayGain executable you use)</li>
</ul>
<h3>Windows</h3>
<ul>
<li>vorbisgain - Executable 0.37 inside zip file from https://www.rarewares.org/ogg-tools.php</li>
<li>mp3gain - Use AACGain from https://www.rarewares.org/aac-encoders.php#aacgain</li>
<li>metaflac - Download the latest flac-*-win.zip file from https://ftp.osuosl.org/pub/xiph/releases/flac/ and extract metaflac.exe</li>
<li>wvgain - http://www.wavpack.com/downloads.html</li>
</ul>
<p>You may also have some success using the Chocolatey package manager for aacgain, flac and wavpack.</p>
<h3>Linux</h3>
<ul>
<li>vorbisgain - Build from source from https://www.rarewares.org/ogg-tools.php</li>
<li>mp3gain - Install aacgain using your package manager e.g. apt.</li>
<li>metaflac - Use package manager to get FLAC</li>
<li>wvgain - http://www.wavpack.com/downloads.html</li>
</ul>
<h3>Mac</h3>
<ul>
<li>vorbisgain - Build from source from https://www.rarewares.org/ogg-tools.php</li>
<li>mp3gain - https://ports.macports.org/port/aacgain/summary</li>
<li>metaflac - Install using "brew install flac"</li>
<li>wvgain - http://www.wavpack.com/downloads.html</li>
</ul>
<p>You might also liketo try MP3Gain Express for MacOS from https://projects.sappharad.com/mp3gain/ as an alternative to mp3gain/aacgain.</p>
"""
PLUGIN_VERSION = "0.3"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from collections import defaultdict
from functools import partial
import subprocess

from picard.album import Album, NatAlbum
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, thread
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.replaygain.ui_options_replaygain import Ui_ReplayGainOptionsPage

# Path to various replay gain tools. There must be a tool for every supported
# audio file format.
REPLAYGAIN_COMMANDS = {
    "Ogg Vorbis": ("replaygain_vorbisgain_command", "replaygain_vorbisgain_options"),
    "MPEG-1 Audio": ("replaygain_mp3gain_command", "replaygain_mp3gain_options"),
    "FLAC": ("replaygain_metaflac_command", "replaygain_metaflac_options"),
    "WavPack": ("replaygain_wvgain_command", "replaygain_wvgain_options"),
}


def calculate_replay_gain_for_files(files, format_, tagger):
    """Calculates the replay gain for a list of files in album mode."""
    file_list = [encode_filename(f.filename) for f in files]

    if format_ in REPLAYGAIN_COMMANDS \
        and tagger.config.setting[REPLAYGAIN_COMMANDS[format_][0]]:
        command = tagger.config.setting[REPLAYGAIN_COMMANDS[format_][0]]
        options = tagger.config.setting[REPLAYGAIN_COMMANDS[format_][1]].split(' ')
        call = [command] + options + file_list
        tagger.log.debug(call)
        with subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
            (output, null) = process.communicate()
            output = output.splitlines()
            for line in output:
                if line:
                    tagger.log.debug(line)
            rc = process.poll()
        if rc:
            raise Exception('ReplayGain: Non-zero return code from command %d' % rc)
    else:
        raise Exception('ReplayGain: Unsupported format %s' % (format_))


class ReplayGain(BaseAction):
    NAME = N_("Calculate track Replay&Gain...")

    def _add_file_to_queue(self, file):
        thread.run_task(
            partial(self._calculate_replaygain, file),
            partial(self._replaygain_callback, file))

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track):
                for file_ in obj.linked_files:
                    self._add_file_to_queue(file_)
            elif isinstance(obj, File):
                self._add_file_to_queue(obj)

    def _calculate_replaygain(self, file):
        self.tagger.window.set_statusbar_message(
            N_('Calculating replay gain for "%(filename)s"...'),
            {'filename': file.filename}
        )
        calculate_replay_gain_for_files([file], file.NAME, self.tagger)

    def _replaygain_callback(self, file, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(
                N_('Replay gain for "%(filename)s" successfully calculated.'),
                {'filename': file.filename}
            )
        else:
            self.tagger.window.set_statusbar_message(
                N_('Could not calculate replay gain for "%(filename)s".'),
                {'filename': file.filename}
            )


class AlbumGain(BaseAction):
    NAME = N_("Calculate album Replay&Gain...")

    def callback(self, objs):
        albums = filter(lambda o: isinstance(o, Album) and not isinstance(o,
                        NatAlbum), objs)
        nats = filter(lambda o: isinstance(o, NatAlbum), objs)

        for album in albums:
            thread.run_task(
                partial(self._calculate_albumgain, album),
                partial(self._albumgain_callback, album))

        for natalbum in nats:
            thread.run_task(
                partial(self._calculate_natgain, natalbum),
                partial(self._albumgain_callback, natalbum))

    def split_files_by_type(self, files):
        """Split the given files by filetype into separate lists."""
        files_by_format = defaultdict(list)

        for file in files:
            files_by_format[file.NAME].append(file)

        return files_by_format

    def _calculate_albumgain(self, album):
        self.tagger.window.set_statusbar_message(
            N_('Calculating album gain for "%(album)s"...'),
            {'album': album.metadata["album"]}
        )
        filelist = [t.linked_files[0] for t in album.tracks if t.is_linked()]

        for format_, files in self.split_files_by_type(filelist).items():
            calculate_replay_gain_for_files(files, format_, self.tagger)

    def _calculate_natgain(self, natalbum):
        """Calculates the replaygain"""
        self.tagger.window.set_statusbar_message(
            N_('Calculating album gain for "%(album)s"...'),
            {'album': natalbum.metadata["album"]}
        )
        filelist = [t.linked_files[0] for t in natalbum.tracks if t.is_linked()]

        for file_ in filelist:
            calculate_replay_gain_for_files([file_], file_.NAME, self.tagger)

    def _albumgain_callback(self, album, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(
                N_('Album gain for "%(album)s" successfully calculated.'),
                {'album': album.metadata["album"]}
            )
        else:
            self.tagger.window.set_statusbar_message(
                N_('Could not calculate album gain for "%(album)s".'),
                {'album': album.metadata["album"]}
            )


class ReplayGainOptionsPage(OptionsPage):

    NAME = "replaygain"
    TITLE = "ReplayGain"
    PARENT = "plugins"

    options = [
        TextOption("setting", "replaygain_vorbisgain_command", "vorbisgain"),
        TextOption("setting", "replaygain_vorbisgain_options", "-asf"),
        TextOption("setting", "replaygain_mp3gain_command", "mp3gain"),
        TextOption("setting", "replaygain_mp3gain_options", "-a -s i"),
        TextOption("setting", "replaygain_metaflac_command", "metaflac"),
        TextOption("setting", "replaygain_metaflac_options", "--add-replay-gain"),
        TextOption("setting", "replaygain_wvgain_command", "wvgain"),
        TextOption("setting", "replaygain_wvgain_options", "-a")
    ]

    def __init__(self, parent=None):
        super(ReplayGainOptionsPage, self).__init__(parent)
        self.ui = Ui_ReplayGainOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.vorbisgain_command.setText(self.config.setting["replaygain_vorbisgain_command"])
        self.ui.mp3gain_command.setText(self.config.setting["replaygain_mp3gain_command"])
        self.ui.metaflac_command.setText(self.config.setting["replaygain_metaflac_command"])
        self.ui.wvgain_command.setText(self.config.setting["replaygain_wvgain_command"])

    def save(self):
        self.config.setting["replaygain_vorbisgain_command"] = self.ui.vorbisgain_command.text()
        self.config.setting["replaygain_mp3gain_command"] = self.ui.mp3gain_command.text()
        self.config.setting["replaygain_metaflac_command"] = self.ui.metaflac_command.text()
        self.config.setting["replaygain_wvgain_command"] = self.ui.wvgain_command.text()


register_file_action(ReplayGain())
register_album_action(AlbumGain())
register_options_page(ReplayGainOptionsPage)
