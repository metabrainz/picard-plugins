# Copyright © 2016 Daniel sobey <dns@dns.id.au >

# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

PLUGIN_NAME = 'wikidata-genre'
PLUGIN_AUTHOR = 'Daniel Sobey'
PLUGIN_DESCRIPTION = 'query wikidata to get genre tags'
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]
PLUGIN_LICENSE = 'WTFPL'
PLUGIN_LICENSE_URL = 'http://www.wtfpl.net/'

from picard import config, log
from picard.metadata import register_album_metadata_processor
from picard.metadata import register_track_metadata_processor
from picard.webservice import XmlWebService
from functools import partial
import threading

class wikidata:
    
    
    def __init__(self):
        self.lock=threading.Lock()	
        # active request queue
        self.requests={}
        self.taggers={}
        
        # cache
        self.cache={}
		
    def process_release(self,tagger, metadata, release):
	    
        self.xmlws=tagger.tagger.xmlws
        self.log=tagger.log
        item_id = dict.get(metadata,'musicbrainz_releasegroupid')[0]
        
        log.info('WIKIDATA: processing release group %s ' % item_id)
        self.process_request(metadata,tagger,item_id,type='release-group')
        for artist in dict.get(metadata,'musicbrainz_albumartistid'):
            item_id=artist
            log.info('WIKIDATA: processing release artist %s' % item_id)
            self.process_request(metadata,tagger,item_id,type='artist')
        
        
    def process_request(self,metadata,tagger,item_id,type):
        self.lock.acquire()
        log.debug('WIKIDATA: Looking up cache for item  %s' % item_id)
        log.debug('WIKIDATA: requests %s'  % tagger._requests)
        log.debug('WIKIDATA: TYPE %s'  % type)
        if item_id in self.cache.keys():
            log.info('WIKIDATA: found in cache')
            genre_list=self.cache.get(item_id);
            metadata["genre"] = genre_list
            
            if tagger._requests==0:
                tagger._finalize_loading(None)
            self.lock.release()
            return
        else:
            # pending requests are handled by adding the metadata object to a list of things to be updated when the genre is found
            if item_id in self.requests.keys():
                log.debug('WIKIDATA: request already pending, add it to the list of items to update once this has been found')
                self.requests[item_id].append(metadata)
                
                tagger._requests += 1
                self.taggers[item_id].append(tagger)
                self.lock.release()
                return
            self.requests[item_id]=[metadata]
            tagger._requests += 1
            self.taggers[item_id]=[tagger]
            log.debug('WIKIDATA: first request for this item')
            
            self.lock.release()
            log.info('WIKIDATA: about to call musicbrainz to look up %s ' % item_id)
            # find the wikidata url if this exists
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            
            
            path = '/ws/2/%s/%s' % (type,item_id)
            queryargs = {"inc": "url-rels"}
            self.xmlws.get(host, port, path,
                          partial(self.musicbrainz_release_lookup, item_id,metadata),
                                   xml=True, priority=False, important=False,queryargs=queryargs)
        
    def musicbrainz_release_lookup(self,item_id,metadata, response, reply, error):
        found=False;
        if error:
            log.info('WIKIDATA: error retrieving release group info')
        else:
            if 'metadata' in response.children:
                if 'release_group' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].release_group[0].children:
                        for relation in response.metadata[0].release_group[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found=True
                                wikidata_url=relation.target[0].text
                                item_id=item_id
                                self.process_wikidata(wikidata_url,item_id)
                if 'artist' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].artist[0].children:
                        for relation in response.metadata[0].artist[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found=True
                                wikidata_url=relation.target[0].text
                                item_id=item_id
                                self.process_wikidata(wikidata_url,item_id)
                                
                if 'work' in response.metadata[0].children:
                    if 'relation_list' in response.metadata[0].work[0].children:
                        for relation in response.metadata[0].work[0].relation_list[0].relation:
                            if relation.type == 'wikidata' and 'target' in relation.children:
                                found=True
                                wikidata_url=relation.target[0].text
                                item_id=item_id
                                self.process_wikidata(wikidata_url,item_id)
        if not found:
            log.info('WIKIDATA: no wikidata url')
            self.lock.acquire()
            for tagger in self.taggers[item_id]:
                tagger._requests -= 1
                if tagger._requests==0: 
                    tagger._finalize_loading(None)
                log.debug('WIKIDATA:  TOTAL REMAINING REQUESTS %s' % tagger._requests)
            self.lock.release()
            
    def process_wikidata(self,wikidata_url,item_id):
        item=wikidata_url.split('/')[4]
        path="/wiki/Special:EntityData/"+item+".rdf"
        log.info('WIKIDATA: fetching the folowing url wikidata.org%s' % path)
        self.xmlws.get('www.wikidata.org', 443, path,
                       partial(self.parse_wikidata_response, item,item_id),
                                xml=True, priority=False, important=False)
    def parse_wikidata_response(self,item,item_id, response, reply, error):
        genre_entries=[]
        genre_list=[]
        if error:
            log.error('WIKIDATA: error getting data from wikidata.org')
        else:
            if 'RDF' in response.children:
                node = response.RDF[0]
                for node1 in node.Description:
                    if 'about' in node1.attribs:
                        if node1.attribs.get('about') == 'http://www.wikidata.org/entity/%s' % item:
                            for key,val in node1.children.items():
                                if key=='P136':
                                    for i in val:
                                        if 'resource' in i.attribs:
                                            tmp=i.attribs.get('resource')
                                            if 'entity' ==tmp.split('/')[3] and len(tmp.split('/'))== 5:
                                                genre_id=tmp.split('/')[4]
                                                log.info('WIKIDATA: Found the wikidata id for the genre: %s' % genre_id)
                                                genre_entries.append(tmp)
                        else:
                            for tmp in genre_entries:
                                if tmp == node1.attribs.get('about'):
                                    list1=node1.children.get('name')
                                    for node2 in list1:
                                        if node2.attribs.get('lang')=='en':
                                            genre=node2.text
                                            genre_list.append(genre)
                                            log.debug('Our genre is: %s' % genre)
                                            
        self.lock.acquire()
        if len(genre_list) > 0:
            log.info('WiKIDATA: final list of wikidata id found: %s' % genre_entries)
            log.info('WIKIDATA: final list of genre: %s' % genre_list)
            
            log.debug('WIKIDATA: total items to update: %s ' % len(self.requests[item_id]))
            for metadata in self.requests[item_id]:
                new_genre=[]
                new_genre.append(metadata["genre"])
                for str in genre_list:
                    if str not in new_genre:
                       new_genre.append(str)
                       log.debug('WIKIDATA: appending genre %s' % str)
                metadata["genre"] = new_genre
                self.cache[item_id]=genre_list
                log.debug('WIKIDATA: setting genre : %s ' % genre_list)
                
        else:
            log.info('WIKIDATA: Genre not found in wikidata')
        
        log.info('WIKIDATA: Seeing if we can finalize tags %s  ' % len(self.taggers[item_id]))
        
        for tagger in self.taggers[item_id]:
            tagger._requests -= 1
            if tagger._requests==0:
                tagger._finalize_loading(None)
            log.info('WIKIDATA:  TOTAL REMAINING REQUESTS %s' % tagger._requests)
        self.lock.release()
        
    def process_track(self, album, metadata, trackXmlNode, releaseXmlNode):
        self.xmlws=album.tagger.xmlws
        self.log=album.log
        tagger=album
        
        item_id = dict.get(metadata,'musicbrainz_releasegroupid')[0]		
        log.debug('WIKIDATA: looking up release metadata for %s ' % item_id)
        self.process_request(metadata,tagger,item_id,type='release-group')
        
        for artist in dict.get(metadata,'musicbrainz_albumartistid'):
            item_id=artist
            log.info('WIKIDATA: processing release artist %s' % item_id)
            self.process_request(metadata,tagger,item_id,type='artist')
        
        for artist in dict.get(metadata,'musicbrainz_artistid'):
            item_id=artist
            log.info('WIKIDATA: processing track artist %s' % item_id)
            self.process_request(metadata,tagger,item_id,type='artist')
        
        if 'musicbrainz_workid' in metadata:
            for workid in dict.get(metadata,'musicbrainz_workid'):
                item_id=workid
                log.info('WIKIDATA: processing track artist %s' % item_id)
                self.process_request(metadata,tagger,item_id,type='work')

        

wikidata=wikidata()
#register_album_metadata_processor(wikidata.process_release)
register_track_metadata_processor(wikidata.process_track)

