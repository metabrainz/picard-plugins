# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021, 2023 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

PLUGIN_NAME = 'Submit ISRC'
PLUGIN_AUTHOR = 'Bob Swift'
PLUGIN_DESCRIPTION = '''
<p>
Adds a right click option on an album to submit the ISRCs to the MusicBrainz server
specified in the Options.
</p><p>
To use this function, you must first match your files to the appropriate tracks for
a release.  Once this is done, but before you save your files if you have Picard set
to overwrite the 'isrc' tag in your files, right-click the release and select "Submit
ISRCs" in the "Plugins" section.  For each file that has a single valid ISRC in its
metadata, the ISRC will be added to the recording on the release if it does not
already exist.  Once all tracks for the release have been processed, the missing
ISRCs will be submitted to MusicBrainz.
</p><p>
If a file's metadata contains multiple ISRCs, such as if the file has already been
tagged, then no ISRCs will be submitted for that file.
</p><p>
If one of the files contains an invalid ISRC, or if the same ISRC appears in the
metadata for two or more files, then a notice will be displayed and the submission
process will be aborted.
</p><p>
When ISRCs have been submitted, a notice will be displayed showing whether or not
the submission was successful.
</p>
'''
PLUGIN_VERSION = '1.1'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.6', '2.9']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

import re

from picard import log, PICARD_VERSION
from picard.ui.itemviews import BaseAction, register_album_action
from picard.version import Version
from picard.webservice.api_helpers import MBAPIHelper, _wrap_xml_metadata
from PyQt5 import QtCore, QtWidgets

RE_VALIDATE_ISRC = re.compile(r'^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$')

NEW_MBAPIHelper = (PICARD_VERSION >= Version(2, 9, 0, 'beta', 2))

XML_HEADER = '<recording-list>'
XML_TEMPLATE = '<recording id="{0}"><isrc-list count="1"><isrc id="{1}" /></isrc-list></recording>'
XML_FOOTER = '</recording-list>'

Q_ERROR_CODES = {
    0: 'No error',
    1: "The remote server refused the connection (the server is not accepting requests).",
    2: "The remote server closed the connection prematurely, before the entire reply was received and processed.",
    3: "The remote host name was not found (invalid hostname).",
    4: "The connection to the remote server timed out.",
    5: "The operation was canceled via calls to abort() or close() before it was finished.",
    6: "The SSL/TLS handshake failed and the encrypted channel could not be established. The sslErrors() signal should have been emitted.",
    7: "The connection was broken due to disconnection from the network, however the system has initiated roaming to another access point. The request should be resubmitted and will be processed as soon as the connection is re-established.",
    8: "The connection was broken due to disconnection from the network or failure to start the network.",
    9: "The background request is not currently allowed due to platform policy.",
    10: "While following redirects, the maximum limit was reached.",
    11: "While following redirects, the network access API detected a redirect from a encrypted protocol (https) to an unencrypted one (http).",
    99: "An unknown network-related error was detected.",
    101: "The connection to the proxy server was refused (the proxy server is not accepting requests).",
    102: "The proxy server closed the connection prematurely, before the entire reply was received and processed.",
    103: "The proxy host name was not found (invalid proxy hostname).",
    104: "The connection to the proxy timed out or the proxy did not reply in time to the request sent.",
    105: "The proxy requires authentication in order to honour the request but did not accept any credentials offered (if any).",
    199: "An unknown proxy-related error was detected.",
    201: "The access to the remote content was denied (similar to HTTP error 403).",
    202: "The operation requested on the remote content is not permitted.",
    203: "The remote content was not found at the server (similar to HTTP error 404).",
    204: "The remote server requires authentication to serve the content but the credentials provided were not accepted (if any).",
    205: "The request needed to be sent again, but this failed for example because the upload data could not be read a second time.",
    206: "The request could not be completed due to a conflict with the current state of the resource.",
    207: "The requested resource is no longer available at the server.",
    299: "An unknown error related to the remote content was detected.",
    301: "The Network Access API cannot honor the request because the protocol is not known.",
    302: "The requested operation is invalid for this protocol.",
    399: "A breakdown in protocol was detected (parsing error, invalid or unexpected responses, etc.).",
    401: "The server encountered an unexpected condition which prevented it from fulfilling the request.",
    402: "The server does not support the functionality required to fulfill the request.",
    403: "The server is unable to handle the request at this time.",
    499: "An unknown error related to the server response was detected.",
}


def validate_isrc(isrc):
    """Verify that the provided ISRC matches the standard pattern for a valid ISRC.

    Args:
        isrc (str): ISRC to validate

    Returns:
        str: Properly formatted ISRC (upper case with no spaces or hyphens) if valid, otherwise None
    """
    formatted_isrc = str(isrc).upper().replace(' ', '').replace('-', '')
    if re.match(RE_VALIDATE_ISRC, formatted_isrc):
        return formatted_isrc
    return None


def show_popup(title, content, window=None):
    """Display a pop-up dialog.

    Args:
        title (str): Title for the pop-up dialog.
        content (str): Test to be displayed in the pop-up dialog..
        window (object, optional): Parent object for the dialog. Defaults to None.
    """
    QtWidgets.QMessageBox.information(
        window,
        title,
        content,
        QtWidgets.QMessageBox.Ok,
        QtWidgets.QMessageBox.Ok
    )


class SubmitAlbumISRCs(BaseAction):
    NAME = 'Submit ISRCs'

    def callback(self, album):
        if not album:
            log.error("{0}: No album specified for submitting ISRCs.".format(PLUGIN_NAME,))
            return

        log.info("{0}: Submitting ISRCs for: {1}".format(PLUGIN_NAME, album[0].metadata['album'],))
        if not album[0].tracks:
            log.debug("{0}: No tracks found in album: {1}".format(PLUGIN_NAME, album[0].metadata['album'],))
            show_popup('Error', 'No tracks found in the album.')
            return

        isrcs = {}
        multi_isrcs = []
        for track in album[0].tracks:
            if not track.files:
                continue
            audio_file = track.files[0]
            metadata = track.metadata
            file_metadata = audio_file.orig_metadata

            # No ISRC found in the file
            if 'isrc' not in file_metadata:
                continue

            # Get string of existing ISRCs on MusicBrainz
            if 'isrc' in metadata:
                mb_isrc = metadata['isrc'].upper()
            else:
                mb_isrc = ''

            # Get ISRC string from the file
            file_isrc = file_metadata['isrc']

            # Multiple ISRCs found in the file (don't process)
            if ';' in file_isrc:
                multi_isrcs.append('  {0} - {1}'.format(metadata['tracknumber'], metadata['title']))
                log.info("{0}: Multiple ISRCs found on track {1} (not processed): {2}".format(PLUGIN_NAME, metadata['tracknumber'], file_isrc))
                continue

            isrc = validate_isrc(file_isrc)

            # ISRC does not pass validation test
            if not isrc:
                log.debug("{0}: Invalid ISRC found on track {1}: {2}".format(PLUGIN_NAME, metadata['tracknumber'], file_isrc))
                show_popup('Error', "Invalid ISRC found on track {0}: '{1}'".format(metadata['tracknumber'], file_isrc))
                return

            # ISRC already found on another track for this album
            if isrc in isrcs:
                log.debug("{0}: Duplicate ISRC found on track {1}: {2}".format(PLUGIN_NAME, metadata['tracknumber'], file_isrc))
                show_popup('Error', "Duplicate ISRC found on track {0}: '{1}'".format(metadata['tracknumber'], file_isrc))
                return

            # ISRC already associated with that track (MusicBrainz recording)
            if isrc in mb_isrc:
                continue

            # New ISRC added for submission
            log.debug("{0}: Adding ISRC '{1}' for track {2} - \"{3}\"".format(PLUGIN_NAME, isrc, metadata['tracknumber'], metadata['title'],))
            isrcs[isrc] = metadata['musicbrainz_recordingid']

        if multi_isrcs:
            multiple_msg = '\n\nThe following track audio files contained multiple ISRCs (not submitted):\n' + '\n'.join(multi_isrcs)
        else:
            multiple_msg = ''

        # Save count of new ISRCs to display in success message
        self.isrc_count = len(isrcs)

        # Nothing to submit
        if not isrcs:
            log.debug("{0}: No new ISRCs found in album: {1}".format(PLUGIN_NAME, album[0].metadata['album'],))
            show_popup('Error', 'No new ISRCs found for the tracks in the album.{0}'.format(multiple_msg,))
            return

        if multiple_msg:
            show_popup('Submitting', 'Submitting {0} ISRC{1}.{2}'.format(self.isrc_count, '' if self.isrc_count == 1 else 's', multiple_msg,))

        # Build the xml data payload
        xml_items = [XML_HEADER]
        for isrc, recording in isrcs.items():
            xml_items.append(XML_TEMPLATE.format(recording, isrc))
        xml_items.append(XML_FOOTER)
        data = _wrap_xml_metadata(''.join(xml_items))

        # Initialize the MusicBrainz API Helper
        webservice = album[0].tagger.webservice
        helper = MBAPIHelper(webservice)

        # Set up parameters for the helper
        client_string = 'Picard_Plugin_{0}-v{1}'.format(PLUGIN_NAME, PLUGIN_VERSION).replace(' ', '_')
        handler = self.submission_handler
        path = '/recording' if NEW_MBAPIHelper else ['recording']
        params = {"client": client_string}

        return helper.post(path, data, handler, priority=True,
                         queryargs=params, parse_response_type="xml",
                         request_mimetype="application/xml; charset=utf-8")

    def submission_handler(self, document, reply, error):
        if not error:
            show_popup('Success', 'Successfully submitted {0} ISRC{1}.'.format(
                self.isrc_count,
                '' if self.isrc_count == 1 else 's',
            ))
            return

        # Decode response if necessary.
        xml_text = str(document, 'UTF-8') if isinstance(document, (bytes, bytearray, QtCore.QByteArray)) else str(document)

        # Build error text message from returned xml payload
        err_text = ''
        matches = re.findall(r'<text>(.*?)</text>', xml_text)
        if matches:
            err_text = '\n'.join(matches)
        else:
            err_text = ''

        # Use standard QNetworkReply error messages if no message was provided in the xml payload
        if not err_text:
            err_text = Q_ERROR_CODES[error] if error in Q_ERROR_CODES else 'There was no error message provided.'

        show_popup('Error', "There was an error processing the ISRC submission.  Please try again.\n\nError Code: {0}\n\n{1}".format(error, err_text))


register_album_action(SubmitAlbumISRCs())
