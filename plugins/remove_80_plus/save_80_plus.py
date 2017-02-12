PLUGIN_NAME = u'Save good files'
PLUGIN_AUTHOR = u'Dan Strohl'
PLUGIN_DESCRIPTION = u'''Save all files at more than 80+ percent.'''
PLUGIN_VERSION = '0.4'
PLUGIN_API_VERSIONS = ['1.3.0']

from picard.album import Album
from picard.ui.itemviews import BaseAction, register_album_action
from picard.file import File
from picard import log
from picard.tagger import Tagger

class RemoveDisSimilarFiles(BaseAction):
    NAME = 'Save good files'

    def callback(self, objs):

        log.debug('Plugin - SGF: Save Good Files Called')
        save_objs = []
        rem_objs = []
        save_batch_size = 100
        loop_cnt = 1
        for album in objs:
            log.debug('Plugin - SGF:Entering album loop...'+str(loop_cnt))
            loop_cnt += 1
            if isinstance(album,Album) and album.loaded == True:
                files_cnt = album.get_num_total_files()
                save_cnt = 0
                for file in album.iterfiles(save=True):
                    files_cnt += 1
                    state = file.get_state()
                    sim = file.similarity
                    fn = file.filename
                    log.debug('Plugin - SGF:         name:'+fn)
                    log.debug('Plugin - SGF:   similarity:'+str(sim))
                    if file.similarity >= 0.8 and (state == file.NORMAL or state == file.CHANGED):
                        save_objs.append(file)
                        rem_objs.append(file)
                        log.debug('Plugin - SGF:            SAVE & REMOVE')
                        save_cnt += 1
                    else:
                        log.debug('Plugin - SGF:             KEEP')
                if album.get_num_total_files() == save_cnt:
                    rem_objs.append(album)

            if len(rem_objs) >= save_batch_size:
                log_msg = 'Plugin - SGF: Saving Batch of {} objects'.format(str(len(save_objs)))
                log.info(log_msg)
                self.tagger.save(save_objs)
                save_objs = []

                log_msg = 'Plugin - SGF: Removing Batch of {} objects'.format(str(len(rem_objs)))
                log.info(log_msg)
                self.tagger.remove(rem_objs)
                rem_objs = []

        if save_objs:
            log_msg = 'Plugin - SGF: Final - Saving {} objects'.format(str(len(save_objs)))
            log.info(log_msg)
            self.tagger.save(save_objs)

        if rem_objs:
            log_msg = 'Plugin - SGF: Final - Removing {} objects'.format(str(len(rem_objs)))
            log.info(log_msg)
            self.tagger.remove(rem_objs)
        log.debug('Plugin - SGF: finishing')


register_album_action(RemoveDisSimilarFiles())
