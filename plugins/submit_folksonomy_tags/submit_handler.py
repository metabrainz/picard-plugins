import functools
import re
from picard import config, log, PICARD_VERSION
from picard.album import Album, Track
from picard.version import Version
from picard.webservice.api_helpers import MBAPIHelper, _wrap_xml_metadata
from PyQt5.QtWidgets import QMessageBox
from xml.sax.saxutils import escape
from .network import network_submission_handler

# MBAPIHelper for version 2.9 and newer
NEW_MBAPIHelper = (PICARD_VERSION >= Version(2, 9, 0, 'beta', 2))

# Variable to enable when inconsistent tagging is detected, which can be problematic for anything other than recordings.
alert_inconsistent = False
inconsistent_detected = False
alert_multiple_mbids = False

banned_mbids = {
    # Any artist entities that can be applied to multiple artists go here.
    # SPAs generally fit the bill here.
    "f731ccc4-e22a-43af-a747-64213329e088",  # artist: [anonymous]
    "33cf029c-63b0-41a0-9855-be2a3665fb3b",  # artist: [data]
    "314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc",  # artist: [dialogue]
    "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61",  # artist: [no artist]
    "9be7f096-97ec-4615-8957-8d40b5dcbc41",  # artist: [traditional]
    "125ec42a-7229-4250-afc5-e057484327fe",  # artist: [unknown]
    "89ad4ac3-39f7-470e-963a-56509c546377",  # artist: Various Artists
    "66ea0139-149f-4a0c-8fbf-5ea9ec4a6e49",  # artist: [Disney]
    "a0ef7e1d-44ff-4039-9435-7d5fefdeecc9",  # artist: [theatre]
    "80a8851f-444c-4539-892b-ad2a49292aa9",  # artist: [language instruction]
    "",                                      # blank
}

tag_bindings = {
    # Bindings from tags to their equivalent XML entity.
    "musicbrainz_recordingid": "recording",
    "musicbrainz_albumid": "release",
    "musicbrainz_releasegroupid": "release-group",
    "musicbrainz_albumartistid": "artist",
    "musicbrainz_artistid": "artist"
}


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


def handle_submit_process(tagger, track_list, target_tag, client_params):
    global alert_inconsistent, inconsistent_detected, alert_multiple_mbids
    tags_to_search = config.setting['tag_submit_plugin_tags_to_submit']

    # Reset all of the global inconsistency variables for a new submission process.
    alert_inconsistent = False if target_tag == "musicbrainz_recordingid" else True
    inconsistent_detected = False
    alert_multiple_mbids = False

    file_list = process_tracks_to_file_list(track_list, target_tag)
    data = process_file_list_to_tag_dict(file_list, target_tag, tags_to_search)
    inconsistency_check_passed = inconsistency_alert_check()
    if inconsistency_check_passed:
        upload_tags_to_mbz(data, tagger, client_params)
    else:
        tagger.window.set_statusbar_message(
            "Tag submission halted by user request."
        )


def process_tracks_to_file_list(track_list, target_tag):
    """
    Processes a track list to just a file list, checking if
    the MBID is in the banned list and if alert_multiple_mbids
    needs to be checked.
    """
    global inconsistent_detected, alert_multiple_mbids

    file_list = []
    for track in track_list:
        for file in track.files if track.files else []:
            mbid_list = file.metadata.getall(target_tag)
            alert_multiple_mbids = True if (
                len(mbid_list) > 1 and alert_inconsistent) else False
            for mbid in mbid_list:
                if mbid not in banned_mbids:
                    file_list.append(file)
                else:
                    log.info(
                        f"Not submitting MBID {track.metadata[target_tag]} as it was found on 'do not submit' MBID set."
                    )
    return file_list


def process_file_list_to_tag_dict(file_list, target_tag, tags_to_search):
    """
    Process tags from a file list to a dictionary of tag data for submission,
    triggering variables if there is inconsistent tagging.
    """
    global alert_inconsistent, inconsistent_detected, alert_multiple_mbids
    dict_key = tag_bindings[target_tag]
    data = {dict_key: {}}
    last_tags = {"mbid": ""}

    for file in file_list:
        mbid_list = file.metadata.getall(target_tag)
        for mbid in mbid_list:
            processed_tags = []
            for tag in tags_to_search:
                if file.metadata[tag]:
                    # perform a check to make sure the tagging is consistent, otherwise trip the inconsistent_detected alarm.
                    if tag not in last_tags:
                        pass
                    elif (last_tags[tag] != file.metadata[tag]) and (last_tags["mbid"] == file.metadata[target_tag]):
                        inconsistent_detected = True
                    # in any case, process the tags in case the user intends to go with it.
                    processed_tags.extend([tag.strip().lower() for tag
                                        in re.split(";|/|,", file.metadata[tag])])
                    # Fill the last tags variables for the inconsistency check.
                    last_tags[tag] = file.metadata[tag]
                    last_tags["mbid"] = file.metadata[target_tag]
            # If a track has multiple files associated to it, there may be duplicate tags.
            processed_tags = list(set(processed_tags))
            if mbid in data[dict_key]:
                data[dict_key][mbid].extend(processed_tags)
            else:
                data[dict_key][mbid] = processed_tags
    return data


def inconsistency_alert_check():
    """
    Returns False if the user cancels the inconsistency alert and therefore
    cancels the upload process.

    Returns True if there are no problems or if the user has verified that
    they want to submit the tags in a way not really supported by this
    plugin.
    """
    global alert_inconsistent, inconsistent_detected, alert_multiple_mbids

    if ((not alert_inconsistent)
        or (not inconsistent_detected and not alert_multiple_mbids)):
        return True

    warning = QMessageBox()
    warning.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    warning.setDefaultButton(QMessageBox.Cancel)
    warning.setIcon(QMessageBox.Warning)
    warning_text = ""
    if inconsistent_detected and alert_multiple_mbids:
        warning_text = """
        <p><b>WARNING: INCONSISTENT TAGGING AND SUBMISSION TO MULTIPLE MBIDS DETECTED.</b></p>
        <p>You are trying to apply different tags to multiple MusicBrainz entities.</p>
        <p>This isn't a use case this plugin supports whatsoever due to the potential for
        wrong tags to be unintentionally assigned, but detects and warns just in case.</p>
        """
    elif inconsistent_detected:
        warning_text = """
        <p><b>WARNING: INCONSISTENT TAGGING DETECTED.</b></p>
        <p>You are trying to apply multiple tags to one entity, which benefits more from
        having the same tags across all tracks when submitting tags via this plugin.</p>
        <p>If you intended to have tracks in a release to have different submitted tags,
        it's better to cancel this attempt and choose the recording option.
        If you didn't, you should apply the same tag across all tracks.</p>
        """
    elif alert_multiple_mbids:
        warning_text = """
        <p><b>MULTIPLE MBIDS DETECTED.</b></p>
        <p>You are trying to apply a tag to multiple MusicBrainz entities.</p>
        <p>This isn't a use case this plugin supports whatsoever due to the potential for
        wrong tags to be unintentionally assigned, but detects and warns just in case.</p>
        """
    warning_text += "<p>If this was intentional, click OK. Otherwise, click Cancel.</p>"
    warning.setText(warning_text)
    result = warning.exec_()
    if result == QMessageBox.Ok:
        return True
    else:
        return False


def upload_tags_to_mbz(data, tagger, client_params):
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
        path = '/tag' if NEW_MBAPIHelper else ['tag']
        helper.post(
            path,
            submitted_xml,
            functools.partial(network_submission_handler, tagger=tagger),
            priority=True,
            queryargs=client_params,
            parse_response_type="xml",
            request_mimetype="application/xml; charset=utf-8"
        )
    else:
        tagger.window.set_statusbar_message(
            "Not submitting to MusicBrainz due to empty data."
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
