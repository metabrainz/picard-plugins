# -*- coding: utf-8 -*-

# Changelog:
#   [2015-09-15] Initial version
# Dependancies:
#   aubio, numpy
#
# TODO:
# See how dependancies are installed automatically or added to Picard if
# not part of it already

PLUGIN_NAME = u"BPM Analyzer"
PLUGIN_AUTHOR = u"Len Joubert"
PLUGIN_DESCRIPTION = """Calculate BPM for selected files and albums."""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.10", "0.15", "0.16"]


from collections import defaultdict
from subprocess import check_call
from picard.album import Album, NatAlbum
from picard.track import Track
from picard.file import File
from picard.util import encode_filename, decode_filename, partial, thread
from picard.ui.options import register_options_page, OptionsPage
from picard.config import TextOption, IntOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.bpm.ui_options_bpm import Ui_BPMOptionsPage
from aubio import source, tempo
from numpy import median, diff

# the python to calculate bpm

bpm_slider_settings = {
    1: (44100, 1024, 512),
    2: (8000, 512, 128),
    3: (4000, 128, 64),
}


def get_file_bpm(self, path):
    """ Calculate the beats per minute (bpm) of a given file.
        path: path to the file
        buf_size    length of FFT
        hop_size    number of frames between two consecutive runs
        samplerate  sampling rate of the signal to analyze
    """

    samplerate, buf_size, hop_size = bpm_slider_settings[BPMOptionsPage.config.setting["bpm_slider_parameter"]]
    mediasource = source(path.encode("utf-8"), samplerate, hop_size)
    samplerate = mediasource.samplerate
    beattracking = tempo("specdiff", buf_size, hop_size, samplerate)
    # List of beats, in samples
    beats = []
    # Total number of frames read
    total_frames = 0

    while True:
        samples, read = mediasource()
        is_beat = beattracking(samples)
        if is_beat:
            this_beat = beattracking.get_last_s()
            beats.append(this_beat)
            # if o.get_confidence() > .2 and len(beats) > 2.:
            #    break
        total_frames += read
        if read < hop_size:
            break

    # Convert to periods and to bpm
    bpms = 60. / diff(beats)
    return median(bpms)


class FileBPM(BaseAction):
    NAME = N_("Calculate BPM...")

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
        calculated_bpm = get_file_bpm(self.tagger, file.filename)
        # self.tagger.log.debug('%s' % (calculated_bpm))
        file.metadata["bpm"] = str(round(calculated_bpm, 1))

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

    def load(self):
        cfg = self.config.setting
        self.ui.slider_parameter.setValue(cfg["bpm_slider_parameter"])

    def save(self):
        cfg = self.config.setting
        cfg["bpm_slider_parameter"] = self.ui.slider_parameter.value()

    def update_parameters(self):
        val = self.ui.slider_parameter.value()
        samplerate, buf_size, hop_size = [unicode(v) for v in
                                          bpm_slider_settings[val]]
        self.ui.samplerate_value.setText(samplerate)
        self.ui.win_s_value.setText(buf_size)
        self.ui.hop_s_value.setText(hop_size)


register_file_action(FileBPM())
register_options_page(BPMOptionsPage)
