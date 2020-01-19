# -*- coding: utf-8 -*-
"""
Declare constants for Picard Classical Extras plugin
v2.0.2
"""
# Copyright (C) 2018 Mark Evens
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

RELATION_TYPES = {
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

ARTISTS_OPTIONS = [
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
     'default': False
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
     'default': False
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
     'default': True
     },
    {'option': 'cea_composer_album',
     'name': 'Album prefix',
     # 'value': 'Composer', # Can't use 'value' if there is only one option, otherwise False will revert to default
     'type': 'Boolean',
     'default': True
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
    # {'option': 'cea_genres',
    #  'name': 'infer work types',
    #  'type': 'Boolean',
    #  'default': True
    #  },
    # Note that the above is no longer used - replaced by cwp_genres_infer from v0.9.2
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
     'default': False
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
    {'option': 'cea_inst_credit',
     'name': 'use credited instrument',
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
    {'option': 'cea_lyricist',
     'name': 'lyricist',
     'type': 'Text',
     'default': 'lyrics'
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
     }
]

TAG_OPTIONS = [
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
     'default': ''
     },
    {'option': 'cea_clear_tags',
     'name': 'Clear previous tags',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cea_tag_sort',
     'name': 'populate sort tags',
     'type': 'Boolean',
     'default': True
     }
]
#  (tag mapping detail lines)
default_list = [
    ('album_soloists, album_ensembles, album_conductors', 'artist, artists', False),
    ('recording_artists', 'artist, artists', True),
    ('soloist_names, ensemble_names, conductors', 'artist, artists', True),
    ('soloists', 'soloists, trackartist, involved people', False),
    ('release', 'release_name', False),
    ('ensemble_names', 'band', False),
    ('composers', 'artist', True),
    ('MB_artists', 'composer', True),
    ('arranger', 'composer', True)
]
TAG_DETAIL_OPTIONS = []
for i in range(0, 16):
    if i < len(default_list):
        default_source, default_tag, default_cond = default_list[i]
    else:
        default_source = ''
        default_tag = ''
        default_cond = False
    TAG_DETAIL_OPTIONS.append({'option': 'cea_source_' + str(i + 1),
                               'name': 'line ' + str(i + 1) + '_source',
                               'type': 'Combo',
                               'default': default_source
                               })
    TAG_DETAIL_OPTIONS.append({'option': 'cea_tag_' + str(i + 1),
                               'name': 'line ' + str(i + 1) + '_tag',
                               'type': 'Text',
                               'default': default_tag
                               })
    TAG_DETAIL_OPTIONS.append({'option': 'cea_cond_' + str(i + 1),
                               'name': 'line ' + str(i + 1) + '_conditional',
                               'type': 'Boolean',
                               'default': default_cond
                               })

WORKPARTS_OPTIONS = [
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
    {'option': 'cwp_allow_empty_parts',
     # allow parts to be blank if there is arrangement or partial text label
     # checked = split
     'name': 'allow-empty-parts',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_common_chars',
     # for use in strip_parent_from_work
     # where no match exists and substring elimination is used
     # this sets the minimum number of matching 'words' (words followed by punctuation/spaces or EOL)
     #  required before they will be eliminated
     # 0 => no elimination
     # default is 2 words
     'name': 'min common words to eliminate',
     'type': 'Integer',
     'default': 2
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
    {'option': 'cwp_split_hyphenated',
     # splitting of hyphenated words for matching purposes
     # checked = split
     'name': 'hyphen-splitting',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_substring_match',
     # Proportion of a string to be matched to a (usually larger) string for
     # it to be considered essentially similar
     'name': 'similarity threshold',
     'type': 'Integer',
     'default': 100
     },
    {'option': 'cwp_fill_part',
     # Fill part name with title text if it would otherwise
     # have no text other than arrangement or partial annotations
     'name': 'disallow empty part names',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_prepositions',
     'name': 'prepositions',
     'type': 'Text',
     'default': "a, the, in, on, at, of, after, and, de, d'un, d'une, la, le, no, from, &, e, ed, et, un,"
                " une, al, ala, alla"
     },
    {'option': 'cwp_removewords',
     'name': 'ignore prefixes',
     'type': 'Text',
     'default': ' part , act , scene, movement, movt, no. , no , n., n , nr., nr , book , the , a , la , le , un ,'
                ' une , el , il , tableau, from , KV ,Concerto in, Concerto'
     },
    {'option': 'cwp_synonyms',
     'name': 'synonyms',
     'type': 'PlainText',
     'default': '(1, one) / (2, two) / (3, three) / (&, and) / (Rezitativ, Recitativo, Recitative) / '
                '(Sinfonia, Sinfonie, Symphonie, Symphony) / (Arie, Aria) / '
                '(Minuetto, Menuetto, Minuetta, Menuet, Minuet) / (Bourée, Bouree , Bourrée)'
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
    {'option': 'cwp_derive_works_from_title',
     'name': 'Derive works from title',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_movt_tag_inc',
     'name': 'movement tag inc num',
     'type': 'Text',
     'default': 'part, movement, subtitle'
     },
    {'option': 'cwp_movt_tag_exc',
     'name': 'movement tag exc num',
     'type': 'Text',
     'default': ''
     },
    {'option': 'cwp_movt_tag_inc1',
     'name': '1-level movement tag inc num',
     'type': 'Text',
     'default': 'movement'
     },
    {'option': 'cwp_movt_tag_exc1',
     'name': '1-level movement tag exc num',
     'type': 'Text',
     'default': ''
     },
    {'option': 'cwp_movt_no_tag',
     'name': 'movement num tag',
     'type': 'Text',
     'default': 'movementnumber'
     },
    {'option': 'cwp_movt_tot_tag',
     'name': 'movement tot tag',
     'type': 'Text',
     'default': 'movementtotal'
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
     'default': 'Medley'
     }
]
# Options on "Genres etc." tab

GENRE_OPTIONS = [
    {'option': 'cwp_genre_tag',
     'name': 'main genre tag',
     'type': 'Text',
     'default': 'genre'
     },
    {'option': 'cwp_subgenre_tag',
     'name': 'sub-genre tag',
     'type': 'Text',
     'default': 'sub-genre'
     },
    {'option': 'cwp_genres_use_file',
     'name': 'source genre from file',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_use_folks',
     'name': 'source genre from folksonomy tags',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_use_worktype',
     'name': 'source genre from work-type(s)',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_infer',
     'name': 'infer genre from artist details(s)',
     'type': 'Boolean',
     'default': False
     },
    # Note that the "infer from artists" option was in  the "artists"
    # section - legacy from v0.9.1 & prior
    {'option': 'cwp_genres_filter',
     'name': 'apply filter to genres',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_classical_main',
     'name': 'classical main genres',
     'type': 'PlainText',
     'default': 'Classical, Chamber music, Concerto, Symphony, Opera, Orchestral, Sonata, Choral, Aria, Ballet, '
                'Oratorio, Motet, Symphonic poem, Suite, Partita, Song-cycle, Overture, '
                'Mass, Cantata'
     },
    {'option': 'cwp_genres_classical_sub',
     'name': 'classical sub-genres',
     'type': 'PlainText',
     'default': 'Chant, Classical crossover, Minimalism, Avant-garde, Impressionist, Aria, Duet, Trio, Quartet'
     },
    {'option': 'cwp_genres_other_main',
     'name': 'general main genres',
     'type': 'PlainText',
     'default': 'Alternative music, Blues, Country, Dance, Easy listening, Electronic music, Folk, Folk / pop, '
                'Hip hop / rap, Indie,  Religious, Asian, Jazz, Latin, New age, Pop, R&B / Soul, Reggae, Rock, '
                'World music, Celtic folk, French Medieval'
     },
    {'option': 'cwp_genres_other_sub',
     'name': 'general sub-genres',
     'type': 'PlainText',
     'default': 'Song, Vocal, Christmas, Instrumental'
     },
    {'option': 'cwp_genres_arranger_as_composer',
     'name': 'treat arranger as for composer for genre-setting',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_classical_all',
     'name': 'make tracks classical',
     'value': 'all',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_genres_classical_selective',
     'name': 'make tracks classical',
     'value': 'selective',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_genres_classical_exclude',
     'name': 'exclude "classical" from main genre tag',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_genres_flag_text',
     'name': 'classical flag',
     'type': 'Text',
     'default': '1'
     },
    {'option': 'cwp_genres_flag_tag',
     'name': 'classical flag tag',
     'type': 'Text',
     'default': 'is_classical'
     },
    {'option': 'cwp_genres_default',
     'name': 'default genre',
     'type': 'Text',
     'default': 'Other'
     },
    {'option': 'cwp_instruments_tag',
     'name': 'instruments tag',
     'type': 'Text',
     'default': 'instrument'
     },
    {'option': 'cwp_instruments_MB_names',
     'name': 'use MB instrument names',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_instruments_credited_names',
     'name': 'use credited instrument names',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_key_tag',
     'name': 'key tag',
     'type': 'Text',
     'default': 'key'
     },
    {'option': 'cwp_key_contingent_include',
     'name': 'contingent include key in workname',
     'value': 'contingent',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_key_never_include',
     'name': 'never include key in workname',
     'value': 'never',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_key_include',
     'name': 'include key in workname',
     'value': 'always',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_workdate_tag',
     'name': 'workdate tag',
     'type': 'Text',
     'default': 'work_year'
     },
    {'option': 'cwp_workdate_source_composed',
     'name': 'use composed for workdate',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_workdate_source_published',
     'name': 'use published for workdate',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_workdate_source_premiered',
     'name': 'use premiered for workdate',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_workdate_use_first',
     'name': 'use workdate sources sequentially',
     'value': 'sequence',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_workdate_use_all',
     'name': 'use all workdate sources',
     'value': 'all',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_workdate_annotate',
     'name': 'annotate dates',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_workdate_include',
     'name': 'include workdate in workname',
     'type': 'Boolean',
     'default': True
     },
    {'option': 'cwp_period_tag',
     'name': 'period tag',
     'type': 'Text',
     'default': 'period'
     },
    {'option': 'cwp_periods_arranger_as_composer',
     'name': 'treat arranger as for composer for period-setting',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_period_map',
     'name': 'period map',
     'type': 'PlainText',
     'default': 'Early, -3000,800; Medieval, 800,1400; Renaissance, 1400, 1600; Baroque, 1600,1750; '
                'Classical, 1750,1820; Early Romantic, 1800,1850; Late Romantic, 1850,1910; '
                '20th Century, 1910,1975; Contemporary, 1975,2525'
     }
]
# Picard options which are also saved (NB only affects plugin processing - not main Picard processing)
PICARD_OPTIONS = [
    {'option': 'standardize_artists',
     'name': 'standardize artists',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'translate_artist_names',
     'name': 'translate artist names',
     'type': 'Boolean',
     'default': True
     },
]

# other options (not saved in file tags)
OTHER_OPTIONS = [
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
    {'option': 'cwp_use_muso_refdb',
     'name': 'use Muso ref database',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_muso_genres',
     'name': 'use Muso classical genres',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_muso_classical',
     'name': 'use Muso classical composers',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_muso_dates',
     'name': 'use Muso composer dates',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_muso_periods',
     'name': 'use Muso periods',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_muso_path',
     'name': 'path to Muso database',
     'type': 'Text',
     'default': 'C:\\Users\\Public\\Music\\muso\\database'
     },
    {'option': 'cwp_muso_refdb',
     'name': 'name of Muso reference database',
     'type': 'Text',
     'default': 'Reference.xml'
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
    {'option': 'log_basic',
     'type': 'Boolean',
     'default': True
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
    {'option': 'ce_tagmap_override',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'cwp_override',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'ce_genres_override',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'ce_options_overwrite',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'ce_no_run',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'ce_show_ui_tags',
     'type': 'Boolean',
     'default': False
     },
    {'option': 'ce_ui_tags',
     ## Note that this is not just for work parts (although that is the main use),
     # but cwp prefix is to make use of code for synonyms
     'name': 'tags for ui columns',
     'type': 'PlainText',
     'default': 'Work diff: (groupheading_DIFF, work_DIFF, top_work_DIFF, grouping_DIFF) / Part diff: (part_DIFF, movement_DIFF) / Missing file metadata: 002_important_warning'
     }
]

ARTIST_TYPE_ORDER = {'vocal': 1,
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

CYRILLIC_UPPER = {
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
CYRILLIC_LOWER = {
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

def tag_strings(pre):
    TAG_STRINGS = {
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
                pre + '_arrangers',
                '~arranger_sort',
                pre + '_arrangers_sort'),
            'performer': (
                'performer:',
                pre + '_performers',
                '~performer_sort',
                pre + '_performers_sort'),
            'instrument': (
                'performer:',
                pre + '_performers',
                '~performer_sort',
                pre + '_performers_sort'),
            'vocal': (
                'performer:',
                pre + '_performers',
                '~performer_sort',
                pre + '_performers_sort'),
            'performing orchestra': (
                'performer:orchestra',
                pre + '_ensembles',
                '~performer_sort',
                pre + '_ensembles_sort'),
            'conductor': (
                'conductor',
                pre + '_conductors',
                '~conductor_sort',
                pre + '_conductors_sort'),
            'chorus master': (
                'conductor',
                pre + '_chorusmasters',
                '~conductor_sort',
                pre + '_chorusmasters_sort'),
            'concertmaster': (
                'performer',
                pre + '~_leaders',
                '~performer_sort',
                pre + '_leaders_sort')}
    return TAG_STRINGS

INSERTIONS = ['writer',
              'lyricist',
              'librettist',
              'revised by',
              'translator',
              'arranger',
              'reconstructed by',
              'orchestrator',
              'instrument arranger',
              'vocal arranger',
              'chorus master']