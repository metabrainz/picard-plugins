# -*- coding: utf-8 -*-

PLUGIN_NAME = u"Compatible TXXX frames"
PLUGIN_AUTHOR = u'Tungol'
PLUGIN_DESCRIPTION = """This plugin improves the compatibility of ID3 tags \
by using only a single value for TXXX frames. Multiple value TXXX frames \
technically don't comply with the ID3 specification."""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.0"]

from picard import config
from picard.formats import register_format
from picard.formats.id3 import MP3File, TrueAudioFile, DSFFile, AiffFile
from mutagen import id3


id3v24_join_with = '; '


def build_compliant_TXXX(self, encoding, desc, values):
    """Return a TXXX frame with only a single value.

    Use id3v23_join_with as the sperator if using id3v2.3, otherwise the value
    set in this plugin (default "; ").
    """
    if config.setting['write_id3v23']:
        sep = config.setting['id3v23_join_with']
    else:
        sep = id3v24_join_with
    joined_values = [sep.join(values)]
    return id3.TXXX(encoding=encoding, desc=desc, text=joined_values)


# I can't actually remove the original MP3File et al formats once they're
# registered. This depends on the name of the replacements sorting after the
# name of the originals, because picard.formats.guess_format picks the last
# item from a sorted list.


class MP3FileCompliant(MP3File):
    """Alternate MP3 format class which uses single-value TXXX frames."""

    build_TXXX = build_compliant_TXXX


class TrueAudioFileCompliant(TrueAudioFile):
    """Alternate TTA format class which uses single-value TXXX frames."""

    build_TXXX = build_compliant_TXXX


class DSFFileCompliant(DSFFile):
    """Alternate DSF format class which uses single-value TXXX frames."""

    build_TXXX = build_compliant_TXXX


class AiffFileCompliant(AiffFile):
    """Alternate AIFF format class which uses single-value TXXX frames."""

    build_TXXX = build_compliant_TXXX


register_format(MP3FileCompliant)
register_format(TrueAudioFileCompliant)
register_format(DSFFileCompliant)
register_format(AiffFileCompliant)
