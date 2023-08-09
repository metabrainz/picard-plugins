import re
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox

# List of Qt network error codes.
# From "Submit ISRC" plugin - credit to rdswift.
q_error_codes = {
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


def network_submission_handler(document, reply, error, tagger):
    """
    The function handling the network response from MusicBrainz
    or QtNetwork, showing a message box if an error had occurred.

    Uses the network response handler code from rdswift's "Submit ISRC"
    plugin.
    """
    if error:
        # Error handling from rdswift's Submit ISRC plugin
        xml_text = str(document, 'UTF-8') if isinstance(document, (bytes, bytearray, QtCore.QByteArray)) else str(document)

        # Build error text message from returned xml payload
        err_text = ''
        matches = re.findall(r'<text>(.*?)</text>', xml_text)
        if matches:
            err_text = '\n'.join(matches)
        else:
            err_text = ''

        if not err_text:
            err_text = q_error_codes[error] if error in q_error_codes else 'There was no error message provided.'

        error = QMessageBox()
        error.setStandardButtons(QMessageBox.Ok)
        error.setDefaultButton(QMessageBox.Ok)
        error.setIcon(QMessageBox.Critical)
        error.setText(f"<p>An error has occurred submitting the tags to MusicBrainz.</p><p>{err_text}</p>")
        error.exec_()
    else:
        tagger.window.set_statusbar_message(
            "Successfully submitted tags to MusicBrainz."
        )
