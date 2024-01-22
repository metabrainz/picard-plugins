# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Giorgio Fontanive (twodoorcoupe)
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

PLUGIN_NAME = "Enhanced Titles"
PLUGIN_AUTHOR = "Giorgio Fontanive"
PLUGIN_DESCRIPTION = """
This plugin sets the albumsort and titlesort tags. It also provides the script
functions $swapprefix_lang, $delprefix_lang and $title_lang. The languages
included at the moment are English, Spanish, Italian, German, French and Portuguese.

The functions do the same thing as their original counterparts, but take
multiple languages as parameters. If no languages are provided, all the available ones are
included. Languages are provided with ISO 639-3 codes: eng, spa, ita, fra, deu, por.

Tagging and checking aliases can be disabled in the plugin's options page, found
under "plugins". Checking aliases will slow down processing.
"""
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["2.10"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log, config
from picard.plugin import PluginPriority
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.script import register_script_function
from picard.script.functions import func_swapprefix, func_delprefix
from picard.webservice.api_helpers import MBAPIHelper

from picard.ui.options import OptionsPage, register_options_page
from .ui_options_enhanced_titles import Ui_EnhancedTitlesOptions

from functools import partial
import re

# Options.
KEEP_ALLCAPS = "et_keep_allcaps"
ENABLE_TAGGING = "et_enable_tagging"
CHECK_ALBUM = "et_check_album_aliases"
CHECK_TRACK = "et_check_track_aliases"

_articles = {
    "eng" : ["the", "a", "an"],
    "spa" : ["el", "los", "la", "las", "lo", "un", "unos", "una", "unas"],
    "ita" : ["il", "l'", "la", "i", "gli", "le", "un", "uno", "una", "un'"],
    "fra" : ["le", "la", "les", "un", "une", "des", "l'"],
    "deu" : ["der", "den", "die", "das", "dem", "des", "den"],
    "por" : ["o", "os", "a", "as", "um", "uns", "uma", "umas"]
}
_articles[""] = [value for values in _articles.values() for value in values]

# Prepositions and conjunctions with 3 letters or less.
_other_minor_words = {
    "eng" : ["so", "yet", "as", "at", "by", "for", "in", "of", "off", "on", "per",
            "to", "up", "via", "and", "as", "but", "for", "if", "nor", "or"],
    "spa" : ["mas", "que", "en", "con", "por", "de", "y", "e", "o", "u", "si", "ni"],
    "ita" : ["di", "a", "da", "in", "con", "su", "per", "tra", "fra", "e", "o", "ma", "se"],
    "fra" : ["à", "de", "en", "par", "sur", "et", "ou", "que", "si"],
    "deu" : ["bis", "für", "um", "an", "auf", "in", "vor", "aus", "bei", "mit",
            "von", "zu", "la", "so", "daß", "als", "ob", "ehe"],
    "por" : ["dem", "em", "por", "ao", "à", "aos", "às", "do", "da", "dos", "das",
            "no", "na", "nos", "nas", "num", "dum", "e", "mas", "até", "em", "ou",
            "que", "se", "por"]
}
_other_minor_words[""] = [value for values in _other_minor_words.values() for value in values]


class ReleaseGroupHelper(MBAPIHelper):
    """API Helper to retreive release group information.
    """

    def get_release_group_by_id(self, release_id, handler, inc = None):
        """Gets the information for a release group.
        """
        return self._get_by_id("release-group", release_id, handler, inc)


class SortTagger:
    """Sets the titlesort and albumsort tags.

    First, it checks if there is already a sort name available in one of the
    aliases. If it does not find any, it swaps the prefix if there is one in
    the title.
    """

    def _select_alias(self, aliases, name):
        """Selects the first alias where the names match and the sort name is
        different.

        Args:
            aliases (list): One dictionary for each alias available.
            name (str): Title of the album/track.

        Returns:
            (str): The sort name of the first useful alias it finds. None if
                   none are found.

        For example, "The Beatles" has alias "Le Double Blanc" with sort name
        "Double Blanc, Le", so it's not considered. But it also has alias
        "The Beatles" with sort name "Beatles, The", so this one is chosen.
        Another example, "The Continuing Story of Bungalow Bill" has an alias
        with the sort name equal to the title, this is not considered because
        it makes more sense to swap the prefix.
        """
        for alias in aliases:
            sortname = alias["sort-name"]
            if (alias["name"].casefold() == name.casefold() and
                    not sortname.casefold() == name.casefold()):
                log.info("Enhanced Titles: sort name found for \"" + name + "\", \"" + sortname + "\".")
                return sortname
        log.info("Enhanced Titles: no proper sort name found for \"" + name + "\".")
        return None

    def _response_handler(self, document, reply, error, metadata = None, field = None):
        """Handles the response from MusicBrainz.

        Args:
            metadata (MetaData): The object that needs to be updated.
            field (str): Either "title" or "album", depending on what is being
                         updated.
        """
        sortname = ""
        try:
            if document:
                if error:
                    log.error("Enhanced Titles: information retrieval error.")
                if document["aliases"]:
                    sortname = self._select_alias(document["aliases"], metadata[field])
                else:
                    log.info("Enhanced Titles: no aliases found for \"" + metadata[field] + "\".")
        finally:
            if sortname:
                sortfield = field + "sort"
                metadata[sortfield] = sortname
            else:
                self._swapprefix(metadata, field)

    def _swapprefix(self, metadata, field):
        """Swaps the prefix of the title based on the album/track language."

        If no language information is found, then it uses all languages available.
        Otherwise, if none of the languages are available, it just copies the title.
        Otherwise it uses exclusively the languages that are also available.
        """
        sortfield = field + "sort"
        languages = [metadata["language"], metadata["_releaselanguage"]]
        languages = [language for language in languages if language]
        if not languages:
            prefixes = _articles[""] + [article.capitalize() for article in _articles[""]]
            metadata[sortfield] = func_swapprefix(None, metadata[field], *prefixes)
        else:
            languages = [language for language in languages if language in _articles.keys()]
            if not languages:
                metadata[sortfield] = metadata[field]
            else:
                prefixes = lang_functions.find_prefixes(languages)
                metadata[sortfield] = func_swapprefix(None, metadata[field], *prefixes)

    def set_track_titlesort(self, album, metadata, track, release):
        """Sets the track's titlesort field.
        """
        if config.setting[ENABLE_TAGGING]:
            handler = partial(self._response_handler, metadata = metadata, field = "title")
            if config.setting[CHECK_TRACK]:
                MBAPIHelper(album.tagger.webservice).get_track_by_id(
                    metadata["musicbrainz_recordingid"],
                    handler,
                    inc = ["aliases"]
                )
            else:
                self._swapprefix(metadata, "title")

    def set_album_titlesort(self, album, metadata, release):
        """Sets the album's albumsort field.
        """
        if config.setting[ENABLE_TAGGING]:
            handler = partial(self._response_handler, metadata = metadata, field = "album")
            if config.setting[CHECK_ALBUM]:
                ReleaseGroupHelper(album.tagger.webservice).get_release_group_by_id(
                    metadata["musicbrainz_releasegroupid"],
                    handler,
                    inc = ["aliases"]
                )
            else:
                self._swapprefix(metadata, "album")


class LangFunctions:
    """Provides scripting functions swapprefix_lang, delprefix_lang, and title_lang.

    Combinations of languages and their prefixes/minor words are stored after
    they're used at least once.
    """

    prefixes_lists = {}
    titles_lists = {}

    def _format_languages(self, languages):
        languages = [lang.lower()[:3] for lang in languages]
        languages = [lang for lang in languages if lang in _articles.keys()]
        return tuple(languages)

    def _create_prefixes_list(self, languages = None, is_title = False):
        """Creates a list of all the prefixes or minor words for all the given languages.

        Args:
            languages (list): All the languages to be considered.
            is_title (bool): If true, only articles are included, with a lower case
                             and a capitalized copy for each. This is because the
                             swapprefix and delprefix functions are case sensitive.
                             If false, also prepositions and conjunctions are included,
                             all in lowercase.

        Returns:
            (set): The set of prefixes or minor words.

        The available languages are saved with ISO 639-3 codes.
        """
        prefixes = set()
        for language in languages:
            prefixes.update(_articles[language])
            if is_title:
                prefixes.update(_other_minor_words[language])
            else:
                prefixes.update([article.capitalize() for article in _articles[language]])
        return prefixes

    def _title_case(self, text, lower_case_words):
        """Returns the text in titlecase.

        If a word has an apostrophe and the segment to its left is an article,
        it capitalizes only the word on the right. Otherwise it capitalizes
        only the word on the left.
        For example, "let's groove" becomes "Let's Groove", but "voglio l'anima"
        becomes "Voglio l'Anima".
        """
        new_text = []
        words = re.split(r"([\w']+)", text.strip().lower().replace("’", "'"))
        words = [word for word in words if word]
        for word in words:
            if "'" in word: # Apply the rule described above
                split = word.split("'")
                if split[0] + "'" in lower_case_words:
                    split[1] = split[1].capitalize()
                else:
                    split[0] = split[0].capitalize()
                word = "'".join(split)
            elif not word in lower_case_words:
                word = word.capitalize()
            new_text.append(word)
        if new_text:
            new_text[0] = new_text[0].capitalize()
            return "".join(new_text)
        else:
            return ""

    def find_prefixes(self, languages):
        """Returns the list of prefixes for the given languages.

        If the same combination was previously used, it finds the values stored
        to avoid recreating the same list twice.
        """
        if not languages or "" in languages:
            return set(_articles[""] + [article.capitalize() for article in _articles[""]])
        combination = self._format_languages(languages)
        if combination in self.prefixes_lists:
            return self.prefixes_lists[combination]
        prefixes = self._create_prefixes_list(combination)
        self.prefixes_lists[combination] = prefixes
        return prefixes

    def find_minor_words(self, languages):
        """Returns the list of minor words for the given languages.

        If the same combination was previously used, it finds the values stored
        to avoid recreating the same list twice.
        """
        if not languages or "" in languages:
            return set(_articles[""] + _other_minor_words[""])
        combination = self._format_languages(languages)
        if combination in self.titles_lists:
            return self.titles_lists[combination]
        minor_words = self._create_prefixes_list(combination, True)
        self.titles_lists[combination] = minor_words
        return minor_words

    swapprefix_lang_documentation = N_(
        """`$swapprefix_lang(text,language1,language2,...)`

    Moves the prefix to the end of the text. It uses a list prefixes
    taken from the specified languages.
    Multiple languages can be added as seperate parameters.
    If none are provided, it uses all the available ones.
        """)
    def swapprefix_lang(self, parser, text, *languages):
        """
        >>> lf = LangFunctions()
        >>> lf.swapprefix_lang(None, "The prefix is swapped")
        'prefix is swapped, The'
        >>> lf.swapprefix_lang(None, "the is swapped also in lower case")
        'is swapped also in lower case, the'
        >>> lf.swapprefix_lang(None, "the prefix is not in Spanish", "spa")
        'the prefix is not in Spanish'
        >>> lf.swapprefix_lang(None, "Il prefisso è scambiato", "ita")
        'prefisso è scambiato, Il'
        >>> lf.swapprefix_lang(None, "the-prefix-is-not-swapped")
        'the-prefix-is-not-swapped'
        >>> lf.swapprefix_lang(None, "the")
        'the'
        """
        prefixes = self.find_prefixes(languages)
        return func_swapprefix(parser, text, *prefixes) if text else ""

    delprefix_lang_documentation = N_(
        """`$delprefix_lang(text,language1,language2,...)`

    Deletes the prefix from the text. It uses a list prefixes
    taken from the specified languages.
    Multiple languages can be added as seperate parameters.
    If none are provided, it uses all the available ones.
        """)
    def delprefix_lang(self, parser, text, *languages):
        """
        >>> lf = LangFunctions()
        >>> lf.delprefix_lang(None, "The prefix is deleted")
        'prefix is deleted'
        >>> lf.delprefix_lang(None, "the is deleted also in lower case")
        'is deleted also in lower case'
        >>> lf.delprefix_lang(None, "the prefix is not in Spanish", "spa")
        'the prefix is not in Spanish'
        >>> lf.delprefix_lang(None, "Il prefisso è eliminato", "ita")
        'prefisso è eliminato'
        >>> lf.delprefix_lang(None, "the-prefix-is-not-deleted")
        'the-prefix-is-not-deleted'
        >>> lf.delprefix_lang(None, "the")
        'the'
        """
        prefixes = self.find_prefixes(languages)
        return func_delprefix(parser, text, *prefixes) if text else ""

    title_lang_documentation = N_(
        """`$title_lang(text,language1,language2,...)`

    Makes the text title case based on the minor words of the specified languages.
    Multiple languages can be added as seperate parameters.
    If none are provided, it uses all the available ones.
        """)
    def title_lang(self, parser, text, *languages):
        """
        >>> lf = LangFunctions()
        >>> lf.title_lang(None, "title case")
        'Title Case'
        >>> lf.title_lang(None, "prepositions and/or conjunctions")
        'Prepositions and/or Conjunctions'
        >>> lf.title_lang(None, "(random-punctuation/and.symbols@")
        '(Random-Punctuation/and.Symbols@'
        >>> lf.title_lang(None, "only in english: and, or, but...", "eng")
        'Only in English: and, or, but...'
        >>> lf.title_lang(None, "only in spanish: and, or, but...", "spa")
        'Only In Spanish: And, Or, But...'
        >>> lf.title_lang(None, "Also in other languages, con altre lingue", "eng", "ita")
        'Also in Other Languages, con Altre Lingue'
        >>> lf.title_lang(None, "with no valid language", "aaa")
        'With No Valid Language'
        >>> lf.title_lang(None, "let's groove")
        "Let's Groove"
        >>> lf.title_lang(None, "voglio l'anima")
        "Voglio l'Anima"
        >>> lf.title_lang(None, "casiopea, カシオペア")
        'Casiopea, カシオペア'
        """
        if text.upper() == text and config.setting[KEEP_ALLCAPS]:
            return text
        minor_words = self.find_minor_words(languages)
        return self._title_case(text, minor_words) if text else ""


class EnhancedTitlesOptions(OptionsPage):
    """Options page found under the "plugins" page.
    """

    NAME = "enhanced_titles"
    TITLE = "Enhanced Titles"
    PARENT = "plugins"

    options = [
        config.BoolOption("setting", KEEP_ALLCAPS, False),
        config.BoolOption("setting", ENABLE_TAGGING, True),
        config.BoolOption("setting", CHECK_ALBUM, True),
        config.BoolOption("setting", CHECK_TRACK, False),
    ]

    def __init__(self, parent = None):
        super(EnhancedTitlesOptions, self).__init__(parent)
        self.ui = Ui_EnhancedTitlesOptions()
        self.ui.setupUi(self)

    def load(self):
        self.ui.check_allcaps.setChecked(config.setting[KEEP_ALLCAPS])
        self.ui.check_tagging.setChecked(config.setting[ENABLE_TAGGING])
        self.ui.check_album_aliases.setChecked(config.setting[CHECK_ALBUM])
        self.ui.check_track_aliases.setChecked(config.setting[CHECK_TRACK])

    def save(self):
        config.setting[KEEP_ALLCAPS] = self.ui.check_allcaps.isChecked()
        config.setting[ENABLE_TAGGING] = self.ui.check_tagging.isChecked()
        config.setting[CHECK_ALBUM] = self.ui.check_album_aliases.isChecked()
        config.setting[CHECK_TRACK] = self.ui.check_track_aliases.isChecked()


sort_tagger = SortTagger()
lang_functions = LangFunctions()
register_track_metadata_processor(sort_tagger.set_track_titlesort, priority = PluginPriority.LOW)
register_album_metadata_processor(sort_tagger.set_album_titlesort, priority = PluginPriority.LOW)
register_script_function(lang_functions.swapprefix_lang, check_argcount = False, documentation = lang_functions.swapprefix_lang_documentation)
register_script_function(lang_functions.delprefix_lang, check_argcount = False, documentation = lang_functions.delprefix_lang_documentation)
register_script_function(lang_functions.title_lang, check_argcount = False, documentation = lang_functions.title_lang_documentation)
register_options_page(EnhancedTitlesOptions)
