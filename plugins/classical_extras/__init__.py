# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Classical Extras'
PLUGIN_AUTHOR = u'Mark Evens'
PLUGIN_DESCRIPTION = u'''This plugin contains 3 classes:

I. ("EXTRA ARTISTS") Create sorted fields for all performers. Creates a number of variables with alternative values for "artists" and "artist".
Creates an ensemble variable for all ensemble-type performers.
Also creates matching sort fields for artist and artists.
Additionally create tags for artist types which are not normally created in Picard - particularly for classical music (notably instrument arrangers).

II. ("WORK PARTS") Create tags for the hierarchy of works which contain a given track recording - particularly for classical music'
Variables provided for each work level, with implied part names
Mixed metadata provided including work and title elements

III. ("OPTIONS") Allows the user to set various options including what tags will be written (otherwise the classes above will just write outputs to "hidden variables")

See Readme file for full details.
'''
PLUGIN_VERSION = '0.8.2'
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page, OptionsPage
from picard.plugins.classical_extras.ui_options_classical_extras import Ui_ClassicalExtrasOptionsPage
from picard import config, log
from picard.config import ConfigSection, BoolOption, IntOption, TextOption
from picard.util import LockableObject
from picard.track import Track
from picard.album import Album
from picard.webservice import XmlNode  # note that in 2.0 this will change to picard.util.xml
from picard.metadata import register_track_metadata_processor, Metadata
from functools import partial
import collections
import re
import unicodedata as ud
import traceback
import json
import copy

##########################
# MODULE-WIDE COMPONENTS #
##########################

# CONSTANTS

prefixes = ['the', 'a', 'an', 'le', 'la', 'les', 'los', 'il']


# OPTIONS

def plugin_options(type):
    # this function contains all the options data in one place - to prevent multiple repetitions elsewhere

    # artists options (excluding tag mapping lines)
    artists_options = [
        {'option': 'classical_extra_artists',
         'name': 'run extra artists',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_orchestras',
         'name': 'orchestra strings',
         'type': 'Text',
         'default': 'orchestra, philharmonic, philharmonica, philharmoniker, musicians, academy, symphony, orkester'
         },
        {'option': 'cea_choirs',
         'name': 'choir strings',
         'type': 'Text',
         'default': 'choir, choir vocals, chorus, singers, domchors, domspatzen, koor'
         },
        {'option': 'cea_groups',
         'name': 'group strings',
         'type': 'Text',
         'default': 'ensemble, band, group, trio, quartet, quintet, sextet, septet, octet, chamber, consort, players, '
                    'les ,the , quartett'
         },
        {'option': 'cea_composer_album',
         'name': 'Album prefix',
         # 'value': 'Composer', # Can't use 'value' if there is only one option, otherwise False will revert to default
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_blank_tag',
         'name': 'Tags to blank',
         'type': 'Text',
         'default': 'artist, artistsort'
         },
        {'option': 'cea_blank_tag_2',
         'name': 'Tags to blank 2',
         'type': 'Text',
         'default': 'performer:orchestra, performer:choir, performer:choir vocals'
         },
        {'option': 'cea_keep',
         'name': 'File tags to keep',
         'type': 'Text',
         'default': 'is_classical'
         },
        {'option': 'cea_arrangers',
         'name': 'include arrangers',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_cyrillic',
         'name': 'fix cyrillic',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_genres',
         'name': 'infer work types',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_credited',
         'name': 'use credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_track_credited',
         'name': 'use track credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_no_solo',
         'name': 'exclude solo',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_chorusmaster',
         'name': 'chorusmaster',
         'type': 'Text',
         'default': 'choirmaster'
         },
        {'option': 'cea_orchestrator',
         'name': 'orchestrator',
         'type': 'Text',
         'default': 'orch.'
         },
        {'option': 'cea_concertmaster',
         'name': 'concertmaster',
         'type': 'Text',
         'default': 'leader'
         },
        {'option': 'cea_tag_sort',
         'name': 'populate sort tags',
         'type': 'Boolean',
         'default': True
         }
    ]

    #  tag mapping lines
    default_list = [
        ('album_soloists, album_conductors, album_ensembles', 'artist, artists', True),
        ('soloists, conductors, ensembles, album_composers, composers', 'artist, artists', True),
        ('soloists', 'soloists, trackartist', False),
        ('ensembles', 'ensembles', False),
        ('ensemble_names', 'band', False),
        ('release', 'release_name', False),
        ('work_type', 'genre', False),
        ('artist', 'artists', False),
        ('artist', 'artist', True),
        ('artist', 'composer', True),
        ('\(Arr.) + arrangers, \(Orch.) + orchestrators', 'composer', False)
    ]
    tag_options = []
    for i in range(0, 16):
        if i < len(default_list):
            default_source = default_list[i][0]
            default_tag = default_list[i][1]
            default_cond = default_list[i][2]
        tag_options.append({'option': 'cea_source_' + str(i + 1),
                            'name': 'line ' + str(i + 1) + '_source',
                            'type': 'Combo',
                            'default': default_source
                            })
        tag_options.append({'option': 'cea_tag_' + str(i + 1),
                            'name': 'line ' + str(i + 1) + '_tag',
                            'type': 'Text',
                            'default': default_tag
                            })
        tag_options.append({'option': 'cea_cond_' + str(i + 1),
                            'name': 'line ' + str(i + 1) + '_conditional',
                            'type': 'Boolean',
                            'default': default_cond
                            })

    # workparts options
    workparts_options = [
        {'option': 'classical_work_parts',
         'name': 'run work parts',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_collections',
         'name': 'include collection relations',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_proximity',
         'name': 'in-string proximity trigger',
         'type': 'Integer',
         'default': 2
         },
        {'option': 'cwp_end_proximity',
         'name': 'end-string proximity trigger',
         'type': 'Integer',
         'default': 1
         },
        {'option': 'cwp_granularity',
         'name': 'work-splitting',
         'type': 'Integer',
         'default': 1
         },
        {'option': 'cwp_substring_match',
         'name': 'similarity threshold',
         'type': 'Integer',
         'default': 66
         },
        {'option': 'cwp_removewords',
         'name': 'ignore prefixes',
         'type': 'Text',
         'default': ' part, act, scene, movement, movt, no., no , n., n , nr., nr , book , the , a , la , le , un ,'
                    ' une , el , il , (part), tableau, from '
         },
        {'option': 'cwp_synonyms',
         'name': 'synonyms',
         'type': 'Text',
         'default': '(1, one) / (2, two) / (3, three) / (&, and)'
         },
        {'option': 'cwp_replacements',
         'name': 'replacements',
         'type': 'Text',
         'default': '(words to be replaced, replacement words) / (please blank me, ) / (etc, etc)'
         },
        {'option': 'cwp_titles',
         'name': 'Style',
         'value': 'Titles',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_works',
         'name': 'Style',
         'value': 'Works',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_extended',
         'name': 'Style',
         'value': 'Extended',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_hierarchical_works',
         'name': 'Work source',
         'value': 'Hierarchy',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_level0_works',
         'name': 'Work source',
         'value': 'Level_0',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_movt_tag_inc',
         'name': 'movement tag inc num',
         'type': 'Text',
         'default': 'part, movement name, subtitle'
         },
        {'option': 'cwp_movt_tag_exc',
         'name': 'movement tag exc num',
         'type': 'Text',
         'default': 'movement'
         },
        {'option': 'cwp_movt_tag_inc1',
         'name': '1-level movement tag inc num',
         'type': 'Text',
         'default': ''
         },
        {'option': 'cwp_movt_tag_exc1',
         'name': '1-level movement tag exc num',
         'type': 'Text',
         'default': ''
         },
        {'option': 'cwp_movt_no_tag',
         'name': 'movement num tag',
         'type': 'Text',
         'default': 'movement_no'
         },
        {'option': 'cwp_work_tag_multi',
         'name': 'multi-level work tag',
         'type': 'Text',
         'default': 'groupheading, work'
         },
        {'option': 'cwp_work_tag_single',
         'name': 'single level work tag',
         'type': 'Text',
         'default': ''
         },
        {'option': 'cwp_top_tag',
         'name': 'top level work tag',
         'type': 'Text',
         'default': 'top_work, style, grouping'
         },
        {'option': 'cwp_multi_work_sep',
         'name': 'multi-level work separator',
         'type': 'Combo',
         'default': ':'
         },
        {'option': 'cwp_single_work_sep',
         'name': 'single level work separator',
         'type': 'Combo',
         'default': ':'
         },
        {'option': 'cwp_movt_no_sep',
         'name': 'movement number separator',
         'type': 'Combo',
         'default': '.'
         },
        {'option': 'cwp_partial',
         'name': 'show partial recordings',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_partial_text',
         'name': 'partial text',
         'type': 'Text',
         'default': '(part)'
         },
        {'option': 'cwp_arrangements',
         'name': 'include arrangement of',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_arrangements_text',
         'name': 'arrangements text',
         'type': 'Text',
         'default': 'Arrangement:'
         },
        {'option': 'cwp_medley',
         'name': 'list medleys',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_medley_text',
         'name': 'medley text',
         'type': 'Text',
         'default': 'Medley of:'
         }
    ]

    # other options (not saved in tags)
    other_options = [
        {'option': 'use_cache',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_use_sk',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_write_sk',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_retries',
         'type': 'Integer',
         'default': 6
         },
        {'option': 'log_error',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'log_warning',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'log_debug',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'log_info',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'ce_version_tag',
         'type': 'Text',
         'default': 'stamp'
         },
        {'option': 'cea_options_tag',
         'type': 'Text',
         'default': 'comment'
         },
        {'option': 'cwp_options_tag',
         'type': 'Text',
         'default': 'comment'
         },
        {'option': 'cea_override',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_override',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'ce_options_overwrite',
         'type': 'Boolean',
         'default': False}
    ]

    if type == 'artists':
        return artists_options
    elif type == 'tag':
        return tag_options
    elif type == 'workparts':
        return workparts_options
    elif type == 'other':
        return other_options
    else:
        return None


def option_settings(config_settings):
    options = {}
    for option in plugin_options('artists') + plugin_options('tag') \
            + plugin_options('workparts') + plugin_options('other'):
        options[option['option']] = copy.deepcopy(config_settings[option['option']])
    return options


# Non-Latin character processing
latin_letters = {}


def is_latin(uchr):
    try:
        return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(uchr, 'LATIN' in ud.name(uchr))


def only_roman_chars(unistr):
    return all(is_latin(uchr)
               for uchr in unistr
               if uchr.isalpha())


def get_roman(string):
    capital_letters = {
        u'А': u'A',
        u'Б': u'B',
        u'В': u'V',
        u'Г': u'G',
        u'Д': u'D',
        u'Е': u'E',
        u'Ё': u'E',
        u'Ж': u'Zh',
        u'З': u'Z',
        u'И': u'I',
        u'Й': u'Y',
        u'К': u'K',
        u'Л': u'L',
        u'М': u'M',
        u'Н': u'N',
        u'О': u'O',
        u'П': u'P',
        u'Р': u'R',
        u'С': u'S',
        u'Т': u'T',
        u'У': u'U',
        u'Ф': u'F',
        u'Х': u'H',
        u'Ц': u'Ts',
        u'Ч': u'Ch',
        u'Ш': u'Sh',
        u'Щ': u'Sch',
        u'Ъ': u'',
        u'Ы': u'Y',
        u'Ь': u'',
        u'Э': u'E',
        u'Ю': u'Yu',
        u'Я': u'Ya'
    }
    lower_case_letters = {
        u'а': u'a',
        u'б': u'b',
        u'в': u'v',
        u'г': u'g',
        u'д': u'd',
        u'е': u'e',
        u'ё': u'e',
        u'ж': u'zh',
        u'з': u'z',
        u'и': u'i',
        u'й': u'y',
        u'к': u'k',
        u'л': u'l',
        u'м': u'm',
        u'н': u'n',
        u'о': u'o',
        u'п': u'p',
        u'р': u'r',
        u'с': u's',
        u'т': u't',
        u'у': u'u',
        u'ф': u'f',
        u'х': u'h',
        u'ц': u'ts',
        u'ч': u'ch',
        u'ш': u'sh',
        u'щ': u'sch',
        u'ъ': u'',
        u'ы': u'y',
        u'ь': u'',
        u'э': u'e',
        u'ю': u'yu',
        u'я': u'ya'
    }
    translit_string = ""
    for index, char in enumerate(string):
        if char in lower_case_letters.keys():
            char = lower_case_letters[char]
        elif char in capital_letters.keys():
            char = capital_letters[char]
            if len(string) > index + 1:
                if string[index + 1] not in lower_case_letters.keys():
                    char = char.upper()
            else:
                char = char.upper()
        translit_string += char
    # fix multi-chars
    translit_string = translit_string.replace('ks', 'x').replace('iy ', 'i ')
    return translit_string


def remove_middle(performer):
    plist = performer.split()
    if len(plist) == 3:
        # to remove middle names of Russian composers
        return plist[0] + ' ' + plist[2]
    else:
        return performer


# Sorting etc.


def sort_field(performer):
    sorter = re.compile(r'(.*)\s(.*)$')
    match = sorter.search(performer)
    if match:
        return match.group(2) + ", " + match.group(1)
    else:
        return performer


def unsort(performer):
    unsorter = re.compile(r'^(.+),\s(.*)')
    match = unsorter.search(performer)
    if match:
        return match.group(2).strip() + " " + match.group(1)
    else:
        return performer


def stripsir(performer):
    sir = re.compile(r'^(Sir|Maestro)\b\s*(.*)', re.IGNORECASE)
    match = sir.search(performer)
    if match:
        return match.group(2).strip()
    else:
        return performer


def swap_prefix(performer):
    prefix = '|'.join(prefixes)
    swap = re.compile(r'^(' + prefix + r')\b\s*(.*)', re.IGNORECASE)
    match = swap.search(performer)
    if match:
        return match.group(2) + ", " + match.group(1)
    else:
        return performer


def replace_roman_numerals(s):
    # replaces roman numerals include in s, where followed by punctuation, by digits
    p = re.compile(
        r'\b(M{0,4}(CM|CD|D?)?C{0,3}(XC|XL|L?)?X{0,3}(IX|IV|V?)?I{0,3})\b(\.|:|,|;|$)',
        #  was r'(^|\s)(\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b)(\W|\s|$)',
        re.IGNORECASE | re.UNICODE)  # Matches Roman numerals (+ ensure non-Latin chars treated as word chars)
    romans = p.findall(s)
    for roman in romans:
        if roman[0]:
            numerals = str(roman[0])
            digits = str(from_roman(numerals))
            to_replace = roman[0] + r'(\.|:|,|;|$)'
            s = re.sub(to_replace, digits, s)
    return s


def from_roman(s):
    romanNumeralMap = (('M', 1000),
                       ('CM', 900),
                       ('D', 500),
                       ('CD', 400),
                       ('C', 100),
                       ('XC', 90),
                       ('L', 50),
                       ('XL', 40),
                       ('X', 10),
                       ('IX', 9),
                       ('V', 5),
                       ('IV', 4),
                       ('I', 1))
    result = 0
    index = 0
    for numeral, integer in romanNumeralMap:
        while s[index:index + len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result


def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]


# maxstart must be >= minstart. If they are equal then the start point is
# fixed.
def longest_common_sequence(list1, list2, minstart=0, maxstart=0):
    if maxstart < minstart:
        return (None, 0)
    min_len = min(len(list1), len(list2))
    longest = 0
    seq = None
    maxstart = min(maxstart, min_len) + 1
    for k in range(minstart, maxstart):
        for i in range(k, min_len + 1):
            if list1[k:i] == list2[k:i] and i - k > longest:
                longest = i - k
                seq = list1[k:i]
    return {'sequence': seq, 'length': longest}


def map_tags(options, tm):
    # ERROR = options["log_error"] # Not currently used
    # WARNING = options["log_warning"] # Not currently used
    DEBUG = options["log_debug"]
    INFO = options["log_info"]
    if DEBUG:
        log.debug('In map_tags, checking readiness...')
    if (options['classical_extra_artists'] and '~cea_artists_complete' not in tm) or (
                options['classical_work_parts'] and '~cea_works_complete' not in tm):
        if INFO:
            log.info('...not ready')
        return
    if DEBUG:
        log.debug('... processing tag mapping')
    if INFO:
        for ind, opt in enumerate(options):
            log.info('Option %s of %s. Option= %s, Value= %s', ind + 1, len(options), opt, options[opt])
    # set arranger tag as required
    if options['cea_arrangers']:
        if '~cea_arrangers' in tm:
            append_tag(tm, 'arranger', tm['~cea_arrangers'])
        if '~cea_orchestrators' in tm:
            append_tag(tm, 'arranger', tm['~cea_orchestrators'])
    # change track artist name to as-credited
    if options['cea_track_credited']:
        if '~cea_credited_track_artists' in tm:
            credit_list = eval(tm['~cea_credited_track_artists'])  # tm is string representation of list
            if not isinstance(credit_list, list):
                credit_list = [credit_list]
            for artist_type in ['~cea_composers', '~cwp_composers']:
                # 'artist', 'artists', '~cea_artist', '~cea_artists', 'composer' should have been set in add_artist_info
                if artist_type in tm:
                    if not isinstance(tm[artist_type], list):
                        artists = tm[artist_type].split('; ')
                    else:
                        artists = tm[artist_type]
                    for x, artist in enumerate(artists):
                        artist_type_sort = artist_type + sort_suffix(artist_type)
                        artist_sort = None
                        if artist_type_sort in tm:
                            if not isinstance(tm[artist_type_sort], list):
                                artists_sort = tm[artist_type_sort].split('; ')
                            else:
                                artists_sort = tm[artist_type_sort]
                            if len(artists_sort) == len(artists):
                                artist_sort = artists_sort[x]
                        for artist_credit in credit_list:
                            if not isinstance(artist_credit[0], list):
                                if artist == artist_credit[1] or (artist_sort and artist_sort == artist_credit[2]):
                                    artists[x] = artist_credit[0]
                            else:
                                if artist_credit[0]:
                                    for i, n in enumerate(artist_credit[0]):
                                        if artist == artist_credit[1][i] or (
                                            artist_sort and artist_sort == artist_credit[2][i]):
                                            artists[x] = n
                    tm[artist_type] = list(set(artists))  # to remove duplicates
    # line-by-line tag mapping
    sort_tags = options['cea_tag_sort']
    for i in range(0, 16):
        tagline = options['cea_tag_' + str(i + 1)].split(",")
        source_group = options['cea_source_' + str(i + 1)].split(",")
        conditional = options['cea_cond_' + str(i + 1)]
        for source_memberx in source_group:
            source_member = source_memberx.strip()
            sourceline = source_member.split("+")
            if len(sourceline) > 1:
                source = "\\"
                for source_itemx in sourceline:
                    source_item = source_itemx.strip()
                    source_itema = source_itemx.lstrip()
                    if INFO:
                        log.info("Source_item: %s", source_item)
                    if "~cea_" + source_item in tm:
                        si = tm['~cea_' + source_item]
                    elif source_item in tm:
                        si = tm[source_item]
                    elif len(source_itema) > 0 and source_itema[0] == "\\":
                        si = source_itema[1:]
                    else:
                        si = ""
                    if si != "" and source != "":
                        source = source + si
                    else:
                        source = ""
            else:
                source = sourceline[0]
            no_names_source = re.sub('(_names)$', 's', source)
            for item, tagx in enumerate(tagline):
                tag = tagx.strip()
                sort = sort_suffix(tag)
                source_sort = sort_suffix(source)
                if DEBUG:
                    log.debug(
                        "%s: Tag mapping: Line: %s, Source: %s, Tag: %s, no_names_source: %s, sort: %s, item %s",
                        PLUGIN_NAME,
                        i +
                        1,
                        source,
                        tag,
                        no_names_source,
                        sort,
                        item)
                if not conditional or tm[tag] == "":
                    if "~cea_" + source in tm:
                        if DEBUG:
                            log.debug("cea")
                        append_tag(tm, tag, tm['~cea_' + source])
                        if sort_tags:
                            if "~cea_" + no_names_source + source_sort in tm:
                                if DEBUG:
                                    log.debug("cea sort")
                                append_tag(
                                    tm, tag + sort, tm['~cea_' + no_names_source + source_sort])
                    elif source in tm:
                        if DEBUG:
                            log.debug("Picard")
                        append_tag(tm, tag, tm[source])
                        if sort_tags:
                            if source + "_sort" in tm:
                                if DEBUG:
                                    log.debug("Picard sort")
                                append_tag(tm, tag + sort,
                                           tm[source + '_sort'])
                    elif len(source) > 0 and source[0] == "\\":
                        append_tag(tm, tag, source[1:])
                    else:
                        pass
    if not DEBUG:
        del tm['~cea_works_complete']
        del tm['~cea_artists_complete']

    # if options over-write enabled, remove it after processing one album
    options['ce_options_overwrite'] = False


def sort_suffix(tag):
    if tag == "composer" or tag == "artist" or tag == "albumartist" or tag == "trackartist":
        sort = "sort"
    else:
        sort = "_sort"
    return sort


def append_tag(tm, tag, source):
    if tag:
        log.debug('appending source: %s to tag: %s (source is type %s)', source, tag, type(source))
        if source and len(source) > 0:
            if isinstance(source, basestring):
                source = source.replace(u'\u2010', u'-')
                source = source.replace(u'\u2019', u"'")
                source = source.split(';')
            if tag in tm:
                for source_item in source:
                    if isinstance(source_item, basestring):
                        source_item = source_item.replace(u'\u2010', u'-')
                    if source_item not in tm[tag]:
                        if not isinstance(tm[tag], list):
                            tag_list = tm[tag].split('; ')
                            tag_list.append(source_item)
                            tm[tag] = tag_list
                            # Picard will have converted it from list to string
                        else:
                            tm[tag].append(source_item)
            else:
                if tag and tag != "":
                    if isinstance(source, list):
                        for source_item in source:
                            if isinstance(source_item, basestring):
                                source_item = source_item.replace(u'\u2010', u'-')
                                source_item = source_item.replace(u'\u2019', u"'")

                            if tag not in tm:
                                tm[tag] = [source_item]
                            else:
                                if not isinstance(tm[tag], list):
                                    tag_list = tm[tag].split('; ')
                                    tag_list.append(source_item)
                                    tm[tag] = tag_list
                                else:
                                    tm[tag].append(source_item)
                    else:
                        tm[tag] = [source]
                        # probably makes no difference to specify a list as Picard will convert the tag to string,
                        # but do it anyway


def parse_data(options, obj, response_list, *match):
    # This function takes any XmlNode object, or list thereof, 
    # and extracts a list of all objects exactly matching the hierarchy listed in match
    # match should contain list of each node in hierarchical sequence, with no gaps in the sequence of nodes, to lowest level required.
    # Insert attribs.attribname:attribvalue in the list to select only branches where attribname is attribvalue.
    # Insert childname.text:childtext in the list to select only branches where a sibling with childname has text childtext.
    #   (Note: childname can be a dot-list if the text is more than one level down - e.g. child1.child2) # TODO - Check this works fully
    DEBUG = False  # options["log_debug"]
    INFO = False  # options["log_info"]
    # XmlNode instances are not iterable, so need to convert to dict
    if isinstance(obj, XmlNode):
        obj = obj.__dict__
    if DEBUG:
        log.debug('%s: parsing data - looking for %s', PLUGIN_NAME, match)
    if INFO:
        log.info('looking in %s', obj)
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, XmlNode):
                item = item.__dict__
            response = parse_data(options, item, response_list, *match)
            response_list + response
        if INFO:
            log.info('response_list: %s', response_list)
        return response_list
    elif isinstance(obj, dict):
        if match[0] in obj:
            if len(match) == 1:
                response = obj[match[0]]
                response_list.append(response)
            else:
                match_list = list(match)
                match_list.pop(0)
                response = parse_data(options, obj[match[0]], response_list, *match_list)
                response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
        elif '.' in match[0]:
            test = match[0].split(':')
            match2 = test[0].split('.')
            test_data = parse_data(options, obj, [], *match2)
            if test[1] in test_data:
                if len(match) == 1:
                    response = obj
                    response_list.append(response)
                else:
                    match_list = list(match)
                    match_list.pop(0)
                    response = parse_data(options, obj, response_list, *match_list)
                    response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
        else:
            if 'children' in obj:
                response = parse_data(options, obj['children'], response_list, *match)
                response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
    else:
        if INFO:
            log.info('response_list: %s', response_list)
        return response_list


def get_artist_credit(options, obj):
    name_credit_list = parse_data(options, obj, [], 'artist_credit', 'name_credit')
    credit_list = []
    if name_credit_list:
        for name_credits in name_credit_list:
            for name_credit in name_credits:
                credited_artist = parse_data(options, name_credit, [], 'name', 'text')
                if credited_artist:
                    name = parse_data(options, name_credit, [], 'artist', 'name', 'text')
                    sort_name = parse_data(options, name_credit, [], 'artist', 'sort_name', 'text')
                    credit_item = (credited_artist, name, sort_name)
                    credit_list.append(credit_item)
        return credit_list


def substitute_name(credit_list, name, sort_name=None):
    new_name = None
    for artist_credit in credit_list:
        if isinstance(artist_credit[0], basestring):
            if name == artist_credit[1] or (sort_name and sort_name == artist_credit[2]):
                new_name = artist_credit[0]
        else:
            if artist_credit[0]:
                for i, n in enumerate(artist_credit[0]):
                    if name == artist_credit[1][i] or (sort_name and sort_name == artist_credit[2][i]):
                        new_name = n
    return new_name


def add_list_uniquely(list_to, list_from):
    # appends only unique elements of list 2 to list 1
    if list_to and list_from:
        if not isinstance(list_to, list) or not isinstance(list_from, list):
            log.error("Cannot add %s to %s because at least one of them is not a list", list_from, list_to)
        else:
            for list_item in list_from:
                if list_item not in list_to:
                    list_to.append(list_item)
    else:
        if list_from:
            list_to = list_from
    return list_to


#################
#################
# EXTRA ARTISTS #
#################
#################


class ExtraArtists:
    # CONSTANTS

    def __init__(self):
        self.album_artists = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of artists to be applied at album level
        self.track_listing = []
        self.options = collections.defaultdict(dict)
        # collection of Classical Extras options

    def add_artist_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):

        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]

        if album.tagger.config.setting['ce_options_overwrite'] and album.tagger.config.setting['cea_override']:
            self.options[track] = album.tagger.config.setting  # mutable
        else:
            self.options[track] = option_settings(album.tagger.config.setting)  # make a copy
        options = self.options[track]

        # OPTIONS - OVER-RIDE IF REQUIRED

        if not options["classical_extra_artists"]:
            return
        # CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.DEBUG = options["log_debug"]
        self.INFO = options["log_info"]
        self.ORCHESTRAS = options["cea_orchestras"].split(',')
        self.CHOIRS = options["cea_choirs"].split(',')
        self.GROUPS = options["cea_groups"].split(',')
        self.ENSEMBLE_TYPES = self.ORCHESTRAS + self.CHOIRS + self.GROUPS

        if self.DEBUG:
            log.debug("%s: add_artist_info", PLUGIN_NAME)

        tm = track_metadata
        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]

        if options["cea_override"]:
            orig_metadata = None
            # Only look up files if needed
            file_options = None
            for music_file in album.tagger.files:
                new_metadata = album.tagger.files[music_file].metadata
                orig_metadata = album.tagger.files[music_file].orig_metadata
                if 'musicbrainz_trackid' in new_metadata and 'musicbrainz_trackid' in tm:
                    if new_metadata['musicbrainz_trackid'] == tm['musicbrainz_trackid']:
                        # find the tag with the options
                        if options['cea_options_tag'] + ':artists_options' in orig_metadata:
                            file_options = eval(orig_metadata[options['cea_options_tag'] + ':artists_options'])
                        else:
                            for om in orig_metadata:
                                if ':artists_options' in om:
                                    file_options = eval(orig_metadata[om])
                        break  # we've found the file and don't want any more!

            if orig_metadata:
                keep_list = options['cea_keep'].split(",")
                for tagx in keep_list:
                    tag = tagx.strip()
                    if tag in orig_metadata:
                        tm[tag] = orig_metadata[tag]

            if file_options:
                options_dict = file_options['Classical Extras']['Artists options']
                for opt in options_dict:
                    if isinstance(options_dict[opt], dict):  # for tag line options
                        opt_list = []
                        for opt_item in options_dict[opt]:
                            opt_list.append({opt + '_' + opt_item: options_dict[opt][opt_item]})
                    else:
                        opt_list = [{opt: options_dict[opt]}]
                    for opt_dict in opt_list:
                        for opt in opt_dict:
                            opt_value = opt_dict[opt]
                            for ea_opt in plugin_options('artists') + plugin_options('tag'):
                                displayed_option = options[ea_opt['option']]
                                if ea_opt['name'] == opt:
                                    if 'value' in ea_opt:
                                        if ea_opt['value'] == opt_value:
                                            options[ea_opt['option']] = True
                                        else:
                                            options[ea_opt['option']] = False
                                    else:
                                        options[ea_opt['option']] = opt_value
                                    if options[ea_opt['option']] != displayed_option:
                                        if self.DEBUG:
                                            log.debug('Options overridden for option = %s',
                                                      opt + ' = ' + str(opt_dict[opt]))
                                        append_tag(tm, '~cwp_info_options', opt + ' = ' + str(opt_dict[opt]))

        self.track_listing.append(track)
        # fix odd hyphens in names for consistency
        field_types = ['~albumartists', '~albumartists_sort']
        for field_type in field_types:
            if field_type in tm:
                field = tm[field_type]
                if isinstance(field, list):
                    for x, it in enumerate(field):
                        field[x] = it.replace(u'\u2010', u'-')
                elif isinstance(field, basestring):
                    field = field.replace(u'\u2010', u'-')
                else:
                    pass
                tm[field_type] = field

        track_artist_credit_list = get_artist_credit(options, trackXmlNode)
        if track_artist_credit_list:
            if self.DEBUG:
                log.debug(
                    "%s: Track artist credit: %s",
                    PLUGIN_NAME,
                    track_artist_credit_list)
            self.append_tag(tm, '~cea_credited_track_artists', track_artist_credit_list)

        if options['cea_track_credited']:
            if track_artist_credit_list:
                for pair in [('artist', 'artistsort'), ('artists', '~artists_sort'), ('composer', 'composersort')]:
                    new_names = []
                    names = {}
                    name_type = ['plain', 'sort']
                    for i in [0, 1]:
                        if pair[i] in tm:
                            if isinstance(tm[pair[i]], basestring):
                                names[name_type[i]] = tm[pair[i]].split('; ')
                            else:
                                names[name_type[i]] = tm[pair[i]]
                        else:
                            names[name_type[i]] = None
                    if names['plain']:
                        for x, name in enumerate(names['plain']):
                            if names['sort'] and len(names['sort']) == len(names['plain']):
                                sort_name = names['sort'][x]
                            else:
                                sort_name = None
                            new_name = substitute_name(track_artist_credit_list, name, sort_name)
                            if new_name:
                                new_names.append(new_name)
                    if new_names:
                        tm[pair[0]] = new_names

        if 'recording' in trackXmlNode.children:
            self.is_recording = True
            for record in trackXmlNode.children['recording']:
                # get recording artists as credited
                recording_artist_credit_list = get_artist_credit(options, record)
                if recording_artist_credit_list:
                    if self.DEBUG:
                        log.debug(
                            "%s: Recording artist credit: %s",
                            PLUGIN_NAME,
                            recording_artist_credit_list)
                    self.append_tag(tm, '~cea_credited_artists', recording_artist_credit_list)

                performerList = self.artist_process_metadata(
                    album, track, record, 'instrument') + self.artist_process_metadata(
                    album, track, record, 'performer') + self.artist_process_metadata(
                    album, track, record, 'vocal')
                #         # returns [(instrument, artist name, artist sort name} or None if no instruments found
                if performerList:
                    if self.DEBUG:
                        log.debug(
                            "%s: Performers: %s",
                            PLUGIN_NAME,
                            performerList)
                    self.set_performer(album, track, performerList, tm, recording_artist_credit_list)

                self.alt_artists(album, track, track_metadata)
                # must be done after performer update but before any special roles

                arrangerList = self.artist_process_metadata(
                    album, track, record, 'instrument arranger') + self.artist_process_metadata(
                    album, track, record, 'arranger')
                #         # returns {instrument, arranger name, arranger sort name} or None if no arrangers found
                if arrangerList:
                    if self.DEBUG:
                        log.debug(
                            "%s: Arrangers: %s",
                            PLUGIN_NAME,
                            arrangerList)
                    self.set_arranger(album, track, arrangerList, tm)

                orchestratorList = self.artist_process_metadata(
                    album, track, record, 'orchestrator')
                #         # returns {None, orchestrator name, orchestrator sort name} or None if no orchestrators found
                if orchestratorList:
                    if self.DEBUG:
                        log.debug(
                            "%s: Orchestrators: %s",
                            PLUGIN_NAME,
                            orchestratorList)
                    self.set_orchestrator(album, track, orchestratorList, tm)

                chorusmasterList = self.artist_process_metadata(
                    album, track, record, 'chorus master')
                #         # returns {None, chorus master name, chorus master sort name} or None if no chorus masters found
                if chorusmasterList:
                    if self.DEBUG:
                        log.debug(
                            "%s: Chorus Masters: %s",
                            PLUGIN_NAME,
                            chorusmasterList)
                    self.set_chorusmaster(album, track, chorusmasterList, tm)

                leaderList = self.artist_process_metadata(
                    album, track, record, 'concertmaster')
                #         # returns {None, leader name, leader sort name} or None if no leaders
                if leaderList:
                    if self.DEBUG:
                        log.debug("%s: Leaders: %s", PLUGIN_NAME, leaderList)
                    self.set_leader(album, track, leaderList, tm)

        # composer last names created by alt_artists function
        if '~cea_album_track_composer_lastnames' in tm:
            if isinstance(tm['~cea_album_track_composer_lastnames'], basestring):
                atc_list = tm['~cea_album_track_composer_lastnames'].split("; ")
            else:
                atc_list = tm['~cea_album_track_composer_lastnames']
            for atc_item in atc_list:
                composer_lastnames = atc_item.strip()
                if album in self.album_artists:
                    if 'composer_lastnames' in self.album_artists[album]:
                        if composer_lastnames not in self.album_artists[album]['composer_lastnames']:
                            self.album_artists[album]['composer_lastnames'].append(
                                composer_lastnames)
                    else:
                        self.album_artists[album]['composer_lastnames'] = [
                            composer_lastnames]
                else:
                    self.album_artists[album]['composer_lastnames'] = [
                        composer_lastnames]
        else:
            if self.WARNING:
                log.warning(
                    "%s: No _cea_album_track_composer_lastnames variable available for recording \"%s\".",
                    PLUGIN_NAME,
                    tm['title'])
            self.append_tag(
                track_metadata,
                '~cea_warning',
                'Composer for this track is not in album artists and will not be available to prefix album')

        if track_metadata['tracknumber'] == track_metadata['totaltracks']:  # last track
            self.process_album(album)

    def alt_artists(self, album, track, metadata):
        if self.INFO:
            log.info("RUNNING %s - alternative artists", PLUGIN_NAME)
        options = self.options[track]
        # provide all the sort fields before creating the new variables
        self.sort_performers(album, track, metadata)
        soloists = []
        soloist_names = []
        soloists_sort = []
        vocalists = []
        instrumentalists = []
        other_soloists = []
        vocalist_names = []
        instrumentalist_names = []
        ensembles = []
        ensemble_names = []
        ensembles_sort = []
        album_soloists = []
        album_soloists_sort = []
        album_conductors = []
        album_conductors_sort = []
        album_ensembles = []
        album_ensembles_sort = []
        album_composers = []
        album_composers_sort = []
        album_composer_lastnames = []
        support_performers = []
        support_performers_sort = []
        composers = []
        conductors = []
        last = re.compile(r'(.*),')
        for key, values in metadata.rawitems():
            if key.startswith('conductor'):
                conductorsort = metadata['~cea_conductors_sort'].split(';')
                for index, conductor in enumerate(values):
                    if not only_roman_chars(conductor):
                        if options['cea_cyrillic']:
                            conductor = remove_middle(
                                unsort(conductorsort[index]))
                    conductors.append(conductor)
                    if stripsir(conductor) in metadata['~albumartists'] or sort_field(stripsir(
                            conductor)) in metadata['~albumartists_sort'] or stripsir(conductor) in metadata[
                        '~albumartists_sort']:
                        album_conductors.append(conductor)
                        album_conductors_sort.append(conductorsort[index])
            if key.startswith('performer'):
                _, subkey = key.split(':', 1)  # mainkey not currently used
                for performer in values:
                    if not only_roman_chars(performer):
                        if options['cea_cyrillic']:
                            performer = remove_middle(get_roman(performer))
                    performername = performer
                    if subkey:
                        perftype = ' (' + subkey + ')'
                    else:
                        perftype = ''
                    performer = performer + perftype
                    if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(
                            performername):
                        if performer not in ensembles:
                            ensembles.append(performer)
                        if performername not in ensemble_names:
                            ensemble_names.append(performername)
                        if performername in metadata['~albumartists'] or swap_prefix(
                                performername) in metadata['~albumartists_sort'] or performername in metadata[
                            '~albumartists_sort']:
                            album_ensembles.append(performername)
                    else:
                        if performer not in soloists:
                            soloists.append(performer)
                        if "vocals" in subkey:
                            if performer not in vocalists:
                                vocalists.append(performer)
                        elif subkey:
                            if performer not in instrumentalists:
                                instrumentalists.append(performer)
                        else:
                            if performer not in other_soloists:
                                other_soloists.append(performer)
                        if performername not in soloist_names:
                            soloist_names.append(performername)
                            if "vocals" in subkey:
                                if performer not in vocalist_names:
                                    vocalist_names.append(performername)
                            elif subkey:
                                if performer not in instrumentalist_names:
                                    instrumentalist_names.append(performername)
                            else:
                                pass
                        match = last.search(
                            sort_field(stripsir(performername)))
                        if match:
                            performerlast = match.group(1)
                        else:
                            performerlast = sort_field(stripsir(performername))
                        if stripsir(performername) in metadata['~albumartists'] or performerlast in metadata[
                            '~albumartists_sort']\
                                or stripsir(performername) in metadata['~albumartists_sort']:
                            album_soloists.append(performername)
                        else:
                            if subkey not in self.ENSEMBLE_TYPES and not self.ensemble_type(
                                    performername):
                                if performer not in support_performers:
                                    support_performers.append(performer)
            if key.startswith('~performer_sort'):
                _, subkey = key.split(':', 1)  # mainkey not used
                for performer in values:
                    if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(
                            performer):
                        if performer not in ensembles_sort:
                            ensembles_sort.append(performer)
                        if performer in metadata['~albumartists_sort'] or unsort(
                                performer) in metadata['~albumartists']:  # in case of sort differences
                            if performer not in album_ensembles_sort:
                                album_ensembles_sort.append(performer)
                    else:
                        if performer not in soloists_sort:  # performer might appear more than once if on multiple instruments
                            soloists_sort.append(performer)
                        match = last.search(performer)
                        if match:
                            performerlast = match.group(1)
                        else:
                            performerlast = sort_field(performer)

                        # in case of sort differences
                        if performer in metadata['~albumartists_sort'] or performerlast in metadata['~albumartists']:
                            if performer not in album_soloists_sort:
                                album_soloists_sort.append(performer)
                        else:
                            if subkey not in self.ENSEMBLE_TYPES and not self.ensemble_type(
                                    performer):
                                if performer not in support_performers_sort:
                                    support_performers_sort.append(performer)
            if key == 'composer':
                if self.DEBUG:
                    log.debug("Setting composer names for: %s", values)
                if isinstance(metadata['composersort'], basestring):
                    composers_sort = metadata['composersort'].split("; ")
                else:
                    composers_sort = metadata['composersort']
                if isinstance(metadata['artists'], basestring):
                    artist_names = metadata['artists'].split("; ")
                else:
                    artist_names = metadata['artists']
                if isinstance(metadata['~artists_sort'], basestring):
                    artists_sort = metadata['~artists_sort'].split("; ")
                else:
                    artists_sort = metadata['~artists_sort']
                metadata['~cea_composers_sort'] = composers_sort
                for index, composer in enumerate(values):
                    if self.DEBUG:
                        log.debug("Setting composer names")
                    composersort = composers_sort[index]
                    composerlast = composersort.split(",")[0]
                    if index < len(artist_names) and index < len(artists_sort):
                        artist_name = artist_names[index]
                        artistsort = artists_sort[index]
                        artistlast = artistsort.split(",")[0]
                        if self.INFO:
                            log.info(
                                "composer: %s, composerlast: %s, artist_name: %s, artistlast: %s",
                                composer,
                                composerlast,
                                artist_name,
                                artistlast)
                        if artistlast == composerlast:
                            # because Picard locale option only works correctly
                            # on artists, not composers etc.
                            composer = artist_name
                    if not only_roman_chars(composer):
                        if options['cea_cyrillic']:
                            composer = remove_middle(unsort(composersort))
                    composers.append(composer)
                    if stripsir(composer) in metadata['~albumartists'] or sort_field(stripsir(composer)) in metadata[
                        '~albumartists_sort'] \
                            or stripsir(composer) in metadata['~albumartists_sort'] or composersort in metadata[
                        '~albumartists_sort'] \
                            or unsort(composersort) in metadata['~albumartists'] or composerlast in metadata[
                        '~albumartists'] \
                            or composerlast in metadata['~albumartists_sort']:
                        album_composers.append(composer)
                        album_composers_sort.append(composersort)
                        album_composer_lastnames.append(composerlast)

        metadata['~cea_soloists'] = soloists
        metadata['~cea_soloist_names'] = soloist_names
        metadata['~cea_vocalists'] = vocalists
        metadata['~cea_vocalist_names'] = vocalist_names
        metadata['~cea_instrumentalists'] = instrumentalists
        metadata['~cea_instrumentalist_names'] = instrumentalist_names
        metadata['~cea_other_soloists'] = other_soloists
        metadata['~cea_soloists_sort'] = soloists_sort
        metadata['~cea_ensembles'] = ensembles
        metadata['~cea_ensemble_names'] = ensemble_names
        metadata['~cea_ensembles_sort'] = ensembles_sort
        metadata['~cea_album_soloists'] = album_soloists
        metadata['~cea_album_soloists_sort'] = album_soloists_sort
        metadata['~cea_album_conductors'] = album_conductors
        metadata['~cea_album_conductors_sort'] = album_conductors_sort
        metadata['~cea_album_ensembles'] = album_ensembles
        metadata['~cea_album_ensembles_sort'] = album_ensembles_sort
        metadata['~cea_album_composers'] = album_composers
        metadata['~cea_album_composers_sort'] = album_composers_sort
        metadata['~cea_album_track_composer_lastnames'] = album_composer_lastnames
        metadata['~cea_support_performers'] = support_performers
        metadata['~cea_support_performers_sort'] = support_performers_sort
        metadata['~cea_composers'] = composers
        if options['cea_cyrillic']:
            self.append_tag(metadata, 'composer', composers)
        metadata['~cea_conductors'] = conductors
        if options['cea_cyrillic']:
            self.append_tag(metadata, 'conductor', conductors)

    def sort_performers(self, album, track, metadata):
        options = self.options[track]
        for key, values in metadata.rawitems():
            if key.startswith('conductor'):
                conductorsort = []
                for conductor in values:
                    if options['cea_cyrillic']:
                        if not only_roman_chars(conductor):
                            conductor = remove_middle(get_roman(conductor))
                    conductorsort.append(sort_field(conductor))
                metadata['~cea_conductors_sort'] = conductorsort
            if not key.startswith('performer'):
                continue
            _, subkey = key.split(':', 1)  # mainkey not used
            performersort = []
            for performer in values:
                if options['cea_cyrillic']:
                    if not only_roman_chars(performer):
                        performer = remove_middle(get_roman(performer))
                if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(
                        performer):
                    performersort.append(swap_prefix(performer))
                else:
                    performersort.append(sort_field(performer))
            sortkey = "~performer_sort:%s" % subkey
            if self.DEBUG:
                log.debug(
                    "%s: sortkey = %s, performersort = %s",
                    PLUGIN_NAME,
                    sortkey,
                    performersort)  # debug
            metadata[sortkey] = performersort

    # Checks for ensembles
    def ensemble_type(self, performer):
        for ensemble_name in self.ORCHESTRAS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Orchestra'
        for ensemble_name in self.CHOIRS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Choir'
        for ensemble_name in self.GROUPS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Group'
        return False

    def artist_process_metadata(self, album, track, record, artistType):
        if self.DEBUG:
            log.debug('%s: Process artist metadata for track: %s, artistType: %s', PLUGIN_NAME, track, artistType)
        options = self.options[track]
        artist_list = []
        if 'relation_list' in record.children:
            artist_types = parse_data(options, record, [], 'relation_list', 'attribs.target_type:artist', 'relation',
                                      'attribs.type:' + artistType)
            for artist_type in artist_types:
                artists = parse_data(options, artist_type, [], 'artist')
                instrument_list = []
                if artistType == 'instrument' or artistType == 'vocal' or artistType == 'instrument arranger':
                    instrument_list = parse_data(options, artist_type, [], 'attribute_list', 'attribute', 'text')
                    if artistType == 'vocal' and instrument_list == []:
                        instrument_list = ['vocals']
                for artist in artists:
                    name = parse_data(options, artist, [], 'name', 'text')
                    sort_name = parse_data(options, artist, [], 'sort_name', 'text')
                    artist_list.append((instrument_list, name, sort_name))
            if artist_list:
                if self.DEBUG:
                    log.debug(
                        "%s: Artists of type %s found: %s",
                        PLUGIN_NAME,
                        artistType,
                        artist_list)  # debug
            else:
                if self.DEBUG:
                    log.debug("%s: No Artist found", PLUGIN_NAME)  # debug
            return artist_list

        else:
            if self.ERROR:
                log.error(
                    "%s: %r: MusicBrainz artist xml result not in correct format.",
                    PLUGIN_NAME,
                    track)
            extra_msg = ' Turn on info logging and refresh for more information' if not self.INFO else ''
            if self.ERROR:
                log.error(
                    "This could be because the recording has no relationships on MusicBrainz.%s",
                    extra_msg)
            if self.INFO:
                log.info(
                    "Check the details on MusicBrainz. XML returned is as follows:")
            if self.INFO:
                log.info(record)
            self.append_tag(
                track.metadata,
                '~cea_error',
                'MusicBrainz artist xml result not in correct format or the recording has no relationships on MusicBrainz.')
        return None

    def process_album(self, album):
        for track in self.track_listing:
            options = self.options[track]
            tm = track.metadata
            tm['~cea_version'] = PLUGIN_VERSION
            blank_tags = options['cea_blank_tag'].split(
                ",") + options['cea_blank_tag_2'].split(",")
            # set work-type before any tags are blanked
            if options['cea_genres']:
                if (self.is_recording and options['classical_work_parts'] and \
                                'artistsort' in tm and 'composersort' in tm and \
                                tm['artistsort'].split(",")[0] == tm['composersort'].split(",")[0]) or \
                        ('is_classical' in tm and tm['is_classical'] == 1):
                    self.append_tag(tm, '~cea_work_type', 'Classical')
                instrument = re.compile(r'.*\((.+)\)')
                vocals = re.compile(r'.*\(((.*)vocals)\)')
                if '~cea_ensembles' in tm:
                    large = False
                    if 'performer:orchestra' in tm:
                        large = True
                        self.append_tag(tm, '~cea_work_type', 'Orchestral')
                        if '~cea_soloists' in tm:
                            if 'vocals' in tm['~cea_soloists']:
                                self.append_tag(tm, '~cea_work_type', 'Voice')
                            if isinstance(tm['~cea_soloists'], basestring):
                                soloists = tm['~cea_soloists'].split(";")
                            else:
                                soloists = tm['~cea_soloists']
                            if len(soloists) == 1:
                                match = instrument.search(soloists[0])
                                if match:
                                    if 'vocals' not in match.group(1).lower():
                                        self.append_tag(
                                            tm, '~cea_work_type', 'Concerto')
                                        self.append_tag(
                                            tm, '~cea_work_type', match.group(1).title())
                                    else:
                                        self.append_tag(
                                            tm, '~cea_work_type', 'Aria')
                                        match2 = vocals.search(soloists[0])
                                        if match2:
                                            self.append_tag(
                                                tm, '~cea_work_type', match2.group(2).strip().title())
                            elif len(soloists) == 2:
                                self.append_tag(tm, '~cea_work_type', 'Duet')
                                for i in range(0, 2):
                                    match = instrument.search(soloists[i])
                                    if match:
                                        if 'vocals' not in match.group(
                                                1).lower():
                                            self.append_tag(
                                                tm, '~cea_work_type', 'Concerto')
                                            self.append_tag(
                                                tm, '~cea_work_type', match.group(1).title())

                    if 'performer:choir' in tm or 'performer:choir vocals' in tm:
                        large = True
                        self.append_tag(tm, '~cea_work_type', 'Choral')
                        self.append_tag(tm, '~cea_work_type', 'Voice')
                    else:
                        if large and 'soloists' in tm and tm['soloists'].count(
                                'vocals') > 1:
                            self.append_tag(tm, '~cea_work_type', 'Opera')
                    if not large:
                        if '~cea_soloists' not in tm:
                            self.append_tag(tm, '~cea_work_type', 'Chamber')
                        else:
                            if 'vocals' in tm['~cea_soloists']:
                                self.append_tag(tm, '~cea_work_type', 'Song')
                                self.append_tag(tm, '~cea_work_type', 'Voice')
                            else:
                                self.append_tag(
                                    tm, '~cea_work_type', 'Chamber')
                else:
                    if '~cea_soloists' in tm:
                        if isinstance(tm['~cea_soloists'], basestring):
                            soloists = tm['~cea_soloists'].split(";")
                        else:
                            soloists = tm['~cea_soloists']
                        if len(soloists) == 1:
                            match = instrument.search(soloists[0])
                            if match:
                                if 'vocals' not in match.group(1).lower():
                                    self.append_tag(
                                        tm, '~cea_work_type', 'Instrumental')
                                    self.append_tag(
                                        tm, '~cea_work_type', match.group(1).title())
                                else:
                                    self.append_tag(
                                        tm, '~cea_work_type', 'Song')
                                    self.append_tag(
                                        tm, '~cea_work_type', 'Voice')
                                    self.append_tag(
                                        tm, '~cea_work_type', match.group(1).title())
                        else:
                            if 'vocals' not in soloists:
                                self.append_tag(
                                    tm, '~cea_work_type', 'Chamber')
                            else:
                                self.append_tag(tm, '~cea_work_type', 'Song')
                                self.append_tag(tm, '~cea_work_type', 'Voice')
            # blank tags
            for tag in blank_tags:
                if tag.strip() in tm:
                    # place blanked tags into hidden variables available for
                    # re-use
                    tm['~cea_' + tag.strip()] = tm[tag.strip()]
                    del tm[tag.strip()]

            # album

            if 'composer_lastnames' in self.album_artists[album]:
                tm['~cea_release'] = tm['album']
                last_names = self.album_artists[album]['composer_lastnames']
                tm['~cea_album_composer_lastnames'] = last_names
                if options['cea_composer_album']:
                    new_last_names = []
                    for last_name in last_names:
                        new_last_names.append(last_name)
                    if len(new_last_names) > 0:
                        tm['album'] = "; ".join(
                            new_last_names) + ": " + tm['album']

            # process tag mapping
            tm['~cea_artists_complete'] = "Y"
            map_tags(options, tm)

            # write out options and errors/warnings to tags
            if options['cea_options_tag'] != "":
                self.cea_options = collections.defaultdict(
                    lambda: collections.defaultdict(
                        lambda: collections.defaultdict(dict)))

                for opt in plugin_options('artists'):
                    if 'name' in opt:
                        if 'value' in opt:
                            if options[opt['option']]:
                                self.cea_options['Classical Extras']['Artists options'][opt['name']] = opt['value']
                        else:
                            self.cea_options['Classical Extras']['Artists options'][opt['name']] = \
                                options[opt['option']]

                for opt in plugin_options('tag'):
                    if opt['option'] != "":
                        name_list = opt['name'].split("_")
                        self.cea_options['Classical Extras']['Artists options'][name_list[0]][name_list[1]] = \
                            options[opt['option']]

                if options['ce_version_tag'] and options['ce_version_tag'] != "":
                    self.append_tag(
                        tm, options['ce_version_tag'], str(
                            'Version ' + tm['~cea_version'] + ' of Classical Extras'))
                if options['cea_options_tag'] and options['cea_options_tag'] != "":
                    self.append_tag(
                        tm,
                        options['cea_options_tag'] +
                        ':artists_options',
                        json.loads(
                            json.dumps(
                                self.cea_options)))
            if self.ERROR and "~cea_error" in tm:
                self.append_tag(tm, '001_errors', tm['~cea_error'])
            if self.WARNING and "~cea_warning" in tm:
                self.append_tag(tm, '002_warnings', tm['~cea_warning'])
        self.track_listing = []
        if self.INFO:
            log.info(
                "FINISHED Classical Extra Artists. Album: %s",
                track.album.metadata)

    def append_tag(self, tm, tag, source):
        if self.INFO:
            log.info("Extra Artists - appending %s to %s", source, tag)
        append_tag(tm, tag, source)

    def remove_tag(self, tm, tag, source):
        if self.INFO:
            log.info("Extra Artists - removing %s from %s", source, tag)
        if tag in tm:
            if isinstance(source, basestring):
                source = source.replace(u'\u2010', u'-')
            if source in tm[tag]:
                if isinstance(tm[tag], list):
                    old_tag = tm[tag]
                else:
                    old_tag = tm[tag].split(";")
                new_tag = old_tag
                for i, tag_item in enumerate(old_tag):
                    if tag_item == source:
                        new_tag.pop(i)
                tm[tag] = new_tag

    def update_tag(self, tm, tag, old_source, new_source):
        # if old_source does not exist, it will just append new_source
        if self.INFO:
            log.info("Extra Artists - updating %s from %s to %s", tag, old_source, new_source)
        self.remove_tag(tm, tag, old_source)
        self.append_tag(tm, tag, new_source)

    def set_performer(self, album, track, performerList, tm, credit_list):
        # performerList is in format [([instrument list],[name list],[sort_name list]),(.....etc]
        if self.DEBUG:
            log.debug("Extra Artists - set_performer")
        options = self.options[track]
        for performer in performerList:
            if performer[0]:
                inst_list = performer[0][:]
                # need to take a copy of the list otherwise (because of list mutability) the old list gets changed too!
                if options['cea_no_solo']:
                    if 'solo' in inst_list:
                        inst_list.remove('solo')
                instrument = ", ".join(inst_list)
            else:
                instrument = None
            name_list = performer[1]
            for ind, name in enumerate(name_list):
                old_name = name
                sort_name = performer[2][ind]
                # change name to as-credited
                if options['cea_credited']:
                    for artist_credit in credit_list:
                        if isinstance(artist_credit[0], basestring):
                            if name == artist_credit[1] or sort_name == artist_credit[2]:
                                name = artist_credit[0]
                        else:
                            if artist_credit[0]:
                                for i, n in enumerate(artist_credit[0]):
                                    if name == artist_credit[1][i] or sort_name == artist_credit[2][i]:
                                        name = n
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        if not only_roman_chars(tm['performer:' + instrument]):
                            name = remove_middle(unsort(sort_name))
                            # Only remove middle name where the existing
                            # performer is in non-latin script
                if only_roman_chars(name):
                    if instrument:
                        newkey = '%s:%s' % ('performer', instrument)
                        oldkey = '%s:%s' % ('performer', ' and '.join(performer[0]).lower())
                    else:
                        newkey = 'performer:'
                        oldkey = newkey
                    if self.DEBUG:
                        log.debug(
                            "%s: SETTING PERFORMER. NEW KEY = %s",
                            PLUGIN_NAME,
                            newkey)
                    if newkey != oldkey:
                        self.remove_tag(tm, oldkey, old_name)
                    self.update_tag(tm, newkey, old_name, name)
                if instrument:
                    details = name + ' (' + instrument + ')'
                else:
                    details = name
                self.update_tag(tm, '~cea_performers', old_name, details)

    def set_arranger(self, album, track, arrangerList, tm):
        if self.DEBUG:
            log.debug("Extra Artists - set_arranger")
        options = self.options[track]
        for arranger in arrangerList:
            if arranger[0]:
                instrument = ', '.join(arranger[0])
            else:
                instrument = None
            name_list = arranger[1]
            for ind, name in enumerate(name_list):
                sort_name = arranger[2][ind]
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        name = remove_middle(unsort(sort_name))
                if instrument:
                    newkey = '%s:%s' % ('arranger', instrument)
                    if self.DEBUG:
                        log.debug("NEW KEY = %s", newkey)
                    tm.add_unique(newkey, name)
                    details = name + ' (' + instrument + ')'
                else:
                    details = name
                if '~cea_arrangers' in tm:
                    tm['~cea_arrangers'] = tm['~cea_arrangers'] + '; ' + details
                else:
                    tm['~cea_arrangers'] = details

    def set_orchestrator(self, album, track, orchestratorList, tm):
        if self.DEBUG:
            log.debug("Extra Artists - set_orchestrator")
        options = self.options[track]
        if isinstance(tm['arranger'], basestring):
            arrangerList = tm['arranger'].split(';')
        else:
            arrangerList = tm['arranger']
        newList = arrangerList
        for orchestrator in orchestratorList:
            name_list = orchestrator[1]
            for ind, name in enumerate(name_list):
                sort_name = orchestrator[2][ind]
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        name = remove_middle(unsort(sort_name))
                if options['cea_orchestrator'] != "":
                    details = name + ' (' + options['cea_orchestrator'] + ')'
                else:
                    details = name
                if '~cea_orchestrators' in tm:
                    if name not in tm['~cea_orchestrators']:
                        tm['~cea_orchestrators'] = tm['~cea_orchestrators'] + '; ' + name
                else:
                    tm['~cea_orchestrators'] = name
                appendList = []
                for index, arranger in enumerate(arrangerList):
                    if name in arranger:
                        newList[index] = details
                    else:
                        appendList.append(details)
                for append_item in appendList:
                    newList.append(append_item)
            if options['cea_orchestrator'] != "":
                tm['arranger'] = newList

    def set_chorusmaster(self, album, track, chorusmasterList, tm):
        if self.DEBUG:
            log.debug("Extra Artists - set_chorusmaster")
        options = self.options[track]
        if isinstance(tm['conductor'], basestring):
            conductorList = tm['conductor'].split(';')
        else:
            conductorList = tm['conductor']
        newList = conductorList
        for chorusmaster in chorusmasterList:
            name_list = chorusmaster[1]
            for ind, name in enumerate(name_list):
                sort_name = chorusmaster[2][ind]
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        name = remove_middle(unsort(sort_name))
                if options['cea_chorusmaster'] != "":
                    details = name + ' (' + options['cea_chorusmaster'] + ')'
                else:
                    details = name
                if '~cea_chorusmasters' in tm:
                    if name not in tm['~cea_chorusmasters']:
                        tm['~cea_chorusmasters'] = tm['~cea_chorusmasters'] + '; ' + name
                else:
                    tm['~cea_chorusmasters'] = name

                for index, conductor in enumerate(conductorList):
                    if name in conductor:
                        newList[index] = details
            if options['cea_chorusmaster'] != "":
                tm['conductor'] = newList

    def set_leader(self, album, track, leaderList, tm):
        if self.DEBUG:
            log.debug("Extra Artists - set_leader")
        options = self.options[track]
        for leader in leaderList:
            name_list = leader[1]
            for ind, name in enumerate(name_list):
                sort_name = leader[2][ind]
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        name = remove_middle(unsort(sort_name))
                newkey = '%s:%s' % ('performer', options['cea_concertmaster'])
                if self.DEBUG:
                    log.debug(
                        "%s: SETTING PERFORMER. NEW KEY = %s",
                        PLUGIN_NAME,
                        newkey)
                if options['cea_concertmaster'] != "":
                    tm.add_unique(newkey, name)
                # #details variable not currently used
                #     details = name + ' (' + options['cea_concertmaster'] + ')'
                # else:
                #     details = name
                if '~cea_leaders' in tm:
                    if name not in tm['~cea_leaders']:
                        tm['~cea_leaders'] = tm['~cea_leaders'] + '; ' + name
                else:
                    tm['~cea_leaders'] = name


##############
##############
# WORK PARTS #
##############
##############

class PartLevels:
    # QUEUE-HANDLING
    class WorksQueue(LockableObject):
        """Object for managing the queue of lookups"""

        def __init__(self):
            LockableObject.__init__(self)
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            self.lock_for_read()
            value = self.queue[name] if name in self.queue else None
            self.unlock()
            return value

        def __setitem__(self, name, value):
            self.lock_for_write()
            self.queue[name] = value
            self.unlock()

        def append(self, name, value):
            self.lock_for_write()
            if name in self.queue:
                self.queue[name].append(value)
                value = False
            else:
                self.queue[name] = [value]
                value = True
            self.unlock()
            return value

        def remove(self, name):
            self.lock_for_write()
            value = None
            if name in self.queue:
                value = self.queue[name]
                del self.queue[name]
            self.unlock()
            return value

        # INITIALISATION

    def __init__(self):
        self.works_cache = {}
        # maintains list of parent of each workid, or None if no parent found,
        # so that XML lookup need only executed if no existing record
        self.partof = {}
        # the inverse of the above (immediate children of each parent)
        self.works_queue = self.WorksQueue()
        # lookup queue - holds track/album pairs for each queued workid (may be
        # more than one pair per id, especially for higher-level parts)
        self.parts = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # metadata collection for all parts - structure is {workid: {name: ,
        # parent: , (track,album): {part_levels}}, etc}
        self.pending_strip = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # metadata collection for parts awaiting higher-level text stripping -
        # structure is {(track, album): {workid: {child: part_level:]}, etc}
        self.top_works = collections.defaultdict(dict)
        # metadata collection for top-level works for (track, album) -
        # structure is {(track, album): {workId: }, etc}
        self.trackback = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # hierarchical iterative work structure - {album: {id: , children:{id:
        # , children{}, id: etc}, id: etc} }
        self.work_listing = collections.defaultdict(list)
        # contains list of workIds for each album
        self.top = collections.defaultdict(list)
        # self.top[album] = list of work Ids which are top-level works in album
        self.options = collections.defaultdict(dict)
        # currently active Classical Extras options
        self.file_works = collections.defaultdict(list)
        # list of works derived from SongKong-style file tags
        # structure is {(album, track): [{workid, name}, {workid ....]}

    ########################################
    # SECTION 1 - Initial track processing #
    ########################################

    def add_work_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):

        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]

        # OPTIONS - OVER-RIDE IF REQUIRED

        if album.tagger.config.setting['ce_options_overwrite'] and album.tagger.config.setting['cwp_override']:
            self.options[track] = album.tagger.config.setting  # mutable
        else:
            self.options[track] = option_settings(album.tagger.config.setting)  # make a copy
        options = self.options[track]

        # CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.DEBUG = options["log_debug"]
        self.INFO = options["log_info"]

        tm = track_metadata
        if options["cwp_override"] or options["cwp_use_sk"]:
            # Only look up files if needed for options override
            file_options = None
            for music_file in album.tagger.files:
                new_metadata = album.tagger.files[music_file].metadata
                orig_metadata = album.tagger.files[music_file].orig_metadata
                if 'musicbrainz_trackid' in new_metadata and 'musicbrainz_trackid' in tm:
                    if new_metadata['musicbrainz_trackid'] == tm['musicbrainz_trackid']:
                        # find the tag with the options, if override required
                        if options["cwp_override"]:
                            if options['cwp_options_tag'] + ':workparts_options' in orig_metadata:
                                file_options = eval(orig_metadata[options['cwp_options_tag'] + ':workparts_options'])
                            else:
                                for om in orig_metadata:
                                    if ':workparts_options' in om:
                                        file_options = eval(orig_metadata[om])
                        # get the work tags
                        if options["cwp_use_sk"]:
                            if 'musicbrainz_work_composition_id' in orig_metadata and 'musicbrainz_workid' in orig_metadata:
                                if 'musicbrainz_work_composition' in orig_metadata:
                                    if 'musicbrainz_work' in orig_metadata:
                                        if orig_metadata['musicbrainz_work_composition_id'] == orig_metadata[
                                            'musicbrainz_workid'] \
                                                and orig_metadata['musicbrainz_work_composition'] != orig_metadata[
                                                    'musicbrainz_work']:
                                            # Picard may have overwritten SongKong tag (top work id) with bottom work id
                                            if self.WARNING:
                                                log.warning(
                                                    '%s: File tag musicbrainz_workid incorrect? id = %s. Sourcing from MB',
                                                    PLUGIN_NAME, orig_metadata['musicbrainz_workid'])
                                            self.append_tag(tm,
                                                            '~cwp_warning',
                                                            'File tag musicbrainz_workid incorrect? id = ' +
                                                            orig_metadata['musicbrainz_workid'] + '. Sourcing from MB')
                                            break
                                    if self.INFO:
                                        log.info('Read from file tag: musicbrainz_work_composition_id: %s',
                                                 orig_metadata['musicbrainz_work_composition_id'])
                                    self.file_works[(album, track)].append({
                                        'workid': orig_metadata['musicbrainz_work_composition_id'].split('; '),
                                        'name': orig_metadata['musicbrainz_work_composition']})
                                else:
                                    if self.ERROR:
                                        wid = orig_metadata['musicbrainz_work_composition_id']
                                        log.error("%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                                    self.append_tag(tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                                    break
                                n = 1
                                while 'musicbrainz_work_part_level' + str(n) + '_id' in orig_metadata:
                                    if 'musicbrainz_work_part_level' + str(n) in orig_metadata:
                                        self.file_works[(album, track)].append({
                                            'workid': orig_metadata[
                                                'musicbrainz_work_part_level' + str(n) + '_id'].split('; '),
                                            'name': orig_metadata['musicbrainz_work_part_level' + str(n)]})
                                        n += 1
                                    else:
                                        if self.ERROR:
                                            wid = orig_metadata['musicbrainz_work_part_level' + str(n) + '_id']
                                            log.error("%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                                        self.append_tag(tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                                        break
                                if orig_metadata['musicbrainz_work_composition_id'] != orig_metadata[
                                    'musicbrainz_workid']:
                                    if 'musicbrainz_work' in orig_metadata:
                                        self.file_works[(album, track)].append({
                                            'workid': orig_metadata['musicbrainz_workid'].split('; '),
                                            'name': orig_metadata['musicbrainz_work']})
                                    else:
                                        if self.ERROR:
                                            wid = orig_metadata['musicbrainz_workid']
                                            log.error("%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                                        self.append_tag(tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                                        break
                                file_work_levels = len(self.file_works[(album, track)])
                                if self.DEBUG:
                                    log.debug('%s: Loaded works from file tags for track %s. Works: %s: ', PLUGIN_NAME,
                                              track, self.file_works[(album, track)])
                                for i, work in enumerate(self.file_works[(album, track)]):
                                    workId = tuple(work['workid'])
                                    if workId not in self.works_cache:  # Use cache in preference to file tags
                                        if workId not in self.work_listing[album]:
                                            self.work_listing[album].append(workId)
                                        self.parts[workId]['name'] = [work['name']]
                                        parentId = None
                                        if i < file_work_levels - 1:
                                            parentId = self.file_works[(album, track)][i + 1]['workid']
                                            parent = self.file_works[(album, track)][i + 1]['name']

                                        if parentId:
                                            self.works_cache[workId] = parentId
                                            self.parts[workId]['parent'] = parentId
                                            self.parts[tuple(parentId)]['name'] = [parent]
                                        else:
                                            # so we remember we looked it up and found none
                                            self.parts[workId]['no_parent'] = True
                                            self.top_works[(track, album)]['workId'] = workId
                                            if workId not in self.top[album]:
                                                self.top[album].append(workId)

                        break  # we've found the file and don't want any more!

            if file_options:
                options_dict = file_options['Classical Extras']['Works options']
                for opt in options_dict:
                    opt_value = options_dict[opt]
                    for wp_opt in plugin_options('workparts'):
                        displayed_option = options[wp_opt['option']]
                        if wp_opt['name'] == opt:
                            if 'value' in wp_opt:
                                if wp_opt['value'] == opt_value:
                                    options[wp_opt['option']] = True
                                else:
                                    options[wp_opt['option']] = False
                            else:
                                options[wp_opt['option']] = opt_value
                            if options[wp_opt['option']] != displayed_option:
                                if self.DEBUG:
                                    log.debug('Options overridden for option = %s',
                                              wp_opt['option'] + ' = ' + str(options[wp_opt['option']]))
                                append_tag(tm, '~cwp_info_options', opt + ' = ' + str(options_dict[opt]))
        # Continue?
        if not options["classical_work_parts"]:
            return

        # OPTION-DEPENDENT CONSTANTS:
        # Maximum number of XML- lookup retries if error returned from server
        self.MAX_RETRIES = options["cwp_retries"]
        # Proportion of a string to be matched to a (usually larger) string for
        # it to be considered essentially similar
        # self.SUBSTRING_MATCH = float(options["cwp_substring_match"]) / 100
        self.USE_CACHE = options["use_cache"]
        # splitting for matching of parents. 1 = split in two, 2 = split in
        # three etc.
        # self.GRANULARITY = options["cwp_granularity"]
        # proximity of new words in title comparison which will result in
        # infill words being included as well. 2 means 2-word 'gaps' of
        # existing words between new words will be treated as 'new'
        # self.PROXIMITY = options["cwp_proximity"]
        # proximity measure to be used when infilling to the end of the title
        # self.END_PROXIMITY = options["cwp_end_proximity"]
        # self.USE_LEVEL_0 = options["cwp_level0_works"]
        # self.REMOVEWORDS = options["cwp_removewords"]
        if options["cwp_partial"] and options["cwp_partial_text"] and options["cwp_level0_works"]:
            options["cwp_removewords"] += ", " + options["cwp_partial_text"] + ' '  # Explanation:
        # If "Partial" is selected then the level 0 work name will have PARTIAL_TEXT appended to it.
        # If a recording is split across several tracks then each sub-part (quasi-movement) will have the same name
        # (with the PARTIAL_TEXT added). If level 0 is used to source work names then the level 1 work name will be
        # changed to be this repeated name and will therefore also include PARTIAL_TEXT.
        # So we need to add PARTIAL_TEXT to the prefixes list to ensure it is excluded from the level 1  work name.
        # self.SYNONYMS = options["cwp_synonyms"]
        # self.REPLACEMENTS = options["cwp_replacements"]
        if self.DEBUG:
            log.debug("%s: LOAD NEW TRACK: :%s", PLUGIN_NAME, track)
        # if self.INFO:
        #     log.info("trackXmlNode: %s", trackXmlNode) #  Only use with small releases
        # fix titles which include composer name
        composersort = dict.get(track_metadata, 'composersort', [])
        composerlastnames = []
        for composer in composersort:
            lname = re.compile(r'(.*),')
            match = lname.search(composer)
            if match:
                composerlastnames.append(match.group(1))
            else:
                composerlastnames.append(composer)
        title = track_metadata['title']
        colons = title.count(":")
        if colons > 0:
            title_split = title.split(': ', 1)
            test = title_split[0]
            if test in composerlastnames:
                track_metadata['~cwp_title'] = title_split[1]
        # now process works

        workIds = dict.get(track_metadata, 'musicbrainz_workid', [])
        if workIds:
            # works = dict.get(track_metadata, 'work', [])
            work_list_info = []
            keyed_workIds = {}
            for i, workId in enumerate(workIds):

                # sort by ordering_key, if any
                match_tree = ['recording', 'relation_list', 'attribs.target_type:work', 'relation',
                              'target.text:' + workId, 'ordering_key', 'text']
                parse_result = parse_data(options, trackXmlNode, [], *match_tree)
                if self.INFO:
                    log.info('multi-works - ordering key: %s', parse_result)
                if parse_result and parse_result[0].isdigit():
                    key = int(parse_result[0])
                else:
                    key = 'no key - id seq: ' + str(i)
                keyed_workIds[key] = workId
            for key in sorted(keyed_workIds.iterkeys()):
                workId = keyed_workIds[key]
                work_rels = parse_data(options, trackXmlNode, [], 'recording', 'relation_list',
                                       'attribs.target_type:work', 'relation', 'target.text:' + workId)
                work_attributes = parse_data(options, work_rels, [], 'attribute_list', 'attribute', 'text')
                work_titles = parse_data(options, work_rels, [], 'work', 'attribs.id:' + workId, 'title', 'text')
                if self.INFO:
                    log.info('Work details. Rels: %s, Attributes: %s, Titles: %s', work_rels, work_attributes,
                             work_titles)
                work_list_info_item = {'id': workId, 'attributes': work_attributes, 'titles': work_titles}
                work_list_info.append(work_list_info_item)
                work = []
                for title in work_titles:
                    work.append(title)

                partial = False
                if options['cwp_partial']:
                    # treat the recording as work level 0 and the work of which it
                    # is a partial recording as work level 1
                    if 'partial' in work_attributes:
                        partial = True
                        parentId = workId
                        workId = track_metadata['musicbrainz_recordingid']

                        works = []
                        for w in work:
                            partwork = w  # + ": " + options["cwp_partial_text"] + ' '
                            works.append(partwork)

                        if self.DEBUG:
                            log.debug(
                                "%s: Id %s is PARTIAL RECORDING OF id: %s, name: %s",
                                PLUGIN_NAME,
                                workId,
                                parentId,
                                work)
                        work_list_info_item = {'id': workId, 'attributes': [], 'titles': works, 'parent': parentId}
                        work_list_info.append(work_list_info_item)
            if self.INFO:
                log.info('work_list_info: %s', work_list_info)
            # we now have a list of items, where the id of each is a work id for the track or (multiple instances of) the recording id (for partial works)
            # we need to turn this into a usable hierarchy - i.e. just one item
            workId_list = []
            work_list = []
            parent_list = []
            attribute_list = []
            workId_list_p = []
            work_list_p = []
            attribute_list_p = []
            for w in work_list_info:
                if 'partial' not in w['attributes'] or not options[
                    'cwp_partial']:  # just do the bottom-level 'works' first
                    workId_list.append(w['id'])
                    work_list += w['titles']
                    attribute_list += w['attributes']
                    if 'parent' in w:
                        if w['parent'] not in parent_list:  # avoid duplicating parents!
                            parent_list.append(w['parent'])
                else:
                    workId_list_p.append(w['id'])
                    work_list_p += w['titles']
                    attribute_list_p += w['attributes']
            # de-duplicate work names
            work_list = list(collections.OrderedDict.fromkeys(work_list)) # list(set()) won't work as need to retain order
            work_list_p =  list(collections.OrderedDict.fromkeys(work_list_p))

            workId_tuple = tuple(workId_list)
            workId_tuple_p = tuple(workId_list_p)
            if workId_tuple not in self.parts or not self.USE_CACHE:
                self.parts[workId_tuple]['name'] = work_list
                if workId_tuple not in self.work_listing[album]:
                    self.work_listing[album].append(workId_tuple)
                if parent_list:
                    if workId_tuple in self.works_cache:
                        self.works_cache[workId_tuple] += parent_list
                        self.parts[workId_tuple]['parent'] += parent_list
                    else:
                        self.works_cache[workId_tuple] = parent_list
                        self.parts[workId_tuple]['parent'] = parent_list
                    self.parts[workId_tuple_p]['name'] = work_list_p
                    if workId_tuple_p not in self.work_listing[album]:
                        self.work_listing[album].append(workId_tuple_p)

                if 'medley' in attribute_list_p:
                    self.parts[workId_tuple_p]['medley'] = True

                if 'medley' in attribute_list:
                    self.parts[workId_tuple]['medley'] = True

                if partial:
                    self.parts[workId_tuple]['partial'] = True

            self.trackback[album][workId_tuple]['id'] = workId_list
            if 'meta' in self.trackback[album][workId_tuple]:
                if (track,
                    album) not in self.trackback[album][workId_tuple]['meta']:
                    self.trackback[album][workId_tuple]['meta'].append(
                        (track, album))
            else:
                self.trackback[album][workId_tuple]['meta'] = [(track, album)]
            if self.DEBUG:
                log.debug(
                    "Trackback for recording of %s is %s. Partial = %s",
                    work,
                    self.trackback[album][workId_tuple],
                    partial)
            if workId_tuple in self.parts and 'arrangers' in self.parts[workId_tuple] and self.USE_CACHE:
                if self.DEBUG:
                    log.debug(
                        "%s GETTING ARRANGERS FROM CACHE", PLUGIN_NAME)
                self.set_arranger(
                    album, track, self.parts[workId_tuple]['arrangers'], track_metadata)
            if workId_tuple in self.works_cache and (self.USE_CACHE or partial):
                if self.DEBUG:
                    log.debug(
                        "%s: GETTING WORK METADATA FROM CACHE",
                        PLUGIN_NAME)  # debug

                not_in_cache = self.check_cache(workId_tuple, [])
            else:
                if partial:
                    not_in_cache = [workId_tuple_p]
                else:
                    not_in_cache = [workId_tuple]
            for workId_tuple in not_in_cache:
                self.work_not_in_cache(album, track, workId_tuple)

        else:  # no work relation
            if self.WARNING:
                log.warning(
                    "%s: WARNING - no works for this track: \"%s\"",
                    PLUGIN_NAME,
                    title)
            self.append_tag(
                track_metadata,
                '~cwp_warning',
                'No works for this track')
            self.publish_metadata(album, track)

        # last track
        if self.DEBUG:
            log.debug('%s, Check for last track. Requests = %s, Tracknumber = %s, Totaltracks = %s', PLUGIN_NAME,
                      album._requests, track_metadata['tracknumber'], track_metadata['totaltracks'])
        if album._requests == 0 and track_metadata['tracknumber'] == track_metadata['totaltracks']:
            self.process_album(album)

    def check_cache(self, workId_tuple, not_in_cache):
        parentId_tuple = tuple(self.works_cache[workId_tuple])
        if parentId_tuple in self.works_cache:
            self.check_cache(parentId_tuple, not_in_cache)
        else:
            not_in_cache.append(parentId_tuple)
        return not_in_cache

    def work_not_in_cache(self, album, track, workId_tuple):
        if 'no_parent' in self.parts[workId_tuple] and (self.USE_CACHE or self.options[track]["cwp_use_sk"]) \
                and self.parts[workId_tuple]['no_parent']:
            self.top_works[(track, album)]['workId'] = workId_tuple
            if album in self.top:
                if workId_tuple not in self.top[album]:
                    self.top[album].append(workId_tuple)
            else:
                self.top[album] = [workId_tuple]
        else:
            # if partial and not self.USE_CACHE:
            #     # workId will not have been updated if cache turned off
            #     workId = true_workId
            for workId in workId_tuple:
                self.work_add_track(album, track, workId, 0)

    def work_add_track(self, album, track, workId, tries):
        if self.DEBUG:
            log.debug("%s: ADDING WORK TO LOOKUP QUEUE", PLUGIN_NAME)
        self.album_add_request(album)
        # to change the _requests variable to indicate that there are pending
        # requests for this item and delay Picard from finalizing the album
        if self.DEBUG:
            log.debug(
                "%s: Added lookup request for id %s. Requests = %s",
                PLUGIN_NAME,
                workId,
                album._requests)
        if self.works_queue.append(
                workId,
                (track,
                 album)):  # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            queryargs = {"inc": "work-rels+artist-rels"}
            if self.DEBUG:
                log.debug(
                    "%s: Initiating XML lookup for %s......",
                    PLUGIN_NAME,
                    workId)
            return album.tagger.xmlws.get(
                host,
                port,
                path,
                partial(
                    self.work_process,
                    workId,
                    tries),
                xml=True,
                priority=True,
                important=False,
                queryargs=queryargs)
        else:
            if self.DEBUG:
                log.debug(
                    "%s: Work is already in queue: %s",
                    PLUGIN_NAME,
                    workId)

    def work_process(self, workId, tries, response, reply, error):
        if self.DEBUG:
            log.debug(
                "%s: work_process. LOOKING UP WORK: %s",
                PLUGIN_NAME,
                workId)
        if error:
            if self.WARNING:
                log.warning(
                    "%s: %r: Network error retrieving work record",
                    PLUGIN_NAME,
                    workId)
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                if self.DEBUG:
                    log.debug(
                        "%s: Removed request after network error. Requests = %s",
                        PLUGIN_NAME,
                        album._requests)
                if tries < self.MAX_RETRIES:
                    if self.DEBUG:
                        log.debug("REQUEUEING...")
                    self.work_add_track(album, track, workId, tries + 1)
                else:
                    if self.ERROR:
                        log.error(
                            "%s: EXHAUSTED MAX RE-TRIES for XML lookup for track %s",
                            PLUGIN_NAME,
                            track)
                    track.metadata[
                        '~cwp_error'] = "ERROR: MISSING METADATA due to network errors. Re-try or fix manually."
                self.album_remove_request(album)
            return
        tuples = self.works_queue.remove(workId)
        for track, album in tuples:
            if self.DEBUG:
                log.debug("%s Requests = %s", PLUGIN_NAME, album._requests)
        if self.INFO:
            log.info("RESPONSE = %s", response)
        # find the id_tuple(s) key with workId in it
        wid_list = []
        for w in self.work_listing[album]:
            if workId in w and w not in wid_list:
                wid_list.append(w)
        if self.INFO:
            log.info('wid_list for %s is %s', workId, wid_list)
        if self.INFO:
            log.info('self.parts: %s', self.parts)
        for wid in wid_list:  # wid is a tuple
            metaList = self.work_process_metadata(workId, wid, tuples, response)
            parentList = metaList[0]
            # returns [parent id, parent name] or None if no parent found
            arrangers = metaList[1]
            if wid in self.parts:

                if arrangers:
                    self.parts[wid]['arrangers'] = arrangers
                    for track, album in tuples:
                        tm = track.metadata
                        self.set_arranger(album, track, arrangers, tm)
                if parentList:
                    parentIds = parentList[0]
                    parents = parentList[1]
                    if self.INFO:
                        log.info('Parents - ids: %s, names: %s', parentIds, parents)
                    if parentIds:
                        if wid in self.works_cache:
                            prev_ids = tuple(self.works_cache[wid])
                            prev_name = self.parts[prev_ids]['name']
                            add_list_uniquely(self.works_cache[wid], parentIds)
                            add_list_uniquely(self.parts[wid]['parent'], parentIds)
                            index = self.work_listing[album].index(prev_ids)
                            new_id_list = add_list_uniquely(list(prev_ids), parentIds)
                            new_ids = tuple(new_id_list)
                            self.work_listing[album][index] = new_ids
                            self.parts[new_ids] = self.parts[prev_ids]
                            del self.parts[prev_ids]
                            self.parts[new_ids]['name'] = add_list_uniquely(prev_name, parents)
                            parentIds = new_id_list

                        else:
                            self.works_cache[wid] = parentIds
                            self.parts[wid]['parent'] = parentIds
                            self.parts[tuple(parentIds)]['name'] = parents
                            self.work_listing[album].append(tuple(parentIds))

                        # de-duplicate the parent names
                            self.parts[tuple(parentIds)]['name'] = \
                                list(collections.OrderedDict.fromkeys(self.parts[tuple(parentIds)]['name']))
                            # list(set()) won't work as need to retain order
                        if self.DEBUG:
                            log.debug('%s: added parent ids to work_listing: %s, [Requests = %s]', PLUGIN_NAME,
                                      parentIds, album._requests)
                        if self.INFO:
                            log.info('work_listing: %s', self.work_listing[album])
                        for parentId in parentIds:
                            for track, album in tuples:
                                self.work_add_track(album, track, parentId, 0)
                    else:
                        # so we remember we looked it up and found none
                        self.parts[wid]['no_parent'] = True
                        self.top_works[(track, album)]['workId'] = wid
                        if wid not in self.top[album]:
                            self.top[album].append(wid)
                        if self.INFO:
                            log.info("TOP[album]: %s", self.top[album])
                else:  # ERROR?
                    # so we remember we looked it up and found none
                    self.parts[wid]['no_parent'] = True
                    self.top_works[(track, album)]['workId'] = wid
                    self.top[album].append(wid)
        for track, album in tuples:
            if album._requests == 1:  # Next remove will finalise album
                # so do the final album-level processing before we go!
                self.process_album(album)
            self.album_remove_request(album)
            if self.DEBUG:
                log.debug(
                    "%s: Removed request. Requests = %s",
                    PLUGIN_NAME,
                    album._requests)
        if self.DEBUG:
            log.debug(
                "%s: End of work_process for workid %s",
                PLUGIN_NAME,
                workId)

    def work_process_metadata(self, workId, wid, tuples, response):
        if self.DEBUG:
            log.debug("%s: In work_process_metadata", PLUGIN_NAME)
        relation_list = []
        log_options = {'log_debug': self.DEBUG, 'log_info': self.INFO}
        if 'metadata' in response.children:
            if 'work' in response.metadata[0].children:
                relation_list = parse_data(log_options, response.metadata[0].work, [], 'relation_list')
                for track, _ in tuples:
                    rep_track = track  # Representative track for option ident only
                return self.work_process_relations(rep_track, workId, wid, relation_list)

            else:
                if self.ERROR:
                    log.error(
                        "%s: %r: MusicBrainz work xml result not in correct format - %s",
                        PLUGIN_NAME,
                        workId,
                        response)
                for track, _ in tuples:  # album not currently used
                    tm = track.metadata
                    self.append_tag(
                        tm,
                        '~cwp_error',
                        'MusicBrainz work xml result not in correct format for work id: ' +
                        str(workId))
        return None

    def work_process_relations(self, track, workId, wid, relations):
        # nb track is just the last track for this work - used as being representative for options identification
        if self.DEBUG:
            log.debug(
                "%s In work_process_relations. Relations--> %s",
                PLUGIN_NAME,
                relations)
        options = self.options[track]
        log_options = {'log_debug': self.DEBUG, 'log_info': self.INFO}
        new_workIds = []
        new_works = []
        artists = []
        relation_attribute = parse_data(log_options, relations, [], 'attribs.target_type:work', 'relation',
                                        'attribs.type:parts', 'direction.text:backward', 'attribute_list', 'attribute',
                                        'text')
        if 'part of collection' not in relation_attribute or options['cwp_collections']:
            new_work_list = parse_data(log_options, relations, [], 'attribs.target_type:work', 'relation',
                                       'attribs.type:parts', 'direction.text:backward', 'work')
        else:
            new_work_list = []
        if new_work_list:
            new_workIds = parse_data(log_options, new_work_list, [], 'attribs', 'id')
            new_works = parse_data(log_options, new_work_list, [], 'title', 'text')
        else:
            arrangement_of = parse_data(log_options, relations, [], 'attribs.target_type:work', 'relation',
                                        'attribs.type:arrangement', 'direction.text:backward', 'work')
            if arrangement_of and options['cwp_arrangements']:
                new_workIds = parse_data(log_options, arrangement_of, [], 'attribs', 'id')
                new_works = parse_data(log_options, arrangement_of, [], 'title', 'text')
                self.parts[wid]['arrangement'] = True
            else:
                medley_of = parse_data(log_options, relations, [], 'attribs.target_type:work', 'relation',
                                       'attribs.type:medley', 'work')
                direction = parse_data(log_options, relations, [], 'attribs.target_type:work', 'relation',
                                       'attribs.type:medley', 'direction', 'text')
                if 'backward' not in direction:
                    if self.DEBUG:
                        log.debug('%s: medley_of: %s', PLUGIN_NAME, medley_of)
                    if medley_of and options['cwp_medley']:
                        medley_list = []
                        for medley_item in medley_of:
                            medley_list = medley_list + parse_data(log_options, medley_item, [], 'title', 'text')
                            # (parse_data is a list...)
                            if self.INFO:
                                log.info('medley_list: %s', medley_list)
                        self.parts[wid]['medley_list'] = medley_list

        if self.INFO:
            log.info('New works: ids: %s, names: %s', new_workIds, new_works)
        artist_types = ['arranger', 'instrument arranger', 'orchestrator', 'composer']
        for artist_type in artist_types:
            type_list = parse_data(log_options, relations, [], 'attribs.target_type:artist', 'relation',
                                   'attribs.type:' + artist_type)
            if type_list:
                artist_name_list = parse_data(log_options, type_list, [],
                                              'direction.text:backward', 'artist', 'name', 'text')
                artist_sort_name_list = parse_data(log_options, type_list, [],
                                                   'direction.text:backward', 'artist', 'sort_name', 'text')
                if artist_type in ['arranger', 'composer', 'orchestrator']:
                    instrument_list = artist_type
                else:
                    instrument_list = parse_data(log_options, type_list, [],
                                                 'direction.text:backward', 'attribute_list', 'attribute', 'text')
                for i, artist_name in enumerate(artist_name_list):
                    artist = (instrument_list, artist_name, artist_sort_name_list[i])
                    artists.append(artist)
        if self.INFO:
            log.info("ARTISTS %s", artists)

        workItems = (new_workIds, new_works)
        itemsFound = [workItems, artists]
        return itemsFound

    def set_arranger(self, album, track, arrangerList, tm):
        options = self.options[track]
        orchestratorList = []
        for arranger in arrangerList:
            instrument = arranger[0]
            if isinstance(instrument, list):
                instrument = '; '.join(instrument)
            name = arranger[1]
            orig_name = arranger[1]
            sort_name = arranger[2]
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))

            if instrument == 'orchestrator':
                orchestratorList.append([instrument, name, sort_name])
                continue
            if instrument == 'composer':
                self.append_tag(tm, '~cea_composers', name)
                self.append_tag(tm, '~cwp_composers', name)
                continue
            if instrument != 'arranger':
                instrument_text = ' (' + instrument + ')'
            else:
                instrument_text = ""
            for tag in ['~cea_arrangers', '~cwp_arrangers']:
                if tag in tm:
                    if name not in tm[tag] and orig_name not in tm[tag]:
                        self.append_tag(tm, tag, name + instrument_text)
                else:
                    tm[tag] = name + instrument_text
            if options['cea_arrangers']:
                if instrument != 'arranger':
                    self.append_tag(tm, 'arranger:' + instrument, name)
                    # (Only necessary to add instrument arrangers as Picard already has "plain" arrangers)
        if orchestratorList:
            self.set_orchestrator(album, track, orchestratorList, tm)

    def set_orchestrator(self, album, track, orchestratorList, tm):
        options = self.options[track]
        if isinstance(tm['arranger'], basestring):
            arrangerList = tm['arranger'].split(';')
        else:
            arrangerList = tm['arranger']
        newList = arrangerList
        orch_name_list = []
        for orchestrator in orchestratorList:
            name = orchestrator[1]
            orch_name_list.append(name)
            sort_name = orchestrator[2]
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            if options['cea_orchestrator'] != "":
                details = name + ' (' + options['cea_orchestrator'] + ')'
            else:
                details = name
            if '~cea_orchestrators' in tm:
                if name not in tm['~cea_orchestrators']:
                    tm['~cea_orchestrators'] = tm['~cea_orchestrators'] + '; ' + name
            else:
                tm['~cea_orchestrators'] = name
            appendList = []
            for index, arranger in enumerate(arrangerList):
                if name in arranger:
                    newList[index] = details
                else:
                    appendList.append(details)
            for append_item in appendList:
                newList.append(append_item)
        if options['cea_orchestrator'] != "":
            self.append_tag(
                tm,
                'arranger:orchestrator',
                "; ".join(orch_name_list))
            # next bit is needed as Picard does not currently write out
            # arranger:instrument tag in the same way as performer:instrument
            # -i.e. it is not included in main arranger tag
            tm['~cwp_arrangers'] = newList

    def album_add_request(self, album):
        album._requests += 1
        if self.INFO:
            log.info("album requests: %s", album._requests)

    def album_remove_request(self, album):
        album._requests -= 1
        if self.INFO:
            log.info("album requests: %s", album._requests)
        album._finalize_loading(None)

    ##################################################
    # SECTION 2 - Organise tracks and works in album #
    ##################################################

    def process_album(self, album):
        if self.DEBUG:
            log.debug("%s: PROCESS ALBUM %s", PLUGIN_NAME, album)
        # populate the inverse hierarchy
        if self.INFO:
            log.info("%s: Cache: %s", PLUGIN_NAME, self.works_cache)
        if self.INFO:
            log.info("%s: Work listing %s", PLUGIN_NAME, self.work_listing)
        for workId in self.parts:  # NB workId is a tuple
            if tuple(workId) in self.work_listing[album]:
                topId = None
                if self.INFO:
                    log.info('Works_cache: %s', self.works_cache)
                if workId in self.works_cache:
                    parentIds = tuple(self.works_cache[workId])
                    # for parentId in parentIds:
                    if self.DEBUG:
                        log.debug("%s: create inverses: %s, %s",
                                  PLUGIN_NAME, workId, parentIds)
                    if parentIds in self.partof:
                        if workId not in self.partof[parentIds]:
                            self.partof[parentIds].append(workId)
                    else:
                        self.partof[parentIds] = [workId]
                    if self.DEBUG:
                        log.debug(
                            "%s: Partof: %s",
                            PLUGIN_NAME,
                            self.partof[parentIds])
                    if 'no_parent' in self.parts[parentIds]:
                        # to handle case if album includes works already in
                        # cache from a different album
                        if self.parts[parentIds]['no_parent']:
                            topId = parentIds
                else:
                    topId = workId
                if topId:
                    if album in self.top:
                        if topId not in self.top[album]:
                            self.top[album].append(topId)
                    else:
                        self.top[album] = [topId]
        # work out the full hierarchy and part levels
        height = 0
        if self.INFO:
            log.info(
                "%s: TOP: %s, \nALBUM: %s, \nTOP[ALBUM]: %s",
                PLUGIN_NAME,
                self.top,
                album,
                self.top[album])
        if self.INFO:
            log.info('top[album]: %s', self.top[album])
        if len(self.top[album]) > 1:
            single_work_album = 0
        else:
            single_work_album = 1
        for topId in self.top[album]:
            self.create_trackback(album, topId)
            if self.INFO:
                log.info(
                    "Top id = %s, Name = %s",
                    topId,
                    self.parts[topId]['name'])

            if self.INFO:
                log.info(
                    "Trackback before levels: %s",
                    self.trackback[album][topId])
            if self.INFO:
                log.info(
                    "Trackback before levels: %s",
                    self.trackback[album][topId])
            work_part_levels = self.level_calc(
                self.trackback[album][topId], height)
            if self.INFO:
                log.info(
                    "Trackback after levels: %s",
                    self.trackback[album][topId])
            if self.INFO:
                log.info(
                    "Trackback after levels: %s",
                    self.trackback[album][topId])
            # determine the level which will be the principal 'work' level
            if work_part_levels >= 3:
                ref_level = work_part_levels - single_work_album
            else:
                ref_level = work_part_levels
            # extended metadata scheme won't display more than 3 work levels
            # ref_level = min(3, ref_level)
            ref_height = work_part_levels - ref_level
            top_info = {
                'levels': work_part_levels,
                'id': topId,
                'name': self.parts[topId]['name'],
                'single': single_work_album}
            # set the metadata in sequence defined by the work structure
            answer = self.process_trackback(
                album, self.trackback[album][topId], ref_height, top_info)
            if answer:
                tracks = answer[1]['track']
                if self.INFO:
                    log.info("TRACKS: %s", tracks)
                work_part_levels = self.trackback[album][topId]['depth']
                for track in tracks:
                    track_meta = track[0]
                    tm = track_meta.metadata
                    title_work_levels = 0
                    if '~cwp_title_work_levels' in tm:
                        title_work_levels = int(tm['~cwp_title_work_levels'])
                    self.extend_metadata(
                        top_info,
                        track_meta,
                        ref_height,
                        title_work_levels)  # revise for new data
                    self.publish_metadata(album, track_meta)
                if self.DEBUG:
                    log.debug(
                        "%s FINISHED TRACK PROCESSING FOR Top work id: %s",
                        PLUGIN_NAME,
                        topId)
        if self.INFO:
            log.info('Self.parts: %s', self.parts)
        if self.INFO:
            log.info('Self.trackback: %s', self.trackback)
        self.trackback[album].clear()

    def create_trackback(self, album, parentId):
        if self.DEBUG:
            log.debug("%s: Create trackback for %s", PLUGIN_NAME, parentId)
        if parentId in self.partof:  # NB parentId is a tuple
            for child in self.partof[parentId]:  # NB child is a tuple
                if child in self.partof:
                    child_trackback = self.create_trackback(album, child)
                    self.append_trackback(album, parentId, child_trackback)
                else:
                    self.append_trackback(
                        album, parentId, self.trackback[album][child])
            return self.trackback[album][parentId]
        else:
            return self.trackback[album][parentId]

    def append_trackback(self, album, parentId, child):
        if self.DEBUG:
            log.debug("In append_trackback...")
        if parentId in self.trackback[album]:  # NB parentId is a tuple
            if 'children' in self.trackback[album][parentId]:
                if child not in self.trackback[album][parentId]['children']:
                    if self.DEBUG:
                        log.debug("TRYING TO APPEND...")
                    self.trackback[album][parentId]['children'].append(child)
                    if self.DEBUG:
                        log.debug("...PARENT %s - ADDED %s as child",
                                  self.parts[parentId]['name'], child)
                else:
                    if self.DEBUG:
                        log.debug(
                            "Parent %s already has %s as child", parentId, child)
            else:
                self.trackback[album][parentId]['children'] = [child]
                if self.DEBUG:
                    log.debug(
                        "Existing PARENT %s - ADDED %s as child",
                        self.parts[parentId]['name'],
                        child)
        else:
            self.trackback[album][parentId]['id'] = parentId
            self.trackback[album][parentId]['children'] = [child]
            if self.DEBUG:
                log.debug("New PARENT %s - ADDED %s as child",
                          self.parts[parentId]['name'], child)
            if self.INFO:
                log.info(
                    "APPENDED TRACKBACK: %s",
                    self.trackback[album][parentId])
        return self.trackback[album][parentId]

    def level_calc(self, trackback, height):
        if 'children' not in trackback:
            if self.INFO:
                log.info("Got to bottom")
            trackback['height'] = height
            trackback['depth'] = 0
            return 0
        else:
            trackback['height'] = height
            height += 1
            max_depth = 0
            for child in trackback['children']:
                if self.DEBUG:
                    log.debug("CHILD: %s", child)
                depth = self.level_calc(child, height) + 1
                if self.DEBUG:
                    log.debug("DEPTH: %s", depth)
                max_depth = max(depth, max_depth)
            trackback['depth'] = max_depth
            return max_depth

        ###########################################
        # SECTION 3 - Process tracks within album #
        ###########################################

    def process_trackback(self, album_req, trackback, ref_height, top_info):
        if self.DEBUG:
            log.debug(
                "%s: IN PROCESS_TRACKBACK. Trackback = %s",
                PLUGIN_NAME,
                trackback)
        tracks = collections.defaultdict(dict)
        process_now = False
        if 'meta' in trackback:
            for track, album in trackback['meta']:
                if album_req == album:
                    process_now = True
        if process_now or 'children' not in trackback:
            if 'meta' in trackback and 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                if self.DEBUG:
                    log.debug("Processing level 0")
                depth = trackback['depth']
                height = trackback['height']
                workId = tuple(trackback['id'])
                if self.INFO:
                    log.info("WorkId %s", workId)
                if self.INFO:
                    log.info("Work name %s", self.parts[workId]['name'])
                for track, album in trackback['meta']:
                    if album == album_req:
                        if self.INFO:
                            log.info("Track: %s", track)
                        tm = track.metadata
                        if self.INFO:
                            log.info("Track metadata = %s", tm)
                        tm['~cwp_workid_' + str(depth)] = workId
                        # strip leading and trailing spaces from work names
                        if isinstance(self.parts[workId]['name'], basestring):
                            worktemp = self.parts[workId]['name'].strip()
                        else:
                            for index, it in enumerate(
                                    self.parts[workId]['name']):
                                self.parts[workId]['name'][index] = it.strip()
                            worktemp = self.parts[workId]['name']
                        if isinstance(top_info['name'], basestring):
                            toptemp = top_info['name'].strip()
                        else:
                            for index, it in enumerate(top_info['name']):
                                top_info['name'][index] = it.strip()
                            toptemp = top_info['name']
                        tm['~cwp_work_' + str(depth)] = worktemp
                        tm['~cwp_part_levels'] = height
                        tm['~cwp_work_part_levels'] = top_info['levels']
                        tm['~cwp_workid_top'] = top_info['id']
                        tm['~cwp_work_top'] = toptemp
                        tm['~cwp_single_work_album'] = top_info['single']
                        if self.INFO:
                            log.info("Track metadata = %s", tm)
                        if 'track' in tracks:
                            tracks['track'].append((track, height))
                        else:
                            tracks['track'] = [(track, height)]
                        if self.INFO:
                            log.info("Tracks: %s", tracks)
                response = (workId, tracks)
                if self.DEBUG:
                    log.debug("%s: LEAVING PROCESS_TRACKBACK", PLUGIN_NAME)
                if self.INFO:
                    log.info("depth %s Response = %s", depth, response)
                return response
            else:
                return None
        else:
            if 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                depth = trackback['depth']
                height = trackback['height']
                parentId = trackback['id']
                parent = self.parts[parentId]['name']
                width = 0
                for child in trackback['children']:
                    width += 1
                    if self.INFO:
                        log.info("child trackback = %s", child)
                    answer = self.process_trackback(
                        album_req, child, ref_height, top_info)
                    if answer:
                        workId = answer[0]
                        child_tracks = answer[1]['track']
                        for track in child_tracks:
                            track_meta = track[0]
                            track_height = track[1]
                            part_level = track_height - height
                            if self.DEBUG:
                                log.debug(
                                    "%s: Calling set metadata %s",
                                    PLUGIN_NAME,
                                    (part_level,
                                     workId,
                                     parentId,
                                     parent,
                                     track_meta))
                            self.set_metadata(
                                part_level, workId, parentId, parent, track_meta)
                            if 'track' in tracks:
                                tracks['track'].append(
                                    (track_meta, track_height))
                            else:
                                tracks['track'] = [(track_meta, track_height)]
                            tm = track_meta.metadata
                            # ~cwp_title if composer had to be removed
                            title = tm['~cwp_title'] or tm['title']
                            if self.DEBUG:
                                log.debug("TITLE: %s", title)
                            if 'title' in tracks:
                                tracks['title'].append(title)
                            else:
                                tracks['title'] = [title]
                            work = tm['~cwp_work_0']
                            if 'work' in tracks:
                                tracks['work'].append(work)
                            else:
                                tracks['work'] = [work]
                            if 'tracknumber' not in tm:
                                tm['tracknumber'] = 0
                            if 'tracknumber' in tracks:
                                tracks['tracknumber'].append(
                                    int(tm['tracknumber']))
                            else:
                                tracks['tracknumber'] = [
                                    int(tm['tracknumber'])]
                if tracks and 'track' in tracks:
                    track = tracks['track'][0][0]
                    # NB this will only be the first track of tracks, but its options will be used for the structure
                    self.derive_from_structure(top_info, tracks, height, depth, width, 'title')
                    if self.options[track]["cwp_level0_works"]:
                        # replace hierarchical works with those from work_0 (for
                        # consistency)
                        self.derive_from_structure(
                            top_info, tracks, height, depth, width, 'work')

                    if self.DEBUG:
                        log.debug("Trackback result for %s = %s", parentId, tracks)
                    response = parentId, tracks
                    if self.DEBUG:
                        log.debug(
                            "%s LEAVING PROCESS_TRACKBACK depth %s Response = %s",
                            PLUGIN_NAME,
                            depth,
                            response)
                    return response
                else:
                    return None
            else:
                return None

    def derive_from_structure(
            self,
            top_info,
            tracks,
            height,
            depth,
            width,
            name_type):
        topId = top_info['id']
        if 'track' in tracks:
            track = tracks['track'][0][0]
            single_work_track = False  # default
            if self.DEBUG:
                log.debug("%s: Deriving info for %s from structure for tracks %s", PLUGIN_NAME, name_type, tracks['track'])
            if 'tracknumber' in tracks:
                sorted_tracknumbers = sorted(tracks['tracknumber'])
            else:
                sorted_tracknumbers = None
            if self.INFO:
                log.info("SORTED TRACKNUMBERS: %s", sorted_tracknumbers)
            common_len = 0
            common_subset = None
            if name_type in tracks:
                meta_str = "_title" if name_type == 'title' else "_X0"
                name_list = tracks[name_type]
                if self.DEBUG:
                    log.debug("%s list %s", name_type, name_list)
                # only one track in this work so try and extract using colons
                if len(name_list) == 1:
                    single_work_track = True
                    track_height = tracks['track'][0][1]
                    if track_height - height > 0:  # part_level
                        if name_type == 'title':
                            if self.DEBUG:
                                log.debug(
                                    "Single track work. Deriving directly from title text: %s", track)
                            tm = track.metadata
                            mb = tm['~cwp_work_0']
                            ti = name_list[0]
                            diff = self.diff_pair(track, tm, mb, ti)
                            if diff:
                                common_subset = self.derive_from_title(track, diff)[
                                    0]
                        else:
                            common_subset = ""
                            common_len = 0
                    else:
                        common_subset = name_list[0]
                    if self.INFO:
                        log.info(
                            "%s is single-track work. common_subset is set to %s",
                            tracks['track'][0][0],
                            common_subset)
                    if common_subset:
                        common_len = len(common_subset)
                    else:
                        common_len = 0
                else:
                    compare = name_list[0].split()
                    for name in name_list:
                        lcs = longest_common_sequence(compare, name.split())
                        compare = lcs['sequence']
                        if not compare:
                            common_subset = None
                            common_len = 0
                            break
                        if lcs['length'] > 0:
                            common_subset = " ".join(compare)
                            if self.INFO:
                                log.info(
                                    "Common subset from %ss at level %s, item name %s ..........",
                                    name_type,
                                    tracks['track'][0][1] - height,
                                    name)
                            if self.INFO:
                                log.info("..........is %s", common_subset)
                            common_len = len(common_subset)

                if self.DEBUG:
                    log.debug(
                        "checked for common sequence - length is %s",
                        common_len)
            for i, track_item in enumerate(tracks['track']):
                track_meta = track_item[0]
                tm = track_meta.metadata
                top_level = int(tm['~cwp_part_levels'])
                part_level = track_item[1] - height
                if common_len > 0:
                    if self.INFO:
                        log.info(
                            "Use %s info for track: %s",
                            name_type,
                            track_meta)
                    name = tracks[name_type][i]
                    work = name[:common_len]
                    work = work.rstrip(":,.;- ")
                    removewords = self.options[track]["cwp_removewords"].split(',')
                    if self.DEBUG:
                        log.debug(
                            "Removewords (in %s) = %s",
                            name_type,
                            removewords)
                    for prefix in removewords:
                        prefix2 = str(prefix).lower().rstrip()
                        if prefix2[0] != " ":
                            prefix2 = " " + prefix2
                        if self.DEBUG:
                            log.debug("checking prefix %s", prefix2)
                        if work.lower().endswith(prefix2):
                            if len(prefix2) > 0:
                                work = work[:-len(prefix2)]
                                common_len = len(work)
                                work = work.rstrip(":,.;- ")
                    if self.INFO:
                        log.info("work after prefix strip %s", work)
                    if self.DEBUG:
                        log.debug("Prefixes checked")

                    tm['~cwp' + meta_str + '_work_' + str(part_level)] = work

                    if part_level > 0 and name_type == "work":
                        if work == tm['~cwp' + meta_str +
                                '_work_' + str(part_level - 1)]:
                            # repeated name - so use hierarchy instead
                            tm['~cwp' + meta_str + '_work_' + str(part_level)] = tm['~cwp_work_' + str(part_level)]
                            tm['~cwp' + meta_str + '_part_' + str(part_level - 1)] = \
                                self.strip_parent_from_work(tm['~cwp' + meta_str + '_work_' + str(part_level - 1)],
                                                            tm['~cwp_work_' + str(part_level)], part_level, True)[0]
                            self.level0_warn(tm, part_level)
                        else:
                            if '~cwp' + meta_str + '_work_' + str(part_level - 1) in tm and tm['~cwp' + meta_str + '_work_' + str(part_level - 1)]:
                                tm['~cwp' + meta_str + '_part_' + str(part_level - 1)] = \
                                    self.strip_parent_from_work(tm['~cwp' + meta_str + '_work_' + str(part_level - 1)],
                                                                work, part_level, True)[0]
                        # top-down action
                        for level in reversed(range(0, part_level)):  # fix lower levels for lack of breaks
                            if self.INFO:
                                log.info('level = %s', level)
                            if '~cwp' + meta_str + '_work_' + str(level) not in tm:
                                if level == 0:
                                    tm['~cwp' + meta_str + '_work_' + str(level)] = tm['~cwp' + '_work_' + str(level)]
                                    tm['~cwp' + meta_str + '_part_' + str(level)] = \
                                        self.strip_parent_from_work(tm['~cwp' + meta_str + '_work_' + str(level)],
                                                                    tm['~cwp' + meta_str + '_work_' + str(level + 1)],
                                                                    level, True)[0]
                                else:
                                    tm['~cwp' + meta_str + '_work_' + str(level)] = tm['~cwp_work_' + str(level)]
                                    self.level0_warn(tm, level)
                                    tm['~cwp' + meta_str + '_part_' + str(level)] =  \
                                        self.strip_parent_from_work(tm['~cwp' + meta_str + '_work_' + str(level)],
                                                                    tm['~cwp' + meta_str + '_work_' + str(level + 1)],
                                                                    level, True)[0]

                    if part_level == 1:
                        movt = name[common_len:].strip().lstrip(":,.;- ")
                        if self.INFO:
                            log.info("%s - movt = %s", name_type, movt)
                        tm['~cwp' + meta_str + '_part_0'] = movt
                    if self.INFO:
                        log.info(
                            "%s Work part_level = %s",
                            name_type,
                            part_level)
                    if name_type == 'title':
                        if '~cwp_title_work_' + str(part_level - 1) in tm and tm['~cwp_title_work_' + str(
                                part_level)] == tm['~cwp_title_work_' + str(part_level - 1)] and width == 1:
                            pass  # don't count higher part-levels which are not distinct from lower ones when the parent work has only one child
                        else:
                            tm['~cwp_title_work_levels'] = depth
                            tm['~cwp_title_part_levels'] = part_level
                    if self.DEBUG:
                        log.debug("Set new metadata for %s OK", name_type)
                else:
                    if self.INFO:
                        log.info('single track work - indicator = %s. track = %s, part_level = %s, top_level = %s',
                              single_work_track,
                              track_item,
                              part_level, top_level)
                    if  part_level >= top_level:  # so it won't be covered by top-down action
                        if name_type == 'work':
                            for level in range(0, part_level +1 ):  # fill in the missing work names from the canonical list
                                if '~cwp' + meta_str + '_work_' + str(level) not in tm:
                                    tm['~cwp' + meta_str + '_work_' + str(level)] = tm['~cwp_work_' + str(level)]
                                if '~cwp' + meta_str + '_part_' + str(level) not in tm and '~cwp_part_' + str(level) in tm:
                                    tm['~cwp' + meta_str + '_part_' + str(level)] = tm['~cwp_part_' + str(level)]
                                    if level > 0:
                                        self.level0_warn(tm, level)

                # set movement number
                if name_type == 'title':  # so we only do it once
                    if part_level == 1:
                        if sorted_tracknumbers:
                            curr_num = tracks['tracknumber'][i]
                            posn = sorted_tracknumbers.index(curr_num) + 1
                            if self.INFO:
                                log.info("posn %s", posn)
                        else:
                            posn = i + 1
                        tm['~cwp_movt_num'] = str(posn)

    def level0_warn(self, tm, level):
        if self.WARNING:
            log.warning('%s: Unable to use level 0 as work name source in level %s - using hierarchy instead',
                        PLUGIN_NAME, level)
            self.append_tag(tm, '~cwp_warning', 'Unable to use level 0 as work name source in level ' + str(
                level) + ' - using hierarchy instead')

    def set_metadata(self, part_level, workId, parentId, parent, track):
        if self.DEBUG:
            log.debug(
                "%s: SETTING METADATA FOR TRACK = %r, parent = %s, part_level = %s",
                PLUGIN_NAME,
                track,
                parent,
                part_level)
        tm = track.metadata
        if parentId:
            # if not isinstance(parent, basestring):
            #     parent = "; ".join(parent)
            tm['~cwp_workid_' + str(part_level)] = parentId
            tm['~cwp_work_' + str(part_level)] = parent
            # maybe more than one work name
            work = self.parts[workId]['name']
            if self.DEBUG:
                log.debug("Set work name to: %s", work)
            works = []
            # in case there is only one and it isn't in a list
            if isinstance(work, basestring):
                works.append(work)
            else:
                works = work[:]
            stripped_works = []
            for work in works:
                # partials (and often) arrangements will have the same name as the "parent" and not be an extension
                if 'arrangement' in self.parts[workId] and self.parts[workId]['arrangement'] \
                        or 'partial' in self.parts[workId] and self.parts[workId]['partial']:
                    if not isinstance(parent, basestring):
                        parent = '; '.join(parent)  # in case it is a list - make sure it is a string
                    if not isinstance(work, basestring):
                        work = '; '.join(work)
                    diff = self.diff_pair(track, tm, parent, work)
                    if diff == None:
                        diff = ""
                    strip = [diff, parent]
                else:
                    extend = True
                    strip = self.strip_parent_from_work(
                        work, parent, part_level, extend, parentId)
                stripped_works.append(strip[0])
                if self.INFO:
                    log.info("Full parent: %s, Parent: %s", strip[1], parent)
                full_parent = strip[1]
                if full_parent != parent:
                    tm['~cwp_work_' + str(part_level)] = full_parent.strip()
                    self.parts[parentId]['name'] = full_parent
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:
                            tm['~cwp_work_top'] = full_parent.strip()
            tm['~cwp_part_' + str(part_level - 1)] = stripped_works
            self.parts[workId]['stripped_name'] = stripped_works
        if self.DEBUG:
            log.debug("GOT TO END OF SET_METADATA")

    def derive_from_title(self, track, title):
        if self.INFO:
            log.info(
                "%s: DERIVING METADATA FROM TITLE for track: %s",
                PLUGIN_NAME,
                track)
        tm = track.metadata
        movt = title
        work = ""
        if '~cwp_part_levels' in tm:
            part_levels = int(tm['~cwp_part_levels'])
            if int(tm['~cwp_work_part_levels']
                   ) > 0:  # we have a work with movements
                colons = title.count(":")
                if colons > 0:
                    title_split = title.split(': ', 1)
                    title_rsplit = title.rsplit(': ', 1)
                    if part_levels >= colons:
                        work = title_rsplit[0]
                        movt = title_rsplit[1]
                    else:
                        work = title_split[0]
                        movt = title_split[1]
        if self.INFO:
            log.info("Work %s, Movt %s", work, movt)
        return (work, movt)

    #################################################
    # SECTION 4 - Extend work metadata using titles #
    #################################################

    def extend_metadata(self, top_info, track, ref_height, depth):
        tm = track.metadata
        if self.DEBUG:
            log.debug(
                "%s: Extending metadata for track: %s, ref_height: %s, depth: %s",
                PLUGIN_NAME,
                track,
                ref_height,
                depth)
        if self.INFO:
            log.info("Metadata = %s", tm)

        title_groupheading = None
        part_levels = int(tm['~cwp_part_levels'])
        work_part_levels = int(tm['~cwp_work_part_levels'])

        # previously: ref_height = work_part_levels - ref_level, where this
        # ref-level is the level for the top-named work
        ref_level = part_levels - ref_height
        work_ref_level = work_part_levels - ref_height

        topId = top_info['id']
        # replace works and parts by those derived from the level 0 work, where
        # required, available and appropriate, but only use work names based on
        # level 0 text if it doesn't cause ambiguity


        vanilla_part = tm['~cwp_part_0']  # before embellishing with partial / arrangement etc

        ## Fix text for arrangements, partials and medleys (Done here so that cache can be used)
        if self.options[track]['cwp_arrangements'] and self.options[track]["cwp_arrangements_text"]:
            for lev in range(0, ref_level):  # top level will not be an arrangement else there would be a higher level
                tup_id = eval(tm['~cwp_workid_' + str(lev)])  # needs to be a tuple to match
                if 'arrangement' in self.parts[tup_id] and self.parts[tup_id]['arrangement']:
                    update_list = ['~cwp_work_', '~cwp_part_']
                    if self.options[track]["cwp_level0_works"] and '~cwp_X0_work_' + str(lev) in tm:
                        update_list += ['~cwp_X0_work_', '~cwp_X0_part_']
                    for item in update_list:
                        tm[item + str(lev)] = self.options[track]["cwp_arrangements_text"] + ' ' + tm[item + str(lev)]

        if self.options[track]['cwp_partial'] and self.options[track]["cwp_partial_text"]:
            if '~cwp_workid_0' in tm:
                work0_id = eval(tm['~cwp_workid_0'])
                if 'partial' in self.parts[work0_id] and self.parts[work0_id]['partial']:
                    update_list = ['~cwp_work_0', '~cwp_part_0']
                    if self.options[track]["cwp_level0_works"] and '~cwp_X0_work_0' in tm:
                        update_list += ['~cwp_X0_work_0', '~cwp_X0_part_0']
                    for item in update_list:
                        if len(work0_id) > 1 and isinstance(tm[item], basestring):
                            meta_item = (tm[item]).split('; ', len(work0_id) - 1)
                        else:
                            meta_item = tm[item]
                        if isinstance(meta_item, list):
                            for ind, w in enumerate(meta_item):
                                meta_item[ind] = self.options[track]["cwp_partial_text"] + ' ' + w
                            tm[item] = meta_item
                        else:
                            tm[item] = self.options[track]["cwp_partial_text"] + ' ' + tm[item]

        # fix "type 1" medley text
        if self.options[track]['cwp_medley']:
            for lev in range(0, ref_level + 1):
                tup_id = eval(tm['~cwp_workid_' + str(lev)])
                if 'medley_list' in self.parts[tup_id]:
                    medley_list = self.parts[tup_id]['medley_list']
                    tm['~cwp_work_' + str(lev)] += " (" + self.options[track]["cwp_medley_text"] + ' ' + ', '.join(medley_list) + ")"

        part = []
        work = []
        for level in range(0, part_levels):
            part.append(tm['~cwp_part_' + str(level)])
            work.append(tm['~cwp_work_' + str(level)])
        work.append(tm['~cwp_work_' + str(part_levels)])

        ## Use level_0-derived names if applicable
        if self.options[track]["cwp_level0_works"]:
            for level in range(0, part_levels + 1):
                if '~cwp_X0_work_' + str(level) in tm:
                    work[level] = tm['~cwp_X0_work_' + str(level)]
                else:
                    if level != 0:
                        work[level] = ''
                if part and len(part) > level:
                    if '~cwp_X0_part_' + str(level) in tm:
                        part[level] = tm['~cwp_X0_part_' + str(level)]
                    else:
                        if level != 0:
                            part[level] = ''

        ## set up group heading and part

        if part_levels > 0:

            groupheading = work[1]
            work_main = work[ref_level]
            inter_work = ""
            work_titles = tm['~cwp_title_work_' + str(ref_level)]
            if ref_level > 1:
                for r in range(1, ref_level):
                    if inter_work:
                        inter_work = ': ' + inter_work
                    inter_work = part[r] + inter_work
                groupheading = work[ref_level] + ':: ' + inter_work

        else:
            groupheading = work[0]
            title_groupheading = tm['~cwp_title_work_0']
            work_main = groupheading
            inter_work = None
            work_titles = None

        if '~cwp_part_0' in tm:
            part_main = part[0]
            tm['~cwp_part'] = part_main
        else:
            part_main = work[0]
            tm['~cwp_part'] = part_main

        # fix medley text for "type 2" medleys
        if self.parts[eval(tm['~cwp_workid_0'])]['medley'] and self.options[track]['cwp_medley']:
            if self.options[track]["cwp_medley_text"]:
                groupheading = self.options[track]["cwp_medley_text"] + ' ' + groupheading

        tm['~cwp_groupheading'] = groupheading
        tm['~cwp_work'] = work_main
        tm['~cwp_inter_work'] = inter_work
        tm['~cwp_title_work'] = work_titles
        if self.DEBUG:
            log.debug("Groupheading set to: %s", groupheading)
        # extend group heading from title metadata
        if groupheading:
            ext_groupheading = groupheading
            title_groupheading = None
            ext_work = work_main
            ext_inter_work = inter_work
            inter_title_work = ""

            if '~cwp_title_work_levels' in tm:

                title_depth = int(tm['~cwp_title_work_levels'])
                if self.INFO:
                    log.info("Title_depth: %s", title_depth)
                diff_work = [""] * ref_level
                diff_part = [""] * ref_level
                tw_str_lower = 'x'  # to avoid errors, reset before used
                max_d = min(ref_level, title_depth) + 1
                for d in range(1, max_d):
                    tw_str = '~cwp_title_work_' + str(d)
                    if self.INFO:
                        log.info("TW_STR = %s", tw_str)
                    if tw_str in tm:
                        title_work = tm[tw_str]
                        work_main = work[d]
                        diff_work[d - 1] = self.diff_pair(track, tm, work_main, title_work)
                        if d > 1 and tw_str_lower in tm:
                            title_part = self.strip_parent_from_work(
                                tm[tw_str_lower], tm[tw_str], 0, False)[0].strip()
                            tm['~cwp_title_part_' + str(d - 1)] = title_part
                            part_n = part[d - 1]
                            diff_part[d -
                                      1] = self.diff_pair(track, tm, part_n, title_part) or ""
                    tw_str_lower = tw_str
                if self.INFO:
                    log.info("diff list for works: %s", diff_work)
                if self.INFO:
                    log.info("diff list for parts: %s", diff_part)
                if not diff_work or len(diff_work) == 0:
                    if part_levels > 0:
                        ext_groupheading = groupheading
                else:
                    if self.DEBUG:
                        log.debug("Now calc extended groupheading...")
                    if self.INFO:
                        log.info(
                            "depth = %s, ref_level = %s, title_depth = %s", depth, ref_level, title_depth)
                    if self.INFO:
                        log.info(
                            "diff_work = %s, diff_part = %s",
                            diff_work,
                            diff_part)
                    if part_levels > 0 and depth >= 1:
                        addn_work = []
                        addn_part = []
                        for stripped_work in diff_work:
                            if stripped_work:
                                if self.INFO:
                                    log.info(
                                        "Stripped work = %s", stripped_work)
                                addn_work.append(" {" + stripped_work + "}")
                            else:
                                addn_work.append("")
                        for stripped_part in diff_part:
                            if stripped_part and stripped_part != "":
                                if self.INFO:
                                    log.info(
                                        "Stripped part = %s", stripped_part)
                                addn_part.append(" {" + stripped_part + "}")
                            else:
                                addn_part.append("")
                        if self.INFO:
                            log.info("addn_work = %s, addn_part = %s", addn_work, addn_part)
                        ext_groupheading = work[1] + addn_work[0]
                        ext_work = work[ref_level] + addn_work[ref_level-1]
                        ext_inter_work = ""
                        inter_title_work = ""
                        title_groupheading = tm['~cwp_title_work_1']
                        if ref_level > 1:
                            for r in range(1, ref_level):
                                if ext_inter_work:
                                    ext_inter_work = ': ' + ext_inter_work
                                ext_inter_work = part[r] + addn_part[r-1] + ext_inter_work
                            ext_groupheading = work[ref_level] + addn_work[ref_level-1] + ':: ' + ext_inter_work
                        if title_depth > 1:
                            for r in range(1, min(title_depth, ref_level)):
                                if inter_title_work:
                                    inter_title_work = ': ' + inter_title_work
                                inter_title_work = tm['~cwp_title_part_' + str(r)] + addn_part[r-1] + inter_title_work
                            title_groupheading = tm['~cwp_title_work_' + str(min(title_depth, ref_level))] + addn_work[min(title_depth, ref_level)-1] + ':: ' + inter_title_work

                    else:
                        ext_groupheading = groupheading  # title will be in part
                        ext_work = work_main
                        ext_inter_work = inter_work
                        inter_title_work = ""

                    if self.DEBUG:
                        log.debug(".... ext_groupheading done")

            if ext_groupheading:
                if self.INFO:
                    log.info("EXTENDED GROUPHEADING: %s", ext_groupheading)
                tm['~cwp_extended_groupheading'] = ext_groupheading
                tm['~cwp_extended_work'] = ext_work
                if ext_inter_work:
                    tm['~cwp_extended_inter_work'] = ext_inter_work
                if inter_title_work:
                    tm['~cwp_inter_title_work'] = inter_title_work
                if title_groupheading:
                    tm['~cwp_title_groupheading'] = title_groupheading
                    if self.INFO:
                        log.info("title_groupheading = %s", title_groupheading)
        # extend part from title metadata
        if self.DEBUG:
            log.debug("%s: Now extend part...(part = %s)", PLUGIN_NAME, part_main)
        if part_main:
            if '~cwp_title_part_0' in tm:
                movement = tm['~cwp_title_part_0']
            else:
                movement = tm['~cwp_title'] or tm['title']
            diff = self.diff_pair(track, tm, work[0], movement)
            # compare with the full work name, not the stripped one unless it results in nothing
            if not diff and not vanilla_part:
                diff = self.diff_pair(track, tm, part_main, movement)
            if self.INFO:
                log.info("DIFF PART - MOVT. ti =%s", diff)
            diff2 = diff
            if diff:
                if '~cwp_work_1' in tm:
                    if self.parts[eval(tm['~cwp_workid_0'])]['partial']:
                        no_diff = False
                    else:
                        diff2 = self.diff_pair(track, tm, work[1], diff)
                        if diff2:
                            no_diff = False
                        else:
                            no_diff = True
                else:
                    no_diff = False
            else:
                no_diff = True
            if self.INFO:
                log.info('Set no_diff for %s = %s', tm['~cwp_workid_0'], no_diff)
                log.info('medley indicator for %s is %s', tm['~cwp_workid_0'],
                         self.parts[eval(tm['~cwp_workid_0'])]['medley'])
            if self.parts[eval(tm['~cwp_workid_0'])]['medley'] and self.options[track]['cwp_medley']:
                no_diff = False
                if self.INFO:
                    log.info('setting no_diff = %s', no_diff)
            if no_diff:
                if part_levels > 0:
                    tm['~cwp_extended_part'] = part_main
                else:
                    tm['~cwp_extended_part'] = work[0]
                    if tm['~cwp_extended_groupheading']:
                        del tm['~cwp_extended_groupheading']
            else:
                if part_levels > 0:
                    stripped_movt = diff2.strip()
                    tm['~cwp_extended_part'] = part_main + \
                                               " {" + stripped_movt + "}"
                else:
                    # title will be in part
                    tm['~cwp_extended_part'] = movement
        # remove unwanted groupheadings (needed them up to now for adding extensions)
        if '~cwp_groupheading' in tm and tm['~cwp_groupheading'] == tm['~cwp_part']:
            del tm['~cwp_groupheading']
        if '~cwp_title_groupheading' in tm and tm['~cwp_title_groupheading'] == tm['~cwp_title_part']:
            del tm['~cwp_title_groupheading']
        if self.DEBUG:
            log.debug("....done")
        return None

    ##########################################################
    # SECTION 5- Write metadata to tags according to options #
    ##########################################################

    def publish_metadata(self, album, track):
        if self.DEBUG:
            log.debug("%s: IN PUBLISH METADATA for %s", PLUGIN_NAME, track)
        options = self.options[track]
        tm = track.metadata
        tm['~cwp_version'] = PLUGIN_VERSION
        if self.DEBUG:
            log.debug("Check options")
        if options["cwp_titles"]:
            if self.DEBUG:
                log.debug("titles")
            part = tm['~cwp_title_part_0'] or tm['~cwp_title'] or tm['title']
            # for multi-level work display
            groupheading = tm['~cwp_title_groupheading'] or ""
            # for single-level work display
            work = tm['~cwp_title_work'] or ""
            inter_work = tm['~cwp_inter_title_work'] or ""
        elif options["cwp_works"]:
            if self.DEBUG:
                log.debug("works")
            part = tm['~cwp_part']
            groupheading = tm['~cwp_groupheading'] or ""
            work = tm['~cwp_work'] or ""
            inter_work = tm['~cwp_inter_work'] or ""
        elif options["cwp_extended"]:
            if self.DEBUG:
                log.debug("extended")
            part = tm['~cwp_extended_part']
            groupheading = tm['~cwp_extended_groupheading'] or ""
            work = tm['~cwp_extended_work'] or ""
            inter_work = tm['~cwp_extended_inter_work'] or ""
        if self.DEBUG:
            log.debug("Done options")
        p1 = re.compile(
            r'^\W*\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b[\s|\.|:|,|;]',
            re.IGNORECASE)  # Matches Roman numerals with punctuation
        # Matches positive integers with punctuation
        p2 = re.compile(r'^\W*\d+[.):-]')
        movt = part
        for _ in range(
                0, 5):  # in case of multiple levels
            movt = p2.sub('', p1.sub('', movt)).strip()
        if self.DEBUG:
            log.debug("Done movt")
        movt_inc_tags = options["cwp_movt_tag_inc"].split(",")
        movt_inc_tags = [x.strip(' ') for x in movt_inc_tags]
        movt_exc_tags = options["cwp_movt_tag_exc"].split(",")
        movt_exc_tags = [x.strip(' ') for x in movt_exc_tags]
        movt_inc_1_tags = options["cwp_movt_tag_inc1"].split(",")
        movt_inc_1_tags = [x.strip(' ') for x in movt_inc_1_tags]
        movt_exc_1_tags = options["cwp_movt_tag_exc1"].split(",")
        movt_exc_1_tags = [x.strip(' ') for x in movt_exc_1_tags]
        movt_no_tags = options["cwp_movt_no_tag"].split(",")
        movt_no_tags = [x.strip(' ') for x in movt_no_tags]
        movt_no_sep = options["cwp_movt_no_sep"]
        gh_tags = options["cwp_work_tag_multi"].split(",")
        gh_tags = [x.strip(' ') for x in gh_tags]
        gh_sep = options["cwp_multi_work_sep"]
        work_tags = options["cwp_work_tag_single"].split(",")
        work_tags = [x.strip(' ') for x in work_tags]
        work_sep = options["cwp_single_work_sep"]
        top_tags = options["cwp_top_tag"].split(",")
        top_tags = [x.strip(' ') for x in top_tags]

        if self.DEBUG:
            log.debug(
                "Done splits. gh_tags: %s, work_tags: %s, movt_inc_tags: %s, movt_exc_tags: %s, movt_no_tags: %s",
                gh_tags,
                work_tags,
                movt_inc_tags,
                movt_exc_tags,
                movt_no_tags)

        for tag in gh_tags + work_tags + movt_inc_tags + movt_exc_tags + movt_no_tags:
            tm[tag] = ""
        for tag in gh_tags:
            if tag in movt_inc_tags + movt_exc_tags + movt_no_tags:
                self.append_tag(tm, tag, groupheading, gh_sep)
            else:
                self.append_tag(tm, tag, groupheading)
        for tag in work_tags:
            if tag in movt_inc_1_tags + movt_exc_1_tags + movt_no_tags:
                self.append_tag(tm, tag, work, work_sep)
            else:
                self.append_tag(tm, tag, work)
            if '~cwp_part_levels' in tm and int(tm['~cwp_part_levels']) > 0:
                self.append_tag(tm, 'show work movement', '1')  # for iTunes
        for tag in top_tags:
            if '~cwp_work_top' in tm:
                self.append_tag(tm, tag, tm['~cwp_work_top'])

        for tag in movt_no_tags:
            self.append_tag(tm, tag, tm['~cwp_movt_num'])
            if tag in movt_inc_tags + movt_exc_tags:
                self.append_tag(tm, tag, movt_no_sep)

        for tag in movt_exc_tags:
            self.append_tag(tm, tag, movt)

        for tag in movt_inc_tags:
            self.append_tag(tm, tag, part)

        for tag in movt_inc_1_tags + movt_exc_1_tags:
            if tag in movt_inc_1_tags:
                pt = part
            else:
                pt = movt
            if inter_work and inter_work != "":
                if tag in movt_exc_tags + movt_inc_tags and tag != "":
                    if self.WARNING:
                        log.warning("Tag %s will have multiple contents", tag)
                    self.append_tag(
                        tm,
                        '~cwp_warning',
                        'Tag ' +
                        tag +
                        ' has multiple contents')
                self.append_tag(tm, tag, inter_work + work_sep + " " + pt)
            else:
                self.append_tag(tm, tag, pt)

        for tag in movt_exc_tags + movt_inc_tags + movt_exc_1_tags + movt_inc_1_tags:
            if tag in movt_no_tags:
                tm[tag] = "".join(tm[tag].split('; '))  # i.e treat as one item, not multiple

        # write "SongKong" tags
        if options['cwp_write_sk']:
            if self.DEBUG:
                log.debug("%s: writing SongKong work tags", PLUGIN_NAME)
            if '~cwp_part_levels' in tm:
                part_levels = int(tm['~cwp_part_levels'])
                for n in range(0, part_levels + 1):
                    if '~cwp_work_' + str(n) in tm and '~cwp_workid_' + str(n) in tm:
                        source = tm['~cwp_work_' + str(n)]
                        source_id = list(eval(tm['~cwp_workid_' + str(n)]))
                        if n == 0:
                            self.append_tag(tm, 'musicbrainz_work_composition', source)
                            for source_id_item in source_id:
                                self.append_tag(tm, 'musicbrainz_work_composition_id', source_id_item)
                        if n == part_levels:
                            self.append_tag(tm, 'musicbrainz_work', source)
                            if 'musicbrainz_workid' in tm:
                                del tm['musicbrainz_workid']
                            # Delete the Picard version of this tag before replacing it with the SongKong version
                            for source_id_item in source_id:
                                self.append_tag(tm, 'musicbrainz_workid', source_id_item)
                        if n != 0 and n != part_levels:
                            self.append_tag(tm, 'musicbrainz_work_part_level' + str(n), source)
                            for source_id_item in source_id:
                                self.append_tag(tm, 'musicbrainz_work_part_level' + str(n) + '_id', source_id_item)

        # carry out tag mapping
        tm['~cea_works_complete'] = "Y"
        map_tags(options, tm)

        if self.DEBUG:
            log.debug("Published metadata for %s", track)
        if options['cwp_options_tag'] != "":
            self.cwp_options = collections.defaultdict(
                lambda: collections.defaultdict(dict))

            for opt in plugin_options('workparts'):
                if 'name' in opt:
                    if 'value' in opt:
                        if options[opt['option']]:
                            self.cwp_options['Classical Extras']['Works options'][opt['name']] = opt['value']
                    else:
                        self.cwp_options['Classical Extras']['Works options'][opt['name']] = \
                            options[opt['option']]

            if self.INFO:
                log.info("Options %s", self.cwp_options)
            if options['ce_version_tag'] and options['ce_version_tag'] != "":
                self.append_tag(tm, options['ce_version_tag'], str(
                    'Version ' + tm['~cwp_version'] + ' of Classical Extras'))
            if options['cwp_options_tag'] and options['cwp_options_tag'] != "":
                self.append_tag(
                    tm,
                    options['cwp_options_tag'] +
                    ':workparts_options',
                    json.loads(
                        json.dumps(
                            self.cwp_options)))
        if self.ERROR and "~cwp_error" in tm:
            # if '001_errors' in tm:
            #     del tm['001_errors']
            self.append_tag(tm, '001_errors', tm['~cwp_error'])
        if self.WARNING and "~cwp_warning" in tm:
            # if '002_warnings' in tm:
            #     del tm['002_warnings']
            self.append_tag(tm, '002_warnings', tm['~cwp_warning'])
        # if '003_information:options_overridden' in tm:
        #     del tm['003_information:options_overridden']
        self.append_tag(tm, '003_information:options_overridden', tm['~cwp_info_options'])

    def append_tag(self, tm, tag, source, sep=None):
        if self.DEBUG:
            log.debug(
                "In append_tag (Work parts). tag = %s, source = %s, sep =%s",
                tag,
                source,
                sep)
        append_tag(tm, tag, source)
        if self.DEBUG:
            log.debug(
                "Appended. Resulting contents of tag: %s are: %s",
                tag,
                tm[tag]
            )

    ################################################
    # SECTION 6 - Common string handling functions #
    ################################################

    def strip_parent_from_work(
            self,
            work,
            parent,
            part_level,
            extend,
            parentId=None):
        # extend=True is used to find "full_parent" names and also (with parentId) to trigger recursion if unable to strip parent name from work
        # extend=False is used when this routine is called for other purposes
        # than strict work: parent relationships
        if self.DEBUG:
            log.debug(
                "%s: STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES",
                PLUGIN_NAME)
        if not isinstance(parent, basestring):
            parent = '; '.join(parent)  # in case it is a list - make sure it is a string
        if not isinstance(work, basestring):
            work = '; '.join(work)
        full_parent = parent
        # replace any punctuation or numbers, with a space (to remove any
        # inconsistent punctuation and numbering) - (?u) specifies the
        # re.UNICODE flag in sub
        clean_parent = re.sub("(?u)[\W]", ' ', parent)
        # now allow the spaces to be filled with up to 2 non-letters
        pattern_parent = re.sub("\s", "\W{0,2}", clean_parent)
        if extend:
            pattern_parent = "(.*\s|^)(\W*" + pattern_parent + "\w*)(\W*\s)(.*)"
        else:
            pattern_parent = "(.*\s|^)(\W*" + pattern_parent + "w*\W?)(.*)"
        if self.INFO:
            log.info("Pattern parent: %s, Work: %s", pattern_parent, work)
        p = re.compile(pattern_parent, re.IGNORECASE | re.UNICODE)
        m = p.search(work)
        if m:
            if self.DEBUG:
                log.debug("Matched...")
            if extend:
                if m.group(1):
                    stripped_work = m.group(1) + '...' + m.group(4)
                else:
                    stripped_work = m.group(4)
            else:
                if m.group(1):
                    stripped_work = m.group(1) + '...' + m.group(3)
                else:
                    stripped_work = m.group(3)
            # may not have a full work name in the parent (missing op. no.
            # etc.)
            if m.group(3) != ": " and extend:
                # no. of colons is consistent with "work: part" structure
                if work.count(": ") >= part_level:
                    split_work = work.split(': ', 1)
                    stripped_work = split_work[1]
                    full_parent = split_work[0]
                    if len(full_parent) < len(
                            parent):  # don't shorten parent names! (in case colon is mis-placed)
                        full_parent = parent
                        stripped_work = m.group(4)
        else:
            if self.DEBUG:
                log.debug("No match...")

            if extend and parentId and parentId in self.works_cache:
                if self.DEBUG:
                    log.debug("Looking for match at next level up")
                grandparentIds = tuple(self.works_cache[parentId])
                grandparent = self.parts[grandparentIds]['name']
                stripped_work = self.strip_parent_from_work(
                    work, grandparent, part_level, True, grandparentIds)[0]

            else:
                stripped_work = work

        if self.INFO:
            log.info("Work: %s", work)
        if self.INFO:
            log.info("Stripped work: %s", stripped_work)
        return (stripped_work, full_parent)

    def diff_pair(self, track, tm, mb_item, title_item):
        if self.DEBUG:
            log.debug("%s: Inside DIFF_PAIR", PLUGIN_NAME)
        mb = mb_item.strip()
        if self.INFO:
            log.info("mb = %s", mb)
        if self.INFO:
            log.info("title_item = %s", title_item)
        if not mb:
            return None
        ti = title_item.strip(" :;-.,")
        if ti.count('"') == 1:
            ti = ti.strip('"')
        if ti.count("'") == 1:
            ti = ti.strip("'")
        if self.INFO:
            log.info("ti (amended) = %s", ti)
        if not ti:
            return None
        p1 = re.compile(
            r'^\W*\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b[\s|\.|:|,|;]',
            re.IGNORECASE)  # Matches Roman numerals with punctuation
        # Matches positive integers with punctuation
        p2 = re.compile(r'^\W*\d+[.):-]')
        # remove certain words from the comparison
        removewords = self.options[track]["cwp_removewords"].split(',')
        if self.INFO:
            log.info("Removewords = %s", removewords)
        # remove numbers, roman numerals, part etc and punctuation from the
        # start
        if self.DEBUG:
            log.debug("checking prefixes")
        for i in range(
                0, 5):  # in case of multiple levels
            mb = p2.sub('', p1.sub('', mb)).strip()
            ti = p2.sub('', p1.sub('', ti)).strip()
            for prefix in removewords:
                prefix2 = str(prefix).lower().lstrip()
                if self.DEBUG:
                    log.debug("checking prefix %s", prefix2)
                if mb.lower().startswith(prefix2):
                    mb = mb[len(prefix2):]
                if ti.lower().startswith(prefix2):
                    ti = ti[len(prefix2):]
            mb = mb.strip()
            ti = ti.strip()
            if self.INFO:
                log.info(
                    "pairs after prefix strip iteration %s. mb = %s, ti = %s",
                    i,
                    mb,
                    ti)
        if self.DEBUG:
            log.debug("Prefixes checked")

        #  replacements
        strreps = self.options[track]["cwp_replacements"].split('/')
        replacements = []
        for rep in strreps:
            tupr = rep.strip(' ()').split(',')
            if len(tupr) == 2:
                for i, t in enumerate(tupr):
                    tupr[i] = t.strip("' ").strip('"')
                tupr = tuple(tupr)
                replacements.append(tupr)
            else:
                if self.ERROR:
                    log.error('Error in replacement format for replacement %s', rep)
                self.append_tag(tm, '~cwp_error', 'Error in replacement format for replacement ' + rep)
        if self.INFO:
            log.info("Replacement: %s", replacements)

        #  synonyms
        strsyns = self.options[track]["cwp_synonyms"].split('/')
        synonyms = []
        for syn in strsyns:
            tup = syn.strip(' ()').split(',')
            if len(tup) == 2:
                for i, t in enumerate(tup):
                    tup[i] = t.strip("' ").strip('"')
                    if re.findall(r'[^\w|\&]+', tup[i], re.UNICODE):
                        if self.ERROR:
                            log.error('Synonyms must be single words without punctuation - error in %s', tup[i])
                        self.append_tag(tm, '~cwp_error',
                                        'Synonyms must be single words without punctuation - error in ' + tup[i])
                        tup[i] = "**BAD**"
                if "**BAD**" in tup:
                    continue
                else:
                    tup = tuple(tup)
                    synonyms.append(tup)
            else:
                if self.ERROR:
                    log.error('Error in synonmym format for synonym %s', syn)
                self.append_tag(tm, '~cwp_error', 'Error in synonym format for synonym ' + syn)
        if self.INFO:
            log.info("Synonyms: %s", synonyms)

        # fix replacements and synonyms

        for key, equiv in replacements:
            if self.INFO:
                log.info("key %s, equiv %s", key, equiv)
            esc_key = re.escape(key)
            key_pattern = '\\b' + esc_key + '\\b'
            ti = re.sub(key_pattern, equiv, ti)
            if self.DEBUG:
                log.debug(
                    "Replaced replacements, ti = %s", ti)
        # Replace Roman numerals as per synonyms
        ti_test = replace_roman_numerals(ti)
        mb_test = replace_roman_numerals(mb)
        if self.INFO:
            log.info('Replaced Roman numerals. mb_test = %s, ti_test = %s', mb_test, ti_test)
        for key, equiv in synonyms:
            if self.INFO:
                log.info("key %s, equiv %s", key, equiv)
            esc_key = re.escape(key)
            key_pattern = '\\b' + esc_key + '\\b'
            mb_test = re.sub(key_pattern, equiv, mb_test)
            ti_test = re.sub(key_pattern, equiv, ti_test)
            # ti_test = ti_test.replace(key, equiv)
            if self.DEBUG:
                log.debug(
                    "Replaced synonyms mb_test = %s, ti_test = %s",
                    mb_test,
                    ti_test)

        # check if the title item is wholly part of the mb item

        if self.DEBUG:
            log.debug(
                "Testing if ti in mb. ti_test = %s, mb_test = %s",
                ti_test,
                mb_test)
        nopunc_ti = self.boil(ti_test)
        if self.INFO:
            log.info("nopunc_ti =%s", nopunc_ti)
        nopunc_mb = self.boil(mb_test)
        if self.INFO:
            log.info("nopunc_mb =%s", nopunc_mb)
        ti_len = len(nopunc_ti)
        if self.INFO:
            log.info("ti len %s", ti_len)
        sub_len = int(ti_len)
        if self.INFO:
            log.info("sub len %s", sub_len)
        if self.DEBUG:
            log.debug(
                "Initial test. nopunc_mb = %s, nopunc_ti = %s, sub_len = %s",
                nopunc_mb,
                nopunc_ti,
                sub_len)
        if self.DEBUG:
            log.debug("test sub....")
        lcs = longest_common_substring(nopunc_mb, nopunc_ti)
        if self.INFO:
            log.info(
                "Longest common substring is: %s. Sub_len is %s",
                lcs,
                sub_len)
        if len(lcs) >= sub_len:
            return None

        # try and strip the canonical item from the title item (only a full
        # strip affects the outcome)
        if len(nopunc_mb) > 0:
            ti_new = self.strip_parent_from_work(ti_test, mb_test, 0, False)[0]
            if ti_new == ti_test:
                mb_list = re.split(
                    r';\s|:\s|\.\s|\-\s', mb_test, self.options[track]["cwp_granularity"])
                if self.DEBUG:
                    log.debug("mb_list = %s", mb_list)
                if mb_list:
                    for mb_bit in mb_list:
                        ti_new = self.strip_parent_from_work(
                            ti_new, mb_bit, 0, False)[0]
                        if self.DEBUG:
                            log.debug("MB_BIT: %s, TI_NEW: %s", mb_bit, ti_new)
            else:
                if len(ti_new) > 0:
                    return ti_new
                else:
                    return None
            if len(ti_new) == 0:
                return None
        # return any significant new words in the title
        words = 0
        nonWords = [
            "a",
            "the",
            "in",
            "on",
            "at",
            "of",
            "after",
            "and",
            "de",
            "d'un",
            "d'une",
            "la",
            "le"]
        if self.DEBUG:
            log.debug(
                "Check before splitting: mb_test = %s, ti_test = %s",
                mb_test,
                ti_test)
        ti_list = re.findall(r"\b\w+?\b|\B\&\B", ti, re.UNICODE)
        # allow ampersands and non-latin characters as word characters
        ti_list_punc = re.findall(r"[^\w|\&]+", ti, re.UNICODE)
        ti_test_list = re.findall(r"\b\w+?\b|\B\&\B", ti_test, re.UNICODE)
        if ti_list_punc:
            if ti_list_punc[0][0]== ti[0]:
                # list begins with punc
                ti_list.insert(0, '')
                ti_test_list.insert(0, '')
        if len(ti_list_punc) < len(ti_list):
            ti_list_punc.append('')
        ti_zip_list = zip(ti_list, ti_list_punc)

        # len(ti_list) should be = len(ti_test_list) as only difference should be synonyms which are each one word
            # ti_list = ti_test_list
        mb_list2 = re.findall(r"\b\w+?\b|\B\&\B", mb_test, re.UNICODE)
        for index, mb_bit2 in enumerate(mb_list2):
            mb_list2[index] = self.boil(mb_bit2)
            if self.DEBUG:
                log.debug("mb_list2[%s] = %s", index, mb_list2[index])
        ti_new = []
        ti_comp_list = []
        ti_rich_list = []
        i = 0
        for i, ti_bit_test in enumerate(ti_test_list):
            # NB ti_bit_test is a tuple
            if i <= len(ti_list) - 1:
                ti_bit = ti_zip_list[i]
            else:
                ti_bit = ('', '')
            if self.INFO:
                log.info("i = %s, ti_bit_test = %s, ti_bit = %s", i, ti_bit_test, ti_bit)
            # Boolean to indicate whether ti_bit is a new word
            ti_rich_list.append((ti_bit, True))
            if self.boil(ti_bit_test) in mb_list2:
                words += 1
                ti_rich_list[i] = (ti_bit, False)
            else:
                if ti_bit_test.lower() not in nonWords and re.findall(r'\w',ti_bit[0], re.UNICODE):
                    ti_comp_list.append(ti_bit[0])
        if self.INFO:
            log.info("words %s", words)
        if self.INFO:
            log.info("ti_comp_list = %s", ti_comp_list)
        if self.INFO:
            log.info(
                "ti_rich_list before removing singletons = %s. length = %s",
                ti_rich_list,
                len(ti_rich_list))
        s = 0
        for i, (t, n) in enumerate(ti_rich_list):
            if n:
                s += 1
                index = i
                change = t # NB this is a tuple
        if s == 1:
            if 0 < index < len(ti_rich_list) - 1:
                # ignore singleton new words in middle of title
                ti_rich_list[index] = (change, False)
                s = 0
        if self.DEBUG:
            log.debug(
                "ti_rich_list before gapping = %s. length = %s",
                ti_rich_list,
                len(ti_rich_list))
        if s > 0:
            p = self.options[track]["cwp_proximity"]
            d = self.options[track]["cwp_proximity"] - self.options[track]["cwp_end_proximity"]
            for i, (ti_bit, new) in enumerate(ti_rich_list):
                if not new:
                    if self.DEBUG:
                        log.debug("%s not new. p = %s", ti_bit, p)
                    if p > 0:
                        for j in range(0, p + 1):
                            if self.DEBUG:
                                log.debug("i = %s, j = %s", i, j)
                            if i + j < len(ti_rich_list):
                                if ti_rich_list[i + j][1]:
                                    if self.DEBUG:
                                        log.debug("Set to true..")
                                    ti_rich_list[i] = (ti_bit, True)
                                    if self.DEBUG:
                                        log.debug("...set OK")
                            else:
                                if j <= p - d:
                                    ti_rich_list[i] = (ti_bit, True)
                else:
                    p = self.options[track]["cwp_proximity"]
                if not ti_rich_list[i][1]:
                    p -= 1
        if self.DEBUG:
            log.debug("ti_rich_list after gapping = %s", ti_rich_list)
        nothing_new = True
        for (ti_bit, new) in ti_rich_list:
            if new:
                nothing_new = False
                new_prev = True
                break
        if nothing_new:
            return None
        else:
            new_prev = False
            for i, (ti_bit, new) in enumerate(ti_rich_list):
                if self.DEBUG:
                    log.debug("Create new for %s?", ti_bit)
                if new:
                    if self.DEBUG:
                        log.debug("Yes for %s", ti_bit)
                    if not new_prev:
                        if i > 0:
                            # check to see if the last char of the prev punctuation group needs to be added first
                            if len(ti_rich_list[i - 1][0][1]) > 1:
                                ti_new.append(ti_rich_list[i - 1][0][1][-1])  # i.e. ti_bit[1][-1] of previous loop
                    ti_new.append(ti_bit[0])
                    if  len(ti_bit[1]) > 1:
                        if i < len(ti_rich_list) - 1:
                            if ti_rich_list[i + 1][1]:
                                ti_new.append(ti_bit[1])
                            else:
                                ti_new.append(ti_bit[1][:-1])
                        else:
                            ti_new.append(ti_bit[1])
                    else:
                        ti_new.append(ti_bit[1])
                    if self.DEBUG:
                        log.debug(
                            "appended %s. ti_new is now %s", ti_bit, ti_new)
                else:
                    if self.DEBUG:
                        log.debug("Not for %s", ti_bit)
                    if new != new_prev:
                        ti_new.append('... ')

                new_prev = new
        if ti_new:
            if self.INFO:
                log.info("ti_new %s", ti_new)
            ti = ''.join(ti_new)
            if self.INFO:
                log.info("New text from title = %s", ti)
        else:
            if self.INFO:
                log.info("New text empty")
            return None
        # see if there is any significant difference between the strings
        if ti:
            nopunc_ti = self.boil(ti)
            nopunc_mb = self.boil(mb)
            ti_len = len(nopunc_ti)
            sub_len = ti_len * float(self.options[track]["cwp_substring_match"]) / 100
            if self.DEBUG:
                log.debug("test sub....")
            lcs = longest_common_substring(nopunc_mb, nopunc_ti)
            if self.INFO:
                log.info(
                    "Longest common substring is: %s. Sub_len is %s",
                    lcs,
                    sub_len)
            if len(lcs) >= sub_len:
                return None
            if self.DEBUG:
                log.debug("...done, ti =%s", ti)
        # remove duplicate successive words (and remove first word of title
        # item if it duplicates last word of mb item)
        if ti:
            ti_list_new = re.split(' ', ti)
            ti_list_ref = ti_list_new
            ti_bit_prev = None
            for i, ti_bit in enumerate(ti_list_ref):
                if ti_bit != "...":

                    if i > 1:
                        if self.boil(ti_bit) == self.boil(ti_bit_prev):
                            #ti_bit_prev = ti_list_new[i]
                            dup = ti_list_new.pop(i)
                            if self.DEBUG:
                                log.debug("...removed dup %s", dup)

                ti_bit_prev = ti_bit

            if self.INFO:
                log.info("1st word of ti = %s. Last word of mb = %s",
                         ti_list_new[0], mb_list2[-1])
            if ti_list_new:
                if self.boil(ti_list_new[0]) == mb_list2[-1]:
                    if self.DEBUG:
                        log.debug("Removing 1st word from ti...")
                    first = ti_list_new.pop(0)
                    if self.DEBUG:
                        log.debug("...removed %s", first)
            else:
                return None
            if ti_list_new:
                if self.DEBUG:
                    log.debug("rejoin list %s", ti_list_new)
                ti = ' '.join(ti_list_new)
            else:
                return None
        # remove excess brackets and punctuation
        if ti:
            ti = ti.strip("!&.-:;, ")
            if ti.count('"') == 1:
                ti = ti.strip('"')
            if ti.count("'") == 1:
                ti = ti.strip("'")
            if self.DEBUG:
                log.debug("stripped punc ok. ti = %s", ti)
            if ti:
                if ti.count("\"") == 1:
                    ti = ti.strip("\"")
                if ti.count("\'") == 1:
                    ti = ti.strip("\'")
                if "(" in ti and ")" not in ti:
                    ti = ti.replace("(", "")
                if ")" in ti and "(" not in ti:
                    ti = ti.replace(")", "")
                if "[" in ti and "]" not in ti:
                    ti = ti.replace("[", "")
                if "]" in ti and "[" not in ti:
                    ti = ti.replace("]", "")
                if "{" in ti and "}" not in ti:
                    ti = ti.replace("{", "")
                if "}" in ti and "{" not in ti:
                    ti = ti.replace("}", "")
            if ti:
                match_chars = [("(", ")"), ("[", "]"), ("{", "}")]
                last = len(ti) - 1
                for char_pair in match_chars:
                    if char_pair[0] == ti[0] and char_pair[1] == ti[last]:
                        ti = ti.lstrip(char_pair[0]).rstrip(char_pair[1])
        if self.DEBUG:
            log.debug("DIFF is returning ti = %s", ti)
        if ti and len(ti) > 0:
            return ti
        else:
            return None

    # Remove punctuation, spaces, capitals and accents for string comprisona
    def boil(self, s):
        if self.DEBUG:
            log.debug("boiling %s", s)
        s = s.lower()
        if isinstance(s, str):
            s = s.decode('unicode_escape')
        s = s.replace('sch', 'sh')\
            .replace(u'\xdfe','ss')\
            .replace('sz','ss')\
            .replace(u'\u0153','oe')\
            .replace('oe','o')\
            .replace(u'\u00fc','ue')\
            .replace('ue','u')\
            .replace('ae','a')
        punc = re.compile(r'\W*')
        s = ''.join(
            c for c in ud.normalize(
                'NFD',
                s) if ud.category(c) != 'Mn')
        boiled = punc.sub('', s).strip().lower().rstrip("s'")
        if self.DEBUG:
            log.debug("boiled result = %s", boiled)
        return boiled

    # Remove certain keywords
    def remove_words(self, query, stopwords):
        if self.DEBUG:
            log.debug("INSIDE REMOVE_WORDS")
        querywords = query.split()
        resultwords = []
        for word in querywords:
            if word.lower() not in stopwords:
                resultwords.append(word)
        return ' '.join(resultwords)


################
# OPTIONS PAGE #
################


class ClassicalExtrasOptionsPage(OptionsPage):
    NAME = "classical_extras"
    TITLE = "Classical Extras"
    PARENT = "plugins"
    opts = plugin_options('artists') + plugin_options('tag') + plugin_options('workparts') + plugin_options('other')

    options = []

    for opt in opts:
        if 'type' in opt:
            if 'default' in opt:
                default = opt['default']
            else:
                default = ""
            if opt['type'] == 'Boolean':
                options.append(BoolOption("setting", opt['option'], default))
            elif opt['type'] == 'Text' or opt['type'] == 'Combo':
                options.append(TextOption("setting", opt['option'], default))
            elif opt['type'] == 'Integer':
                options.append(IntOption("setting", opt['option'], default))
            else:
                log.error("Error in setting options for option = %s", opt['option'])

    def __init__(self, parent=None):
        super(ClassicalExtrasOptionsPage, self).__init__(parent)
        self.ui = Ui_ClassicalExtrasOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        opts = plugin_options('artists') + plugin_options('tag') + plugin_options('workparts') + plugin_options('other')
        # count = 0
        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
            else:
                ui_name = opt['option']
            if opt['type'] == 'Boolean':
                self.ui.__dict__[ui_name].setChecked(self.config.setting[opt['option']])
            elif opt['type'] == 'Text':
                self.ui.__dict__[ui_name].setText(self.config.setting[opt['option']])
            elif opt['type'] == 'Combo':
                self.ui.__dict__[ui_name].setEditText(self.config.setting[opt['option']])
            elif opt['type'] == 'Integer':
                self.ui.__dict__[ui_name].setValue(self.config.setting[opt['option']])
            else:
                log.error("Error in loading options for option = %s", opt['option'])

    def save(self):
        opts = plugin_options('artists') + plugin_options('tag') + plugin_options('workparts') + plugin_options('other')

        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
            else:
                ui_name = opt['option']
            if opt['type'] == 'Boolean':
                self.config.setting[opt['option']] = self.ui.__dict__[ui_name].isChecked()
            elif opt['type'] == 'Text':
                self.config.setting[opt['option']] = unicode(self.ui.__dict__[ui_name].text())
            elif opt['type'] == 'Combo':
                self.config.setting[opt['option']] = unicode(self.ui.__dict__[ui_name].currentText())
            elif opt['type'] == 'Integer':
                self.config.setting[opt['option']] = self.ui.__dict__[ui_name].value()
            else:
                log.error("Error in saving options for option = %s", opt['option'])


#################
# MAIN ROUTINE  #
#################

register_track_metadata_processor(PartLevels().add_work_info)
register_track_metadata_processor(ExtraArtists().add_artist_info)
register_options_page(ClassicalExtrasOptionsPage)
