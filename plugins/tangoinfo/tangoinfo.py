# -*- coding: utf-8 -*-
PLUGIN_NAME = "Tango.info Adapter"
PLUGIN_AUTHOR = "Felix Elsner"
PLUGIN_DESCRIPTION = """
<p>Load genre, date and vocalist tags from the online database
<a href"http://tango.info">tango.info</a>.</p>
<p>This plugin uses web scraping, but only once per album. In so doing
it does not cause unnecessary server load for either MusicBrainz.org
or tango.info</p>
"""
PLUGIN_VERSION = "0.1.5"
PLUGIN_API_VERSIONS = ["1.3.0", "1.4.0"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard import log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor

from functools import partial
import re

# Python3 compatability
try:
    unicode
except NameError:
    unicode = str

table_regex = re.compile(
       """<h2><a href="\/tracks">Tracks<\/a><\/h2>(?!<\/table>)(.+?)<\/table>"""
) # Match the 'tracks' <table>
trs = re.compile("<tr>((?!<\/tr>).+?)</tr>") # Match <tr> elements
tds = re.compile("<td[^>]*>((?!<\td>).+?)</td>") # Match <td> elements


class TangoInfoTagger:

    class TangoInfoScrapeQueue(LockableObject):

        def __init__(self):
            LockableObject.__init__(self)
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            self.lock_for_read()
            value = self.queue.get(name)
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
        self.albumpage_cache = {}
        self.albumpage_queue = self.TangoInfoScrapeQueue()

    def add_tangoinfo_data(self, album, track_metadata,
            trackXmlNode, releaseXmlNode):
        #log.debug("%s: Track metadata: %s " % (PLUGIN_NAME, track_metadata))

        # BARCODE or barcode
        if track_metadata["barcode"]:
            barcode = str(track_metadata["barcode"])
        elif track_metadata["BARCODE"]:
            barcode = str(track_metadata["BARCODE"])
        else:
            # Abort if no barcode in track_metadata
            #log.debug("%s: No barcode found for %s" % (PLUGIN_NAME, \
            #        trackXmlNode) # No __getitem__ function? too verbose...
            #         )
            return

        tint = str("0%s-%s-%s" % (
                        barcode,
                        str(track_metadata["discnumber"])\
                                if track_metadata.get("discnumber") else "1",
                        str(track_metadata["tracknumber"])
                        ))

        if barcode in self.albumpage_cache:
            if self.albumpage_cache[barcode]:
                if not self.albumpage_cache[barcode].get(tint):
                    log.debug("%s: No information on tango.info for barcode \
                            %s" % (PLUGIN_NAME, barcode))
                else:
                    for field in ['genre', 'date', 'vocal']:
                        # Checks, as not to overwrite with empty data
                        if self.albumpage_cache[barcode][tint].get(field):
                            track_metadata[field] = self\
                                    .albumpage_cache[barcode][tint][field]
            else:
                log.debug("%s: No information on tango.info for barcode %s" \
                        % (PLUGIN_NAME, barcode))
        else:
            #log.debug("%s: Adding to queue: %s, new track: %s" \
            #       % (PLUGIN_NAME, barcode, album._new_tracks[-1]))
            self.website_add_track(album, album._new_tracks[-1], barcode, tint)


    def website_add_track(self, album, track, barcode, tint, zeros=0):
        """
        :param zeros: Number of zeros that have been prepended to the barcode
        """
        self.album_add_request(album)

        if self.albumpage_queue.append(barcode, (track, album, tint)):
            log.debug("%s: Downloading from tango.info: track %s, album %s, \
                  with TINT %s" % (\
                    PLUGIN_NAME, str(track), str(album), tint)
            )

            host = 'tango.info'
            port = 443
            path = '/%s' % (barcode)

            # Call website_process as a partial func
            return album.tagger.xmlws.get(host, port, path,
                        partial(self.website_process, barcode, zeros),
                        xml=False, priority=False, important=False)

    def website_process(self, barcode, zeros, response, reply, error):

        if error:
            log.error("%s: Error retrieving info for barcode %s" % \
                    PLUGIN_NAME, barcode)
            tuples = self.albumpage_queue.remove(barcode)
            for track, album in tuples:
                self.album_remove_request(album)
            return

        tangoinfo_album_data = self.barcode_process_metadata(barcode, response)

        self.albumpage_cache[barcode] = tangoinfo_album_data
        tuples = self.albumpage_queue.remove(barcode)

        if tangoinfo_album_data:
            if zeros > 0:
                log.debug("%s: "
            "tango.info does not seem to have data for barcode %s.  However, "
            "retrying with barcode %s (i.e. the same with 0 prepended) was "
            "successful. This most likely means either MusicBrainz or "
            "tango.info has stored a wrong barcode for this release. You might "
            "want to investigate this discrepancy and report it." \
                          % (PLUGIN_NAME, barcode[zeros:], barcode)
                )

            for track, album, tint in tuples:
                tm = track.metadata

                for field in ['genre', 'date', 'vocal']:
                    # Write track metadata
                    if self.albumpage_cache[barcode][tint].get(field):
                        tm[field] = self.albumpage_cache[barcode][tint][field]
                for file in track.iterfiles(True):
                    # from track.py: def iterfiles(self, save=False)...
                    fm = file.metadata
                    for field in ['genre', 'date', 'vocal']:
                        # Write file metadata
                        if self.albumpage_cache[barcode][tint][field]:
                            fm[field] = self.albumpage_cache[barcode][tint][field]
                self.album_remove_request(album)
        else:
            if zeros >= 2:
                log.debug("%s: "
                    "Could not load album with barcode %s even with zero "
                    "prepended(%s).  This most likely means tango.info does "
                    "not have a release for this barcode (or MusicBrainz has a "
                    "wrong barcode)" \
                          % (PLUGIN_NAME, barcode[1:], barcode)
                )
                for track, album, tint in tuples:
                    self.album_remove_request(album)
                return

            log.debug("%s: Retrying with 0-padded barcode for barcode %s" % \
                    (PLUGIN_NAME, barcode))

            for track, album, tint in tuples:
                retry_barcode = "0" + str(barcode)
                retry_tint = "0" + tint
                # Try again with new barcode, but at most two times(param zero)
                self.website_add_track(
                        album, track, retry_barcode, retry_tint, zeros=(zeros+1)
                )
                self.album_remove_request(album)


    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    def barcode_process_metadata(self, barcode, response):

        # Check whether we have a concealed 404 and get the homepage
        if "<title>Contents - tango.info</title>" in response:
            log.debug("%s: No album with barcode %s on tango.info" % \
                    (PLUGIN_NAME, barcode))
            return

        table = re.findall(table_regex, response)[0]
        albuminfo = {}
        trcontent = [match.groups()[0] for match in trs.finditer(table)]

        for tr in trcontent:
            trackinfo = [trmatch.groups()[0] for trmatch in tds.finditer(tr)]
            if not trackinfo: # check if list is empty, e.g. contains a <th>
                continue

            # Get genre
            if trackinfo[3] and not trackinfo[3] == "-":
                genre = unicode(
                            re.split('<|>', trackinfo[3])[2].title(), 'utf8'
                        )
            else:
                genre = False
            # Get date
            if trackinfo[6] and not trackinfo[6] == "-":
                date = unicode(re.split('<|>', trackinfo[6])[2], 'utf8')
            else:
                date = False
            # Get singers
            if trackinfo[5] == "-" or not trackinfo[5]:
                vocal = False
            elif trackinfo[5]:
                # Catch and strip <a> tags
                vocal = unicode(re.sub("<[^>]*>", "", trackinfo[5]), 'utf8')
            else:
                vocal = False

            # expected format in HTML: <a href="/002390...">...
            tint = trackinfo[8].split("\"")[1][1:]
            albuminfo[tint] = {
                                'genre': genre,
                                'date': date,
                                'vocal': vocal
                              }

        return albuminfo

register_track_metadata_processor(TangoInfoTagger().add_tangoinfo_data)
