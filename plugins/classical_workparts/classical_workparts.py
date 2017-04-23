# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Classical Work Parts'
PLUGIN_AUTHOR = u'Mark Evens (using some code & techniques from "Album Artist Website" by Sophist)'
PLUGIN_DESCRIPTION = u'A plugin to create tags for the hierarchy of works which contain a given track recording - particularly for classical music'
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial
import collections
import re


class PartLevels:

    #CONSTANTS
    MAX_RETRIES = 6           #Maximum number of XML- lookup retries if error returned from server
    SUBSTRING_MATCH = 0.66     #Proportion of a string to be matched to a (usually larger) string for it to be considered essentially similar
                                #(used in extended metadata)

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
        self.works_queue = self.WorksQueue()
            # lookup queue - holds track/album pairs for each queued workid (may be more than one pair per id, especially for higher-level parts)
        self.parts = collections.defaultdict(lambda: collections.defaultdict(dict))
            # metadata collection for all parts - structure is {workid: {name: , parent: , (track,album): {part_levels}}, etc}
        self.pending_strip = collections.defaultdict(lambda: collections.defaultdict(dict))
            # metadata collection for parts awaiting higher-level text stripping - structure is {(track, album): {workid: {child: part_level:]}, etc}
        self.top_works = collections.defaultdict(dict)
            # metadata collection for top-level works for (track, album) - structure is {(track, album): {workId: }, etc}

    def add_work_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        log.debug("%s: LOAD NEW TRACK", PLUGIN_NAME)                                      #debug
        part_level = 0
        workIds = dict.get(track_metadata,'musicbrainz_workid', [])
        if workIds:
            # log.debug("WorkIds: %s", workIds)                                              #debug
            track_metadata["cwp_workid_" + str(part_level)] = workIds
            works = dict.get(track_metadata,'work', [])
            log.debug("Work names: %s", works)                                              #debug
            track_metadata["cwp_work_" + str(part_level)] = works
            #track_metadata['cwp_error'] = None
            for index, workId in enumerate(workIds):
                    # there may be >1 workid but this is not yet fully supported, so code below joins together the work names for multiple ids and attaches it to the first id
                    # this is based on the (reasonable) assumption that multiple "recording of"s will be children of the same parent work.
                if len(works)>1:
                    track_metadata['cwp_error'] = "WARNING: More than one work for this recording. Check that works are parts of the same higher work as only one parent will be followed up."
                work = works          ## until multi-works functionality added
                self.rename_works(track_metadata, workId, work, part_level)
                self.parts[workId]['name']= work
                track = album._new_tracks[-1]     # Jump through hoops to get track object!!
                # check to see if the work's parent has already been cached before doing a full lookup
                if workId in self.works_cache:
                    log.debug("%s: GETTING METADATA FROM CACHE", PLUGIN_NAME)             #debug
                    partId = workId
                    while partId in self.works_cache:
                        #log.debug("Work: %s, level: %s", self.parts[partId]['name'], part_level)                 #debug
                        part_level += 1
                        parentId = self.works_cache[partId]
                        parent = self.parts[parentId]['name']
#
                        track_metadata['cwp_workid_' + str(part_level)] = parentId
                        track_metadata['cwp_work_' + str(part_level)] = parent
                        self.rename_works(track_metadata, parentId, parent, part_level)
                        stripped_work = self.parts[partId]['stripped_name']
                        track_metadata['cwp_part_' + str(part_level-1)]=stripped_work
#
                        if parentId not in self.works_cache:                   # We've reached the top
                            log.debug("Reached the top in cache.")
                            self.parts[parentId][(track, album)]['part_level'] = part_level       # max number of part levels for work (so far)
                            self.top_works[(track, album)]['workId'] = parentId
#
                        partId = parentId
                    if track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
                        self.final_process(album)                       # so do the final album-level processing before we go!  
                else:
                    if 'no_parent' in self.parts[workId]:             # i.e. don't look it up if we have already done so and found no parent         
                        if not self.parts[workId]['no_parent']:
                            part_level += 1
                            self.work_add_track(part_level, album, track, workId)
                        else:
                            self.parts[workId][(track, album)]['part_level'] = 0 
                            self.top_works[(track, album)]['workId'] = workId
                            if track_metadata['tracknumber'] == track_metadata['totaltracks']:            #last track
                                self.final_process(album)   
                    else:
                        part_level += 1
                        self.work_add_track(part_level, album, track, workId, 0)
                break #plugin does not currently support multiple workIds. Works for multiple workIds are assumed to be children of the same parent and are concatenated.
        else:                                                       # there are no workiIds
            track_metadata['cwp_single_work_album'] = 0
            track_metadata['cwp_part_levels'] = part_level

    def work_add_track(self, part_level, album, track, workId, tries):
        log.debug("%s: ADDING WORK TO LOOKUP QUEUE", PLUGIN_NAME)                   #debug
        self.album_add_request(album)
            # to change the _requests variable to indicate that there are pending requests for this item and delay picard from finalizing the album                   
        #log.debug("%s: Added lookup request. Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if self.works_queue.append(workId, (track, album)): # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            queryargs = {"inc": "work-rels"}
            log.debug("%s: Initiating XML lookup for %s......", PLUGIN_NAME, workId)   #debug
            #log.debug("Part level: %s", part_level)                                     #debug
            #log.debug("workId: %s", workId)                                         #debug
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.work_process, part_level, workId, tries),
                                xml=True, priority=True, important=False,
                                queryargs=queryargs)
        #else:                                                                      #debug
            #log.debug("%s: Work is already in queue: %s", PLUGIN_NAME, workId)      #debug

    def work_process(self, part_level, workId, tries, response, reply, error):
        log.debug("%s: LOOKING UP WORK: %s", PLUGIN_NAME, workId)                     #debug
        if error:
            log.error("%s: %r: Network error retrieving work record", PLUGIN_NAME, workId)
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                log.debug("%s: Removed request after network error. Requests = %s", PLUGIN_NAME, album._requests)   #debug
                if tries < self.MAX_RETRIES:
                    log.debug("REQUEUEING...")
                    self.work_add_track(part_level, album, track, workId, tries + 1)
                else:
                    log.error("EXHAUSTED MAX RE-TRIES")
                    track.metadata['cwp_error'] = "ERROR: MISSING METADATA due to network errors. Re-try or fix manually."
                self.album_remove_request(album)
            return
        tuples = self.works_queue.remove(workId)
        #for track, album in tuples:                                       #debug
            #log.debug("%s Requests = %s", PLUGIN_NAME, album._requests)   #debug
        if workId in self.parts:
            parentList = self.work_process_metadata(workId, response)
                # returns [parent id, parent name] or None if no parent found
            if parentList:
                parentId = parentList[0]
                parent = parentList[1]
                #log.debug("%s: Processed metadata and found parent :%s", PLUGIN_NAME, parentId)      #debug
                if parentId:
                    self.works_cache[workId] = parentId
                    self.parts[workId]['parent']= parentId
                    self.parts[parentId]['name'] = parent
                    self.set_metadata(part_level, workId, parentId, parent, tuples)
                    part_level += 1 
                    #log.debug("Look for the next level.....")           #debug
                    for track, album in tuples:         
                        self.work_add_track(part_level, album, track, parentId, 0)
                else:
                    self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                    # We've reached the top - NB part_level refers to (non-existent) parent, so is one higher than would be expected
                    for track, album in tuples:
                        self.parts[workId][(track, album)]['part_level'] = part_level - 1         # max number of part levels for work (so far)
                        self.top_works[(track, album)]['workId'] = workId
            else:
                self.parts[workId]['no_parent'] = True          # so we remember we looked it up and found none
                for track, album in tuples:
                    self.parts[workId][(track, album)]['part_level'] = part_level - 1         # max number of part levels for work (so far)
                    self.top_works[(track, album)]['workId'] = workId
        for track, album in tuples:
            if album._requests == 1:                                  # Next remove will finalise album
                self.final_process(album)                       # so do the final album-level processing before we go!  
            self.album_remove_request(album)
            #log.debug("%s: Removed request. Requests = %s", PLUGIN_NAME, album._requests)   #debug

    
    def work_process_metadata(self, workId, response):
        if 'metadata' in response.children:
            if 'work' in response.metadata[0].children:
                if 'relation_list' in response.metadata[0].work[0].children:
                    if 'relation' in response.metadata[0].work[0].relation_list[0].children:
                        return self.work_process_relations(response.metadata[0].work[0].relation_list[0].relation)
            else:
                log.error("%s: %r: MusicBrainz work xml result not in correct format - %s", 
                          PLUGIN_NAME, workId, response)
        return None

    def work_process_relations(self, relations):
        new_workIds = []
        new_works = []
        for relation in relations:
            if relation.type == 'parts':
                if 'direction' in relation.children:
                    if relation.direction[0].text == 'backward':
                        new_workIds.append(relation.work[0].id)
                        new_works.append(relation.work[0].title[0].text)
        log.debug("%s: Parent works found: %s", PLUGIN_NAME, new_works)                          #debug
        #if not new_workIds:                                            #debug
            #log.debug("No parent found")                             #debug
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
            
        return (new_workId, new_work)
    
    def set_metadata(self, part_level, workId, parentId, parent, tuples):
        log.debug("%s: %r: SETTING METADATA FOR PARENT = %r", PLUGIN_NAME, workId, parentId)                     #debug
        for track, album in tuples:
            tm = track.metadata
            #tm['cwp_error'] = None
            if parentId:
                tm['cwp_workid_' + str(part_level)] = parentId
                tm['cwp_work_' + str(part_level)] = parent
                self.rename_works(tm, parentId, parent, part_level)
                work = self.parts[workId]['name']                                          # maybe more than one work name
                works = []
                if isinstance(work, basestring):                                           # in case there is only one and it isn't in a list
                    works.append(work)
                else:
                    works = work
                stripped_works = []
                for work in works:
                    stripped_works.append(self.strip_parent_from_work(work, parent))
                tm['cwp_part_' + str(part_level-1)]= stripped_works
                self.parts[workId]['stripped_name'] = stripped_works
                if stripped_works == works:                          # no match found: nothing stripped
                    self.pending_strip[(track, album)][parentId]['childId'] = workId
                    self.pending_strip[(track, album)][parentId]['children'] = works
                    self.pending_strip[(track, album)][parentId]['part_level'] = part_level - 1
                if workId in self.pending_strip[(track, album)]:
                    children = self.pending_strip[(track, album)][workId]['children']              # maybe more than one work name
                    stripped_works = []
                    for child in children:
                        stripped_works.append(self.strip_parent_from_work(child, parent))
                    child_level = self.pending_strip[(track, album)][workId]['part_level']
                    tm['cwp_part_' + str(child_level)] = stripped_works
                    childId = self.pending_strip[(track, album)][workId]['childId']
                    self.parts[childId]['stripped_name'] = stripped_works
                    

    def rename_works(self, track_metadata, workId, work, part_level):
        track_metadata['cwp_workid_top'] = workId
        track_metadata['cwp_work_top'] = work
        track_metadata['cwp_part_levels'] = part_level

    def strip_parent_from_work(self, work, parent):
        log.debug("%s: STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES", PLUGIN_NAME)
        clean_parent = re.sub('[^\w\s]',' ',parent)
        pattern_parent = re.sub("\s","\W*", clean_parent)
        pattern_parent = "\W*"+pattern_parent+"\W*\s(.*)"
        p = re.compile(pattern_parent, re.IGNORECASE)
        m = p.search(work)              
        if m:
            #log.debug("Matched...")                                           #debug
            stripped_work = m.group(1)
        else:
            #log.debug("No match...")                                          #debug
            stripped_work = work
        log.debug("Work: %s", work)
        log.debug("Stripped work: %s", stripped_work)
        return stripped_work


    def final_process(self, album):
        log.debug("%s: FINAL PROCESSING OF ALBUM-LEVEL METADATA", PLUGIN_NAME)
        top_work = None
        single_work_album = 1
        entries_to_remove = []
        work_part_levels = {}
        for track, album in self.top_works:
            if top_work:
                if top_work != self.top_works[(track, album)]['workId']:            #we have a new top work in the album
                    single_work_album = 0
            top_work = self.top_works[(track, album)]['workId']
            part_levels = self.parts[top_work][(track, album)]['part_level']
            if part_levels == 0:
                single_work_album = 0
            if top_work in work_part_levels:
                work_part_levels[top_work] = max(work_part_levels[top_work], part_levels)
            else:
                work_part_levels[top_work] = part_levels
        for track, album in self.top_works:
            tm = track.metadata
            tm['cwp_work_part_levels'] = work_part_levels[self.top_works[(track, album)]['workId']]
            tm['cwp_single_work_album'] = single_work_album
            self.derive_from_title(track, album)
            self.extend_metadata(track, album, single_work_album)
            entries_to_remove.append((track, album))
        for k in entries_to_remove:
            self.top_works.pop(k, None)
        return None

    def derive_from_title(self, track, album):
        tm = track.metadata
        title = tm['title']
        movt = ""
        work = ""
        if 'cwp_part_levels' in tm:
            part_levels = int(tm['cwp_part_levels'])
            if int(tm['cwp_work_part_levels']) > 0:                          # we have a work with movements
                if part_levels > 0:
                    if 'cwp_work_1' in tm:
                        parent = tm['cwp_work_1']
                        try_movt = self.strip_parent_from_work(title, parent)
                        if try_movt != title:
                            movt = try_movt
                            work = parent
                        else:
                            colons = title.count(":")
                            if colons > 0:
                                title_split = title.split(': ',1)
                                title_rsplit = title.rsplit(': ',1)
                                work = title_split[0]
                                movt = title_rsplit[1] 
                            else:
                                movt = title
                        tm['cwp_title_work'] = work
                        tm['cwp_title_movement'] =movt              
        return None

    def extend_metadata(self, track, album, single_work_album):
        tm = track.metadata
        part_levels = int(tm['cwp_part_levels'])
        ## set up group heading and part
        if single_work_album == 1:
            if int(tm['cwp_work_part_levels']) > 2:
                part_levels -= 1
        if part_levels > 0:
            if part_levels == 1:
                groupheading = tm['cwp_work_1']
            if part_levels == 2:
                groupheading = tm['cwp_work_2'] + ":: " + tm['cwp_part_1']
            if part_levels >= 3:
                groupheading = tm['cwp_work_3'] + ":: " + tm['cwp_part_2'] + ": " + tm['cwp_part_1']
            tm['cwp_groupheading'] = groupheading
        if 'cwp_part_0' in tm:
            part = tm ['cwp_part_0']
            tm['cwp_part'] = part
        else:
            part = tm['title']
            tm['cwp_extended_part'] = part
        if part_levels == 0:
            groupheading = tm['cwp_work_0']
        ## extend group heading from title metadata
        punc = re.compile(r'\W*')
        if groupheading:
            if 'cwp_title_work' in tm:
                work = tm['cwp_title_work']
                nopunc_work = punc.sub('',work).strip().lower()          # Could also use translate to remove accented chars etc.?
                nopunc_gh = punc.sub('',groupheading).strip().lower()
                work_len = len(nopunc_work)
                sub_len = work_len * self.SUBSTRING_MATCH
                if self.test_sub(nopunc_gh, nopunc_work, sub_len, 0):
                    if part_levels > 0:
                        tm['cwp_extended_groupheading'] = groupheading
                else:
                    if part_levels > 0:
                        tm['cwp_extended_groupheading'] = groupheading + " {" + work + "}"
                    else:
                        tm['cwp_extended_groupheading'] = groupheading           # title will be in part
            else:
                tm['cwp_extended_groupheading'] = groupheading
        ## extend part from title metadata
        if part:
            if 'cwp_title_movement' in tm:
                movement = tm['cwp_title_movement']
            else:
                movement = tm['title']    
            nopunc_movt = punc.sub('',movement).strip().lower()          # Could also use translate to remove accented chars etc.?
            nopunc_part = punc.sub('',part).strip().lower()
            movt_len = len(nopunc_movt)
            sub_len = movt_len * self.SUBSTRING_MATCH
            if self.test_sub(nopunc_part, nopunc_movt, sub_len, 0):
                if part_levels > 0:
                    tm['cwp_extended_part'] = part
            else:
                if part_levels > 0:
                    tm['cwp_extended_part'] = part + " {" + movement + "}"
                else:
                    tm['cwp_extended_part'] = part           # title will be in part
        return None

    def test_sub(self, strA, strB, sub_len, depth):
        if strA.count(strB) > 0:
            log.info("FOUND: %s", strB)
            return strB
        else:
            if depth < 16:     #to prevent excessive recursioon, which can cause Picard to hang
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

register_track_metadata_processor(PartLevels().add_work_info)