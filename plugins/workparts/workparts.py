# -*- coding: utf-8 -*-

PLUGIN_NAME = u'Work Parts'
PLUGIN_AUTHOR = u'Mark Evens (using some code & techniques from "Album Artist Website" by Sophist)'
PLUGIN_DESCRIPTION = u'A plugin to load all work tags which contain a given track recording'
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import config, log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor
from functools import partial
import collections


class PartLevels:

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
            log.debug("APPEND to queue?")                               #debug
            log.debug("Name: " + str(name) + " Value: " + str(value))   #debug
            return value

        def remove(self, name):
            self.lock_for_write()
            value = None
            if name in self.queue:
                value = self.queue[name]
                del self.queue[name]
            self.unlock()
            log.debug("REMOVE for use :")                               #debug
            log.debug("Name: " + str(name) + " Value: " + str(value))   #debug
            return value

    def __init__(self):
        self.works_cache = {}
            # maintains list of parent of each workid, or None if no parent found, so that XML looup only executed if no existing record                            
        self.works_queue = self.WorksQueue()
            # lookup queue - holds track/album pairs for each queued workid (may be more than one pair per id, especially for higher-level parts)
        self.parts = collections.defaultdict(dict)
            # metadata collection - structure is {workid: {name: , parent: }, etc}

    def add_work_info(self, album, track_metadata, trackXmlNode, releaseXmlNode):
        log.info("LOAD NEW TRACK")                                      #debug
        log.debug("Queue is: ")                                         #debug
        log.debug(self.works_queue.queue)                               #debug
        log.debug("parts dictionary: ")                                 #debug
        log.debug(self.parts)                                           #debug
        part_level = 0
        workIds = dict.get(track_metadata,'musicbrainz_workid', [])
        for index, workId in enumerate(workIds):
                # there may be >1 workid (syntactically permitted but semantically dubious)
            work = dict.get(track_metadata,'work', [index])
            log.info("Work is: ")
            log.info(work)
            part_level = part_level + (index /10)
                # in case there is >1 workid, the part_level will store the workid index after the dec pt (used in all parent metadata too)
            track_metadata["workId_" + str(part_level)] = workId
            track_metadata["work_" + str(part_level)] = work
            self.parts[workId]['name']= work
            
            # check to see if the work's parent has already been cached before doing a full lookup
            if workId in self.works_cache:
                log.debug('works_cache')                                #debug
                log.debug(self.works_cache)                             #debug
                part_level += 1
                while self.works_cache[workId]:
                    parentId = self.works_cache[workId]
                    track_metadata['work_parentId_' + str(part_level)] = parentId
                    track_metadata['work_parent_' + str(part_level)] = self.parts[parentId]['name']
                    log.info("Adding parent from cache: ")
                    log.info(parentId + self.parts[parentId]['name'])
                    workId = parentId

            else:
                # Jump through hoops to get track object!!
                part_level += 1
                log.debug("part_level before calling add_track")        #debug
                log.debug(part_level)                                   #debug
                self.work_add_track(part_level, album, album._new_tracks[-1], workId)

    def work_add_track(self, part_level, album, track, workId):
        log.debug("AT work_add_track")
        log.debug("Queue is: ")
        log.debug(self.works_queue.queue)
        log.debug("parts dictionary: ")
        log.debug(self.parts)
        self.album_add_request(album)
            # to change the _requests variable to indicate that there are pending requests for this item and delay picard from finalizing the album                   
        log.info("Added lookup request. Requests = ")
        log.info(album._requests)
        if self.works_queue.append(workId, (track, album)): # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            queryargs = {"inc": "work-rels"}
            log.info("Initiating XML lookup.......")
            log.debug("album")                                          #debug
            log.debug(album)                                            #debug
            log.info("Part level: ")
            log.info(part_level)
            log.debug("workId")                                         #debug
            log.debug(workId)                                           #debug
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.work_process, part_level, workId),
                                xml=True, priority=True, important=False,
                                queryargs=queryargs)
        else:
            log.info("Work is already in queue: " + workId)
            log.debug("Queue is: ")                                     #debug
            log.debug(self.works_queue.queue)                           #debug
            log.debug("parts dictionary: ")                             #debug
            log.debug(self.parts)                                       #debug

    def work_process(self, part_level, workId, response, reply, error):
        log.info("LOOKING UP WORK: ")     
        log.info("Id: " + str(workId) + " Name: " + str(self.parts[workId]['name']))
        if error:
            log.error("%s: %r: Network error retrieving work record", PLUGIN_NAME, workId)
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                self.album_remove_request(album)
                log.info("Removed request. Requests = ")
                log.info(album._requests)
            return
        tuples = self.works_queue.remove(workId)
        log.debug("part_level:")                                        #debug
        log.debug(part_level)                                           #debug
        if self.parts[workId]:
            partId = workId
            log.debug("call work_process_metdata")                      #debug
            parentList = self.work_process_metadata(workId, response)
                # returns [parent id, parent name] or None if no parent found
            if parentList:
                parentId = parentList[0]
                parent = parentList[1]
                log.debug("Processed metadata...")                      #debug
                log.debug("parentId")                                   #debug
                log.debug(parentId)                                     #debug
                self.works_cache[workId] = parentId
                if parentId:
                    self.parts[workId]['parent']= parentId
                    self.parts[parentId]['name'] = parent
                    log.debug("parts: ")                                #debug
                    log.debug(self.parts)                               #debug
                    self.set_metadata(part_level, workId, parentId, parent, tuples)
                    part_level += 1 
                    log.info("Look for the next level.....") 
                    for track, album in tuples:         
                        self.work_add_track(part_level, album, track, parentId)
            else:
                self.works_cache[workId] = None
                    # to prevent looking it up again
        for track, album in tuples:
            log.debug("remove request for album: ")                     #debug
            log.debug(album)                                            #debug
            self.album_remove_request(album)
            log.info("Removed request. Requests = ")
            log.info(album._requests)

    def set_metadata(self, part_level, workId, parentId, parent, tuples):
            log.debug("%s: %r: Parent works = %r", PLUGIN_NAME,
                  workId, parentId)                                     #debug
            for track, album in tuples:
                log.debug("processing tuples...Track is: ")             #debug
                log.debug(track)                                        #debug
                log.debug("part_level is: ")                            #debug
                log.debug(part_level)                                   #debug
                if parentId:
                    tm = track.metadata
                    tm['work_parentId_' + str(part_level)] = parentId
                    tm['work_parent_' + str(part_level)] = parent
                    log.debug("Writing metadata. Parent should be: ")    #debug
                    log.debug(self.works_cache[workId])                  #debug

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    def work_process_metadata(self, workId, response):
        log.debug("got to work_process_metadata...")                    #debug
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
        log.debug("got to work_process_relations...")                   #debug
        new_workIds = []
        new_works = []
        for relation in relations:
            if relation.type == 'parts':
                if 'direction' in relation.children:
                    log.debug('Direction')                              #debug
                    if relation.direction[0].text == 'backward':
                        log.info("Found parent. Id: ")
                        log.info(relation.work[0].id)
                        log.info("Found parent. Name: ")
                        log.info(relation.work[0].title[0].text)
                        new_workIds.append(relation.work[0].id)
                        new_works.append(relation.work[0].title[0].text)
        log.debug("new_workIds:  ")                                     #debug
        log.debug(new_workIds)                                          #debug
        if not new_workIds:
                log.info("No parent found")
        # just select one parent work to return (the longest named, as it is likely to be the lowest level)
        if new_workIds:
            if new_works:
                new_work = max(new_works, key=len)
                i = new_works.index(new_work)
                new_workId = new_workIds[i]
            else:
                new_workId = new_workIds[0]     # in case work is not named for some reason
                new_work = None
        else:
            new_workId = None
            new_work = None   
        if len(new_workIds) > 1:
            log.info("Selected parent = " + str(new_work))     
        return (new_workId, new_work)


register_track_metadata_processor(PartLevels().add_work_info)