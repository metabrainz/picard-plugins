# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Classical Extras'
PLUGIN_AUTHOR = u'Mark Evens (using some code & techniques from "Album Artist Website" by Sophist)'
PLUGIN_DESCRIPTION = u'''A plugin to:
I. Create tags for the hierarchy of works which contain a given track recording - particularly for classical music'

II. Create sorted fields for all performers. Creates a number of variables with alternative values for "artists" and "artist".
Creates an ensemble variable for all ensemble-type performers.
Also creates matching sort fields for artist and artists.
The outputs are hidden variables in Picard (the user can then use a tagger script to choose which value
 they want in their artist, artists or other tags). 

Variables provided are:
Sort fields for all performers
All soloists, with and without instruments/voices (and sorted without instruments/voices).
All ensembles, with and without type (and sorted without type).
All soloists who are also album artists (without instrument etc.).
All ensembles who are also album artists (without type etc.).
All conductors who are also album artists.
All composers who are also album artists.

In case composers / peformers etc are in non-latin script, a latin alternative is provided.
This should not be necessary if "Translate artist names to this locale" is selected in Options->METADATA
- an alternative composer variable is returned where the composer is constructed from the sorted composer variable.
- a performer tag is created using a transliteration technique (for crtyllic scripts).

A variable is also provided for soloists who are not album artists ("support performers").

III. Create tags for artist types which are not normally created in Picard - particularly for classical music (notably instrument arrangers).
'''
PLUGIN_VERSION = '0.5'
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial
import collections
import re
import unicodedata as ud

# CONSTANTS
orchestras = ['orchestra', 'philharmonic', 'philharmonica', 'philharmoniker', 'musicians', 'academy', 'symphony', 'orkester']
choirs = ['choir', 'choir vocals', 'chorus', 'singers', 'domchors', 'domspatzen', 'koor']
groups = ['ensemble', 'band', 'group', 'trio', 'quartet', 'quintet', 'sextet', 'septet', 'octet', 'chamber', 'consort', 'players', 'les ']
ensemble_types = orchestras + choirs + groups
prefixes = ['the', 'a', 'an', 'le', 'la', 'les', 'los', 'il']
synonyms = [('1', 'one'), ('2', 'two'), ('3','three'), ('&', 'and')]

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

# Checks for ensembles
def ensemble_type(performer):
    for ensemble_name in ensemble_types:
        ensemble=re.compile(r'(.*)\b' + ensemble_name + r'\b(.*)', re.IGNORECASE)
        if ensemble.search(performer):
            return True
    return False



class AltArtists:

    def alt_artists(self, album, metadata, *args):
        log.info("RUNNING %s", PLUGIN_NAME)
        self.sort_performers(metadata)                 #provide all the sort fields before creating the new variables
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
                conductorsort = metadata['~caa_conductor_sort'].split(';')
                for index, conductor in enumerate(values):
                    if not only_roman_chars(conductor):
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
                        performer = remove_middle(get_roman(performer))
                    performername = performer
                    if subkey:
                        perftype = ' ('+subkey+')'
                    else:
                        perftype = ''
                    performer = performer + perftype
                    if subkey in ensemble_types or ensemble_type(performername):
                        ensembles.append(performer)
                        ensemble_names.append(performername)
                        #newkey = 'ensemble'
                        if performername in metadata['~albumartists'] or swap_prefix(performername) in metadata['~albumartists_sort'] \
                        or performername in metadata['~albumartists_sort']:
                            album_ensembles.append(performername)
                    else:
                        soloists.append(performer)
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
                            if not subkey in ensemble_types and not ensemble_type(performername):
                                support_performers.append(performer)

            if key.startswith('~performer_sort'):
                mainkey, subkey = key.split(':', 1)
                for performer in values:
                    if subkey in ensemble_types or ensemble_type(performer):
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
                            if not subkey in ensemble_types and not ensemble_type(performer):
                                support_performers_sort.append(performer)

            if key == 'composer':
                composers_sort = metadata['composersort'].split(';')
                for index, composer in enumerate(values):
                    composersort = composers_sort[index]
                    match=last.search(composersort)
                    if match:
                        composerlast = match.group(1)
                    else:
                        composerlast = composersort
                    if not only_roman_chars(composer):
                        composer = remove_middle(unsort(composersort))
                    composers.append(composer)
                    if stripsir(composer) in metadata['~albumartists'] or sort_field(stripsir(composer)) in metadata['~albumartists_sort'] \
                    or stripsir(composer) in metadata['~albumartists_sort'] or composersort in metadata['~albumartists_sort'] \
                    or unsort(composersort) in metadata['~albumartists'] or composerlast in metadata['~albumartists'] \
                    or composerlast in metadata['~albumartists_sort']:
                       album_composers.append(composer)
                       album_composers_sort.append(composersort[index])
                       album_composer_lastnames.append(composerlast)


        metadata['~caa_soloists'] = soloists
        metadata['~caa_soloist_names'] = soloist_names
        metadata['~caa_soloists_sort'] = soloists_sort
        metadata['~caa_ensembles'] = ensembles
        metadata['~caa_ensemble_names'] = ensemble_names
        metadata['~caa_ensembles_sort'] = ensembles_sort
        metadata['~caa_album_soloists'] = album_soloists
        metadata['~caa_album_soloists_sort'] = album_soloists_sort
        metadata['~caa_album_conductors'] = album_conductors
        metadata['~caa_album_conductors_sort'] = album_conductors_sort
        metadata['~caa_album_ensembles'] = album_ensembles
        metadata['~caa_album_ensembles_sort'] = album_ensembles_sort
        metadata['~caa_album_composers'] = album_composers
        metadata['~caa_album_composers_sort'] = album_composers_sort
        metadata['~caa_album_composer_lastnames'] = album_composer_lastnames
        metadata['~caa_support_performers'] = support_performers
        metadata['~caa_support_performers_sort'] = support_performers_sort
        metadata['~caa_composer'] = composers
        metadata['~caa_conductor'] = conductors

    def sort_performers(self, metadata):
        for key, values in metadata.rawitems():
            if key.startswith('conductor'):
                conductorsort = []
                for conductor in values:
                    if not only_roman_chars(conductor):
                        conductor = remove_middle(get_roman(conductor))
                    conductorsort.append(sort_field(conductor))
                metadata['~caa_conductor_sort'] = conductorsort
            if not key.startswith('performer'):
                continue
            mainkey, subkey = key.split(':', 1)
            performersort = []
            for performer in values:
                if not only_roman_chars(performer):
                    performer = remove_middle(get_roman(performer))
                if subkey in ensemble_types or ensemble_type(performer):
                    performersort.append(swap_prefix(performer))
                else:
                    performersort.append(sort_field(performer))
            sortkey = "~performer_sort:%s" % subkey
            log.debug("%s: sortkey = %s, performersort = %s", PLUGIN_NAME, sortkey, performersort)   #debug
            metadata[sortkey] = performersort



class ExtraArtists:
    #CONSTANTS
###
    def __init__(self):

        self.album_artists = collections.defaultdict(lambda: collections.defaultdict(dict))
            # collection of artists to be applied at album level
        self.track_listing = []


    def add_artist_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        log.debug("%s: LOAD NEW TRACK", PLUGIN_NAME)                                      #debug
        #log.info("ALBUM %s", album)
        #log.info("METADATA %s", track_metadata)
        #log.info("TRACKXMLNODE %s", trackXmlNode)
        #log.info("RELEASEXMLNODE %s", releaseXmlNode)
        tm = track_metadata
        track = album._new_tracks[-1]     # Jump through hoops to get track object!!
        self.track_listing.append(track)
        if '~caa_album_composer_lastnames' in track_metadata:                          # composer last names created by alternative artists (this will be made more seamless )
            composer_lastnames = track_metadata['~caa_album_composer_lastnames']
            if album in self.album_artists:
                if composer_lastnames not in self.album_artists[album]['composer_lastnames']:
                    self.album_artists[album]['composer_lastnames'].append(composer_lastnames)
            else:
                self.album_artists[album]['composer_lastnames'] = [composer_lastnames]
        else:
            log.error("NO _CAA_ALBUM_COMPOSER_LASTNAMES variable available for recording. Try REFRESH.")


        if 'recording' in trackXmlNode.children:
            for record in trackXmlNode.children['recording']:
                performerList = self.artist_process_metadata(record, 'instrument')
        #         # returns [(instrument, artist name, artist sort name} or None if no instruments found
                if performerList:
                    log.debug("%s: Instrument Performers: %s", PLUGIN_NAME, performerList)
                    log.info("Processing performer list: %s", performerList)
                    self.set_performer(performerList,tm)
                arrangerList = self.artist_process_metadata(record, 'instrument arranger')
        #         # returns {instrument, arranger name, arranger sort name} or None if no instrument arrangers found
                if arrangerList:
                    log.debug("%s: Instrument Arrangers: %s", PLUGIN_NAME, arrangerList)
                    log.info("Processing arranger list: %s", arrangerList)
                    self.set_arranger(arrangerList,tm)
        if track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
            self.process_album(album)

    
    def artist_process_metadata(self, record, artistType):
        relationList = []
        log.debug("PROCESSING metadata")

        if 'relation_list' in record.children:
            log.debug("PROCESSING relation")
            if 'relation' in record.relation_list[0].children:
                for relation_list_item in record.relation_list:
                    log.info("Relation list item %s", relation_list_item)
                    relationList.append(relation_list_item.relation)
                log.debug("PASS TO PROCESSING RELATIONS")
                return self.artist_process_relations(relationList, artistType)
        else:
            log.error("%s: %r: MusicBrainz work xml result not in correct format - %s",
                      PLUGIN_NAME, workId, response)
        return None

    def artist_process_relations(self, relations, artistType):
        artists = []
        #log.debug("PROCESSING RELATIONS, %s for type = %s", relations, artistType)
        for relation in relations:
            for rel in relation:
                if 'type' in rel.attribs:
                    log.debug("RELATION attribs type OK")
                    log.info(rel.attribs['type'])
                if rel.attribs['type'] == artistType:
                    log.info("found type %s", artistType)
                    log.debug("Rel.children: %s", rel.children)
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            name = rel.artist[0].name[0].text
                            sort_name = rel.artist[0].sort_name[0].text
                            instrument_list = []
                            if 'attribute_list' in rel.children:
                                for inst in rel.attribute_list[0].attribute:
                                    log.info("instrument_list = %s inst = %s, inst.text = %s", instrument_list, inst, inst.text)
                                    if instrument_list:
                                        log.debug("Append %s  .....", inst.text)
                                        instrument_list.append(inst.text)
                                        log.debug("....appended. Instrument_list = %s", instrument_list)
                                    else:
                                        instrument_list = [inst.text]
                            if instrument_list:
                                log.debug("OK OK")
                                log.debug("Instrument list %r", instrument_list)
                                for instrument in instrument_list:
                                    artist = (instrument, name, sort_name)
                                    artists.append(artist)
        if artists:
            log.debug("%s: Artists of type %s found: %s", PLUGIN_NAME, artistType, artists)                          #debug
        else:
            log.debug("No Artist found")                                                                    #debug
        return artists

    def process_album(self, album):
        for track in self.track_listing:
            tm = track.metadata
            if self.album_artists[album]['composer_lastnames']:
                tm['~cea_album_composer_lastnames'] = self.album_artists[album]['composer_lastnames']
                track.album.metadata['~cea_album_composer_lastnames'] = self.album_artists[album]['composer_lastnames']
        log.info("FINISHED Classical Extra Artists. Album: %s", track.album.metadata)

    def set_performer(self,performerList,tm):
        for performer in performerList:
            if performer[0]:
                instrument = performer[0].lower()
                name = performer[1]
                sort_name = performer[2]

                if not only_roman_chars(name):
                    if not only_roman_chars(tm['performer:'+instrument]):
                        name = remove_middle(unsort(sort_name))
                        # Only remove middle name where the existing performer is in non-latin script
                newkey = '%s:%s' % ('performer', instrument)
                log.debug("SETTING PERFORMER. NEW KEY = %s", newkey)
                tm.add_unique(newkey, name)

                details = name + ' (' + instrument +')'
                if '~cea_performer' in tm:
                    tm['~cea_performer'] = tm['~cea_performer'] + '; ' + details
                else:
                    tm['~cea_performer'] = details

    def set_arranger(self,arrangerList,tm):
        for arranger in arrangerList:
            instrument = arranger[0].lower()
            name = arranger[1]
            sort_name = arranger[2]

            if not only_roman_chars(name):
                name = remove_middle(unsort(sort_name))

            newkey = '%s:%s' % ('arranger', instrument)
            log.debug("NEW KEY = %s", newkey)
            tm.add_unique(newkey, name)
            if instrument:
                details = name + ' (' + instrument +')'
            else:
                details = name
            if '~cea_arranger' in tm:
                tm['~cea_arranger'] = tm['~cea_arranger'] + '; ' + details
            else:
                tm['~cea_arranger'] = details


class PartLevels:

    #CONSTANTS
    MAX_RETRIES = 6           #Maximum number of XML- lookup retries if error returned from server
    SUBSTRING_MATCH = 0.66     #Proportion of a string to be matched to a (usually larger) string for it to be considered essentially similar
    USE_CACHE = True
    GRANULARITY = 1            #splitting for matching of parents. 1 = split in two, 2 = split in three etc.

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
        self.trackback  = collections.defaultdict(dict)
            # hierarchical iterative work structure - {id: , children:{id: , children{}, id: etc}, id: etc}
        self.track_listing = {}
            # not used?
        self.top = collections.defaultdict(list)
            # self.top[album] = list of work Ids which are top-level works in album

    def add_work_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        log.debug("%s: LOAD NEW TRACK", PLUGIN_NAME)                                      #debug
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
        workIds = dict.get(track_metadata,'musicbrainz_workid', [])
        if workIds:
            # #log.debug("WorkIds: %s", workIds)                                              #debug
            works = dict.get(track_metadata,'work', [])
            #log.debug("Work names: %s", works)                                              #debug
            for index, workId in enumerate(workIds):
                    # there may be >1 workid but this is not yet fully supported, so code below joins together the work names for multiple ids and attaches it to the first id
                    # this is based on the (reasonable) assumption that multiple "recording of"s will be children of the same parent work.
                if len(works)>1:
                    track_metadata['~cwp_error'] = "WARNING: More than one work for this recording. Check that works are parts of the same higher work as only one parent will be followed up."
                work = sorted(works)
                         ## until multi-works functionality added
                self.parts[workId]['name']= work
                track = album._new_tracks[-1]     # Jump through hoops to get track object!!
                self.trackback[workId]['id'] = workId
                if 'meta' in self.trackback[workId]:
                    self.trackback[workId]['meta'].append((track, album))
                else:
                    self.trackback[workId]['meta'] = [(track, album)]
                if 'arrangers' in self.parts[workId]:
                    log.debug("%s GETTING ARRANGERS FROM CACHE", PLUGIN_NAME)
                    self.set_arranger(self.parts[workId]['arrangers'],track_metadata)
                if workId in self.works_cache and self.USE_CACHE:
                    log.debug("%s: GETTING WORK METADATA FROM CACHE", PLUGIN_NAME)             #debug
                    partId = workId
                    while partId in self.works_cache:
                        ##log.debug("Work: %s", self.parts[partId]['name'])                 #debug
                        parentId = self.works_cache[partId]
                        partId = parentId
                    workId = partId
                if 'no_parent' not in self.parts[workId] or ('no_parent' in self.parts[workId] and not self.parts[workId]['no_parent']):
                    self.work_add_track(album, track, workId, 0)

                if album._requests == 0 and track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
                    self.process_album(album)
                break #plugin does not currently support multiple workIds. Works for multiple workIds are assumed to be children of the same parent and are concatenated.

    def work_add_track(self, album, track, workId, tries):
        #log.debug("%s: ADDING WORK TO LOOKUP QUEUE", PLUGIN_NAME)                   #debug
        self.album_add_request(album)
            # to change the _requests variable to indicate that there are pending requests for this item and delay picard from finalizing the album
        log.debug("%s: Added lookup request. Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if self.works_queue.append(workId, (track, album)): # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            queryargs = {"inc": "work-rels+artist-rels"}
            log.debug("%s: Initiating XML lookup for %s......", PLUGIN_NAME, workId)   #debug
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.work_process, workId, tries),
                                xml=True, priority=True, important=False,
                                queryargs=queryargs)
        else:                                                                      #debug
            log.debug("%s: Work is already in queue: %s", PLUGIN_NAME, workId)      #debug

    def work_process(self, workId, tries, response, reply, error):
        log.debug("%s: LOOKING UP WORK: %s", PLUGIN_NAME, workId)                     #debug
        if error:
            log.error("%s: %r: Network error retrieving work record", PLUGIN_NAME, workId)
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                #log.debug("%s: Removed request after network error. Requests = %s", PLUGIN_NAME, album._requests)   #debug
                if tries < self.MAX_RETRIES:
                    #log.debug("REQUEUEING...")
                    self.work_add_track(album, track, workId, tries + 1)
                else:
                    #log.warning("%s: EXHAUSTED MAX RE-TRIES for XML lookup for track %s", PLUGIN_NAME, track)
                    track.metadata['~cwp_error'] = "ERROR: MISSING METADATA due to network errors. Re-try or fix manually."
                self.album_remove_request(album)
            return
        tuples = self.works_queue.remove(workId)
        for track, album in tuples:
            self.track_listing[(track, album)] = workId
            #log.debug("%s Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if workId in self.parts:
            metaList = self.work_process_metadata(workId, response)
            #log.debug("metaList: %s", metaList)
            parentList = metaList[0]
                # returns [parent id, parent name] or None if no parent found
            arrangers = metaList[1]
            if arrangers:
                self.parts[workId]['arrangers'] = arrangers
                for track, album in tuples:
                    tm = track.metadata
                    self.set_arranger(arrangers,tm)
            if parentList:
                parentId = parentList[0]
                parent = parentList[1]
                #log.debug("%s: Processed metadata and found parent id: %s, name: %s", PLUGIN_NAME, parentId, parent)      #debug
                if parentId:
                    self.works_cache[workId] = parentId
                    self.parts[workId]['parent']= parentId
                    self.parts[parentId]['name'] = parent
                    for track, album in tuples:         
                        self.work_add_track(album, track, parentId, 0)
                else:
                    #log.info("No parent 1")
                    self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                    self.top_works[(track, album)]['workId'] = workId
                    if workId not in self.top[album]:
                        self.top[album].append(workId)
                    #log.info("TOP[album]: %s", self.top[album])
            else:  #ERROR?
                #log.info("No parent 2")
                self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                self.top_works[(track, album)]['workId'] = parentId
                self.top[album].append(parentId)
        for track, album in tuples:
            if album._requests == 1:                                  # Next remove will finalise album
                self.process_album(album)                       # so do the final album-level processing before we go!
            self.album_remove_request(album)
            log.debug("%s: Removed request. Requests = %s", PLUGIN_NAME, album._requests)   #debug


    def process_album(self, album):
        log.info("PROCESS ALBUM %s", album)
        # populate the inverse hierarchy
        log.debug("Cache: %s", self.works_cache)
        for workId in self.works_cache:
            parentId = self.works_cache[workId]
            log.debug("create inverses: %s, %s", workId, parentId)
            if parentId in self.partof:
                if workId not in self.partof[parentId]:
                    self.partof[parentId].append(workId)
            else:
                self.partof[parentId] = [workId]
            log.debug("Partof: %s", self.partof[parentId])
        # work out the full hierarchy and part levels
        height = 0
        #log.debug("TRACKBACK - full : %s", self.trackback)
        log.debug("TOP %s", self.top[album])
        if len(self.top[album]) > 1:
            single_work_album = 0
        else:
            single_work_album = 1
        for topId in self.top[album]:
            self.create_trackback(topId)
            log.info("Top id = %s, Name = %s", topId, self.parts[topId]['name'])
            log.info("Trackback before levels: %s", self.trackback[topId])
            work_part_levels = self.level_calc(self.trackback[topId], height)
            log.info("Trackback after levels: %s", self.trackback[topId])
            # determine the level which will be the principal 'work' level
            if work_part_levels >= 3:
                ref_level = work_part_levels - single_work_album
            else:
                ref_level = work_part_levels
            ref_level = min(3, ref_level)               # extended metadata scheme won't display more than 3 work levels
            ref_height = work_part_levels - ref_level
            top_info = {'levels': work_part_levels, 'id': topId, 'name': self.parts[topId]['name'], 'single': single_work_album}
            # set the metadata in sequence defined by the work structure
            answer = self.process_trackback(self.trackback[topId], ref_height, top_info)
            if answer:
                tracks = answer[1]['track']
                #log.info("TRACKS: %s", tracks)
                work_part_levels = self.trackback[topId]['depth']
                for track in tracks:
                    track_meta = track[0]
                    tm = track_meta.metadata
                    title_work_level = 0
                    if '~cwp_title_work' in tm and '~cwp_title_work_level' in tm:
                        title_work_level = int(tm['~cwp_title_work_level'])
                    self.extend_metadata(track_meta, ref_height, title_work_level)   # revise for new data
                              
                log.debug("FINISHED TRACK PROCESSING FOR Top work id: %s", topId)

    def create_trackback(self, parentId):
        log.debug("Create trackback for %s", parentId)
        if parentId in self.partof:
            for child in self.partof[parentId]:
                if child in self.partof:
                    child_trackback = self.create_trackback(child)
                    self.append_trackback(parentId, child_trackback)
                else:
                    self.append_trackback(parentId, self.trackback[child])
            return self.trackback[parentId]
        else:
            return self.trackback[parentId]

    def append_trackback(self, parentId, child):
        if parentId in self.trackback:
            if child not in self.trackback[parentId]['children']:
                log.debug("TRYING TO APPEND...")
                self.trackback[parentId]['children'].append(child)
                log.debug("...PARENT %s - ADDED %s as child", self.parts[parentId]['name'], child)
            else:
                log.error("LOGIC ERROR trying to add %s to trackback", child)
        else:
            self.trackback[parentId]['id'] = parentId
            self.trackback[parentId]['children'] = [child]
            log.debug("PARENT %s - ADDED %s as child", self.parts[parentId]['name'], child)
            log.info("APPENDED TRACKBACK: %s", self.trackback[parentId])
        return self.trackback[parentId]






    def level_calc(self, trackback, height):
        if 'children' not in trackback:
            log.info("Got to bottom")
            trackback['height'] = height
            trackback['depth'] = 0
            return 0
        else:
            trackback['height'] = height
            height += 1
            max_depth = 0
            for child in trackback['children']:
                log.debug("CHILD: %s", child)
                depth = self.level_calc(child, height) + 1
                log.debug("DEPTH: %s", depth)
                max_depth = max(depth, max_depth)
            trackback['depth'] = max_depth
            return max_depth
    
    def work_process_metadata(self, workId, response):
        relationList = []
        if 'metadata' in response.children:
            if 'work' in response.metadata[0].children:
                if 'relation_list' in response.metadata[0].work[0].children:
                    if 'relation' in response.metadata[0].work[0].relation_list[0].children:
                        for relation_list_item in response.metadata[0].work[0].relation_list:
                            relationList.append(relation_list_item.relation)
                        return self.work_process_relations(relationList)

            else:
                log.error("%s: %r: MusicBrainz work xml result not in correct format - %s", 
                          PLUGIN_NAME, workId, response)
        return None

    def work_process_relations(self, relations):
        #log.debug("%s RelationSS--> %s", PLUGIN_NAME, relations)
        new_workIds = []
        new_works = []
        artists = []
        itemsFound = []
        for relation in relations:
            #log.info("%s Relation--> %s", PLUGIN_NAME, relation)
            for rel in relation:
                if rel.attribs['type'] == 'parts':
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            new_workIds.append(rel.work[0].id)
                            new_works.append(rel.work[0].title[0].text)
                if rel.attribs['type'] == 'instrument arranger':
                    #log.info("found INSTRUMENT ARRANGER")
                    if 'direction' in rel.children:
                        if rel.direction[0].text == 'backward':
                            name = rel.artist[0].name[0].text
                            sort_name = rel.artist[0].sort_name[0].text
                            instrument = rel.attribute_list[0].attribute[0].text
                            artist = (instrument, name, sort_name)
                            artists.append(artist)
                            #log.debug("ARTISTS %s", artists)

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
    
    def set_metadata(self, part_level, workId, parentId, parent, track):
        log.info("Got to set metadata")
        log.debug("%s: SETTING METADATA FOR TRACK = %r, parent = %s, part_level = %s", PLUGIN_NAME, track, parent, part_level)                     #debug
        tm = track.metadata
        if parentId:
            tm['~cwp_workid_' + str(part_level)] = parentId
            tm['~cwp_work_' + str(part_level)] = parent
            work = self.parts[workId]['name']                                          # maybe more than one work name
            works = []
            if isinstance(work, basestring):                                           # in case there is only one and it isn't in a list
                works.append(work)
            else:
                works = work
            stripped_works = []
            for work in works:
                strip = self.strip_parent_from_work(work, parent, part_level, True)
                stripped_works.append(strip[0])
                log.info("Full parent: %s, Parent: %s", strip[1], parent)
                full_parent = strip[1]
                if full_parent != parent:
                    tm['~cwp_work_' + str(part_level)]= full_parent
                    self.parts[parentId]['name'] = full_parent
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:
                            tm['~cwp_work_top'] = full_parent
            tm['~cwp_part_' + str(part_level-1)]= stripped_works
            self.parts[workId]['stripped_name'] = stripped_works
            if stripped_works == works:                          # no match found: nothing stripped
                self.pending_strip[(track)][parentId]['childId'] = workId
                self.pending_strip[(track)][parentId]['children'] = works
                self.pending_strip[(track)][parentId]['part_level'] = part_level - 1
            if workId in self.pending_strip[(track)]:
                children = self.pending_strip[(track)][workId]['children']              # maybe more than one work name
                stripped_works = []
                for child in children:
                    strip = self.strip_parent_from_work(child, parent, part_level, True)
                    stripped_works.append(strip[0])
                child_level = self.pending_strip[(track)][workId]['part_level']
                tm['~cwp_part_' + str(child_level)] = stripped_works
                childId = self.pending_strip[(track)][workId]['childId']
                self.parts[childId]['stripped_name'] = stripped_works
        log.debug("GOT TO END OF SET_METADATA")
    
    def set_arranger(self,arrangerList,tm):
        for arranger in arrangerList:
            instrument = arranger[0]
            name = arranger[1]
            sort_name = arranger[2]
            newkey = '%s:%s' % ('arranger', instrument)
            tm.add_unique(newkey, name)
            tm['~cwp_arranger'] = name + ' (' + instrument + ')'
            tm['~cwp_arranger_sort'] = sort_name


    def strip_parent_from_work(self, work, parent, part_level, extend):             #extend=True is used to find "full_parent" names
        log.debug("%s: STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES", PLUGIN_NAME)
        full_parent = parent
        clean_parent = re.sub('[^\w\s]',' ',parent)
        pattern_parent = re.sub("\s","\W*", clean_parent)
        if extend:
            pattern_parent = "(\W*"+pattern_parent+")(\W*\s)(.*)"
        else:
            pattern_parent = "(\W*"+pattern_parent+")(.*)"
        log.info("Pattern parent: %s, Work: %s", pattern_parent, work)
        p = re.compile(pattern_parent, re.IGNORECASE)
        m = p.search(work)
        if m:
            log.debug("Matched...")                                           #debug
            if extend:
                stripped_work = m.group(3)
            else:
                stripped_work = m.group(2)
            if m.group(2) != ": " and extend:            # may not have a full work name in the parent (missing op. no. etc.)
                if work.count(":") >= part_level:                  # no. of colons is consistent with "work: part" structure
                    split_work = work.split(': ',1)
                    stripped_work = split_work[1]
                    full_parent = split_work[0]
                    if len(full_parent) < len(parent):              # don't shorten parent names! (in case colon is mis-placed)
                        full_parent = parent
                        stripped_work = m.group(3)
        else:
            log.debug("No match...")                                          #debug
            stripped_work = work
        log.debug("Work: %s", work)                                             #debug
        log.debug("Stripped work: %s", stripped_work)                           #debug
        return (stripped_work, full_parent)

    def process_trackback(self, trackback, ref_height, top_info):
        log.debug("IN PROCESS_TRACKBACK. Trackback = %s", trackback)
        tracks = collections.defaultdict(dict)
        if 'children' not in trackback:
            if 'meta' in trackback and 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                log.debug("Processing level 0")
                depth = trackback['depth']
                height = trackback['height']
                workId = trackback['id']
                log.debug("WorkId %s", workId)
                log.debug("Work name %s", self.parts[workId]['name'])
                for track, album in trackback['meta']:
                    log.debug("Track: %s", track)
                    tm = track.metadata
                    log.info("Track metadata = %s", tm)
                    tm['~cwp_workid_' + str(depth)] = workId
                    tm['~cwp_work_' + str(depth)] = self.parts[workId]['name']
                    tm['~cwp_part_levels'] = height
                    tm['~cwp_work_part_levels'] = top_info['levels']
                    tm['~cwp_workid_top'] = top_info['id']
                    tm['~cwp_work_top'] = top_info['name']
                    tm['~cwp_single_work_album'] = top_info['single']
                    log.info("Track metadata = %s", tm)
                    if 'track' in tracks:
                        tracks['track'].append((track, height))
                    else: 
                        tracks['track'] =[(track, height)]
                    log.debug("Tracks: %s", tracks)
                response = (workId, tracks)
                log.debug("LEAVING PROCESS_TRACKBACK depth %s Response = %s", depth, response)
                return response
            else:
                return None
        else:
            if 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                depth = trackback['depth']
                height = trackback['height']
                parentId = trackback['id']
                parent = self.parts[parentId]['name']
                use_titles_in_work = True
                prev_title_work = None
                for child in trackback['children']:
                    log.info("child trackback = %s", child)
                    answer = self.process_trackback(child, ref_height, top_info)
                    if answer:
                        workId = answer[0]
                        child_tracks = answer[1]['track']
                        for track in child_tracks:
                            track_meta = track[0]
                            track_height = track[1]
                            part_level = track_height - height
                            log.debug("Calling set metadata %s", (part_level, workId, parentId, parent, track_meta))
                            self.set_metadata(part_level, workId, parentId, parent, track_meta)

                            if 'track' in tracks:
                                tracks['track'].append((track_meta, track_height))
                            else: 
                                tracks['track'] =[(track_meta, track_height)]

                            title_works = self.derive_from_title(track_meta)
                            work = title_works[0]
                            if prev_title_work and work != prev_title_work:
                                use_titles_in_work = False
                                log.debug("Do not use titles in work for track %s. Work: %s, Prev work: %s, Parent: %s", track, work, prev_title_work, parent)
                            prev_title_work = work
                if use_titles_in_work:
                    if 'track' in tracks:
                        for track in tracks['track']:
                            track_meta = track[0]
                            log.info("Use title info for track: %s", track_meta)
                            title_works = self.derive_from_title(track_meta)
                            work = title_works[0]
                            movt = title_works[1]
                            tm = track_meta.metadata
                            tm['~cwp_title_work'] = work
                            tm['~cwp_title_movement'] = movt
                            log.debug("Title Work depth = %s", depth)
                            tm['~cwp_title_work_level'] = depth                 # depth at which the title work can be applied in extended metadata

                log.debug("Trackback result for %s = %s", parentId, tracks)
                response = parentId, tracks
                log.debug("LEAVING PROCESS_TRACKBACK depth %s Response = %s", depth, response)
                return response
            else:
                return None
        return response


    def derive_from_title(self, track):
        log.info("DERIVING METADATA FROM TITLE for track: %s", track)
        tm = track.metadata
        title = tm['~cwp_title'] or tm['title']
        movt = ""
        work = ""
        if '~cwp_part_levels' in tm:
            part_levels = int(tm['~cwp_part_levels'])
            if int(tm['~cwp_work_part_levels']) > 0:                          # we have a work with movements
                if part_levels > 0:
                    if '~cwp_work_1' in tm:
                        parent = tm['~cwp_work_1']
                        strip = self.strip_parent_from_work(title, parent, 1, False)
                        if strip[0] != title:
                            movt = strip[0]
                            work = strip[1]
                        else:
                            colons = title.count(":")
                            if colons > 0:
                                title_split = title.split(': ',1)
                                title_rsplit = title.rsplit(': ',1)
                                work = title_split[0]
                                movt = title_rsplit[1]
                            else:
                                movt = title
        log.info("Work %s, Movt %s", work, movt)
        return (work, movt)

    def extend_metadata(self, track, ref_height, depth):
        tm = track.metadata
        part_levels = int(tm['~cwp_part_levels'])
        ## set up group heading and part
        log.debug("Extending metadata for track: %s, ref_height: %s, depth: %s", track, ref_height, depth)
        log.debug("Metadata = %s", tm)
        if part_levels > 0:
            ref_level = part_levels - ref_height
            if ref_level == 1:
                groupheading = tm['~cwp_work_1']
            elif ref_level == 2:
                groupheading = tm['~cwp_work_2'] + ":: " + tm['~cwp_part_1']
            elif ref_level >= 3:
                groupheading = tm['~cwp_work_3'] + ":: " + tm['~cwp_part_2'] + ": " + tm['~cwp_part_1']
            else:
                groupheading = None
            tm['~cwp_groupheading'] = groupheading
        if '~cwp_part_0' in tm:
            part = tm ['~cwp_part_0']
            tm['~cwp_part'] = part
        else:
            part = tm['~cwp_work_0']
            tm['~cwp_part'] = part
            #tm['~cwp_extended_part'] = part
        if part_levels == 0:
            groupheading = tm['~cwp_work_0']
        ## extend group heading from title metadata
        log.debug("Set groupheading OK")
        if groupheading:
            if '~cwp_title_work' in tm and '~cwp_title_work_level' in tm:
                work = tm['~cwp_title_work']
                #log.debug("Test for GH/work diffs. gh = %s, work = %s", groupheading, work)
                diff = self.diff_pair(groupheading, work)
                #log.debug("DIFF GH - WORK. ti =%s", diff)
                if not diff:
                    if part_levels > 0:
                        ext_groupheading = groupheading
                else:
                    log.debug("Now calc extended groupheading...")
                    log.info("depth = %s, ref_level = %s", depth, ref_level)
                    if part_levels > 0:
                        stripped_work = diff #self.strip_parent_from_work(work, groupheading, 1, False)[0]
                        log.debug("Stripped work = %s", stripped_work)
                        if ref_level == 1:
                            ext_groupheading = tm['~cwp_work_1'] + " {" + stripped_work + "}"
                        if ref_level == 2:
                            if depth >= 2:
                                ext_groupheading = tm['~cwp_work_2'] + " {" + stripped_work + "}" + ":: " + tm['~cwp_part_1']
                            elif depth == 1:
                                ext_groupheading = tm['~cwp_work_2']  + ":: " + tm['~cwp_part_1'] + " {" + stripped_work + "}"
                            else:
                                ext_groupheading = groupheading

                        if ref_level >= 3:
                            if depth == 3:
                                ext_groupheading = tm['~cwp_work_3'] + " {" + stripped_work + "}" + ":: " + tm['~cwp_part_2'] + ": " + tm['~cwp_part_1']
                            elif depth ==2:
                                ext_groupheading = tm['~cwp_work_3'] + ":: " + tm['~cwp_part_2'] + " {" + stripped_work + "}" + ": " + tm['~cwp_part_1']
                            elif depth ==1:
                                ext_groupheading = tm['~cwp_work_3'] + ":: " + tm['~cwp_part_2'] + ": " + tm['~cwp_part_1'] + " {" + stripped_work + "}"
                            else:
                                ext_groupheading = groupheading

                    else:
                        ext_groupheading = groupheading           # title will be in part
                    log.debug(".... done")
            else:
                ext_groupheading = groupheading
            if ext_groupheading:
                log.debug("EXTENDED GROUPHEADING: %s", ext_groupheading)
                tm['~cwp_extended_groupheading'] = ext_groupheading
        ## extend part from title metadata
        log.debug("Now extend part...")
        if part:
            if '~cwp_title_movement' in tm:
                movement = tm['~cwp_title_movement']
            else:
                movement = tm['~cwp_title'] or tm['title']

            diff = self.diff_pair(part, movement)
            log.debug("DIFF PART - MOVT. ti =%s", diff)
            if not diff:
                log.debug("....strings compared....")
                if part_levels > 0:
                    tm['~cwp_extended_part'] = part
                else:
                    tm['~cwp_extended_part'] = tm['~cwp_work_0']
                    if tm['~cwp_extended_groupheading']:
                        del tm['~cwp_extended_groupheading']
            else:
                if part_levels > 0:
                    stripped_movt = diff  #self.strip_parent_from_work(movement, part, 0, False)[0]
                    tm['~cwp_extended_part'] = part + " {" + stripped_movt + "}"
                else:
                    tm['~cwp_extended_part'] = movement           # title will be in part
        log.debug("....done")
        return None

    def diff_pair(self, mb_item, title_item):
        log.debug("Inside DIFF_PAIR")

        p1 = re.compile(r'^\W*\bM{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b\W*', re.IGNORECASE)  # Matches Roman numerals with punctuation
        p2 = re.compile(r'^\W*\d+\W*')             # Matches positive integers with punctuation
        #p3 = re.compile(r'([\s\w]+)')             # Matches phrases separated by punctuation
    # remove certain words from the comparison
        removewords = ["part", "act","scene","movement","movt" ]
        #log.info("Words to remove in comparison: %s", removewords)
        #log.debug("mb_item: %s", mb_item)
        querywords = mb_item.split()
        resultwords = []
        for word in querywords:
            if word.lower() not in removewords:
                resultwords.append(word)
        mb = ' '.join(resultwords)
        log.debug("mb_item(2): %s", mb_item)
        querywords = title_item.split()
        resultwords = []
        for word in querywords:
            if word.lower() not in removewords:   
                resultwords.append(word)
        ti = ' '.join(resultwords)
        log.debug("title_item: %s", title_item)
    # replace synonyms
        
        for key, equiv in synonyms:
            mb = mb.replace(key, equiv)
            ti = ti.replace(key, equiv)

    #remove numbers, roman numerals and punctuation from the start
        for i in range(0,3):                                                # in case of multiple levels
            mb = p2.sub('',p1.sub('',mb))
            ti = p2.sub('',p1.sub('',ti))

    # try and strip the canonical item from the title item
        ti_new = self.strip_parent_from_work(ti,mb,0,False)[0]
        if ti_new == ti:
            mb_list = re.split(r'[;:\.\-]\s',mb,self.GRANULARITY)
            log.debug("mb_list = %s", mb_list)
            if mb_list:
                for mb_bit in mb_list:
                    ti_new = self.strip_parent_from_work(ti_new,mb_bit,0,False)[0]
                    log.debug("MB_BIT: %s, TI_NEW: %s", mb_bit, ti_new)
        ti = ti_new
        if len(ti) == 0:
            return None
    # return any significant new words in the title
        words = 0
        nonWords = ["in", "on", "at", "of", "and", "de", "d'un", "d'une", "la", "le"]
        ti_list = re.split(' ', ti)
        mb_list2 = re.split(' ', mb)
        for index, mb_bit2 in enumerate(mb_list2):
            log.debug("mb_bit2 %s, boiled bit2: %s, index: %s", mb_bit2, self.boil(mb_bit2), index)
            mb_list2[index] = self.boil(mb_bit2)
            log.debug("mb_list2[%s] = %s", index, mb_list2[index])
        ti_new = []
        ti_test = []
        i=0
        for ti_bit in ti_list:
            log.debug("ti_bit %s", ti_bit)
            if self.boil(ti_bit) in mb_list2:
                words+=1
            else:
                ti_new.append(ti_bit)
                if ti_bit.lower() not in nonWords:
                    ti_test.append(ti_bit)
        log.debug("words %s", words)
        #words_prop = words / len(ti_list)              # proportion of words in ti which are in mb
        log.debug("ti_test = %s", ti_test)
        new_words = len(ti_test)                       # only significant new words count
        #if words_prop > self.SUBSTRING_MATCH and new_words < 4:
        if new_words < 1:
            log.debug("No significantly new text")
            ti = None
        else:
            if ti_new:                               # should be the case as ti_new > ti_test
                ti = ' '.join(ti_new)
                log.debug("New text from title = %s", ti)
            else:
                log.debug("New text empty")
                ti = None
    # see if there is any significant difference between the strings
        if ti:
            nopunc_ti = self.boil(ti)
            nopunc_mb = self.boil(mb)
            ti_len = len(nopunc_ti)
            sub_len = ti_len * self.SUBSTRING_MATCH
            log.debug("test sub....")
            if self.test_sub(nopunc_mb, nopunc_ti, sub_len, 0):   # is there a substring of ti of length at least sub_len in mb?
                ti = None                                         # in which case treat it as essentially the same
            log.debug("...done, ti =%s", ti)
    
    # remove excess brackets and punctuation
        if ti:
            ti = ti.strip("&.-:;,\'\" ")
            log.debug("stripped punc ok. ti = %s", ti)
            if ti:
                if ti.count("\"") == 1:
                    ti = ti.replace("\"", "")
                if ti.count("\'") == 1:
                    ti = ti.replace("\'", "")
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
        log.debug("DIFF is returning ti = %s", ti)
        return ti


    def test_sub(self, strA, strB, sub_len, depth):
        if strA.count(strB) > 0:
            log.info("FOUND: %s", strB)
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
    
    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    # Remove punctuation, spaces, capitals and accents for string comprisona
    def boil(self, s):   
        punc = re.compile(r'\W*')
        s = ''.join(c for c in ud.normalize('NFD', s) if ud.category(c) != 'Mn')
        return punc.sub('',s).strip().lower()

    # Remove certain keywords
    def remove_words(self, query, stopwords):
        log.debg("INSIDE REMOVE_WORDS")
        querywords = query.split()
        resultwords = []
        for word in querywords:
            if word.lower() not in stopwords:   
                resultwords.append(word)
        return ' '.join(resultwords)
        #resultwords  = [word for word in querywords if word.lower() not in stopwords]


register_track_metadata_processor(PartLevels().add_work_info)
register_track_metadata_processor(AltArtists().alt_artists)
register_track_metadata_processor(ExtraArtists().add_artist_info)