# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024, 2026 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = 'Genre Mapper'
PLUGIN_AUTHOR = 'Bob Swift'
PLUGIN_DESCRIPTION = '''
This plugin provides the ability to standardize genres in the "genre"
tag by matching the genres as found to a standard genre as defined in
the genre replacement mapping configuration option. Once installed a
settings page will be added to Picard's options, which is where the
plugin is configured.
<br /><br />
Please see the <a href="https://github.com/rdswift/picard-plugins/blob/2.0_RDS_Plugins/plugins/genre_mapper/docs/README.md">user guide</a> on GitHub for more information.
'''
PLUGIN_VERSION = '0.8'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.6', '2.7', '2.8', '2.9', '2.10', '2.11']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

import re

from picard import (
    config,
    log,
)
from picard.metadata import (
    MULTI_VALUED_JOINER,
    register_track_metadata_processor,
)
from picard.plugin import PluginPriority
from picard.plugins.genre_mapper.ui_options_genre_mapper import (
    Ui_GenreMapperOptionsPage,
)

from picard.ui.options import (
    OptionsPage,
    register_options_page,
)


pairs_split = re.compile(r"\r\n|\n\r|\n").split

OPT_GENRE_SEPARATOR = 'join_genres'
OPT_MATCH_ENABLED = 'genre_mapper_enabled'
OPT_MATCH_PAIRS = 'genre_mapper_replacement_pairs'
OPT_MATCH_FIRST = 'genre_mapper_apply_first_match_only'
OPT_MATCH_REGEX = 'genre_mapper_use_regex'


def make_re(map_string: str, full_match: bool = True) -> str:
    """Convert a string with wildcards '*' and '?' to a regular expression.

    Args:
        map_string (str): String to convert
        full_match (bool, optional): Add the '^' and '$' bookends to the
        regular expression. Defaults to True.

    Returns:
        str: Regular expression.
    """
    re_string = str(map_string)

    # Escape the regular expression special characters
    re_string = re.escape(re_string)

    # Replace the escaped wildcard characters with their regular expression equivalents
    re_string = re_string.replace(r'\*', '.*').replace(r'\?', '.')

    # Clean up any accidental '.*.*' that may have been created by replacing multiple '*' characters
    re_string = re_string.replace('.*.*', '.*')

    # Clean up hard spaces that may have been escaped by re.escape()
    re_string = re_string.replace(r'\ ', ' ')

    # If full_match is True, add the '^' and '$' bookends to the regular expression
    if full_match:
        re_string = '^' + re_string + '$'

    return re_string


class GenreMappingPairs():
    pairs = []

    @classmethod
    def refresh(cls):
        log.debug("%s: Refreshing the genre replacement maps processing pairs using '%s' translation.",
            PLUGIN_NAME, 'RegEx' if config.Option.exists("setting", OPT_MATCH_REGEX) and config.setting[OPT_MATCH_REGEX] else 'Simple',)
        if not config.Option.exists("setting", OPT_MATCH_PAIRS):
            log.warning("%s: Unable to read the '%s' setting.", PLUGIN_NAME, OPT_MATCH_PAIRS,)
            return

        cls.pairs = []
        for pair in pairs_split(config.setting[OPT_MATCH_PAIRS]):
            if "=" not in pair:
                continue
            original, replacement = pair.split('=', 1)
            original = original.strip()
            if not original:
                continue
            replacement = replacement.strip()
            cls.pairs.append((original if config.setting[OPT_MATCH_REGEX] else make_re(original), replacement))
            log.debug('%s: Add genre mapping pair: "%s" = "%s"', PLUGIN_NAME, original, replacement,)
        if not cls.pairs:
            log.debug("%s: No genre replacement maps defined.", PLUGIN_NAME,)


class GenreMapperOptionsPage(OptionsPage):

    NAME = "genre_mapper"
    TITLE = "Genre Mapper"
    PARENT = "plugins"

    options = [
        config.TextOption("setting", OPT_MATCH_PAIRS, ''),
        config.BoolOption("setting", OPT_MATCH_FIRST, False),
        config.BoolOption("setting", OPT_MATCH_ENABLED, False),
        config.BoolOption("setting", OPT_MATCH_REGEX, False),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GenreMapperOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        # Enable external link
        self.ui.format_description.setOpenExternalLinks(True)

        self.ui.genre_mapper_replacement_pairs.setPlainText(config.setting[OPT_MATCH_PAIRS])
        self.ui.genre_mapper_first_match_only.setChecked(config.setting[OPT_MATCH_FIRST])
        self.ui.cb_enable_genre_mapping.setChecked(config.setting[OPT_MATCH_ENABLED])
        self.ui.cb_use_regex.setChecked(config.setting[OPT_MATCH_REGEX])

        self.ui.cb_enable_genre_mapping.stateChanged.connect(self._set_enabled_state)
        self._set_enabled_state()

    def save(self):
        config.setting[OPT_MATCH_PAIRS] = self.ui.genre_mapper_replacement_pairs.toPlainText()
        config.setting[OPT_MATCH_FIRST] = self.ui.genre_mapper_first_match_only.isChecked()
        config.setting[OPT_MATCH_ENABLED] = self.ui.cb_enable_genre_mapping.isChecked()
        config.setting[OPT_MATCH_REGEX] = self.ui.cb_use_regex.isChecked()

        GenreMappingPairs.refresh()

    def _set_enabled_state(self, *args):
        self.ui.gm_replacement_pairs.setEnabled(self.ui.cb_enable_genre_mapping.isChecked())


def track_genre_mapper(album, metadata, *args):
    if not config.setting[OPT_MATCH_ENABLED]:
        return
    if 'genre' not in metadata or not metadata['genre']:
        log.debug('%s: No genres found for: "%s"', PLUGIN_NAME, metadata['title'],)
        return
    genre_joiner = config.setting[OPT_GENRE_SEPARATOR] if config.setting[OPT_GENRE_SEPARATOR] else MULTI_VALUED_JOINER
    genres = set()
    metadata_genres = str(metadata['genre']).split(genre_joiner)
    for genre in metadata_genres:
        for (original, replacement) in GenreMappingPairs.pairs:
            try:
                if genre and re.search(original, genre, re.IGNORECASE):
                    genre = replacement
                    if config.setting[OPT_MATCH_FIRST]:
                        break
            except re.error:
                log.error('%s: Invalid regular expression ignored: "%s"', PLUGIN_NAME, original,)
        if genre:
            genres.add(genre.title())
    genres = sorted(genres)
    log.debug('%s: Genres updated from %s to %s', PLUGIN_NAME, metadata_genres, genres,)
    metadata['genre'] = genres


# Register the plugin to run at a LOW priority.
register_track_metadata_processor(track_genre_mapper, priority=PluginPriority.LOW)
register_options_page(GenreMapperOptionsPage)

GenreMappingPairs.refresh()
