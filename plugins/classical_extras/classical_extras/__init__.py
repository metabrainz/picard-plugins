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
PLUGIN_VERSION = '0.6.4'
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PyQt4 import QtCore
from picard.ui.options import register_options_page, OptionsPage
from picard.plugins.classical_extras.ui_options_classical_extras import Ui_ClassicalExtrasOptionsPage
from picard import config, log
from picard.config import BoolOption, IntOption, TextOption
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial
import collections
import re
import unicodedata as ud
import traceback
import json

##########################
# MODULE-WIDE COMPONENTS #
##########################

# CONSTANTS

prefixes = ['the', 'a', 'an', 'le', 'la', 'les', 'los', 'il']

# Non-Latin character processing
latin_letters= {}

def is_latin(uchr):
    try: return latin_letters[uchr]
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
            if len(string) > index+1:
                if string[index+1] not in lower_case_letters.keys():
                    char = char.upper()
            else:
                char = char.upper()
        translit_string += char
    # fix multi-chars
    translit_string = translit_string.replace('ks','x').replace('iy ','i ')
    return translit_string

def remove_middle(performer):
    plist = performer.split()
    if len(plist) == 3:
        return plist[0] + ' ' + plist[2]                             # to remove middle names of Russian composers
    else:
        return performer

# Sorting etc.
def sort_field(performer):
    sorter=re.compile(r'(.*)\s(.*)$')
    match=sorter.search(performer)
    if match:
        return match.group(2) + ", " + match.group(1)
    else:
        return performer

def unsort(performer):
    unsorter=re.compile(r'^(.+),\s(.*)')
    match=unsorter.search(performer)
    if match:
        return match.group(2).strip() + " " + match.group(1)
    else:
        return performer

def stripsir(performer):
    sir=re.compile(r'^(Sir|Maestro)\b\s*(.*)',re.IGNORECASE)
    match=sir.search(performer)
    if match:
        return match.group(2).strip()
    else:
        return performer

def swap_prefix(performer):
    prefix = '|'.join(prefixes)
    swap=re.compile(r'^(' + prefix + r')\b\s*(.*)', re.IGNORECASE)
    match=swap.search(performer)
    if match:
        return match.group(2) + ", " + match.group(1)
    else:
        return performer

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

def longest_common_sequence(list1, list2, start=0):
    min_len = min(len(list1),len(list2))
    longest = 0
    seq = None
    for k in range(start,min_len):
        for i in range(k,min_len + 1):
            if list1[k:i] == list2[k:i] and i-k>longest:
                longest = i-k
                seq = list1[k:i]
    return {'sequence': seq, 'length': longest}



#################
#################
# EXTRA ARTISTS #
#################
#################

class ExtraArtists:
    #CONSTANTS

    def __init__(self):
        self.album_artists = collections.defaultdict(lambda: collections.defaultdict(dict))
            # collection of artists to be applied at album level
        self.track_listing = []



    def add_artist_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        options = album.tagger.config.setting
        if  not options["classical_extra_artists"]:
            return

        #CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.DEBUG = options["log_debug"]
        self.INFO = options["log_info"]
        self.ORCHESTRAS = options["cea_orchestras"].split(',')
        self.CHOIRS = options["cea_choirs"].split(',')
        self.GROUPS = options["cea_groups"].split(',')
        self.ENSEMBLE_TYPES = self.ORCHESTRAS + self.CHOIRS + self.GROUPS

        if self.DEBUG: log.debug("%s: add_artist_info", PLUGIN_NAME)

        self.alt_artists(album, track_metadata)
        tm = track_metadata
        track = album._new_tracks[-1]     # Jump through hoops to get track object!!
        self.track_listing.append(track)
        if '~cea_album_track_composer_lastnames' in tm:                          # composer last names created by alt_artists function
            composer_lastnames = track_metadata['~cea_album_track_composer_lastnames']
            if album in self.album_artists:
                if 'composer_lastnames' in self.album_artists[album]:
                    if composer_lastnames not in self.album_artists[album]['composer_lastnames']:
                        self.album_artists[album]['composer_lastnames'].append(composer_lastnames)
                else:
                    self.album_artists[album]['composer_lastnames'] = [composer_lastnames]
            else:
                self.album_artists[album]['composer_lastnames'] = [composer_lastnames]
        else:
            if self.WARNING: log.warning("%s: No _cea_album_track_composer_lastnames variable available for recording \"%s\".", PLUGIN_NAME, tm['title'])
            self.append_tag(track_metadata, '~cea_warning', 'No _cea_album_track_composer_lastnames variable available for recording')
        if 'recording' in trackXmlNode.children:
            self.is_classical = True
            for record in trackXmlNode.children['recording']:

                performerList = self.artist_process_metadata(track, record, 'instrument')
        #         # returns [(instrument, artist name, artist sort name} or None if no instruments found
                if performerList:
                    if self.DEBUG: log.debug("%s: Instrument Performers: %s", PLUGIN_NAME, performerList)
                    self.set_performer(album, performerList, tm)

                arrangerList = self.artist_process_metadata(track, record, 'instrument arranger')
        #         # returns {instrument, arranger name, arranger sort name} or None if no instrument arrangers found
                if arrangerList:
                    if self.DEBUG: log.debug("%s: Instrument Arrangers: %s", PLUGIN_NAME, arrangerList)
                    self.set_arranger(album, arrangerList,tm)

                if options['cea_orchestrator'] != "":    
                    orchestratorList = self.artist_process_metadata(track, record, 'orchestrator')
            #         # returns {None, orchestrator name, orchestrator sort name} or None if no orchestrators found
                    if orchestratorList:
                        if self.DEBUG: log.debug("%s: Orchestrators: %s", PLUGIN_NAME, orchestratorList)
                        self.set_orchestrator(album, orchestratorList,tm)

                if options['cea_chorusmaster'] != "":
                    chorusmasterList = self.artist_process_metadata(track, record, 'chorus master')
            #         # returns {None, chorus master name, chorus master sort name} or None if no chorus masters found
                    if chorusmasterList:
                        if self.DEBUG: log.debug("%s: Chorus Masters: %s", PLUGIN_NAME, chorusmasterList)
                        self.set_chorusmaster(album, chorusmasterList,tm)

                if options['cea_concertmaster'] != "":
                    leaderList = self.artist_process_metadata(track, record, 'concertmaster')
            #         # returns {None, leader name, leader sort name} or None if no leaders
                    if leaderList:
                        if self.DEBUG: log.debug("%s: Leaders: %s", PLUGIN_NAME, leaderList)
                        self.set_leader(album, leaderList,tm)

        if track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
            self.process_album(album)

    def alt_artists(self, album, metadata):
        if self.INFO: log.info("RUNNING %s - alternative artists", PLUGIN_NAME)
        self.sort_performers(album, metadata)                 #provide all the sort fields before creating the new variables
        soloists = []
        soloist_names=[]
        soloists_sort =[]
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
                        if album.tagger.config.setting['cea_cyrillic']:
                            conductor = remove_middle(unsort(conductorsort[index]))
                    conductors.append(conductor)
                    if stripsir(conductor) in metadata['~albumartists'] or sort_field(stripsir(conductor)) in metadata['~albumartists_sort'] \
                    or stripsir(conductor) in metadata['~albumartists_sort']:
                       album_conductors.append(conductor)
                       album_conductors_sort.append(conductorsort[index])
            if key.startswith('performer'):
                mainkey, subkey = key.split(':', 1)
                for performer in values:
                    if not only_roman_chars(performer):
                        if album.tagger.config.setting['cea_cyrillic']:
                            performer = remove_middle(get_roman(performer))
                    performername = performer
                    if subkey:
                        perftype = ' ('+subkey+')'
                    else:
                        perftype = ''
                    performer = performer + perftype
                    if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(performername):
                        ensembles.append(performer)
                        if performername not in ensemble_names:
                            ensemble_names.append(performername)
                        if performername in metadata['~albumartists'] or swap_prefix(performername) in metadata['~albumartists_sort'] \
                        or performername in metadata['~albumartists_sort']:
                            album_ensembles.append(performername)
                    else:
                        soloists.append(performer)
                        if performername not in soloist_names:
                            soloist_names.append(performername)
                        match=last.search(sort_field(stripsir(performername)))
                        if match:
                            performerlast = match.group(1)
                        else:
                            performerlast = sort_field(stripsir(performername))
                        if stripsir(performername) in metadata['~albumartists'] or performerlast in metadata['~albumartists_sort'] \
                        or stripsir(performername) in metadata['~albumartists_sort']:
                            album_soloists.append(performername)
                        else:
                            if not subkey in self.ENSEMBLE_TYPES and not self.ensemble_type(performername):
                                support_performers.append(performer)
            if key.startswith('~performer_sort'):
                mainkey, subkey = key.split(':', 1)
                for performer in values:
                    if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(performer):
                        ensembles_sort.append(performer)
                        if performer in metadata['~albumartists_sort'] or unsort(performer) in metadata['~albumartists']:    #in case of sort differences
                            album_ensembles_sort.append(performer)
                    else:
                        soloists_sort.append(performer)
                        match=last.search(performer)
                        if match:
                            performerlast = match.group(1)
                        else:
                            performerlast = sort_field(performer)


                        if performer in metadata['~albumartists_sort'] or performerlast in metadata['~albumartists']:    #in case of sort differences
                            album_soloists_sort.append(performer)
                        else:
                            if not subkey in self.ENSEMBLE_TYPES and not self.ensemble_type(performer):
                                support_performers_sort.append(performer)
            if key == 'composer':
                composers_sort = metadata['composersort'].split(';')
                metadata['~cea_composers_sort'] = composers_sort
                for index, composer in enumerate(values):
                    composersort = composers_sort[index]
                    match=last.search(composersort)
                    if match:
                        composerlast = match.group(1)
                    else:
                        composerlast = composersort
                    if not only_roman_chars(composer):
                        if album.tagger.config.setting['cea_cyrillic']:
                            composer = remove_middle(unsort(composersort))
                    composers.append(composer)
                    if stripsir(composer) in metadata['~albumartists'] or sort_field(stripsir(composer)) in metadata['~albumartists_sort'] \
                    or stripsir(composer) in metadata['~albumartists_sort'] or composersort in metadata['~albumartists_sort'] \
                    or unsort(composersort) in metadata['~albumartists'] or composerlast in metadata['~albumartists'] \
                    or composerlast in metadata['~albumartists_sort']:
                       album_composers.append(composer)
                       album_composers_sort.append(composersort)
                       album_composer_lastnames.append(composerlast)
        metadata['~cea_soloists'] = soloists
        metadata['~cea_soloist_names'] = soloist_names
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
        metadata['~cea_conductors'] = conductors

    def sort_performers(self, album, metadata):
        for key, values in metadata.rawitems():
            if key.startswith('conductor'):
                conductorsort = []
                for conductor in values:
                    if album.tagger.config.setting['cea_cyrillic']:
                        if not only_roman_chars(conductor):
                            conductor = remove_middle(get_roman(conductor))
                    conductorsort.append(sort_field(conductor))
                metadata['~cea_conductors_sort'] = conductorsort
            if not key.startswith('performer'):
                continue
            mainkey, subkey = key.split(':', 1)
            performersort = []
            for performer in values:
                if album.tagger.config.setting['cea_cyrillic']:
                    if not only_roman_chars(performer):
                        performer = remove_middle(get_roman(performer))
                if subkey in self.ENSEMBLE_TYPES or self.ensemble_type(performer):
                    performersort.append(swap_prefix(performer))
                else:
                    performersort.append(sort_field(performer))
            sortkey = "~performer_sort:%s" % subkey
            if self.DEBUG: log.debug("%s: sortkey = %s, performersort = %s", PLUGIN_NAME, sortkey, performersort)   #debug
            metadata[sortkey] = performersort

    # Checks for ensembles
    def ensemble_type(self, performer):
        for ensemble_name in self.ORCHESTRAS:
            ensemble=re.compile(r'(.*)\b' + ensemble_name + r'\b(.*)', re.IGNORECASE)
            if ensemble.search(performer):
                return 'Orchestra'
        for ensemble_name in self.CHOIRS:
            ensemble=re.compile(r'(.*)\b' + ensemble_name + r'\b(.*)', re.IGNORECASE)
            if ensemble.search(performer):
                return 'Choir'
        for ensemble_name in self.GROUPS:
            ensemble=re.compile(r'(.*)\b' + ensemble_name + r'\b(.*)', re.IGNORECASE)
            if ensemble.search(performer):
                return 'Group'
        return False




    def artist_process_metadata(self, track, record, artistType):
        relationList = []
        if 'relation_list' in record.children:
            for relation_list_item in record.relation_list:
                if 'target_type' in relation_list_item.attribs:
                    if relation_list_item.attribs['target_type'] == 'artist':
                        if 'relation' in relation_list_item.children:
                            for relation_item in relation_list_item.relation:
                                relationList.append(relation_item)
            return self.artist_process_relations(relationList, artistType)
        else:
            if self.ERROR: log.error("%s: %r: MusicBrainz artist xml result not in correct format.",
                      PLUGIN_NAME, track)
            extra_msg = ' Turn on info logging and refresh for more information' if not self.INFO else ''
            if self.ERROR: log.error("This could be because the recording has no relationships on MusicBrainz.%s", extra_msg)
            if self.INFO: log.info("Check the details on MusicBrainz. XML returned is as follows:")
            if self.INFO: log.error(record)
            self.append_tag(track.metadata, '~cea_error', 'MusicBrainz artist xml result not in correct format.')
        return None

    def artist_process_relations(self, relations, artistType):
        artists = []
        for rel in relations:
            if 'type' in rel.attribs:
                if rel.attribs['type'] == artistType:
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            name = rel.artist[0].name[0].text
                            sort_name = rel.artist[0].sort_name[0].text
                            instrument_list = []
                            if 'attribute_list' in rel.children:
                                for inst in rel.attribute_list[0].attribute:
                                    if instrument_list:
                                        instrument_list.append(inst.text)
                                    else:
                                        instrument_list = [inst.text]
                            if instrument_list:
                                for instrument in instrument_list:
                                    artist = (instrument, name, sort_name)
                                    artists.append(artist)
                            else:
                                artist = (None, name, sort_name)
                                artists.append(artist)
        if artists:
            if self.DEBUG: log.debug("%s: Artists of type %s found: %s", PLUGIN_NAME, artistType, artists)                          #debug
        else:
            if self.DEBUG: log.debug("%s: No Artist found", PLUGIN_NAME)                                                                    #debug
        return artists

    def process_album(self, album):
        options = album.tagger.config.setting
        blank_tags = options['cea_blank_tag'].split(",") + options['cea_blank_tag_2'].split(",")
        sort_tags = options['cea_tag_sort']
        for track in self.track_listing:
            tm = track.metadata
            tm['~cea_version'] = PLUGIN_VERSION
            # set work-type before any tags are blanked
            if options['cea_genres']:
                if self.is_classical:
                    self.append_tag(tm, '~cea_work_type', 'Classical')
                instrument = re.compile(r'.*\((.+)\)')
                vocals = re.compile(r'.*\(((.*)vocals)\)')
                if '~cea_ensembles' in tm:
                    large = False
                    if 'performer:orchestra' in tm:
                        large = True
                        self.append_tag(tm, '~cea_work_type', 'Orchestral')
                        if '~cea_soloists'  in tm:
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
                                        self.append_tag(tm, '~cea_work_type', 'Concerto')
                                        self.append_tag(tm, '~cea_work_type', match.group(1).title())
                                    else:
                                        self.append_tag(tm, '~cea_work_type', 'Aria')
                                        match2 = vocals.search(soloists[0])
                                        if match2:
                                            self.append_tag(tm, '~cea_work_type', match2.group(2).strip().title())
                            elif len(soloists) == 2:
                                self.append_tag(tm, '~cea_work_type', 'Duet')

                    if 'performer:choir' in tm or 'performer:choir vocals' in tm:
                        large = True
                        self.append_tag(tm, '~cea_work_type', 'Choral')
                        self.append_tag(tm, '~cea_work_type', 'Voice')
                    else:
                        if large and 'soloists' in tm and tm['soloists'].count('vocals') > 1:
                            self.append_tag(tm, '~cea_work_type','Opera')
                    if not large:
                        if '~cea_soloists' not in tm:
                            self.append_tag(tm, '~cea_work_type', 'Chamber')
                        else:
                            if 'vocals' in tm['~cea_soloists']:
                                self.append_tag(tm, '~cea_work_type', 'Song')
                                self.append_tag(tm, '~cea_work_type', 'Voice')
                            else:
                                self.append_tag(tm, '~cea_work_type', 'Chamber')
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
                                    self.append_tag(tm, '~cea_work_type', 'Instrumental')
                                    self.append_tag(tm, '~cea_work_type', match.group(1).title())
                                else:
                                    self.append_tag(tm, '~cea_work_type', 'Song')
                                    self.append_tag(tm, '~cea_work_type', 'Voice')
                                    self.append_tag(tm, '~cea_work_type', match.group(1).title())
                        else:
                            if 'vocals' not in soloists:
                                self.append_tag(tm, '~cea_work_type', 'Chamber')
                            else:
                                self.append_tag(tm, '~cea_work_type', 'Song')
                                self.append_tag(tm, '~cea_work_type', 'Voice')
            # blank tags
            for tag in blank_tags:
                if tag.strip() in tm:
                    tm['~cea_'+tag.strip()] = tm[tag.strip()]  # place blanked tags into hidden variables available for re-use
                    del tm[tag.strip()]
            for i in range(0,16):
                tagline = options['cea_tag_' + str(i+1)].split(",")
                source = options['cea_source_' + str(i+1)].strip()
                no_names_source =re.sub('(_names)$','s',source)
                conditional = options['cea_cond_' + str(i+1)]
                for item, tagx in enumerate(tagline):
                    tag = tagx.strip()
                    if tag == "composer" or tag == "artist" or tag == "albumartist" or tag == "trackartist":
                        sort = "sort"
                    else:
                        sort = "_sort"
                    if source == "composer" or source == "artist" or source == "albumartist" or source == "trackartist":
                        source_sort = "sort"
                    else:
                        source_sort = "_sort"
                    if self.DEBUG: log.debug("%s: Tag mapping: Line: %s, Source: %s, Tag: %s, no_names_source: %s, sort: %s, item %s",PLUGIN_NAME, i+1, source, tag, no_names_source, sort, item)
                    if not conditional or tm[tag] == "":
                        if "~cea_" + source in tm:
                            if self.DEBUG: log.debug("cea")
                            self.append_tag(tm, tag, tm['~cea_' + source])
                            if sort_tags:
                                if "~cea_" + no_names_source + source_sort in tm:
                                    if self.DEBUG: log.debug("cea sort")
                                    self.append_tag(tm, tag + sort, tm['~cea_' + no_names_source + source_sort])
                        elif source in tm:
                            if self.DEBUG: log.debug("Picard")
                            self.append_tag(tm, tag, tm[source])
                            if sort_tags:
                                if source + "_sort" in tm:
                                    if self.DEBUG: log.debug("Picard sort")
                                    self.append_tag(tm, tag + sort, tm[source + '_sort'])
                        elif len(source) > 0 and source[0] == "\\":
                            self.append_tag(tm, tag, source[1:])
                        else:
                            pass
            if options['cea_arrangers']:
                if '~cea_arranger' in tm:
                    if 'arranger' in tm:
                        tm['arranger'] = tm['arranger'] + "; " + tm['~cea_arranger']
                    else:
                        tm['arranger'] = tm['~cea_arranger']
            if 'composer_lastnames' in self.album_artists[album]:
                last_names = self.album_artists[album]['composer_lastnames']
                tm['~cea_album_composer_lastnames'] = last_names
                if options['cea_composer_album']:
                    new_last_names = []
                    for last_name in last_names:
                        if last_name not in tm['album']:
                            new_last_names.append(last_name)
                    if len(new_last_names) > 0:
                        tm['album'] = "; ".join(new_last_names) + ": " + tm['album']

            if options['cea_options_tag'] != "":
                self.cea_options = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
                self.cea_options['Classical Extras']['Artists options']['Album prefix'] = 'Composer' if options['cea_composer_album'] \
                    else 'None'
                self.cea_options['Classical Extras']['Artists options']['Tags to blank'] = ",".join([options['cea_blank_tag'] , options['cea_blank_tag_2']])
                for i in range(0,16):
                    if options['cea_tag_'+str(i+1)] != "":
                        self.cea_options['Classical Extras']['Artists options']['line ' + str(i+1)]['source'] = options['cea_source_' + str(i+1)]
                        self.cea_options['Classical Extras']['Artists options']['line ' + str(i+1)]['tag'] = options['cea_tag_' + str(i+1)]
                        self.cea_options['Classical Extras']['Artists options']['line ' + str(i+1)]['conditional'] = options['cea_cond_' + str(i+1)]
                self.cea_options['Classical Extras']['Artists options']['populate sort tags'] = options['cea_tag_sort']
                self.cea_options['Classical Extras']['Artists options']['include arrangers'] = options['cea_arrangers']
                self.cea_options['Classical Extras']['Artists options']['infer work types'] = options['cea_genres']
                self.cea_options['Classical Extras']['Artists options']['fix cyrillic'] = options['cea_cyrillic']
                self.cea_options['Classical Extras']['Artists options']['orchestra strings'] = options['cea_orchestras']
                self.cea_options['Classical Extras']['Artists options']['choir strings'] = options['cea_choirs']
                self.cea_options['Classical Extras']['Artists options']['group strings'] = options['cea_groups']
                if options['ce_version_tag'] and options['ce_version_tag'] != "":
                    self.append_tag(tm, options['ce_version_tag'], str('Version ' + tm['~cea_version'] + ' of Classical Extras'))
                if options['cea_options_tag'] and options['cea_options_tag'] != "":
                    self.append_tag(tm, options['cea_options_tag'] + ':artists_options', json.loads(json.dumps(self.cea_options)))
            if self.ERROR and "~cea_error" in tm:
                self.append_tag(tm, '001_ERRORS', tm['~cea_error'])
            if self.WARNING and "~cea_warning" in tm:
                self.append_tag(tm, '002_WARNINGS', tm['~cea_warning'])
        self.track_listing = []
        if self.INFO: log.info("FINISHED Classical Extra Artists. Album: %s", track.album.metadata)

    def append_tag(self, tm, tag, source):
        if tag in tm:
            if source not in tm[tag]:
                if isinstance(tm[tag], basestring):
                    if self.DEBUG: log.debug("tm[tag]: %s", tm[tag])
                    tm[tag] = [tm[tag], source]
                else:
                    tm[tag].append(source)
        else:
            if tag and tag !="":
                tm[tag] = [source]

    def set_performer(self, album, performerList, tm):
        for performer in performerList:
            if performer[0]:
                instrument = performer[0].lower()
                name = performer[1]
                sort_name = performer[2]
                if album.tagger.config.setting['cea_cyrillic']:
                    if not only_roman_chars(name):
                        if not only_roman_chars(tm['performer:'+instrument]):
                            name = remove_middle(unsort(sort_name))
                            # Only remove middle name where the existing performer is in non-latin script
                if only_roman_chars(name):
                    newkey = '%s:%s' % ('performer', instrument)
                    if self.DEBUG: log.debug("%s: SETTING PERFORMER. NEW KEY = %s", PLUGIN_NAME, newkey)
                    tm.add_unique(newkey, name)
                details = name + ' (' + instrument +')'
                if '~cea_performer' in tm:
                    tm['~cea_performer'] = tm['~cea_performer'] + '; ' + details
                else:
                    tm['~cea_performer'] = details

    def set_arranger(self, album, arrangerList,tm):
        for arranger in arrangerList:
            instrument = arranger[0].lower()
            name = arranger[1]
            sort_name = arranger[2]
            if album.tagger.config.setting['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            newkey = '%s:%s' % ('arranger', instrument)
            if self.DEBUG: log.debug("NEW KEY = %s", newkey)
            tm.add_unique(newkey, name)
            if instrument:
                details = name + ' (' + instrument +')'
            else:
                details = name
            if '~cea_arranger' in tm:
                tm['~cea_arranger'] = tm['~cea_arranger'] + '; ' + details
            else:
                tm['~cea_arranger'] = details

    def set_orchestrator(self, album, orchestratorList,tm):
        options = album.tagger.config.setting
        if isinstance(tm['arranger'], basestring):
            arrangerList = tm['arranger'].split(';')
        else:
            arrangerList = tm['arranger']
        newList = arrangerList
        for orchestrator in orchestratorList:
            name = orchestrator[1]
            sort_name = orchestrator[2]
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            details = name + ' (' + options['cea_orchestrator'] + ')'
            if '~cea_orchestrator' in tm:
                tm['~cea_orchestrator'] = tm['~cea_orchestrator'] + '; ' + details
            else:
                tm['~cea_orchestrator'] = details

            for index, arranger in enumerate(arrangerList):
                if name in arranger:
                    newList[index] = details
        tm['arranger'] = newList

    def set_chorusmaster(self, album, chorusmasterList,tm):
        options = album.tagger.config.setting
        if isinstance(tm['conductor'], basestring):
            conductorList = tm['conductor'].split(';')
        else:
            conductorList = tm['conductor']
        newList = conductorList
        for chorusmaster in chorusmasterList:
            name = chorusmaster[1]
            sort_name = chorusmaster[2]
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            details = name + ' (' + options['cea_chorusmaster'] + ')'
            if '~cea_chorusmaster' in tm:
                tm['~cea_chorusmaster'] = tm['~cea_chorusmaster'] + '; ' + details
            else:
                tm['~cea_chorusmaster'] = details

            for index, conductor in enumerate(conductorList):
                if name in conductor:
                    newList[index] = details
        tm['conductor'] = newList

    def set_leader(self, album, leaderList,tm):
        options = album.tagger.config.setting
        for leader in leaderList:
            name = leader[1]
            sort_name = leader[2]
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            newkey = '%s:%s' % ('performer', options['cea_concertmaster'])
            if self.DEBUG: log.debug("%s: SETTING PERFORMER. NEW KEY = %s", PLUGIN_NAME, newkey)
            tm.add_unique(newkey, name)
            details = name + ' (' + options['cea_concertmaster'] + ')'
            if '~cea_leader' in tm:
                tm['~cea_leader'] = tm['~cea_leader'] + '; ' + details
            else:
                tm['~cea_leader'] = details





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
            # maintains list of parent of each workid, or None if no parent found, so that XML lookup only executed if no existing record
        self.partof = {}
            # the inverse of the above (immediate children of each parent)
        self.works_queue = self.WorksQueue()
            # lookup queue - holds track/album pairs for each queued workid (may be more than one pair per id, especially for higher-level parts)
        self.parts = collections.defaultdict(lambda: collections.defaultdict(dict))
            # metadata collection for all parts - structure is {workid: {name: , parent: , (track,album): {part_levels}}, etc}
        self.pending_strip = collections.defaultdict(lambda: collections.defaultdict(dict))
            # metadata collection for parts awaiting higher-level text stripping - structure is {(track, album): {workid: {child: part_level:]}, etc}
        self.top_works = collections.defaultdict(dict)
            # metadata collection for top-level works for (track, album) - structure is {(track, album): {workId: }, etc}
        self.trackback  = collections.defaultdict(lambda: collections.defaultdict(dict))
            # hierarchical iterative work structure - {album: {id: , children:{id: , children{}, id: etc}, id: etc} }
        self.work_listing = collections.defaultdict(list)
            # contains list of workIds for each album
        self.top = collections.defaultdict(list)
            # self.top[album] = list of work Ids which are top-level works in album



########################################
# SECTION 1 - Initial track processing #
########################################

    def add_work_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        options = album.tagger.config.setting
        if not options["classical_work_parts"]:
            return

        # CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.DEBUG = options["log_debug"]
        self.INFO = options["log_info"]

        self.MAX_RETRIES = options["cwp_retries"]           #Maximum number of XML- lookup retries if error returned from server
        self.SUBSTRING_MATCH = float(options["cwp_substring_match"]) / 100   #Proportion of a string to be matched to a (usually larger) string for it to be considered essentially similar
        self.USE_CACHE = options["use_cache"]
        self.GRANULARITY = options["cwp_granularity"]            #splitting for matching of parents. 1 = split in two, 2 = split in three etc.
        self.PROXIMITY = options["cwp_proximity"]           #proximity of new words in title comparison which will result in infill words being included as well. 2 means 2-word 'gaps' of existing words between new words will be treated as 'new'
        self.END_PROXIMITY = options["cwp_end_proximity"]         # proximity measure to be used when infilling to the end of the title
        self.REMOVEWORDS = options["cwp_removewords"]
        self.SYNONYMS = options["cwp_synonyms"]
        self.USE_LEVEL_0 = options["cwp_level0_works"]

        if self.DEBUG: log.debug("%s: LOAD NEW TRACK", PLUGIN_NAME)
        if self.INFO: log.info("trackXmlNode: %s", trackXmlNode)
        # fix titles which include composer name
        composersort = dict.get(track_metadata,'composersort', [])
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
            title_split = title.split(': ',1)
            test = title_split[0]
            if test in composerlastnames:
                track_metadata['~cwp_title'] = title_split[1]
        # now process works
        track = album._new_tracks[-1]     # Jump through hoops to get track object!!
        workIds = dict.get(track_metadata,'musicbrainz_workid', [])
        if workIds:
            works = dict.get(track_metadata,'work', [])
            for workId in workIds:
                    # there may be >1 workid but this is not yet fully supported, so code below joins together the work names for multiple ids and attaches it to the first id
                    # this is based on the (reasonable) assumption that multiple "recording of"s will be children of the same parent work.
                if len(works)>1:
                    if self.WARNING: log.warning("%s: WARNING: More than one work for this recording (%s). Check that works are parts of the same higher work as only one parent will be followed up.", PLUGIN_NAME, track_metadata['title'])
                    track_metadata['~cwp_warning'] = "WARNING: More than one work for this recording. Check that works are parts of the same higher work as only one parent will be followed up."
                work = sorted(works)
                         ## until multi-works functionality added
                self.parts[workId]['name']= work
                partial = False
                if 'partial' in track_metadata['~performance_attributes']:               # treat the recording as work level 0 and the work of which it is a partial recording as work level 1
                    partial = True
                    parentId = workId
                    true_workId = workId
                    workId = track_metadata['musicbrainz_recordingid']
                    if isinstance(work, basestring):
                        self.parts[workId]['name'] =  work + ': (part)'
                    else:
                        works=[]
                        for w in work:
                            partwork = w + ': (part)'
                            works.append(partwork)
                        self.parts[workId]['name'] = works
                    self.works_cache[workId] = parentId
                    self.parts[workId]['parent'] = parentId
                    self.parts[parentId]['name'] = self.parts[parentId]['name'][0]
                    if workId not in self.work_listing[album]:
                        self.work_listing[album].append(workId)
                    if self.DEBUG: log.debug("%s: Id %s is PARTIAL RECORDING OF id: %s, name: %s", PLUGIN_NAME, workId, parentId, work)
                self.trackback[album][workId]['id'] = workId
                if 'meta' in self.trackback[album][workId]:
                    if (track,album) not in self.trackback[album][workId]['meta']:
                        self.trackback[album][workId]['meta'].append((track, album))
                else:
                    self.trackback[album][workId]['meta'] = [(track, album)]
                if self.DEBUG: log.debug("Trackback for recording of %s is %s. Partial = %s", work, self.trackback[album][workId], partial)
                if 'arrangers' in self.parts[workId]:
                    if self.DEBUG: log.debug("%s GETTING ARRANGERS FROM CACHE", PLUGIN_NAME)
                    self.set_arranger(album, self.parts[workId]['arrangers'],track_metadata)
                if workId in self.works_cache and self.USE_CACHE:
                    if self.DEBUG: log.debug("%s: GETTING WORK METADATA FROM CACHE", PLUGIN_NAME)             #debug
                    partId = workId
                    while partId in self.works_cache:
                        parentId = self.works_cache[partId]
                        partId = parentId
                    workId = partId
                if 'no_parent' in self.parts[workId]:
                    if self.parts[workId]['no_parent']:
                        self.top_works[(track, album)]['workId'] = workId
                        if album in self.top:
                            if workId not in self.top[album]:
                                self.top[album].append(workId)
                        else:
                            self.top[album] = [workId]
                if 'no_parent' not in self.parts[workId] or ('no_parent' in self.parts[workId] and not self.parts[workId]['no_parent']):
                    if partial and not self.USE_CACHE:
                        workId = true_workId                                          # workId will not have been updated if cache turned off
                    self.work_add_track(album, track, workId, 0)
                if album._requests == 0 and track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
                    self.process_album(album)
                break #plugin does not currently support multiple workIds. Works for multiple workIds are assumed to be children of the same parent and are concatenated.
        else:     # no work relation
            if self.WARNING: log.warning("%s: WARNING - no works for this track: \"%s\"", PLUGIN_NAME, title)
            self.append_tag(track_metadata,'~cwp_warning', 'No works for this track')
            self.publish_metadata(album, track)

    def work_add_track(self, album, track, workId, tries):
        if self.DEBUG: log.debug("%s: ADDING WORK TO LOOKUP QUEUE", PLUGIN_NAME)                   #debug
        self.album_add_request(album)
            # to change the _requests variable to indicate that there are pending requests for this item and delay picard from finalizing the album
        if self.DEBUG: log.debug("%s: Added lookup request. Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if self.works_queue.append(workId, (track, album)): # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            queryargs = {"inc": "work-rels+artist-rels"}
            if self.DEBUG: log.debug("%s: Initiating XML lookup for %s......", PLUGIN_NAME, workId)   #debug
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.work_process, workId, tries),
                                xml=True, priority=True, important=False,
                                queryargs=queryargs)
        else:                                                                      #debug
            if self.DEBUG: log.debug("%s: Work is already in queue: %s", PLUGIN_NAME, workId)      #debug

    def work_process(self, workId, tries, response, reply, error):
        if self.DEBUG: log.debug("%s: work_process. LOOKING UP WORK: %s", PLUGIN_NAME, workId)                     #debug
        if error:
            if self.WARNING: log.warning("%s: %r: Network error retrieving work record", PLUGIN_NAME, workId)
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                if self.DEBUG: log.debug("%s: Removed request after network error. Requests = %s", PLUGIN_NAME, album._requests)   #debug
                if tries < self.MAX_RETRIES:
                    if self.DEBUG: log.debug("REQUEUEING...")
                    self.work_add_track(album, track, workId, tries + 1)
                else:
                    if self.ERROR: log.error("%s: EXHAUSTED MAX RE-TRIES for XML lookup for track %s", PLUGIN_NAME, track)
                    track.metadata['~cwp_error'] = "ERROR: MISSING METADATA due to network errors. Re-try or fix manually."
                self.album_remove_request(album)
            return
        tuples = self.works_queue.remove(workId)
        for track, album in tuples:
            if workId not in self.work_listing[album]:
                self.work_listing[album].append(workId)
            if self.DEBUG: log.debug("%s Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if self.DEBUG: log.debug("RESPONSE = %s", response)
        if workId in self.parts:
            metaList = self.work_process_metadata(workId, tuples, response)
            parentList = metaList[0]
                # returns [parent id, parent name] or None if no parent found
            arrangers = metaList[1]
            if arrangers:
                self.parts[workId]['arrangers'] = arrangers
                for track, album in tuples:
                    tm = track.metadata
                    self.set_arranger(album, arrangers,tm)
            if parentList:
                parentId = parentList[0]
                parent = parentList[1]
                if parentId:
                    self.works_cache[workId] = parentId
                    self.parts[workId]['parent']= parentId
                    self.parts[parentId]['name'] = parent
                    for track, album in tuples:
                        self.work_add_track(album, track, parentId, 0)
                else:
                    self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                    self.top_works[(track, album)]['workId'] = workId
                    if workId not in self.top[album]:
                        self.top[album].append(workId)
                    if self.INFO: log.info("TOP[album]: %s", self.top[album])
            else:  #ERROR?
                self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                self.top_works[(track, album)]['workId'] = workId
                self.top[album].append(workId)
        for track, album in tuples:
            if album._requests == 1:                                  # Next remove will finalise album
                self.process_album(album)                       # so do the final album-level processing before we go!
            self.album_remove_request(album)
            if self.DEBUG: log.debug("%s: Removed request. Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if self.DEBUG: log.debug("%s: End of work_process for workid %s", PLUGIN_NAME, workid)

    def work_process_metadata(self, workId, tuples, response):
        if self.DEBUG: log.debug("%s: In work_process_metadata", PLUGIN_NAME)
        relationList = []
        if 'metadata' in response.children:
            if 'work' in response.metadata[0].children:
                if 'relation_list' in response.metadata[0].work[0].children:
                    if 'relation' in response.metadata[0].work[0].relation_list[0].children:
                        for relation_list_item in response.metadata[0].work[0].relation_list:
                            relationList.append(relation_list_item.relation)
                        return self.work_process_relations(relationList)
            else:
                if self.ERROR: log.error("%s: %r: MusicBrainz work xml result not in correct format - %s",
                          PLUGIN_NAME, workId, response)
                for track, album in tuples:
                    tm = track.metadata
                    self.append_tag(tm, '~cwp_error', 'MusicBrainz work xml result not in correct format for work id: ' + str(workId))
        return None

    def work_process_relations(self, relations):
        if self.DEBUG: log.debug("%s In work_process_relations. Relations--> %s", PLUGIN_NAME, relations)
        new_workIds = []
        new_works = []
        artists = []
        itemsFound = []
        for relation in relations:
            #if self.INFO: log.info("%s Relation--> %s", PLUGIN_NAME, relation)
            for rel in relation:
                if rel.attribs['type'] == 'parts':
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            new_workIds.append(rel.work[0].id)
                            new_works.append(rel.work[0].title[0].text)

                if rel.attribs['type'] == 'instrument arranger':
                    #if self.INFO: log.info("found INSTRUMENT ARRANGER")
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            name = rel.artist[0].name[0].text
                            sort_name = rel.artist[0].sort_name[0].text
                            instrument = rel.attribute_list[0].attribute[0].text
                            artist = (instrument, name, sort_name)
                            artists.append(artist)
                            #if self.DEBUG: log.debug("ARTISTS %s", artists)

                if rel.attribs['type'] == 'orchestrator':
                    #if self.INFO: log.info("found orchestrator")
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            name = rel.artist[0].name[0].text
                            sort_name = rel.artist[0].sort_name[0].text
                            artist = ('orchestrator', name, sort_name)
                            artists.append(artist)
                            #if self.DEBUG: log.debug("ARTISTS %s", artists)

        # just select one parent work to return (the longest named, as it is likely to be the lowest level)
        if new_workIds:
            if len(new_workIds) > 1:
                if new_works:
                    new_work = max(new_works)
                    i = new_works.index(new_work)
                    new_workId = new_workIds[i]
                else:
                    new_workId = new_workIds[0]     # in case work is not named for some reason
                    new_work = None
            else:
                new_workId = new_workIds[0]
                new_work = new_works[0]
        else:
            new_workId = None
            new_work = None
        workItems = (new_workId, new_work)
        itemsFound = [workItems, artists]
        return itemsFound

    def set_arranger(self, album, arrangerList, tm):
        orchestratorList = []
        for arranger in arrangerList:
            instrument = arranger[0]
            if instrument == 'orchestrator':
                orchestratorList.append(arranger)
                break
            name = arranger[1]
            sort_name = arranger[2]
            tm['~cwp_arranger'] = name + ' (' + instrument + ')'
            if album.tagger.config.setting['cea_arrangers']:
                newkey = '%s:%s' % ('arranger', instrument)
                tm.add_unique(newkey, name)
                tm['~cwp_arranger_sort'] = sort_name
                # next bit is needed as Picard does not currently write out arranger:instrument tag in the same way as performer:instrument -i.e. it is not included in main arranger tag         
                if 'arranger' in tm:
                    tm['arranger'] = tm['arranger'] + "; " + tm['~cwp_arranger']
                else:
                    tm['arranger'] = tm['~cwp_arranger']
        if orchestratorList:
            self.set_orchestrator(album, orchestratorList,tm)

    def set_orchestrator(self, album, orchestratorList,tm):
        if isinstance(tm['arranger'], basestring):
            arrangerList = tm['arranger'].split(';')
        else:
            arrangerList = tm['arranger']
        newList = arrangerList
        for orchestrator in orchestratorList:
            name = orchestrator[1]
            sort_name = orchestrator[2]
            if album.tagger.config.setting['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
            details = name + ' (orch.)'
            if '~cea_orchestrator' in tm:
                tm['~cea_orchestrator'] = tm['~cea_orchestrator'] + '; ' + details
            else:
                tm['~cea_orchestrator'] = details

            for index, arranger in enumerate(arrangerList):
                if name in arranger:
                    newList[index] = details
        tm['arranger'] = newList

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)


##################################################
# SECTION 2 - Organise tracks and works in album #
##################################################

    def process_album(self, album):
        if self.DEBUG: log.debug("%s: PROCESS ALBUM %s", PLUGIN_NAME, album)
        # populate the inverse hierarchy
        if self.INFO: log.info("%s: Cache: %s", PLUGIN_NAME, self.works_cache)
        if self.INFO: log.info("%s: Work listing %s", PLUGIN_NAME, self.work_listing)
        for workId in self.parts:
            if workId in self.work_listing[album]:
                topId = None
                if workId in self.works_cache:
                    parentId = self.works_cache[workId]
                    if self.DEBUG: log.debug("%s: create inverses: %s, %s", PLUGIN_NAME, workId, parentId)
                    if parentId in self.partof:
                        if workId not in self.partof[parentId]:
                            self.partof[parentId].append(workId)
                    else:
                        self.partof[parentId] = [workId]
                    if self.DEBUG: log.debug("%s: Partof: %s", PLUGIN_NAME, self.partof[parentId])
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:     # to handle case if album includes works already in cache from a different album
                            topId = parentId
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
        if self.INFO: log.info("%s: TOP: %s, \nALBUM: %s, \nTOP[ALBUM]: %s", PLUGIN_NAME, self.top, album, self.top[album])
        if len(self.top[album]) > 1:
            single_work_album = 0
        else:
            single_work_album = 1
        for topId in self.top[album]:
            self.create_trackback(album, topId)
            if self.INFO: log.info("Top id = %s, Name = %s", topId, self.parts[topId]['name'])
            if self.INFO: log.info("Trackback before levels: %s", self.trackback[album][topId])
            work_part_levels = self.level_calc(self.trackback[album][topId], height)
            if self.INFO: log.info("Trackback after levels: %s", self.trackback[album][topId])
            # determine the level which will be the principal 'work' level
            if work_part_levels >= 3:
                ref_level = work_part_levels - single_work_album
            else:
                ref_level = work_part_levels
            ref_level = min(3, ref_level)               # extended metadata scheme won't display more than 3 work levels
            ref_height = work_part_levels - ref_level
            top_info = {'levels': work_part_levels, 'id': topId, 'name': self.parts[topId]['name'], 'single': single_work_album}
            # set the metadata in sequence defined by the work structure
            answer = self.process_trackback(album, self.trackback[album][topId], ref_height, top_info)
            if answer:
                tracks = answer[1]['track']
                #if self.INFO: log.info("TRACKS: %s", tracks)
                work_part_levels = self.trackback[album][topId]['depth']
                for track in tracks:
                    track_meta = track[0]
                    tm = track_meta.metadata
                    title_work_levels = 0
                    if '~cwp_title_work_levels' in tm:
                        title_work_levels = int(tm['~cwp_title_work_levels'])
                    self.extend_metadata(top_info, track_meta, ref_height, title_work_levels)   # revise for new data
                    self.publish_metadata(album, track_meta)
                if self.DEBUG: log.debug("%s FINISHED TRACK PROCESSING FOR Top work id: %s", PLUGIN_NAME, topId)
        self.trackback[album].clear()

    def create_trackback(self, album, parentId):
        if self.DEBUG: log.debug("%s: Create trackback for %s", PLUGIN_NAME, parentId)
        if parentId in self.partof:
            for child in self.partof[parentId]:
                if child in self.partof:
                    child_trackback = self.create_trackback(album, child)
                    self.append_trackback(album, parentId, child_trackback)
                else:
                    self.append_trackback(album, parentId, self.trackback[album][child])
            return self.trackback[album][parentId]
        else:
            return self.trackback[album][parentId]

    def append_trackback(self, album, parentId, child):
        if parentId in self.trackback[album]:
            if 'children' in self.trackback[album][parentId]:
                if child not in self.trackback[album][parentId]['children']:
                    if self.DEBUG: log.debug("TRYING TO APPEND...")
                    self.trackback[album][parentId]['children'].append(child)
                    if self.DEBUG: log.debug("...PARENT %s - ADDED %s as child", self.parts[parentId]['name'], child)
                else:
                    if self.DEBUG: log.debug("Parent %s already has %s as child", parentId, child)
            else:
                self.trackback[album][parentId]['children'] = [child]
                if self.DEBUG: log.debug("Existing PARENT %s - ADDED %s as child", self.parts[parentId]['name'], child)
        else:
            self.trackback[album][parentId]['id'] = parentId
            self.trackback[album][parentId]['children'] = [child]
            if self.DEBUG: log.debug("New PARENT %s - ADDED %s as child", self.parts[parentId]['name'], child)
            if self.INFO: log.info("APPENDED TRACKBACK: %s", self.trackback[album][parentId])
        return self.trackback[album][parentId]

    def level_calc(self, trackback, height):
        if 'children' not in trackback:
            if self.INFO: log.info("Got to bottom")
            trackback['height'] = height
            trackback['depth'] = 0
            return 0
        else:
            trackback['height'] = height
            height += 1
            max_depth = 0
            for child in trackback['children']:
                if self.DEBUG: log.debug("CHILD: %s", child)
                depth = self.level_calc(child, height) + 1
                if self.DEBUG: log.debug("DEPTH: %s", depth)
                max_depth = max(depth, max_depth)
            trackback['depth'] = max_depth
            return max_depth

###########################################
# SECTION 3 - Process tracks within album #
###########################################

    def process_trackback(self, album_req, trackback, ref_height, top_info):
        if self.DEBUG: log.debug("%s: IN PROCESS_TRACKBACK. Trackback = %s", PLUGIN_NAME, trackback)
        tracks = collections.defaultdict(dict)
        process_now = False
        if 'meta' in trackback:
            for track, album in trackback['meta']:
                if album_req == album:
                    process_now = True
        if process_now or 'children' not in trackback:
            if 'meta' in trackback and 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                if self.DEBUG: log.debug("Processing level 0")
                depth = trackback['depth']
                height = trackback['height']
                workId = trackback['id']
                if self.INFO: log.info("WorkId %s", workId)
                if self.INFO: log.info("Work name %s", self.parts[workId]['name'])
                for track, album in trackback['meta']:
                    if album == album_req:
                        if self.INFO: log.info("Track: %s", track)
                        tm = track.metadata
                        if self.INFO: log.info("Track metadata = %s", tm)
                        tm['~cwp_workid_' + str(depth)] = workId
                        tm['~cwp_work_' + str(depth)] = self.parts[workId]['name']
                        tm['~cwp_part_levels'] = height
                        tm['~cwp_work_part_levels'] = top_info['levels']
                        tm['~cwp_workid_top'] = top_info['id']
                        tm['~cwp_work_top'] = top_info['name']
                        tm['~cwp_single_work_album'] = top_info['single']
                        if self.INFO: log.info("Track metadata = %s", tm)
                        if 'track' in tracks:
                            tracks['track'].append((track, height))
                        else:
                            tracks['track'] =[(track, height)]
                        if self.INFO: log.info("Tracks: %s", tracks)
                response = (workId, tracks)
                if self.DEBUG: log.debug("%s: LEAVING PROCESS_TRACKBACK", PLUGIN_NAME)
                if self.INFO: log.info("depth %s Response = %s", depth, response)
                return response
            else:
                return None
        else:
            if 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                depth = trackback['depth']
                height = trackback['height']
                parentId = trackback['id']
                parent = self.parts[parentId]['name']
                for child in trackback['children']:
                    if self.INFO: log.info("child trackback = %s", child)
                    answer = self.process_trackback(album_req, child, ref_height, top_info)
                    if answer:
                        workId = answer[0]
                        child_tracks = answer[1]['track']
                        for track in child_tracks:
                            track_meta = track[0]
                            track_height = track[1]
                            part_level = track_height - height
                            if self.DEBUG: log.debug("%s: Calling set metadata %s", PLUGIN_NAME, (part_level, workId, parentId, parent, track_meta))
                            self.set_metadata(part_level, workId, parentId, parent, track_meta)
                            if 'track' in tracks:
                                tracks['track'].append((track_meta, track_height))
                            else:
                                tracks['track'] =[(track_meta, track_height)]
                            tm = track_meta.metadata
                            title = tm['~cwp_title'] or tm['title']                            # ~cwp_title if composer had to be removed
                            if self.DEBUG: log.debug("TITLE: %s", title)
                            if 'title' in tracks:
                                tracks['title'].append(title)
                            else:
                                tracks['title']=[title]
                            work = tm['~cwp_work_0']
                            if 'work' in tracks:
                                tracks['work'].append(work)
                            else:
                                tracks['work']=[work]
                            if 'tracknumber' not in tm:
                                tm['tracknumber'] = 0
                            if 'tracknumber' in tracks:
                                tracks['tracknumber'].append(int(tm['tracknumber']))
                            else:
                                tracks['tracknumber']=[int(tm['tracknumber'])]
                self.derive_from_structure(top_info, tracks, height, depth, 'title')
                if self.USE_LEVEL_0:
                    self.derive_from_structure(top_info, tracks, height, depth, 'work')    #replace hierarchical works with those from work_0 (for consistency)
                
          
                if self.DEBUG: log.debug("Trackback result for %s = %s", parentId, tracks)
                response = parentId, tracks
                if self.DEBUG: log.debug("%s LEAVING PROCESS_TRACKBACK depth %s Response = %s", PLUGIN_NAME, depth, response)
                return response
            else:
                return None
        return response

    def derive_from_structure(self, top_info, tracks, height, depth, name_type):
        if 'track' in tracks:
            if self.DEBUG: log.debug("%s: Deriving info from structure", PLUGIN_NAME)
            if 'tracknumber' in tracks:
                sorted_tracknumbers = sorted(tracks['tracknumber'])
            else:
                sorted_tracknumbers = None
            if self.INFO: log.info("SORTED TRACKNUMBERS: %s", sorted_tracknumbers)
            common_len = 0
            common_subset = None
            if name_type in tracks:
                name_list = tracks[name_type]
                if self.DEBUG: log.debug("%s list %s", name_type, name_list)
                if len(name_list) == 1:                    # only one track in this work so try and extract using colons
                    track_height = tracks['track'][0][1]
                    if track_height - height >0:            # part_level
                        if name_type == 'title':
                            track = tracks['track'][0][0]
                            if self.DEBUG: log.debug("Single track work. Deriving directly from title text: %s", track)
                            tm = track.metadata
                            mb = tm['~cwp_work_0']
                            ti = name_list[0]
                            diff = self.diff_pair(mb, ti)
                            if diff:
                                common_subset = self.derive_from_title(track, diff)[0]
                        else:
                            common_subset = ""
                            common_len = 0
                    else:    
                        common_subset = name_list[0]
                    if self.INFO: log.info("%s is single-track work. common_subset is set to %s", tracks['track'][0][0], common_subset)
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
                            if self.INFO: log.info("Common subset from %ss at level %s, item name %s ..........", name_type, tracks['track'][0][1] - height, name)
                            if self.INFO: log.info("..........is %s", common_subset)
                            common_len = len(common_subset)

                if self.DEBUG: log.debug("checked for common sequence - length is %s", common_len)
            for i, track in enumerate(tracks['track']):
                track_meta = track[0]
                tm = track_meta.metadata
                part_level = track[1] - height
                if common_len > 0:
                    if self.INFO: log.info("Use %s info for track: %s", name_type, track_meta)
                    name = tracks[name_type][i]
                    
                    work = name[:common_len]
                    work = work.rstrip(":,.;- ")
                    removewords = self.REMOVEWORDS.split(',')
                    if self.DEBUG: log.debug("Removewords (in %s) = %s", name_type, removewords)
                    for prefix in removewords:
                        prefix2 = str(prefix).lower().rstrip()
                        if prefix2[0] != " ":
                            prefix2 = " " + prefix2
                        if self.DEBUG: log.debug("checking prefix %s", prefix2)
                        if work.lower().endswith(prefix2):
                            if len(prefix2) > 0:
                                work = work[:-len(prefix2)]
                                common_len = len(work)
                                work = work.rstrip(":,.;- ")
                    if self.INFO: log.info("work after prefix strip %s", work)
                    if self.DEBUG: log.debug("Prefixes checked")
                    meta_str = "_title" if name_type == 'title' else "_X0"
                    tm['~cwp' + meta_str + '_work_'+str(part_level)] = work
                    if part_level > 0 and name_type == "work":
                        if work == tm['~cwp' + meta_str + '_work_'+str(part_level - 1)]:
                            topId = top_info['id']
                            self.parts[topId]['X0_work_repeat'] = str(part_level)
                    if part_level == 1:
                        movt = name[common_len:].strip().lstrip(":,.;- ")
                        if self.INFO: log.info("%s - movt = %s", name_type, movt)
                        tm['~cwp' + meta_str + '_part_0'] = movt
                    if self.INFO: log.info("%s Work part_level = %s", name_type, part_level)
                    if name_type == 'title':
                        tm['~cwp' + meta_str + '_work_levels'] = depth
                        tm['~cwp' + meta_str + '_part_levels'] =part_level
                        if self.DEBUG: log.debug("Set new metadata for %s OK", name_type)
                # set movement number
                if name_type == 'title':                # so we only do it once
                    if part_level == 1:
                        if sorted_tracknumbers:
                            curr_num = tracks['tracknumber'][i]
                            posn = sorted_tracknumbers.index(curr_num) + 1
                            if self.INFO: log.info("posn %s", posn)
                        else:
                            posn = i + 1
                        tm['~cwp_movt_num'] = str(posn)



    def set_metadata(self, part_level, workId, parentId, parent, track):
        if self.DEBUG: log.debug("%s: SETTING METADATA FOR TRACK = %r, parent = %s, part_level = %s", PLUGIN_NAME, track, parent, part_level)                     #debug
        tm = track.metadata
        if parentId:
            if not isinstance(parent, basestring):
                parent = parent[0]
            tm['~cwp_workid_' + str(part_level)] = parentId
            tm['~cwp_work_' + str(part_level)] = parent
            work = self.parts[workId]['name']                                          # maybe more than one work name
            if self.DEBUG: log.debug("Set work name to: %s", work)
            works = []
            if isinstance(work, basestring):                                           # in case there is only one and it isn't in a list
                works.append(work)
            else:
                works = work
            stripped_works = []
            for work in works:
                strip = self.strip_parent_from_work(work, parent, part_level, True, parentId)
                stripped_works.append(strip[0])
                if self.INFO: log.info("Full parent: %s, Parent: %s", strip[1], parent)
                full_parent = strip[1]
                if full_parent != parent:
                    tm['~cwp_work_' + str(part_level)]= full_parent
                    self.parts[parentId]['name'] = full_parent
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:
                            tm['~cwp_work_top'] = full_parent
            tm['~cwp_part_' + str(part_level-1)]= stripped_works
            self.parts[workId]['stripped_name'] = stripped_works
            # if stripped_works == works:                          # no match found: nothing stripped




            #     self.pending_strip[(track)][parentId]['childId'] = workId
            #     self.pending_strip[(track)][parentId]['children'] = works
            #     self.pending_strip[(track)][parentId]['part_level'] = part_level - 1
            # if workId in self.pending_strip[(track)]:
            #     children = self.pending_strip[(track)][workId]['children']              # maybe more than one work name
            #     stripped_works = []
            #     for child in children:
            #         strip = self.strip_parent_from_work(child, parent, part_level, True)
            #         stripped_works.append(strip[0])
            #     child_level = self.pending_strip[(track)][workId]['part_level']
            #     tm['~cwp_part_' + str(child_level)] = stripped_works
            #     childId = self.pending_strip[(track)][workId]['childId']
            #     self.parts[childId]['stripped_name'] = stripped_works
        if self.DEBUG: log.debug("GOT TO END OF SET_METADATA")

    def derive_from_title(self, track, title):
        if self.INFO: log.info("%s: DERIVING METADATA FROM TITLE for track: %s", PLUGIN_NAME, track)
        tm = track.metadata
        movt = ""
        work = ""
        if '~cwp_part_levels' in tm:
            part_levels = int(tm['~cwp_part_levels'])
            if int(tm['~cwp_work_part_levels']) > 0:                          # we have a work with movements
                colons = title.count(":")
                if colons > 0:
                    title_split = title.split(': ',1)
                    title_rsplit = title.rsplit(': ',1)
                    if part_levels >= colons:
                        work = title_rsplit[0]
                        movt = title_rsplit[1]
                    else:
                        work = title_split[0]
                        movt = title_split[1]
                else:
                    movt = title
        if self.INFO: log.info("Work %s, Movt %s", work, movt)
        return (work, movt)

#################################################
# SECTION 4 - Extend work metadata using titles #
#################################################

    def extend_metadata(self, top_info, track, ref_height, depth):
        tm = track.metadata
        title_groupheading = None
        part_levels = int(tm['~cwp_part_levels'])
        topId = top_info['id']
        if self.USE_LEVEL_0 and 'X0_work_repeat' not in self.parts[topId]:                 #Only use work names based on level 0 text if it doesn't cause ambiguity
            if '~cwp_X0_part_0' in tm:
                tm['~cwp_part_0'] = tm['~cwp_X0_part_0']
            for level in range(1, part_levels + 1):
                if '~cwp_X0_work_' + str(level) in tm:
                    tm['~cwp_work_' + str(level)] = tm['~cwp_X0_work_' + str(level)]
        ## set up group heading and part
        if self.DEBUG: log.debug("%s: Extending metadata for track: %s, ref_height: %s, depth: %s", PLUGIN_NAME, track, ref_height, depth)
        if self.INFO: log.info("Metadata = %s", tm)
        if part_levels > 0:
            ref_level = part_levels - ref_height
            if ref_level == 1:
                groupheading = tm['~cwp_work_1']
                work = tm['~cwp_work_1']
                work_titles = tm['~cwp_title_work_1']
            elif ref_level == 2:
                groupheading = tm['~cwp_work_2'] + ":: " + tm['~cwp_part_1']
                work = tm['~cwp_work_2']
                work_titles = tm['~cwp_title_work_2']
            elif ref_level >= 3:
                groupheading = tm['~cwp_work_3'] + ":: " + tm['~cwp_part_2'] + ": " + tm['~cwp_part_1']
                work = tm['~cwp_work_3']
                work_titles = tm['~cwp_title_work_3']
            else:
                groupheading = None
                title_groupheading = None
            tm['~cwp_groupheading'] = groupheading
            
            tm['~cwp_work'] = work
            tm['~cwp_title_work'] = work_titles
        if '~cwp_part_0' in tm:
            part = tm ['~cwp_part_0']
            tm['~cwp_part'] = part
        else:
            part = tm['~cwp_work_0']
            tm['~cwp_part'] = part
        if part_levels == 0:
            groupheading = tm['~cwp_work_0']
            work = groupheading
        ## extend group heading from title metadata
        if self.DEBUG: log.debug("Set groupheading OK")
        if groupheading:
            if '~cwp_title_work_levels' in tm:
                title_depth = int(tm['~cwp_title_work_levels'])
                if self.INFO: log.info("Title_depth: %s", title_depth)
                diff_work = []
                diff_part = []
                tw_str_lower = 'x' # to avoid errors, reset before used
                for d in range(1,title_depth+1):
                    tw_str = '~cwp_title_work_'+str(d)
                    if self.INFO: log.info("TW_STR = %s", tw_str)
                    if tw_str in tm:
                        title_work = tm[tw_str]
                        work = tm['~cwp_work_'+str(d)]
                        diff_work.append(self.diff_pair(work, title_work))
                        if d > 1 and tw_str_lower in tm:
                            title_part = self.strip_parent_from_work(tm[tw_str_lower],tm[tw_str],0,False)[0].strip()
                            tm['~cwp_title_part_'+str(d-1)] = title_part
                            part_n = tm['~cwp_part_' + str(d-1)]
                            diff_part.append(self.diff_pair(part_n,title_part))
                    tw_str_lower = tw_str
                if self.INFO: log.info("diff list for works: %s", diff_work)
                if self.INFO: log.info("diff list for parts: %s", diff_part)
                if not diff_work or len(diff_work) == 0:
                    if part_levels > 0:
                        ext_groupheading = groupheading
                else:
                    if self.DEBUG: log.debug("Now calc extended groupheading...")
                    if self.INFO: log.info("depth = %s, ref_level = %s", depth, ref_level)
                    if part_levels > 0 and depth >= 1:
                        addn_work = []
                        addn_part = []
                        for stripped_work in diff_work:
                            if stripped_work:
                                if self.INFO: log.info("Stripped work = %s", stripped_work)
                                addn_work.append(" {" + stripped_work + "}")
                            else:
                                addn_work.append("")
                        for stripped_part in diff_part:
                            if stripped_part:
                                if self.INFO: log.info("Stripped part = %s", stripped_part)
                                addn_part.append(" {" + stripped_part + "}")
                            else:
                                addn_part.append("")
                        if ref_level == 1:
                            ext_groupheading = tm['~cwp_work_1'] + addn_work[0]
                            title_groupheading = tm['~cwp_title_work_1']
                            ext_work = tm['~cwp_work_1'] + addn_work[0]
                        elif ref_level == 2:
                            ext_groupheading = tm['~cwp_work_2'] + addn_work[1] + ":: " + tm['~cwp_part_1'] + addn_part[0]
                            title_groupheading = tm['~cwp_title_work_2'] + ":: " + tm['~cwp_title_part_1']
                            if self.DEBUG: log.debug("set title_groupheading at ref-level =2 as %s", title_groupheading)
                            if self.DEBUG: log.debug("based on title_work 2 = %s and title_part_1 = %s", tm['~cwp_title_work_2'], tm['~cwp_title_part_1'])
                            ext_work = tm['~cwp_work_2'] + addn_work[1]
                        elif ref_level >= 3:
                            ext_groupheading = tm['~cwp_work_3'] + addn_work[2] + ":: " + tm['~cwp_part_2'] + addn_part[1] + ": " + tm['~cwp_part_1'] + addn_part[0]
                            title_groupheading = tm['~cwp_title_work_3'] + ":: " + tm['~cwp_title_part_2'] + ": " + tm['~cwp_title_part_1']
                            ext_work = tm['~cwp_work_3'] + addn_work[2]
                    else:
                        ext_groupheading = groupheading           # title will be in part
                        ext_work = work
                    if self.DEBUG: log.debug("....groupheading done")
            else:
                ext_groupheading = groupheading
                title_groupheading = None
                ext_work = work
            if ext_groupheading:
                if self.INFO: log.info("EXTENDED GROUPHEADING: %s", ext_groupheading)
                tm['~cwp_extended_groupheading'] = ext_groupheading
                tm['~cwp_extended_work'] = ext_work
            if self.INFO: log.info("title_groupheading = %s", title_groupheading)
            if title_groupheading:
                tm['~cwp_title_groupheading'] = title_groupheading
        ## extend part from title metadata
        if self.DEBUG: log.debug("%s: Now extend part...(part = %s)", PLUGIN_NAME, part)
        if part:
            if '~cwp_title_part_0' in tm:
                movement = tm['~cwp_title_part_0']
            else:
                movement = tm['~cwp_title'] or tm['title']
            diff = self.diff_pair(part, movement)
            if self.INFO: log.info("DIFF PART - MOVT. ti =%s", diff)
            if diff:
                if '~cwp_work_1' in tm:
                    diff2 = self.diff_pair(tm['~cwp_work_1'], diff)
                    if diff2:
                        no_diff = False
                    else:
                        no_diff = True
                else:
                    no_diff = False
            else:
                no_diff = True
            if no_diff:
                if part_levels > 0:
                    tm['~cwp_extended_part'] = part
                else:
                    tm['~cwp_extended_part'] = tm['~cwp_work_0']
                    if tm['~cwp_extended_groupheading']:
                        del tm['~cwp_extended_groupheading']
            else:
                if part_levels > 0:
                    stripped_movt = diff2.strip()
                    tm['~cwp_extended_part'] = part + " {" + stripped_movt + "}"
                else:
                    tm['~cwp_extended_part'] = movement           # title will be in part
        if self.DEBUG: log.debug("....done")
        return None

    def diff_pair(self, mb_item, title_item):
        if self.DEBUG: log.debug("%s: Inside DIFF_PAIR", PLUGIN_NAME)
        mb = mb_item.strip()
        if self.INFO: log.info("mb = %s", mb)
        if not mb:
            return None
        ti = title_item.strip(" \"':;-.,")
        if self.INFO: log.info("ti = %s", ti)
        if not ti:
            return None
        p1 = re.compile(r'^\W*\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b[\s|\.|:|,|;]', re.IGNORECASE)  # Matches Roman numerals with punctuation
        p2 = re.compile(r'^\W*\d+[.):-]')             # Matches positive integers with punctuation
        # remove certain words from the comparison
        removewords = self.REMOVEWORDS.split(',')
        if self.INFO: log.info("Removewords = %s", removewords)
        #remove numbers, roman numerals, part etc and punctuation from the start
        try:
            if self.DEBUG: log.debug("checking prefixes")
            for i in range(0,5):                                                # in case of multiple levels
                mb = p2.sub('',p1.sub('',mb)).strip()
                ti = p2.sub('',p1.sub('',ti)).strip()
                for prefix in removewords:
                    prefix2 = str(prefix).lower().lstrip()
                    if self.DEBUG: log.debug("checking prefix %s", prefix2)
                    if mb.lower().startswith(prefix2):
                        mb = mb[len(prefix2):]
                    if ti.lower().startswith(prefix2):
                        ti = ti[len(prefix2):]
                mb = mb.strip()
                ti = ti.strip()
                if self.INFO: log.info("pairs after prefix strip iteration %s. mb = %s, ti = %s", i, mb, ti)
            if self.DEBUG: log.debug("Prefixes checked")
        except:
            if self.ERROR: log.error("Execution error in plugin %s: Error: %s, Line No.: %s", PLUGIN_NAME, sys.exc_info()[0], sys.exc_traceback.tb_lineno)
        # replace synonyms
        strsyns = self.SYNONYMS.split('/')
        synonyms = []
        for syn in strsyns:
            tup = syn.strip(' ()').split(',')
            for i, t in enumerate(tup):
                tup[i] = t.strip("' ")
            tup = tuple(tup)
            synonyms.append(tup)
        if self.INFO: log.info("Synonyms: %s", synonyms)
        ti_test = ti
        mb_test = mb
        try:
            for key, equiv in synonyms:
                key = ' ' + key + ' '
                equiv = ' ' + equiv + ' '
                if self.INFO: log.info("key %s, equiv %s", key, equiv)
                mb_test = mb_test.replace(key, equiv)
                ti_test = ti_test.replace(key, equiv)
                if self.DEBUG: log.debug("Replaced synonyms mb = %s, ti = %s", mb_test, ti_test)
        except:
            if self.ERROR: log.error("Execution error in plugin %s: Error: %s, Line No.: %s", PLUGIN_NAME, sys.exc_info()[0], sys.exc_traceback.tb_lineno)
        # check if the title item is wholly part of the mb item
        try:
            if self.DEBUG: log.debug("Testing if ti in mb. ti = %s, mb = %s", ti_test, mb_test)
            nopunc_ti = self.boil(ti_test)
            if self.INFO: log.info("nopunc_ti =%s", nopunc_ti)
            nopunc_mb = self.boil(mb_test)
            if self.INFO: log.info("nopunc_mb =%s", nopunc_mb)
            ti_len = len(nopunc_ti)
            if self.INFO: log.info("ti len %s", ti_len)
            sub_len = int(ti_len)
            if self.INFO: log.info("sub len %s", sub_len)
            if self.DEBUG: log.debug("Initial test. nopunc_mb = %s, nopunc_ti = %s, sub_len = %s", nopunc_mb, nopunc_ti, sub_len)
            if self.test_sub(nopunc_mb, nopunc_ti, sub_len, 0):
                return None
        except:
            log.error("Execution error in plugin %s: Error: %s, Line No.: %s", PLUGIN_NAME, sys.exc_info()[0], sys.exc_traceback.tb_lineno)
        # try and strip the canonical item from the title item (only a full strip affects the outcome)
        if len(nopunc_mb) > 0:
            ti_new = self.strip_parent_from_work(ti_test,mb_test,0,False)[0]
            if ti_new == ti_test:
                mb_list = re.split(r';\s|:\s|\.\s|\-\s',mb_test,self.GRANULARITY)
                if self.DEBUG: log.debug("mb_list = %s", mb_list)
                if mb_list:
                    for mb_bit in mb_list:
                        ti_new = self.strip_parent_from_work(ti_new,mb_bit,0,False)[0]
                        if self.DEBUG: log.debug("MB_BIT: %s, TI_NEW: %s", mb_bit, ti_new)
            else:
                if len(ti_new) > 0:
                    return ti_new
                else:
                    return None
            if len(ti_new) == 0:
                return None
        # return any significant new words in the title
        words = 0
        nonWords = ["a", "the", "in", "on", "at", "of", "after", "and", "de", "d'un", "d'une", "la", "le"]
        if self.DEBUG: log.debug("Check before splitting: mb = %s, ti = %s", mb_test, ti_test)
        ti_list = re.split(' ', ti)
        ti_test_list = re.split(' ', ti_test)
        if len(ti_list) != len(ti_test_list):
            ti_list = ti_test_list                               # should not be necessary, but just in case to avoid index errors (only difference should be synonyms)
        mb_list2 = re.split(' ', mb_test)
        for index, mb_bit2 in enumerate(mb_list2):
            if self.INFO: log.info("mb_bit2 %s, boiled bit2: %s, index: %s", mb_bit2, self.boil(mb_bit2), index)
            mb_list2[index] = self.boil(mb_bit2)
            if self.INFO: log.info("mb_list2[%s] = %s", index, mb_list2[index])
        ti_new = []
        ti_comp_list = []
        ti_rich_list = []
        i=0
        for i, ti_bit in enumerate(ti_list):
            ti_bit_test = ti_test_list[i]
            if self.INFO: log.info("i = %s, ti_bit = %s", i, ti_bit)
            ti_rich_list.append((ti_bit, True))                   # Boolean to indicate whether ti_bit is a new word
            if self.INFO: log.info("ti_bit %s", ti_bit)
            if self.boil(ti_bit_test) in mb_list2:
                words+=1
                ti_rich_list[i] = (ti_bit, False)
            else:
                if ti_bit.lower() not in nonWords:
                    ti_comp_list.append(ti_bit)
        if self.INFO: log.info("words %s", words)
        if self.INFO: log.info("ti_comp_list = %s", ti_comp_list)
        if self.INFO: log.info("ti_rich_list before removing singletons = %s. length = %s", ti_rich_list, len(ti_rich_list))
        s = 0
        for  i, (t, n) in enumerate(ti_rich_list):
            if n:
                s += 1
                index = i
                change = t
        if s == 1:
            if 0 < index < len(ti_rich_list) - 1:
                ti_rich_list[index] = (change, False)    # ignore singleton new words in middle of title
                s = 0
        if self.DEBUG: log.debug("ti_rich_list before gapping = %s. length = %s", ti_rich_list, len(ti_rich_list))
        if s > 0:
            p = self.PROXIMITY
            d = self.PROXIMITY - self.END_PROXIMITY
            for i, (ti_bit, new) in enumerate(ti_rich_list):
                if not new:
                    if self.DEBUG: log.debug("%s not new. p = %s", ti_bit, p)
                    if p > 0:
                        for j in range(0,p+1):
                            if self.DEBUG: log.debug("i = %s, j = %s", i, j)
                            if i+j < len(ti_rich_list):
                                if ti_rich_list[i+j][1]:
                                    if self.DEBUG: log.debug("Set to true..")
                                    ti_rich_list[i]= (ti_bit, True)
                                    if self.DEBUG: log.debug("...set OK")
                            else:
                                if j <= p - d:
                                    ti_rich_list[i]= (ti_bit, True)
                else:
                    p = self.PROXIMITY
                if not ti_rich_list[i][1]:
                    p -= 1
        if self.DEBUG: log.debug("ti_rich_list after gapping = %s", ti_rich_list)
        nothing_new = True
        for (ti_bit, new) in ti_rich_list:
            if new:
                nothing_new = False
                new_prev = True
                break
        if nothing_new:
            return None
        else:
            for (ti_bit, new) in ti_rich_list:
                if self.DEBUG: log.debug("Create new for %s?", ti_bit)
                if new:
                    if self.DEBUG: log.debug("Yes for %s", ti_bit)
                    ti_new.append(ti_bit)
                    if self.DEBUG: log.debug("appended %s. ti_new is now %s", ti_bit, ti_new)
                else:
                    if self.DEBUG: log.debug("Not for %s", ti_bit)
                    if new != new_prev:
                        ti_new.append('...')
                new_prev = new
        if ti_new:
            if self.INFO: log.info("ti_new %s", ti_new)
            ti = ' '.join(ti_new)
            if self.INFO: log.info("New text from title = %s", ti)
        else:
            if self.INFO: log.info("New text empty")
            return None
        # see if there is any significant difference between the strings
        if ti:
            nopunc_ti = self.boil(ti)
            nopunc_mb = self.boil(mb)
            ti_len = len(nopunc_ti)
            sub_len = ti_len * self.SUBSTRING_MATCH
            if self.DEBUG: log.debug("test sub....")
            # if self.test_sub(nopunc_mb, nopunc_ti, sub_len, 0):   # is there a substring of ti of length at least sub_len in mb?
            #     return None                                         # in which case treat it as essentially the same
            lcs = longest_common_substring(nopunc_mb, nopunc_ti)
            if self.INFO: log.info("Longest common substring is: %s. Sub_len is %s", lcs, sub_len)
            if len(lcs) >= sub_len:
                return None
            if self.DEBUG: log.debug("...done, ti =%s", ti)
        # remove duplicate successive words (and remove first word of title item if it duplicates last word of mb item)
        if ti:
            ti_list_new = re.split(' ', ti)
            ti_bit_prev = None
            for i, ti_bit in enumerate(ti_list_new):
                if ti_bit != "...":

                    if i > 1:
                        if self.boil(ti_bit) == self.boil(ti_bit_prev):
                            ti_bit_prev = ti_list_new[i]
                            dup = ti_list_new.pop(i)
                            if self.DEBUG: log.debug("...removed dup %s", dup)
                        else:
                            ti_bit_prev = ti_list_new[i]
                    else:
                        ti_bit_prev = ti_list_new[i]

            if self.INFO: log.info("1st word of ti = %s. Last word of mb = %s", ti_list_new[0], mb_list2[-1])
            if ti_list_new:
                if self.boil(ti_list_new[0]) == mb_list2[-1]:
                    if self.DEBUG: log.debug("Removing 1st word from ti...")
                    first = ti_list_new.pop(0)
                    if self.DEBUG: log.debug("...removed %s", first)
            else:
                return None
            if ti_list_new:
                if self.DEBUG: log.debug("rejoin list %s", ti_list_new)
                ti = ' '.join(ti_list_new)
            else:
                return None
        # remove excess brackets and punctuation
        if ti:
            ti = ti.strip("!&.-:;, ")
            ti = ti.lstrip("\"\' ")
            if self.DEBUG: log.debug("stripped punc ok. ti = %s", ti)
            if ti:
                if ti.count("\"") == 1:
                    ti = ti.strip("\"")
                if ti.count("\'") == 1:
                    ti = ti.strip("\'")
                if "(" in ti and ")" not in ti:
                    ti = ti.replace("(", "")
                if ")" in ti and "(" not in ti:
                    ti = ti.replace(")", "")
            if ti:
                match_chars = [("(",")"),("[","]"),("{","}")]
                last = len(ti) - 1
                for char_pair in match_chars:
                    if char_pair[0] == ti[0] and char_pair[1] == ti[last]:
                        ti = ti.lstrip(char_pair[0]).rstrip(char_pair[1])
        if self.DEBUG: log.debug("DIFF is returning ti = %s", ti)
        if ti and len(ti) > 0:
            return ti
        else:
            return None

    def test_sub(self, strA, strB, sub_len, depth):
        if strA.count(strB) > 0:
            if self.INFO: log.info("FOUND: %s", strB)
            return strB
        else:
            if depth < 16:     #to prevent excessive recursion, which can cause Picard to hang
                depth += 1
                if len(strB) <= sub_len:
                    return None
                strB1 = strB[1:]
                test = self.test_sub(strA, strB1, sub_len, depth)
                if not test:
                    strB2 = strB[:-1]
                    return self.test_sub(strA, strB2, sub_len, depth)
                else:
                    return test
            else:
                return None

##########################################################
# SECTION 5- Write metadata to tags according to options #
##########################################################

    def publish_metadata(self, album, track):
        if self.DEBUG: log.debug("%s: IN PUBLISH METADATA for %s", PLUGIN_NAME, track)
        options = album.tagger.config.setting
        tm = track.metadata
        tm['~cwp_version'] = PLUGIN_VERSION
        if self.DEBUG: log.debug("Check options")
        if options["cwp_titles"]:
            if self.DEBUG: log.debug("titles")
            part = tm['~cwp_title_part_0'] or tm['~cwp_title'] or tm['title']
            groupheading = tm['~cwp_title_groupheading'] or ""                  # for multi-level work display
            work = tm['~cwp_title_work'] or ""                                  # for single-level work display
        elif options["cwp_works"]:
            if self.DEBUG: log.debug("works")
            part = tm['~cwp_part']
            groupheading = tm['~cwp_groupheading'] or ""
            work = tm['~cwp_work'] or ""
        elif options["cwp_extended"]:
            if self.DEBUG: log.debug("extended")
            part = tm['~cwp_extended_part']
            groupheading = tm['~cwp_extended_groupheading'] or ""
            work = tm['~cwp_extended_work'] or ""
        if self.DEBUG: log.debug("Done options")
        p1 = re.compile(r'^\W*\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b[\s|\.|:|,|;]', re.IGNORECASE)  # Matches Roman numerals with punctuation
        p2 = re.compile(r'^\W*\d+[.):-]')             # Matches positive integers with punctuation
        movt = part
        for _ in range(0,5):                                                # in case of multiple levels
            movt = p2.sub('',p1.sub('',movt)).strip()
        if self.DEBUG: log.debug("Done movt")
        movt_inc_tags = options["cwp_movt_tag_inc"].split(",")
        movt_inc_tags = [x.strip(' ') for x in movt_inc_tags]
        movt_exc_tags = options["cwp_movt_tag_exc"].split(",")
        movt_exc_tags = [x.strip(' ') for x in movt_exc_tags]
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

        if self.DEBUG: log.debug("Done splits. gh_tags: %s, work_tags: %s, movt_inc_tags: %s, movt_exc_tags: %s, movt_no_tags: %s", gh_tags, work_tags, movt_inc_tags, movt_exc_tags, movt_no_tags)

        for tag in gh_tags + work_tags + movt_inc_tags + movt_exc_tags + movt_no_tags:
            tm[tag] = ""
        for tag in gh_tags:
            if tag in movt_inc_tags + movt_exc_tags + movt_no_tags:
                self.append_tag(tm, tag, groupheading, gh_sep)
            else:
                self.append_tag(tm, tag, groupheading)
        for tag in work_tags:
            if tag in movt_inc_tags + movt_exc_tags + movt_no_tags:
                self.append_tag(tm, tag, work, work_sep)
            else:
                self.append_tag(tm, tag, work)
            if '~cwp_part_levels' in tm and int(tm['~cwp_part_levels'])>0:
                self.append_tag(tm,'show work movement','1') #for iTunes
        for tag in top_tags:
            tm[tag] = tm['~cwp_work_top'] or ""
        for tag in movt_inc_tags:
            self.append_tag(tm, tag, part)
        for tag in  movt_no_tags:
            if tag in movt_inc_tags + movt_exc_tags:
                self.append_tag(tm, tag, tm['~cwp_movt_num'], movt_no_sep)
            else:
                self.append_tag(tm, tag, tm['~cwp_movt_num'])
        for tag in movt_exc_tags:
            self.append_tag(tm, tag, movt)

        if self.DEBUG: log.debug("Published metadata for %s", track)
        if options['cwp_options_tag'] != "":
            self.cwp_options = collections.defaultdict(lambda: collections.defaultdict(dict))
            if options['cwp_titles']:
                self.cwp_options['Classical Extras']['Works options']['Style'] = 'Titles'
            else:
                if options['cwp_works']:
                    self.cwp_options['Classical Extras']['Works options']['Style'] = 'Works'
                else:
                    self.cwp_options['Classical Extras']['Works options']['Style'] = 'Extended'
                self.cwp_options['Classical Extras']['Works options']['Work source'] = 'Hierarchy' if options['cwp_hierarchical_works'] \
                    else 'Level_0'
            self.cwp_options['Classical Extras']['Works options']['movement tag inc num'] = options['cwp_movt_tag_inc']
            self.cwp_options['Classical Extras']['Works options']['movement tag exc num'] = options['cwp_movt_tag_exc']
            self.cwp_options['Classical Extras']['Works options']['movement num tag'] = options['cwp_movt_no_tag']
            self.cwp_options['Classical Extras']['Works options']['multi-level work tag'] = options['cwp_work_tag_multi']
            self.cwp_options['Classical Extras']['Works options']['single level work tag'] = options['cwp_work_tag_single']
            self.cwp_options['Classical Extras']['Works options']['top level work tag'] = options['cwp_top_tag']
            self.cwp_options['Classical Extras']['Works options']['in-string proximity trigger'] = options['cwp_proximity']
            self.cwp_options['Classical Extras']['Works options']['end-string proximity trigger'] = options['cwp_end_proximity']
            self.cwp_options['Classical Extras']['Works options']['work-splitting'] = options['cwp_granularity']
            self.cwp_options['Classical Extras']['Works options']['similarity threshold'] = options['cwp_substring_match']
            self.cwp_options['Classical Extras']['Works options']['ignore prefixes'] = options['cwp_removewords']
            self.cwp_options['Classical Extras']['Works options']['synonyms'] = options['cwp_synonyms']
            if self.INFO: log.info("Options %s", self.cwp_options)
            if options['ce_version_tag'] and options['ce_version_tag'] != "":
                self.append_tag(tm, options['ce_version_tag'], str('Version ' + tm['~cwp_version'] + ' of Classical Extras'))
            if options['cwp_options_tag'] and options['cwp_options_tag'] != "":
                self.append_tag(tm, options['cwp_options_tag'] + ':workparts_options', json.loads(json.dumps(self.cwp_options)))
        if self.ERROR and "~cwp_error" in tm:
            self.append_tag(tm, '001_ERRORS', tm['~cwp_error'])
        if self.WARNING and "~cwp_warning" in tm:
            self.append_tag(tm, '002_WARNINGS', tm['~cwp_warning'])

    def append_tag(self, tm, tag, source, sep = None):
        if self.DEBUG: log.debug("In append_tag. tag = %s, source = %s, sep =%s", tag, source, sep)
        if sep:
            if source and source != "":
                source = source + sep 
        if tag in tm:
            if self.INFO: log.info("Existing tag (%s) to be updated: %s", tag, tm[tag])
            if source not in tm[tag]:
                if isinstance(tm[tag], basestring):
                    if self.DEBUG: log.debug("tm[tag]: %s, separator = %s", tm[tag], sep)
                    newtag = [tm[tag], source]
                else:  
                    newtag = tm[tag].append(source)
                if sep:
                    tm[tag] = "".join(newtag)
                else:
                    tm[tag] = newtag
            if self.INFO: log.info("Updated tag (%s) is: %s", tag, tm[tag])
        else:
            if tag and tag != "":              
                tm[tag] = [source]
                if self.INFO: log.info("Newly created (%s) tag is: %s", tag, tm[tag])


################################################
# SECTION 6 - Common string handling functions #
################################################

    def strip_parent_from_work(self, work, parent, part_level, extend, parentId=None):
        #extend=True is used to find "full_parent" names and also (with parentId) to trigger recursion if unable to strip parent name from work
        #extend=False is used when this routine is called for other purposes than strict work: parent relationships
        if self.DEBUG: log.debug("%s: STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES", PLUGIN_NAME)
        full_parent = parent
        clean_parent = re.sub("(?u)\W",' ',parent)                  # replace any punctuation followed by a space, with a space (to remove any inconsistent punctuation) - (?u) specifies the re.UNICODE flag in sub
        pattern_parent = re.sub("\s","\W{0,2}", clean_parent)         # now allow the spaces to be filled with up to 2 non-letters
        if extend:
            pattern_parent = "(.*\s|^)(\W*"+pattern_parent+"\w*)(\W*\s)(.*)"
        else:
            pattern_parent = "(.*\s|^)(\W*"+pattern_parent+"w*\W?)(.*)"
        if self.INFO: log.info("Pattern parent: %s, Work: %s", pattern_parent, work)
        p = re.compile(pattern_parent, re.IGNORECASE|re.UNICODE)
        m = p.search(work)
        if m:
            if self.DEBUG: log.debug("Matched...")                                           #debug
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
            if m.group(3) != ": " and extend:            # may not have a full work name in the parent (missing op. no. etc.)
                if work.count(":") >= part_level:                  # no. of colons is consistent with "work: part" structure
                    split_work = work.split(': ',1)
                    stripped_work = split_work[1]
                    full_parent = split_work[0]
                    if len(full_parent) < len(parent):              # don't shorten parent names! (in case colon is mis-placed)
                        full_parent = parent
                        stripped_work = m.group(4)
        else:
            if self.DEBUG: log.debug("No match...")                                          #debug
            
            if extend and parentId and parentId in self.works_cache:
                if self.DEBUG: log.debug("Looking for match at next level up")
                grandparentId = self.works_cache[parentId]
                grandparent = self.parts[grandparentId]['name']
                stripped_work = self.strip_parent_from_work(work, grandparent, part_level, True, grandparentId)[0]

            else:
                stripped_work = work

        if self.INFO: log.info("Work: %s", work)                                             #debug
        if self.INFO: log.info("Stripped work: %s", stripped_work)                           #debug
        return (stripped_work, full_parent)

    # Remove punctuation, spaces, capitals and accents for string comprisona
    def boil(self, s):
        if self.DEBUG: log.debug("boiling %s", s)
        if isinstance(s, str):
            s = s.decode('unicode_escape')
        s = s.replace('sch','sh').replace(u'\xdfe', 'ss').replace('sz', 'ss').replace(u'\u0153','oe').replace('oe', 'o').replace('ue', 'u').replace('ae', 'a')
        punc = re.compile(r'\W*')
        s = ''.join(c for c in ud.normalize('NFD', s) if ud.category(c) != 'Mn')
        return punc.sub('',s).strip().lower().rstrip("s'")

    # Remove certain keywords
    def remove_words(self, query, stopwords):
        if self.DEBUG: log.debug("INSIDE REMOVE_WORDS")
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

    # Note - for the purposes of Options, the "Alternative Artists" and "Extra Artists" are combined (and the prefix caa used)

    options = [
        BoolOption("setting", "classical_work_parts", True),
        BoolOption("setting", "classical_extra_artists", True),
        IntOption("setting", "cwp_retries", 6),
        TextOption("setting", "cea_orchestras", "orchestra, philharmonic, philharmonica, philharmoniker, musicians, academy, symphony, orkester"),
        TextOption("setting", "cea_choirs", "choir, choir vocals, chorus, singers, domchors, domspatzen, koor"),
        TextOption("setting", "cea_groups", "ensemble, band, group, trio, quartet, quintet, sextet, septet, octet, chamber, consort, players, les , the "),
        BoolOption("setting", "use_cache", True),
        IntOption("setting", "cwp_proximity", 2),
        IntOption("setting", "cwp_end_proximity", 1),
        IntOption("setting", "cwp_granularity", 1),
        IntOption("setting", "cwp_substring_match", 66),
        TextOption("setting", "cwp_removewords", " part, act, scene, movement, movt, no., no , n., n , nr., nr , book , the , a , la , le , un , une , el , il , (part)"),
        TextOption("setting", "cwp_synonyms", "(1, one) / (2, two) / (3, three) / (&, and)"),
        
        BoolOption("setting", "cwp_titles", False),
        BoolOption("setting", "cwp_works", False),
        BoolOption("setting", "cwp_extended", True),
        BoolOption("setting", "cwp_hierarchical_works", False),
        BoolOption("setting", "cwp_level0_works", True),
        TextOption("setting", "cwp_movt_tag_inc", "part"),
        TextOption("setting", "cwp_movt_tag_exc", "movement"),
        TextOption("setting", "cwp_movt_no_tag", "movement_no"),
        TextOption("setting", "cwp_multi_work_sep", ": "),
        TextOption("setting", "cwp_single_work_sep", ": "),
        TextOption("setting", "cwp_movt_no_sep", ". "),

        TextOption("setting", "cwp_work_tag_multi", "groupheading"),
        TextOption("setting", "cwp_work_tag_single", "grouping"),
        TextOption("setting", "cwp_top_tag", "top_work"),

        BoolOption("setting", "cea_composer_album", True),

        TextOption("setting", "cea_blank_tag", "artist, artistsort"),
        TextOption("setting", "cea_blank_tag_2", "performer:orchestra, performer:choir, performer:choir vocals"),

        TextOption("setting", "cea_source_1", "album_soloists"),
        TextOption("setting", "cea_tag_1", "artist, artists"),
        BoolOption("setting", "cea_cond_1", True),

        TextOption("setting", "cea_source_2", "album_conductors"),
        TextOption("setting", "cea_tag_2", "artist, artists"),
        BoolOption("setting", "cea_cond_2", True),

        TextOption("setting", "cea_source_3", "album_ensembles"),
        TextOption("setting", "cea_tag_3", "artist, artists"),
        BoolOption("setting", "cea_cond_3", True),

        TextOption("setting", "cea_source_4", "soloists"),
        TextOption("setting", "cea_tag_4", "artist, artists, soloists, trackartist"),
        BoolOption("setting", "cea_cond_4", True),

        TextOption("setting", "cea_source_5", "conductors"),
        TextOption("setting", "cea_tag_5", "artist, artists"),
        BoolOption("setting", "cea_cond_5", True),

        TextOption("setting", "cea_source_6", "ensembles"),
        TextOption("setting", "cea_tag_6", "artist, artists, ensembles"),
        BoolOption("setting", "cea_cond_6", True),

        TextOption("setting", "cea_source_7", "album_composers"),
        TextOption("setting", "cea_tag_7", "artist, artists"),
        BoolOption("setting", "cea_cond_7", True),

        TextOption("setting", "cea_source_8", "ensemble_names"),
        TextOption("setting", "cea_tag_8", "band"),
        BoolOption("setting", "cea_cond_8", False),

        TextOption("setting", "cea_source_9", "composers"),
        TextOption("setting", "cea_tag_9", "artist, artists"),
        BoolOption("setting", "cea_cond_9", True),

        TextOption("setting", "cea_source_10", "album"),
        TextOption("setting", "cea_tag_10", "release_name"),
        BoolOption("setting", "cea_cond_10", False),

        TextOption("setting", "cea_source_11", "work_type"),
        TextOption("setting", "cea_tag_11", "genre"),
        BoolOption("setting", "cea_cond_11", False),

        TextOption("setting", "cea_source_12", ""),
        TextOption("setting", "cea_tag_12", ""),
        BoolOption("setting", "cea_cond_12", False),

        TextOption("setting", "cea_source_13", ""),
        TextOption("setting", "cea_tag_13", ""),
        BoolOption("setting", "cea_cond_13", False),

        TextOption("setting", "cea_source_14", ""),
        TextOption("setting", "cea_tag_14", ""),
        BoolOption("setting", "cea_cond_14", False),

        TextOption("setting", "cea_source_15", "artist"),
        TextOption("setting", "cea_tag_15", "artists"),
        BoolOption("setting", "cea_cond_15", False),

        TextOption("setting", "cea_source_16", "artist"),
        TextOption("setting", "cea_tag_16", "artist"),
        BoolOption("setting", "cea_cond_16", True),

        BoolOption("setting", "cea_tag_sort", True),

        BoolOption("setting", "cea_arrangers", True),
        BoolOption("setting", "cea_cyrillic", True),
        BoolOption("setting", "cea_genres", True),
        TextOption("setting", "cea_chorusmaster", "choirmaster"),
        TextOption("setting", "cea_orchestrator", "orch."),
        TextOption("setting", "cea_concertmaster", "leader"),

        BoolOption("setting", "log_error", True),
        BoolOption("setting", "log_warning", True),
        BoolOption("setting", "log_debug", False),
        BoolOption("setting", "log_info", False),

        TextOption("setting", "ce_version_tag", ""),
        TextOption("setting", "cea_options_tag", ""),
        TextOption("setting", "cwp_options_tag", ""),


    ]

    def __init__(self, parent=None):
        super(ClassicalExtrasOptionsPage, self).__init__(parent)
        self.ui = Ui_ClassicalExtrasOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.use_cwp.setChecked(self.config.setting["classical_work_parts"])
        self.ui.use_cea.setChecked(self.config.setting["classical_extra_artists"])
        self.ui.cwp_retries.setValue(self.config.setting["cwp_retries"])
        self.ui.cea_orchestras.setText(self.config.setting["cea_orchestras"])
        self.ui.cea_choirs.setText(self.config.setting["cea_choirs"])
        self.ui.cea_groups.setText(self.config.setting["cea_groups"])
        self.ui.use_cache.setChecked(self.config.setting["use_cache"])
        self.ui.cwp_proximity.setValue(self.config.setting["cwp_proximity"])
        self.ui.cwp_end_proximity.setValue(self.config.setting["cwp_end_proximity"])
        self.ui.cwp_granularity.setValue(self.config.setting["cwp_granularity"])
        self.ui.cwp_substring_match.setValue(self.config.setting["cwp_substring_match"])
        self.ui.cwp_removewords.setText(self.config.setting["cwp_removewords"])
        self.ui.cwp_synonyms.setText(self.config.setting["cwp_synonyms"])
        self.ui.cwp_titles.setChecked(self.config.setting["cwp_titles"])
        self.ui.cwp_works.setChecked(self.config.setting["cwp_works"])
        self.ui.cwp_extended.setChecked(self.config.setting["cwp_extended"])
        self.ui.cwp_hierarchical_works.setChecked(self.config.setting["cwp_hierarchical_works"])
        self.ui.cwp_level0_works.setChecked(self.config.setting["cwp_level0_works"])
        self.ui.cwp_movt_tag_inc.setText(self.config.setting["cwp_movt_tag_inc"])
        self.ui.cwp_movt_tag_exc.setText(self.config.setting["cwp_movt_tag_exc"])
        self.ui.cwp_movt_no_tag.setText(self.config.setting["cwp_movt_no_tag"])
        self.ui.cwp_work_tag_multi.setText(self.config.setting["cwp_work_tag_multi"])
        self.ui.cwp_work_tag_single.setText(self.config.setting["cwp_work_tag_single"])
        self.ui.cwp_top_tag.setText(self.config.setting["cwp_top_tag"])

        self.ui.cwp_multi_work_sep.setEditText(self.config.setting["cwp_multi_work_sep"])
        self.ui.cwp_single_work_sep.setEditText(self.config.setting["cwp_single_work_sep"])
        self.ui.cwp_movt_no_sep.setEditText(self.config.setting["cwp_movt_no_sep"])

        self.ui.cea_composer_album.setChecked(self.config.setting["cea_composer_album"])

        self.ui.cea_blank_tag.setText(self.config.setting["cea_blank_tag"])
        self.ui.cea_blank_tag_2.setText(self.config.setting["cea_blank_tag_2"])
        
        self.ui.cea_source_1.setEditText(self.config.setting["cea_source_1"])
        self.ui.cea_tag_1.setText(self.config.setting["cea_tag_1"])
        self.ui.cea_cond_1.setChecked(self.config.setting["cea_cond_1"])

        self.ui.cea_source_2.setEditText(self.config.setting["cea_source_2"])
        self.ui.cea_tag_2.setText(self.config.setting["cea_tag_2"])
        self.ui.cea_cond_2.setChecked(self.config.setting["cea_cond_2"])

        self.ui.cea_source_3.setEditText(self.config.setting["cea_source_3"])
        self.ui.cea_tag_3.setText(self.config.setting["cea_tag_3"])
        self.ui.cea_cond_3.setChecked(self.config.setting["cea_cond_3"])

        self.ui.cea_source_4.setEditText(self.config.setting["cea_source_4"])
        self.ui.cea_tag_4.setText(self.config.setting["cea_tag_4"])
        self.ui.cea_cond_4.setChecked(self.config.setting["cea_cond_4"])

        self.ui.cea_source_5.setEditText(self.config.setting["cea_source_5"])
        self.ui.cea_tag_5.setText(self.config.setting["cea_tag_5"])
        self.ui.cea_cond_5.setChecked(self.config.setting["cea_cond_5"])

        self.ui.cea_source_6.setEditText(self.config.setting["cea_source_6"])
        self.ui.cea_tag_6.setText(self.config.setting["cea_tag_6"])
        self.ui.cea_cond_6.setChecked(self.config.setting["cea_cond_6"])

        self.ui.cea_source_7.setEditText(self.config.setting["cea_source_7"])
        self.ui.cea_tag_7.setText(self.config.setting["cea_tag_7"])
        self.ui.cea_cond_7.setChecked(self.config.setting["cea_cond_7"])

        self.ui.cea_source_8.setEditText(self.config.setting["cea_source_8"])
        self.ui.cea_tag_8.setText(self.config.setting["cea_tag_8"])
        self.ui.cea_cond_8.setChecked(self.config.setting["cea_cond_8"])

        self.ui.cea_source_9.setEditText(self.config.setting["cea_source_9"])
        self.ui.cea_tag_9.setText(self.config.setting["cea_tag_9"])
        self.ui.cea_cond_9.setChecked(self.config.setting["cea_cond_9"])

        self.ui.cea_source_10.setEditText(self.config.setting["cea_source_10"])
        self.ui.cea_tag_10.setText(self.config.setting["cea_tag_10"])
        self.ui.cea_cond_10.setChecked(self.config.setting["cea_cond_10"])

        self.ui.cea_source_11.setEditText(self.config.setting["cea_source_11"])
        self.ui.cea_tag_11.setText(self.config.setting["cea_tag_11"])
        self.ui.cea_cond_11.setChecked(self.config.setting["cea_cond_11"])

        self.ui.cea_source_12.setEditText(self.config.setting["cea_source_12"])
        self.ui.cea_tag_12.setText(self.config.setting["cea_tag_12"])
        self.ui.cea_cond_12.setChecked(self.config.setting["cea_cond_12"])

        self.ui.cea_source_13.setEditText(self.config.setting["cea_source_13"])
        self.ui.cea_tag_13.setText(self.config.setting["cea_tag_13"])
        self.ui.cea_cond_13.setChecked(self.config.setting["cea_cond_13"])

        self.ui.cea_source_14.setEditText(self.config.setting["cea_source_14"])
        self.ui.cea_tag_14.setText(self.config.setting["cea_tag_14"])
        self.ui.cea_cond_14.setChecked(self.config.setting["cea_cond_14"])

        self.ui.cea_source_15.setEditText(self.config.setting["cea_source_15"])
        self.ui.cea_tag_15.setText(self.config.setting["cea_tag_15"])
        self.ui.cea_cond_15.setChecked(self.config.setting["cea_cond_15"])

        self.ui.cea_source_16.setEditText(self.config.setting["cea_source_16"])
        self.ui.cea_tag_16.setText(self.config.setting["cea_tag_16"])
        self.ui.cea_cond_16.setChecked(self.config.setting["cea_cond_16"])

        self.ui.cea_tag_sort.setChecked(self.config.setting["cea_tag_sort"])

        self.ui.cea_arrangers.setChecked(self.config.setting["cea_arrangers"])
        self.ui.cea_cyrillic.setChecked(self.config.setting["cea_cyrillic"])
        self.ui.cea_genres.setChecked(self.config.setting["cea_genres"])
        self.ui.cea_chorusmaster.setText(self.config.setting["cea_chorusmaster"])
        self.ui.cea_orchestrator.setText(self.config.setting["cea_orchestrator"])
        self.ui.cea_concertmaster.setText(self.config.setting["cea_concertmaster"])

        self.ui.log_error.setChecked(self.config.setting["log_error"])
        self.ui.log_warning.setChecked(self.config.setting["log_warning"])
        self.ui.log_debug.setChecked(self.config.setting["log_debug"])
        self.ui.log_info.setChecked(self.config.setting["log_info"])

        self.ui.ce_version_tag.setText(self.config.setting["ce_version_tag"])
        self.ui.cea_options_tag.setText(self.config.setting["cea_options_tag"])
        self.ui.cwp_options_tag.setText(self.config.setting["cwp_options_tag"])

    def save(self):
        self.config.setting["classical_work_parts"] = self.ui.use_cwp.isChecked()
        self.config.setting["classical_extra_artists"] = self.ui.use_cea.isChecked()
        self.config.setting["cwp_retries"] = self.ui.cwp_retries.value()
        self.config.setting["cea_orchestras"] = unicode(self.ui.cea_orchestras.text())
        self.config.setting["cea_choirs"] = unicode(self.ui.cea_choirs.text())
        self.config.setting["cea_groups"] = unicode(self.ui.cea_groups.text())
        self.config.setting["use_cache"] = self.ui.use_cache.isChecked()
        self.config.setting["cwp_proximity"] = self.ui.cwp_proximity.value()
        self.config.setting["cwp_end_proximity"] = self.ui.cwp_end_proximity.value()
        self.config.setting["cwp_granularity"] = self.ui.cwp_granularity.value()
        self.config.setting["cwp_substring_match"] = self.ui.cwp_substring_match.value()
        self.config.setting["cwp_removewords"] = unicode(self.ui.cwp_removewords.text())
        self.config.setting["cwp_synonyms"] = unicode(self.ui.cwp_synonyms.text())
        self.config.setting["cwp_titles"] = self.ui.cwp_titles.isChecked()
        self.config.setting["cwp_works"] = self.ui.cwp_works.isChecked()
        self.config.setting["cwp_extended"] = self.ui.cwp_extended.isChecked()
        self.config.setting["cwp_hierarchical_works"] = self.ui.cwp_hierarchical_works.isChecked()
        self.config.setting["cwp_level0_works"] = self.ui.cwp_level0_works.isChecked()
        self.config.setting["cwp_movt_tag_inc"] = unicode(self.ui.cwp_movt_tag_inc.text())
        self.config.setting["cwp_movt_tag_exc"] = unicode(self.ui.cwp_movt_tag_exc.text())
        self.config.setting["cwp_movt_no_tag"] = unicode(self.ui.cwp_movt_no_tag.text())
        self.config.setting["cwp_work_tag_multi"] = unicode(self.ui.cwp_work_tag_multi.text())
        self.config.setting["cwp_work_tag_single"] = unicode(self.ui.cwp_work_tag_single.text())
        self.config.setting["cwp_top_tag"] = unicode(self.ui.cwp_top_tag.text())

        self.config.setting["cwp_multi_work_sep"] = self.ui.cwp_multi_work_sep.currentText()
        self.config.setting["cwp_single_work_sep"] = self.ui.cwp_single_work_sep.currentText()
        self.config.setting["cwp_movt_no_sep"] = self.ui.cwp_movt_no_sep.currentText()

        self.config.setting["cea_composer_album"] = self.ui.cea_composer_album.isChecked()

        self.config.setting["cea_blank_tag"] = unicode(self.ui.cea_blank_tag.text())
        self.config.setting["cea_blank_tag_2"] = unicode(self.ui.cea_blank_tag_2.text())

        self.config.setting["cea_source_1"] = unicode(self.ui.cea_source_1.currentText())
        self.config.setting["cea_tag_1"] = unicode(self.ui.cea_tag_1.text())
        self.config.setting["cea_cond_1"] = self.ui.cea_cond_1.isChecked()

        self.config.setting["cea_source_2"] = unicode(self.ui.cea_source_2.currentText())
        self.config.setting["cea_tag_2"] = unicode(self.ui.cea_tag_2.text())
        self.config.setting["cea_cond_2"] = self.ui.cea_cond_2.isChecked()

        self.config.setting["cea_source_3"] = unicode(self.ui.cea_source_3.currentText())
        self.config.setting["cea_tag_3"] = unicode(self.ui.cea_tag_3.text())
        self.config.setting["cea_cond_3"] = self.ui.cea_cond_3.isChecked()

        self.config.setting["cea_source_4"] = unicode(self.ui.cea_source_4.currentText())
        self.config.setting["cea_tag_4"] = unicode(self.ui.cea_tag_4.text())
        self.config.setting["cea_cond_4"] = self.ui.cea_cond_4.isChecked()

        self.config.setting["cea_source_5"] = unicode(self.ui.cea_source_5.currentText())
        self.config.setting["cea_tag_5"] = unicode(self.ui.cea_tag_5.text())
        self.config.setting["cea_cond_5"] = self.ui.cea_cond_5.isChecked()

        self.config.setting["cea_source_6"] = unicode(self.ui.cea_source_6.currentText())
        self.config.setting["cea_tag_6"] = unicode(self.ui.cea_tag_6.text())
        self.config.setting["cea_cond_6"] = self.ui.cea_cond_6.isChecked()

        self.config.setting["cea_source_7"] = unicode(self.ui.cea_source_7.currentText())
        self.config.setting["cea_tag_7"] = unicode(self.ui.cea_tag_7.text())
        self.config.setting["cea_cond_7"] = self.ui.cea_cond_7.isChecked()

        self.config.setting["cea_source_8"] = unicode(self.ui.cea_source_8.currentText())
        self.config.setting["cea_tag_8"] = unicode(self.ui.cea_tag_8.text())
        self.config.setting["cea_cond_8"] = self.ui.cea_cond_8.isChecked()

        self.config.setting["cea_source_9"] = unicode(self.ui.cea_source_9.currentText())
        self.config.setting["cea_tag_9"] = unicode(self.ui.cea_tag_9.text())
        self.config.setting["cea_cond_9"] = self.ui.cea_cond_9.isChecked()

        self.config.setting["cea_source_10"] = unicode(self.ui.cea_source_10.currentText())
        self.config.setting["cea_tag_10"] = unicode(self.ui.cea_tag_10.text())
        self.config.setting["cea_cond_10"] = self.ui.cea_cond_10.isChecked()

        self.config.setting["cea_source_11"] = unicode(self.ui.cea_source_11.currentText())
        self.config.setting["cea_tag_11"] = unicode(self.ui.cea_tag_11.text())
        self.config.setting["cea_cond_11"] = self.ui.cea_cond_11.isChecked()

        self.config.setting["cea_source_12"] = unicode(self.ui.cea_source_12.currentText())
        self.config.setting["cea_tag_12"] = unicode(self.ui.cea_tag_12.text())
        self.config.setting["cea_cond_12"] = self.ui.cea_cond_12.isChecked()

        self.config.setting["cea_source_13"] = unicode(self.ui.cea_source_13.currentText())
        self.config.setting["cea_tag_13"] = unicode(self.ui.cea_tag_13.text())
        self.config.setting["cea_cond_13"] = self.ui.cea_cond_13.isChecked()

        self.config.setting["cea_source_14"] = unicode(self.ui.cea_source_14.currentText())
        self.config.setting["cea_tag_14"] = unicode(self.ui.cea_tag_14.text())
        self.config.setting["cea_cond_14"] = self.ui.cea_cond_14.isChecked()

        self.config.setting["cea_source_15"] = unicode(self.ui.cea_source_15.currentText())
        self.config.setting["cea_tag_15"] = unicode(self.ui.cea_tag_15.text())
        self.config.setting["cea_cond_15"] = self.ui.cea_cond_15.isChecked()

        self.config.setting["cea_source_16"] = unicode(self.ui.cea_source_16.currentText())
        self.config.setting["cea_tag_16"] = unicode(self.ui.cea_tag_16.text())
        self.config.setting["cea_cond_16"] = self.ui.cea_cond_16.isChecked()

        self.config.setting["cea_tag_sort"] = self.ui.cea_tag_sort.isChecked()

        self.config.setting["cea_arrangers"] = self.ui.cea_arrangers.isChecked()
        self.config.setting["cea_cyrillic"] = self.ui.cea_cyrillic.isChecked()
        self.config.setting["cea_genres"] = self.ui.cea_genres.isChecked()
        self.config.setting["cea_chorusmaster"] = unicode(self.ui.cea_chorusmaster.text())
        self.config.setting["cea_orchestrator"] = unicode(self.ui.cea_orchestrator.text())
        self.config.setting["cea_concertmaster"] = unicode(self.ui.cea_concertmaster.text())

        self.config.setting["log_error"] = self.ui.log_error.isChecked()
        self.config.setting["log_warning"] = self.ui.log_warning.isChecked()
        self.config.setting["log_debug"] = self.ui.log_debug.isChecked()
        self.config.setting["log_info"] = self.ui.log_info.isChecked()

        self.config.setting["ce_version_tag"] = unicode(self.ui.ce_version_tag.text())
        self.config.setting["cea_options_tag"] = unicode(self.ui.cea_options_tag.text())
        self.config.setting["cwp_options_tag"] = unicode(self.ui.cwp_options_tag.text())




#################
# MAIN ROUTINE  #
#################

register_track_metadata_processor(PartLevels().add_work_info)
register_track_metadata_processor(ExtraArtists().add_artist_info)
register_options_page(ClassicalExtrasOptionsPage)
