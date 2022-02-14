# -*- coding: utf-8 -*-
PLUGIN_NAME = "Tango.info Adapter"
PLUGIN_AUTHOR = "Felix Elsner, Sambhav Kothari, Philipp Wolfer"
PLUGIN_DESCRIPTION = """
<p>Load genre, date and vocalist tags for latin dance music
from <a href="https://tango.info">tango.info</a>.</p>
"""
PLUGIN_VERSION = "0.2.0"
PLUGIN_API_VERSIONS = ["2.6", "2.7"]

PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import re
from functools import partial

from picard import log
from picard.util import LockableObject
from picard.metadata import register_track_metadata_processor


table_regex = re.compile(
       r'<h2><a href="\/tracks?">Tracks?<\/a><\/h2>(?!<\/table>)(.+?)<\/table>'
)  # Match the 'tracks'/'track' <table>
tr_regex = re.compile(r"<tr>((?!</tr>).+?)</tr>")  # Match <tr> elements
td_regex = re.compile(r"<td[^>]*>((?!</td>).+?)</td>")  # Match <td> elements
tint_regex = re.compile(r"TINT:([0-9]+-[0-9]{1,2}-[0-9]{1,2})")

TANGO_INFO_HOST = "tango.info"
TANGO_INFO_PORT = 443


# FIXME Remove all this
# This is all just a hack to get around server issues at tango.info
# The server will reply with an empty body if the Host header is set to
# "tango.info:443", but just "tango.info" is fine.
# Picard 2.8+ will by default not append the port to the Host header and thus
# not need this workaround
from picard import PICARD_VERSION
from picard.version import Version
host_workaround_needed = False
if PICARD_VERSION < Version(2, 8, 0, 'dev', 1):
    log.warning("%s: Picard version is older than 2.8, using workaround for "
                "tango.info Host header issue", PLUGIN_NAME)
    host_workaround_needed = True
if host_workaround_needed:
    from picard.webservice import WSGetRequest
    from PyQt5.QtCore import QUrl
    class WrappedWSGetRequest(WSGetRequest):  # noqa
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            url_without_port = QUrl(self.url().url())
            # -1 is QUrl defaultPort
            url_without_port.setPort(-1)
            self.setUrl(url_without_port)


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

        def pop(self, name):
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

    def add_tangoinfo_data(self, album, track_metadata, track, release):

        # Look for BARCODE or barcode tag
        if track_metadata.get("barcode"):
            barcode = str(track_metadata["barcode"])
        elif track_metadata.get("BARCODE"):
            barcode = str(track_metadata["BARCODE"])
        else:
            # Abort if no barcode in track_metadata
            return

        # https://tango.info/wiki/TINT = <TINP>-<Side#>-<Track#>
        # https://tango.info/wiki/TINP - "Tango Info Number for a Product" is a
        # 14-digit numeric tango.info code used by tango.info and others.
        # Example: TINT:00743216335725-1-5
        # This plugin normalizes TINTs by stripping all zeros from the left
        tint = "%s-%s-%s" % (
            barcode.lstrip("0"),
            str(track_metadata.get("discnumber", "1")),
            str(track_metadata.get("tracknumber")),
        )

        if barcode in self.albumpage_cache:
            if self.albumpage_cache[barcode].get(tint):
                for field in ("genre", "date", "vocal"):
                    # Do no overwrite with empty data
                    if not self.albumpage_cache[barcode][tint].get(field):
                        continue
                    track_metadata[field] = \
                        self.albumpage_cache[barcode][tint][field]
            else:
                log.debug(
                    "%s: No information on tango.info for barcode %s",
                    PLUGIN_NAME, barcode)
        else:
            self.website_add_track(album, album._new_tracks[-1], barcode, tint)

    def website_add_track(self, album, track, barcode, tint, zeros=0):
        """
        :param zeros: Number of zeros that have been prepended to the barcode
        """
        self.album_add_request(album)

        if self.albumpage_queue.append(barcode, (track, album, tint)):

            # Barcode, zero-padded as needed
            path = "/%s" % ("0" * zeros) + barcode

            log.debug("%s: Downloading from tango.info: track %s, album %s "
                      "with TINT %s from %s",
                      PLUGIN_NAME, str(track), str(album), tint,
                      "https://%s%s" % (TANGO_INFO_HOST, path))
            # FIXME: Remove this
            if host_workaround_needed:
                ws = album.tagger.webservice
                def get_patched(self, *args, **kwargs):  # noqa
                    request = WrappedWSGetRequest(self, *args, **kwargs)
                    return ws.add_request(request)
                ws.get_patched = get_patched
                return ws.get_patched(
                    TANGO_INFO_HOST,
                    TANGO_INFO_PORT,
                    path,
                    partial(self.website_process, barcode, zeros),
                    priority=False,
                    important=False,
                    parse_response_type=None,
                    queryargs=None,
                )
            # Call website_process() as a partial func
            return album.tagger.webservice.get(
                TANGO_INFO_HOST,
                TANGO_INFO_PORT,
                path,
                partial(self.website_process, barcode, zeros),
                priority=False,
                important=False,
                parse_response_type=None,
                queryargs=None,
            )

    def website_process(self, barcode, zeros, response_bytes, reply, error):
        """
        response_bytes: PyQt5.QtCore.QByteArray, equals reply.readAll()
        reply:          PyQt5.QtNetwork.QNetworkReply
        error:          PyQt5.QtNetwork.QNetworkReply.NetworkError (optional)
        """

        if error:
            log.warning("%s: Network error retrieving info for barcode %s",
                        PLUGIN_NAME, barcode)
            track_triple = self.albumpage_queue.pop(barcode)
            for track, album, tint in track_triple:
                self.album_remove_request(album)
            return

        # Decode QByteArray into unicode
        response_decoded = response_bytes.data().decode('utf-8')

        tangoinfo_albumdata = self.extract_data(barcode, response_decoded)

        self.albumpage_cache[barcode] = tangoinfo_albumdata
        track_triple = self.albumpage_queue.pop(barcode)

        if tangoinfo_albumdata:
            if zeros:
                log.debug("%s: tango.info does not seem to have data for "
                          "barcode %s. "
                          "However, retrying with barcode %s (i.e. the same "
                          "with %s prepended) was successful. "
                          "This most likely means either MusicBrainz or "
                          "tango.info has stored a wrong barcode for this "
                          "release. You might want to investigate this "
                          "discrepancy and report it.",
                          PLUGIN_NAME, barcode, ("0" * zeros) + barcode,
                          ("a zero" if zeros == 1 else "%d zeros" % zeros))

            for track, album, tint in track_triple:
                tm = track.metadata
                if not self.albumpage_cache[barcode].get(tint):
                    self.album_remove_request(album)
                    continue

                for field in ("genre", "date", "vocal"):
                    # Write track metadata
                    if self.albumpage_cache[barcode][tint].get(field):
                        tm[field] = self.albumpage_cache[barcode][tint][field]

                for file in track.iterfiles():
                    fm = file.metadata
                    for field in ("genre", "date", "vocal"):
                        if not self.albumpage_cache[barcode][tint].get(field):
                            continue
                        # Write file metadata
                        fm[field] = self.albumpage_cache[barcode][tint][field]
                self.album_remove_request(album)
        else:
            if zeros >= 2:
                log.debug("%s: Could not load album with barcode %s even with "
                          "zero prepended(%s). This most likely means "
                          "tango.info does not have a release for this "
                          "barcode (or MusicBrainz has a wrong barcode)",
                          PLUGIN_NAME, barcode, ("0" * zeros) + barcode)
                for track, album, tint in track_triple:
                    self.album_remove_request(album)
                return

            log.debug("%s: Retrying with 0-padded barcode for barcode %s",
                      PLUGIN_NAME, barcode)

            for track, album, tint in track_triple:
                # Try again with zero-prepended barcode, but at most two times
                self.website_add_track(
                    album, track, barcode, tint, zeros=(zeros + 1)
                )
                self.album_remove_request(album)

    def album_add_request(self, album):
        album._requests += 1

    def album_remove_request(self, album):
        album._requests -= 1
        album._finalize_loading(None)

    def extract_data(self, barcode, response):

        # Check whether we have a concealed 404 and get the homepage
        if "<title>Contents - tango.info</title>" in response:
            log.debug("%s: No album with barcode %s on tango.info",
                      PLUGIN_NAME, barcode)
            return

        table = re.findall(table_regex, response)
        if not table:
            log.warning("%s: Could not extract table from album webpage - "
                        "regex failed or page structure changed", PLUGIN_NAME)
            return
        table = table[0]  # re.findall() returns a list

        # Content inside of <tr> elements
        trcontent = (match.groups()[0] for match in tr_regex.finditer(table))

        page_structure_warned = False  # Ratelimit warnings

        albuminfo = {}

        for tr in trcontent:
            # Content inside of <td> elements
            trackinfo = [m.groups()[0] for m in td_regex.finditer(tr)]

            # Example of expected structure:
            # <tr>
            # <td class="side_num">1</td>
            # <td class="track_num">6</td>
            # <td><a href="/T0370182390">Ese sos vos</a></td>
            # <td><a href="/genre.tango">tango</a></td>
            # <td><a href="/RicarTantu">Ricardo Tanturi</a></td>
            # <td><a href="/AlberDeluc">Alberto Castillo</a></td>
            # <td><a class="date" href="/1941-12-23">1941-12-23</a></td>
            # <td>02:38</td>
            # <td><a href="/00743216335725-1-6"
            #        title="TINT:00743216335725-1-6">info</a><br /></td>
            # </tr>

            # Sanity checks
            if not trackinfo:
                # Check if list is empty, e.g. contains a <th> for table header
                continue
            if len(trackinfo) < 9:
                if not page_structure_warned:  # Only warn once per <tr>
                    log.warning("%s: Table '<tr>' structure on webpage "
                                "unexpected for barcode %s",
                                PLUGIN_NAME, barcode)
                    page_structure_warned = True
                # Bail out early
                continue

            # Get tango.info TINT, e.g.
            # <a href="/00743216335725-1-4" title="TINT:00743216335725-1-4">
            tint = re.findall(tint_regex, trackinfo[8])
            if tint:
                # Normalize TINT by stripping all leading slashes and zeros
                tint = tint[0].lstrip("/").lstrip("0")
                albuminfo[tint] = {}
            else:
                # This really shouldn't happen
                log.warning("%s: No TINT found on webpage for barcode %s",
                            PLUGIN_NAME, barcode)
                continue

            # Get genre, e.g.
            # <a href="/genre.tango">tango</a>
            if trackinfo[3] != "-":
                genre = re.split("<|>", trackinfo[3])[2].title()
                albuminfo[tint]['genre'] = genre

            # Get date, e.g.
            # <a class="date" href="/1941-08-14">1941-08-14</a>
            if trackinfo[6] != "-":
                date = re.split("<|>", trackinfo[6])[2]
                albuminfo[tint]['date'] = date

            # Get singers, e.g.
            # <a href="/AlberDeluc">Alberto Castillo</a>
            if trackinfo[5] != "-":
                # Catch and strip <a> tags
                vocal = re.sub("<[^>]*>", "", trackinfo[5])
                albuminfo[tint]['vocal'] = vocal

        return albuminfo or None


tagger = TangoInfoTagger()
register_track_metadata_processor(tagger.add_tangoinfo_data)
