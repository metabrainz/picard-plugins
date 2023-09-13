# -*- coding: utf-8 -*-
PLUGIN_NAME = "ReplayGain 2.0"
PLUGIN_AUTHOR = "complexlogic"
PLUGIN_DESCRIPTION = '''
Calculates ReplayGain information for tracks and albums according to the
[ReplayGain 2.0 specification](https://wiki.hydrogenaud.io/index.php?title=ReplayGain_2.0_specification).
This plugin depends on the ReplayGain utility [rsgain](https://github.com/complexlogic/rsgain). Users
are required to install rsgain and set its path in the plugin settings before use.

#### Usage
Select one or more tracks or albums, then right click and select Plugin->Calculate ReplayGain. The plugin
will calculate ReplayGain information for the selected items and display the results in the metadata
window. Click the save button to write the tags to file.

The following file formats are supported:

- MP3 (.mp3)
- FLAC (.flac)
- Ogg (.ogg, .oga, spx)
- Opus (.opus)
- MPEG-4 Audio (.m4a, .mp4)
- Wavpack (.wv)
- Monkey's Audio (.ape)
- WMA (.wma)
- MP2 (.mp2)
- WAV (.wav)
- AIFF (.aiff)
- TAK (.tak)

This plugin is based on the original ReplayGain plugin by Philipp Wolfer and Sophist.
'''
PLUGIN_VERSION = "1.4"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from functools import partial
import subprocess  # nosec: B404
import shutil
import os

from PyQt5.QtWidgets import QFileDialog

from picard import log
from picard.formats import (
    AiffFile,
    ASFFile,
    FLACFile,
    MonkeysAudioFile,
    MP3File,
    MP4File,
    OggFLACFile,
    OggOpusFile,
    OggSpeexFile,
    OggTheoraFile,
    OggVorbisFile,
    TAKFile,
    WAVFile,
    WavPackFile,
)
from picard.album import Album
from picard.track import Track, NonAlbumTrack
from picard.util import thread
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption, BoolOption, IntOption, config
from picard.ui.itemviews import (BaseAction, register_track_action,
                                 register_album_action)
from picard.plugins.replaygain2.ui_options_replaygain2 import Ui_ReplayGain2OptionsPage


CLIP_MODE_DISABLED = 0
CLIP_MODE_POSITIVE = 1
CLIP_MODE_ALWAYS = 2

CLIP_MODE_MAP = (
    "n",
    "p",
    "a"
)

OPUS_MODE_STANDARD = 0
OPUS_MODE_R128 = 1

SUPPORTED_FORMATS = (
    AiffFile,
    ASFFile,
    FLACFile,
    MonkeysAudioFile,
    MP3File,
    MP4File,
    OggFLACFile,
    OggOpusFile,
    OggSpeexFile,
    OggTheoraFile,
    OggVorbisFile,
    TAKFile,
    WAVFile,
    WavPackFile,
)

TABLE_HEADER = (
    "filename",
    "loudness",
    "gain",
    "peak",
    "peak_db",
    "peak_type",
    "clipping_adjustment"
)

TAGS = (
    "replaygain_album_gain",
    "replaygain_album_peak",
    "replaygain_album_range",
    "replaygain_reference_loudness",
    "replaygain_track_gain",
    "replaygain_track_peak",
    "replaygain_track_range",
    "r128_album_gain",
    "r128_track_gain"
)

# Make sure the rsgain executable exists
def rsgain_found(rsgain_command, window):
    if not os.path.exists(rsgain_command) and shutil.which(rsgain_command) is None:
        window.set_statusbar_message("Failed to locate rsgain. Enter the path in the plugin settings.")
        return False
    return True

# Convert Picard settings dict to rsgain command line options
def build_options(config):
    options = ["custom", "-O", "-s", "s"]
    if (config.setting["album_tags"]):
        options.append("-a")
    if (config.setting["true_peak"]):
        options.append("-t")
    options += ["-l", str(config.setting["target_loudness"])]
    options += ["-c", CLIP_MODE_MAP[config.setting["clip_mode"]]]
    options += ["-m", str(config.setting["max_peak"])]
    return options

# Convert table row to result dict
def parse_result(line):
    result = dict()
    columns = line.split("\t")

    if len(columns) != len(TABLE_HEADER):
        return None
    for i, column in enumerate(columns):
        result[TABLE_HEADER[i]] = column
    return result

# Format the gain as a Q7.8 fixed point number per RFC 7845
# see: https://datatracker.ietf.org/doc/html/rfc7845
def format_r128(result, config):
    gain = float(result["gain"])
    if config.setting["opus_m23"]:
        gain += float(-23 - config.setting["target_loudness"])
    return str(int(round(gain * 256.0)))

def update_metadata(metadata, track_result, album_result, is_nat, r128_tags):
    for tag in TAGS:
        metadata.delete(tag)

    # Opus R128 tags
    if r128_tags:
        metadata.set("r128_track_gain", format_r128(track_result, config))
        if album_result is not None:
            metadata.set("r128_album_gain", format_r128(album_result, config))

    # Standard ReplayGain tags
    else:
        metadata.set("replaygain_track_gain", track_result["gain"] + " dB")
        metadata.set("replaygain_track_peak", track_result["peak"])
        if config.setting["album_tags"]:
            if is_nat:
                metadata.set("replaygain_album_gain", track_result["gain"] + " dB")
                metadata.set("replaygain_album_peak", track_result["peak"])
            elif album_result is not None:
                metadata.set("replaygain_album_gain", album_result["gain"] + " dB")
                metadata.set("replaygain_album_peak", album_result["peak"])
        if config.setting["reference_loudness"]:
            metadata.set("replaygain_reference_loudness", f"{float(config.setting['target_loudness']):.2f} LUFS")

def calculate_replaygain(tracks, options):

    # Make sure files are of supported type, build file list
    files = list()
    valid_tracks = list()
    for track in tracks:
        if not track.files:
            continue
        file = track.files[0]
        if not type(file) in SUPPORTED_FORMATS:
            raise Exception(f"ReplayGain 2.0: File '{file.filename}' is of unsupported format")
        files.append(file.filename)
        valid_tracks.append(track)

    call = [config.setting["rsgain_command"]] + options + files
    for item in call:
        item.encode("utf-8")

    # Prevent an unwanted console spawn in Windows
    si = None
    if (os.name == "nt"):
        si = subprocess.STARTUPINFO()
        si.dwFlags = subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE

    # Execute the scan with rsgain
    lines = list()
    with subprocess.Popen(  # nosec: B603
        call,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        startupinfo=si,
        encoding="utf-8",
        text=True
    ) as process:
        (output, _unused) = process.communicate()
        rc = process.poll()
        if rc:
            raise Exception(f'ReplayGain 2.0: rsgain returned non-zero code ({rc})')
        log.debug(output)
        lines = output.splitlines()
    album_tags = config.setting["album_tags"]

    # Make sure the number of rows in the output is what we expected
    if (len(lines) !=
        1                            # Table header
        + len(valid_tracks)          # 1 row per track
        + 1 if album_tags else 0):   # Album result
        raise Exception(f"ReplayGain 2.0: Unexpected output from rsgain: {lines}")
    lines.pop(0) # Don't care about the table header

    # Parse album result
    album_result = None
    if album_tags:
        album_result = parse_result(lines[-1])
        lines.pop(-1)

    # Parse track results
    results = list()
    for line in lines:
        result = parse_result(line)
        if result is None:
            raise Exception("ReplayGain 2.0: Failed to parse result")
        results.append(result)

    # Update track metadata with results
    opus_r128 = config.setting["opus_mode"] == OPUS_MODE_R128
    for i, track in enumerate(valid_tracks):
        for file in track.files:
            update_metadata(
                file.metadata,
                results[i],
                album_result,
                isinstance(track, NonAlbumTrack),
                opus_r128 and isinstance(file, OggOpusFile)
            )


class ScanTracks(BaseAction):
    NAME = "Calculate Replay&Gain..."

    def callback(self, objs):
        if not rsgain_found(self.config.setting["rsgain_command"], self.tagger.window):
            return
        tracks = list(filter(lambda o: isinstance(o, Track), objs))
        self.options = build_options(self.config)
        num_tracks = len(tracks)
        if num_tracks == 1:
            self.tagger.window.set_statusbar_message(
                'Calculating ReplayGain for %s...', {tracks[0].files[0].filename}
            )
        else:
            self.tagger.window.set_statusbar_message(
                'Calculating ReplayGain for %i tracks...', num_tracks
            )
        thread.run_task(
            partial(calculate_replaygain, tracks, self.options),
            partial(self._replaygain_callback, tracks)
        )

    def _replaygain_callback(self, tracks, result=None, error=None):
        if error is None:
            for track in tracks:
                for file in track.files:
                    file.update()
                track.update()
            self.tagger.window.set_statusbar_message('ReplayGain successfully calculated.')
        else:
            self.tagger.window.set_statusbar_message('Could not calculate ReplayGain.')


class ScanAlbums(BaseAction):
    NAME = "Calculate Replay&Gain..."

    def callback(self, objs):
        if not rsgain_found(self.config.setting["rsgain_command"], self.tagger.window):
            return
        self.options = build_options(self.config)
        albums = list(filter(lambda o: isinstance(o, Album), objs))

        self.num_albums = len(albums)
        self.current = 0
        if (self.num_albums == 1):
            self.tagger.window.set_statusbar_message(
                'Calculating ReplayGain for "%s"...', albums[0].metadata['album']
            )
        else:
            self.tagger.window.set_statusbar_message(
                'Calculating ReplayGain for %i albums...', self.num_albums
            )
        for album in albums:
            thread.run_task(
                partial(calculate_replaygain, album.tracks, self.options),
                partial(self._albumgain_callback, album)
            )

    def _format_progress(self):
        if self.num_albums == 1:
            return ""
        else:
            self.current += 1
            return f" ({self.current}/{self.num_albums})"

    def _albumgain_callback(self, album, result=None, error=None):
        progress = self._format_progress()
        if error is None:
            for track in album.tracks:
                for file in track.files:
                    file.update()
                track.update()
            album.update()
            self.tagger.window.set_statusbar_message(
                'Successfully calculated ReplayGain for "%(album)s"%(progress)s.',
                {
                    'album': album.metadata['album'],
                    'progress': progress,
                }
            )
        else:
            self.tagger.window.set_statusbar_message(
                'Failed to calculate ReplayGain for "%(album)s"%(progress)s.',
                {
                    'album': album.metadata['album'],
                    'progress': progress,
                }
            )

class ReplayGain2OptionsPage(OptionsPage):

    NAME = "replaygain2"
    TITLE = "ReplayGain 2.0"
    PARENT = "plugins"

    options = [
        TextOption("setting", "rsgain_command", "rsgain"),
        BoolOption("setting", "album_tags", True),
        BoolOption("setting", "true_peak", False),
        BoolOption("setting", "reference_loudness", False),
        IntOption("setting", "target_loudness", -18),
        IntOption("setting", "clip_mode", CLIP_MODE_POSITIVE),
        IntOption("setting", "max_peak", 0),
        IntOption("setting", "opus_mode", OPUS_MODE_STANDARD),
        BoolOption("setting", "opus_m23", False)
    ]

    def __init__(self, parent=None):
        super(ReplayGain2OptionsPage, self).__init__(parent)
        self.ui = Ui_ReplayGain2OptionsPage()
        self.ui.setupUi(self)
        self.ui.clip_mode.addItems([
            "Disabled",
            "Enabled for positive gain values only",
            "Always enabled"
        ])
        self.ui.opus_mode.addItems([
            "Write standard ReplayGain tags",
            "Write R128_*_GAIN tags"
        ])
        self.ui.rsgain_command_browse.clicked.connect(self.rsgain_command_browse)

    def load(self):
        self.ui.rsgain_command.setText(self.config.setting["rsgain_command"])
        self.ui.album_tags.setChecked(self.config.setting["album_tags"])
        self.ui.true_peak.setChecked(self.config.setting["true_peak"])
        self.ui.reference_loudness.setChecked(self.config.setting["reference_loudness"])
        self.ui.target_loudness.setValue(self.config.setting["target_loudness"])
        self.ui.clip_mode.setCurrentIndex(self.config.setting["clip_mode"])
        self.ui.max_peak.setValue(self.config.setting["max_peak"])
        self.ui.opus_mode.setCurrentIndex(self.config.setting["opus_mode"])
        self.ui.opus_m23.setChecked(self.config.setting["opus_m23"])

    def save(self):
        self.config.setting["rsgain_command"] = self.ui.rsgain_command.text()
        self.config.setting["album_tags"] = self.ui.album_tags.isChecked()
        self.config.setting["true_peak"] = self.ui.true_peak.isChecked()
        self.config.setting["reference_loudness"] = self.ui.reference_loudness.isChecked()
        self.config.setting["target_loudness"] = self.ui.target_loudness.value()
        self.config.setting["clip_mode"] = self.ui.clip_mode.currentIndex()
        self.config.setting["max_peak"] = self.ui.max_peak.value()
        self.config.setting["opus_mode"] = self.ui.opus_mode.currentIndex()
        self.config.setting["opus_m23"] = self.ui.opus_m23.isChecked()

    def rsgain_command_browse(self):
        path, _filter = QFileDialog.getOpenFileName(self, "", self.ui.rsgain_command.text())
        if path:
            path = os.path.normpath(path)
            self.ui.rsgain_command.setText(path)


register_track_action(ScanTracks())
register_album_action(ScanAlbums())
register_options_page(ReplayGain2OptionsPage)
