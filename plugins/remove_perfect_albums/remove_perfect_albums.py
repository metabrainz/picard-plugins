PLUGIN_NAME = 'Remove Perfect Albums'
PLUGIN_AUTHOR = 'ichneumon, hrglgrmpf, dsparkplug'
PLUGIN_DESCRIPTION = '''Remove all perfectly matched albums from the selection.'''
PLUGIN_VERSION = '0.3'
PLUGIN_API_VERSIONS = ['0.15', '2.0']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import os
import os.path
from picard import log
from picard.album import Album
from picard.ui.itemviews import BaseAction, register_album_action

class RemovePerfectAlbums(BaseAction):
    NAME = 'Remove perfect albums'

    def callback(self, objs):
        for album in objs:
            if (isinstance(album, Album) and album.is_complete() and album.get_num_unmatched_files() == 0
              	and album.get_num_matched_tracks() == len(list(album.iterfiles()))
              	and album.get_num_unsaved_files() == 0 and album.loaded == True):
                self.tagger.remove_album(album)

class RemovePerfectAlbumsAllowingMultipleFileExtensions(BaseAction):
    NAME = 'Remove perfect albums (allowing multiple file extensions)'

    def callback(self, objs):
        for album in objs:
            
            if (not(isinstance(album, Album))):
                continue
           
            title = album.column('title')
            log.info('Checking album perfection: %s', title)
            
            if (album.loaded != True):
                log.info('Album is not loaded')
                continue

            unsavedFiles = album.get_num_unsaved_files()
            if (unsavedFiles > 0):
                log.info('Album has %s unsaved files', unsavedFiles)
                continue
            
            unmatchedFiles = album.get_num_unmatched_files()
            if (unmatchedFiles > 0):
                log.info('Album has %s unmatched files', unmatchedFiles)
                continue
            
            numberOfTracks = len(album.tracks)
            totalFiles = album.get_num_total_files()
            if (totalFiles < numberOfTracks):
                log.info('The number of files %s in album is less than the number of tracks %s', totalFiles, numberOfTracks)
                continue

            if (totalFiles % numberOfTracks != 0):
                log.info('The number of files %s in album is not wholly divisible by the number of tracks %s', totalFiles, numberOfTracks)
                continue

            #get dictionary of file extension counts
            extDict = {}
            for file in album.iterfiles():
                _, ext = os.path.splitext(file.filename)
                extCount = 0
                if ext in extDict:
                    extCount = extDict.get(ext)
                extCount += 1
                extDict[ext] = extCount
            
            #check each extension has the correct number of files
            incorrectExtensionCount = False
            for ext, extCount in extDict.items():
                if (extCount != numberOfTracks):
                    log.info('The number of %s files in album %s is not equal to the number of tracks %s', ext, extCount, numberOfTracks)
                    incorrectExtensionCount = True
                    break
            
            if (incorrectExtensionCount == True):
                continue

            log.info('Removing perfect album: %s', title)
            self.tagger.remove_album(album)

register_album_action(RemovePerfectAlbums())
register_album_action(RemovePerfectAlbumsAllowingMultipleFileExtensions())
