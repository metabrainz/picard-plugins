PLUGIN_NAME = "Submit Folksonomy Tags"
PLUGIN_AUTHOR = "Flaky"
PLUGIN_DESCRIPTION = """
A plugin allowing submission of specific tags on tracks you own (defaults to <i>genre</i> and <i>mood</i>) as folksonomy tags on MusicBrainz. Supports submitting to recording, release, release group and release artist entities.

A MusicBrainz login is required to use this plugin. Log in first by going to the General options. Then, to use, right click on a track or release then go to <i>Plugins</i> and depending on what you want to submit, choose the option you want.

Uses code from rdswift's "Submit ISRC" plugin (specifically, the handling of the network response)
"""
PLUGIN_VERSION = '0.2.4'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.txt"

from picard import config, log
from picard.album import Album, Track
from picard.ui.itemviews import (BaseAction,
                                 register_album_action,
                                 register_track_action
                                 )
from picard.ui.options import OptionsPage, register_options_page
from picard.webservice.api_helpers import MBAPIHelper, _wrap_xml_metadata
from .ui_config import TagSubmitPluginOptionsUI
import re
import functools
from xml.sax.saxutils import escape
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

# Some internal settings.
# Don't change these unless you know what you're doing.
# You can change the tags you want to submit in the settings.
client_params = {
    "client": f"picard_plugin_{PLUGIN_NAME.replace(' ', '_')}-v{PLUGIN_VERSION}"
}
default_tags_to_submit = ['genre', 'mood']

# The options as saved in Picard.ini
config.BoolOption("setting", 'tag_submit_plugin_destructive', False)
config.BoolOption("setting", 'tag_submit_plugin_destructive_alert_acknowledged', False)
config.BoolOption("setting", 'tag_submit_plugin_aliases_enabled', False)
config.ListOption("setting", 'tag_submit_plugin_alias_list', [])
config.ListOption("setting", 'tag_submit_plugin_tags_to_submit', default_tags_to_submit)

def tag_submit_handler(document, reply, error, tagger):
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

def process_tag_aliases(tag_input):
    """
    Retrieves a string as input, and searches the tag alias tuple list
    for a match.
    """
    matched_tag_index = next(
        (tag for tag,
            tag_tuple in enumerate(config.setting['tag_submit_plugin_alias_list'])
            if tag_tuple[0] == tag_input.lower()),
        None
    )
    if matched_tag_index is not None:
        resolved_tag = config.setting['tag_submit_plugin_alias_list'][matched_tag_index][1]
        return resolved_tag
    else:
        return tag_input

def process_objs_to_track_list(objs):
    """
    Creates a track list out of Album/Track objects
    """
    track_list = []
    for item in objs:
        if isinstance(item, Track):
            track_list.append(item)
        elif isinstance(item, Album):
            if len(item.tracks) > 0:
                for track in item.tracks:
                    track_list.append(track)
    return track_list

# TODO handle artist
def handle_submit_process(tagger, track_list, target_tag):
    """
    Does some pre-processing before submitting tags. Handles tag deduplication
    and halting when inconsistent tagging is detected (i.e. the user is trying
    to submit tags to a release with the submitted track tags not being
    consistent.)
    """

    dict_key = ""
    tags_to_search = config.setting['tag_submit_plugin_tags_to_submit']

    # Variable to enable when inconsistent tagging is detected, which can be problematic for anything other than recordings.
    alert_inconsistent = True
    inconsistent_detected = False
    # Variable to enable alert if multiple MBIDs are associated, must be toggled.
    alert_multiple_mbids = False

    # TODO when Windows Picard updates with Python 3.10, use case/switch.
    if target_tag == "musicbrainz_recordingid":
        dict_key = "recording"
        alert_inconsistent = False
    elif target_tag == "musicbrainz_albumid":
        dict_key = "release"
    elif target_tag == "musicbrainz_releasegroupid":
        dict_key = "release-group"
    elif target_tag == "musicbrainz_albumartistid" or target_tag == "musicbrainz_artistid":
        dict_key = "artist"

    data = {dict_key: {}}

    last_tags = {"mbid": ""}
    banned_mbids = {
        # Any artist entities that can be applied to multiple artists go here.
        # SPAs generally fit the bill here.
        "f731ccc4-e22a-43af-a747-64213329e088", # artist: [anonymous]
        "33cf029c-63b0-41a0-9855-be2a3665fb3b", # artist: [data]
        "314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc", # artist: [dialogue]
        "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61", # artist: [no artist]
        "9be7f096-97ec-4615-8957-8d40b5dcbc41", # artist: [traditional]
        "125ec42a-7229-4250-afc5-e057484327fe", # artist: [unknown]
        "89ad4ac3-39f7-470e-963a-56509c546377", # artist: Various Artists
        "66ea0139-149f-4a0c-8fbf-5ea9ec4a6e49", # artist: [Disney]
        "a0ef7e1d-44ff-4039-9435-7d5fefdeecc9", # artist: [theatre]
        "80a8851f-444c-4539-892b-ad2a49292aa9", # artist: [language instruction]
        "",                                     # blank
    }

    for track in track_list:
        if track.files:
            for file in track.files:
                mbid_list = file.metadata.getall(target_tag)
                if len(mbid_list) > 1:
                    alert_multiple_mbids = True
                for mbid in mbid_list:
                    if mbid not in banned_mbids:
                        processed_tags = []
                        for tag in tags_to_search:
                            if file.metadata[tag]:
                                if tag not in last_tags:
                                    pass
                                else:
                                    # Flip the switch when current tag didn't match last tag on current mbid, on an entity that needs this checked.
                                    if (last_tags[tag] != file.metadata[tag]) and (last_tags["mbid"] == file.metadata[target_tag]) and alert_inconsistent:
                                        inconsistent_detected = True
                                # in any case, process the tags in case the user intends to go with it.
                                processed_tags.extend([tag.strip().lower() for tag
                                                    in re.split(";|/|,", file.metadata[tag])])
                                last_tags[tag] = file.metadata[tag]
                                last_tags["mbid"] = file.metadata[target_tag]
                        # If a track has multiple files associated to it, there may be duplicate tags.
                        processed_tags = list(set(processed_tags))
                        if processed_tags and mbid in data[dict_key]:
                            data[dict_key][mbid].extend(processed_tags)
                        else:
                            data[dict_key][mbid] = processed_tags
                    else:
                        log.info(f"Not submitting MBID {track.metadata[target_tag]} as it was found on 'do not submit' MBID set.")

    # Send an alert when, at the end of it all, inconsistent tagging was detected.
    if inconsistent_detected or alert_multiple_mbids:
        warning = QMessageBox()
        warning.setStandardButtons(QMessageBox.Ok|QMessageBox.Cancel)
        warning.setDefaultButton(QMessageBox.Cancel)
        warning.setIcon(QMessageBox.Warning)
        if inconsistent_detected and alert_multiple_mbids:
            warning.setText("""
            <p><b>WARNING: INCONSISTENT TAGGING AND SUBMISSION TO MULTIPLE MBIDS DETECTED.</b></p>
            <p>You are trying to apply different tags to multiple MusicBrainz entities.</p>
            <p>This isn't a use case this plugin supports whatsoever due to the potential for
            wrong tags to be unintentionally assigned, but detects and warns just in case.</p>
            <p>If this was intentional, click OK. Otherwise, click Cancel.</p>
            """)
        elif inconsistent_detected:
            warning.setText("""
            <p><b>WARNING: INCONSISTENT TAGGING DETECTED.</b></p>
            <p>You are trying to apply multiple tags to one entity, which benefits more from
            having the same tags across all tracks when submitting tags via this plugin.</p>
            <p>If you intended to have tracks in a release to have different submitted tags,
            it's better to cancel this attempt and choose the recording option.
            If you didn't, you should apply the same tag across all tracks.</p>
            <p>If this was intentional, click OK. Otherwise, click Cancel.</p>
            """)
        elif alert_multiple_mbids:
            warning.setText("""
            <p><b>MULTIPLE MBIDS DETECTED.</b></p>
            <p>You are trying to apply a tag to multiple MusicBrainz entities.</p>
            <p>This isn't a use case this plugin supports whatsoever due to the potential for
            wrong tags to be unintentionally assigned, but detects and warns just in case.</p>
            <p>If this was intentional, click OK. Otherwise, click Cancel.</p>
            """)
        result = warning.exec_()
        if result == QMessageBox.Ok:
            upload_tags_to_mbz(data, tagger)
        else:
            tagger.window.set_statusbar_message(
                "Tag submission halted by user request."
            )
    else:
        upload_tags_to_mbz(data, tagger)

def upload_tags_to_mbz(data, tagger):
    """
    Generates the XML from the data retrieved, and then uploads it to MusicBrainz.
    """
    helper = MBAPIHelper(tagger.webservice)

    empty_data = {
        "<recording-list></recording-list>",
        "<release-list></release-list>",
        "<release-group-list></release-group-list>",
        "<artist-list></artist-list>"
    }

    xml_data = []
    upvote_tag_fill = ' vote="upvote"' if not config.setting['tag_submit_plugin_destructive'] else ''
    for key in data:
        # start the list
        xml_data.append(f"<{key}-list>")
        for mbid in data[key]:
            # deduplicate the list of genres so no redundant tags are sent.
            data[key][mbid] = list(set(data[key][mbid]))
            # start the user tag list
            xml_data.extend([f'<{key} id="{mbid}">', "<user-tag-list>"])
            # add the tags
            for tag in data[key][mbid]:
                xml_data.append(f'<user-tag{upvote_tag_fill}><name>{escape(process_tag_aliases(tag.lower()))}</name></user-tag>')
            # close the user tag list
            xml_data.extend(["</user-tag-list>", f"</{key}>"])
        # close the list
        xml_data.append(f"</{key}-list>")
    # make the string that would become our submitted XML.
    final_xml = ''.join(xml_data)
    log.info(final_xml)

    if final_xml not in empty_data:
    # post it to MusicBrainz
        tagger.window.set_statusbar_message(
                "Submitting tags to MusicBrainz..."
                )
        submitted_xml = _wrap_xml_metadata(''.join(xml_data))
        helper.post(
            ['tag'],
            submitted_xml,
            functools.partial(tag_submit_handler, tagger=tagger),
            priority=True,
            queryargs=client_params,
            parse_response_type="xml",
            request_mimetype="application/xml; charset=utf-8"
        )
    else:
        tagger.window.set_statusbar_message(
            "Not submitting to MusicBrainz due to empty data."
            )


class TagSubmitPlugin_OptionsPage(OptionsPage):
    NAME = "tag_submit_plugin"
    TITLE = "Tag Submission Plugin"
    PARENT = "plugins"
    HELP_URL = ""

    def __init__(self, parent=None):
        super().__init__()
        self.ui = TagSubmitPluginOptionsUI(self)
        self.destructive_acknowledgement = config.setting['tag_submit_plugin_destructive_alert_acknowledged']
        self.ui.overwrite_radio_button.clicked.connect(self.on_destructive_selected)

    def on_destructive_selected(self):
        if not config.setting['tag_submit_plugin_destructive_alert_acknowledged']:
            warning = QMessageBox()
            warning.setStandardButtons(QMessageBox.Ok)
            warning.setDefaultButton(QMessageBox.Ok)
            warning.setIcon(QMessageBox.Warning)
            warning.setText("<p><b>WARNING: BY SELECTING TO OVERWRITE ALL TAGS, THIS MEANS <i>ALL</i> TAGS.</b></p><p>By enabling this option, you acknowledge that you may lose the tags already saved online from the tracks you process via this plugin. This alert will only be displayed once before you save.</p><p>If you do not want this behaviour, select the maintain option.</p>")
            warning.exec_()
            config.setting['tag_submit_plugin_destructive_alert_acknowledged'] = True

    def load(self):
        # Destructive option
        if config.setting['tag_submit_plugin_destructive']:
            self.ui.overwrite_radio_button.setChecked(True)
        else:
            self.ui.keep_radio_button.setChecked(True)

        self.ui.tags_to_save_textbox.setText(
            '; '.join(config.setting['tag_submit_plugin_tags_to_submit'])
            )

        # Aliases enabled option
        self.ui.tag_alias_groupbox.setChecked(
            config.setting['tag_submit_plugin_aliases_enabled']
        )

        # Alias list
        if 'tag_submit_plugin_alias_list' in config.setting:
            log.info("Alias list exists! Let's populate the table.")
            for alias_tuple in config.setting['tag_submit_plugin_alias_list']:
                self.ui.add_row(alias_tuple[0], alias_tuple[1])
            self.ui.tag_alias_table.resizeColumnsToContents()

        config.setting['tag_submit_plugin_destructive_alert_acknowledged'] = self.destructive_acknowledgement

    def save(self):
        config.setting['tag_submit_plugin_destructive'] = self.ui.overwrite_radio_button.isChecked()
        config.setting['tag_submit_plugin_aliases_enabled'] = self.ui.tag_alias_groupbox.isChecked()

        tag_textbox_text = self.ui.tags_to_save_textbox.text()
        if tag_textbox_text:
            config.setting['tag_submit_plugin_tags_to_submit'] = [
                tag.strip() for tag in tag_textbox_text.split(';')
                ]
        else:
            config.setting['tag_submit_plugin_tags_to_submit'] = default_tags_to_submit

        if config.setting['tag_submit_plugin_aliases_enabled']:
            new_alias_list = self.ui.rows_to_tuple_list()
            log.info(new_alias_list)
            config.setting['tag_submit_plugin_alias_list'] = new_alias_list

class SubmitTrackTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (recording)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_recordingid"
            )

class SubmitReleaseTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_albumid"
            )

class SubmitRGTagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release group)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_releasegroupid"
            )

class SubmitRATagsMenuAction(BaseAction):
    NAME = 'Submit tags to MusicBrainz (release artist)'

    def callback(self, objs):
        handle_submit_process(
            objs[0].tagger,
            process_objs_to_track_list(objs),
            "musicbrainz_albumartistid"
            )

register_options_page(TagSubmitPlugin_OptionsPage)
register_album_action(SubmitTrackTagsMenuAction())
register_track_action(SubmitTrackTagsMenuAction())
register_album_action(SubmitReleaseTagsMenuAction())
register_track_action(SubmitReleaseTagsMenuAction())
register_album_action(SubmitRGTagsMenuAction())
register_track_action(SubmitRGTagsMenuAction())
register_album_action(SubmitRATagsMenuAction())
register_track_action(SubmitRATagsMenuAction())
