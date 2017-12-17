# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Classical Extras'
PLUGIN_AUTHOR = u'Mark Evens'
PLUGIN_DESCRIPTION = u"""This plugin contains 3 classes:
<br /><br />
I. ("EXTRA ARTISTS") Create sorted fields for all performers. Creates a number of variables with alternative values for "artists" and "artist".
Creates an ensemble variable for all ensemble-type performers.
Also creates matching sort fields for artist and artists.
Additionally create tags for artist types which are not normally created in Picard - particularly for classical music (notably instrument arrangers).
<br /><br />
II. ("PART LEVELS" [aka Work Parts]) Create tags for the hierarchy of works which contain a given track recording - particularly for classical music'
Variables provided for each work level, with implied part names
Mixed metadata provided including work and title elements
<br /><br />
III. ("OPTIONS") Allows the user to set various options including what tags will be written (otherwise the classes above will just write outputs to "hidden variables")
<br /><br />
See Readme file for full details.
"""
PLUGIN_VERSION = '0.8.7'
PLUGIN_API_VERSIONS = ["1.4.0", "1.4.2"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page, OptionsPage
from picard.plugins.classical_extras.ui_options_classical_extras import Ui_ClassicalExtrasOptionsPage
from picard import config, log
from picard.config import ConfigSection, BoolOption, IntOption, TextOption
from picard.util import LockableObject

# note that in 2.0 picard.webservice will change to picard.util.xml
from picard.webservice import XmlNode
from picard.metadata import register_track_metadata_processor, Metadata
from functools import partial
import collections
import re
import unicodedata
# import traceback
import json
import copy

##########################
# MODULE-WIDE COMPONENTS #
##########################

# CONSTANTS

prefixes = ['the', 'a', 'an', 'le', 'la', 'les', 'los', 'il']

relation_types = {
    'work': [
        'arranger',
        'instrument arranger',
        'orchestrator',
        'composer',
        'writer',
        'lyricist',
        'librettist',
        'revised by',
        'translator',
        'reconstructed by',
        'vocal arranger'],
    'release': [
        'instrument',
        'performer',
        'vocal',
        'performing orchestra',
        'conductor',
        'chorus master',
        'concertmaster',
        'arranger',
        'instrument arranger',
        'orchestrator',
        'vocal arranger'],
    'recording': [
        'instrument',
        'performer',
        'vocal',
        'performing orchestra',
        'conductor',
        'chorus master',
        'concertmaster',
        'arranger',
        'instrument arranger',
        'orchestrator',
        'vocal arranger']}


# OPTIONS

def get_options(album, track):
    """
    :param album: current release
    :param track: current track
    :return: None (result is passed via tm)
    A common function for both Artist and Workparts, so that the first class to process a track will execute
    this function so that the results are available to both (via a track metadata item)
    """
    set_options = collections.defaultdict(dict)
    sections = ['artists', 'workparts']
    override = {'artists': 'cea_override', 'workparts': 'cwp_override'}
    sect_text = {'artists': 'Artists', 'workparts': 'Works'}

    if album.tagger.config.setting['ce_options_overwrite'] and all(
            album.tagger.config.setting[override[sect]] for sect in sections):
        set_options[track] = album.tagger.config.setting  # mutable
    else:
        set_options[track] = option_settings(
            album.tagger.config.setting)  # make a copy

    # Also use some of the main Picard options
    set_options[track]['translate_artist_names'] = config.setting['translate_artist_names']
    set_options[track]['standardize_artists'] = config.setting['standardize_artists']

    options = set_options[track]
    tm = track.metadata
    orig_metadata = None
    # Only look up files if needed
    file_options = {}
    music_file = None
    found_file = False
    for music_file in album.tagger.files:
        new_metadata = album.tagger.files[music_file].metadata
        orig_metadata = album.tagger.files[music_file].orig_metadata
        if options['log_info']:
            log.info('orig_metadata for file %s is', music_file)
            log.info(orig_metadata)
        if 'musicbrainz_trackid' in new_metadata and 'musicbrainz_trackid' in tm:
            if new_metadata['musicbrainz_trackid'] == tm['musicbrainz_trackid']:
                # find the tag with the options
                for section in sections:
                    if options[override[section]]:
                        if section == 'artists':
                            prefix = 'cea'
                        else:
                            prefix = 'cwp'
                        if options[prefix + '_options_tag'] + ':' + \
                                section + '_options' in orig_metadata:
                            file_options[section] = interpret(
                                orig_metadata[options[prefix + '_options_tag'] + ':' + section + '_options'])
                        elif options[prefix + '_options_tag'] in orig_metadata:
                            options_tag_contents = orig_metadata[options[prefix + '_options_tag']]
                            if isinstance(options_tag_contents, list):
                                options_tag_contents = options_tag_contents[0]
                            combined_options = ''.join(options_tag_contents.split(
                                '(workparts_options)')).split('(artists_options)')
                            for i, _ in enumerate(combined_options):
                                combined_options[i] = interpret(
                                    combined_options[i].lstrip('; '))
                                if isinstance(
                                        combined_options[i],
                                        dict) and 'Classical Extras' in combined_options[i]:
                                    if sect_text[section] + \
                                            ' options' in combined_options[i]['Classical Extras']:
                                        file_options[section] = combined_options[i]
                        else:
                            for om in orig_metadata:
                                if ':' + section + '_options' in om:
                                    file_options[section] = interpret(
                                        orig_metadata[om])
                        if section not in file_options or not file_options[section]:
                            if options['log_error']:
                                log.error(
                                    '%s: Saved ' +
                                    section +
                                    ' options cannot be read for file %s. Using current settings',
                                    PLUGIN_NAME,
                                    music_file)
                            append_tag(
                                tm,
                                '~' + prefix + '_error',
                                'Saved ' +
                                section +
                                ' options cannot be read. Using current settings')

                found_file = True
                break  # we've found the file and don't want any more!
        else:
            if 'musicbrainz_trackid' not in new_metadata:
                if options['log_warning']:
                    log.warning('No trackid in file %s', music_file)
            if 'musicbrainz_trackid' not in tm:
                if options['log_warning']:
                    log.warning('No trackid in track %s', track)
    if not found_file:
        if options['log_warning']:
            log.warning(
                "No file with matching trackid for track %s. IF THERE SHOULD BE ONE, TRY 'REFRESH'",
                track)
            append_tag(
                tm,
                "002_warning",
                "No file with matching trackid - IF THERE SHOULD BE ONE, TRY 'REFRESH' - (unable to process any saved options, lyrics or 'keep' tags)")

    for section in sections:
        if options[override[section]]:
            if section in file_options and file_options[section]:
                options_dict = file_options[section]['Classical Extras'][sect_text[section] + ' options']
                for opt in options_dict:
                    if isinstance(
                            options_dict[opt],
                            dict):  # for tag line options
                        opt_list = []
                        for opt_item in options_dict[opt]:
                            opt_list.append(
                                {opt + '_' + opt_item: options_dict[opt][opt_item]})
                    else:
                        opt_list = [{opt: options_dict[opt]}]
                    for opt_dict in opt_list:
                        for opt in opt_dict:
                            opt_value = opt_dict[opt]
                            if section == 'artists':
                                addn = plugin_options('tag')
                            else:
                                addn = []
                            for ea_opt in plugin_options(section) + addn:
                                displayed_option = options[ea_opt['option']]
                                if ea_opt['name'] == opt:
                                    if 'value' in ea_opt:
                                        if ea_opt['value'] == opt_value:
                                            options[ea_opt['option']] = True
                                        else:
                                            options[ea_opt['option']] = False
                                    else:
                                        options[ea_opt['option']] = opt_value
                                    if options[ea_opt['option']
                                               ] != displayed_option:
                                        if options['log_debug']:
                                            log.debug(
                                                'Options overridden for option %s = %s', ea_opt['option'], opt_value)

                                        opt_text = unicode(opt_value)
                                        append_tag(
                                            tm, '003_information:options_overridden', unicode(
                                                ea_opt['name']) + ' = ' + opt_text)

    if orig_metadata:
        keep_list = options['cea_keep'].split(",")
        if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
            keep_list.append(options['cea_lyrics_tag'])
        for tagx in keep_list:
            tag = tagx.strip()
            if tag in orig_metadata:
                tm[tag] = orig_metadata[tag]
    tm['~ce_options'] = options
    tm['~ce_file'] = music_file
    if options['log_info']:
        log.info('Get_options is returning options: %s', options)
        log.info('... and file: %s', music_file)


def plugin_options(type):
    """
    :param type: artists, tag, workparts or other
    :return: the relevant dictionary for the type
    This function contains all the options data in one place - to prevent multiple repetitions elsewhere
    """

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
         'default': 'choir, choir vocals, chorus, singers, domchors, domspatzen, koor, kammerkoor'
         },
        {'option': 'cea_groups',
         'name': 'group strings',
         'type': 'Text',
         'default': 'ensemble, band, group, trio, quartet, quintet, sextet, septet, octet, chamber, consort, players, '
                    'les ,the , quartett'
         },
        {'option': 'cea_aliases',
         'name': 'replace artist name with alias?',
         'value': 'replace',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_aliases_composer',
         'name': 'replace artist name with alias?',
         'value': 'composer',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cea_no_aliases',
         'name': 'replace artist name with alias?',
         'value': 'no replace',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cea_alias_overrides',
         'name': 'alias vs credited-as',
         'value': 'alias over-rides',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_credited_overrides',
         'name': 'alias vs credited-as',
         'value': 'credited-as over-rides',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cea_ra_use',
         'name': 'use recording artist',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_ra_trackartist',
         'name': 'recording artist name style',
         'value': 'track artist',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cea_ra_performer',
         'name': 'recording artist name style',
         'value': 'performer',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_ra_replace_ta',
         'name': 'recording artist effect on track artist',
         'value': 'replace',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_ra_noblank_ta',
         'name': 'disallow blank recording artist',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cea_ra_merge_ta',
         'name': 'recording artist effect on track artist',
         'value': 'merge',
         'type': 'Boolean',
         'default': False
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
        {'option': 'cea_no_lyricists',
         'name': 'exclude lyricists if no vocals',
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
         'name': 'use release credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_release_relationship_credited',
         'name': 'use release relationship credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_group_credited',
         'name': 'use release-group credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_recording_credited',
         'name': 'use recording credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_recording_relationship_credited',
         'name': 'use recording relationship credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_track_credited',
         'name': 'use track credited-as name',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_performer_credited',
         'name': 'use credited-as name for performer',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_composer_credited',
         'name': 'use credited-as name for composer',
         'type': 'Boolean',
         'default': False
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
        {'option': 'cea_lyricist',
         'name': 'lyricist',
         'type': 'Text',
         'default': ''
         },
        {'option': 'cea_librettist',
         'name': 'librettist',
         'type': 'Text',
         'default': 'libretto'
         },
        {'option': 'cea_writer',
         'name': 'writer',
         'type': 'Text',
         'default': 'writer'
         },
        {'option': 'cea_arranger',
         'name': 'arranger',
         'type': 'Text',
         'default': 'arr.'
         },
        {'option': 'cea_reconstructed',
         'name': 'reconstructed by',
         'type': 'Text',
         'default': 'reconstructed'
         },
        {'option': 'cea_revised',
         'name': 'revised by',
         'type': 'Text',
         'default': 'revised'
         },
        {'option': 'cea_translator',
         'name': 'translator',
         'type': 'Text',
         'default': 'trans.'
         },
        {'option': 'cea_split_lyrics',
         'name': 'split lyrics',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cea_lyrics_tag',
         'name': 'lyrics',
         'type': 'Text',
         'default': 'lyrics'
         },
        {'option': 'cea_album_lyrics',
         'name': 'album lyrics',
         'type': 'Text',
         'default': 'albumnotes'
         },
        {'option': 'cea_track_lyrics',
         'name': 'track lyrics',
         'type': 'Text',
         'default': 'tracknotes'
         },
        {'option': 'cea_tag_sort',
         'name': 'populate sort tags',
         'type': 'Boolean',
         'default': True
         }
    ]

    #  tag mapping lines
    default_list = [
        ('album_soloists, album_ensembles, album_conductors', 'artist, artists', False),
        ('recording_artists', 'artist, artists', True),
        ('soloist_names, ensemble_names, conductors', 'artist, artists', True),
        ('soloists', 'soloists, trackartist', False),
        ('release', 'release_name', False),
        ('work_type', 'genre', False),
        ('ensemble_names', 'band', False),
        ('composers', 'artist', True),
        ('MB_artists', 'composer', True),
        ('arranger', 'composer', True)
    ]
    tag_options = []
    for i in range(0, 16):
        if i < len(default_list):
            default_source = default_list[i][0]
            default_tag = default_list[i][1]
            default_cond = default_list[i][2]
        tag_options.append({'option': 'cea_source_' + unicode(i + 1),
                            'name': 'line ' + unicode(i + 1) + '_source',
                            'type': 'Combo',
                            'default': default_source
                            })
        tag_options.append({'option': 'cea_tag_' + unicode(i + 1),
                            'name': 'line ' + unicode(i + 1) + '_tag',
                            'type': 'Text',
                            'default': default_tag
                            })
        tag_options.append({'option': 'cea_cond_' + unicode(i + 1),
                            'name': 'line ' + unicode(i + 1) + '_conditional',
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
         # proximity of new words in title comparison which will result in
         # infill words being included as well. 2 means 2-word 'gaps' of
         # existing words between new words will be treated as 'new'
         'name': 'in-string proximity trigger',
         'type': 'Integer',
         'default': 2
         },
        {'option': 'cwp_end_proximity',
         # proximity measure to be used when infilling to the end of the title
         'name': 'end-string proximity trigger',
         'type': 'Integer',
         'default': 1
         },
        {'option': 'cwp_granularity',
         # splitting for matching of parents. 1 = split in two, 2 = split in
         # three etc.
         'name': 'work-splitting',
         'type': 'Integer',
         'default': 1
         },
        {'option': 'cwp_substring_match',
         # Proportion of a string to be matched to a (usually larger) string for
         # it to be considered essentially similar
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
         'default': '(1, one) / (2, two) / (3, three) / (&, and) / (Rezitativ, Recitativo) / (Recitativo, Recitative) / (Arie, Aria)'
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
         'default': True
         },
        {'option': 'cwp_level0_works',
         'name': 'Work source',
         'value': 'Level_0',
         'type': 'Boolean',
         'default': False
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

    # other options (not saved in file tags)
    other_options = [
        {'option': 'use_cache',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_aliases',
         'name': 'replace with alias?',
         'value': 'replace',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_no_aliases',
         'name': 'replace with alias?',
         'value': 'no replace',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_aliases_all',
         'name': 'alias replacement type',
         'value': 'all',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_aliases_greek',
         'name': 'alias replacement type',
         'value': 'non-latin',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_aliases_tagged',
         'name': 'alias replacement type',
         'value': 'tagged works',
         'type': 'Boolean',
         'default': False
         },
        {'option': 'cwp_aliases_tag_text',
         'name': 'use_alias tag text',
         'type': 'Text',
         'default': 'use_alias'
         },
        {'option': 'cwp_aliases_tags_all',
         'name': 'use_alias tags all',
         'type': 'Boolean',
         'default': True
         },
        {'option': 'cwp_aliases_tags_user',
         'name': 'use_alias tags user',
         'type': 'Boolean',
         'default': False
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
    """
    :param config_settings: options from UI
    :return: a (deep) copy of the Classical Extras options
    """
    options = {}
    for option in plugin_options('artists') + plugin_options('tag') \
            + plugin_options('workparts') + plugin_options('other'):
        options[option['option']] = copy.deepcopy(
            config_settings[option['option']])
    return options


def get_aliases(self, album, options, releaseXmlNode):
    """
    :param self:
    :param album:
    :param options:
    :param releaseXmlNode: all the metadata for the release
    :return: Dta is returned via self.artist_aliases and self.artist_credits[album]

    Note regarding aliases and credited-as names:
    In a MB release, an artist can appear in one of six contexts. Each of these is accessible in releaseXmlNode
    and the track and recording contexts are also accessible in trackXmlNode.
    The six contexts are:
    Release-group: credited-as and alias
    Release: credited-as and alias
    Release relationship: credited-as only
    Recording: credited-as and alias
    Recording relationship: credited-as only
    Track: credited-as and alias
    This function collects all the available aliases and as-credited names once (on processing the first track).
    N.B. if more than one release is loaded in Picard, any available alias names loaded so far will be available
    and used. However, as-credited names will only be used from the current release."""

    if 'artist_locale' in config.setting and options['cea_aliases'] or options['cea_aliases_composer']:
        locale = config.setting["artist_locale"]
        lang = locale.split("_")[0]  # NB this is the Picard code in /util

        # Release group artists
        obj = parse_data(options, releaseXmlNode, [], 'release_group')
        get_aliases_and_credits(
            self,
            options,
            album,
            obj,
            lang,
            options['cea_group_credited'])

        # Release artists
        get_aliases_and_credits(
            self,
            options,
            album,
            releaseXmlNode,
            lang,
            options['cea_credited'])
        # Next bit needed to identify artists who are album artists
        self.release_artists_sort[album] = parse_data(
            options,
            releaseXmlNode,
            [],
            'artist_credit',
            'name_credit',
            'artist',
            'sort_name',
            'text')
        # Release relationship artists (credits only)
        if options['cea_release_relationship_credited']:
            get_relation_credits(self, options, album, releaseXmlNode)

        # Track and recording aliases/credits are gathered by parsing the
        # media, track and recording nodes
        media = parse_data(
            options,
            releaseXmlNode,
            [],
            'medium_list',
            'medium')
        for m in media:
            # disc_num = int(parse_data(options, m, [], 'position', 'text')[0])
            # not currently used
            tracks = parse_data(options, m, [], 'track_list', 'track')
            for tlist in tracks:
                for t in tlist:
                    # track_num = int(parse_data(options, t, [], 'number',
                    # 'text')[0]) # not currently used
                    obj = parse_data(options, t, [], 'recording')
                    get_aliases_and_credits(
                        self,
                        options,
                        album,
                        obj,
                        lang,
                        options['cea_recording_credited'])  # recording artists
                    if options['cea_recording_relationship_credited']:
                        # recording relationship artists (credits only)
                        get_relation_credits(self, options, album, obj)
                    get_aliases_and_credits(
                        self, options, album, t, lang, options['cea_track_credited'])  # track artists
    if options['log_info']:
        log.info('Alias and credits info for %s', self)
        log.info('Aliases :%s', self.artist_aliases)
        log.info('Credits :%s', self.artist_credits[album])


def get_artists(log_options, relations, relation_type):
    """
    Get artist info from XML lookup
    :param log_options:
    :param relations:
    :param relation_type: 'release' or 'recording'
    :return:
    """
    artists = []
    artist_types = relation_types[relation_type]
    for artist_type in artist_types:
        type_list = parse_data(
            log_options,
            relations,
            [],
            'attribs.target_type:artist',
            'relation',
            'attribs.type:' +
            artist_type)
        for type_item in type_list:
            artist_name_list = parse_data(
                log_options,
                type_item,
                [],
                'direction.text:backward',
                'artist',
                'name',
                'text')
            artist_sort_name_list = parse_data(
                log_options,
                type_item,
                [],
                'direction.text:backward',
                'artist',
                'sort_name',
                'text')
            if artist_type not in [
                'instrument',
                'vocal',
                'instrument arranger',
                    'vocal arranger']:
                instrument_list = None
            else:
                instrument_list = parse_data(
                    log_options,
                    type_item,
                    [],
                    'direction.text:backward',
                    'attribute_list',
                    'attribute',
                    'text')
                if artist_type == 'vocal':
                    if not instrument_list:
                        instrument_list = ['vocals']
                    elif not any('vocals' in x for x in instrument_list):
                        instrument_list.append('vocals')
            if instrument_list:
                instrument_sort = 3
                s_key = {
                    'lead vocals': 1,
                    'solo': 2,
                    'guest': 4,
                    'additional': 5}
                for inst in s_key:
                    if inst in instrument_list:
                        instrument_sort = s_key[inst]
            else:
                instrument_sort = 0

            type_sort_dict = {'vocal': 1,
                              'instrument': 1,
                              'performer': 0,
                              'performing orchestra': 2,
                              'concertmaster': 3,
                              'conductor': 4,
                              'chorus master': 5,
                              'composer': 6,
                              'writer': 7,
                              'reconstructed by': 8,
                              'instrument arranger': 9,
                              'vocal arranger': 9,
                              'arranger': 11,
                              'orchestrator': 12,
                              'revised by': 13,
                              'lyricist': 14,
                              'librettist': 15,
                              'translator': 16
                              }
            if artist_type in type_sort_dict:
                type_sort = type_sort_dict[artist_type]
            else:
                type_sort = 99
                if log_options['log_error']:
                    log.error(
                        "Error in artist type. Type '%s' is not in dictionary",
                        artist_type)

            artist = (
                artist_type,
                instrument_list,
                artist_name_list,
                artist_sort_name_list,
                instrument_sort,
                type_sort)
            artists.append(artist)
            # Sorted by sort name then instrument_sort then artist type
            artists = sorted(artists, key=lambda x: (x[5], x[3], x[4], x[1]))
            if log_options['log_info']:
                log.info('sorted artists = %s', artists)
    return artists


def set_work_artists(self, album, track, writerList, tm, count):
    """
    :param self is the calling object from Artists or WorkParts
    :param album: the current album
    :param track: the current track
    :param writerList: format [(artist_type, [instrument_list], [name list],[sort_name list]),(.....etc]
    :param tm: track metatdata
    :param count: depth count of recursion in process_work_artists (should equate to part level)
    :return:
    """

    options = self.options[track]
    if not options['classical_work_parts']:
        caller = 'ExtraArtists'
        pre = '~cea'
    else:
        caller = 'PartLevels'
        pre = '~cwp'
    if self.DEBUG:
        log.debug(
            '%s, Class: %s: in set_work_artists for track %s. Count (level) is %s',
            PLUGIN_NAME,
            caller,
            track,
            count)
    # tag strings are a tuple (Picard tag, cwp tag, Picard sort tag, cwp sort
    # tag) (NB this is modelled on set_performer)
    tag_strings = {
        'writer': (
            'composer',
            pre + '_writers',
            'composersort',
            pre + '_writers_sort'),
        'composer': (
            'composer',
            pre + '_composers',
            'composersort',
            pre + '_composers_sort'),
        'lyricist': (
            'lyricist',
            pre + '_lyricists',
            '~lyricists_sort',
            pre + '_lyricists_sort'),
        'librettist': (
            'lyricist',
            pre + '_librettists',
            '~lyricists_sort',
            pre + '_librettists_sort'),
        'revised by': (
            'arranger',
            pre + '_revisors',
            '~arranger_sort',
            pre + '_revisors_sort'),
        'translator': (
            'lyricist',
            pre + '_translators',
            '~lyricists_sort',
            pre + '_translators_sort'),
        'reconstructed by': (
            'arranger',
            pre + '_reconstructors',
            '~arranger_sort',
            pre + '_reconstructors_sort'),
        'arranger': (
            'arranger',
            pre + '_arrangers',
            '~arranger_sort',
            pre + '_arrangers_sort'),
        'instrument arranger': (
            'arranger',
            pre + '_arrangers',
            '~arranger_sort',
            pre + '_arrangers_sort'),
        'orchestrator': (
            'arranger',
            pre + '_orchestrators',
            '~arranger_sort',
            pre + '_orchestrators_sort'),
        'vocal arranger': (
            'arranger',
            '~arranger_sort',
            pre + '_arrangers_sort')}
    # insertions lists artist types where names in the main Picard tags may be
    # updated for annotations
    insertions = ['writer',
                  'lyricist',
                  'librettist',
                  'revised by',
                  'translator',
                  'arranger',
                  'reconstructed by',
                  'orchestrator',
                  'instrument arranger',
                  'vocal arranger']
    no_more_lyricists = False
    if caller == 'PartLevels' and self.lyricist_filled[track]:
        no_more_lyricists = True

    for writer in writerList:
        writer_type = writer[0]
        if writer_type not in tag_strings:
            break
        if no_more_lyricists and (
                writer_type == 'lyricist' or writer_type == 'librettist'):
            break
        if writer[1]:
            inst_list = writer[1][:]
            # take a copy of the list in case (because of list
            # mutability) we need the old one
            instrument = ", ".join(inst_list)
        else:
            instrument = None
        sub_strings = {  # 'instrument arranger': instrument,
            #'vocal arranger': instrument
        }
        if options['cea_arranger']:
            if instrument:
                arr_inst = options['cea_arranger'] + ' ' + instrument
            else:
                arr_inst = options['cea_arranger']
        else:
            arr_inst = instrument
        annotations = {'writer': options['cea_writer'],
                       'lyricist': options['cea_lyricist'],
                       'librettist': options['cea_librettist'],
                       'revised by': options['cea_revised'],
                       'translator': options['cea_translator'],
                       'arranger': options['cea_arranger'],
                       'reconstructed by': options['cea_reconstructed'],
                       'orchestrator': options['cea_orchestrator'],
                       'instrument arranger': arr_inst,
                       'vocal arranger': arr_inst}
        tag = tag_strings[writer_type][0]
        sort_tag = tag_strings[writer_type][2]
        cwp_tag = tag_strings[writer_type][1]
        cwp_sort_tag = tag_strings[writer_type][3]
        cwp_names_tag = cwp_tag[:-1] + '_names'
        if writer_type in sub_strings:
            if sub_strings[writer_type]:
                tag += sub_strings[writer_type]
        if tag:
            if '~ce_tag_cleared_' + \
                    tag not in tm or not tm['~ce_tag_cleared_' + tag] == "Y":
                if tag in tm:
                    if options['log_info']:
                        log.info('delete tag %s', tag)
                    del tm[tag]
            tm['~ce_tag_cleared_' + tag] = "Y"
        if sort_tag:
            if '~ce_tag_cleared_' + \
                    sort_tag not in tm or not tm['~ce_tag_cleared_' + sort_tag] == "Y":
                if sort_tag in tm:
                    del tm[sort_tag]
            tm['~ce_tag_cleared_' + sort_tag] = "Y"

        name_list = writer[2]

        for ind, name in enumerate(name_list):
            sort_name = writer[3][ind]
            no_credit = True
            if self.INFO:
                log.info('In set_work_artists. Name before changes = %s', name)
            # change name to as-credited
            if options['cea_composer_credited']:
                if sort_name in self.artist_credits[album]:
                    no_credit = False
                    name = self.artist_credits[album][sort_name]
            # over-ride with aliases if appropriate
            if (options['cea_aliases'] or options['cea_aliases_composer']) and (
                    no_credit or options['cea_alias_overrides']):
                if sort_name in self.artist_aliases:
                    name = self.artist_aliases[sort_name]
            # fix cyrillic names if not already fixed
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    # if not only_roman_chars(tm[tag]):
                    name = remove_middle(unsort(sort_name))
                    # Only remove middle name where the existing
                    # performer is in non-latin script
            annotated_name = name

            # add annotations and write performer tags
            if writer_type in annotations:
                if annotations[writer_type]:
                    annotated_name += ' (' + annotations[writer_type] + ')'
            if instrument:
                instrumented_name = name + ' (' + instrument + ')'
            else:
                instrumented_name = name

            if writer_type in insertions and options['cea_arrangers']:
                self.append_tag(tm, tag, annotated_name)
            else:
                if options['cea_arrangers'] or writer_type == tag:
                    self.append_tag(tm, tag, name)

            if options['cea_arrangers'] or writer_type == tag:
                if sort_tag:
                    self.append_tag(tm, sort_tag, sort_name)
                    if options['cea_tag_sort'] and '~' in sort_tag:
                        explicit_sort_tag = sort_tag.replace('~', '')
                        self.append_tag(tm, explicit_sort_tag, sort_name)

            self.append_tag(tm, cwp_tag, annotated_name)
            self.append_tag(tm, cwp_names_tag, instrumented_name)

            if cwp_sort_tag:
                self.append_tag(tm, cwp_sort_tag, sort_name)

        if caller == 'PartLevels' and (
                writer_type == 'lyricist' or writer_type == 'librettist'):
            self.lyricist_filled[track] = True
            if self.DEBUG:
                log.debug(
                    '%s: Filled lyricist for track %s. Not looking further',
                    PLUGIN_NAME,
                    track)

        if writer_type == 'composer':
            if sort_name in self.release_artists_sort[album]:
                composerlast = sort_name.split(",")[0]
                self.append_tag(tm, '~cea_album_composers', name)
                self.append_tag(tm, '~cea_album_composers_sort', sort_name)
                self.append_tag(
                    tm, '~cea_album_track_composer_lastnames', composerlast)
                composer_last_names(self, tm, album)



# Non-Latin character processing
latin_letters = {}


def is_latin(uchr):
    """Test whether character is in Latin script"""
    try:
        return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(
            uchr, 'LATIN' in unicodedata.name(uchr))


def only_roman_chars(unistr):
    """Test whether string is in Latin script"""
    return all(is_latin(uchr)
               for uchr in unistr
               if uchr.isalpha())


def get_roman(string):
    """Transliterate cyrillic script to Latin script"""
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
    """To remove middle names of Russian composers"""
    plist = performer.split()
    if len(plist) == 3:
        return plist[0] + ' ' + plist[2]
    else:
        return performer


# Sorting etc.


# def sort_field(performer):
#     """
#     To create a sort
#     No longer used as all sort names are now sourced from XML lookup
#     """
#     sorter = re.compile(r'(.*)\s(.*)$')
#     match = sorter.search(performer)
#     if match:
#         return match.group(2) + ", " + match.group(1)
#     else:
#         return performer


def unsort(performer):
    """
    To take a sort field and recreate the name
    Only now used for last-ditch cyrillic translation - superseded by 'translate_from_sortname'
    """

    sorted_list = performer.split(', ')
    sorted_list.reverse()
    for i, item in enumerate(sorted_list):
        if item[-1] != "'":
            sorted_list[i] += ' '
    return ''.join(sorted_list).strip()


def translate_from_sortname(name, sortname):
    """
    'Translate' the artist name by reversing the sortname.
    Code is from picard/util/__init__.py
    """
    for c in name:
        ctg = unicodedata.category(c)
        if ctg[0] == "L" and unicodedata.name(c).find("LATIN") == -1:
            for separator in (" & ", "; ", " and ", " vs. ", " with ", " y "):
                if separator in sortname:
                    parts = sortname.split(separator)
                    break
            else:
                parts = [sortname]
                separator = ""
            return separator.join(map(_reverse_sortname, parts))
    return name


def _reverse_sortname(sortname):
    """
    Reverse sortnames.
    Code is from picard/util/__init__.py
    """

    chunks = [a.strip() for a in sortname.split(",")]
    if len(chunks) == 2:
        return "%s %s" % (chunks[1], chunks[0])
    elif len(chunks) == 3:
        return "%s %s %s" % (chunks[2], chunks[1], chunks[0])
    elif len(chunks) == 4:
        return "%s %s, %s %s" % (chunks[1], chunks[0], chunks[3], chunks[2])
    else:
        return sortname.strip()


def stripsir(performer):
    """Remove honorifics from names"""
    performer = performer.replace(u'\u2010', u'-').replace(u'\u2019', u"'")
    sir = re.compile(r'(.*)\b(Sir|Maestro|Dame)\b\s*(.*)', re.IGNORECASE)
    match = sir.search(performer)
    if match:
        return match.group(1) + match.group(3)
    else:
        return performer


# def swap_prefix(performer):
#     """NOT CURRENTLY USED. Create sort fields for ensembles etc., by placing the prefix (see constants) at the end"""
#     prefix = '|'.join(prefixes)
#     swap = re.compile(r'^(' + prefix + r')\b\s*(.*)', re.IGNORECASE)
#     match = swap.search(performer)
#     if match:
#         return match.group(2) + ", " + match.group(1)
#     else:
#         return performer


def replace_roman_numerals(s):
    """Replaces roman numerals include in s, where followed by punctuation, by digits"""
    p = re.compile(
        r'\b(M{0,4}(CM|CD|D?)?C{0,3}(XC|XL|L?)?X{0,3}(IX|IV|V?)?I{0,3})\b(\.|:|,|;|$)',
        # was
        # r'(^|\s)(\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b)(\W|\s|$)',
        re.IGNORECASE | re.UNICODE)  # Matches Roman numerals (+ ensure non-Latin chars treated as word chars)
    romans = p.findall(s)
    for roman in romans:
        if roman[0]:
            numerals = unicode(roman[0])
            digits = unicode(from_roman(numerals))
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
    """
    :param s1: substring 1
    :param s2: substring 2
    :return: {'string': the longest common substring,
        'start': the start position in s1,
        'length': the length of the common substring}
    NB this also works on list arguments - i.e. it will find the longest common sub-list
    """
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
    return {'string': s1[x_longest - longest: x_longest],
            'start': x_longest - longest, 'length': x_longest}


def longest_common_sequence(list1, list2, minstart=0, maxstart=0):
    """
    :param list1: list 1
    :param list2: list 2
    :param minstart: the earliest point to start looking for a match
    :param maxstart: the latest point to start looking for a match
    :return: {'sequence': the common subsequence, 'length': length of subsequence}
    maxstart must be >= minstart. If they are equal then the start point is fixed.
    Note that this only finds subsequences starting at the same position
    Use longest_common_substring for the more general problem
    """
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
    """
    :param options: options passed from eith Artists or Workparts
    :param tm: track metadata
    :return: None - action is through setting tm contents
    This is a common function for Artists and Workparts which should only run after both sections have completed for
    a given track. If, say, Artists calls it and Workparts is not done,
    then it will not execute until Workparts calls it (and vice versa).
    """
    ERROR = options["log_error"]
    WARNING = options["log_warning"]
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
            log.info('Option %s of %s. Option= %s, Value= %s',
                     ind + 1, len(options), opt, options[opt])
    # album
    if tm['~cea_album_composer_lastnames']:
        if isinstance(tm['~cea_album_composer_lastnames'], list):
            last_names = tm['~cea_album_composer_lastnames']
        else:
            last_names = tm['~cea_album_composer_lastnames'].split(';')
        if options['cea_composer_album']:
            # save it as a list to prevent splitting when appending tag
            tm['~cea_release'] = [tm['album']]
            new_last_names = []
            for last_name in last_names:
                last_name = last_name.strip()
                new_last_names.append(last_name)
            if len(new_last_names) > 0:
                tm['album'] = "; ".join(new_last_names) + ": " + tm['album']

    if options['cea_no_lyricists'] and 'vocals' not in tm['~cea_performers']:
        if 'lyricist' in tm:
            del tm['lyricist']
    for lyricist_tag in ['lyricists', 'librettists', 'translators']:
        if '~cwp_' + lyricist_tag in tm:
            del tm['~cwp_' + lyricist_tag]

    sort_tags = options['cea_tag_sort']
    if sort_tags:
        tm['artists_sort'] = tm['~artists_sort']
    for i in range(0, 16):
        tagline = options['cea_tag_' + unicode(i + 1)].split(",")
        source_group = options['cea_source_' + unicode(i + 1)].split(",")
        conditional = options['cea_cond_' + unicode(i + 1)]
        for item, tagx in enumerate(tagline):
            tag = tagx.strip()
            sort = sort_suffix(tag)
            if not conditional or tm[tag] == "":
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
                            elif "~cwp_" + source_item in tm:
                                si = tm['~cwp_' + source_item]
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
                    if '~cea_' + source in tm or '~cwp_' + source in tm:
                        for prefix in ['~cea_', '~cwp_']:
                            if prefix + source in tm:
                                if INFO:
                                    log.info(prefix)
                                append_tag(
                                    tm, tag, tm[prefix + source], ['; '])
                                if sort_tags:
                                    if prefix + no_names_source + source_sort in tm:
                                        if INFO:
                                            log.info(prefix + " sort")
                                        append_tag(
                                            tm, tag + sort, tm[prefix + no_names_source + source_sort], ['; '])
                    elif source in tm or '~' + source in tm:
                        if INFO:
                            log.info("Picard")
                        for p in ['', '~']:
                            if p + source in tm:
                                append_tag(
                                    tm, tag, tm[p + source], ['; ', '/ '])
                        if sort_tags:
                            if "~" + source + source_sort in tm:
                                source = "~" + source
                            if source + source_sort in tm:
                                if INFO:
                                    log.info("Picard sort")
                                append_tag(tm, tag + sort,
                                           tm[source + source_sort], ['; ', '/ '])
                    elif len(source) > 0 and source[0] == "\\":
                        append_tag(tm, tag, source[1:], ['; ', '/ '])
                    else:
                        pass

    if ERROR and "~cea_error" in tm:
        append_tag(tm, '001_errors', tm['~cea_error'], ['; '])
    if WARNING and "~cea_warning" in tm:
        append_tag(tm, '002_warnings', tm['~cea_warning'], ['; '])

    if not DEBUG:
        if '~cea_works_complete' in tm:
            del tm['~cea_works_complete']
        if '~cea_artists_complete' in tm:
            del tm['~cea_artists_complete']
        del_list = []
        for t in tm:
            if 'ce_tag_cleared' in t:
                del_list.append(t)
        for t in del_list:
            del tm[t]

    # if options over-write enabled, remove it after processing one album
    options['ce_options_overwrite'] = False


def sort_suffix(tag):
    """To determine what sort suffix is appropriate for a given tag"""
    if tag == "composer" or tag == "artist" or tag == "albumartist" or tag == "trackartist":
        sort = "sort"
    else:
        sort = "_sort"
    return sort


def append_tag(tm, tag, source, separators=[]):
    """
    :param tm: track metadata
    :param tag: tag to be appended to
    :param source: item to append to tag
    :param separators: characters which may be used to split string into a list
        (any of the characters will be a split point)
    :return: None. Action is on tm
    """
    if tag:
        if config.setting['log_debug']:
            log.debug(
                '%s: appending source: %r to tag: %s (source is type %s) ...',
                PLUGIN_NAME,
                source,
                tag,
                type(source))
            log.debug('... existing tag contents = %r', tm[tag])
        if source and len(source) > 0:
            if isinstance(source, basestring):
                source = source.replace(u'\u2010', u'-')
                source = source.replace(u'\u2019', u"'")
                source = re.split('|'.join(separators), source)

            if tag in tm:
                for source_item in source:
                    if isinstance(source_item, basestring):
                        source_item = source_item.replace(u'\u2010', u'-')
                    if source_item not in tm[tag]:
                        if not isinstance(tm[tag], list):
                            tag_list = re.split('|'.join(separators), tm[tag])
                            tag_list.append(source_item)
                            tm[tag] = tag_list
                            # Picard will have converted it from list to string
                        else:
                            tm[tag].append(source_item)
            else:
                if tag and tag != "":
                    if isinstance(source, list):
                        if tag == 'artists_sort':
                            # no artists_sort tag in Picard - just a hidden var
                            hidden = tm['~artists_sort']
                            if not isinstance(hidden, list):
                                hidden = re.split('|'.join(separators), hidden)
                            source = add_list_uniquely(source, hidden)
                        for source_item in source:
                            if isinstance(source_item, basestring):
                                source_item = source_item.replace(
                                    u'\u2010', u'-')
                                source_item = source_item.replace(
                                    u'\u2019', u"'")

                            if tag not in tm:
                                tm[tag] = [source_item]
                            else:
                                if not isinstance(tm[tag], list):
                                    tag_list = re.split(
                                        '|'.join(separators), tm[tag])
                                    tag_list.append(source_item)
                                    tm[tag] = tag_list
                                else:
                                    tm[tag].append(source_item)
                    else:
                        tm[tag] = [source]
                        # probably makes no difference to specify a list as Picard will convert the tag to string,
                        # but do it anyway


def parse_data(options, obj, response_list, *match):
    """
    :param options:
    :param obj: an XmlNode object, list or dictionary containing nodes
    :param response_list: working memory for recursive calls
    :param match: list of items to search for in node (see detailed notes below
    :return: a list of matching items (always a list, even if only one item)
    This function takes any XmlNode object, or list thereof,
    and extracts a list of all objects exactly matching the hierarchy listed in match
    match should contain list of each node in hierarchical sequence, with no gaps in the sequence of nodes, to lowest level required.
    Insert attribs.attribname:attribvalue in the list to select only branches where attribname is attribvalue.
    Insert childname.text:childtext in the list to select only branches where a sibling with childname has text childtext.
      (Note: childname can be a dot-list if the text is more than one level down - e.g. child1.child2) # TODO - Check this works fully
    """

    DEBUG = False  # options["log_debug"]
    INFO = False  # options["log_info"]
    # Over-ridden options as these can be VERY wordy

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
                response = parse_data(
                    options, obj[match[0]], response_list, *match_list)
                response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
        elif '.' in match[0]:
            test = match[0].split(':')
            match2 = test[0].split('.')
            test_data = parse_data(options, obj, [], *match2)
            if len(test) > 1:
                if test[1] in test_data:
                    if len(match) == 1:
                        response = obj
                        response_list.append(response)
                    else:
                        match_list = list(match)
                        match_list.pop(0)
                        response = parse_data(
                            options, obj, response_list, *match_list)
                        response_list + response
            else:
                response = parse_data(options, obj, response_list, *match2)
                response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
        else:
            if 'children' in obj:
                response = parse_data(
                    options, obj['children'], response_list, *match)
                response_list + response
            if INFO:
                log.info('response_list: %s', response_list)
            return response_list
    else:
        if INFO:
            log.info('response_list: %s', response_list)
        return response_list


def get_artist_credit(options, obj):
    """
    :param options:
    :param obj: an XmlNode
    :return: a list of as-credited names
    """
    name_credit_list = parse_data(
        options, obj, [], 'artist_credit', 'name_credit')
    credit_list = []
    if name_credit_list:
        for name_credits in name_credit_list:
            for name_credit in name_credits:
                credited_artist = parse_data(
                    options, name_credit, [], 'name', 'text')
                if credited_artist:
                    name = parse_data(
                        options, name_credit, [], 'artist', 'name', 'text')
                    sort_name = parse_data(
                        options, name_credit, [], 'artist', 'sort_name', 'text')
                    credit_item = (credited_artist, name, sort_name)
                    credit_list.append(credit_item)
        return credit_list


def get_aliases_and_credits(self, options, album, obj, lang, credits):
    """
    :param album:
    :param self: This relates to the object in the class which called this function
    :param options:
    :param obj: an XmlNode
    :param lang: The language selected in the Picard metadata options
    :param credits: The options item to determine what as-credited names are being sought
    :return: None. Sets self.artist_aliases and self.artist_credits[album]
    """
    name_credit_list = parse_data(
        options, obj, [], 'artist_credit', 'name_credit')
    artist_list = parse_data(options, name_credit_list, [], 'artist')
    for artist in artist_list:
        sort_names = parse_data(options, artist, [], 'sort_name', 'text')
        if sort_names:
            aliases = parse_data(
                options,
                artist,
                [],
                'alias_list',
                'alias',
                'attribs.locale:' +
                lang,
                'attribs.primary:primary',
                'text')
            if aliases:
                self.artist_aliases[sort_names[0]] = aliases[0]
    if credits:
        for name_credits in name_credit_list:
            for name_credit in name_credits:
                credited_artists = parse_data(
                    options, name_credit, [], 'name', 'text')
                if credited_artists:
                    sort_names = parse_data(
                        options, name_credit, [], 'artist', 'sort_name', 'text')
                    if sort_names:
                        self.artist_credits[album][sort_names[0]
                                                   ] = credited_artists[0]


def get_relation_credits(self, options, album, obj):
    """
    :param self:
    :param options: UI options
    :param album: current album
    :param obj: XmloOde
    :return: None
    """
    rels = parse_data(
        options,
        obj,
        [],
        'relation_list',
        'attribs.target_type:artist',
        'relation')
    for rel in rels:
        for artist in rel:
            sort_names = parse_data(
                options, artist, [], 'artist', 'sort_name', 'text')
            if sort_names:
                credited_artists = parse_data(
                    options, artist, [], 'target_credit', 'text')
                if credited_artists:
                    self.artist_credits[album][sort_names[0]
                                               ] = credited_artists[0]


def composer_last_names(self, tm, album):
    """
    :param self:
    :param tm:
    :param album:
    :return: None
    Sets composer last names for album prefixing
    """
    if '~cea_album_track_composer_lastnames' in tm:
        if not isinstance(tm['~cea_album_track_composer_lastnames'], list):
            atc_list = re.split(
                '|'.join(
                    self.SEPARATORS),
                tm['~cea_album_track_composer_lastnames'])
        else:
            atc_list = tm['~cea_album_track_composer_lastnames']
        for atc_item in atc_list:
            composer_lastnames = atc_item.strip()
            track_length = time_to_secs(tm['~length'])
            if album in self.album_artists:
                if 'composer_lastnames' in self.album_artists[album]:
                    if composer_lastnames not in self.album_artists[album]['composer_lastnames']:
                        self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                            'length': track_length}
                    else:
                        self.album_artists[album]['composer_lastnames'][composer_lastnames]['length'] += track_length
                else:
                    self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                        'length': track_length}
            else:
                self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                    'length': track_length}
    else:
        if self.WARNING:
            log.warning(
                "%s: No _cea_album_track_composer_lastnames variable available for recording \"%s\".",
                PLUGIN_NAME,
                tm['title'])
        if 'composer' in tm:
            self.append_tag(
                tm,
                '~cea_warning',
                'Composer for this track is not in album artists and will not be available to prefix album')
        else:
            self.append_tag(
                tm,
                '~cea_warning',
                'No composer for this track, but checking parent work.')


# def substitute_name(credit_list, name, sort_name=None):
#     """
#     NOT CURRENTLY USED
#     :param credit_list:
#     :param name:
#     :param sort_name:
#     :return:
#     """
#     new_name = None
#     for artist_credit in credit_list:
#         if not isinstance(artist_credit[0], list):
#             if name == artist_credit[1] or (
#                     sort_name and sort_name == artist_credit[2]):
#                 new_name = artist_credit[0]
#         else:
#             if artist_credit[0]:
#                 for i, n in enumerate(artist_credit[0]):
#                     if name == artist_credit[1][i] or (
#                             sort_name and sort_name == artist_credit[2][i]):
#                         new_name = n
#     return new_name


def add_list_uniquely(list_to, list_from):
    """
    :param list_to:
    :param list_from:
    :return: appends only unique elements of list 2 to list 1
    """
    #
    if list_to and list_from:
        if not isinstance(list_to, list):
            list_to = str_to_list(list_to)
        if not isinstance(list_from, list):
            list_from = str_to_list(list_from)
        for list_item in list_from:
            if list_item not in list_to:
                list_to.append(list_item)
    else:
        if list_from:
            list_to = list_from
    return list_to


def str_to_list(s):
    """
    :param s:
    :return: list from string using ; as separator
    """
    if not isinstance(s, basestring):
        return list(s)
    else:
        return s.split('; ')


def interpret(tag):
    """
    :param tag:
    :return: safe form of eval(tag)
    """
    if isinstance(tag, basestring):
        try:
            tag = tag.strip(' \n\t')
            return eval(tag)
        except SyntaxError:
            return ''
    else:
        return tag


def time_to_secs(a):
    """
    :param a: string x:x:x
    :return: seconds
    converts string times to seconds
    """
    ax = a.split(':')
    ax = ax[::-1]
    t = 0
    for i, x in enumerate(ax):
        t += int(x) * (60 ** i)
    return t


def seq_last_names(self, album):
    """
    Sequences composer last names for album prefix by the total lengths of their tracks
    :self:
    :param album:
    :return:
    """
    ln = []
    if album in self.album_artists and 'composer_lastnames' in self.album_artists[album]:
        for x in self.album_artists[album]['composer_lastnames']:
            if 'length' in self.album_artists[album]['composer_lastnames'][x]:
                ln.append([x, self.album_artists[album]
                           ['composer_lastnames'][x]['length']])
            else:
                return []
        ln = sorted(ln, key=lambda a: a[1])
        ln = ln[::-1]
    return [a[0] for a in ln]

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
        self.globals = collections.defaultdict(dict)
        # collection of global variables for this class
        self.album_performers = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of performers who have release relationships, not track
        # relationships
        self.artist_aliases = {}
        # collection of alias names - format is {sort_name: alias_name, ...}
        self.artist_credits = collections.defaultdict(dict)
        # collection of credited-as names - format is {album: {sort_name: credit_name,
        # ...}, ...}
        self.release_artists_sort = collections.defaultdict(list)
        # collection of release artists - format is {album: [sort_name_1,
        # sort_name_2, ...]}

    def add_artist_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):
        """
        Main routine run for each track of release
        :param album: Current release
        :param track_metadata: track metadata dictionary
        :param trackXmlNode: Everything in the track node downwards
        :param releaseXmlNode: Everything in the release node downwards (so includes all track nodes)
        :return:
        """
        # log.info('trackXmlNode = %s', trackXmlNode) # NB can crash Picard
        # log.info('releaseXmlNode = %s', releaseXmlNode) # NB can crash Picard

        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]
        tm = track.metadata

        if '~ce_options' not in tm:
            # log.error('Artists gets track first...')
            get_options(album, track)
        options = interpret(tm['~ce_options'])
        if not options:
            if self.ERROR:
                log.error(
                    '%s: Artists. Failure to read options for track %s. options = %s',
                    PLUGIN_NAME,
                    track,
                    tm['~ce_options'])
            options = config.setting
        self.options[track] = options

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
        self.SEPARATORS = ['; ', '/ ', ';', '/']

        if self.DEBUG:
            log.debug("%s: add_artist_info", PLUGIN_NAME)

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

        # log.error('disc = %s, track = %s', tm['discnumber'], tm['tracknumber']) # not currently used
        # first time for this album (reloads each refresh)
        if tm['discnumber'] == '1' and tm['tracknumber'] == '1':
            # get artist aliases - these are cached so can be re-used across
            # releases, but are reloaded with each refresh
            get_aliases(self, album, options, releaseXmlNode)

            # xml_type = 'release'
            # get performers etc who are related at the release level
            relation_list = parse_data(
                options, releaseXmlNode, [], 'relation_list')
            album_performerList = get_artists(
                options, relation_list, 'release')
            self.album_performers[album] = album_performerList

        else:
            if album in self.album_performers:
                album_performerList = self.album_performers[album]
            else:
                album_performerList = []

        if 'recording' in trackXmlNode.children:
            self.globals[track]['is_recording'] = True
            for record in trackXmlNode.children['recording']:
                # Note that the lists below reflect https://musicbrainz.org/relationships/artist-recording
                # Any changes to that DB structure will require changes here

                # get recording artists data
                recording_artist_list = parse_data(
                    options, record, [], 'artist_credit', 'name_credit')
                if recording_artist_list:
                    recording_artist = []
                    recording_artistsort = []
                    recording_artists = []
                    recording_artists_sort = []
                    locale = config.setting["artist_locale"]
                    # NB this is the Picard code in /util
                    lang = locale.split("_")[0]

                    # Set naming option
                    # Put naming style into preferential list

                    # naming as for vanilla Picard for track artists
                    if options['cea_ra_trackartist']:
                        if config.setting['translate_artist_names'] and lang:
                            if config.setting['standardize_artists']:
                                name_style = ['alias', 'sort']
                            else:
                                name_style = ['alias', 'credit', 'sort']
                        else:
                            if not config.setting['standardize_artists']:
                                name_style = ['credit']
                            else:
                                name_style = []
                    # naming as for performers in classical extras
                    elif options['cea_ra_performer']:
                        # if config.setting['standardize_artists']:
                        if options['cea_aliases']:
                            if options['cea_alias_overrides']:
                                name_style = ['alias', 'credit']
                            else:
                                name_style = ['credit', 'alias']
                        else:
                            name_style = ['credit']

                    else:
                        name_style = []
                    if self.INFO:
                        log.info(
                            'Priority order of naming style for recording artists = %s',
                            name_style)
                    # Get recording artist and apply style
                    for acs in recording_artist_list:
                        for ncs in acs:
                            artistlist = parse_data(
                                options, ncs, [], 'artist', 'name', 'text')
                            sortlist = parse_data(
                                options, ncs, [], 'artist', 'sort_name', 'text')
                            names = {}
                            if lang:
                                names['alias'] = parse_data(
                                    options,
                                    ncs,
                                    [],
                                    'artist',
                                    'alias_list',
                                    'alias',
                                    'attribs.locale:' +
                                    lang,
                                    'attribs.primary:primary',
                                    'text')
                            else:
                                names['alias'] = []
                            names['credit'] = parse_data(
                                options, ncs, [], 'name', 'text')
                            pairslist = zip(artistlist, sortlist)
                            names['sort'] = [
                                translate_from_sortname(
                                    *pair) for pair in pairslist]
                            for style in name_style:
                                if names[style]:
                                    artistlist = names[style]
                                    break
                            joinlist = parse_data(
                                options, ncs, [], 'attribs.joinphrase')

                            if artistlist:
                                recording_artist.append(artistlist[0])
                                recording_artistsort.append(sortlist[0])
                                recording_artists.append(artistlist[0])
                                recording_artists_sort.append(sortlist[0])

                            if joinlist:
                                recording_artist.append(joinlist[0])
                                recording_artistsort.append(joinlist[0])

                    recording_artist_str = ''.join(recording_artist)
                    recording_artistsort_str = ''.join(recording_artistsort)
                    self.append_tag(
                        tm, '~cea_recording_artists', recording_artists)
                    self.append_tag(
                        tm,
                        '~cea_recording_artists_sort',
                        recording_artists_sort)
                    self.append_tag(
                        tm, '~cea_recording_artist', recording_artist_str)
                    self.append_tag(
                        tm,
                        '~cea_recording_artistsort',
                        recording_artistsort_str)
                else:
                    tm['~cea_recording_artists'] = ''
                    tm['~cea_recording_artists_sort'] = ''
                    tm['~cea_recording_artist'] = ''
                    tm['~cea_recording_artistsort'] = ''

                # use recording artist options
                tm['~cea_MB_artists'] = tm['artists']
                tm['~cea_MB_artists_sort'] = tm['~artists_sort']

                if options['cea_ra_use']:
                    if options['cea_ra_replace_ta']:
                        if tm['~cea_recording_artist']:
                            tm['artist'] = tm['~cea_recording_artist']
                            tm['artistsort'] = tm['~cea_recording_artistsort']
                            tm['artists'] = tm['~cea_recording_artists']
                            tm['~artists_sort'] = tm['~cea_recording_artists_sort']
                        elif not options['cea_ra_noblank_ta']:
                            tm['artist'] = ''
                            tm['artistsort'] = ''
                            tm['artists'] = ''
                            tm['~artists_sort'] = ''
                    elif options['cea_ra_merge_ta']:
                        if tm['~cea_recording_artist']:
                            tm['artists'] = add_list_uniquely(
                                tm['artists'], tm['~cea_recording_artists'])
                            tm['~artists_sort'] = add_list_uniquely(
                                tm['~artists_sort'], tm['~cea_recording_artists_sort'])
                            if tm['artist'] != tm['~cea_recording_artist']:
                                tm['artist'] = tm['artist'] + \
                                    ' (' + tm['~cea_recording_artist'] + ')'
                                tm['artistsort'] = tm['artistsort'] + \
                                    ' (' + tm['~cea_recording_artistsort'] + ')'

                # xml_type = 'recording'
                relation_list = parse_data(
                    options, record, [], 'relation_list')
                performerList = album_performerList + \
                    get_artists(options, relation_list, 'recording')
                # returns [(artist type, instrument or None, artist name, artist sort name, instrument sort, type sort)]
                # where instrument sort places solo ahead of additional etc. and type sort applies a custom sequencing
                # to the artist types
                if performerList:
                    if self.DEBUG:
                        log.debug(
                            "%s: Performers: %s",
                            PLUGIN_NAME,
                            performerList)
                    self.set_performer(album, track, performerList, tm)

                if not options['classical_work_parts']:
                    work_artist_list = parse_data(
                        options,
                        record,
                        [],
                        'relation_list',
                        'attribs.target_type:work',
                        'relation',
                        'attribs.type:performance',
                        'work',
                        'relation_list',
                        'attribs.target_type:artist')
                    work_artists = get_artists(
                        options, work_artist_list, 'work')
                    set_work_artists(self, album, track, work_artists, tm, 0)
                # otherwise composers etc. will be set in work parts
        if track_metadata['tracknumber'] == track_metadata['totaltracks'] and track_metadata[
                'discnumber'] == track_metadata['totaldiscs']:  # last track
            self.process_album(album)

    # Checks for ensembles
    def ensemble_type(self, performer):
        """
        Returns ensemble types
        :param performer:
        :return:
        """
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

    def process_album(self, album):
        """
        Perform final processing after all tracks read
        :param album:
        :return:
        """
        # process lyrics tags
        common = []
        first = True
        tmlyrics_list = {}
        for track in self.track_listing:
            options = self.options[track]
            if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
                tm = track.metadata
                lyrics_tag = options['cea_lyrics_tag']
                if tm[lyrics_tag]:
                    # turn text into word lists to speed processing
                    tmlyrics_list[track] = tm[lyrics_tag].split()
                    if first:
                        common = tmlyrics_list[track]
                        first = False
                    else:
                        lcs = longest_common_substring(
                            tmlyrics_list[track], common)
                        common = lcs['string']

                else:
                    common = []
            else:
                common = []
        if common:
            for track in self.track_listing:
                options = self.options[track]
                if options['cea_split_lyrics']:
                    tm = track.metadata
                    lcs = longest_common_substring(
                        tmlyrics_list[track], common)
                    start = lcs['start']
                    length = lcs['length']
                    end = start + length
                    # log.error('lyrics start: %s, end: %s', start, end)
                    unique = tmlyrics_list[track][:start] + \
                        tmlyrics_list[track][end:]
                    tm['~cea_track_lyrics'] = ' '.join(unique)
                    tm['~cea_album_lyrics'] = ' '.join(common)
                    if options['cea_album_lyrics']:
                        tm[options['cea_album_lyrics']] = tm['~cea_album_lyrics']
                    if options['cea_track_lyrics']:
                        tm[options['cea_track_lyrics']] = tm['~cea_track_lyrics']

        for track in self.track_listing:
            options = self.options[track]
            tm = track.metadata
            tm['~cea_version'] = PLUGIN_VERSION
            blank_tags = options['cea_blank_tag'].split(
                ",") + options['cea_blank_tag_2'].split(",")

            # set work-type before any tags are blanked
            # (this will be more customisable when genre UI is introduced)
            if options['cea_genres']:
                if (self.globals[track]['is_recording'] and options['classical_work_parts']
                        and '~artists_sort' in tm and 'composersort' in tm
                        and any(x in tm['~artists_sort'] for x in tm['composersort'])
                        and 'writer' not in tm) \
                        or ('is_classical' in tm and tm['is_classical'] == '1'):
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
                                soloists = re.split(
                                    '|'.join(
                                        self.SEPARATORS),
                                    tm['~cea_soloists'])
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
                            soloists = re.split(
                                '|'.join(
                                    self.SEPARATORS),
                                tm['~cea_soloists'])
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
            if not options['classical_work_parts']:
                if 'composer_lastnames' in self.album_artists[album]:
                    last_names = seq_last_names(self, album)
                    self.append_tag(
                        tm, '~cea_album_composer_lastnames', last_names)
            # otherwise this is done in the workparts class, which has all
            # composer info

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
                            self.cea_options['Classical Extras']['Artists options'][opt['name']
                                                                                    ] = options[opt['option']]

                for opt in plugin_options('tag'):
                    if opt['option'] != "":
                        name_list = opt['name'].split("_")
                        self.cea_options['Classical Extras']['Artists options'][name_list[0]
                                                                                ][name_list[1]] = options[opt['option']]

                if options['ce_version_tag'] and options['ce_version_tag'] != "":
                    self.append_tag(
                        tm,
                        options['ce_version_tag'],
                        unicode(
                            'Version ' +
                            tm['~cea_version'] +
                            ' of Classical Extras'))
                if options['cea_options_tag'] and options['cea_options_tag'] != "":
                    self.append_tag(
                        tm,
                        options['cea_options_tag'] +
                        ':artists_options',
                        json.loads(
                            json.dumps(
                                self.cea_options)))
        self.track_listing = []
        if self.INFO:
            log.info(
                "FINISHED Classical Extra Artists. Album: %s",
                album)

    def append_tag(self, tm, tag, source):
        """
        :param tm:
        :param tag:
        :param source:
        :return:
        """
        if self.INFO:
            log.info("Extra Artists - appending %s to %s", source, tag)
        append_tag(tm, tag, source, self.SEPARATORS)

    # def remove_tag(self, tm, tag, source):
    #     """
    #     NO LONGER USED
    #     :param tm:
    #     :param tag:
    #     :param source:
    #     :return:
    #     """
    #     if self.INFO:
    #         log.info("Extra Artists - removing %s from %s", source, tag)
    #     if tag in tm:
    #         if isinstance(source, basestring):
    #             source = source.replace(u'\u2010', u'-')
    #         if source in tm[tag]:
    #             if isinstance(tm[tag], list):
    #                 old_tag = tm[tag]
    #             else:
    #                 old_tag = re.split('|'.join(self.SEPARATORS), tm[tag])
    #             new_tag = old_tag
    #             for i, tag_item in enumerate(old_tag):
    #                 if tag_item == source:
    #                     new_tag.pop(i)
    #             tm[tag] = new_tag

    # def update_tag(self, tm, tag, old_source, new_source):
    #     """
    #     NO LONGER USED
    #     :param tm:
    #     :param tag:
    #     :param old_source:
    #     :param new_source:
    #     :return:
    #     """
    #     # if old_source does not exist, it will just append new_source
    #     if self.INFO:
    #         log.info(
    #             "Extra Artists - updating %s from %s to %s",
    #             tag,
    #             old_source,
    #             new_source)
    #     self.remove_tag(tm, tag, old_source)
    #     self.append_tag(tm, tag, new_source)

    def set_performer(self, album, track, performerList, tm):
        """
        Sets the performer-related tags
        :param album:
        :param track:
        :param performerList: see below
        :param tm:
        :return:
        """
        # performerList is in format [(artist_type, [instrument list],[name list],[sort_name list],
        # instrument_sort, type_sort),(.....etc]
        # Sorted by type_sort then sort name then instrument_sort
        if self.DEBUG:
            log.debug("Extra Artists - set_performer")
        if self.INFO:
            log.info("Performer list is:")
            log.info(performerList)
        options = self.options[track]
        # tag strings are a tuple (Picard tag, cea tag, Picard sort tag, cea
        # sort tag)
        tag_strings = {'performer': ('performer:', '~cea_performers', '~performer_sort', '~cea_performers_sort'),
                       'instrument': ('performer:', '~cea_performers', '~performer_sort', '~cea_performers_sort'),
                       'vocal': ('performer:', '~cea_performers', '~performer_sort', '~cea_performers_sort'),
                       'performing orchestra': ('performer:orchestra', '~cea_ensembles', '~performer_sort', '~cea_ensembles_sort'),
                       'conductor': ('conductor', '~cea_conductors', '~conductor_sort', '~cea_conductors_sort'),
                       'chorus master': ('conductor', '~cea_chorusmasters', '~conductor_sort', '~cea_chorusmasters_sort'),
                       'concertmaster': ('performer', '~cea_leaders', '~performer_sort', '~cea_leaders_sort'),
                       'arranger': ('arranger', '~cea_arrangers', '_arranger_sort', '~cea_arrangers_sort'),
                       'instrument arranger': ('arranger', '~cea_arrangers', '~arranger_sort', '~cea_arrangers_sort'),
                       'orchestrator': ('arranger', '~cea_orchestrators', '~arranger_sort', '~cea_orchestrators_sort'),
                       'vocal arranger': ('arranger', '~cea_arrangers', '~arranger_sort', '~cea_arrangers_sort')
                       }
        # insertions lists artist types where names in the main Picard tags may be updated for annotations
        # (not for performer types as Picard will write performer:inst as Performer name (inst) )
        insertions = [
            'chorus master',
            'arranger',
            'instrument arranger',
            'orchestrator',
            'vocal arranger']

        # First remove all existing performer tags
        del_list = []
        for meta in tm:
            if 'performer' in meta:
                del_list.append(meta)
        for del_item in del_list:
            del tm[del_item]
        last_artist = []
        last_inst_list = []
        last_instrument = None
        artist_inst = []
        artist_inst_list = {}
        for performer in performerList:
            artist_type = performer[0]
            if artist_type not in tag_strings:
                return None
            if artist_type in ['instrument', 'vocal', 'performing orchestra']:
                if performer[1]:
                    inst_list = performer[1]
                    if options['cea_no_solo']:
                        for attrib in ['solo', 'guest', 'additional']:
                            if attrib in inst_list:
                                inst_list.remove(attrib)
                    instrument = ", ".join(inst_list)
                    if performer[3] == last_artist:
                        if instrument != last_instrument:
                            artist_inst.append(instrument)
                        else:
                            if inst_list == last_inst_list:
                                if self.WARNING:
                                    log.warning(
                                        'Duplicated performer information for %s (may be in Release Relationship as well as Track Relationship). Duplicates have been ignored.',
                                        performer[3])
                                    self.append_tag(
                                        tm,
                                        '~cea_warning',
                                        'Duplicated performer information for "' +
                                        '; '.join(
                                            performer[3]) +
                                        '" (may be in Release Relationship as well as Track Relationship). Duplicates have been ignored.')
                    else:
                        artist_inst = [instrument]
                        last_artist = performer[3]
                        last_inst_list = inst_list
                        last_instrument = instrument

                    instrument = ", ".join(artist_inst)
                else:
                    instrument = None
                if artist_type == 'performing orchestra':
                    instrument = 'orchestra'
                artist_inst_list[tuple(performer[3])] = instrument
        for performer in performerList:
            artist_type = performer[0]
            if artist_type not in tag_strings:
                return None
            performing_artist = False if artist_type in [
                'arranger', 'instrument arranger', 'orchestrator', 'vocal arranger'] else True
            if True and artist_type in [
                'instrument',
                'vocal',
                    'performing orchestra']:  # There may be an option here,
                # Currently groups instruments by artist - alternative has been
                # tested if required
                instrument = artist_inst_list[tuple(performer[3])]
            else:
                if performer[1]:
                    inst_list = performer[1]
                    if options['cea_no_solo']:
                        for attrib in ['solo', 'guest', 'additional']:
                            if attrib in inst_list:
                                inst_list.remove(attrib)
                    instrument = " ".join(inst_list)
                else:
                    instrument = None
                if artist_type == 'performing orchestra':
                    instrument = 'orchestra'
            sub_strings = {'instrument': instrument,
                           'vocal': instrument  # ,
                           # 'instrument arranger': instrument,
                           # 'vocal arranger': instrument
                           }
            for typ in ['concertmaster']:
                if options['cea_' + typ] and options['cea_arrangers']:
                    sub_strings[typ] = ':' + options['cea_' + typ]

            if options['cea_arranger']:
                if instrument:
                    arr_inst = options['cea_arranger'] + ' ' + instrument
                else:
                    arr_inst = options['cea_arranger']
            else:
                arr_inst = instrument
            annotations = {'instrument': instrument,
                           'vocal': instrument,
                           'performing orchestra': instrument,
                           'chorus master': options['cea_chorusmaster'],
                           'concertmaster': options['cea_concertmaster'],
                           'arranger': options['cea_arranger'],
                           'instrument arranger': arr_inst,
                           'orchestrator': options['cea_orchestrator'],
                           'vocal arranger': arr_inst}
            tag = tag_strings[artist_type][0]
            cea_tag = tag_strings[artist_type][1]
            sort_tag = tag_strings[artist_type][2]
            cea_sort_tag = tag_strings[artist_type][3]
            cea_names_tag = cea_tag[:-1] + '_names'
            if artist_type in sub_strings:
                if sub_strings[artist_type]:
                    tag += sub_strings[artist_type]
                else:
                    if self.WARNING:
                        log.warning(
                            '%s: No instrument/sub-key available for artist_type %s. Performer = %s. Track is %s',
                            PLUGIN_NAME,
                            artist_type,
                            performer[2],
                            track)

            if tag:
                if '~ce_tag_cleared_' + \
                        tag not in tm or not tm['~ce_tag_cleared_' + tag] == "Y":
                    if tag in tm:
                        if self.INFO:
                            log.info('delete tag %s', tag)
                        del tm[tag]
                tm['~ce_tag_cleared_' + tag] = "Y"
            if sort_tag:
                if '~ce_tag_cleared_' + \
                        sort_tag not in tm or not tm['~ce_tag_cleared_' + sort_tag] == "Y":
                    if sort_tag in tm:
                        del tm[sort_tag]
                tm['~ce_tag_cleared_' + sort_tag] = "Y"

            name_list = performer[2]
            for ind, name in enumerate(name_list):
                performer_type = ''
                sort_name = performer[3][ind]
                no_credit = True
                # change name to as-credited
                if (performing_artist and options['cea_performer_credited'] or
                        not performing_artist and options['cea_composer_credited']):
                    if sort_name in self.artist_credits[album]:
                        no_credit = False
                        name = self.artist_credits[album][sort_name]
                # over-ride with aliases and use standard MB name (not
                # as-credited) if no alias
                if (options['cea_aliases'] or not performing_artist and options['cea_aliases_composer']) and (
                        no_credit or options['cea_alias_overrides']):
                    if sort_name in self.artist_aliases:
                        name = self.artist_aliases[sort_name]
                # fix cyrillic names if not already fixed
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        # if not only_roman_chars(tm[tag]):
                        name = remove_middle(unsort(sort_name))
                        # Only remove middle name where the existing
                        # performer is in non-latin script
                annotated_name = name
                if instrument:
                    instrumented_name = name + ' (' + instrument + ')'
                else:
                    instrumented_name = name
                # add annotations and write performer tags
                if artist_type in annotations:
                    if annotations[artist_type]:
                        annotated_name += ' (' + annotations[artist_type] + ')'
                    else:
                        if self.WARNING:
                            log.warning(
                                '%s: No annotation (instrument) available for artist_type %s. Performer = %s. Track is %s',
                                PLUGIN_NAME,
                                artist_type,
                                performer[2],
                                track)
                if artist_type in insertions and options['cea_arrangers']:
                    self.append_tag(tm, tag, annotated_name)
                else:
                    if options['cea_arrangers'] or artist_type == tag:
                        self.append_tag(tm, tag, name)

                if options['cea_arrangers'] or artist_type == tag:
                    if sort_tag:
                        self.append_tag(tm, sort_tag, sort_name)
                        if options['cea_tag_sort'] and '~' in sort_tag:
                            explicit_sort_tag = sort_tag.replace('~', '')
                            self.append_tag(tm, explicit_sort_tag, sort_name)

                self.append_tag(tm, cea_tag, annotated_name)
                if artist_type not in [
                        'instrument', 'vocal', 'performing orchestra']:
                    self.append_tag(tm, cea_names_tag, instrumented_name)
                else:
                    self.append_tag(tm, cea_names_tag, name)
                if cea_sort_tag:
                    self.append_tag(tm, cea_sort_tag, sort_name)

                # differentiate soloists etc and write related tags
                if artist_type == 'performing orchestra' or (
                        instrument and instrument in self.ENSEMBLE_TYPES) or self.ensemble_type(name):
                    performer_type = 'ensembles'
                    self.append_tag(tm, '~cea_ensembles', instrumented_name)
                    self.append_tag(tm, '~cea_ensemble_names', name)
                    self.append_tag(tm, '~cea_ensembles_sort', sort_name)
                elif artist_type in ['performer', 'instrument', 'vocal']:
                    performer_type = 'soloists'
                    self.append_tag(tm, '~cea_soloists', instrumented_name)
                    self.append_tag(tm, '~cea_soloist_names', name)
                    self.append_tag(tm, '~cea_soloists_sort', sort_name)
                    if artist_type == "vocal":
                        self.append_tag(
                            tm, '~cea_vocalists', instrumented_name)
                        self.append_tag(tm, '~cea_vocalist_names', name)
                        self.append_tag(tm, '~cea_vocalists_sort', sort_name)
                    elif instrument:
                        self.append_tag(
                            tm, '~cea_instrumentalists', instrumented_name)
                        self.append_tag(tm, '~cea_instrumentalist_names', name)
                        self.append_tag(
                            tm, '~cea_instrumentalists_sort', sort_name)
                    else:
                        self.append_tag(
                            tm, '~cea_other_soloists', instrumented_name)
                        self.append_tag(tm, '~cea_other_soloist_names', name)
                        self.append_tag(
                            tm, '~cea_other_soloists_sort', sort_name)

                # set album artists
                if performer_type or artist_type == 'conductor':
                    cea_album_tag = cea_tag.replace(
                        'cea', 'cea_album').replace(
                        'performers', performer_type)
                    cea_album_sort_tag = cea_sort_tag.replace(
                        'cea', 'cea_album').replace(
                        'performers', performer_type)
                    if stripsir(name) in tm['~albumartists'] or stripsir(
                            sort_name) in tm['~albumartists_sort']:
                        self.append_tag(tm, cea_album_tag, name)
                        self.append_tag(tm, cea_album_sort_tag, sort_name)
                    else:
                        if performer_type:
                            self.append_tag(
                                tm, '~cea_support_performers', instrumented_name)
                            self.append_tag(
                                tm, '~cea_support_performer_names', name)
                            self.append_tag(
                                tm, '~cea_support_performers_sort', sort_name)

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
        self.partof = collections.defaultdict(dict)
        # the inverse of the above (immediate children of each parent)
        # but note that this is specific to the album as children may vary between albums
        # so format is {album1{parent1: child1, parent2:, child2},
        # album2{....}}
        self.works_queue = self.WorksQueue()
        # lookup queue - holds track/album pairs for each queued workid (may be
        # more than one pair per id, especially for higher-level parts)
        self.parts = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # metadata collection for all parts - structure is {workid: {name: ,
        # parent: , (track,album): {part_levels}}, etc}
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
        self.album_artists = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of artists to be applied at album level
        self.artist_aliases = {}
        # collection of alias names - format is {sort_name: alias_name, ...}
        self.artist_credits = collections.defaultdict(dict)
        # collection of credited-as names - format is {album: {sort_name: credit_name,
        # ...}, ...}
        self.release_artists_sort = collections.defaultdict(list)
        # collection of release artists - format is {album: [sort_name_1,
        # sort_name_2, ...]}
        self.lyricist_filled = collections.defaultdict(dict)
        # Boolean for each track to indicate if lyricist has been found (don't
        # want to add more from higher levels)
        self.orphan_tracks = collections.defaultdict(list)
        # To keep a list for each album of tracks which do not have works -
        # format is {album: [track1, track2, ...], etc}
        self.tracks = collections.defaultdict(list)
        # To keep a list of all tracks for the album - format is {album:
        # [track1, track2, ...], etc}

    ########################################
    # SECTION 1 - Initial track processing #
    ########################################

    def add_work_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):
        """
        Main Routine - run for each track
        :param album:
        :param track_metadata:
        :param trackXmlNode:
        :param releaseXmlNode:
        :return:
        """

        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]
        tm = track.metadata

        # OPTIONS - OVER-RIDE IF REQUIRED
        if '~ce_options' not in tm:
            # log.debug('%s: Workparts gets track first...', PLUGIN_NAME)
            get_options(album, track)
        options = interpret(tm['~ce_options'])

        if not options:
            if self.ERROR:
                log.error(
                    '%s: Work Parts. Failure to re-read options for track %s. options = %s',
                    PLUGIN_NAME,
                    track,
                    tm['~ce_options'])
            options = config.setting
        self.options[track] = options

        # CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.DEBUG = options["log_debug"]
        self.INFO = options["log_info"]
        self.SEPARATORS = ['; ']

        self.get_sk_tags(album, track, tm, options)

        # Continue?
        if not options["classical_work_parts"]:
            return

        # OPTION-DEPENDENT CONSTANTS:
        # Maximum number of XML- lookup retries if error returned from server
        self.MAX_RETRIES = options["cwp_retries"]
        self.USE_CACHE = options["use_cache"]
        if options["cwp_partial"] and options["cwp_partial_text"] and options["cwp_level0_works"]:
            options["cwp_removewords_p"] = options["cwp_removewords"] + \
                ", " + options["cwp_partial_text"] + ' '
        else:
            options["cwp_removewords_p"] = options["cwp_removewords"]
        # Explanation:
        # If "Partial" is selected then the level 0 work name will have PARTIAL_TEXT appended to it.
        # If a recording is split across several tracks then each sub-part (quasi-movement) will have the same name
        # (with the PARTIAL_TEXT added). If level 0 is used to source work names then the level 1 work name will be
        # changed to be this repeated name and will therefore also include PARTIAL_TEXT.
        # So we need to add PARTIAL_TEXT to the prefixes list to ensure it is
        # excluded from the level 1  work name.
        if self.DEBUG:
            log.debug("%s: LOAD NEW TRACK: :%s", PLUGIN_NAME, track)

        # first time for this album (reloads each refresh)
        if tm['discnumber'] == '1' and tm['tracknumber'] == '1':
            # get artist aliases - these are cached so can be re-used across
            # releases, but are reloaded with each refresh
            get_aliases(self, album, options, releaseXmlNode)

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
                match_tree = [
                    'recording',
                    'relation_list',
                    'attribs.target_type:work',
                    'relation',
                    'target.text:' + workId]
                rels = parse_data(
                    options, trackXmlNode, [], *match_tree)
                # for recordings which are ordered within track:-
                match_tree_1 = [
                    'ordering_key',
                    'text']
                # for recordings of works which are ordered as part of parent
                # (may be duplicated by top-down check later):-
                match_tree_2 = [
                    'work',
                    'relation_list',
                    'attribs.target_type:work',
                    'relation',
                    'attribs.type:parts',
                    'direction.text:backward',
                    'ordering_key',
                    'text']
                parse_result = parse_data(
                    options, rels, [], *match_tree_1) + parse_data(
                    options, rels, [], *match_tree_2)
                if self.INFO:
                    log.info('multi-works - ordering key: %s', parse_result)
                if parse_result and parse_result[0].isdigit():
                    key = int(parse_result[0])
                else:
                    key = 'no key - id seq: ' + unicode(i)
                keyed_workIds[key] = workId
            for key in sorted(keyed_workIds.iterkeys()):
                workId = keyed_workIds[key]
                work_rels = parse_data(
                    options,
                    trackXmlNode,
                    [],
                    'recording',
                    'relation_list',
                    'attribs.target_type:work',
                    'relation',
                    'target.text:' +
                    workId)
                work_attributes = parse_data(
                    options, work_rels, [], 'attribute_list', 'attribute', 'text')
                work_titles = parse_data(
                    options,
                    work_rels,
                    [],
                    'work',
                    'attribs.id:' +
                    workId,
                    'title',
                    'text')
                # if self.INFO:
                #     log.info(
                #         'Work details. Rels: %s \n Attributes: %s \n Titles: %s',
                #         work_rels,
                #         work_attributes,
                #         work_titles)
                work_list_info_item = {
                    'id': workId,
                    'attributes': work_attributes,
                    'titles': work_titles}
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
                            partwork = w
                            works.append(partwork)

                        if self.DEBUG:
                            log.debug(
                                "%s: Id %s is PARTIAL RECORDING OF id: %s, name: %s",
                                PLUGIN_NAME,
                                workId,
                                parentId,
                                work)
                        work_list_info_item = {
                            'id': workId,
                            'attributes': [],
                            'titles': works,
                            'parent': parentId}
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
            # list(set()) won't work as need to retain order
            work_list = list(collections.OrderedDict.fromkeys(work_list))
            work_list_p = list(collections.OrderedDict.fromkeys(work_list_p))

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
                    "Trackback for %s is %s. Partial = %s",
                    track,
                    self.trackback[album][workId_tuple],
                    partial)

            if workId_tuple in self.works_cache and (
                    self.USE_CACHE or partial):
                if self.DEBUG:
                    log.debug(
                        "%s: GETTING WORK METADATA FROM CACHE",
                        PLUGIN_NAME)  # debug
                if workId_tuple not in self.work_listing[album]:
                    self.work_listing[album].append(workId_tuple)
                not_in_cache = self.check_cache(
                    track_metadata, album, track, workId_tuple, [])
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
            if album in self.orphan_tracks:
                if track not in self.orphan_tracks[album]:
                    self.orphan_tracks[album].append(track)
            else:
                self.orphan_tracks[album] = [track]
            # Don't publish metadata yet until all album is processed

        # last track
        if self.DEBUG:
            log.debug(
                '%s, Check for last track. Requests = %s, Tracknumber = %s, Totaltracks = %s, Discnumber = %s, Totaldiscs = %s',
                PLUGIN_NAME,
                album._requests,
                track_metadata['tracknumber'],
                track_metadata['totaltracks'],
                track_metadata['discnumber'],
                track_metadata['totaldiscs'])
        if album._requests == 0 and track_metadata['tracknumber'] == track_metadata[
                'totaltracks'] and track_metadata['discnumber'] == track_metadata['totaldiscs']:
            self.process_album(album)

    def get_sk_tags(self, album, track, tm, options):
        """
        Get file tags which are consistent with SongKong's metadata usage
        :param album:
        :param track:
        :param tm:
        :param options:
        :return:
        """
        if options["cwp_use_sk"]:
            if '~ce_file' in tm and eval(tm['~ce_file']):
                music_file = tm['~ce_file']
                orig_metadata = album.tagger.files[music_file].orig_metadata
                if 'musicbrainz_work_composition_id' in orig_metadata and 'musicbrainz_workid' in orig_metadata:
                    if 'musicbrainz_work_composition' in orig_metadata:
                        if 'musicbrainz_work' in orig_metadata:
                            if orig_metadata['musicbrainz_work_composition_id'] == orig_metadata[
                                'musicbrainz_workid'] \
                                    and orig_metadata['musicbrainz_work_composition'] != orig_metadata[
                                        'musicbrainz_work']:
                                # Picard may have overwritten SongKong tag (top
                                # work id) with bottom work id
                                if self.WARNING:
                                    log.warning(
                                        '%s: File tag musicbrainz_workid incorrect? id = %s. Sourcing from MB',
                                        PLUGIN_NAME,
                                        orig_metadata['musicbrainz_workid'])
                                self.append_tag(
                                    tm,
                                    '~cwp_warning',
                                    'File tag musicbrainz_workid incorrect? id = ' +
                                    orig_metadata['musicbrainz_workid'] +
                                    '. Sourcing from MB')
                                return None
                        if self.INFO:
                            log.info(
                                'Read from file tag: musicbrainz_work_composition_id: %s',
                                orig_metadata['musicbrainz_work_composition_id'])
                        self.file_works[(album, track)].append({
                            'workid': orig_metadata['musicbrainz_work_composition_id'].split('; '),
                            'name': orig_metadata['musicbrainz_work_composition']})
                    else:
                        wid = orig_metadata['musicbrainz_work_composition_id']
                        if self.ERROR:
                            log.error(
                                "%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                        self.append_tag(
                            tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                        return None
                    n = 1
                    while 'musicbrainz_work_part_level' + \
                            unicode(n) + '_id' in orig_metadata:
                        if 'musicbrainz_work_part_level' + \
                                unicode(n) in orig_metadata:
                            self.file_works[(album, track)].append({
                                'workid': orig_metadata[
                                    'musicbrainz_work_part_level' + unicode(n) + '_id'].split('; '),
                                'name': orig_metadata['musicbrainz_work_part_level' + unicode(n)]})
                            n += 1
                        else:
                            wid = orig_metadata['musicbrainz_work_part_level' +
                                                unicode(n) + '_id']
                            if self.ERROR:
                                log.error(
                                    "%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                            self.append_tag(
                                tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                            break
                    if orig_metadata['musicbrainz_work_composition_id'] != orig_metadata[
                            'musicbrainz_workid']:
                        if 'musicbrainz_work' in orig_metadata:
                            self.file_works[(album, track)].append({
                                'workid': orig_metadata['musicbrainz_workid'].split('; '),
                                'name': orig_metadata['musicbrainz_work']})
                        else:
                            wid = orig_metadata['musicbrainz_workid']
                            if self.ERROR:
                                log.error(
                                    "%s: No matching work name for id tag %s", PLUGIN_NAME, wid)
                            self.append_tag(
                                tm, '~cwp_error', 'No matching work name for id tag ' + wid)
                            return None
                    file_work_levels = len(self.file_works[(album, track)])
                    if self.DEBUG:
                        log.debug('%s: Loaded works from file tags for track %s. Works: %s: ',
                                  PLUGIN_NAME, track, self.file_works[(album, track)])
                    for i, work in enumerate(self.file_works[(album, track)]):
                        workId = tuple(work['workid'])
                        if workId not in self.works_cache:  # Use cache in preference to file tags
                            if workId not in self.work_listing[album]:
                                self.work_listing[album].append(workId)
                            self.parts[workId]['name'] = [work['name']]
                            parentId = None
                            parent = ''
                            if i < file_work_levels - 1:
                                parentId = self.file_works[(
                                    album, track)][i + 1]['workid']
                                parent = self.file_works[(
                                    album, track)][i + 1]['name']

                            if parentId:
                                self.works_cache[workId] = parentId
                                self.parts[workId]['parent'] = parentId
                                self.parts[tuple(parentId)]['name'] = [parent]
                            else:
                                # so we remember we looked it up and found none
                                self.parts[workId]['no_parent'] = True
                                self.top_works[(track, album)
                                               ]['workId'] = workId
                                if workId not in self.top[album]:
                                    self.top[album].append(workId)

    def check_cache(self, tm, album, track, workId_tuple, not_in_cache):
        """
        Recursive loop to get cached works
        :param tm:
        :param album:
        :param track:
        :param workId_tuple:
        :param not_in_cache:
        :return:
        """
        parentId_tuple = tuple(self.works_cache[workId_tuple])
        if parentId_tuple not in self.work_listing[album]:
            self.work_listing[album].append(parentId_tuple)

        if parentId_tuple in self.works_cache:
            self.check_cache(tm, album, track, parentId_tuple, not_in_cache)
        else:
            not_in_cache.append(parentId_tuple)
        return not_in_cache

    def work_not_in_cache(self, album, track, workId_tuple):
        """
        Determine actions if work not in cache (is it the top or do we need to look up?)
        :param album:
        :param track:
        :param workId_tuple:
        :return:
        """
        if 'no_parent' in self.parts[workId_tuple] and (
                self.USE_CACHE or self.options[track]["cwp_use_sk"]) and self.parts[workId_tuple]['no_parent']:
            self.top_works[(track, album)]['workId'] = workId_tuple
            if album in self.top:
                if workId_tuple not in self.top[album]:
                    self.top[album].append(workId_tuple)
            else:
                self.top[album] = [workId_tuple]
        else:
            for workId in workId_tuple:
                self.work_add_track(album, track, workId, 0)

    def work_add_track(self, album, track, workId, tries):
        """
        Add the work to the lookup queue
        :param album:
        :param track:
        :param workId:
        :param tries: number of lookup attempts
        :return:
        """
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
            if config.setting['cwp_aliases'] and config.setting['cwp_aliases_tag_text']:
                if config.setting['cwp_aliases_tags_user']:
                    login = True
                    tag_type = '+user-tags'
                else:
                    login = False
                    tag_type = '+tags'
            else:
                login = False
                tag_type = ''
            queryargs = {"inc": "work-rels+artist-rels+aliases" + tag_type}
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
                mblogin=login,
                queryargs=queryargs)
        else:
            if self.DEBUG:
                log.debug(
                    "%s: Work is already in queue: %s",
                    PLUGIN_NAME,
                    workId)

    def work_process(self, workId, tries, response, reply, error):
        """
        Top routine to process the XML node response from the lookup
        :param workId:
        :param tries:
        :param response:
        :param reply:
        :param error:
        :return:
        """
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
        if tuples:
            for track, album in tuples:
                if self.DEBUG:
                    log.debug("%s Requests = %s", PLUGIN_NAME, album._requests)
            # use representative album & track
            album = tuples[0][1]
            track = tuples[0][0]
            options = self.options[track]
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
                metaList = self.work_process_metadata(
                    workId, wid, tuples, response)
                parentList = metaList[0]
                # returns [parent id, parent name] or None if no parent found
                arrangers = metaList[1]
                if wid in self.parts:

                    if arrangers:
                        if 'arrangers' in self.parts[wid]:
                            self.parts[wid]['arrangers'] += arrangers
                        else:
                            self.parts[wid]['arrangers'] = arrangers

                    if parentList:
                        # first fix the sort order of multi-works at the prev
                        # level
                        if len(wid) > 1:
                            for id in wid:
                                if id == workId:
                                    match_tree = [
                                        'metadata',
                                        'work',
                                        'relation_list',
                                        'attribs.target_type:work',
                                        'relation',
                                        'direction.text:backward',
                                        'ordering_key',
                                        'text']
                                    parse_result = parse_data(
                                        options, response, [], *match_tree)
                                    if self.INFO:
                                        log.info(
                                            'multi-works - ordering key for id %s is %s', id, parse_result)
                                    if parse_result and parse_result[0].isdigit(
                                    ):
                                        key = int(parse_result[0])
                                        self.parts[wid]['order'][id] = key

                        parentIds = parentList[0]
                        parents = parentList[1]
                        if self.INFO:
                            log.info(
                                'Parents - ids: %s, names: %s', parentIds, parents)
                        if parentIds:
                            if wid in self.works_cache:
                                prev_ids = tuple(self.works_cache[wid])
                                prev_name = self.parts[prev_ids]['name']
                                self.works_cache[wid] = add_list_uniquely(
                                    self.works_cache[wid], parentIds)
                                self.parts[wid]['parent'] = add_list_uniquely(
                                    self.parts[wid]['parent'], parentIds)
                                index = self.work_listing[album].index(
                                    prev_ids)
                                new_id_list = add_list_uniquely(
                                    list(prev_ids), parentIds)
                                new_ids = tuple(new_id_list)
                                self.work_listing[album][index] = new_ids
                                self.parts[new_ids] = self.parts[prev_ids]
                                del self.parts[prev_ids]
                                self.parts[new_ids]['name'] = add_list_uniquely(
                                    prev_name, parents)
                                parentIds = new_id_list

                            else:
                                self.works_cache[wid] = parentIds
                                self.parts[wid]['parent'] = parentIds
                                self.parts[tuple(parentIds)]['name'] = parents
                                self.work_listing[album].append(
                                    tuple(parentIds))

                            # de-duplicate the parent names
                                self.parts[tuple(parentIds)]['name'] = list(
                                    collections.OrderedDict.fromkeys(self.parts[tuple(parentIds)]['name']))
                                # list(set()) won't work as need to retain
                                # order
                            if self.DEBUG:
                                log.debug(
                                    '%s: added parent ids to work_listing: %s, [Requests = %s]',
                                    PLUGIN_NAME,
                                    parentIds,
                                    album._requests)
                            if self.INFO:
                                log.info(
                                    'work_listing: %s', self.work_listing[album])
                            # the higher-level work might already be in cache
                            # from another album
                            if tuple(parentIds) in self.works_cache:
                                not_in_cache = self.check_cache(
                                    track.metadata, album, track, tuple(parentIds), [])
                                for workId_tuple in not_in_cache:
                                    self.work_not_in_cache(
                                        album, track, workId_tuple)
                            else:
                                for parentId in parentIds:
                                    for track, album in tuples:
                                        self.work_add_track(
                                            album, track, parentId, 0)
                        else:
                            # so we remember we looked it up and found none
                            self.parts[wid]['no_parent'] = True
                            self.top_works[(track, album)]['workId'] = wid
                            if wid not in self.top[album]:
                                self.top[album].append(wid)
                            if self.INFO:
                                log.info("TOP[album]: %s", self.top[album])
                    else:
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
        """
        Process XML node
        :param workId:
        :param wid:
        :param tuples:
        :param response:
        :return:
        """
        if self.DEBUG:
            log.debug("%s: In work_process_metadata", PLUGIN_NAME)
        log_options = {'log_debug': self.DEBUG, 'log_info': self.INFO}
        if 'metadata' in response.children:
            if 'work' in response.metadata[0].children:
                if 'artist_locale' in config.setting:
                    locale = config.setting["artist_locale"]
                    # NB this is the Picard code in /util
                    lang = locale.split("_")[0]
                    alias = parse_data(
                        log_options,
                        response.metadata[0].work,
                        [],
                        'alias_list',
                        'alias',
                        'attribs.locale:' + lang,
                        'attribs.primary:primary',
                        'text')
                    if config.setting['cwp_aliases_tags_user']:
                        tags = parse_data(
                            log_options,
                            response.metadata[0].work,
                            [],
                            'user_tag_list',
                            'user_tag',
                            'name',
                            'text')
                    else:
                        tags = parse_data(
                            log_options,
                            response.metadata[0].work,
                            [],
                            'tag_list',
                            'tag',
                            'name',
                            'text')
                    if alias:
                        self.parts[wid]['alias'] = self.parts[wid]['name'][:]
                        self.parts[wid]['tags'] = tags
                        for ind, w in enumerate(wid):
                            if w == workId:
                                # alias should be a one item list but...
                                self.parts[wid]['alias'][ind] = '; '.join(
                                    alias)
                relation_list = parse_data(
                    log_options, response.metadata[0].work, [], 'relation_list')
                for track, _ in tuples:
                    rep_track = track  # Representative track for option ident only
                return self.work_process_relations(
                    rep_track, workId, wid, relation_list)

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
                        unicode(workId))
        return None

    def work_process_relations(self, track, workId, wid, relations):
        """
        Find the parents etc.
        :param track:
        :param workId:
        :param wid:
        :param relations:
        :return:
        """
        # nb track is just the last track for this work - used as being
        # representative for options identification
        if self.DEBUG:
            log.debug(
                "%s In work_process_relations. Relations--> %s",
                PLUGIN_NAME,
                relations)
        options = self.options[track]
        log_options = {'log_debug': self.DEBUG, 'log_info': self.INFO}
        new_workIds = []
        new_works = []

        relation_attribute = parse_data(
            log_options,
            relations,
            [],
            'attribs.target_type:work',
            'relation',
            'attribs.type:parts',
            'direction.text:backward',
            'attribute_list',
            'attribute',
            'text')
        if 'part of collection' not in relation_attribute or options['cwp_collections']:
            new_work_list = parse_data(
                log_options,
                relations,
                [],
                'attribs.target_type:work',
                'relation',
                'attribs.type:parts',
                'direction.text:backward',
                'work')
        else:
            new_work_list = []
        if new_work_list:
            new_workIds = parse_data(
                log_options, new_work_list, [], 'attribs', 'id')
            new_works = parse_data(
                log_options, new_work_list, [], 'title', 'text')
        else:
            arrangement_of = parse_data(
                log_options,
                relations,
                [],
                'attribs.target_type:work',
                'relation',
                'attribs.type:arrangement',
                'direction.text:backward',
                'work')
            if arrangement_of and options['cwp_arrangements']:
                new_workIds = parse_data(
                    log_options, arrangement_of, [], 'attribs', 'id')
                new_works = parse_data(
                    log_options, arrangement_of, [], 'title', 'text')
                self.parts[wid]['arrangement'] = True
            else:
                medley_of = parse_data(
                    log_options,
                    relations,
                    [],
                    'attribs.target_type:work',
                    'relation',
                    'attribs.type:medley',
                    'work')
                direction = parse_data(
                    log_options,
                    relations,
                    [],
                    'attribs.target_type:work',
                    'relation',
                    'attribs.type:medley',
                    'direction',
                    'text')
                if 'backward' not in direction:
                    if self.DEBUG:
                        log.debug('%s: medley_of: %s', PLUGIN_NAME, medley_of)
                    if medley_of and options['cwp_medley']:
                        medley_list = []
                        for medley_item in medley_of:
                            medley_list = medley_list + \
                                parse_data(log_options, medley_item, [], 'title', 'text')
                            # (parse_data is a list...)
                            if self.INFO:
                                log.info('medley_list: %s', medley_list)
                        self.parts[wid]['medley_list'] = medley_list

        if self.INFO:
            log.info('New works: ids: %s, names: %s', new_workIds, new_works)

        artists = get_artists(log_options, relations, 'work')
        # artist_types = ['arranger', 'instrument arranger', 'orchestrator', 'composer', 'writer', 'lyricist',
        #                 'librettist', 'revised by', 'translator', 'reconstructed by', 'vocal arranger']

        if self.INFO:
            log.info("ARTISTS %s", artists)

        workItems = (new_workIds, new_works)
        itemsFound = [workItems, artists]
        return itemsFound

    def album_add_request(self, album):
        """
        To keep track as to whether all lookups have been processed
        :param album:
        :return:
        """
        album._requests += 1
        if self.INFO:
            log.info("album requests: %s", album._requests)

    def album_remove_request(self, album):
        """
        To keep track as to whether all lookups have been processed
        :param album:
        :return:
        """
        album._requests -= 1
        if self.INFO:
            log.info("album requests: %s", album._requests)
        album._finalize_loading(None)

    ##################################################
    # SECTION 2 - Organise tracks and works in album #
    ##################################################

    def process_album(self, album):
        """
        Top routine to run end-of-album processes
        :param album:
        :return:
        """
        if self.DEBUG:
            log.debug("%s: PROCESS ALBUM %s", PLUGIN_NAME, album)
        # populate the inverse hierarchy
        if self.INFO:
            log.info("%s: Cache: %s", PLUGIN_NAME, self.works_cache)
        if self.INFO:
            log.info("%s: Work listing %s", PLUGIN_NAME, self.work_listing)
        alias_tag_list = config.setting['cwp_aliases_tag_text'].split(',')
        for i, tag_item in enumerate(alias_tag_list):
            alias_tag_list[i] = tag_item.strip()
        for workId in self.work_listing[album]:
            if workId in self.parts:
                if self.INFO:
                    log.info('Processing workid: %s', workId)
                    log.info(
                        'self.work_listing[album]: %s',
                        self.work_listing[album])
                if len(workId) > 1:
                    # fix the order of names using ordering keys gathered in
                    # work_process
                    if 'order' in self.parts[workId]:
                        seq = []
                        for id in workId:
                            if id in self.parts[workId]['order']:
                                seq.append(self.parts[workId]['order'][id])
                            else:
                                # for the possibility of workids not part of
                                # the same parent and not all ordered
                                seq.append(999)
                        zipped_names = zip(self.parts[workId]['name'], seq)
                        sorted_tups = sorted(zipped_names, key=lambda x: x[1])
                        self.parts[workId]['name'] = [x[0]
                                                      for x in sorted_tups]
                # use aliases where appropriate
                # name is a list - need a string to test for Latin chars
                name_string = '; '.join(self.parts[workId]['name'])
                if config.setting['cwp_aliases']:
                    if config.setting['cwp_aliases_all'] or (
                        config.setting['cwp_aliases_greek'] and not only_roman_chars(name_string)) or (
                        'tags' in self.parts[workId] and any(
                            x in self.parts[workId]['tags'] for x in alias_tag_list)):
                        if 'alias' in self.parts[workId] and self.parts[workId]['alias']:
                            self.parts[workId]['name'] = self.parts[workId]['alias'][:]
                topId = None
                if self.INFO:
                    log.info('Works_cache: %s', self.works_cache)
                if workId in self.works_cache:
                    parentIds = tuple(self.works_cache[workId])
                    # for parentId in parentIds:
                    if self.DEBUG:
                        log.debug("%s: create inverses: %s, %s",
                                  PLUGIN_NAME, workId, parentIds)
                    if parentIds in self.partof[album]:
                        if workId not in self.partof[album][parentIds]:
                            self.partof[album][parentIds].append(workId)
                    else:
                        self.partof[album][parentIds] = [workId]
                    if self.DEBUG:
                        log.debug(
                            "%s: Partof: %s",
                            PLUGIN_NAME,
                            self.partof[album][parentIds])
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
                    if '~cwp_workid_0' in tm:
                        workIds = eval(tm['~cwp_workid_0'])
                        if workIds:
                            count = 0
                            self.process_work_artists(
                                album, track_meta, workIds, tm, count)
                    title_work_levels = 0
                    if '~cwp_title_work_levels' in tm:
                        title_work_levels = int(tm['~cwp_title_work_levels'])
                    self.extend_metadata(
                        top_info,
                        track_meta,
                        ref_height,
                        title_work_levels)  # revise for new data
                    if track_meta not in self.tracks[album]:
                        self.tracks[album].append(track_meta)
                if self.DEBUG:
                    log.debug(
                        "%s FINISHED TRACK PROCESSING FOR Top work id: %s",
                        PLUGIN_NAME,
                        topId)
        # Need to redo the loop so that all album-wide tm is updated before
        # publishing
        for track in self.tracks[album]:
            self.publish_metadata(album, track)
        if self.INFO:
            log.info('Self.parts: %s', self.parts)
        if self.INFO:
            log.info('Self.trackback: %s', self.trackback)
        self.trackback[album].clear()
        # Finally process the orphan tracks
        if album in self.orphan_tracks:
            for track in self.orphan_tracks[album]:
                self.publish_metadata(album, track)

    def create_trackback(self, album, parentId):
        """
        Create an inverse listing of the work-parent relationships
        :param album:
        :param parentId:
        :return: trackback for a given parentId
        """
        if self.DEBUG:
            log.debug("%s: Create trackback for %s", PLUGIN_NAME, parentId)
        if parentId in self.partof[album]:  # NB parentId is a tuple
            for child in self.partof[album][parentId]:  # NB child is a tuple
                if child in self.partof[album]:
                    child_trackback = self.create_trackback(album, child)
                    self.append_trackback(album, parentId, child_trackback)
                else:
                    self.append_trackback(
                        album, parentId, self.trackback[album][child])
            return self.trackback[album][parentId]
        else:
            return self.trackback[album][parentId]

    def append_trackback(self, album, parentId, child):
        """
        Recursive process to populate trackback
        :param album:
        :param parentId:
        :param child:
        :return:
        """
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
        """
        Recursive process to determine the max level for a work
        :param trackback:
        :param height: number of levels above this one
        :return:
        """
        if self.DEBUG:
            log.debug('%s: In level_calc process')
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
                if self.INFO:
                    log.info("CHILD: %s", child)
                depth = self.level_calc(child, height) + 1
                if self.INFO:
                    log.info("DEPTH: %s", depth)
                max_depth = max(depth, max_depth)
            trackback['depth'] = max_depth
            return max_depth

        ###########################################
        # SECTION 3 - Process tracks within album #
        ###########################################

    def process_trackback(self, album_req, trackback, ref_height, top_info):
        """
        Set work structure metadata & govern other metadata-setting processes
        :param album_req:
        :param trackback:
        :param ref_height:
        :param top_info:
        :return:
        """
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
                        tm['~cwp_workid_' + unicode(depth)] = workId
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
                        tm['~cwp_work_' + unicode(depth)] = worktemp
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
                    # NB this will only be the first track of tracks, but its
                    # options will be used for the structure
                    self.derive_from_structure(
                        top_info, tracks, height, depth, width, 'title')
                    if self.options[track]["cwp_level0_works"]:
                        # replace hierarchical works with those from work_0 (for
                        # consistency)
                        self.derive_from_structure(
                            top_info, tracks, height, depth, width, 'work')

                    if self.DEBUG:
                        log.debug(
                            "Trackback result for %s = %s", parentId, tracks)
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
        """
        Derive title (or work level-0) components from MB hierarchical work structure
        :param top_info: {'levels': work_part_levels,'id': topId,'name': self.parts[topId]['name'],'single': single_work_album}
        :param tracks: {'track':[(track1, height1), (track2, height2), ...], 'work': [work1, work2,...], 'title': [title1, title2, ...], 'tracknumber': [tracknumber1, tracknumber2, ...]}
            where height is the number of levels in total in the branch
        :param height: number of levels above the current one
        :param depth: maximum number of levels
        :param width: number of siblings
        :param name_type: work or title
        :return:
        """
        allow_repeats = True
        if 'track' in tracks:
            track = tracks['track'][0][0]
            # NB this will only be the first track of tracks, but its
            # options will be used for the structure
            single_work_track = False  # default
            if self.DEBUG:
                log.debug(
                    "%s: Deriving info for %s from structure for tracks %s",
                    PLUGIN_NAME,
                    name_type,
                    tracks['track'])
            if 'tracknumber' in tracks:
                sorted_tracknumbers = sorted(tracks['tracknumber'])
            else:
                sorted_tracknumbers = None
            if self.INFO:
                log.info("SORTED TRACKNUMBERS: %s", sorted_tracknumbers)
            common_len = 0
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
                            ti = name_list[0]
                            common_subset = self.derive_from_title(track, ti)[
                                0]
                        else:
                            common_subset = ""
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
                            "Use %s info for track: %s at level %s",
                            name_type,
                            track_meta,
                            part_level)
                    name = tracks[name_type][i]
                    work = name[:common_len]
                    work = work.rstrip(":,.;- ")
                    removewords = self.options[track]["cwp_removewords_p"].split(
                        ',')
                    if self.INFO:
                        log.info(
                            "Removewords (in %s) = %s",
                            name_type,
                            removewords)
                    for prefix in removewords:
                        prefix2 = unicode(prefix).lower().rstrip()
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

                    tm['~cwp' + meta_str + '_work_' +
                        unicode(part_level)] = work

                    if part_level > 0 and name_type == "work":
                        if self.INFO:
                            log.info(
                                'checking if %s is repeated name at part_level = %s', work, part_level)
                            log.info('lower work name is %s',
                                     tm['~cwp' + meta_str + '_work_' + unicode(part_level - 1)])
                        # fill in missing names caused by no common string at lower levels
                        # count the missing levels and push the current name
                        # down to the lowest missing level
                        missing_levels = 0
                        fill_level = part_level - 1
                        while '~cwp' + meta_str + '_work_' + \
                                unicode(fill_level) not in tm:
                            missing_levels += 1
                            fill_level -= 1
                            if fill_level < 0:
                                break
                        if self.INFO:
                            log.info(
                                'there is/are %s missing level(s)',
                                missing_levels)
                        if missing_levels > 0:
                            allow_repeats = True
                        for lev in range(
                                part_level - missing_levels, part_level):

                            if lev > 0:  # not filled_lowest and lev > 0:
                                tm['~cwp' + meta_str +
                                    '_work_' + unicode(lev)] = work
                                tm['~cwp' +
                                   meta_str +
                                   '_part_' +
                                   unicode(lev -
                                           1)] = self.strip_parent_from_work(tm['~cwp' +
                                                                                meta_str +
                                                                                '_work_' +
                                                                                unicode(lev -
                                                                                        1)], tm['~cwp' +
                                                                                                meta_str +
                                                                                                '_work_' +
                                                                                                unicode(lev)], lev -
                                                                             1, False)[0]
                            else:
                                tm['~cwp' +
                                   meta_str +
                                   '_work_' +
                                   unicode(lev)] = tm['~cwp_work_' +
                                                      unicode(lev)]

                        if missing_levels > 0 and self.INFO:
                            log.info('lower work name is now %s',
                                     tm['~cwp' + meta_str + '_work_' + unicode(part_level - 1)])
                        # now fix the repeated work name at this level
                        if work == tm['~cwp' + meta_str + '_work_' +
                                      unicode(part_level - 1)] and not allow_repeats:
                            tm['~cwp' +
                               meta_str +
                               '_work_' +
                               unicode(part_level)] = tm['~cwp_work_' +
                                                         unicode(part_level)]
                            self.level0_warn(tm, part_level)
                        tm['~cwp' +
                           meta_str +
                           '_part_' +
                           unicode(part_level -
                                   1)] = self.strip_parent_from_work(tm['~cwp' +
                                                                        meta_str +
                                                                        '_work_' +
                                                                        unicode(part_level -
                                                                                1)], tm['~cwp' +
                                                                                        meta_str +
                                                                                        '_work_' +
                                                                                        unicode(part_level)], part_level -
                                                                     1, False)[0]

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
                        if '~cwp_title_work_' + unicode(part_level - 1) in tm and tm['~cwp_title_work_' + unicode(
                                part_level)] == tm['~cwp_title_work_' + unicode(part_level - 1)] and width == 1:
                            pass  # don't count higher part-levels which are not distinct from lower ones when the parent work has only one child
                        else:
                            tm['~cwp_title_work_levels'] = depth
                            tm['~cwp_title_part_levels'] = part_level
                    if self.DEBUG:
                        log.debug("Set new metadata for %s OK", name_type)
                else:  # (no common substring at this level)
                    if name_type == 'work':
                        if self.INFO:
                            log.info(
                                'single track work - indicator = %s. track = %s, part_level = %s, top_level = %s',
                                single_work_track,
                                track_item,
                                part_level,
                                top_level)
                        if part_level >= top_level:  # so it won't be covered by top-down action
                            for level in range(
                                    0, part_level + 1):  # fill in the missing work names from the canonical list
                                if '~cwp' + meta_str + '_work_' + \
                                        unicode(level) not in tm:
                                    tm['~cwp' +
                                       meta_str +
                                       '_work_' +
                                       unicode(level)] = tm['~cwp_work_' +
                                                            unicode(level)]
                                    if level > 0:
                                        self.level0_warn(tm, level)
                                if '~cwp' + meta_str + '_part_' + \
                                        unicode(level) not in tm and '~cwp_part_' + unicode(level) in tm:
                                    tm['~cwp' +
                                       meta_str +
                                       '_part_' +
                                       unicode(level)] = tm['~cwp_part_' +
                                                            unicode(level)]
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
                        tm['~cwp_movt_num'] = unicode(posn)

    def level0_warn(self, tm, level):
        """
        Issue warnings if inadequate level 0 data
        :param tm:
        :param level:
        :return:
        """
        if self.WARNING:
            log.warning(
                '%s: Unable to use level 0 as work name source in level %s - using hierarchy instead',
                PLUGIN_NAME,
                level)
            self.append_tag(
                tm,
                '~cwp_warning',
                'Unable to use level 0 as work name source in level ' +
                unicode(level) +
                ' - using hierarchy instead')

    def set_metadata(self, part_level, workId, parentId, parent, track):
        """
        Set the names of works and parts
        :param part_level:
        :param workId:
        :param parentId:
        :param parent:
        :param track:
        :return:
        """
        if self.DEBUG:
            log.debug(
                "%s: SETTING METADATA FOR TRACK = %r, parent = %s, part_level = %s",
                PLUGIN_NAME,
                track,
                parent,
                part_level)
        tm = track.metadata
        if parentId:

            tm['~cwp_workid_' + unicode(part_level)] = parentId
            tm['~cwp_work_' + unicode(part_level)] = parent
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
                # partials (and often) arrangements will have the same name as
                # the "parent" and not be an extension
                if 'arrangement' in self.parts[workId] and self.parts[workId]['arrangement'] \
                        or 'partial' in self.parts[workId] and self.parts[workId]['partial']:
                    if not isinstance(parent, basestring):
                        # in case it is a list - make sure it is a string
                        parent = '; '.join(parent)
                    if not isinstance(work, basestring):
                        work = '; '.join(work)
                    diff = self.diff_pair(track, tm, parent, work)
                    if diff is None:
                        diff = ""
                    strip = [diff, parent]
                else:
                    extend = True
                    strip = self.strip_parent_from_work(
                        work, parent, part_level, extend, parentId)
                stripped_works.append(strip[0])
                if self.INFO:
                    log.info("Parent: %s", parent)
                # now == parent, after removing full_parent logic
                full_parent = strip[1]
                if full_parent != parent:
                    tm['~cwp_work_' +
                       unicode(part_level)] = full_parent.strip()
                    self.parts[parentId]['name'] = full_parent
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:
                            tm['~cwp_work_top'] = full_parent.strip()
            tm['~cwp_part_' + unicode(part_level - 1)] = stripped_works
            self.parts[workId]['stripped_name'] = stripped_works
        if self.DEBUG:
            log.debug("GOT TO END OF SET_METADATA")

    def derive_from_title(self, track, title):
        """
        Attempt to parse title to get components
        :param track:
        :param title:
        :return:
        """
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

    def process_work_artists(self, album, track, workIds, tm, count):
        """
        Carry out the artist processing that needs to be done in the PartLevels class
        as it requires XML lookups of the works
        :param album:
        :param track:
        :param workIds:
        :param tm:
        :param count:
        :return:
        """
        if not self.options[track]['classical_extra_artists']:
            if self.DEBUG:
                log.debug(
                    '%s: Not processing work_artists as ExtraArtists not selected to be run',
                    PLUGIN_NAME)
            return None
        if self.DEBUG:
            log.debug(
                '%s: In process_work_artists for track: %s, workIds: %s',
                PLUGIN_NAME,
                track,
                workIds)
        if workIds in self.parts and 'arrangers' in self.parts[workIds]:
            if self.INFO:
                log.info('Arrangers = %s', self.parts[workIds]['arrangers'])
            set_work_artists(
                self,
                album,
                track,
                self.parts[workIds]['arrangers'],
                tm,
                count)
        if workIds in self.works_cache:
            count += 1
            self.process_work_artists(
                album, track, tuple(
                    self.works_cache[workIds]), tm, count)

    #################################################
    # SECTION 4 - Extend work metadata using titles #
    #################################################

    def extend_metadata(self, top_info, track, ref_height, depth):
        """
        Combine MB work and title data according to user options
        :param top_info:
        :param track:
        :param ref_height:
        :param depth:
        :return:
        """
        tm = track.metadata
        options = self.options[track]
        if self.DEBUG:
            log.debug(
                "%s: Extending metadata for track: %s, ref_height: %s, depth: %s",
                PLUGIN_NAME,
                track,
                ref_height,
                depth)
        if self.INFO:
            log.info("Metadata = %s", tm)

        part_levels = int(tm['~cwp_part_levels'])
        work_part_levels = int(tm['~cwp_work_part_levels'])

        # previously: ref_height = work_part_levels - ref_level,
        # where this ref-level is the level for the top-named work
        ref_level = part_levels - ref_height
        work_ref_level = work_part_levels - ref_height

        # replace works and parts by those derived from the level 0 work, where
        # required, available and appropriate, but only use work names based on
        # level 0 text if it doesn't cause ambiguity

        # before embellishing with partial / arrangement etc
        vanilla_part = tm['~cwp_part_0']

        # Fix text for arrangements, partials and medleys (Done here so that
        # cache can be used)
        if options['cwp_arrangements'] and options["cwp_arrangements_text"]:
            for lev in range(
                    0,
                    ref_level):  # top level will not be an arrangement else there would be a higher level
                # needs to be a tuple to match
                tup_id = eval(tm['~cwp_workid_' + unicode(lev)])
                if 'arrangement' in self.parts[tup_id] and self.parts[tup_id]['arrangement']:
                    update_list = ['~cwp_work_', '~cwp_part_']
                    if options["cwp_level0_works"] and '~cwp_X0_work_' + \
                            unicode(lev) in tm:
                        update_list += ['~cwp_X0_work_', '~cwp_X0_part_']
                    for item in update_list:
                        tm[item + unicode(lev)] = options["cwp_arrangements_text"] + \
                            ' ' + tm[item + unicode(lev)]

        if options['cwp_partial'] and options["cwp_partial_text"]:
            if '~cwp_workid_0' in tm:
                work0_id = eval(tm['~cwp_workid_0'])
                if 'partial' in self.parts[work0_id] and self.parts[work0_id]['partial']:
                    update_list = ['~cwp_work_0', '~cwp_part_0']
                    if options["cwp_level0_works"] and '~cwp_X0_work_0' in tm:
                        update_list += ['~cwp_X0_work_0', '~cwp_X0_part_0']
                    for item in update_list:
                        if len(work0_id) > 1 and isinstance(
                                tm[item], basestring):
                            meta_item = re.split(
                                '|'.join(self.SEPARATORS), (tm[item]))
                        else:
                            meta_item = tm[item]
                        if isinstance(meta_item, list):
                            for ind, w in enumerate(meta_item):
                                meta_item[ind] = options["cwp_partial_text"] + ' ' + w
                            tm[item] = meta_item
                        else:
                            tm[item] = options["cwp_partial_text"] + \
                                ' ' + tm[item]

        # fix "type 1" medley text
        if options['cwp_medley']:
            for lev in range(0, ref_level + 1):
                tup_id = eval(tm['~cwp_workid_' + unicode(lev)])
                if 'medley_list' in self.parts[tup_id]:
                    medley_list = self.parts[tup_id]['medley_list']
                    tm['~cwp_work_' + unicode(lev)] += " (" + options["cwp_medley_text"] + \
                        ' ' + ', '.join(medley_list) + ")"

        part = []
        work = []
        for level in range(0, part_levels):
            part.append(tm['~cwp_part_' + unicode(level)])
            work.append(tm['~cwp_work_' + unicode(level)])
        work.append(tm['~cwp_work_' + unicode(part_levels)])
        # log.error('part list = %s', part)

        # Use level_0-derived names if applicable
        if options["cwp_level0_works"]:
            for level in range(0, part_levels + 1):
                if '~cwp_X0_work_' + unicode(level) in tm:
                    work[level] = tm['~cwp_X0_work_' + unicode(level)]
                else:
                    if level != 0:
                        work[level] = ''
                if part and len(part) > level:
                    if '~cwp_X0_part_' + unicode(level) in tm:
                        part[level] = tm['~cwp_X0_part_' + unicode(level)]
                    else:
                        if level != 0:
                            part[level] = ''

        # set up group heading and part
        if part_levels > 0:

            groupheading = work[1]
            work_main = work[ref_level]
            inter_work = ""
            work_titles = tm['~cwp_title_work_' + unicode(ref_level)]
            if ref_level > 1:
                for r in range(1, ref_level):
                    if inter_work:
                        inter_work = ': ' + inter_work
                    inter_work = part[r] + inter_work
                groupheading = work[ref_level] + ':: ' + inter_work

        else:
            groupheading = work[0]
            work_main = groupheading
            inter_work = None
            work_titles = None

        if part:
            part_main = part[0]
        else:
            part_main = work[0]
        tm['~cwp_part'] = part_main

        # fix medley text for "type 2" medleys
        if self.parts[eval(tm['~cwp_workid_0'])
                      ]['medley'] and options['cwp_medley']:
            if options["cwp_medley_text"]:
                groupheading = options["cwp_medley_text"] + ' ' + groupheading

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
                title_tag = [""]
                tw_str_lower = 'x'  # to avoid errors, reset before used
                max_d = min(ref_level, title_depth) + 1
                for d in range(1, max_d):
                    tw_str = '~cwp_title_work_' + unicode(d)
                    if self.INFO:
                        log.info("TW_STR = %s", tw_str)
                    if tw_str in tm:
                        title_tag.append(tm[tw_str])
                        # if title_tag[d] == title_tag[d - 1]:
                        #     title_work = ''
                        # else:
                        title_work = title_tag[d]  # indent if re-instate else
                        work_main = work[d]
                        diff_work[d -
                                  1] = self.diff_pair(track, tm, work_main, title_work)
                        if d > 1 and tw_str_lower in tm:
                            title_part = self.strip_parent_from_work(
                                tm[tw_str_lower], tm[tw_str], 0, False)[0].strip()
                            tm['~cwp_title_part_' +
                                unicode(d - 1)] = title_part
                            part_n = part[d - 1]
                            diff_part[d -
                                      1] = self.diff_pair(track, tm, part_n, title_part) or ""
                    else:
                        title_tag.append('')
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
                            "depth = %s, ref_level = %s, title_depth = %s",
                            depth,
                            ref_level,
                            title_depth)
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
                            log.info(
                                "addn_work = %s, addn_part = %s", addn_work, addn_part)
                        ext_groupheading = work[1] + addn_work[0]
                        ext_work = work[ref_level] + addn_work[ref_level - 1]
                        ext_inter_work = ""
                        inter_title_work = ""
                        title_groupheading = tm['~cwp_title_work_1']
                        if ref_level > 1:
                            for r in range(1, ref_level):
                                if ext_inter_work:
                                    ext_inter_work = ': ' + ext_inter_work
                                ext_inter_work = part[r] + \
                                    addn_part[r] + ext_inter_work
                            ext_groupheading = work[ref_level] + \
                                addn_work[ref_level - 1] + ':: ' + ext_inter_work
                        if title_depth > 1:
                            for r in range(1, min(title_depth, ref_level)):
                                if inter_title_work:
                                    inter_title_work = ': ' + inter_title_work
                                inter_title_work = tm['~cwp_title_part_' +
                                                      unicode(r)] + inter_title_work
                            title_groupheading = tm['~cwp_title_work_' + unicode(
                                min(title_depth, ref_level))] + ':: ' + inter_title_work

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
            log.debug(
                "%s: Now extend part...(part = %s)",
                PLUGIN_NAME,
                part_main)
        if part_main:
            if '~cwp_title_part_0' in tm:
                movement = tm['~cwp_title_part_0']
            else:
                movement = tm['~cwp_title'] or tm['title']
            diff = self.diff_pair(track, tm, work[0], movement)
            # compare with the full work name, not the stripped one unless it
            # results in nothing
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
                log.info(
                    'Set no_diff for %s = %s',
                    tm['~cwp_workid_0'],
                    no_diff)
                log.info('medley indicator for %s is %s', tm['~cwp_workid_0'],
                         self.parts[eval(tm['~cwp_workid_0'])]['medley'])
            if self.parts[eval(tm['~cwp_workid_0'])
                          ]['medley'] and options['cwp_medley']:
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
        # remove unwanted groupheadings (needed them up to now for adding
        # extensions)
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
        """
        Write out the metadata according to user options
        :param album:
        :param track:
        :return:
        """
        if self.DEBUG:
            log.debug("%s: IN PUBLISH METADATA for %s", PLUGIN_NAME, track)
        options = self.options[track]
        tm = track.metadata
        tm['~cwp_version'] = PLUGIN_VERSION
        # album composers needed by map_tags (set in set_work_artists)
        if 'composer_lastnames' in self.album_artists[album]:
            last_names = seq_last_names(self, album)
            self.append_tag(tm, '~cea_album_composer_lastnames', last_names)

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
                # i.e treat as one item, not multiple
                tm[tag] = "".join(re.split('|'.join(self.SEPARATORS), tm[tag]))

        # write "SongKong" tags
        if options['cwp_write_sk']:
            if self.DEBUG:
                log.debug("%s: writing SongKong work tags", PLUGIN_NAME)
            if '~cwp_part_levels' in tm:
                part_levels = int(tm['~cwp_part_levels'])
                for n in range(0, part_levels + 1):
                    if '~cwp_work_' + \
                            unicode(n) in tm and '~cwp_workid_' + unicode(n) in tm:
                        source = tm['~cwp_work_' + unicode(n)]
                        source_id = list(eval(tm['~cwp_workid_' + unicode(n)]))
                        if n == 0:
                            self.append_tag(
                                tm, 'musicbrainz_work_composition', source)
                            for source_id_item in source_id:
                                self.append_tag(
                                    tm, 'musicbrainz_work_composition_id', source_id_item)
                        if n == part_levels:
                            self.append_tag(tm, 'musicbrainz_work', source)
                            if 'musicbrainz_workid' in tm:
                                del tm['musicbrainz_workid']
                            # Delete the Picard version of this tag before
                            # replacing it with the SongKong version
                            for source_id_item in source_id:
                                self.append_tag(
                                    tm, 'musicbrainz_workid', source_id_item)
                        if n != 0 and n != part_levels:
                            self.append_tag(
                                tm, 'musicbrainz_work_part_level' + unicode(n), source)
                            for source_id_item in source_id:
                                self.append_tag(
                                    tm, 'musicbrainz_work_part_level' + unicode(n) + '_id', source_id_item)

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
                        self.cwp_options['Classical Extras']['Works options'][opt['name']
                                                                              ] = options[opt['option']]

            if self.INFO:
                log.info("Options %s", self.cwp_options)
            if options['ce_version_tag'] and options['ce_version_tag'] != "":
                self.append_tag(tm, options['ce_version_tag'], unicode(
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
            self.append_tag(tm, '001_errors', tm['~cwp_error'])
        if self.WARNING and "~cwp_warning" in tm:
            self.append_tag(tm, '002_warnings', tm['~cwp_warning'])

    def append_tag(self, tm, tag, source, sep=None):
        """
        pass to main append routine
        :param tm:
        :param tag:
        :param source:
        :param sep: separators may be used to split string into list on appending
        :return:
        """
        if self.DEBUG:
            log.debug(
                "In append_tag (Work parts). tag = %s, source = %s, sep =%s",
                tag,
                source,
                sep)
        append_tag(tm, tag, source, self.SEPARATORS)
        if self.DEBUG:
            log.debug(
                "Appended. Resulting contents of tag: %s are: %s",
                tag,
                tm[tag]
            )

    # def remove_tag(self, tm, tag, source):
    #     """
    #     NO LONGER USED
    #     :param tm:
    #     :param tag:
    #     :param source:
    #     :return:
    #     """
    #     if self.INFO:
    #         log.info("Work Partss - removing %s from %s", source, tag)
    #     if tag in tm:
    #         if isinstance(source, basestring):
    #             source = source.replace(u'\u2010', u'-')
    #         if source in tm[tag]:
    #             if isinstance(tm[tag], list):
    #                 old_tag = tm[tag]
    #             else:
    #                 old_tag = re.split('|'.join(self.SEPARATORS), tm[tag])
    #             new_tag = old_tag
    #             for i, tag_item in enumerate(old_tag):
    #                 if tag_item == source:
    #                     new_tag.pop(i)
    #             tm[tag] = new_tag

    # def update_tag(self, tm, tag, old_source, new_source):
    #     """
    #     NO LONGER USED
    #     :param tm:
    #     :param tag:
    #     :param old_source:
    #     :param new_source:
    #     :return:
    #     """
    #     # if old_source does not exist, it will just append new_source
    #     if self.INFO:
    #         log.info(
    #             "Work Parts - updating %s from %s to %s",
    #             tag,
    #             old_source,
    #             new_source)
    #     self.remove_tag(tm, tag, old_source)
    #     self.append_tag(tm, tag, new_source)
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
        """
        Remove common text
        :param work:
        :param parent:
        :param part_level:
        :param extend:
        :param parentId:
        :return:
        """
        # extend=True is used [ NO LONGER to find "full_parent" names] and also (with parentId) to trigger recursion if unable to strip parent name from work
        # extend=False is used when this routine is called for other purposes
        # than strict work: parent relationships
        if self.DEBUG:
            log.debug(
                "%s: STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES",
                PLUGIN_NAME)
        if not isinstance(parent, basestring):
            # in case it is a list - make sure it is a string
            parent = '; '.join(parent)
        if not isinstance(work, basestring):
            work = '; '.join(work)
        # replace any punctuation or numbers, with a space (to remove any
        # inconsistent punctuation and numbering) - (?u) specifies the
        # re.UNICODE flag in sub
        clean_parent = re.sub("(?u)[\W]", ' ', parent)
        # now allow the spaces to be filled with up to 2 non-letters
        pattern_parent = re.sub("\s", "\W{0,2}", clean_parent)
        if extend:
            pattern_parent = "(.*\s|^)(\W*" + \
                pattern_parent + "\w*)(\W*\s)(.*)"
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
                    stripped_work = m.group(1) + u'\u2026' + m.group(4)
                else:
                    stripped_work = m.group(4)
            else:
                if m.group(1):
                    stripped_work = m.group(1) + u'\u2026' + m.group(3)
                else:
                    stripped_work = m.group(3)
            # may not have a full work name in the parent (missing op. no.
            # etc.)
            # HOWEVER, this next section has been removed, because it can cause incorrect answers if lower level
                    # works are inconsistently named. Use of level_0 naming can achieve result better and
                    # We want top work to be MB-canonical, regardless
            # if m.group(3) != ": " and extend:
            #     # no. of colons is consistent with "work: part" structure
            #     if work.count(": ") >= part_level:
            #         split_work = work.split(': ', 1)
            #         stripped_work = split_work[1]
            #         full_parent = split_work[0]
            #         if len(full_parent) < len(
            #                 parent):  # don't shorten parent names! (in case colon is mis-placed)
            #             full_parent = parent
            #             stripped_work = m.group(4)
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
        if extend and stripped_work == work:
            # try just stripping only the first portion
            common_dets = longest_common_sequence(parent, work)
            common_seq = common_dets['sequence']
            seq_length = common_dets['length']
            if self.INFO:
                log.info(
                    'Checking common sequence between parent and work. Longest sequence = %s',
                    common_seq)
            if seq_length > 2 and ' ' in common_seq:  # Make sure it is non-trivial
                # self.strip_parent_from_work(work, common_seq, part_level, False)[0]
                stripped_work = work.replace(common_seq, '', 1).lstrip(' ;:,-')
        if self.INFO:
            log.info("Work: %s", work)
        if self.INFO:
            log.info("Stripped work: %s", stripped_work)
        # Changed full_parent to parent after removal of 'extend' logic above
        return (stripped_work, parent)

    def diff_pair(self, track, tm, mb_item, title_item):
        """
        Removes common text from title item
        :param track:
        :param tm:
        :param mb_item:
        :param title_item:
        :return: Reduced title item
        """
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
        removewords = self.options[track]["cwp_removewords_p"].split(',')
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
                if prefix[0] != " ":
                    prefix2 = unicode(prefix).lower().lstrip()
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
                for i, tr in enumerate(tupr):
                    tupr[i] = tr.strip("' ").strip('"')
                tupr = tuple(tupr)
                replacements.append(tupr)
            else:
                if self.ERROR:
                    log.error(
                        'Error in replacement format for replacement %s', rep)
                self.append_tag(
                    tm,
                    '~cwp_error',
                    'Error in replacement format for replacement ' +
                    rep)
        if self.INFO:
            log.info("Replacement: %s", replacements)

        #  synonyms
        strsyns = self.options[track]["cwp_synonyms"].split('/')
        synonyms = []
        for syn in strsyns:
            tup = syn.strip(' ()').split(',')
            if len(tup) == 2:
                for i, ts in enumerate(tup):
                    tup[i] = ts.strip("' ").strip('"')
                    if re.findall(r'[^\w|\&]+', tup[i], re.UNICODE):
                        if self.ERROR:
                            log.error(
                                'Synonyms must be single words without punctuation - error in %s', tup[i])
                        self.append_tag(
                            tm,
                            '~cwp_error',
                            'Synonyms must be single words without punctuation - error in ' +
                            tup[i])
                        tup[i] = "**BAD**"
                if "**BAD**" in tup:
                    continue
                else:
                    tup = tuple(tup)
                    synonyms.append(tup)
            else:
                if self.ERROR:
                    log.error('Error in synonmym format for synonym %s', syn)
                self.append_tag(
                    tm,
                    '~cwp_error',
                    'Error in synonym format for synonym ' +
                    syn)
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
            log.info(
                'Replaced Roman numerals. mb_test = %s, ti_test = %s',
                mb_test,
                ti_test)
        for key, equiv in synonyms:
            if self.INFO:
                log.info("key %s, equiv %s", key, equiv)
            # mark the equivalents so that they can be reversed later
            esc_equiv = re.escape(equiv)
            equiv_pattern = '\\b' + esc_equiv + '\\b'
            equiv = 'EQ_TO_BE_REVERSED' + equiv
            esc_key = re.escape(key)
            key_pattern = '\\b' + esc_key + '\\b'
            mb_test = re.sub(equiv_pattern, equiv, mb_test)
            ti_test = re.sub(equiv_pattern, equiv, ti_test)
            mb_test = re.sub(key_pattern, equiv, mb_test)
            ti_test = re.sub(key_pattern, equiv, ti_test)
            # better than ti_test = ti_test.replace(key, equiv)
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
        lcs = longest_common_substring(nopunc_mb, nopunc_ti)['string']
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
                    r';\s|:\s|\.\s|\-\s',
                    mb_test,
                    self.options[track]["cwp_granularity"])
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
                    return self.reverse_syn(ti_new, synonyms)
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
        # TODO Parameterize this?
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
            if ti_list_punc[0][0] == ti[0]:
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
            if i <= len(ti_list) - 1:
                ti_bit = ti_zip_list[i]
                # NB ti_bit is a tuple where the word (1st item) is grouped with its following punctuation (2nd item)
            else:
                ti_bit = ('', '')
            if self.INFO:
                log.info(
                    "i = %s, ti_bit_test = %s, ti_bit = %s",
                    i,
                    ti_bit_test,
                    ti_bit)
            # Boolean to indicate whether ti_bit is a new word
            ti_rich_list.append((ti_bit, True))
            if not ti_bit_test or (ti_bit_test and self.boil(ti_bit_test) in mb_list2):
                if ti_bit_test:
                    words += 1
                ti_rich_list[i] = (ti_bit, False)
            else:
                if ti_bit_test.lower() not in nonWords and re.findall(
                        r'\w', ti_bit[0], re.UNICODE):
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
                change = t  # NB this is a tuple
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
            d = self.options[track]["cwp_proximity"] - \
                self.options[track]["cwp_end_proximity"]
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
                            # check to see if the last char of the prev
                            # punctuation group needs to be added first
                            if len(ti_rich_list[i - 1][0][1]) > 1:
                                # i.e. ti_bit[1][-1] of previous loop
                                ti_new.append(ti_rich_list[i - 1][0][1][-1])
                    ti_new.append(ti_bit[0])
                    if len(ti_bit[1]) > 1:
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
                        ti_new.append(u'\u2026 ')

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
            sub_len = ti_len * \
                float(self.options[track]["cwp_substring_match"]) / 100
            if self.DEBUG:
                log.debug("test sub....")
            lcs = longest_common_substring(nopunc_mb, nopunc_ti)['string']
            if self.INFO:
                log.info(
                    "Longest common substring is: %s. Threshold length is %s",
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
            if ti_list_new and mb_list2:
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
            return self.reverse_syn(ti, synonyms)
        else:
            return None

    def reverse_syn(self, term, synonyms):
        """
        reverse any synonyms left in the tititle item
        :param term: the title item
        :param synonyms: tuples
        :return: title item without synonyms
        """
        for key, equiv in synonyms:
            if self.INFO:
                log.info("key %s, equiv %s", key, equiv)
            equiv = 'EQ_TO_BE_REVERSED ' + equiv
            esc_equiv = re.escape(equiv)
            equiv_pattern = '\\b' + esc_equiv + '\\b'
            term = re.sub(equiv_pattern, key, term)
        return term

    def boil(self, s):
        """
        Remove punctuation, spaces, capitals and accents for string comprisons
        :param s:
        :return:
        """
        if self.DEBUG:
            log.debug("boiling %s", s)
        s = s.lower()
        if isinstance(s, str):
            s = s.decode('unicode_escape')
        s = s.replace('sch', 'sh')\
            .replace(u'\xdf', 'ss')\
            .replace('sz', 'ss')\
            .replace(u'\u0153', 'oe')\
            .replace('oe', 'o')\
            .replace(u'\u00fc', 'ue')\
            .replace('ue', 'u')\
            .replace('ae', 'a')
        punc = re.compile(r'\W*')
        s = ''.join(
            c for c in unicodedata.normalize(
                'NFD',
                s) if unicodedata.category(c) != 'Mn')
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
    opts = plugin_options('artists') + plugin_options('tag') + \
        plugin_options('workparts') + plugin_options('other')

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
                log.error(
                    "Error in setting options for option = %s",
                    opt['option'])

    def __init__(self, parent=None):
        super(ClassicalExtrasOptionsPage, self).__init__(parent)
        self.ui = Ui_ClassicalExtrasOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        """
        Load the options - NB all options are set in plugin_options, so this just parses that
        :return:
        """
        opts = plugin_options('artists') + plugin_options('tag') + \
            plugin_options('workparts') + plugin_options('other')
        # count = 0
        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
                not_cwp_setting = not self.config.setting[opt['option']]
                # To force a toggle so that signal given
                self.ui.__dict__[ui_name].setChecked(not_cwp_setting)
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
                not_cea_setting = not self.config.setting[opt['option']]
                # To force a toggle so that signal given
                self.ui.__dict__[ui_name].setChecked(not_cea_setting)
            else:
                ui_name = opt['option']
            if opt['type'] == 'Boolean':
                self.ui.__dict__[ui_name].setChecked(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Text':
                self.ui.__dict__[ui_name].setText(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Combo':
                self.ui.__dict__[ui_name].setEditText(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Integer':
                self.ui.__dict__[ui_name].setValue(
                    self.config.setting[opt['option']])
            else:
                log.error(
                    "Error in loading options for option = %s",
                    opt['option'])

    def save(self):
        opts = plugin_options('artists') + plugin_options('tag') + \
            plugin_options('workparts') + plugin_options('other')

        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
            else:
                ui_name = opt['option']
            if opt['type'] == 'Boolean':
                self.config.setting[opt['option']] = self.ui.__dict__[
                    ui_name].isChecked()
            elif opt['type'] == 'Text':
                self.config.setting[opt['option']] = unicode(
                    self.ui.__dict__[ui_name].text())
            elif opt['type'] == 'Combo':
                self.config.setting[opt['option']] = unicode(
                    self.ui.__dict__[ui_name].currentText())
            elif opt['type'] == 'Integer':
                self.config.setting[opt['option']
                                    ] = self.ui.__dict__[ui_name].value()
            else:
                log.error(
                    "Error in saving options for option = %s",
                    opt['option'])


#################
# MAIN ROUTINE  #
#################

register_track_metadata_processor(PartLevels().add_work_info)
register_track_metadata_processor(ExtraArtists().add_artist_info)
register_options_page(ClassicalExtrasOptionsPage)
