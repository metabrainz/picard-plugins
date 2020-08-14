PLUGIN_NAME = "Collect Album Artists"
PLUGIN_AUTHOR = "johbi"
PLUGIN_DESCRIPTION = "Adds a context menu shortcut to collect all track artists from a release and format them as the releases album artist."
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.1', '2.2']
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl.txt"

from picard.album import Album
from picard.ui.itemviews import BaseAction, register_album_action

class CollectArtists(BaseAction):
    NAME = 'Replace release artist with &track artists...'

    def callback(self, objs):
        for album in objs:
            if isinstance(album, Album):
                trackartists = []
                for track in album.tracks:
                    if "artists" in track.metadata:
                        artists = track.metadata.getall("artists")
                    elif "artist" in track.metadata:
                        artists = track.metadata.getall("artist")
                    else:
                        continue

                    for artist in artists:
                        if artist not in trackartists:
                            trackartists.append(artist)

                if len(trackartists) >= 2:
                    albumartist = (", ").join(trackartists[:-1]) + ' & ' + trackartists[-1]
                elif len(trackartists) == 1:
                    albumartist = trackartists[0]
                else:
                    self.tagger.window.set_statusbar_message("Could not find any artists for the album ALBUMTITLE")
                    continue
                album.metadata.set("albumartist",albumartist)

                for track in album.tracks:
                    track.metadata.set("albumartist",albumartist)

                    for files in track.linked_files:
                        track.update_file_metadata(files)

                album.update()

# class ReformatAlbumArtist(BaseAction):
#     NAME = 'Re&format release artist...'

#     def callback(self, objs):
#         print("yup")

register_album_action(CollectArtists())
# register_album_action(ReformatAlbumArtist())
