PLUGIN_NAME = u'Remove dis-similar files'
PLUGIN_AUTHOR = u'Dan Strohl'
PLUGIN_DESCRIPTION = u'''Remove all files that are below 80% match and remove empty albums.'''
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ['1.3.0']

from picard.album import Album
from picard.ui.itemviews import BaseAction, register_album_action
from picard.file import File
from picard import log
from picard.tagger import Tagger

class RemoveDisSimilarFiles(BaseAction):
    NAME = 'Remove dis-similar files'

    def callback(self, objs):

        log.debug('Plugin - RDF: Remove DisSimilar Files Called')
        rem_objs = []

        for album in objs:
            if isinstance(album,Album) and album.loaded == True:
                files_cnt = 0
                remove_cnt = 0
                for file in album.iterfiles():
                    files_cnt += 1
                    state = file.get_state()
                    sim = file.similarity
                    fn = file.filename
                    log.debug('Plugin - RDF:         name:'+fn)
                    log.debug('Plugin - RDF:   similarity:'+str(sim))
                    if file.similarity < 0.8 and (state == file.NORMAL or state == file.CHANGED):
                        rem_objs.append(file)
                        log.debug('Plugin - RDF:            REMOVE')
                        remove_cnt += 1
                    else:
                        log.debug('Plugin - RDF:             KEEP')
            if files_cnt == remove_cnt:
                rem_objs.append(album)

        log_msg = 'Plugin - RDF: Removing {} objects'.format(str(len(rem_objs)))
        log.debug(log_msg)

        self.tagger.remove(rem_objs)
        log.debug('Plugin - RDF: requested removal of objects')

register_album_action(RemoveDisSimilarFiles())
