PLUGIN_NAME = 'wikidata-genre'
PLUGIN_AUTHOR = 'Daniel Sobey'
PLUGIN_DESCRIPTION = 'query wikidata to get genre tags'
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]

from picard import config, log
from picard.metadata import register_album_metadata_processor
from picard.webservice import XmlWebService
from functools import partial
import threading

class wikidata:
    
    def __init__(self):
        self.lock=threading.Lock()	
        # active request queue
        self.requests=[]
        
        # cache
        self.cache={}
		
    def process(self,tagger, metadata, release):
	    
        self.xmlws=tagger.tagger.xmlws
        self.log=tagger.log
        self.tagger=tagger

        release_id = dict.get(metadata,'musicbrainz_releasegroupid')[0]		
        self.lock.acquire()
        if release_id in self.cache.keys():
            log.info('WIKIDATA: found in cache')
            genre_list=self.cache.get(release_id);
            metadata["genre"] = genre_list
            if tagger._requests==0:
                tagger._finalize_loading(None)
            self.lock.release()
            return
        self.lock.release()
        tagger._requests += 1
        # find the wikidata url if this exists
        host = config.setting["server_host"]
        port = config.setting["server_port"]
        path = '/ws/2/release-group/%s?inc=url-rels' % release_id
        
        self.xmlws.get(host, port, path,
                       partial(self.website_process, release_id,metadata,tagger),
                                xml=True, priority=False, important=False)
    
    def website_process(self,release_id,metadata,tagger, response, reply, error):
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
                                self.process_wikidata(wikidata_url,metadata,tagger)
        if not found:
            log.info('WIKIDATA: no wikidata url')
            tagger._requests -= 1
            if tagger._requests==0:
                tagger._finalize_loading(None)


    def process_wikidata(self,wikidata_url,metadata,tagger):
        item=wikidata_url.split('/')[4]
        path="/wiki/Special:EntityData/"+item+".rdf"
        log.info('WIKIDATA: fetching the folowing url wikidata.org%s' % path)
        self.xmlws.get('www.wikidata.org', 443, path,
                       partial(self.parse_wikidata_response, item,metadata,tagger),
                                xml=True, priority=False, important=False)
    def parse_wikidata_response(self,item,metadata,tagger, response, reply, error):
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
        if len(genre_list) > 0:
            log.info('WiKIDATA: final list of wikidata id found: %s' % genre_entries)
            log.info('WIKIDATA: final list of genre: %s' % genre_list)
            metadata["genre"] = genre_list
            
            release_id = dict.get(metadata,'musicbrainz_releasegroupid')[0]		
            self.cache[release_id]=genre_list
        else:
            log.info('WIKIDATA: Genre not found in wikidata')
        tagger._requests -= 1
        if tagger._requests==0:
            tagger._finalize_loading(None)

register_album_metadata_processor(wikidata().process)

