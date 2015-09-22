# -*- coding: utf-8 -*-

# Changelog:
#   [2015-09-15] Initial version
# Dependancies: 
#   aubio, numpy
#
# TODO:
#   See how dependancies are isntalled automatically or added to Picard if not part of it already

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
from picard.config import TextOption
from picard.ui.itemviews import (BaseAction, register_file_action,
                                 register_album_action)
from picard.plugins.bpm.ui_options_bpm import Ui_BPMOptionsPage
from aubio import source, tempo
from numpy import median, diff

# the python to calculate bpm
# todo: add the correct way to pass options from options page to it

def get_file_bpm(self, path):
    """ Calculate the beats per minute (bpm) of a given file.
        path: path to the file
    """

    samplerate = int(float(BMPOptionsPage.config.setting["bpm_samplerate_parameter"]))
    win_s = int(float(BMPOptionsPage.config.setting["bpm_win_s_parameter"]))
    hop_s = int(float(BMPOptionsPage.config.setting["bpm_hop_s_parameter"]))
    
    #    self.tagger.log.debug('%s' % (win_s))
    
    s = source(path, samplerate, hop_s)
    samplerate = s.samplerate
    o = tempo("specdiff", win_s, hop_s, samplerate)
    # List of beats, in samples
    beats = []
    # Total number of frames read
    total_frames = 0

    while True:
        samples, read = s()
        is_beat = o(samples)
        if is_beat:
            this_beat = o.get_last_s()
            beats.append(this_beat)
            #if o.get_confidence() > .2 and len(beats) > 2.:
            #    break
        total_frames += read
        if read < hop_s:
            break

    # Convert to periods and to bpm 
    bpms = 60./diff(beats)
    b = median(bpms)
    return b

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

class BMPOptionsPage(OptionsPage):

    NAME = "bpm"
    TITLE = "BPM"
    PARENT = "plugins"

    options = [
        TextOption("setting", "bpm_win_s_parameter", "1024"),
        TextOption("setting", "bpm_hop_s_parameter", "512"),
        TextOption("setting", "bpm_samplerate_parameter", "44100"),
    ]

    def __init__(self, parent=None):
        super(BMPOptionsPage, self).__init__(parent)
        self.ui = Ui_BPMOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.win_s_parameter.setText(self.config.setting["bpm_win_s_parameter"])
        self.ui.hop_s_parameter.setText(self.config.setting["bpm_hop_s_parameter"])
        self.ui.samplerate_parameter.setText(self.config.setting["bpm_samplerate_parameter"])

    def save(self):
        self.config.setting["bpm_win_s_parameter"] = unicode(self.ui.win_s_parameter.text())
        self.config.setting["bpm_hop_s_parameter"] = unicode(self.ui.hop_s_parameter.text())
        self.config.setting["bpm_samplerate_parameter"] = unicode(self.ui.samplerate_parameter.text())

register_file_action(FileBPM())
register_options_page(BMPOptionsPage)
