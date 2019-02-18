# -*- coding: utf-8 -*-

# Changelog:
# [2015-09-15] Initial version
# [2017-11-24] Qt5, Python3 for Picard-plugins branch 2
# Dependancies:
# aubio, numpy
#

PLUGIN_NAME = "BPM Analyzer"
PLUGIN_AUTHOR = "Len Joubert, Sambhav Kothari, Philipp Wolfer"
PLUGIN_DESCRIPTION = """Calculate BPM for selected files and albums. Linux only version with dependancy on Aubio and Numpy"""
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"
PLUGIN_VERSION = "1.4"
PLUGIN_API_VERSIONS = ["2.0"]
# PLUGIN_INCOMPATIBLE_PLATFORMS = [
#    'win32', 'cygwyn', 'darwin', 'os2', 'os2emx', 'riscos', 'atheos']

from aubio import source, tempo
from numpy import median, diff
from collections import defaultdict
from functools import partial
from subprocess import check_call
from picard.album import Album, NatAlbum
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, thread
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption, IntOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.bpm.ui_options_bpm import Ui_BPMOptionsPage


bpm_slider_settings = {
    1: (44100, 1024, 512),
    2: (8000, 512, 128),
    3: (4000, 128, 64),
}


class FileBPM(BaseAction):
    NAME = N_("Calculate BPM...")

    def __init__(self):
        super().__init__()
        self._close = False
        self.tagger.aboutToQuit.connect(self._cleanup)

    def _cleanup(self):
        self._close = True

    def _add_file_to_queue(self, file):
        thread.run_task(
            partial(self._calculate_bpm, file),
            partial(self._calculate_bpm_callback, file))

    def callback(self, objs):
        for obj in objs:
            if isinstance(obj, Track):
                for file_ in obj.linked_files:
                    self._add_file_to_queue(file_)
            elif isinstance(obj, File):
                self._add_file_to_queue(obj)

    def _calculate_bpm(self, file):
        self.tagger.window.set_statusbar_message(
            N_('Calculating BPM for "%(filename)s"...'),
            {'filename': file.filename}
        )
        calculated_bpm = self._get_file_bpm(file.filename)
        # self.tagger.log.debug('%s' % (calculated_bpm))
        if self._close:
            return
        file.metadata["bpm"] = str(round(calculated_bpm, 1))
        file.update()

    def _calculate_bpm_callback(self, file, result=None, error=None):
        if not error:
            self.tagger.window.set_statusbar_message(
                N_('BPM for "%(filename)s" successfully calculated.'),
                {'filename': file.filename}
            )
        else:
            self.tagger.window.set_statusbar_message(
                N_('Could not calculate BPM for "%(filename)s".'),
                {'filename': file.filename}
            )

    def _get_file_bpm(self, path):
        """ Calculate the beats per minute (bpm) of a given file.
            path: path to the file
            buf_size    length of FFT
            hop_size    number of frames between two consecutive runs
            samplerate  sampling rate of the signal to analyze
        """

        samplerate, buf_size, hop_size = bpm_slider_settings[
            BPMOptionsPage.config.setting["bpm_slider_parameter"]]
        mediasource = source(path, samplerate, hop_size)
        samplerate = mediasource.samplerate
        beattracking = tempo("specdiff", buf_size, hop_size, samplerate)
        # List of beats, in samples
        beats = []
        # Total number of frames read
        total_frames = 0

        while True:
            if self._close:
                return
            samples, read = mediasource()
            is_beat = beattracking(samples)
            if is_beat:
                this_beat = beattracking.get_last_s()
                beats.append(this_beat)
            total_frames += read
            if read < hop_size:
                break

        # Convert to periods and to bpm
        bpms = 60. / diff(beats)
        return median(bpms)


class BPMOptionsPage(OptionsPage):

    NAME = "bpm"
    TITLE = "BPM"
    PARENT = "plugins"
    ACTIVE = True

    options = [
        IntOption("setting", "bpm_slider_parameter", 1)
    ]

    def __init__(self, parent=None):
        super(BPMOptionsPage, self).__init__(parent)
        self.ui = Ui_BPMOptionsPage()
        self.ui.setupUi(self)
        self.ui.slider_parameter.valueChanged.connect(self.update_parameters)
        self.update_parameters()

    def load(self):
        cfg = self.config.setting
        self.ui.slider_parameter.setValue(cfg["bpm_slider_parameter"])

    def save(self):
        cfg = self.config.setting
        cfg["bpm_slider_parameter"] = self.ui.slider_parameter.value()

    def update_parameters(self):
        val = self.ui.slider_parameter.value()
        samplerate, buf_size, hop_size = [str(v) for v in
                                          bpm_slider_settings[val]]
        self.ui.samplerate_value.setText(samplerate)
        self.ui.win_s_value.setText(buf_size)
        self.ui.hop_s_value.setText(hop_size)


register_file_action(FileBPM())
register_options_page(BPMOptionsPage)
