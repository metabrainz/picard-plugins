# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Mark Evens
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

PLUGIN_NAME = u'Classical Extras'
PLUGIN_AUTHOR = u'Mark Evens'
PLUGIN_DESCRIPTION = u"""Classical Extras provides tagging enhancements for Picard and, in particular,
utilises MusicBrainz’s hierarchy of works to provide work/movement tags. All options are set through a
user interface in Picard options->plugins. This interface provides separate sections
to enhance artist/performer tags, works and parts, genres and also allows for a generalised
"tag mapping" (simple scripting).
While it is designed to cater for the complexities of classical music tagging,
it may also be useful for other music which has more than just basic song/artist/album data.
<br /><br />
The options screen provides five tabs for users to control the tags produced:
<br /><br />
1. Artists: Options as to whether artist tags will contain standard MB names, aliases or as-credited names.
Ability to include and annotate names for specialist roles (chorus master, arranger, lyricist etc.).
Ability to read lyrics tags on the file which has been loaded and assign them to track and album levels if required.
(Note: Picard will not normally process incoming file tags).
<br /><br />
2. Works and parts: The plugin will build a hierarchy of works and parts (e.g. Work -> Part -> Movement or
Opera -> Act -> Number) based on the works in MusicBrainz's database. These can then be displayed in tags in a variety
of ways according to user preferences. Furthermore partial recordings, medleys, arrangements and collections of works
are all handled according to user choices. There is a processing overhead for this at present because MusicBrainz limits
look-ups to one per second.
<br /><br />
3. Genres etc.: Options are available to customise the source and display of information relating to genres,
instruments, keys, work dates and periods. Additional capabilities are provided for users of Muso (or others who
provide the relevant XML files) to use pre-existing databases of classical genres, classical composers and classical
periods.
<br /><br />
4. Tag mapping: in some ways, this is a simple substitute for some of Picard's scripting capability. The main advantage
 is that the plugin will remember what tag mapping you use for each release (or even track).
<br /><br />
5. Advanced: Various options to control the detailed processing of the above.
<br /><br />
All user options can be saved on a per-album (or even per-track) basis so that tweaks can be used to deal with
inconsistencies in the MusicBrainz data (e.g. include English titles from the track listing where the MusicBrainz works
are in the composer's language and/or script).
Also existing file tags can be processed (not possible in native Picard).
<br /><br />
See the readme file <a href="https://github.com/MetaTunes/picard-plugins/tree/metabrainz/2.0/plugins/classical_extras">
on GitHub here</a> for full details.
"""

########################
# DEVELOPERS NOTES: ####
########################
#  This plugin contains 3 classes:
#
# I. ("EXTRA ARTISTS") Create sorted fields for all performers. Creates a number of variables with alternative values
# for "artists" and "artist".
# Creates an ensemble variable for all ensemble-type performers.
# Also creates matching sort fields for artist and artists.
# Additionally create tags for artist types which are not normally created in Picard - particularly for classical music
#  (notably instrument arrangers).
#
# II. ("PART LEVELS" [aka Work Parts]) Create tags for the hierarchy of works which contain a given track recording
# - particularly for classical music'
# Variables provided for each work level, with implied part names
# Mixed metadata provided including work and title elements
#
# III. ("OPTIONS") Allows the user to set various options including what tags will be written
# (otherwise the classes above will just write outputs to "hidden variables")
#
# The main control routine is at the end of the module

PLUGIN_VERSION = '2.0.12'
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.ui.options import register_options_page, OptionsPage
from picard.plugins.classical_extras.ui_options_classical_extras import Ui_ClassicalExtrasOptionsPage
import picard.plugins.classical_extras.suffixtree
from picard import config, log
from picard.config import ConfigSection, BoolOption, IntOption, TextOption
from picard.util import LockableObject, uniqify

# note that in 2.0 picard.webservice changed to picard.util.xml
from picard.util.xml import XmlNode
from picard.util import translate_from_sortname
from picard.metadata import register_track_metadata_processor, Metadata
from functools import partial
from datetime import datetime
import collections
import re
import unicodedata
import json
import copy
import os
from PyQt5.QtCore import QXmlStreamReader
from picard.const import USER_DIR
import operator
import ast
import picard.plugins.classical_extras.const



##########################
# MODULE-WIDE COMPONENTS #
##########################
# CONSTANTS
# N.B. Constants with long definitions are set in const.py
DATE_SEP = '-'

# COMMONLY USED REGEX
ROMAN_NUMERALS = r'\b((?=[MDCLXVI])(M{0,4}(CM|CD|D?)?C{0,3}(XC|XL|L?)?X{0,3}(IX|IV|V?)?I{0,3}))(?:\.|\-|:|;|,|\s|$)'
ROMAN_NUMERALS_AT_START = r'^\W*' + ROMAN_NUMERALS
RE_ROMANS = re.compile(ROMAN_NUMERALS, re.IGNORECASE)
RE_ROMANS_AT_START = re.compile(ROMAN_NUMERALS_AT_START, re.IGNORECASE)
# KEYS
RE_NOTES = r'(\b[ABCDEFG])'
RE_ACCENTS = r'(\-sharp(?:\s+|\b)|\-flat(?:\s+|\b)|\ssharp(?:\s+|\b)|\sflat(?:\s+|\b)|\u266F(?:\s+|\b)|\u266D(?:\s+|\b)|(?:[:,.]?\s+|$|\-))'
RE_SCALES = r'(major|minor)?(?:\b|$)'
RE_KEYS = re.compile(
    RE_NOTES + RE_ACCENTS + RE_SCALES,
    re.UNICODE | re.IGNORECASE)

# LOGGING

# If logging occurs before any album is loaded, the startup log file will
# be written
log_files = collections.defaultdict(dict)
# entries are release-ids: to keep track of which log files are open
release_status = collections.defaultdict(dict)
# release_status[release_id]['works'] = True indicates that we are still processing works for release_id
# & similarly for 'artists'
# release_status[release_id]['start'] holds start time of release processing
# release_status[release_id]['name'] holds the album name
# release_status[release_id]['lookups'] holds number of lookups for this release
# release_status[release_id]['file_objects'] holds a cumulative list of file objects (tagger seems a bit unreliable)
# release_status[release_id]['file_found'] = False indicates that "No file
# with matching trackid" has (yet) been found


def write_log(release_id, log_type, message, *args):
    """
    Custom logging function - if log_info is set, all messages will be written to a custom file in a 'Classical_Extras'
    subdirectory in the same directory as the main Picard log. A different file is used for each album,
    to aid in debugging - the log file is release_id.log. Any startup messages (i.e. before a release has been loaded)
    are written to session.log. Summary information for each release is also written to session.log even if log_info
    is not set.
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param log_type: 'error', 'warning', 'debug' or 'info'
    :param message: string, e.g. 'error message for workid: %s'
    :param args: arguments for parameters in string, e.g. if workId then str(workId) will replace %s in the above
    :return:
    """
    options = config.setting
    if not isinstance(message, str):
        msg = repr(message)
    else:
        msg = message
    if args:
        msg = msg % args

    if options["log_info"] or log_type == "basic":
        # if log_info is True, all log messages will be written to the custom log, regardless of other log_... settings
        # basic session log will always be written (summary of releases and
        # processing times)
        filename = release_id + ".log"
        log_dir = os.path.join(USER_DIR, "Classical_Extras")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        if release_id not in log_files:
            try:
                if release_id == 'session':
                    log_file = open(
                        os.path.join(
                            log_dir,
                            filename),
                        'w',
                        encoding='utf8',
                        buffering=1)
                    # buffering=1 so that session log (low volume) is up to
                    # date even if not closed
                else:
                    log_file = open(
                        os.path.join(
                            log_dir,
                            filename),
                        'w',
                        encoding='utf8')  # , buffering=1)
                    # default buffering for speed, buffering = 1 for currency
                log_files[release_id] = log_file
                log_file.write(
                    PLUGIN_NAME +
                    ' Version:' +
                    PLUGIN_VERSION +
                    '\n')
                if release_id == 'session':
                    log_file.write('session' + '\n')
                else:
                    log_file.write('Release id: ' + release_id + '\n')
                    if release_id in release_status and 'name' in release_status[release_id]:
                        log_file.write(
                            'Album name: ' + release_status[release_id]['name'] + '\n')
            except IOError:
                log.error('Unable to open file %s for writing log', filename)
                return
        else:
            log_file = log_files[release_id]
        try:
            log_file.write(log_type[0].upper() + ': ')
            log_file.write(str(datetime.now()) + ' : ')
            log_file.write(msg)
            log_file.write("\n")
        except IOError:
            log.error('Unable to write to log file %s', filename)
            return
    # Only debug, warning and error messages will be written to the main
    # Picard log, if those options have been set
    if log_type != 'info' and log_type != 'basic':  # i.e. non-custom log items
        message2 = PLUGIN_NAME + ': ' + message
    else:
        message2 = message
    if log_type == 'debug' and options["log_debug"]:
        if release_id in release_status and 'debug' in release_status[release_id]:
            add_list_uniquely(release_status[release_id]['debug'], msg)
        else:
            release_status[release_id]['debug'] = [msg]
        log.debug(message2, *args)
    if log_type == 'warning' and options["log_warning"]:
        if release_id in release_status and 'warnings' in release_status[release_id]:
            add_list_uniquely(release_status[release_id]['warnings'], msg)
        else:
            release_status[release_id]['warnings'] = [msg]
        if args:
            log.warning(message2, *args)
        else:
            log.warning(message2)
    if log_type == 'error' and options["log_error"]:
        if release_id in release_status and 'errors' in release_status[release_id]:
            add_list_uniquely(release_status[release_id]['errors'], msg)
        else:
            release_status[release_id]['errors'] = [msg]
        if args:
            log.error(message2, *args)
        else:
            log.error(message2)


def close_log(release_id, caller):
    # close the custom log file if we are done
    if release_id == 'session':   # shouldn't happen but, just in case, don't close the session log
        return
    if caller in ['works', 'artists']:
        release_status[release_id][caller] = False
    if (caller == 'works' and release_status[release_id]['artists']) or \
            (caller == 'artists' and release_status[release_id]['works']):
        # log.error('exiting close_log. only %s done', caller) # debug line
        return
    duration = 'N/A'
    lookups = 'N/A'
    artists_time = 0
    works_time = 0
    lookup_time = 0
    album_process_time = 0
    if release_id in release_status:
        duration = datetime.now() - release_status[release_id]['start']
        lookups = release_status[release_id]['lookups']
        done_lookups = release_status[release_id]['done-lookups']
        lookup_time = done_lookups - release_status[release_id]['start']
        album_process_time = duration - lookup_time
        artists_time = release_status[release_id]['artists-done'] - \
            release_status[release_id]['start']
        works_time = release_status[release_id]['works-done'] - \
            release_status[release_id]['start']
        del release_status[release_id]['start']
        del release_status[release_id]['lookups']
        del release_status[release_id]['done-lookups']
        del release_status[release_id]['artists-done']
        del release_status[release_id]['works-done']
    if release_id in log_files:
        write_log(
            release_id,
            'info',
            'Duration = %s. Number of lookups = %s.',
            duration,
            lookups)
        write_log(release_id, 'info', 'Closing log file for %s', release_id)
        log_files[release_id].close()
        del log_files[release_id]
    if 'session' in log_files and release_id in release_status:
        write_log(
            'session',
            'basic',
            '\n Completed processing release id %s. Details below:-',
            release_id)
        if 'name' in release_status[release_id]:
            write_log('session', 'basic', 'Album name %s',
                      release_status[release_id]['name'])
        if 'errors' in release_status[release_id]:
            write_log(
                'session',
                'basic',
                '-------------------- Errors --------------------')
            for error in release_status[release_id]['errors']:
                write_log('session', 'basic', error)
            del release_status[release_id]['errors']
        if 'warnings' in release_status[release_id]:
            write_log(
                'session',
                'basic',
                '-------------------- Warnings --------------------')
            for warning in release_status[release_id]['warnings']:
                write_log('session', 'basic', warning)
            del release_status[release_id]['warnings']
        if 'debug' in release_status[release_id]:
            write_log(
                'session',
                'basic',
                '-------------------- Debug log --------------------')
            for debug in release_status[release_id]['debug']:
                write_log('session', 'basic', debug)
            del release_status[release_id]['debug']
        write_log(
            'session',
            'basic',
            'Duration = %s. Artists time = %s. Works time = %s. Of which: Lookup time = %s. '
            'Album-process time = %s. Number of lookups = %s.',
            duration,
            artists_time,
            works_time,
            lookup_time,
            album_process_time,
            lookups)
    if release_id in release_status:
        del release_status[release_id]


# FILE READING AND OBJECT PARSING

_node_name_re = re.compile('[^a-zA-Z0-9]')


def _node_name(n):
    return _node_name_re.sub('_', str(n))


def _read_xml(stream):
    document = XmlNode()
    current_node = document
    path = []
    while not stream.atEnd():
        stream.readNext()
        if stream.isStartElement():
            node = XmlNode()
            attrs = stream.attributes()
            for i in range(attrs.count()):
                attr = attrs.at(i)
                node.attribs[_node_name(attr.name())] = str(attr.value())
            current_node.append_child(_node_name(stream.name()), node)
            path.append(current_node)
            current_node = node
        elif stream.isEndElement():
            current_node = path.pop()
        elif stream.isCharacters():
            current_node.text += str(stream.text())
    return document


def parse_data(release_id, obj, response_list, *match):
    """
    This function takes any XmlNode object, or list thereof, or a JSON object
    and extracts a list of all objects exactly matching the hierarchy listed in match.
    match should contain list of each node in hierarchical sequence, with no gaps in the sequence
     of nodes, to lowest level required.
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param obj: an XmlNode or JSON object, list or dictionary containing nodes
    :param response_list: working memory for recursive calls
    :param match: list of items to search for in node (see detailed notes below)
    :return: a list of matching items (always a list, even if only one item)

    Insert attribs.attribname:attribvalue in the list to select only branches where attribname
     is attribvalue. (Omit the attribs prefix if the obj is JSON)
    Insert childname.text:childtext in the list to select only branches where
     a sibling with childname has text childtext.
      (Note: childname can be a dot-list if the text is more than one level down - e.g. child1.child2
      # TODO - Check this works fully )
    """
    if '!log' in response_list:
        DEBUG = True
        INFO = True
    else:
        DEBUG = False
        INFO = False
    # Normally logging options are off as these can be VERY wordy
    # They can be turned on by using !log in the call

    # XmlNode instances are not iterable, so need to convert to dict
    if isinstance(obj, XmlNode):
        obj = obj.__dict__
    if DEBUG or INFO:
        write_log(release_id, 'debug', 'Parsing data - looking for %s', match)
    if INFO:
        write_log(release_id, 'info', 'Looking in object: %s', obj)
    if isinstance(obj, list):
        objlen = len(obj)
        for i, item in enumerate(obj):
            if isinstance(item, XmlNode):
                item = item.__dict__
            if INFO:
                write_log(
                    release_id,
                    'info',
                    'Getting response for list item no.%s of %s - object is: %s',
                    i + 1,
                    objlen,
                    item)
            parse_data(release_id, item, response_list, *match)
            if INFO:
                write_log(
                    release_id,
                    'info',
                    'response_list for list item no.%s of %s is %s',
                    i + 1,
                    objlen,
                    response_list)
        return response_list
    elif isinstance(obj, dict):
        if match[0] in obj:
            if len(match) == 1:
                response = obj[match[0]]
                if response is not None:  # To prevent adding NoneTypes to list
                    response_list.append(response)
                if INFO:
                    write_log(
                        release_id,
                        'info',
                        'response_list (last match item): %s',
                        response_list)
            else:
                match_list = list(match)
                match_list.pop(0)
                parse_data(release_id, obj[match[0]],
                           response_list, *match_list)
                if INFO:
                    write_log(
                        release_id,
                        'info',
                        'response_list (passing up): %s',
                        response_list)
            return response_list
        elif ':' in match[0]:
            test = match[0].split(':')
            match2 = test[0].split('.')
            test_data = parse_data(release_id, obj, [], *match2)
            if INFO:
                write_log(
                    release_id,
                    'info',
                    'Value comparison - looking in %s for value %s',
                    test_data,
                    test[1])
            if len(test) > 1:
                # latter is because Booleans are stored as such, not as
                # strings, in JSON
                if (test[1] in test_data) or (
                        (test[1] == 'True') in test_data):
                    if len(match) == 1:
                        response = obj
                        if response is not None:
                            response_list.append(response)
                    else:
                        match_list = list(match)
                        match_list.pop(0)
                        parse_data(release_id, obj, response_list, *match_list)
            else:
                parse_data(release_id, obj, response_list, *match2)
            if INFO:
                write_log(
                    release_id,
                    'info',
                    'response_list (from value look-up): %s',
                    response_list)
            return response_list
        else:
            if 'children' in obj:
                parse_data(release_id, obj['children'], response_list, *match)
            if INFO:
                write_log(
                    release_id,
                    'info',
                    'response_list (from children): %s',
                    response_list)
            return response_list
    else:
        if INFO:
            write_log(
                release_id,
                'info',
                'response_list (obj is not a list or dict): %s',
                response_list)
        return response_list


def create_dict_from_ref_list(options, release_id, ref_list, keys, tags):
    ref_dict_list = []
    for refs in ref_list:
        for ref in refs:
            parsed_refs = [
                parse_data(
                    release_id,
                    ref,
                    [],
                    t,
                    'text') for t in tags]
            ref_dict_list.append(dict(zip(keys, parsed_refs)))
    return ref_dict_list


def get_references_from_file(release_id, path, filename):
    """
    Lookup Muso Reference.xml or similar
    :param release_id: name of log file
    :param path: Reference file path
    :param filename: Reference file name
    :return:
    """
    options = config.setting
    composer_dict_list = []
    period_dict_list = []
    genre_dict_list = []
    xml_file = None
    try:
        xml_file = open(os.path.join(path, filename), encoding="utf8")
        reply = xml_file.read()
        xml_file.close()
        document = _read_xml(QXmlStreamReader(reply))
        # Composers
        composer_list = parse_data(
            release_id, document, [], 'ReferenceDB', 'Composer')
        keys = ['name', 'sort', 'birth', 'death', 'country', 'core']
        tags = ['Name', 'Sort', 'Birth', 'Death', 'CountryCode', 'Core']
        composer_dict_list = create_dict_from_ref_list(
            options, release_id, composer_list, keys, tags)
        # Periods
        period_list = parse_data(
            release_id,
            document,
            [],
            'ReferenceDB',
            'ClassicalPeriod')
        keys = ['name', 'start', 'end']
        tags = ['Name', 'Start_x0020_Date', 'End_x0020_Date']
        period_dict_list = create_dict_from_ref_list(
            options, release_id, period_list, keys, tags)
        # Genres
        genre_list = parse_data(
            release_id,
            document,
            [],
            'ReferenceDB',
            'ClassicalGenre')
        keys = ['name']
        tags = ['Name']
        genre_dict_list = create_dict_from_ref_list(
            options, release_id, genre_list, keys, tags)

    except (IOError, FileNotFoundError, UnicodeDecodeError):
        if options['cwp_muso_genres'] or options['cwp_muso_classical'] or options['cwp_muso_dates'] or options['cwp_muso_periods']:
            write_log(
                release_id,
                'error',
                'File %s does not exist or is corrupted',
                os.path.join(
                    path,
                    filename))
    finally:
        if xml_file:
            xml_file.close()
    return {
            'composers': composer_dict_list,
            'periods': period_dict_list,
            'genres': genre_dict_list}

# OPTIONS


def get_preserved_tags():
    preserved = config.setting["preserved_tags"]
    if isinstance(preserved, str):
        preserved = [x.strip() for x in preserved.split(',')]
    return preserved


def get_options(release_id, album, track):
    """
    Get the saved options from a release and use them according to flags set on the "advanced" tab
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param album: current release
    :param track: current track
    :return: None (result is passed via tm)
    A common function for both Artist and Workparts, so that the first class to process a track will execute
    this function so that the results are available to both (via a track metadata item)
    """
    release_status[release_id]['done'] = False
    set_options = collections.defaultdict(dict)
    main_sections = ['artists', 'workparts']
    all_sections = ['artists', 'tag', 'workparts', 'genres']
    parent_sections = {
        'artists': 'artists',
        'tag': 'artists',
        'workparts': 'workparts',
        'genres': 'workparts'}
    # The above needs to be done for legacy reasons - there  are only two tags which store options - artists and workparts
    # This dates from when there were only two sections
    # To split these now will create compatibility issues
    override = {
        'artists': 'cea_override',
        'tag': 'ce_tagmap_override',
        'workparts': 'cwp_override',
        'genres': 'ce_genres_override'}
    sect_text = {'artists': 'Artists', 'workparts': 'Works'}
    prefix = {'artists': 'cea', 'workparts': 'cwp'}

    if album.tagger.config.setting['ce_options_overwrite'] and all(
            album.tagger.config.setting[override[sect]] for sect in main_sections):
        set_options[track] = album.tagger.config.setting  # mutable
    else:
        set_options[track] = option_settings(
            album.tagger.config.setting)  # make a copy
        if set_options[track]["log_info"]:
            write_log(
                release_id,
                'info',
                'Default (i.e. per UI) options for track %s are %r',
                track,
                set_options[track])

    # As we use some of the main Picard options and may over-write them, save them here
    # set_options[track]['translate_artist_names'] = config.setting['translate_artist_names']
    # set_options[track]['standardize_artists'] = config.setting['standardize_artists']
    # (not sure this is needed - TODO reconsider)

    options = set_options[track]
    tm = track.metadata
    new_metadata = None
    orig_metadata = None
    # Only look up files if needed
    file_options = {}
    music_file = ''
    music_file_found = None
    release_status[release_id]['file_found'] = False
    start = datetime.now()
    if options["log_info"]:
        write_log(release_id, 'info', 'Clock start at %s', start)
    trackno = tm['tracknumber']
    discno = tm['discnumber']

    album_filenames = album.tagger.get_files_from_objects([album])
    if options["log_info"]:
        write_log(
            release_id,
            'info',
            'No. of album files found = %s',
            len(album_filenames))
    # Note that sometimes Picard fails to get all the file objects, even if they are there (network issues)
    # so we will cache whatever we can get!
    if release_id in release_status and 'file_objects' in release_status[release_id]:
        add_list_uniquely(
            release_status[release_id]['file_objects'],
            album_filenames)
    else:
        release_status[release_id]['file_objects'] = album_filenames
    if options["log_info"]:
        write_log(release_id, 'info', 'No. of album files cached = %s',
                  len(release_status[release_id]['file_objects']))
    track_file = None
    for album_file in release_status[release_id]['file_objects']:
        if options["log_info"]:
            write_log(release_id,
                      'info',
                      'Track file = %s, tracknumber = %s, discnumber = %s. Metadata trackno = %s, discno = %s',
                      album_file.filename,
                      str(album_file.tracknumber),
                      str(album_file.discnumber),
                      trackno,
                      discno)
        if str(
                album_file.tracknumber) == trackno and str(
                album_file.discnumber) == discno:
            if options["log_info"]:
                write_log(
                    release_id,
                    'info',
                    'Track file found = %r',
                    album_file.filename)
            track_file = album_file.filename
            break

    # Note: It would have been nice to do a rough check beforehand of total tracks,
    # but ~totalalbumtracks is not yet populated
    if not track_file:
        album_fullnames = [
            x.filename for x in release_status[release_id]['file_objects']]
        if options["log_info"]:
            write_log(
                release_id,
                'info',
                'Album files found = %r',
                album_fullnames)
        for music_file in album_fullnames:
            new_metadata = album.tagger.files[music_file].metadata

            if 'musicbrainz_trackid' in new_metadata and 'musicbrainz_trackid' in tm:
                if new_metadata['musicbrainz_trackid'] == tm['musicbrainz_trackid']:
                    track_file = music_file
                    break
        # Nothing found...
        if new_metadata and 'musicbrainz_trackid' not in new_metadata:
            if options['log_warning']:
                write_log(
                    release_id,
                    'warning',
                    'No trackid in file %s',
                    music_file)
        if 'musicbrainz_trackid' not in tm:
            if options['log_warning']:
                write_log(
                    release_id,
                    'warning',
                    'No trackid in track %s',
                    track)
    #
    # Note that, on initial load, new_metadata == orig_metadata; but, after refresh, new_metadata will have
    # the same track metadata as tm (plus the file metadata as per orig_metadata), so a trackid match
    # is then possible for files that do not have musicbrainz_trackid in orig_metadata. That is why
    # new_metadata is used in the above test, rather than orig_metadata, but orig_metadata is then used below
    # to get the saved options.
    #

    # Find the tag with the options:-
    if track_file:
        orig_metadata = album.tagger.files[track_file].orig_metadata
        music_file_found = track_file
        if options['log_info']:
            write_log(
                release_id,
                'info',
                'orig_metadata for file %s is',
                music_file)
            write_log(release_id, 'info', orig_metadata)
        for child_section in all_sections:
            section = parent_sections[child_section]
            if options[override[child_section]]:
                if options[prefix[section] + '_options_tag'] + ':' + \
                        section + '_options' in orig_metadata:
                    file_options[section] = interpret(
                        orig_metadata[options[prefix[section] + '_options_tag'] + ':' + section + '_options'])
                elif options[prefix[section] + '_options_tag'] in orig_metadata:
                    options_tag_contents = orig_metadata[options[prefix[section] + '_options_tag']]
                    if isinstance(options_tag_contents, list):
                        options_tag_contents = options_tag_contents[0]
                    combined_options = ''.join(options_tag_contents.split(
                        '(workparts_options)')).split('(artists_options)')
                    for i, _ in enumerate(combined_options):
                        combined_options[i] = interpret(
                            combined_options[i].lstrip('; '))
                        if isinstance(
                                combined_options[i],
                                dict) and 'Classical Extras' in combined_options[i]:
                            if sect_text[section] + \
                                    ' options' in combined_options[i]['Classical Extras']:
                                file_options[section] = combined_options[i]
                else:
                    for om in orig_metadata:
                        if ':' + section + '_options' in om:
                            file_options[section] = interpret(
                                orig_metadata[om])
                if section not in file_options or not file_options[section]:
                    if options['log_error']:
                        write_log(
                            release_id,
                            'error',
                            'Saved ' +
                            section +
                            ' options cannot be read for file %s. Using current settings',
                            music_file)
                    append_tag(
                        release_id,
                        tm,
                        '~' +
                        prefix[section] +
                        '_error',
                        '1. Saved ' +
                        section +
                        ' options cannot be read. Using current settings')

        release_status[release_id]['file_found'] = True

    end = datetime.now()
    if options['log_info']:
        write_log(release_id, 'info', 'Clock end at %s', end)
        write_log(release_id, 'info', 'Duration = %s', end - start)

    if not release_status[release_id]['file_found']:
        if options['log_warning']:
            write_log(
                release_id,
                'warning',
                "No file with matching trackid for track %s. IF THERE SHOULD BE ONE, TRY 'REFRESH'",
                track)
        append_tag(
            release_id,
            tm,
            "002_important_warning",
            "No file with matching trackid - IF THERE SHOULD BE ONE, TRY 'REFRESH' - "
            "(unable to process any saved options, lyrics or 'keep' tags)")
        # Nothing else is done with this info as yet - ideally we need to refresh and re-run
        # for all releases where, say, release_status[release_id]['file_prob']
        # == True  TODO?

    else:
        if options['log_info']:
            write_log(
                release_id,
                'info',
                'Found music file: %r',
                music_file_found)
        for section in all_sections:
            if options[override[section]]:
                parent_section = parent_sections[section]
                if parent_section in file_options and file_options[parent_section]:
                    try:
                        options_dict = file_options[parent_section]['Classical Extras'][sect_text[parent_section] + ' options']
                    except TypeError as err:
                        if options['log_error']:
                            write_log(
                                release_id,
                                'error',
                                'Error: %s. Saved ' +
                                section +
                                ' options cannot be read for file %s. Using current settings',
                                err,
                                music_file)
                        append_tag(
                            release_id,
                            tm,
                            '~' +
                            prefix[parent_section] +
                            '_error',
                            '1. Saved ' +
                            parent_section +
                            ' options cannot be read. Using current settings')
                        break
                    for opt in options_dict:
                        if isinstance(
                                options_dict[opt],
                                dict) and options[override['tag']]:  # for tag line options
                            # **NB tag mapping lines are the only entries of type dict**
                            opt_list = []
                            for opt_item in options_dict[opt]:
                                opt_list.append(
                                    {opt + '_' + opt_item: options_dict[opt][opt_item]})
                        else:
                            opt_list = [{opt: options_dict[opt]}]
                        for opt_dict in opt_list:
                            for opt_det in opt_dict:
                                opt_value = opt_dict[opt_det]
                                addn = []
                                if section == 'artists':
                                    addn = plugin_options('picard')
                                if section == 'tag':
                                    addn = plugin_options('tag_detail')
                                for ea_opt in plugin_options(section) + addn:
                                    displayed_option = options[ea_opt['option']]
                                    if ea_opt['name'] == opt_det:
                                        if 'value' in ea_opt:
                                            if ea_opt['value'] == opt_value:
                                                options[ea_opt['option']] = True
                                            else:
                                                options[ea_opt['option']
                                                        ] = False
                                        else:
                                            options[ea_opt['option']
                                                    ] = opt_value
                                        if options[ea_opt['option']
                                                   ] != displayed_option:
                                            if options['log_debug'] or options['log_info']:
                                                write_log(
                                                    release_id,
                                                    'info',
                                                    'Options overridden for option %s = %s',
                                                    ea_opt['option'],
                                                    opt_value)

                                            opt_text = str(opt_value)
                                            append_tag(
                                                release_id, tm, '003_information:options_overridden', str(
                                                    ea_opt['name']) + ' = ' + opt_text)

        if orig_metadata:
            keep_list = options['cea_keep'].split(",")
            if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
                keep_list.append(options['cea_lyrics_tag'])
            if options['cwp_genres_use_file']:
                if 'genre' in orig_metadata:
                    append_tag(
                        release_id,
                        tm,
                        '~cwp_candidate_genres',
                        orig_metadata['genre'])
                if options['cwp_genre_tag'] and options['cwp_genre_tag'] in orig_metadata:
                    keep_list.append(options['cwp_genre_tag'])
            really_keep_list = get_preserved_tags()[:]
            really_keep_list.append(
                options['cwp_options_tag'] +
                ':workparts_options')
            really_keep_list.append(
                options['cea_options_tag'] +
                ':artists_options')
            for tagx in keep_list:
                tag = tagx.strip()
                really_keep_list.append(tag)
                if tag in orig_metadata:
                    append_tag(release_id, tm, tag, orig_metadata[tag])
            if options['cea_clear_tags']:
                delete_list = []
                for tag_item in orig_metadata:
                    if tag_item not in really_keep_list and tag_item[0] != '~':
                        # the second condition is to ensure that (hidden) file variables are not deleted,
                        #  as these are in orig_metadata, not track_metadata
                        delete_list.append(tag_item)
                # this will be used in map_tags to delete unwanted tags
                options['delete_tags'] = delete_list
            ## Create a "mirror" tag with the old data, for comparison purposes
            mirror_tags = []
            for tag_item in orig_metadata:
                mirror_name = tag_item + '_OLD'
                if mirror_name[0] == '~' :
                    mirror_name.replace('~', '_')
                mirror_name = '~' + mirror_name
                mirror_tags.append((mirror_name, tag_item))
                append_tag(release_id, tm, mirror_name, orig_metadata[tag_item])
            append_tag(release_id, tm, '~ce_mirror_tags', mirror_tags)

        if not isinstance(options, dict):
            options_dict = option_settings(config.setting)
            write_log(
                'session',
                'info',
                'Using option_settings(config.setting): %s',
                options_dict)
        else:
            options_dict = options
            write_log(
                'session',
                'info',
                'Using options: %s',
                options_dict)
        tm['~ce_options'] = str(options_dict)
        tm['~ce_file'] = music_file_found


def plugin_options(option_type):
    """
    :param option_type: artists, tag, workparts, genres or other
    :return: the relevant dictionary for the type
    This function contains all the options data in one place - to prevent multiple repetitions elsewhere
    """
    if option_type == 'artists':
        return const.ARTISTS_OPTIONS
    elif option_type == 'tag':
        return const.TAG_OPTIONS
    elif option_type == 'tag_detail':
        return const.TAG_DETAIL_OPTIONS
    elif option_type == 'workparts':
        return const.WORKPARTS_OPTIONS
    elif option_type == 'genres':
        return const.GENRE_OPTIONS
    elif option_type == 'picard':
        return const.PICARD_OPTIONS
    elif option_type == 'other':
        return const.OTHER_OPTIONS
    else:
        return None

def option_settings(config_settings):
    """
    :param config_settings: options from UI
    :return: a (deep) copy of the Classical Extras options
    """
    options = {}
    for option in plugin_options('artists') + plugin_options('tag') + plugin_options('tag_detail') + plugin_options(
            'workparts') + plugin_options('genres') + plugin_options('picard') + plugin_options('other'):
        options[option['option']] = copy.deepcopy(
            config_settings[option['option']])
    return options


def get_aliases(self, release_id, album, options, releaseXmlNode):
    """
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param self:
    :param album:
    :param options:
    :param releaseXmlNode: all the metadata for the release
    :return: Data is returned via self.artist_aliases and self.artist_credits[album]

    Note regarding aliases and credited-as names:
    In a MB release, an artist can appear in one of seven contexts. Each of these is accessible in releaseXmlNode
    and the track and recording contexts are also accessible in trackXmlNode.
    The seven contexts are:
    Recording: credited-as and alias
    Release-group: credited-as and alias
    Release: credited-as and alias
    Release relationship: credited-as and (not reliably?) alias
    Recording relationship (direct): credited-as and (not reliably?) alias
    Recording relationship (via work): credited-as and (not reliably?) alias
    Track: credited-as and alias
    (The above are applied in sequence - e.g. track artist credit will over-ride release artist credit. "Recording" gets
    the lowest priority as it is more generic than the release data {may apply to multiple releases})
    This function collects all the available aliases and as-credited names once (on processing the first track).
    N.B. if more than one release is loaded in Picard, any available alias names loaded so far will be available
    and used. However, as-credited names will only be used from the current release."""

    if 'artist_locale' in config.setting and options['cea_aliases'] or options['cea_aliases_composer']:
        locale = config.setting["artist_locale"]
        lang = locale.split("_")[0]  # NB this is the Picard code in /util

        # Track and recording aliases/credits are gathered by parsing the
        # media, track and recording nodes
        # Do the recording relationship first as it may apply to multiple releases, so release and track data
        # is more specific.
        media = parse_data(release_id, releaseXmlNode, [], 'media')
        for m in media:
            # disc_num = int(parse_data(options, m, [], 'position', 'text')[0])
            # not currently used
            tracks = parse_data(release_id, m, [], 'tracks')
            for track in tracks:
                for t in track:
                    # track_num = int(parse_data(options, t, [], 'number',
                    # 'text')[0]) # not currently used

                    # Recording artists
                    obj = parse_data(release_id, t, [], 'recording')
                    get_aliases_and_credits(
                        self,
                        options,
                        release_id,
                        album,
                        obj,
                        lang,
                        options['cea_recording_credited'])

        # Get the release data before the recording relationshiops and track data
        # Release group artists
        obj = parse_data(release_id, releaseXmlNode, [], 'release-group')
        get_aliases_and_credits(
            self,
            options,
            release_id,
            album,
            obj,
            lang,
            options['cea_group_credited'])

        # Release artists
        get_aliases_and_credits(
            self,
            options,
            release_id,
            album,
            releaseXmlNode,
            lang,
            options['cea_credited'])
        # Next bit needed to identify artists who are album artists
        self.release_artists_sort[album] = parse_data(
            release_id, releaseXmlNode, [], 'artist-credit', 'artist', 'sort-name')
        # Release relationship artists
        get_relation_credits(
            self,
            options,
            release_id,
            album,
            releaseXmlNode,
            lang,
            options['cea_release_relationship_credited'])

        # Now get the rest:
        for m in media:
            tracks = parse_data(release_id, m, [], 'tracks')
            for track in tracks:
                for t in track:
                    # Recording relationship artists
                    obj = parse_data(release_id, t, [], 'recording')
                    get_relation_credits(
                        self,
                        options,
                        release_id,
                        album,
                        obj,
                        lang,
                        options['cea_recording_relationship_credited'])
                    # Track artists
                    get_aliases_and_credits(
                        self,
                        options,
                        release_id,
                        album,
                        t,
                        lang,
                        options['cea_track_credited'])

    if options['log_info']:
        write_log(release_id, 'info', 'Alias and credits info for %s', self)
        write_log(release_id, 'info', 'Aliases :%s', self.artist_aliases)
        write_log(
            release_id,
            'info',
            'Credits :%s',
            self.artist_credits[album])


def get_artists(options, release_id, tm, relations, relation_type):
    """
    Get artist info from XML lookup
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param options:
    :param tm:
    :param relations:
    :param relation_type: 'release', 'recording' or 'work' (NB 'work' does not pass a param for tm)
    :return:
    """
    if options['log_debug'] or options['log_info']:
        write_log(
            release_id,
            'debug',
            'In get_artists. relation_type: %s, relations: %s',
            relation_type,
            relations)
    log_options = {
        'log_debug': options['log_debug'],
        'log_info': options['log_info']}
    artists = []
    instruments = []
    artist_types = const.RELATION_TYPES[relation_type]
    for artist_type in artist_types:
        artists, instruments = create_artist_data(release_id, options, log_options, tm, relations,
                                                  relation_type, artist_type, artists, instruments)
    artist_dict = {'artists': artists, 'instruments': instruments}
    return artist_dict


def create_artist_data(release_id, options, log_options, tm, relations,
                       relation_type, artist_type, artists, instruments):
    """
    Update the artists and instruments
    :param release_id: the current album id
    :param options:
    :param log_options:
    :param tm: track metadata
    :param relations:
    :param relation_type: release', 'recording' or 'work' (NB 'work' does not pass a param for tm)
    :param artist_type: from const.RELATION_TYPES[relation_type]
    :param artists: current artist list - updated with each call
    :param instruments: current instruments list - updated with each call
    :return: artists, instruments
    """
    type_list = parse_data(
        release_id,
        relations,
        [],
        'target-type:artist',
        'type:' +
        artist_type)
    for type_item in type_list:
        artist_name_list = parse_data(
            release_id, type_item, [], 'artist', 'name')
        artist_sort_name_list = parse_data(
            release_id, type_item, [], 'artist', 'sort-name')
        if artist_type not in [
            'instrument',
            'vocal',
            'instrument arranger',
            'vocal arranger']:
            instrument_list = None
            credited_inst_list = None
        else:
            instrument_list_list = parse_data(
                release_id, type_item, [], 'attributes')
            if instrument_list_list:
                instrument_list = instrument_list_list[0]
            else:
                instrument_list = []
            credited_inst_list = instrument_list[:]
            credited_inst_dict_list = parse_data(
                release_id, type_item, [], 'attribute-credits')  # keyed to insts
            if credited_inst_dict_list:
                credited_inst_dict = credited_inst_dict_list[0]
            else:
                credited_inst_dict = {}
            for i, inst in enumerate(instrument_list):
                if inst in credited_inst_dict:
                    credited_inst_list[i] = credited_inst_dict[inst]

            if artist_type == 'vocal':
                if not instrument_list:
                    instrument_list = ['vocals']
                elif not any('vocals' in x for x in instrument_list):
                    instrument_list.append('vocals')
                    credited_inst_list.append('vocals')
        # fill the hidden vars before we choose to use the as-credited
        # version
        if relation_type != 'work':
            inst_tag = []
            cred_tag = []
            if instrument_list:
                inst_tag = list(set(instrument_list))
            if credited_inst_list:
                cred_tag = list(set(credited_inst_list))
            for attrib in ['solo', 'guest', 'additional']:
                if attrib in inst_tag:
                    inst_tag.remove(attrib)
                if attrib in cred_tag:
                    cred_tag.remove(attrib)
            if inst_tag:
                if tm['~cea_instruments']:
                    tm['~cea_instruments'] = add_list_uniquely(
                        tm['~cea_instruments'], inst_tag)
                else:
                    tm['~cea_instruments'] = inst_tag
            if cred_tag:
                if tm['~cea_instruments_credited']:
                    tm['~cea_instruments_credited'] = add_list_uniquely(
                        tm['~cea_instruments_credited'], cred_tag)
                else:
                    tm['~cea_instruments_credited'] = cred_tag
            if inst_tag or cred_tag:
                if tm['~cea_instruments_all']:
                    tm['~cea_instruments_all'] = add_list_uniquely(
                        tm['~cea_instruments_all'], list(set(inst_tag + cred_tag)))
                else:
                    tm['~cea_instruments_all'] = list(
                        set(inst_tag + cred_tag))
        if '~cea_instruments' in tm and '~cea_instruments_credited' in tm and '~cea_instruments_all' in tm:
            instruments = [
                tm['~cea_instruments'],
                tm['~cea_instruments_credited'],
                tm['~cea_instruments_all']]
        if options['cea_inst_credit'] and credited_inst_list:
            instrument_list = credited_inst_list
        if instrument_list:
            instrument_sort = 3
            s_key = {
                'lead vocals': 1,
                'solo': 2,
                'guest': 4,
                'additional': 5}
            for inst in s_key:
                if inst in instrument_list:
                    instrument_sort = s_key[inst]
        else:
            instrument_sort = 0

        if artist_type in const.ARTIST_TYPE_ORDER:
            type_sort = const.ARTIST_TYPE_ORDER[artist_type]
        else:
            type_sort = 99
            if log_options['log_error']:
                write_log(
                    release_id,
                    'error',
                    "Error in artist type. Type '%s' is not in ARTIST_TYPE_ORDER dictionary",
                    artist_type)

        artist = (
            artist_type,
            instrument_list,
            artist_name_list,
            artist_sort_name_list,
            instrument_sort,
            type_sort)
        artists.append(artist)
        # Sorted by sort name then instrument_sort then artist type
        artists = sorted(artists, key=lambda x: (x[5], x[3], x[4], x[1]))
        if log_options['log_info']:
            write_log(release_id, 'info', 'sorted artists = %s', artists)
    return artists, instruments


def get_series(options, release_id, relations):
    """
    Get series info (depends on lookup having used inc=series-rel)
    :param options:
    :param release_id:
    :param relations:
    :return:
    """
    # if options['log_debug'] or options['log_info']:
    #     write_log(
    #         release_id,
    #         'debug',
    #         'In get_series.  relations: %s',
    #         relations)
    # series_name_list =[]
    # series_id_list = []
    # for series_rels in relations:
    #     series_rel = parse_data(
    #         release_id,
    #         series_rels,
    #         [],
    #         'target-type:series',
    #         'type:part-of')
    #     if options['log_debug'] or options['log_info']:
    #         write_log(
    #             release_id,
    #             'debug',
    #             'series_rel =  %s',
    #             series_rel)
    #     series_name_list.extend(
    #         parse_data(release_id, series_rel, [], 'series', 'name')
    #     )
    #     series_id_list.extend(
    #         parse_data(release_id, series_rel, [], 'series', 'id')
    #     )
    type_list = parse_data(
        release_id,
        relations,
        [],
        'target-type:series',
        'type:part of')
    if type_list:
        series_name_list = []
        series_id_list = []
        series_number_list = []
        for type_item in type_list:
            series_name_list = parse_data(
                release_id, type_item, [], 'series', 'name')
            series_id_list = parse_data(
                release_id, type_item, [], 'series', 'id')
            series_number_list = parse_data(
                release_id, type_item, [], 'attribute-values', 'number')
        return {'name_list': series_name_list, 'id_list': series_id_list, 'number_list': series_number_list}
    else:
        return None



def apply_artist_style(
        options,
        release_id,
        lang,
        a_list,
        name_style,
        name_tag,
        sort_tag,
        names_tag,
        names_sort_tag):
    # Get  artist and apply style
    for a_item in a_list:
        for acs in a_item:
            artistlist = parse_data(release_id, acs, [], 'name')
            sortlist = parse_data(release_id, acs, [], 'artist', 'sort-name')
            names = {}
            if lang:
                names['alias'] = parse_data(
                    release_id,
                    acs,
                    [],
                    'artist',
                    'aliases',
                    'locale:' + lang,
                    'primary:True',
                    'name')
            else:
                names['alias'] = []
            names['credit'] = parse_data(release_id, acs, [], 'name')
            pairslist = list(zip(artistlist, sortlist))
            names['sort'] = [
                translate_from_sortname(
                    *pair) for pair in pairslist]
            for style in name_style:
                if names[style]:
                    artistlist = names[style]
                    break
            joinlist = parse_data(release_id, acs, [], 'joinphrase')

            if artistlist:
                name_tag.append(artistlist[0])
                sort_tag.append(sortlist[0])
                names_tag.append(artistlist[0])
                names_sort_tag.append(sortlist[0])

            if joinlist:
                name_tag.append(joinlist[0])
                sort_tag.append(joinlist[0])

    name_tag_str = ''.join(name_tag)
    sort_tag_str = ''.join(sort_tag)

    return {
        'artists': names_tag,
        'artists_sort': names_sort_tag,
        'artist': name_tag_str,
        'artistsort': sort_tag_str}


def set_work_artists(self, release_id, album, track, writerList, tm, count):
    """
    :param release_id:
    :param self is the calling object from Artists or WorkParts
    :param album: the current album
    :param track: the current track
    :param writerList: format [(artist_type, [instrument_list], [name list],[sort_name list]),(.....etc]
    :param tm: track metadata
    :param count: depth count of recursion in process_work_artists (should equate to part level)
    :return:
    """

    options = self.options[track]
    if not options['classical_work_parts']:
        caller = 'ExtraArtists'
        pre = '~cea'
    else:
        caller = 'PartLevels'
        pre = '~cwp'
    write_log(
        release_id,
        'debug',
        'Class: %s: in set_work_artists for track %s. Count (level) is %s. Writer list is %s',
        caller,
        track,
        count,
        writerList)
    # tag strings are a tuple (Picard tag, cwp tag, Picard sort tag, cwp sort
    # tag) (NB this is modelled on set_performer)
    tag_strings = const.tag_strings(pre)
    # insertions lists artist types where names in the main Picard tags may be
    # updated for annotations
    insertions = const.INSERTIONS
    no_more_lyricists = False
    if caller == 'PartLevels' and self.lyricist_filled[track]:
        no_more_lyricists = True

    for writer in writerList:
        writer_type = writer[0]
        if writer_type not in tag_strings:
            break
        if no_more_lyricists and (
                writer_type == 'lyricist' or writer_type == 'librettist'):
            break
        if writer[1]:
            inst_list = writer[1][:]
            # take a copy of the list in case (because of list
            # mutability) we need the old one
            instrument = ", ".join(inst_list)
        else:
            instrument = None
        sub_strings = {  # 'instrument arranger': instrument, 'vocal arranger': instrument
        }
        if options['cea_arranger']:
            if instrument:
                arr_inst = options['cea_arranger'] + ' ' + instrument
            else:
                arr_inst = options['cea_arranger']
        else:
            arr_inst = instrument
        annotations = {'writer': options['cea_writer'],
                       'lyricist': options['cea_lyricist'],
                       'librettist': options['cea_librettist'],
                       'revised by': options['cea_revised'],
                       'translator': options['cea_translator'],
                       'arranger': options['cea_arranger'],
                       'reconstructed by': options['cea_reconstructed'],
                       'orchestrator': options['cea_orchestrator'],
                       'instrument arranger': arr_inst,
                       'vocal arranger': arr_inst}
        tag = tag_strings[writer_type][0]
        sort_tag = tag_strings[writer_type][2]
        cwp_tag = tag_strings[writer_type][1]
        cwp_sort_tag = tag_strings[writer_type][3]
        cwp_names_tag = cwp_tag[:-1] + '_names'
        cwp_instrumented_tag = cwp_names_tag + '_instrumented'
        if writer_type in sub_strings:
            if sub_strings[writer_type]:
                tag += sub_strings[writer_type]
        if tag:
            if '~ce_tag_cleared_' + \
                    tag not in tm or not tm['~ce_tag_cleared_' + tag] == "Y":
                if tag in tm:
                    if options['log_info']:
                        write_log(release_id, 'info', 'delete tag %s', tag)
                    del tm[tag]
            tm['~ce_tag_cleared_' + tag] = "Y"
        if sort_tag:
            if '~ce_tag_cleared_' + \
                    sort_tag not in tm or not tm['~ce_tag_cleared_' + sort_tag] == "Y":
                if sort_tag in tm:
                    del tm[sort_tag]
            tm['~ce_tag_cleared_' + sort_tag] = "Y"

        name_list = writer[2]
        for ind, name in enumerate(name_list):
            sort_name = writer[3][ind]
            no_credit = True
            write_log(
                    release_id,
                    'info',
                    'In set_work_artists. Name before changes = %s',
                    name)
            # change name to as-credited
            if options['cea_composer_credited']:
                if album in self.artist_credits and sort_name in self.artist_credits[album]:
                    no_credit = False
                    name = self.artist_credits[album][sort_name]
            # over-ride with aliases if appropriate
            if (options['cea_aliases'] or options['cea_aliases_composer']) and (
                    no_credit or options['cea_alias_overrides']):
                if sort_name in self.artist_aliases:
                    name = self.artist_aliases[sort_name]
            # fix cyrillic names if not already fixed
            if options['cea_cyrillic']:
                if not only_roman_chars(name):
                    name = remove_middle(unsort(sort_name))
                    # Only remove middle name where the existing
                    # performer is in non-latin script
            annotated_name = name
            write_log(
                    release_id,
                    'info',
                    'In set_work_artists. Name after changes = %s',
                    name)
            # add annotations and write performer tags
            if writer_type in annotations:
                if annotations[writer_type]:
                    annotated_name += ' (' + annotations[writer_type] + ')'
            if instrument:
                instrumented_name = name + ' (' + instrument + ')'
            else:
                instrumented_name = name

            if writer_type in insertions and options['cea_arrangers']:
                self.append_tag(release_id, tm, tag, annotated_name)
            else:
                if options['cea_arrangers'] or writer_type == tag:
                    self.append_tag(release_id, tm, tag, name)

            if options['cea_arrangers'] or writer_type == tag:
                if sort_tag:
                    self.append_tag(release_id, tm, sort_tag, sort_name)
                    if options['cea_tag_sort'] and '~' in sort_tag:
                        explicit_sort_tag = sort_tag.replace('~', '')
                        self.append_tag(
                            release_id, tm, explicit_sort_tag, sort_name)
            self.append_tag(release_id, tm, cwp_tag, annotated_name)
            self.append_tag(release_id, tm, cwp_names_tag, name)
            if instrumented_name != name:
                self.append_tag(
                    release_id,
                    tm,
                    cwp_instrumented_tag,
                    instrumented_name)

            if cwp_sort_tag:
                self.append_tag(release_id, tm, cwp_sort_tag, sort_name)

            if caller == 'PartLevels' and (
                    writer_type == 'lyricist' or writer_type == 'librettist'):
                self.lyricist_filled[track] = True
                write_log(
                        release_id,
                        'info',
                        'Filled lyricist for track %s. Not looking further',
                        track)

            if writer_type == 'composer':
                composerlast = sort_name.split(",")[0]
                write_log(
                        release_id,
                        'info',
                        'composerlast = %s',
                        composerlast)
                self.append_tag(
                    release_id,
                    tm,
                    pre +
                    '_composer_lastnames',
                    composerlast)
                if sort_name in self.release_artists_sort[album]:
                    self.append_tag(
                        release_id, tm, '~cea_album_composers', name)
                    self.append_tag(
                        release_id, tm, '~cea_album_composers_sort', sort_name)
                    self.append_tag(
                        release_id,
                        tm,
                        '~cea_album_track_composer_lastnames',
                        composerlast)
                    composer_last_names(self, release_id, tm, album)


# Non-Latin character processing
latin_letters = {}

def is_latin(uchr):
    """Test whether character is in Latin script"""
    try:
        return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(
            uchr, 'LATIN' in unicodedata.name(uchr))


def only_roman_chars(unistr):
    """Test whether string is in Latin script"""
    return all(is_latin(uchr)
               for uchr in unistr
               if uchr.isalpha())


def get_roman(string):
    """Transliterate cyrillic script to Latin script"""
    translit_string = ""
    for index, char in enumerate(string):
        if char in const.CYRILLIC_LOWER.keys():
            char = const.CYRILLIC_LOWER[char]
        elif char in const.CYRILLIC_UPPER.keys():
            char = const.CYRILLIC_UPPER[char]
            if string[index + 1] not in const.CYRILLIC_LOWER.keys():
                char = char.upper()
        translit_string += char
    # fix multi-chars
    translit_string = translit_string.replace('ks', 'x').replace('iy ', 'i ')
    return translit_string


def remove_middle(performer):
    """To remove middle names of Russian composers"""
    plist = performer.split()
    if len(plist) == 3:
        return plist[0] + ' ' + plist[2]
    else:
        return performer


# Sorting etc.

def unsort(performer):
    """
    To take a sort field and recreate the name
    Only now used for last-ditch cyrillic translation - superseded by 'translate_from_sortname'
    """
    sorted_list = performer.split(', ')
    sorted_list.reverse()
    for i, item in enumerate(sorted_list):
        if item[-1] != "'":
            sorted_list[i] += ' '
    return ''.join(sorted_list).strip()


def _reverse_sortname(sortname):
    """
    Reverse sortnames.
    Code is from picard/util/__init__.py
    """

    chunks = [a.strip() for a in sortname.split(",")]
    chunk_len = len(chunks)
    if chunk_len == 2:
        return "%s %s" % (chunks[1], chunks[0])
    elif chunk_len == 3:
        return "%s %s %s" % (chunks[2], chunks[1], chunks[0])
    elif chunk_len == 4:
        return "%s %s, %s %s" % (chunks[1], chunks[0], chunks[3], chunks[2])
    else:
        return sortname.strip()


def stripsir(performer):
    """
    Remove honorifics from names
    Also standardize hyphens and apostrophes in names
    """
    performer = performer.replace(u'\u2010', u'-').replace(u'\u2019', u"'")
    sir = re.compile(r'(.*)\b(Sir|Maestro|Dame)\b\s*(.*)', re.IGNORECASE)
    match = sir.search(performer)
    if match:
        return match.group(1) + match.group(3)
    else:
        return performer


# def swap_prefix(performer):
#     """NOT CURRENTLY USED. Create sort fields for ensembles etc., by placing the prefix (see constants) at the end"""
#     prefix = '|'.join(prefixes)
#     swap = re.compile(r'^(' + prefix + r')\b\s*(.*)', re.IGNORECASE)
#     match = swap.search(performer)
#     if match:
#         return match.group(2) + ", " + match.group(1)
#     else:
#         return performer


def replace_roman_numerals(s):
    """Replaces roman numerals include in s, where followed by certain punctuation, by digits"""
    romans = RE_ROMANS.findall(s)
    for roman in romans:
        if roman[0]:
            numerals = str(roman[0])
            digits = str(from_roman(numerals))
            to_replace = r'\b' + roman[0] + r'\b'
            s = re.sub(to_replace, digits, s)
    return s


def from_roman(s):
    romanNumeralMap = (('M', 1000),
                       ('CM', 900),
                       ('D', 500),
                       ('CD', 400),
                       ('C', 100),
                       ('XC', 90),
                       ('L', 50),
                       ('XL', 40),
                       ('X', 10),
                       ('IX', 9),
                       ('V', 5),
                       ('IV', 4),
                       ('I', 1),
                       ('m', 1000),
                       ('cm', 900),
                       ('d', 500),
                       ('cd', 400),
                       ('c', 100),
                       ('xc', 90),
                       ('l', 50),
                       ('xl', 40),
                       ('x', 10),
                       ('ix', 9),
                       ('v', 5),
                       ('iv', 4),
                       ('i', 1))
    result = 0
    index = 0
    for numeral, integer in romanNumeralMap:
        while s[index:index + len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result


def turbo_lcs(release_id, multi_list):
    """
    Picks the best longest common string method to use
    Works with a list of lists or a list of strings
    :param release_id:
    :param multi_list: a list of strings or a list of lists
    :return: longest common substring/list
    """
    write_log(release_id, 'debug', 'In turbo_lcs')
    if not isinstance(multi_list, list):
        return None
    list_sum = sum([len(x) for x in multi_list])
    list_len = len(multi_list)
    if list_len < 2:
        if list_len == 1:
            return multi_list[0]  # Nothing to do!
        else:
            return []
    # for big matches, use the generalised suffix tree method
    if ((list_sum / list_len) ** 2) * list_len > 1000:
        # heuristic: may need to tweak the 1000 in the light of results
        lcs_dict = suffixtree.multi_lcs(multi_list)
        # NB suffixtree may be shown as an unresolved reference in the IDE,
        # but it should work provided it is included in the package
        if "error" not in lcs_dict:
            if "response" in lcs_dict:
                write_log(
                        release_id,
                        'info',
                        'Longest common string was returned from suffix tree algo')
                return lcs_dict['response']

     ## If suffix tree fails, write errors to log before proceeding with alternative
            else:
                write_log(
                        release_id,
                        'error',
                        'Suffix tree failure for release %s. Error unknown. Using standard lcs algo instead',
                        release_id)
        else:
            write_log(
                    release_id,
                    'error',
                    'Suffix tree failure for release %s. Error message: %s. Using standard lcs algo instead',
                    release_id,
                    lcs_dict['error'])
    # otherwise, or if gst fails, use the standard algorithm
    first = True
    common = []
    for item in multi_list:
        if first:
            common = item
            first = False
        else:
            lcs = longest_common_substring(
                item, common)
            common = lcs['string']
    write_log(release_id, 'debug', 'LCS returned from standard algo')
    return common


def longest_common_substring(s1, s2):
    """
    Standard lcs algo for short strings, or if suffix tree does not work
    :param s1: substring 1
    :param s2: substring 2
    :return: {'string': the longest common substring,
        'start': the start position in s1,
        'length': the length of the common substring}
    NB this also works on list arguments - i.e. it will find the longest common sub-list
    """
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return {'string': s1[x_longest - longest: x_longest],
            'start': x_longest - longest, 'length': longest}


def longest_common_sequence(list1, list2, minstart=0, maxstart=0):
    """
    :param list1: list 1
    :param list2: list 2
    :param minstart: the earliest point to start looking for a match
    :param maxstart: the latest point to start looking for a match
    :return: {'sequence': the common subsequence, 'length': length of subsequence}
    maxstart must be >= minstart. If they are equal then the start point is fixed.
    Note that this only finds subsequences starting at the same position
    Use longest_common_substring for the more general problem
    """
    if maxstart < minstart:
        return None, 0
    min_len = min(len(list1), len(list2))
    longest = 0
    seq = None
    maxstart = min(maxstart, min_len) + 1
    for k in range(minstart, maxstart):
        for i in range(k, min_len + 1):
            if list1[k:i] == list2[k:i] and i - k > longest:
                longest = i - k
                seq = list1[k:i]
    return {'sequence': seq, 'length': longest}


def substart_finder(mylist, pattern):
    for i, list_item in enumerate(mylist):
        if list_item == pattern[0] and mylist[i:i + len(pattern)] == pattern:
            return i
    return len(mylist)  # if nothing found


def get_ui_tags():
## Determine tags for display in ui
    options = config.setting
    ui_tags_raw = options['ce_ui_tags']
    ui_tags = {}
    ui_tags_split = [x.replace('(','').strip(') ') for x in ui_tags_raw.split('/')]
    for ui_column in ui_tags_split:
        if ':'  in ui_column:
            ui_col_parts = [x.strip() for x in ui_column.split(':')]
            heading = ui_col_parts[0]
            tag_names = ui_col_parts[1].split(',')
            tag_names = [x.strip() for x in tag_names]
            ui_tags[heading] = tuple(tag_names)
    return ui_tags


def map_tags(options, release_id, album, tm):
    """
    Do the common tag processing - including for the genres and tag-mapping sections
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param options: options passed from either Artists or Workparts
    :param album:
    :param tm: track metadata
    :return: None - action is through setting tm contents
    This is a common function for Artists and Workparts which should only run after both sections have completed for
    a given track. If, say, Artists calls it and Workparts is not done,
    then it will not execute until Workparts calls it (and vice versa).
    """

    write_log(release_id, 'debug', 'In map_tags, checking readiness...')
    if (options['classical_extra_artists'] and '~cea_artists_complete' not in tm) or (
            options['classical_work_parts'] and '~cea_works_complete' not in tm):
        write_log(release_id, 'info', '...not ready')
        return
    write_log(release_id, 'debug', '... processing tag mapping')

    # blank tags
    blank_tags = options['cea_blank_tag'].split(
        ",") + options['cea_blank_tag_2'].split(",")
    if 'artists_sort' in [x.strip() for x in blank_tags]:
        blank_tags.append('~artists_sort')
    for tag in blank_tags:
        if tag.strip() in tm:
            # place blanked tags into hidden variables available for
            # re-use
            tm['~cea_' + tag.strip()] = tm[tag.strip()]
            del tm[tag.strip()]

    # album
    if tm['~cea_album_composer_lastnames']:
        last_names = str_to_list(tm['~cea_album_composer_lastnames'])
        if options['cea_composer_album']:
            # save it as a list to prevent splitting when appending tag
            tm['~cea_release'] = [tm['album']]
            new_last_names = []
            for last_name in last_names:
                last_name = last_name.strip()
                new_last_names.append(last_name)
            if len(new_last_names) > 0:
                tm['album'] = "; ".join(new_last_names) + ": " + tm['album']

    # remove lyricists if no vocals, according to option set
    if options['cea_no_lyricists'] and not any(
            [x for x in str_to_list(tm['~cea_performers']) if 'vocals' in x]):
        if 'lyricist' in tm:
            del tm['lyricist']
        for lyricist_tag in ['lyricists', 'librettists', 'translators']:
            if '~cwp_' + lyricist_tag in tm:
                del tm['~cwp_' + lyricist_tag]

    # genres
    if config.setting['folksonomy_tags'] and 'genre' in tm:
        candidate_genres = str_to_list(tm['genre'])
        append_tag(release_id, tm, '~cea_candidate_genres', candidate_genres)
        # to avoid confusion as it will contain unmatched folksonomy tags
        del tm['genre']
    else:
        candidate_genres = []
    is_classical = False
    composers_not_found = []
    composer_found = False
    composer_born_list = []
    composer_died_list = []
    arrangers_not_found = []
    arranger_found = False
    arranger_born_list = []
    arranger_died_list = []
    no_composer_in_metadata = False
    if options['cwp_use_muso_refdb'] and options['cwp_muso_classical'] or options['cwp_muso_dates']:
        if COMPOSER_DICT:
            composersort_list = []
            if '~cwp_composer_names' in tm:
                composer_list = str_to_list(tm['~cwp_composer_names'])
            else:
                # maybe there were no works linked,
                # but it might still a classical track (based on composer name)
                no_composer_in_metadata = True
                composer_list = str_to_list(tm['artists'])
                composersort_list = str_to_list(tm['~artists_sort'])
                write_log(release_id, 'info', "No composer metadata for track %s. Using artists %r", tm['title'],
                          composer_list)
            lc_composer_list = [c.lower() for c in composer_list]
            for ind, composer in enumerate(lc_composer_list):
                for classical_composer in COMPOSER_DICT:
                    if composer in classical_composer['lc_name']:
                        if options['cwp_muso_classical']:
                            candidate_genres.append('Classical')
                            is_classical = True
                        if options['cwp_muso_dates']:
                            composer_born_list = classical_composer['birth']
                            composer_died_list = classical_composer['death']
                        composer_found = True
                        if no_composer_in_metadata:
                            composersort = composersort_list[ind]
                            append_tag(release_id, tm, 'composer', composer_list[ind])
                            append_tag(release_id, tm, '~cwp_composer_names', composer_list[ind])
                            append_tag(release_id, tm, 'composersort', composersort)
                            append_tag(release_id, tm, '~cwp_composers_sort', composersort)
                            append_tag(release_id, tm, '~cwp_composer_lastnames', composersort.split(', ')[0])
                        break
                if not composer_found:
                    composer_index = lc_composer_list.index(composer)
                    orig_composer = composer_list[composer_index]
                    composers_not_found.append(orig_composer)
                    append_tag(
                        release_id,
                        tm,
                        '~cwp_unrostered_composers',
                        orig_composer)
            if composers_not_found:
                append_tag(
                    release_id,
                    tm,
                    '003_information:composers',
                    'Composer(s) ' +
                    list_to_str(composers_not_found) +
                    ' not found in reference database of classical composers')

            # do the same for arrangers, if required
            if options['cwp_genres_arranger_as_composer'] or options['cwp_periods_arranger_as_composer']:
                arranger_list = str_to_list(
                    tm['~cea_arranger_names']) + str_to_list(tm['~cwp_arranger_names'])
                lc_arranger_list = [c.lower() for c in arranger_list]
                for arranger in lc_arranger_list:
                    for classical_arranger in COMPOSER_DICT:
                        if arranger in classical_arranger['lc_name']:
                            if options['cwp_muso_classical'] and options['cwp_genres_arranger_as_composer']:
                                candidate_genres.append('Classical')
                                is_classical = True
                            if options['cwp_muso_dates'] and options['cwp_periods_arranger_as_composer']:
                                arranger_born_list = classical_arranger['birth']
                                arranger_died_list = classical_arranger['death']
                            arranger_found = True
                            break
                    if not arranger_found:
                        arranger_index = lc_arranger_list.index(arranger)
                        orig_arranger = arranger_list[arranger_index]
                        arrangers_not_found.append(orig_arranger)
                        append_tag(
                            release_id,
                            tm,
                            '~cwp_unrostered_arrangers',
                            orig_arranger)
                if arrangers_not_found:
                    append_tag(
                        release_id,
                        tm,
                        '003_information:arrangers',
                        'Arranger(s) ' +
                        list_to_str(arrangers_not_found) +
                        ' not found in reference database of classical composers')

        else:
            append_tag(
                release_id,
                tm,
                '001_errors:8',
                '8. No composer reference file. Check log for error messages re path name.')

    if options['cwp_use_muso_refdb'] and options['cwp_muso_genres'] and GENRE_DICT:
        main_classical_genres_list = [list_to_str(
            mg['name']).strip() for mg in GENRE_DICT]
    else:
        main_classical_genres_list = [
            sg.strip() for sg in options['cwp_genres_classical_main'].split(',')]
    sub_classical_genres_list = [
        sg.strip() for sg in options['cwp_genres_classical_sub'].split(',')]
    main_other_genres_list = [
        sg.strip() for sg in options['cwp_genres_other_main'].split(',')]
    sub_other_genres_list = [sg.strip()
                             for sg in options['cwp_genres_other_sub'].split(',')]
    main_classical_genres = []
    sub_classical_genres = []
    main_other_genres = []
    sub_other_genres = []
    if '~cea_work_type' in tm:
        candidate_genres += str_to_list(tm['~cea_work_type'])
    if '~cwp_candidate_genres' in tm:
        candidate_genres += str_to_list(tm['~cwp_candidate_genres'])
    write_log(release_id, 'info', "Candidate genres: %r", candidate_genres)
    untagged_genres = []
    if candidate_genres:
        main_classical_genres = [
            val for val in main_classical_genres_list if val.lower() in [
                genre.lower() for genre in candidate_genres]]
        sub_classical_genres = [
            val for val in sub_classical_genres_list if val.lower() in [
                genre.lower() for genre in candidate_genres]]

        if main_classical_genres or sub_classical_genres or options['cwp_genres_classical_all']:
            is_classical = True
            main_classical_genres.append('Classical')
            candidate_genres.append('Classical')
            write_log(release_id, 'info', "Main classical genres for track %s: %r", tm['title'], main_classical_genres)
            candidate_genres += str_to_list(tm['~cea_work_type_if_classical'])
            # next two are repeated statements, but a separate fn would be
            # clumsy too!
            main_classical_genres = [
                val for val in main_classical_genres_list if val.lower() in [
                    genre.lower() for genre in candidate_genres]]
            sub_classical_genres = [
                val for val in sub_classical_genres_list if val.lower() in [
                    genre.lower() for genre in candidate_genres]]
        if options['cwp_genres_classical_exclude']:
            main_classical_genres = [
                g for g in main_classical_genres if g.lower() != 'classical']

        main_other_genres = [
            val for val in main_other_genres_list if val.lower() in [
                genre.lower() for genre in candidate_genres]]
        sub_other_genres = [
            val for val in sub_other_genres_list if val.lower() in [
                genre.lower() for genre in candidate_genres]]
        all_genres = main_classical_genres + sub_classical_genres + \
            main_other_genres + sub_other_genres
        untagged_genres = [
            un for un in candidate_genres if un.lower() not in [
                genre.lower() for genre in all_genres]]

    if options['cwp_genre_tag']:
        if not options['cwp_genres_filter']:
            append_tag(
                release_id,
                tm,
                options['cwp_genre_tag'],
                candidate_genres)
        else:
            append_tag(
                release_id,
                tm,
                options['cwp_genre_tag'],
                main_classical_genres +
                main_other_genres)
    if options['cwp_subgenre_tag'] and options['cwp_genres_filter']:
        append_tag(
            release_id,
            tm,
            options['cwp_subgenre_tag'],
            sub_classical_genres +
            sub_other_genres)
    if is_classical and options['cwp_genres_flag_text'] and options['cwp_genres_flag_tag']:
        tm[options['cwp_genres_flag_tag']] = options['cwp_genres_flag_text']
    if not (
            main_classical_genres +
            main_other_genres)and options['cwp_genres_filter']:
        if options['cwp_genres_default']:
            append_tag(
                release_id,
                tm,
                options['cwp_genre_tag'],
                options['cwp_genres_default'])
        else:
            if options['cwp_genre_tag'] in tm:
                del tm[options['cwp_genre_tag']]
    if untagged_genres and options['cwp_genres_filter']:
        append_tag(
            release_id,
            tm,
            '003_information:genres',
            'Candidate genres found but not matched: ' +
            list_to_str(untagged_genres))
        append_tag(release_id, tm, '~cwp_untagged_genres', untagged_genres)

    # instruments and keys
    if options['cwp_instruments_MB_names'] and options['cwp_instruments_credited_names'] and tm['~cea_instruments_all']:
        instruments = str_to_list(tm['~cea_instruments_all'])
    elif options['cwp_instruments_MB_names'] and tm['~cea_instruments']:
        instruments = str_to_list(tm['~cea_instruments'])
    elif options['cwp_instruments_credited_names'] and tm['~cea_instruments_credited']:
        instruments = str_to_list(tm['~cea_instruments_credited'])
    else:
        instruments = None
    if instruments and options['cwp_instruments_tag']:
        append_tag(release_id, tm, options['cwp_instruments_tag'], instruments)
        # need to append rather than over-write as it may be the same as
        # another tag (e.g. genre)
    if tm['~cwp_keys'] and options['cwp_key_tag']:
        append_tag(release_id, tm, options['cwp_key_tag'], tm['~cwp_keys'])
    # dates
    if options['cwp_workdate_annotate']:
        comp = ' (composed)'
        publ = ' (published)'
        prem = ' (premiered)'
    else:
        comp = ''
        publ = ''
        prem = ''
    tm[options['cwp_workdate_tag']] = ''
    earliest_date = 9999
    latest_date = -9999
    found = False
    if tm['~cwp_composed_dates']:
        composed_dates_list = str_to_list(tm['~cwp_composed_dates'])
        if len(composed_dates_list) > 1:
            composed_dates_list = str_to_list(
                composed_dates_list[0])  # use dates of lowest-level work
        earliest_date = min([int(dates.split(DATE_SEP)[0].strip())
                             for dates in composed_dates_list])
        append_tag(
            release_id,
            tm,
            options['cwp_workdate_tag'],
            list_to_str(composed_dates_list) +
            comp)
        found = True
    if tm['~cwp_published_dates'] and (
            not found or options['cwp_workdate_use_all']):
        if not found:
            published_dates_list = str_to_list(tm['~cwp_published_dates'])
            if len(published_dates_list) > 1:
                published_dates_list = str_to_list(
                    published_dates_list[0])  # use dates of lowest-level work
            earliest_date = min([int(dates.split(DATE_SEP)[0].strip())
                                 for dates in published_dates_list])
            append_tag(
                release_id,
                tm,
                options['cwp_workdate_tag'],
                list_to_str(published_dates_list) +
                publ)
            found = True
    if tm['~cwp_premiered_dates'] and (
            not found or options['cwp_workdate_use_all']):
        if not found:
            premiered_dates_list = str_to_list(tm['~cwp_premiered_dates'])
            if len(premiered_dates_list) > 1:
                premiered_dates_list = str_to_list(
                    premiered_dates_list[0])  # use dates of lowest-level work
            earliest_date = min([int(dates.split(DATE_SEP)[0].strip())
                                 for dates in premiered_dates_list])
            append_tag(
                release_id,
                tm,
                options['cwp_workdate_tag'],
                list_to_str(premiered_dates_list) +
                prem)

    # periods
    PERIODS = {}
    if options['cwp_period_map']:
        if options['cwp_use_muso_refdb'] and options['cwp_muso_periods'] and PERIOD_DICT:
            for p_item in PERIOD_DICT:
                if 'start' not in p_item or p_item['start'] == []:
                    p_item['start'] = [u'-9999']
                if 'end' not in p_item or p_item['end'] == []:
                    p_item['end'] = [u'2525']
                if 'name' not in p_item or p_item['name'] == []:
                    p_item['name'] = ['NOT SPECIFIED']
            PERIODS = {list_to_str(mp['name']).strip(): (
                list_to_str(mp['start']),
                list_to_str(mp['end']))
                for mp in PERIOD_DICT}
            for period in PERIODS:
                if PERIODS[period][0].lstrip(
                        '-').isdigit() and PERIODS[period][1].lstrip('-').isdigit():
                    PERIODS[period] = (int(PERIODS[period][0]),
                                       int(PERIODS[period][1]))
                else:
                    PERIODS[period] = (
                        9999,
                        'ERROR - start and/or end of ' +
                        period +
                        ' are not integers')

        else:
            periods = [p.strip() for p in options['cwp_period_map'].split(';')]
            for p in periods:
                p = p.split(',')
                if len(p) == 3:
                    period = p[0].strip()
                    start = p[1].strip()
                    end = p[2].strip()
                    if start.lstrip(
                            '-').isdigit() and end.lstrip('-').isdigit():
                        PERIODS[period] = (int(start), int(end))
                    else:
                        PERIODS[period] = (
                            9999,
                            'ERROR - start and/or end of ' +
                            period +
                            ' are not integers')
                else:
                    PERIODS[p[0]] = (
                        9999, 'ERROR in period map - each item must contain 3 elements')
    if options['cwp_period_tag'] and PERIODS:
        if earliest_date == 9999:  # i.e. no work date found
            if options['cwp_use_muso_refdb'] and options['cwp_muso_dates']:
                for composer_born in composer_born_list + arranger_born_list:
                    if composer_born and composer_born.isdigit():
                        birthdate = int(composer_born)
                        # productive age is taken as 20->death as per Muso
                        earliest_date = min(earliest_date, birthdate + 20)
                        for composer_died in composer_died_list + arranger_died_list:
                            if composer_died and composer_died.isdigit():
                                deathdate = int(composer_died)
                                latest_date = max(latest_date, deathdate)
                            else:
                                latest_date = datetime.now().year
        # sort into start date order before writing tags
        sorted_periods = collections.OrderedDict(
            sorted(PERIODS.items(), key=lambda t: t[1]))
        for period in sorted_periods:
            if isinstance(
                    sorted_periods[period][1],
                    str) and 'ERROR' in sorted_periods[period][1]:
                tm[options['cwp_period_tag']] = ''
                append_tag(
                    release_id,
                    tm,
                    '001_errors:9',
                    '9. ' +
                    sorted_periods[period])
                break
            if earliest_date < 9999:
                if sorted_periods[period][0] <= earliest_date <= sorted_periods[period][1]:
                    append_tag(
                        release_id,
                        tm,
                        options['cwp_period_tag'],
                        period)
            if latest_date > -9999:
                if sorted_periods[period][0] <= latest_date <= sorted_periods[period][1]:
                    append_tag(
                        release_id,
                        tm,
                        options['cwp_period_tag'],
                        period)

    # generic tag mapping
    sort_tags = options['cea_tag_sort']
    if sort_tags:
        tm['artists_sort'] = str_to_list(tm['~artists_sort'])
    for i in range(0, 16):
        tagline = options['cea_tag_' + str(i + 1)].split(",")
        source_group = options['cea_source_' + str(i + 1)].split(",")
        conditional = options['cea_cond_' + str(i + 1)]
        for item, tagx in enumerate(tagline):
            tag = tagx.strip()
            sort = sort_suffix(tag)
            if not conditional or tm[tag] == "":
                for source_memberx in source_group:
                    source_member = source_memberx.strip()
                    sourceline = source_member.split("+")
                    if len(sourceline) > 1:
                        source = "\\"
                        for source_itemx in sourceline:
                            source_item = source_itemx.strip()
                            source_itema = source_itemx.lstrip()
                            write_log(
                                    release_id, 'info', "Source_item: %s", source_item)
                            if "~cea_" + source_item in tm:
                                si = tm['~cea_' + source_item]
                            elif "~cwp_" + source_item in tm:
                                si = tm['~cwp_' + source_item]
                            elif source_item in tm:
                                si = tm[source_item]
                            elif len(source_itema) > 0 and source_itema[0] == "\\":
                                si = source_itema[1:]
                            else:
                                si = ""
                            if si != "" and source != "":
                                source = source + si
                            else:
                                source = ""
                    else:
                        source = sourceline[0]
                    no_names_source = re.sub('(_names)$', 's', source)
                    source_sort = sort_suffix(source)
                    write_log(
                            release_id,
                            'info',
                            "Tag mapping: Line: %s, Source: %s, Tag: %s, no_names_source: %s, sort: %s, item %s",
                            i +
                            1,
                            source,
                            tag,
                            no_names_source,
                            sort,
                            item)
                    if '~cea_' + source in tm or '~cwp_' + source in tm:
                        for prefix in ['~cea_', '~cwp_']:
                            if prefix + source in tm:
                                write_log(release_id, 'info', prefix)
                                append_tag(release_id, tm, tag,
                                           tm[prefix + source], ['; '])
                                if sort_tags:
                                    if prefix + no_names_source + source_sort in tm:
                                        write_log(
                                                release_id, 'info', prefix + " sort")
                                        append_tag(release_id, tm, tag + sort,
                                                   tm[prefix + no_names_source + source_sort], ['; '])
                    elif source in tm or '~' + source in tm:
                        write_log(release_id, 'info', "Picard")
                        for p in ['', '~']:
                            if p + source in tm:
                                append_tag(release_id, tm, tag,
                                           tm[p + source], ['; ', '/ '])
                        if sort_tags:
                            if "~" + source + source_sort in tm:
                                source = "~" + source
                            if source + source_sort in tm:
                                write_log(
                                        release_id, 'info', "Picard sort")
                                append_tag(release_id, tm, tag + sort,
                                           tm[source + source_sort], ['; ', '/ '])
                    elif len(source) > 0 and source[0] == "\\":
                        append_tag(release_id, tm, tag,
                                   source[1:], ['; ', '/ '])
                    else:
                        pass

    # write error messages to tags
    if options['log_error'] and "~cea_error" in tm:
        for error in str_to_list(tm['~cea_error']):
            ecode = error[0]
            append_tag(release_id, tm, '001_errors:' + ecode, error)
    if options['log_warning'] and "~cea_warning" in tm:
        for warning in str_to_list(tm['~cea_warning']):
            wcode = warning[0]
            append_tag(release_id, tm, '002_warnings:' + wcode, warning)

    # delete unwanted tags
    if not options['log_debug']:
        if '~cea_works_complete' in tm:
            del tm['~cea_works_complete']
        if '~cea_artists_complete' in tm:
            del tm['~cea_artists_complete']
        del_list = []
        for t in tm:
            if 'ce_tag_cleared' in t:
                del_list.append(t)
        for t in del_list:
            del tm[t]

    # create hidden tags to flag differences
    if options['ce_show_ui_tags'] and options['ce_ui_tags']:
        for heading_name, tag_tuple in UI_TAGS:  # UI_TAGS is already iterated in main routine, so no need for .items() method here
            heading_tag = '~' + heading_name + '_VAL'
            for tag in tag_tuple:
                if tag[-5:] != '_DIFF':
                    append_tag(release_id, tm, heading_tag, tm[tag])
                else:
                    tag = '~' + tag
                    mirror_tags = str_to_list((tm['~ce_mirror_tags']))
                    for mirror_tag in mirror_tags:
                        mt = interpret(mirror_tag)
                        st = str_to_list(mt)
                        (old_tag, new_tag) = tuple(st)
                        diff_name = old_tag.replace('OLD', 'DIFF')
                        if diff_name == tag and  tm[old_tag] != tm[new_tag]:
                            tm[diff_name] = '*****'
                            append_tag(release_id, tm, heading_tag, '*****')
                            break

    # if options over-write enabled, remove it after processing one album
    options['ce_options_overwrite'] = False
    config.setting['ce_options_overwrite'] = False
    # so that options are not retained (in case of refresh with different
    # options)
    if '~ce_options' in tm:
        del tm['~ce_options']

    # remove any unwanted file tags
    if '~ce_file' in tm and tm['~ce_file'] != "None":
        music_file = tm['~ce_file']
        orig_metadata = album.tagger.files[music_file].orig_metadata
        if 'delete_tags' in options and options['delete_tags']:
            warn = []
            for delete_item in options['delete_tags']:
                if delete_item not in tm:  # keep the original for comparison if we have a new version
                    if delete_item in orig_metadata:
                        del orig_metadata[delete_item]
                        if delete_item != '002_warnings:7':  # to avoid circularity!
                            warn.append(delete_item)
            if warn and options['log_warning']:
                append_tag(
                    release_id,
                    tm,
                    '002_warnings:7',
                    '7. Deleted tags: ' +
                    ', '.join(warn))
                write_log(
                    release_id,
                    'warning',
                    'Deleted tags: ' +
                    ', '.join(warn))


def sort_suffix(tag):
    """To determine what sort suffix is appropriate for a given tag"""
    if tag == "composer" or tag == "artist" or tag == "albumartist" or tag == "trackartist" or tag == "~cea_MB_artist":
        sort = "sort"
    else:
        sort = "_sort"
    return sort


def append_tag(release_id, tm, tag, source, separators=None):
    """
    Update a tag
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param tm: track metadata
    :param tag: tag to be appended to
    :param source: item to append to tag
    :param separators: characters which may be used to split string into a list
        (any of the characters will be a split point)
    :return: None. Action is on tm
    """
    if not separators:
        separators = []
    if tag and tag != "":
        if config.setting['log_info']:
            write_log(
                release_id,
                'info',
                'Appending source: %r to tag: %s (source is type %s) ...',
                source,
                tag,
                type(source))
            if tag in tm:
                write_log(
                    release_id,
                    'info',
                    '... existing tag contents = %r',
                    tm[tag])
        if source and len(source) > 0:
            if isinstance(source, str):
                if separators:
                    source = re.split('|'.join(separators), source)
                else:
                    source = [source]
            if not isinstance(source, list):
                source = [source]  # typically for dict items such as saved options
            if all([isinstance(x, str) for x in source]):  # only append if if source is a list of strings
                if tag not in tm:
                    if tag == 'artists_sort':
                        # There is no artists_sort tag in Picard - just a
                        # hidden var ~artists_sort, so pick up those into the new tag
                        hidden = tm['~artists_sort']
                        if not isinstance(hidden, list):
                            if separators:
                                hidden = re.split(
                                    '|'.join(separators), hidden)
                                for i, h in enumerate(hidden):
                                    hidden[i] = h.strip()
                            else:
                                hidden = [hidden]
                        source = add_list_uniquely(source, hidden)
                    new_tag = True
                else:
                    new_tag = False

                for source_item in source:
                    if isinstance(source_item, str):
                        source_item = source_item.replace(u'\u2010', u'-')
                        source_item = source_item.replace(u'\u2011', u'-')
                        source_item = source_item.replace(u'\u2019', u"'")
                        source_item = source_item.replace(u'\u2018', u"'")
                        source_item = source_item.replace(u'\u201c', u'"')
                        source_item = source_item.replace(u'\u201d', u'"')
                    if new_tag:
                        tm[tag] = [source_item]
                        new_tag = False
                    else:
                        if not isinstance(tm[tag], list):
                            if separators:
                                tag_list = re.split(
                                    '|'.join(separators), tm[tag])
                                for i, t in enumerate(tag_list):
                                    tag_list[i] = t.strip()
                            else:
                                tag_list = [tm[tag]]
                        else:
                            tag_list = tm[tag]
                        if source_item not in tm[tag]:
                            tag_list.append(source_item)
                            tm[tag] = tag_list
                    # NB tag_list is used as metadata object will convert single-item lists to strings
            else:  # source items are not strings, so just replace
                tm[tag] = source

def get_artist_credit(options, release_id, obj):
    """
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param options:
    :param obj: an XmlNode
    :return: a list of as-credited names
    """
    name_credit_list = parse_data(release_id, obj, [], 'artist-credit')
    credit_list = []
    if name_credit_list:
        for name_credits in name_credit_list:
            for name_credit in name_credits:
                credited_artist = parse_data(
                    release_id, name_credit, [], 'name')
                if credited_artist:
                    name = parse_data(
                        release_id, name_credit, [], 'artist', 'name')
                    sort_name = parse_data(
                        release_id, name_credit, [], 'artist', 'sort-name')
                    credit_item = (credited_artist, name, sort_name)
                    credit_list.append(credit_item)
        return credit_list


def get_aliases_and_credits(
        self,
        options,
        release_id,
        album,
        obj,
        lang,
        credited):
    """
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param album:
    :param self: This relates to the object in the class which called this function
    :param options:
    :param obj: an XmlNode
    :param lang: The language selected in the Picard metadata options
    :param credited: The options item to determine what as-credited names are being sought
    :return: None. Sets self.artist_aliases and self.artist_credits[album]
    """
    name_credit_list = parse_data(release_id, obj, [], 'artist-credit')
    artist_list = parse_data(release_id, name_credit_list, [], 'artist')
    for artist in artist_list:
        sort_names = parse_data(release_id, artist, [], 'sort-name')
        if sort_names:
            aliases = parse_data(release_id, artist, [], 'aliases', 'locale:' +
                                 lang, 'primary:True', 'name')
            if aliases:
                self.artist_aliases[sort_names[0]] = aliases[0]
    if credited:
        for name_credit in name_credit_list[0]:
            credited_artist = parse_data(release_id, name_credit, [], 'name')
            if credited_artist:
                sort_name = parse_data(
                    release_id, name_credit, [], 'artist', 'sort-name')
                if sort_name:
                    self.artist_credits[album][sort_name[0]
                                               ] = credited_artist[0]


def get_relation_credits(
        self,
        options,
        release_id,
        album,
        obj,
        lang,
        credited):
    """
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param self:
    :param options: UI options
    :param album: current album
    :param obj: Xmlnode
    :param lang: language
    :param credited: credited-as name
    :return: None
    Note that direct recording relationships will over-ride indirect ones (via work)
    """

    rels = parse_data(release_id, obj, [], 'relations', 'target-type:work',
                      'work', 'relations', 'target-type:artist')

    for artist in rels:
        sort_names = parse_data(release_id, artist, [], 'artist', 'sort-name')
        if sort_names:
            credited_artists = parse_data(
                release_id, artist, [], 'target-credit')
            if credited_artists and credited_artists[0] != '' and credited:
                self.artist_credits[album][sort_names[0]
                                           ] = credited_artists[0]
            aliases = parse_data(
                release_id,
                artist,
                [],
                'artist',
                'aliases',
                'locale:' + lang,
                'primary:True',
                'name')
            if aliases:
                self.artist_aliases[sort_names[0]] = aliases[0]

    rels2 = parse_data(release_id, obj, [], 'relations', 'target-type:artist')

    for artist in rels2:
        sort_names = parse_data(release_id, artist, [], 'artist', 'sort-name')
        if sort_names:
            credited_artists = parse_data(
                release_id, artist, [], 'target-credit')
            if credited_artists and credited_artists[0] != '' and credited:
                self.artist_credits[album][sort_names[0]
                                           ] = credited_artists[0]
            aliases = parse_data(
                release_id,
                artist,
                [],
                'artist',
                'aliases',
                'locale:' + lang,
                'primary:True',
                'name')
            if aliases:
                self.artist_aliases[sort_names[0]] = aliases[0]


def composer_last_names(self, release_id, tm, album):
    """
    :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
    :param self:
    :param tm:
    :param album:
    :return: None
    Sets composer last names for album prefixing
    """
    if '~cea_album_track_composer_lastnames' in tm:
        if not isinstance(tm['~cea_album_track_composer_lastnames'], list):
            atc_list = re.split(
                '|'.join(
                    self.SEPARATORS),
                tm['~cea_album_track_composer_lastnames'])
        else:
            atc_list = str_to_list(tm['~cea_album_track_composer_lastnames'])
        for atc_item in atc_list:
            composer_lastnames = atc_item.strip()
            if '~length' in tm and tm['~length']:
                track_length = time_to_secs(tm['~length'])
            else:
                track_length = 0
            if album in self.album_artists:
                if 'composer_lastnames' in self.album_artists[album]:
                    if composer_lastnames not in self.album_artists[album]['composer_lastnames']:
                        self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                            'length': track_length}
                    else:
                        self.album_artists[album]['composer_lastnames'][composer_lastnames]['length'] += track_length
                else:
                    self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                        'length': track_length}
            else:
                self.album_artists[album]['composer_lastnames'][composer_lastnames] = {
                    'length': track_length}
    else:
        write_log(
                release_id,
                'warning',
                "No _cea_album_track_composer_lastnames variable available for recording \"%s\".",
                tm['title'])
        if 'composer' in tm:
            self.append_tag(
                release_id,
                release_id,
                tm,
                '~cea_warning',
                '1. Composer for this track is not in album artists and will not be available to prefix album')
        else:
            self.append_tag(
                release_id,
                release_id,
                tm,
                '~cea_warning',
                '1. No composer for this track, but checking parent work.')


def add_list_uniquely(list_to, list_from):
    """
    Adds any items in list_from to list_to, if they are not already present
    If either arg is a string, it will be converted to a list, e.g. 'abc' -> ['abc']
    :param list_to:
    :param list_from:
    :return: appends only unique elements of list 2 to list 1
    """
    #
    if list_to and list_from:
        if not isinstance(list_to, list):
            list_to = str_to_list(list_to)
        if not isinstance(list_from, list):
            list_from = str_to_list(list_from)
        for list_item in list_from:
            if list_item not in list_to:
                list_to.append(list_item)
    else:
        if list_from:
            list_to = list_from
    return list_to


def str_to_list(s):
    """
    :param s:
    :return: list from string using ; as separator
    """
    if isinstance(s, list):
        return s
    if not isinstance(s, str):
        try:
            return list(s)
        except TypeError:
            return []
    else:
        if s == '':
            return []
        else:
            return s.split('; ')


def list_to_str(l):
    """
    :param l:
    :return: string from list using ; as separator
    """
    if not isinstance(l, list):
        return l
    else:
        return '; '.join(l)


def interpret(tag):
    """
    :param tag:
    :return: safe form of eval(tag)
    """
    if isinstance(tag, str):
        try:
            tag = tag.strip(' \n\t')
            return ast.literal_eval(tag)
        except (SyntaxError, ValueError):
            return tag
    else:
        return tag


def time_to_secs(a):
    """
    :param a: string x:x:x
    :return: seconds
    converts string times to seconds
    """
    ax = a.split(':')
    ax = ax[::-1]
    t = 0
    for i, x in enumerate(ax):
        if x.isdigit():
            t += int(x) * (60 ** i)
        else:
            return 0
    return t


def seq_last_names(self, album):
    """
    Sequences composer last names for album prefix by the total lengths of their tracks
    :param self:
    :param album:
    :return:
    """
    ln = []
    if album in self.album_artists and 'composer_lastnames' in self.album_artists[album]:
        for x in self.album_artists[album]['composer_lastnames']:
            if 'length' in self.album_artists[album]['composer_lastnames'][x]:
                ln.append([x, self.album_artists[album]
                           ['composer_lastnames'][x]['length']])
            else:
                return []
        ln = sorted(ln, key=lambda a: a[1])
        ln = ln[::-1]
    return [a[0] for a in ln]


def year(date):
    """
    Return YYYY portion of date(s) in YYYY-MM-DD format (may be incomplete, string or list)
    :param date:
    :return: YYYY
    """
    if isinstance(date, list):
        year_list = [blank_if_none(d).split('-')[0] for d in date]
        return year_list
    else:
        date_list = blank_if_none(date).split('-')
        return [date_list[0]]


def blank_if_none(val):
    """
    Make NoneTypes strings
    :param val: str or None
    :return: str
    """
    if not val:
        return ''
    else:
        return val


def strip_excess_punctuation(s):
    """
    remove orphan punctuation, unmatched quotes and brackets
    :param s: string
    :return: string
    """
    if s:
        s_prev = ''
        counter = 0
        while s != s_prev:
            if counter > 100:
                break  # safety valve
            s_prev = s
            s = s.replace('  ', ' ')
            s = s.strip("&.-:;, ")
            s = s.lstrip("!)]}")
            s = s.rstrip("([{")
            s = s.lstrip(u"\u2019") # Right single quote
            s = s.lstrip(u"\u201D") # Right double quote
            if s.count(u"\u201E") == 0: # u201E is lower double quote (German etc.)
                s = s.rstrip(u"\u201C") # Left double quote - only strip if there is no German-style lower quote present
            s = s.rstrip(u"\u2018") # Left single quote
            if s.count('"') % 2 != 0:
                s = s.strip('"')
            if s.count("'") % 2 != 0:
                s = s.strip("'")
            if len(s) > 0 and s[0] == u"\u201C" and s.count(u"\u201D") == 0:
                s = s.lstrip(u"\u201C")
            if len(s) > 0 and s[-1] == u"\u201D" and s.count(u"\u201C") == 0 and s.count(u"\u201E") == 0:  # only strip if there is no German-style lower quote present
                s = s.rstrip(u"\u201D")
            if len(s) > 0 and s[0] == u"\u2018" and s.count(u"\u2019") == 0:
                s = s.lstrip(u"\u2018")
            if len(s) > 0 and s[-1] == u"\u2019" and s.count(u"\u2018") == 0:
                s = s.rstrip(u"\u2019")
            if s:
                if s.count("\"") == 1:
                    s = s.replace('"', '')
                if s.count("\'") == 1:
                    s = s.replace(" '", " ")
                    # s = s.replace("' ", " ") # removed to prevent removal of genuine apostrophes
                if "(" in s and ")" not in s:
                    s = s.replace("(", "")
                if ")" in s and "(" not in s:
                    s = s.replace(")", "")
                if "[" in s and "]" not in s:
                    s = s.replace("[", "")
                if "]" in s and "[" not in s:
                    s = s.replace("]", "")
                if "{" in s and "}" not in s:
                    s = s.replace("{", "")
                if "}" in s and "{" not in s:
                    s = s.replace("}", "")
            if s:
                match_chars = [("(", ")"), ("[", "]"), ("{", "}")]
                last = len(s) - 1
                for char_pair in match_chars:
                    if char_pair[0] == s[0] and char_pair[1] == s[last]:
                        s = s.lstrip(char_pair[0]).rstrip(char_pair[1])
            counter += 1
    return s


#################
#################
# EXTRA ARTISTS #
#################
#################


class ExtraArtists():

    # CONSTANTS
    def __init__(self):
        self.album_artists = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of artists to be applied at album level

        self.track_listing = collections.defaultdict(list)
        # collection of tracks - format is {album: [track 1,
        # track 2, ...]}

        self.options = collections.defaultdict(dict)
        # collection of Classical Extras options

        self.globals = collections.defaultdict(dict)
        # collection of global variables for this class

        self.album_performers = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of performers who have release relationships, not track
        # relationships

        self.album_instruments = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of instruments which have release relationships, not track
        # relationships

        self.artist_aliases = {}
        # collection of alias names - format is {sort_name: alias_name, ...}

        self.artist_credits = collections.defaultdict(dict)
        # collection of credited-as names - format is {album: {sort_name: credit_name,
        # ...}, ...}

        self.release_artists_sort = collections.defaultdict(list)
        # collection of release artists - format is {album: [sort_name_1,
        # sort_name_2, ...]}

        self.lyricist_filled = collections.defaultdict(dict)
        # Boolean for each track to indicate if lyricist has been found (don't
        # want to add more from higher levels)
        # NB this last one is for completeness - not actually used by
        # ExtraArtists, but here to remove pep8 error

        self.album_series_list = collections.defaultdict(dict)
        # series relationships - format is {'name_list': series names, 'id_list': series ids, 'number_list': number within series}

    def add_artist_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):
        """
        Main routine run for each track of release
        :param album: Current release
        :param track_metadata: track metadata dictionary
        :param trackXmlNode: Everything in the track node downwards
        :param releaseXmlNode: Everything in the release node downwards (so includes all track nodes)
        :return:
        """
        release_id = track_metadata['musicbrainz_albumid']
        if 'start' not in release_status[release_id]:
            release_status[release_id]['start'] = datetime.now()
        if 'lookups' not in release_status[release_id]:
            release_status[release_id]['lookups'] = 0
        release_status[release_id]['name'] = track_metadata['album']
        release_status[release_id]['artists'] = True
        if config.setting['log_debug'] or config.setting['log_info']:
            write_log(
                release_id,
                'debug',
                'STARTING ARTIST PROCESSING FOR ALBUM %s, DISC %s, TRACK %s',
                track_metadata['album'],
                track_metadata['discnumber'],
                track_metadata['tracknumber'] +
                ' ' +
                track_metadata['title'])
        # write_log(release_id, 'info', 'trackXmlNode = %s', trackXmlNode) # NB can crash Picard
        # write_log('info', 'releaseXmlNode = %s', releaseXmlNode) # NB can crash Picard
        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]
        tm = track.metadata

        # OPTIONS - OVER-RIDE IF REQUIRED
        if '~ce_options' not in tm:
            if config.setting['log_debug'] or config.setting['log_info']:
                write_log(release_id, 'debug', 'Artists gets track first...')
            get_options(release_id, album, track)
        options = interpret(tm['~ce_options'])
        if not options:
            if config.setting["log_error"]:
                write_log(
                    release_id,
                    'error',
                    'Artists. Failure to read saved options for track %s. options = %s',
                    track,
                    tm['~ce_options'])
            options = option_settings(config.setting)
        self.options[track] = options

        # CONSTANTS
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.ORCHESTRAS = options["cea_orchestras"].split(',')
        self.CHOIRS = options["cea_choirs"].split(',')
        self.GROUPS = options["cea_groups"].split(',')
        self.ENSEMBLE_TYPES = self.ORCHESTRAS + self.CHOIRS + self.GROUPS
        self.SEPARATORS = ['; ', '/ ', ';', '/']

        # continue?
        if not options["classical_extra_artists"]:
            return
        # album_files is not used - this is just for logging
        album_files = album.tagger.get_files_from_objects([album])
        if options['log_info']:
            write_log(
                release_id,
                'info',
                'ALBUM FILENAMES for album %r = %s',
                album,
                album_files)

        if not (
            options["ce_no_run"] and (
                not tm['~ce_file'] or tm['~ce_file'] == "None")):
            # continue
            write_log(
                    release_id,
                    'debug',
                    "ExtraArtists - add_artist_info")
            if album not in self.track_listing or track not in self.track_listing[album]:
                self.track_listing[album].append(track)
            # fix odd hyphens in names for consistency
            field_types = ['~albumartists', '~albumartists_sort']
            for field_type in field_types:
                if field_type in tm:
                    field = tm[field_type]
                    if isinstance(field, list):
                        for x, it in enumerate(field):
                            field[x] = it.replace(u'\u2010', u'-')
                    elif isinstance(field, str):
                        field = field.replace(u'\u2010', u'-')
                    else:
                        pass
                    tm[field_type] = field

            # first time for this album (reloads each refresh)
            if tm['discnumber'] == '1' and tm['tracknumber'] == '1':
                # get artist aliases - these are cached so can be re-used across
                # releases, but are reloaded with each refresh
                get_aliases(self, release_id, album, options, releaseXmlNode)

                # xml_type = 'release'
                # get performers etc who are related at the release level
                relation_list = parse_data(
                    release_id, releaseXmlNode, [], 'relations')
                album_performerList = get_artists(
                    options, release_id, tm, relation_list, 'release')['artists']
                self.album_performers[album] = album_performerList
                album_instrumentList = get_artists(
                    options, release_id, tm, relation_list, 'release')['instruments']
                self.album_instruments[album] = album_instrumentList

                # get series information
                self.album_series_list = get_series(
                    options, release_id, relation_list)

            else:
                if album in self.album_performers:
                    album_performerList = self.album_performers[album]
                else:
                    album_performerList = []
                if album in self.album_instruments and self.album_instruments[album]:
                    tm['~cea_instruments'] = self.album_instruments[album][0]
                    tm['~cea_instruments_credited'] = self.album_instruments[album][1]
                    tm['~cea_instruments_all'] = self.album_instruments[album][2]
                    # Should be OK to initialise these here as recording artists
                    # yet to be processed

            # Fill release info not given by vanilla Picard
            if self.album_series_list:
                tm['series'] = self.album_series_list['name_list'] if 'name_list' in self.album_series_list else None
                tm['musicbrainz_seriesid'] = self.album_series_list['id_list'] if 'id_list' in self.album_series_list else None
                tm['series_number'] = self.album_series_list['number_list'] if 'number_list' in self.album_series_list else None
                ## TODO add label id too
            recording_relation_list = parse_data(
                release_id, trackXmlNode, [], 'recording', 'relations')
            recording_series_list = get_series(
                options, release_id, recording_relation_list)
            write_log(
                release_id,
                'info',
                'Recording_series_list = %s',
                recording_series_list)

            track_artist_list = parse_data(
                release_id, trackXmlNode, [], 'artist-credit')
            if track_artist_list:
                track_artist = []
                track_artistsort = []
                track_artists = []
                track_artists_sort = []
                locale = config.setting["artist_locale"]
                # NB this is the Picard code in /util
                lang = locale.split("_")[0]

                # Set naming option
                # Put naming style into preferential list

                # naming as for vanilla Picard for track artists

                if options['translate_artist_names'] and lang:
                    name_style = ['alias', 'sort']
                    # documentation indicates that processing should be as below,
                    # but processing above appears to reflect what vanilla Picard actually does
                    # if options['standardize_artists']:
                    #     name_style = ['alias', 'sort']
                    # else:
                    #     name_style = ['alias', 'credit', 'sort']
                else:
                    if not options['standardize_artists']:
                        name_style = ['credit']
                    else:
                        name_style = []
                write_log(
                        release_id,
                        'info',
                        'Priority order of naming style for track artists = %s',
                        name_style)
                styled_artists = apply_artist_style(
                    options,
                    release_id,
                    lang,
                    track_artist_list,
                    name_style,
                    track_artist,
                    track_artistsort,
                    track_artists,
                    track_artists_sort)
                tm['artists'] = styled_artists['artists']
                tm['~artists_sort'] = styled_artists['artists_sort']
                tm['artist'] = styled_artists['artist']
                tm['artistsort'] = styled_artists['artistsort']

            if 'recording' in trackXmlNode:
                self.globals[track]['is_recording'] = True
                write_log(release_id, 'debug', 'Getting recording details')
                recording = trackXmlNode['recording']
                if not isinstance(recording, list):
                    recording = [recording]
                for record in recording:
                    rec_type = type(record)
                    write_log(release_id, 'info', 'rec-type = %s', rec_type)
                    write_log(release_id, 'info', record)
                    # Note that the lists below reflect https://musicbrainz.org/relationships/artist-recording
                    # Any changes to that DB structure will require changes
                    # here

                    # get recording artists data
                    recording_artist_list = parse_data(
                        release_id, record, [], 'artist-credit')
                    if recording_artist_list:
                        recording_artist = []
                        recording_artistsort = []
                        recording_artists = []
                        recording_artists_sort = []
                        locale = config.setting["artist_locale"]
                        # NB this is the Picard code in /util
                        lang = locale.split("_")[0]

                        # Set naming option
                        # Put naming style into preferential list

                        # naming as for vanilla Picard for track artists (per
                        # documentation rather than actual?)
                        if options['cea_ra_trackartist']:
                            if options['translate_artist_names'] and lang:
                                if options['standardize_artists']:
                                    name_style = ['alias', 'sort']
                                else:
                                    name_style = ['alias', 'credit', 'sort']
                            else:
                                if not options['standardize_artists']:
                                    name_style = ['credit']
                                else:
                                    name_style = []
                        # naming as for performers in classical extras
                        elif options['cea_ra_performer']:
                            if options['cea_aliases']:
                                if options['cea_alias_overrides']:
                                    name_style = ['alias', 'credit']
                                else:
                                    name_style = ['credit', 'alias']
                            else:
                                name_style = ['credit']

                        else:
                            name_style = []
                        write_log(
                                release_id,
                                'info',
                                'Priority order of naming style for recording artists = %s',
                                name_style)

                        styled_artists = apply_artist_style(
                            options,
                            release_id,
                            lang,
                            recording_artist_list,
                            name_style,
                            recording_artist,
                            recording_artistsort,
                            recording_artists,
                            recording_artists_sort)
                        self.append_tag(
                            release_id,
                            tm,
                            '~cea_recording_artists',
                            styled_artists['artists'])
                        self.append_tag(
                            release_id,
                            tm,
                            '~cea_recording_artists_sort',
                            styled_artists['artists_sort'])
                        self.append_tag(
                            release_id,
                            tm,
                            '~cea_recording_artist',
                            styled_artists['artist'])
                        self.append_tag(
                            release_id,
                            tm,
                            '~cea_recording_artistsort',
                            styled_artists['artistsort'])

                    else:
                        tm['~cea_recording_artists'] = ''
                        tm['~cea_recording_artists_sort'] = ''
                        tm['~cea_recording_artist'] = ''
                        tm['~cea_recording_artistsort'] = ''

                    # use recording artist options
                    tm['~cea_MB_artist'] = str_to_list(tm['artist'])
                    tm['~cea_MB_artistsort'] = str_to_list(tm['artistsort'])
                    tm['~cea_MB_artists'] = str_to_list(tm['artists'])
                    tm['~cea_MB_artists_sort'] = str_to_list(tm['~artists_sort'])

                    if options['cea_ra_use']:
                        if options['cea_ra_replace_ta']:
                            if tm['~cea_recording_artist']:
                                tm['artist'] = str_to_list(tm['~cea_recording_artist'])
                                tm['artistsort'] = str_to_list(tm['~cea_recording_artistsort'])
                                tm['artists'] = str_to_list(tm['~cea_recording_artists'])
                                tm['~artists_sort'] = str_to_list(tm['~cea_recording_artists_sort'])
                            elif not options['cea_ra_noblank_ta']:
                                tm['artist'] = ''
                                tm['artistsort'] = ''
                                tm['artists'] = ''
                                tm['~artists_sort'] = ''
                        elif options['cea_ra_merge_ta']:
                            if tm['~cea_recording_artist']:
                                tm['artists'] = add_list_uniquely(
                                    tm['artists'], tm['~cea_recording_artists'])
                                tm['~artists_sort'] = add_list_uniquely(
                                    tm['~artists_sort'], tm['~cea_recording_artists_sort'])
                                if tm['artist'] != tm['~cea_recording_artist']:
                                    tm['artist'] = tm['artist'] + \
                                        ' (' + tm['~cea_recording_artist'] + ')'
                                    tm['artistsort'] = tm['artistsort'] + \
                                        ' (' + tm['~cea_recording_artistsort'] + ')'

                    # xml_type = 'recording'
                    relation_list = parse_data(
                        release_id, record, [], 'relations')
                    performerList = album_performerList + \
                        get_artists(options, release_id, tm, relation_list, 'recording')['artists']
                    # returns
                    # [(artist type, instrument or None, artist name, artist sort name, instrument sort, type sort)]
                    # where instrument sort places solo ahead of additional etc.
                    # and type sort applies a custom sequencing to the artist
                    # types
                    if performerList:
                        write_log(
                                release_id, 'info', "Performers: %s", performerList)
                        self.set_performer(
                            release_id, album, track, performerList, tm)
                    if not options['classical_work_parts']:
                        work_artist_list = parse_data(
                            release_id,
                            record,
                            [],
                            'relations',
                            'target-type:work',
                            'type:performance',
                            'work',
                            'relations',
                            'target-type:artist')
                        work_artists = get_artists(
                            options, release_id, tm, work_artist_list, 'work')['artists']
                        set_work_artists(
                            self, release_id, album, track, work_artists, tm, 0)
                    # otherwise composers etc. will be set in work parts
            else:
                self.globals[track]['is_recording'] = False
        else:
            tm['000_major_warning'] = "WARNING: Classical Extras not run for this track as no file present - " \
                "deselect the option on the advanced tab to run. If there is a file, then try 'Refresh'."
        if track_metadata['tracknumber'] == track_metadata['totaltracks'] and track_metadata[
                'discnumber'] == track_metadata['totaldiscs']:  # last track
            self.process_album(release_id, album)
            release_status[release_id]['artists-done'] = datetime.now()
            close_log(release_id, 'artists')

    # Checks for ensembles
    def ensemble_type(self, performer):
        """
        Returns ensemble types
        :param performer:
        :return:
        """
        for ensemble_name in self.ORCHESTRAS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Orchestra'
        for ensemble_name in self.CHOIRS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Choir'
        for ensemble_name in self.GROUPS:
            ensemble = re.compile(
                r'(.*)\b' +
                ensemble_name +
                r'\b(.*)',
                re.IGNORECASE)
            if ensemble.search(performer):
                return 'Group'
        return False

    def process_album(self, release_id, album):
        """
        Perform final processing after all tracks read
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :return:
        """
        write_log(
                release_id,
                'debug',
                'ExtraArtists: Starting process_album')
        # process lyrics tags
        write_log(release_id, 'debug', 'Starting lyrics processing')
        common = []
        tmlyrics_dict = {}
        tmlyrics_sort = []
        options = {}
        for track in self.track_listing[album]:
            options = self.options[track]
            if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
                tm = track.metadata
                lyrics_tag = options['cea_lyrics_tag']
                if tm[lyrics_tag]:
                    # turn text into word lists to speed processing
                    tmlyrics_dict[track] = tm[lyrics_tag].split()
        if tmlyrics_dict:
            tmlyrics_sort = sorted(
                tmlyrics_dict.items(),
                key=operator.itemgetter(1))
            prev = None
            first_track = None
            unique_lyrics = []
            ref_track = {}
            for lyric_tuple in tmlyrics_sort:  # tuple is (track, lyrics)
                if lyric_tuple[1] != prev:
                    unique_lyrics.append(lyric_tuple[1])
                    first_track = lyric_tuple[0]
                ref_track[lyric_tuple[0]] = first_track
                prev = lyric_tuple[1]
            common = turbo_lcs(
                release_id,
                unique_lyrics)

        if common:
            unique = []
            for tup in tmlyrics_sort:
                track = tup[0]
                ref = ref_track[track]
                if track == ref:
                    start = substart_finder(tup[1], common)
                    length = len(common)
                    end = min(start + length, len(tup[1]))
                    unique = tup[1][:start] + tup[1][end:]

                options = self.options[track]
                if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
                    tm = track.metadata
                    if unique:
                        tm['~cea_track_lyrics'] = ' '.join(unique)
                    tm['~cea_album_lyrics'] = ' '.join(common)
                    if options['cea_album_lyrics']:
                        tm[options['cea_album_lyrics']] = tm['~cea_album_lyrics']
                    if unique and options['cea_track_lyrics']:
                        tm[options['cea_track_lyrics']] = tm['~cea_track_lyrics']
        else:
            for track in self.track_listing[album]:
                options = self.options[track]
                if options['cea_split_lyrics'] and options['cea_lyrics_tag']:
                    tm['~cea_track_lyrics'] = tm[options['cea_lyrics_tag']]
                    if options['cea_track_lyrics']:
                        tm[options['cea_track_lyrics']] = tm['~cea_track_lyrics']
        write_log(release_id, 'debug', 'Ending lyrics processing')

        for track in self.track_listing[album]:
            self.write_metadata(release_id, options, album, track)
        self.track_listing[album] = []
        write_log(
                release_id,
                'info',
                "FINISHED Classical Extra Artists. Album: %s",
                album)


    def write_metadata(self, release_id, options, album, track):
        """
        Write the metadata for this track
        :param release_id:
        :param options:
        :param album:
        :param track:
        :return:
        """
        options = self.options[track]
        tm = track.metadata
        tm['~cea_version'] = PLUGIN_VERSION

        # set inferred genres before any tags are blanked
        if options['cwp_genres_infer']:
            self.infer_genres(release_id, options, track, tm)

        # album
        if not options['classical_work_parts']:
            if 'composer_lastnames' in self.album_artists[album]:
                last_names = seq_last_names(self, album)
                self.append_tag(
                    release_id,
                    tm,
                    '~cea_album_composer_lastnames',
                    last_names)
        # otherwise this is done in the workparts class, which has all
        # composer info

        # process tag mapping
        tm['~cea_artists_complete'] = "Y"
        map_tags(options, release_id, album, tm)

        # write out options and errors/warnings to tags
        if options['cea_options_tag'] != "":
            self.cea_options = collections.defaultdict(
                lambda: collections.defaultdict(
                    lambda: collections.defaultdict(dict)))

            for opt in plugin_options(
                    'artists') + plugin_options('tag') + plugin_options('picard'):
                if 'name' in opt:
                    if 'value' in opt:
                        if options[opt['option']]:
                            self.cea_options['Classical Extras']['Artists options'][opt['name']] = opt['value']
                    else:
                        self.cea_options['Classical Extras']['Artists options'][opt['name']
                        ] = options[opt['option']]

            for opt in plugin_options('tag_detail'):
                if opt['option'] != "":
                    name_list = opt['name'].split("_")
                    self.cea_options['Classical Extras']['Artists options'][name_list[0]
                    ][name_list[1]] = options[opt['option']]

            if options['ce_version_tag'] and options['ce_version_tag'] != "":
                self.append_tag(release_id, tm, options['ce_version_tag'], str(
                    'Version ' + tm['~cea_version'] + ' of Classical Extras'))
            if options['cea_options_tag'] and options['cea_options_tag'] != "":
                self.append_tag(
                    release_id,
                    tm,
                    options['cea_options_tag'] +
                    ':artists_options',
                    json.loads(
                        json.dumps(
                            self.cea_options)))


    def infer_genres(self, release_id, options, track, tm):
        """
        Infer a genre from the artist/instrument metadata
        :param release_id:
        :param options:
        :param track:
        :param tm: track metadata
        :return:
        """
        # Note that this is now mixed in with other sources of genres in def map_tags
        # ~cea_work_type_if_classical is used for types that are specifically classical
        # and is only applied in map_tags if the track is deemed to be
        # classical
        if (self.globals[track]['is_recording'] and options['classical_work_parts']
                and '~artists_sort' in tm and 'composersort' in tm
                and any(x in tm['~artists_sort'] for x in tm['composersort'])
                and 'writer' not in tm
                and not any(x in tm['~artists_sort'] for x in tm['~cea_performers_sort'])):
            self.append_tag(
                release_id, tm, '~cea_work_type', 'Classical')

        if isinstance(tm['~cea_soloists'], str):
            soloists = re.split(
                '|'.join(
                    self.SEPARATORS),
                tm['~cea_soloists'])
        else:
            soloists = tm['~cea_soloists']
        if '~cea_vocalists' in tm:
            if isinstance(tm['~cea_vocalists'], str):
                vocalists = re.split(
                    '|'.join(
                        self.SEPARATORS),
                    tm['~cea_vocalists'])
            else:
                vocalists = tm['~cea_vocalists']
        else:
            vocalists = []

        if '~cea_ensembles' in tm:
            large = False
            if 'performer:orchestra' in tm:
                large = True
                self.append_tag(
                    release_id, tm, '~cea_work_type_if_classical', 'Orchestral')
                if '~cea_soloists' in tm:
                    if 'vocals' in tm['~cea_instruments_all']:
                        self.append_tag(
                            release_id, tm, '~cea_work_type', 'Vocal')
                    if len(soloists) == 1:
                        if soloists != vocalists:
                            self.append_tag(
                                release_id, tm, '~cea_work_type_if_classical', 'Concerto')
                        else:
                            self.append_tag(
                                release_id, tm, '~cea_work_type_if_classical', 'Aria')
                    elif len(soloists) == 2:
                        self.append_tag(
                            release_id, tm, '~cea_work_type_if_classical', 'Duet')
                        if not vocalists:
                            self.append_tag(
                                release_id, tm, '~cea_work_type_if_classical', 'Concerto')
                    elif len(soloists) == 3:
                        self.append_tag(
                            release_id, tm, '~cea_work_type_if_classical', 'Trio')
                    elif len(soloists) == 4:
                        self.append_tag(
                            release_id, tm, '~cea_work_type_if_classical', 'Quartet')

            if 'performer:choir' in tm or 'performer:choir vocals' in tm:
                large = True
                self.append_tag(
                    release_id, tm, '~cea_work_type_if_classical', 'Choral')
                self.append_tag(
                    release_id, tm, '~cea_work_type', 'Vocal')
            else:
                if large and 'soloists' in tm and tm['soloists'].count(
                        'vocals') > 1:
                    self.append_tag(
                        release_id, tm, '~cea_work_type_if_classical', 'Opera')
            if not large:
                if '~cea_soloists' not in tm:
                    self.append_tag(
                        release_id, tm, '~cea_work_type_if_classical', 'Chamber music')
                else:
                    if vocalists:
                        self.append_tag(
                            release_id, tm, '~cea_work_type', 'Song')
                        self.append_tag(
                            release_id, tm, '~cea_work_type', 'Vocal')
                    else:
                        self.append_tag(
                            release_id, tm, '~cea_work_type_if_classical', 'Chamber music')
        else:
            if len(soloists) == 1:
                if vocalists != soloists:
                    self.append_tag(
                        release_id, tm, '~cea_work_type', 'Instrumental')
                else:
                    self.append_tag(
                        release_id, tm, '~cea_work_type', 'Song')
                    self.append_tag(
                        release_id, tm, '~cea_work_type', 'Vocal')
            elif len(soloists) == 2:
                self.append_tag(
                    release_id, tm, '~cea_work_type_if_classical', 'Duet')
            elif len(soloists) == 3:
                self.append_tag(
                    release_id, tm, '~cea_work_type_if_classical', 'Trio')
            elif len(soloists) == 4:
                self.append_tag(
                    release_id, tm, '~cea_work_type_if_classical', 'Quartet')
            else:
                if not vocalists:
                    self.append_tag(
                        release_id, tm, '~cea_work_type_if_classical', 'Chamber music')
                else:
                    self.append_tag(
                        release_id, tm, '~cea_work_type', 'Song')
                    self.append_tag(
                        release_id, tm, '~cea_work_type', 'Vocal')


    def append_tag(self, release_id, tm, tag, source):
        """
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param tm:
        :param tag:
        :param source:
        :return:
        """
        write_log(
                release_id,
                'info',
                "Extra Artists - appending %s to %s",
                source,
                tag)
        append_tag(release_id, tm, tag, source, self.SEPARATORS)

    def set_performer(self, release_id, album, track, performerList, tm):
        """
        Sets the performer-related tags
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param track:
        :param performerList: see below
        :param tm:
        :return:
        """
        # performerList is in format [(artist_type, [instrument list],[name list],[sort_name list],
        # instrument_sort, type_sort),(.....etc]
        # Sorted by type_sort then sort name then instrument_sort
        write_log(release_id, 'debug', "Extra Artists - set_performer")
        write_log(release_id, 'info', "Performer list is:")
        write_log(release_id, 'info', performerList)
        options = self.options[track]
        # tag strings are a tuple (Picard tag, cea tag, Picard sort tag, cea
        # sort tag)
        tag_strings = const.tag_strings('~cea')
        # insertions lists artist types where names in the main Picard tags may be updated for annotations
        # (not for performer types as Picard will write performer:inst as Performer name (inst) )
        insertions = const.INSERTIONS

        # First remove all existing performer tags
        del_list = []
        for meta in tm:
            if 'performer' in meta:
                del_list.append(meta)
        for del_item in del_list:
            del tm[del_item]
        last_artist = []
        last_inst_list = []
        last_instrument = None
        artist_inst = []
        artist_inst_list = {}
        for performer in performerList:
            artist_type = performer[0]
            if artist_type not in tag_strings:
                return None
            if artist_type in ['instrument', 'vocal', 'performing orchestra']:
                if performer[1]:
                    inst_list = performer[1]
                    attrib_list = []
                    for attrib in ['solo', 'guest', 'additional']:
                        if attrib in inst_list:
                            inst_list.remove(attrib)
                            attrib_list.append(attrib)
                    attribs = " ".join(attrib_list)
                    instrument = ", ".join(inst_list)
                    if not options['cea_no_solo'] and attrib_list:
                        instrument = attribs + " " + instrument
                    if performer[3] == last_artist:
                        if instrument != last_instrument:
                            artist_inst.append(instrument)
                        else:
                            if inst_list == last_inst_list:
                                write_log(
                                    release_id, 'warning', 'Duplicated performer information for %s'
                                                           ' (may be in Release Relationship as well as Track Relationship).'
                                                           ' Duplicates have been ignored.', performer[3])
                                if self.WARNING:
                                    self.append_tag(
                                        release_id,
                                        tm,
                                        '~cea_warning',
                                        '2. Duplicated performer information for "' +
                                        '; '.join(
                                            performer[3]) +
                                        '" (may be in Release Relationship as well as Track Relationship).'
                                        ' Duplicates have been ignored.')
                    else:
                        artist_inst = [instrument]
                        last_artist = performer[3]
                        last_inst_list = inst_list
                        last_instrument = instrument

                    instrument = ", ".join(artist_inst)
                else:
                    instrument = None
                if artist_type == 'performing orchestra':
                    instrument = 'orchestra'
                artist_inst_list[tuple(performer[3])] = instrument
        for performer in performerList:
            artist_type = performer[0]
            if artist_type not in tag_strings:
                return None
            performing_artist = False if artist_type in [
                'arranger', 'instrument arranger', 'orchestrator', 'vocal arranger'] else True
            if True and artist_type in [
                'instrument',
                'vocal',
                    'performing orchestra']:  # There may be an option here (to replace 'True')
                # Currently groups instruments by artist - alternative has been
                # tested if required
                instrument = artist_inst_list[tuple(performer[3])]
            else:
                if performer[1]:
                    inst_list = performer[1]
                    if options['cea_no_solo']:
                        for attrib in ['solo', 'guest', 'additional']:
                            if attrib in inst_list:
                                inst_list.remove(attrib)
                    instrument = " ".join(inst_list)
                else:
                    instrument = None
                if artist_type == 'performing orchestra':
                    instrument = 'orchestra'
            sub_strings = {'instrument': instrument,
                           'vocal': instrument  # ,
                           # 'instrument arranger': instrument,
                           # 'vocal arranger': instrument
                           }
            for typ in ['concertmaster']:
                if options['cea_' + typ] and options['cea_arrangers']:
                    sub_strings[typ] = ':' + options['cea_' + typ]

            if options['cea_arranger']:
                if instrument:
                    arr_inst = options['cea_arranger'] + ' ' + instrument
                else:
                    arr_inst = options['cea_arranger']
            else:
                arr_inst = instrument
            annotations = {'instrument': instrument,
                           'vocal': instrument,
                           'performing orchestra': instrument,
                           'chorus master': options['cea_chorusmaster'],
                           'concertmaster': options['cea_concertmaster'],
                           'arranger': options['cea_arranger'],
                           'instrument arranger': arr_inst,
                           'orchestrator': options['cea_orchestrator'],
                           'vocal arranger': arr_inst}
            tag = tag_strings[artist_type][0]
            cea_tag = tag_strings[artist_type][1]
            sort_tag = tag_strings[artist_type][2]
            cea_sort_tag = tag_strings[artist_type][3]
            cea_names_tag = cea_tag[:-1] + '_names'
            cea_instrumented_tag = cea_names_tag + '_instrumented'
            if artist_type in sub_strings:
                if sub_strings[artist_type]:
                    tag += sub_strings[artist_type]
                else:
                    write_log(
                            release_id,
                            'warning',
                            'No instrument/sub-key available for artist_type %s. Performer = %s. Track is %s',
                            artist_type,
                            performer[2],
                            track)

            if tag:
                if '~ce_tag_cleared_' + \
                        tag not in tm or not tm['~ce_tag_cleared_' + tag] == "Y":
                    if tag in tm:
                        write_log(release_id, 'info', 'delete tag %s', tag)
                        del tm[tag]
                tm['~ce_tag_cleared_' + tag] = "Y"
            if sort_tag:
                if '~ce_tag_cleared_' + \
                        sort_tag not in tm or not tm['~ce_tag_cleared_' + sort_tag] == "Y":
                    if sort_tag in tm:
                        del tm[sort_tag]
                tm['~ce_tag_cleared_' + sort_tag] = "Y"

            name_list = performer[2]
            for ind, name in enumerate(name_list):
                performer_type = ''
                sort_name = performer[3][ind]
                no_credit = True
                # change name to as-credited
                if (performing_artist and options['cea_performer_credited'] or
                        not performing_artist and options['cea_composer_credited']):
                    if sort_name in self.artist_credits[album]:
                        no_credit = False
                        name = self.artist_credits[album][sort_name]
                # over-ride with aliases and use standard MB name (not
                # as-credited) if no alias
                if (options['cea_aliases'] or not performing_artist and options['cea_aliases_composer']) and (
                        no_credit or options['cea_alias_overrides']):
                    if sort_name in self.artist_aliases:
                        name = self.artist_aliases[sort_name]
                # fix cyrillic names if not already fixed
                if options['cea_cyrillic']:
                    if not only_roman_chars(name):
                        name = remove_middle(unsort(sort_name))
                        # Only remove middle name where the existing
                        # performer is in non-latin script
                annotated_name = name
                if instrument:
                    instrumented_name = name + ' (' + instrument + ')'
                else:
                    instrumented_name = name
                # add annotations and write performer tags
                if artist_type in annotations:
                    if annotations[artist_type]:
                        annotated_name += ' (' + annotations[artist_type] + ')'
                    else:
                        write_log(
                                release_id,
                                'warning',
                                'No annotation (instrument) available for artist_type %s.'
                                ' Performer = %s. Track is %s',
                                artist_type,
                                performer[2],
                                track)
                if artist_type in insertions and options['cea_arrangers']:
                    self.append_tag(release_id, tm, tag, annotated_name)
                else:
                    if options['cea_arrangers'] or artist_type == tag:
                        self.append_tag(release_id, tm, tag, name)

                if options['cea_arrangers'] or artist_type == tag:
                    if sort_tag:
                        self.append_tag(release_id, tm, sort_tag, sort_name)
                        if options['cea_tag_sort'] and '~' in sort_tag:
                            explicit_sort_tag = sort_tag.replace('~', '')
                            self.append_tag(
                                release_id, tm, explicit_sort_tag, sort_name)

                self.append_tag(release_id, tm, cea_tag, annotated_name)
                self.append_tag(release_id, tm, cea_names_tag, name)
                if instrumented_name != name:
                    self.append_tag(
                        release_id,
                        tm,
                        cea_instrumented_tag,
                        instrumented_name)

                if cea_sort_tag:
                    self.append_tag(release_id, tm, cea_sort_tag, sort_name)

                # differentiate soloists etc and write related tags
                if artist_type == 'performing orchestra' or (
                        instrument and instrument in self.ENSEMBLE_TYPES) or self.ensemble_type(name):
                    performer_type = 'ensembles'
                    self.append_tag(
                        release_id, tm, '~cea_ensembles', instrumented_name)
                    self.append_tag(
                        release_id, tm, '~cea_ensemble_names', name)
                    self.append_tag(
                        release_id, tm, '~cea_ensembles_sort', sort_name)
                elif artist_type in ['performer', 'instrument', 'vocal']:
                    performer_type = 'soloists'
                    self.append_tag(
                        release_id, tm, '~cea_soloists', instrumented_name)
                    self.append_tag(release_id, tm, '~cea_soloist_names', name)
                    self.append_tag(
                        release_id, tm, '~cea_soloists_sort', sort_name)
                    if artist_type == "vocal":
                        self.append_tag(
                            release_id, tm, '~cea_vocalists', instrumented_name)
                        self.append_tag(
                            release_id, tm, '~cea_vocalist_names', name)
                        self.append_tag(
                            release_id, tm, '~cea_vocalists_sort', sort_name)
                    elif instrument:
                        self.append_tag(
                            release_id, tm, '~cea_instrumentalists', instrumented_name)
                        self.append_tag(
                            release_id, tm, '~cea_instrumentalist_names', name)
                        self.append_tag(
                            release_id, tm, '~cea_instrumentalists_sort', sort_name)
                    else:
                        self.append_tag(
                            release_id, tm, '~cea_other_soloists', instrumented_name)
                        self.append_tag(
                            release_id, tm, '~cea_other_soloist_names', name)
                        self.append_tag(
                            release_id, tm, '~cea_other_soloists_sort', sort_name)

                # set album artists
                if performer_type or artist_type == 'conductor':
                    cea_album_tag = cea_tag.replace(
                        'cea', 'cea_album').replace(
                        'performers', performer_type)
                    cea_album_sort_tag = cea_sort_tag.replace(
                        'cea', 'cea_album').replace(
                        'performers', performer_type)
                    if stripsir(name) in tm['~albumartists'] or stripsir(
                            sort_name) in tm['~albumartists_sort']:
                        self.append_tag(release_id, tm, cea_album_tag, name)
                        self.append_tag(
                            release_id, tm, cea_album_sort_tag, sort_name)
                    else:
                        if performer_type:
                            self.append_tag(
                                release_id, tm, '~cea_support_performers', instrumented_name)
                            self.append_tag(
                                release_id, tm, '~cea_support_performer_names', name)
                            self.append_tag(
                                release_id, tm, '~cea_support_performers_sort', sort_name)

##############
##############
# WORK PARTS #
##############
##############


class PartLevels():
    # QUEUE-HANDLING
    class WorksQueue(LockableObject):
        """Object for managing the queue of lookups"""

        def __init__(self):
            LockableObject.__init__(self)
            self.queue = {}

        def __contains__(self, name):
            return name in self.queue

        def __iter__(self):
            return self.queue.__iter__()

        def __getitem__(self, name):
            self.lock_for_read()
            value = self.queue[name] if name in self.queue else None
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

        # INITIALISATION

    def __init__(self):
        self.works_cache = {}
        # maintains list of parent of each workid, or None if no parent found,
        # so that XML lookup need only executed if no existing record

        self.partof = collections.defaultdict(dict)
        # the inverse of the above (immediate children of each parent)
        # but note that this is specific to the album as children may vary between albums
        # so format is {album1{parent1: child1, parent2:, child2},
        # album2{....}}

        self.works_queue = self.WorksQueue()
        # lookup queue - holds track/album pairs for each queued workid (may be
        # more than one pair per id, especially for higher-level parts)

        self.parts = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # metadata collection for all parts - structure is {workid: {name: ,
        # parent: , (track,album): {part_levels}}, etc}

        self.top_works = collections.defaultdict(dict)
        # metadata collection for top-level works for (track, album) -
        # structure is {(track, album): {workId: }, etc}

        self.trackback = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # hierarchical iterative work structure - {album: {id: , children:{id:
        # , children{}, id: etc}, id: etc} }

        self.child_listing = collections.defaultdict(list)
        # contains list of workIds which are descendants of a given workId, to
        # prevent recursion when adding new ids

        self.work_listing = collections.defaultdict(list)
        # contains list of workIds for each album

        self.top = collections.defaultdict(list)
        # self.top[album] = list of work Ids which are top-level works in album

        self.options = collections.defaultdict(dict)
        # active Classical Extras options for current track

        self.synonyms = collections.defaultdict(dict)
        # active synonym options for current track

        self.replacements = collections.defaultdict(dict)
        # active synonym options for current track

        self.file_works = collections.defaultdict(list)
        # list of works derived from SongKong-style file tags
        # structure is {(album, track): [{workid: , name: }, {workid: ....}}

        self.album_artists = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # collection of artists to be applied at album level

        self.artist_aliases = {}
        # collection of alias names - format is {sort_name: alias_name, ...}

        self.artist_credits = collections.defaultdict(dict)
        # collection of credited-as names - format is {album: {sort_name: credit_name,
        # ...}, ...}

        self.release_artists_sort = collections.defaultdict(list)
        # collection of release artists - format is {album: [sort_name_1,
        # sort_name_2, ...]}

        self.lyricist_filled = collections.defaultdict(dict)
        # Boolean for each track to indicate if lyricist has been found (don't
        # want to add more from higher levels)

        self.orphan_tracks = collections.defaultdict(list)
        # To keep a list for each album of tracks which do not have works -
        # format is {album: [track1, track2, ...], etc}

        self.tracks = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        # To keep a list of all tracks for the album - format is {album:
        # {track1: {movement-group: movementgroup, movement-number: movementnumber},
        #  track2: {}, ..., etc}, album2: etc}

    ########################################
    # SECTION 1 - Initial track processing #
    ########################################

    def add_work_info(
            self,
            album,
            track_metadata,
            trackXmlNode,
            releaseXmlNode):
        """
        Main Routine - run for each track
        :param album:
        :param track_metadata:
        :param trackXmlNode:
        :param releaseXmlNode:
        :return:
        """
        release_id = track_metadata['musicbrainz_albumid']
        if 'start' not in release_status[release_id]:
            release_status[release_id]['start'] = datetime.now()
        if 'lookups' not in release_status[release_id]:
            release_status[release_id]['lookups'] = 0
        release_status[release_id]['name'] = track_metadata['album']
        release_status[release_id]['works'] = True
        if config.setting['log_debug'] or config.setting['log_info']:
            write_log(
                release_id,
                'debug',
                'STARTING WORKS PROCESSING FOR ALBUM %s, DISC %s, TRACK %s',
                track_metadata['album'],
                track_metadata['discnumber'],
                track_metadata['tracknumber'] +
                ' ' +
                track_metadata['title'])
        # clear the cache if required (if this is not done, then queue count may get out of sync)
        # Jump through hoops to get track object!!
        track = album._new_tracks[-1]
        tm = track.metadata
        if config.setting['log_debug'] or config.setting['log_info']:
            write_log(
                release_id,
                'debug',
                'Cache setting for track %s is %s',
                track,
                config.setting['use_cache'])

        # OPTIONS - OVER-RIDE IF REQUIRED
        if '~ce_options' not in tm:
            if config.setting['log_debug'] or config.setting['log_info']:
                write_log(release_id, 'debug', 'Workparts gets track first...')
            get_options(release_id, album, track)
        options = interpret(tm['~ce_options'])

        if not options:
            if config.setting['log_error']:
                write_log(
                    release_id,
                    'error',
                    'Work Parts. Failure to read saved options for track %s. options = %s',
                    track,
                    tm['~ce_options'])
            options = option_settings(config.setting)
        self.options[track] = options

        # CONSTANTS
        write_log(release_id, 'basic', 'Options: %s' ,options)
        self.ERROR = options["log_error"]
        self.WARNING = options["log_warning"]
        self.SEPARATORS = ['; ']
        self.EQ = "EQ_TO_BE_REVERSED"  # phrase to indicate that a synonym has been used

        self.get_sk_tags(release_id, album, track, tm, options)
        self.synonyms[track] = self.get_text_tuples(
            release_id, track, 'synonyms')  # a list of tuples
        self.replacements[track] = self.get_text_tuples(
            release_id, track, 'replacements')  # a list of tuples

        # Continue?
        if not options["classical_work_parts"]:
            return

        # OPTION-DEPENDENT CONSTANTS:
        # Maximum number of XML- lookup retries if error returned from server
        self.MAX_RETRIES = options["cwp_retries"]
        self.USE_CACHE = options["use_cache"]
        if options["cwp_partial"] and options["cwp_partial_text"] and options["cwp_level0_works"]:
            options["cwp_removewords_p"] = options["cwp_removewords"] + \
                ", " + options["cwp_partial_text"] + ' '
        else:
            options["cwp_removewords_p"] = options["cwp_removewords"]
        # Explanation:
        # If "Partial" is selected then the level 0 work name will have PARTIAL_TEXT appended to it.
        # If a recording is split across several tracks then each sub-part (quasi-movement) will have the same name
        # (with the PARTIAL_TEXT added). If level 0 is used to source work names then the level 1 work name will be
        # changed to be this repeated name and will therefore also include PARTIAL_TEXT.
        # So we need to add PARTIAL_TEXT to the prefixes list to ensure it is excluded from the level 1 work name.
        #
        write_log(
                release_id,
                'debug',
                "PartLevels - LOAD NEW TRACK: :%s",
                track)
        # write_log(release_id, 'info', "trackXmlNode:") # warning - may break Picard

        # first time for this album (reloads each refresh)
        if tm['discnumber'] == '1' and tm['tracknumber'] == '1':
            # get artist aliases - these are cached so can be re-used across
            # releases, but are reloaded with each refresh
            get_aliases(self, release_id, album, options, releaseXmlNode)

        # fix titles which include composer name
        composersort =[]
        if 'compposersort' in tm:
            composersort = str_to_list(['composersort'])
        composerlastnames = []
        for composer in composersort:
            lname = re.compile(r'(.*),')
            match = lname.search(composer)
            if match:
                composerlastnames.append(match.group(1))
            else:
                composerlastnames.append(composer)
        title = track_metadata['title']
        colons = title.count(":")
        if colons > 0:
            title_split = title.split(': ', 1)
            test = title_split[0]
            if test in composerlastnames:
                track_metadata['~cwp_title'] = title_split[1]

        # now process works
        write_log(
                release_id,
                'info',
                'PartLevels - add_work_info - metadata load = %r',
                track_metadata)
        workIds = []
        if 'musicbrainz_workid' in tm:
            workIds = str_to_list(tm['musicbrainz_workid'])
        if workIds and not (options["ce_no_run"] and (
                not tm['~ce_file'] or tm['~ce_file'] == "None")):
            self.build_work_info(release_id, options, trackXmlNode, album, track, track_metadata, workIds)

        else:  # no work relation
            write_log(
                    release_id,
                    'warning',
                    "WARNING - no works for this track: \"%s\"",
                    title)
            self.append_tag(
                release_id,
                track_metadata,
                '~cwp_warning',
                '3. No works for this track')
            if album in self.orphan_tracks:
                if track not in self.orphan_tracks[album]:
                    self.orphan_tracks[album].append(track)
            else:
                self.orphan_tracks[album] = [track]
            # Don't publish metadata yet until all album is processed

        # last track
        write_log(
                release_id,
                'debug',
                'Check for last track. Requests = %s, Tracknumber = %s, Totaltracks = %s,'
                ' Discnumber = %s, Totaldiscs = %s',
                album._requests,
                track_metadata['tracknumber'],
                track_metadata['totaltracks'],
                track_metadata['discnumber'],
                track_metadata['totaldiscs'])
        if album._requests == 0 and track_metadata['tracknumber'] == track_metadata[
                'totaltracks'] and track_metadata['discnumber'] == track_metadata['totaldiscs']:
            self.process_album(release_id, album)
            release_status[release_id]['works-done'] = datetime.now()
            close_log(release_id, 'works')


    def build_work_info(self, release_id, options, trackXmlNode, album, track, track_metadata, workIds):
        """
        Construct the work metadata, taking into account partial recordings and medleys
        :param release_id:
        :param options:
        :param trackXmlNode: JSON returned by the webservice
        :param album:
        :param track:
        :param track_metadata:
        :param workIds: work ids for this track
        :return:
        """
        work_list_info = []
        keyed_workIds = {}
        for i, workId in enumerate(workIds):

            # sort by ordering_key, if any
            match_tree = [
                'recording',
                'relations',
                'target-type:work',
                'work',
                'id:' + workId]
            rels = parse_data(release_id, trackXmlNode, [], *match_tree)
            # for recordings which are ordered within track:-
            match_tree_1 = [
                'ordering-key']
            # for recordings of works which are ordered as part of parent
            # (may be duplicated by top-down check later):-
            match_tree_2 = [
                'relations',
                'target-type:work',
                'type:parts',
                'direction:backward',
                'ordering-key']
            parse_result = parse_data(release_id,
                                      rels,
                                      [],
                                      *match_tree_1) + parse_data(release_id,
                                                                  rels,
                                                                  [],
                                                                  *match_tree_2)
            write_log(
                release_id,
                'info',
                'multi-works - ordering key: %s',
                parse_result)
            if parse_result:
                if isinstance(parse_result[0], int):
                    key = parse_result[0]
                elif isinstance(parse_result[0], str) and parse_result[0].isdigit():
                    key = int(parse_result[0])
                else:
                    key = 100 + i
            else:
                key = 100 + i
            keyed_workIds[key] = workId
        partial = False
        for key in sorted(keyed_workIds):
            workId = keyed_workIds[key]
            work_rels = parse_data(
                release_id,
                trackXmlNode,
                [],
                'recording',
                'relations',
                'target-type:work',
                'work.id:' + workId)
            write_log(release_id, 'info', 'work_rels: %s', work_rels)
            work_attributes = parse_data(
                release_id, work_rels, [], 'attributes')[0]
            write_log(
                release_id,
                'info',
                'work_attributes: %s',
                work_attributes)
            work_titles = parse_data(
                release_id, work_rels, [], 'work', 'title')
            work_list_info_item = {
                'id': workId,
                'attributes': work_attributes,
                'titles': work_titles}
            work_list_info.append(work_list_info_item)
            work = []
            for title in work_titles:
                work.append(title)
            if options['cwp_partial']:
                # treat the recording as work level 0 and the work of which it
                # is a partial recording as work level 1
                if 'partial' in work_attributes:
                    partial = True
                    parentId = workId
                    workId = track_metadata['musicbrainz_recordingid']

                    works = []
                    for w in work:
                        partwork = w
                        works.append(partwork)

                    write_log(
                        release_id,
                        'info',
                        "Id %s is PARTIAL RECORDING OF id: %s, name: %s",
                        workId,
                        parentId,
                        work)
                    work_list_info_item = {
                        'id': workId,
                        'attributes': [],
                        'titles': works,
                        'parent': parentId}
                    work_list_info.append(work_list_info_item)
        write_log(
            release_id,
            'info',
            'work_list_info: %s',
            work_list_info)
        # we now have a list of items, where the id of each is a work id for the track or
        #  (multiple instances of) the recording id (for partial works)
        # we need to turn this into a usable hierarchy - i.e. just one item
        workId_list = []
        work_list = []
        parent_list = []
        attribute_list = []
        workId_list_p = []
        work_list_p = []
        attribute_list_p = []
        for w in work_list_info:
            if 'partial' not in w['attributes'] or not options[
                'cwp_partial']:  # just do the bottom-level 'works' first
                workId_list.append(w['id'])
                work_list += w['titles']
                attribute_list += w['attributes']
                if 'parent' in w:
                    if w['parent'] not in parent_list:  # avoid duplicating parents!
                        parent_list.append(w['parent'])
            else:
                workId_list_p.append(w['id'])
                work_list_p += w['titles']
                attribute_list_p += w['attributes']
        # de-duplicate work names
        # list(set()) won't work as need to retain order
        work_list = list(collections.OrderedDict.fromkeys(work_list))
        work_list_p = list(collections.OrderedDict.fromkeys(work_list_p))

        workId_tuple = tuple(workId_list)
        workId_tuple_p = tuple(workId_list_p)
        if workId_tuple not in self.work_listing[album]:
            self.work_listing[album].append(workId_tuple)
        if workId_tuple not in self.parts or not self.USE_CACHE:
            self.parts[workId_tuple]['name'] = work_list
            if parent_list:
                if workId_tuple in self.works_cache:
                    self.works_cache[workId_tuple] += parent_list
                    self.parts[workId_tuple]['parent'] += parent_list
                else:
                    self.works_cache[workId_tuple] = parent_list
                    self.parts[workId_tuple]['parent'] = parent_list
                self.parts[workId_tuple_p]['name'] = work_list_p
                if workId_tuple_p not in self.work_listing[album]:
                    self.work_listing[album].append(workId_tuple_p)

            if 'medley' in attribute_list_p:
                self.parts[workId_tuple_p]['medley'] = True

            if 'medley' in attribute_list:
                self.parts[workId_tuple]['medley'] = True

            if partial:
                self.parts[workId_tuple]['partial'] = True

        self.trackback[album][workId_tuple]['id'] = workId_list
        if 'meta' in self.trackback[album][workId_tuple]:
            if (track,
                album) not in self.trackback[album][workId_tuple]['meta']:
                self.trackback[album][workId_tuple]['meta'].append(
                    (track, album))
        else:
            self.trackback[album][workId_tuple]['meta'] = [(track, album)]
        write_log(
            release_id,
            'info',
            "Trackback for %s is %s. Partial = %s",
            track,
            self.trackback[album][workId_tuple],
            partial)

        if workId_tuple in self.works_cache and (
                self.USE_CACHE or partial):
            write_log(
                release_id,
                'debug',
                "GETTING WORK METADATA FROM CACHE, for work %s",
                workId_tuple)
            if workId_tuple not in self.work_listing[album]:
                self.work_listing[album].append(workId_tuple)
            not_in_cache = self.check_cache(
                track_metadata, album, track, workId_tuple, [])
        else:
            if partial:
                not_in_cache = [workId_tuple_p]
            else:
                not_in_cache = [workId_tuple]
        for workId_tuple in not_in_cache:
            if not self.USE_CACHE:
                if workId_tuple in self.works_cache:
                    del self.works_cache[workId_tuple]
            self.work_not_in_cache(release_id, album, track, workId_tuple)


    def get_sk_tags(self, release_id, album, track, tm, options):
        """
        Get file tags which are consistent with SongKong's metadata usage
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param track:
        :param tm:
        :param options:
        :return:
        """
        if options["cwp_use_sk"]:
            if '~ce_file' in tm and interpret(tm['~ce_file']):
                music_file = tm['~ce_file']
                orig_metadata = album.tagger.files[music_file].orig_metadata
                if 'musicbrainz_work_composition_id' in orig_metadata and 'musicbrainz_workid' in orig_metadata:
                    if 'musicbrainz_work_composition' in orig_metadata:
                        if 'musicbrainz_work' in orig_metadata:
                            if orig_metadata['musicbrainz_work_composition_id'] == orig_metadata[
                                'musicbrainz_workid'] \
                                    and orig_metadata['musicbrainz_work_composition'] != orig_metadata[
                                        'musicbrainz_work']:
                                # Picard may have overwritten SongKong tag (top
                                # work id) with bottom work id
                                write_log(
                                    release_id,
                                    'warning',
                                    'File tag musicbrainz_workid incorrect? id = %s. Sourcing from MB',
                                    orig_metadata['musicbrainz_workid'])
                                if self.WARNING:
                                    self.append_tag(
                                        release_id,
                                        tm,
                                        '~cwp_warning',
                                        '4. File tag musicbrainz_workid incorrect? id = ' +
                                        orig_metadata['musicbrainz_workid'] +
                                        '. Sourcing from MB')
                                return None
                        write_log(
                                release_id,
                                'info',
                                'Read from file tag: musicbrainz_work_composition_id: %s',
                                orig_metadata['musicbrainz_work_composition_id'])
                        self.file_works[(album, track)].append({
                            'workid': orig_metadata['musicbrainz_work_composition_id'].split('; '),
                            'name': orig_metadata['musicbrainz_work_composition']})
                    else:
                        wid = orig_metadata['musicbrainz_work_composition_id']
                        write_log(
                            release_id,
                            'error',
                            "No matching work name for id tag %s",
                            wid)
                        if self.ERROR:
                            self.append_tag(
                                release_id,
                                tm,
                                '~cwp_error',
                                '2. No matching work name for id tag ' +
                                wid)
                        return None
                    n = 1
                    while 'musicbrainz_work_part_level' + \
                            str(n) + '_id' in orig_metadata:
                        if 'musicbrainz_work_part_level' + \
                                str(n) in orig_metadata:
                            self.file_works[(album, track)].append({
                                'workid': orig_metadata[
                                    'musicbrainz_work_part_level' + str(n) + '_id'].split('; '),
                                'name': orig_metadata['musicbrainz_work_part_level' + str(n)]})
                            n += 1
                        else:
                            wid = orig_metadata['musicbrainz_work_part_level' +
                                                str(n) + '_id']
                            write_log(
                                release_id, 'error', "No matching work name for id tag %s", wid)
                            if self.ERROR:
                                self.append_tag(
                                    release_id,
                                    tm,
                                    '~cwp_error',
                                    '2. No matching work name for id tag ' +
                                    wid)
                            break
                    if orig_metadata['musicbrainz_work_composition_id'] != orig_metadata[
                            'musicbrainz_workid']:
                        if 'musicbrainz_work' in orig_metadata:
                            self.file_works[(album, track)].append({
                                'workid': orig_metadata['musicbrainz_workid'].split('; '),
                                'name': orig_metadata['musicbrainz_work']})
                        else:
                            wid = orig_metadata['musicbrainz_workid']
                            write_log(
                                release_id, 'error', "No matching work name for id tag %s", wid)
                            if self.ERROR:
                                self.append_tag(
                                    release_id,
                                    tm,
                                    '~cwp_error',
                                    '2. No matching work name for id tag ' +
                                    wid)
                            return None
                    file_work_levels = len(self.file_works[(album, track)])
                    write_log(release_id,
                                  'debug',
                                  'Loaded works from file tags for track %s. Works: %s: ',
                                  track,
                                  self.file_works[(album,
                                                   track)])
                    for i, work in enumerate(self.file_works[(album, track)]):
                        workId = tuple(work['workid'])
                        if workId not in self.works_cache:  # Use cache in preference to file tags
                            if workId not in self.work_listing[album]:
                                self.work_listing[album].append(workId)
                            self.parts[workId]['name'] = [work['name']]
                            parentId = None
                            parent = ''
                            if i < file_work_levels - 1:
                                parentId = self.file_works[(
                                    album, track)][i + 1]['workid']
                                parent = self.file_works[(
                                    album, track)][i + 1]['name']

                            if parentId:
                                self.works_cache[workId] = parentId
                                self.parts[workId]['parent'] = parentId
                                self.parts[tuple(parentId)]['name'] = [parent]
                            else:
                                # so we remember we looked it up and found none
                                self.parts[workId]['no_parent'] = True
                                self.top_works[(track, album)
                                               ]['workId'] = workId
                                if workId not in self.top[album]:
                                    self.top[album].append(workId)

    def check_cache(self, tm, album, track, workId_tuple, not_in_cache):
        """
        Recursive loop to get cached works
        :param tm:
        :param album:
        :param track:
        :param workId_tuple:
        :param not_in_cache:
        :return:
        """
        parentId_tuple = tuple(self.works_cache[workId_tuple])
        if parentId_tuple not in self.work_listing[album]:
            self.work_listing[album].append(parentId_tuple)

        if parentId_tuple in self.works_cache:
            self.check_cache(tm, album, track, parentId_tuple, not_in_cache)
        else:
            not_in_cache.append(parentId_tuple)
        return not_in_cache

    def work_not_in_cache(self, release_id, album, track, workId_tuple):
        """
        Determine actions if work not in cache (is it the top or do we need to look up?)
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param track:
        :param workId_tuple:
        :return:
        """

        write_log(
                release_id,
                'debug',
                'Processing work_not_in_cache for workId %s',
                workId_tuple)
        ## NB the first condition below is to prevent the side effect of assigning a dictionary entry in self.parts for workId with no details
        if workId_tuple in self.parts and 'no_parent' in self.parts[workId_tuple] and (
                self.USE_CACHE or self.options[track]["cwp_use_sk"]) and self.parts[workId_tuple]['no_parent']:
            write_log(release_id, 'info', '%s is top work', workId_tuple)
            self.top_works[(track, album)]['workId'] = workId_tuple
            if album in self.top:
                if workId_tuple not in self.top[album]:
                    self.top[album].append(workId_tuple)
            else:
                self.top[album] = [workId_tuple]
        else:
            write_log(
                    release_id,
                    'info',
                    'Calling work_add_track to look up parents for %s',
                    workId_tuple)
            for workId in workId_tuple:
                self.work_add_track(album, track, workId, 0)

        write_log(
                release_id,
                'debug',
                'End of work_not_in_cache for workId %s',
                workId_tuple)

    def work_add_track(self, album, track, workId, tries, user_data=True):
        """
        Add the work to the lookup queue
        :param user_data:
        :param album:
        :param track:
        :param workId:
        :param tries: number of lookup attempts
        :return:
        """
        release_id = track.metadata['musicbrainz_albumid']
        write_log(
                release_id,
                'debug',
                "ADDING WORK TO LOOKUP QUEUE for work %s",
                workId)
        self.album_add_request(release_id, album)
        # to change the _requests variable to indicate that there are pending
        # requests for this item and delay Picard from finalizing the album
        write_log(
                release_id,
                'debug',
                "Added lookup request for id %s. Requests = %s",
                workId,
                album._requests)
        if self.works_queue.append(
                workId,
                (track,
                 album)):  # All work combos are queued, but only new workIds are passed to XML lookup
            host = config.setting["server_host"]
            port = config.setting["server_port"]
            path = "/ws/2/%s/%s" % ('work', workId)
            if config.setting['cwp_aliases'] and config.setting['cwp_aliases_tag_text']:
                if config.setting['cwp_aliases_tags_user'] and user_data:
                    login = True
                    tag_type = '+tags +user-tags'
                else:
                    login = False
                    tag_type = '+tags'
            else:
                login = False
                tag_type = ''
            queryargs = {
                "inc": "work-rels+artist-rels+label-rels+place-rels+aliases" +
                tag_type}
            write_log(
                    release_id,
                    'debug',
                    "Initiating XML lookup for %s......",
                    workId)
            if release_id in release_status and 'lookups' in release_status[release_id]:
                release_status[release_id]['lookups'] += 1
            return album.tagger.webservice.get(
                host,
                port,
                path,
                partial(
                    self.work_process,
                    workId,
                    tries),
                # parse_response_type="xml",
                priority=True,
                important=False,
                mblogin=login,
                queryargs=queryargs)
        else:
            write_log(
                    release_id,
                    'debug',
                    "Work is already in queue: %s",
                    workId)

    ##########################################################################
    # SECTION 2 - Works processing                                                                     #
    # NB These functions may operate asynchronously over multiple albums (as well as multiple tracks)  #
    ##########################################################################

    def work_process(self, workId, tries, response, reply, error):
        """
        Top routine to process the XML/JSON node response from the lookup
        NB This function may operate over multiple albums (as well as multiple tracks)
        :param workId:
        :param tries:
        :param response:
        :param reply:
        :param error:
        :return:
        """

        if error:
            tuples = self.works_queue.remove(workId)
            for track, album in tuples:
                release_id = track.metadata['musicbrainz_albumid']
                write_log(
                        release_id,
                        'warning',
                        "%r: Network error retrieving work record. Error code %r",
                        workId,
                        error)
                write_log(
                        release_id,
                        'debug',
                        "Removed request after network error. Requests = %s",
                        album._requests)
                if tries < self.MAX_RETRIES:
                    user_data = True
                    write_log(release_id, 'debug', "REQUEUEING...")
                    if str(error) == '204':  # Authentication error
                        write_log(
                                release_id, 'debug', "... without user authentication")
                        user_data = False
                        self.append_tag(
                            release_id,
                            track.metadata,
                            '~cwp_error',
                            '3. Authentication failure - data retrieval omits user-specific requests')
                    self.work_add_track(
                        album, track, workId, tries + 1, user_data)
                else:
                    write_log(
                        release_id,
                        'error',
                        "EXHAUSTED MAX RE-TRIES for XML lookup for track %s",
                        track)
                    if self.ERROR:
                        self.append_tag(
                            release_id,
                            track.metadata,
                            '~cwp_error',
                            "4. ERROR: MISSING METADATA due to network errors. Re-try or fix manually.")
                self.album_remove_request(release_id, album)
            return

        tuples = self.works_queue.remove(workId)
        if tuples:
            new_queue = []
            prev_album = None
            album = tuples[0][1] # just added to prevent technical "reference before assignment" error
            release_id = 'No_release_id'
            for (track, album) in tuples:
                release_id = track.metadata['musicbrainz_albumid']
                # Note that this need to be set here as the work may cover
                # multiple albums
                if album != prev_album:
                    write_log(release_id, 'debug',
                                  "Work_process. FOUND WORK: %s for album %s",
                                  workId, album)
                    write_log(
                        release_id,
                        'debug',
                        "Requests for album %s = %s",
                        album,
                        album._requests)
                prev_album = album
                write_log(release_id, 'info', "RESPONSE = %s", response)
                # find the id_tuple(s) key with workId in it
                wid_list = []
                for w in self.work_listing[album]:
                    if workId in w and w not in wid_list:
                        wid_list.append(w)
                write_log(
                        release_id,
                        'info',
                        'wid_list for %s is %s',
                        workId,
                        wid_list)
                for wid in wid_list:  # wid is a tuple
                    write_log(
                            release_id,
                            'info',
                            'processing workId tuple: %r',
                            wid)
                    metaList = self.work_process_metadata(
                        release_id, workId, wid, track, response)
                    parentList = metaList[0]
                    # returns [[parent id], [parent name], attribute_list] or None if no parent
                    # found
                    arrangers = metaList[1]
                    # not just arrangers - also composers, lyricists etc.
                    if wid in self.parts:

                        if arrangers:
                            if 'arrangers' in self.parts[wid]:
                                self.parts[wid]['arrangers'] += arrangers
                            else:
                                self.parts[wid]['arrangers'] = arrangers

                        if parentList:
                            # first fix the sort order of multi-works at the prev level
                            # so that recordings of multiple movements of the same parent work will have the
                            # movements listed in the correct order (i.e.
                            # ordering-key, if available)
                            if len(wid) > 1:
                                for idx in wid:
                                    if idx == workId:
                                        match_tree = [
                                            'relations',
                                            'target-type:work',
                                            'direction:backward',
                                            'ordering-key']
                                        parse_result = parse_data(
                                            release_id, response, [], *match_tree)
                                        write_log(
                                                release_id,
                                                'info',
                                                'multi-works - ordering key for id %s is %s',
                                                idx,
                                                parse_result)
                                        if parse_result:
                                            if isinstance(
                                                    parse_result[0], str) and parse_result[0].isdigit():
                                                key = int(parse_result[0])
                                            elif isinstance(parse_result[0], int):
                                                key = parse_result[0]
                                            else:
                                                key = 9999
                                            self.parts[wid]['order'][idx] = key

                            parentIds = parentList[0]
                            parents = parentList[1]
                            parent_attributes = parentList[2]
                            write_log(
                                    release_id,
                                    'info',
                                    'Parents - ids: %s, names: %s',
                                    parentIds,
                                    parents)
                            # remove any parents that are descendants of wid as
                            # they will result in circular references
                            del_list = []
                            for i, parentId in enumerate(parentIds):
                                for work_item in wid:
                                    if work_item in self.child_listing and parentId in self.child_listing[
                                            work_item]:
                                        del_list.append(i)
                            for i in list(set(del_list)):
                                removed_id = parentIds.pop(i)
                                removed_name = parents.pop(i)
                                write_log(
                                        release_id, 'error', "Found parent which is descendant of child - "
                                        "not using, to prevent circular references. id = %s,"
                                        " name = %s", removed_id, removed_name)
                                tm = track.metadata
                                self.append_tag(
                                    release_id,
                                    tm,
                                    '~cwp_error',
                                    '5. Found parent which which is descendant of child - not using '
                                    'to prevent circular references. id = ' +
                                    removed_id +
                                    ', name = ' +
                                    removed_name)
                            is_collection = False
                            for attribute in parent_attributes:
                                if attribute['collection']:
                                    is_collection = True
                                    break
                            # de-dup parent ids before we start
                            parentIds = list(
                                collections.OrderedDict.fromkeys(parentIds))

                            # add descendants to checklist to prevent recursion
                            for p in parentIds:
                                for w in wid:
                                    self.child_listing[p].append(w)
                                    if w in self.child_listing:
                                        self.child_listing[p] += self.child_listing[w]

                            if parentIds:
                                if wid in self.works_cache:
                                    # Make sure we haven't done this
                                    # relationship before, perhaps for another
                                    # album

                                    if not (set(
                                            self.works_cache[wid]) >= set(parentIds)):
                                        prev_ids = tuple(self.works_cache[wid])
                                        prev_name = self.parts[prev_ids]['name']
                                        self.works_cache[wid] = add_list_uniquely(
                                            self.works_cache[wid], parentIds)
                                        self.parts[wid]['parent'] = add_list_uniquely(
                                            self.parts[wid]['parent'], parentIds)
                                        index = self.work_listing[album].index(
                                            prev_ids)
                                        new_id_list = add_list_uniquely(
                                            list(prev_ids), parentIds)
                                        new_ids = tuple(new_id_list)
                                        self.work_listing[album][index] = new_ids
                                        self.parts[new_ids] = self.parts[prev_ids]
                                        #del self.parts[prev_ids]  # Removed from here to deal with multi-parent parts. De-dup now takes place in process_albums.
                                        self.parts[new_ids]['name'] = add_list_uniquely(
                                            prev_name, parents)
                                        parentIds = new_id_list
                                        write_log(
                                            release_id,
                                            'debug',
                                            "In work_process. Changed wid in self.part: prev_ids = %s, new_ids = %s, prev_name = %s, new name = %s",
                                            prev_ids,
                                            new_ids,
                                            prev_name,
                                            self.parts[new_ids]['name'])


                                else:
                                    self.works_cache[wid] = parentIds
                                    self.parts[wid]['parent'] = parentIds
                                    self.parts[tuple(parentIds)
                                               ]['name'] = parents
                                    self.work_listing[album].append(
                                        tuple(parentIds))
                                # de-duplicate the parent names
                                # self.parts[tuple(parentIds)]['name'] = list(
                                #     collections.OrderedDict.fromkeys(self.parts[tuple(parentIds)]['name']))
                                # list(set()) won't work as need to retain order
                                self.parts[tuple(parentIds)]['is_collection'] = is_collection
                                write_log(
                                    release_id,
                                    'debug',
                                    "In work_process. self.parts[%s]['is_collection']: %s",
                                    tuple(parentIds),
                                    self.parts[tuple(parentIds)]['is_collection'])
                                # de-duplicate the parent ids also, otherwise they will be treated as a separate parent
                                # in the trackback structure
                                self.parts[wid]['parent'] = list(
                                    collections.OrderedDict.fromkeys(
                                        self.parts[wid]['parent']))
                                self.works_cache[wid] = list(
                                    collections.OrderedDict.fromkeys(
                                        self.works_cache[wid]))
                                write_log(
                                        release_id,
                                        'info',
                                        'Added parent ids to work_listing: %s, [Requests = %s]',
                                        parentIds,
                                        album._requests)
                                write_log(
                                        release_id,
                                        'info',
                                        'work_listing after adding parents: %s',
                                        self.work_listing[album])
                                # the higher-level work might already be in
                                # cache from another album
                                if tuple(
                                        parentIds) in self.works_cache and self.USE_CACHE:
                                    not_in_cache = self.check_cache(
                                        track.metadata, album, track, tuple(parentIds), [])
                                    for workId_tuple in not_in_cache:
                                        new_queue.append(
                                            (release_id, album, track, workId_tuple))

                                else:
                                    if not self.USE_CACHE:
                                        if tuple(
                                                parentIds) in self.works_cache:
                                            del self.works_cache[tuple(
                                                parentIds)]
                                    for parentId in parentIds:
                                        new_queue.append(
                                            (release_id, album, track, (parentId,)))

                            else:
                                # so we remember we looked it up and found none
                                self.parts[wid]['no_parent'] = True
                                self.top_works[(track, album)]['workId'] = wid
                                if wid not in self.top[album]:
                                    self.top[album].append(wid)
                                write_log(
                                        release_id, 'info', "TOP[album]: %s", self.top[album])
                        else:
                            # so we remember we looked it up and found none
                            self.parts[wid]['no_parent'] = True
                            self.top_works[(track, album)]['workId'] = wid
                            self.top[album].append(wid)

                write_log(
                        release_id,
                        'debug',
                        "End of tuple processing for workid %s in album %s, track %s,"
                        " requests remaining  = %s, new queue is %r",
                        workId,
                        album,
                        track,
                        album._requests,
                        new_queue)
                self.album_remove_request(release_id, album)
                for queued_item in new_queue:
                    write_log(
                            release_id,
                            'info',
                            'Have a new queue: queued_item = %r',
                            queued_item)
            write_log(
                    release_id,
                    'debug',
                    'Penultimate end of work_process for %s (subject to parent lookups in "new_queue")',
                    workId)
            for queued_item in new_queue:
                self.work_not_in_cache(
                    queued_item[0],
                    queued_item[1],
                    queued_item[2],
                    queued_item[3])
            write_log(release_id, 'debug',
                          'Ultimate end of work_process for %s', workId)

            if album._requests == 0:
                self.process_album(release_id, album)
                album._finalize_loading(None)
                release_status[release_id]['works-done'] = datetime.now()
                close_log(release_id, 'works')

    def work_process_metadata(self, release_id, workId, wid, track, response):
        """
        Process XML node
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        NB release_id may be from a different album than the original, if works lookups are identical
        :param workId:
        :param wid: The work id tuple of which workId is a member
        :param track:
        :param response:
        :return:
        """
        write_log(release_id, 'debug', "In work_process_metadata")
        all_tags = parse_data(release_id, response, [], 'tags', 'name')
        self.parts[wid]['folks_genres'] = all_tags
        self.parts[wid]['worktype_genres'] = parse_data(
            release_id, response, [], 'type')
        key = parse_data(
            release_id,
            response,
            [],
            'attributes',
            'type:Key',
            'value')
        self.parts[wid]['key'] = key
        composed_begin_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:artist',
                'type:composer',
                'begin'))
        composed_end_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:artist',
                'type:composer',
                'end'))
        if composed_begin_dates == composed_end_dates:
            composed_dates = composed_begin_dates
        else:
            composed_dates = list(
                zip(composed_begin_dates, composed_end_dates))
            composed_dates = [y + DATE_SEP + z if y != z else y for y, z in composed_dates]
        self.parts[wid]['composed_dates'] = composed_dates
        published_begin_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:label',
                'type:publishing',
                'begin'))
        published_end_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:label',
                'type:publishing',
                'end'))
        if published_begin_dates == published_end_dates:
            published_dates = published_begin_dates
        else:
            published_dates = list(
                zip(published_begin_dates, published_end_dates))
            published_dates = [x + DATE_SEP + y for x, y in published_dates]
        self.parts[wid]['published_dates'] = published_dates

        premiered_begin_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:place',
                'type:premiere',
                'begin'))
        premiered_end_dates = year(
            parse_data(
                release_id,
                response,
                [],
                'relations',
                'target-type:place',
                'type:premiere',
                'end'))
        if premiered_begin_dates == premiered_end_dates:
            premiered_dates = premiered_begin_dates
        else:
            premiered_dates = list(
                zip(premiered_begin_dates, premiered_end_dates))
            premiered_dates = [x + DATE_SEP + y for x, y in premiered_dates]
        self.parts[wid]['premiered_dates'] = premiered_dates

        if 'artist_locale' in config.setting:
            locale = config.setting["artist_locale"]
            # NB this is the Picard code in /util
            lang = locale.split("_")[0]
            alias = parse_data(release_id, response, [], 'aliases',
                               'locale:' + lang, 'primary:True', 'name')
            user_tags = parse_data(
                release_id, response, [], 'user-tags', 'name')
            if config.setting['cwp_aliases_tags_user']:
                tags = user_tags
            else:
                tags = all_tags
            if alias:
                self.parts[wid]['alias'] = self.parts[wid]['name'][:]
                self.parts[wid]['tags'] = tags
                for ind, w in enumerate(wid):
                    if w == workId:
                        # alias should be a one item list but just in case it isn't...
                        if len(self.parts[wid]['alias']) > ind:
                            # The condition here is just to trap errors caused by database inconsistencies
                            # (e.g. a part is shown as a recording of two works, one of which is an arrangement
                            # of the other - this can create a two-item wid with a one-item self.parts[wid]['name']
                            self.parts[wid]['alias'][ind] = '; '.join(
                                alias)
        relation_list = parse_data(release_id, response, [], 'relations')
        return self.work_process_relations(
            release_id, track, workId, wid, relation_list)

    def work_process_relations(
            self,
            release_id,
            track,
            workId,
            wid,
            relations):
        """
        Find the parents etc.
        NB track is just the last album/track for this work - used as being
        representative for options identification. If this is inconsistent (e.g. different collections
        option for albums with the same works) then the latest added track will over-ride others' settings).
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param track:
        :param workId:
        :param wid:
        :param relations:
        :return:
        """
        write_log(
                release_id,
                'debug',
                "In work_process_relations. Relations--> %s",
                relations)
        if track:
            options = self.options[track]
        else:
            options = config.setting
        new_workIds = []
        new_works = []
        attributes_list = []
        relation_attributes = parse_data(
            release_id,
            relations,
            [],
            'target-type:work',
            'type:parts',
            'direction:backward',
            'attributes')
        new_work_list = []
        write_log(
            release_id,
            'debug',
            "relation_attributes--> %s",
            relation_attributes)
        for relation_attribute in relation_attributes:
            if (
                    'part of collection' not in relation_attribute) or options['cwp_collections']:
                new_work_list += parse_data(release_id,
                                            relations,
                                            [],
                                            'target-type:work',
                                            'type:parts',
                                            'direction:backward',
                                            'work')
            attributes_dict = {'collection' : ('part of collection' in relation_attribute),
                               'movements' : ('movement' in relation_attribute),
                               'acts' : ('act' in relation_attribute),
                               'numbers' : ('number' in relation_attribute)}
            attributes_list += [attributes_dict]
            if (
                    'part of collection' in relation_attribute) and not options['cwp_collections']:
                write_log(
                    release_id,
                    'info',
                    'Not getting parent work because relationship is "part of collection" and option not selected')
        if new_work_list:
            write_log(
                    release_id,
                    'info',
                    'new_work_list: %s',
                    new_work_list)
            new_workIds = parse_data(release_id, new_work_list, [], 'id')
            new_works = parse_data(release_id, new_work_list, [], 'title')
        else:
            arrangement_of = parse_data(
                release_id,
                relations,
                [],
                'target-type:work',
                'type:arrangement',
                'direction:backward',
                'work')
            if arrangement_of and options['cwp_arrangements']:
                new_workIds = parse_data(release_id, arrangement_of, [], 'id')
                new_works = parse_data(release_id, arrangement_of, [], 'title')
                self.parts[wid]['arrangement'] = True
            else:
                medley_of = parse_data(
                    release_id,
                    relations,
                    [],
                    'target-type:work',
                    'type:medley',
                    'work')
                direction = parse_data(
                    release_id,
                    relations,
                    [],
                    'target-type:work',
                    'type:medley',
                    'direction')
                if 'backward' not in direction:
                    write_log(
                            release_id, 'info', 'Medley_of: %s', medley_of)
                    if medley_of and options['cwp_medley']:
                        medley_list = []
                        medley_id_list = []
                        for medley_item in medley_of:
                            medley_list = medley_list + \
                                parse_data(release_id, medley_item, [], 'title')
                            medley_id_list = medley_id_list + \
                                parse_data(release_id, medley_item, [], 'id')
                            # (parse_data is a list...)
                            new_workIds = medley_id_list
                            new_works = medley_list
                            write_log(
                                    release_id, 'info', 'Medley_list: %s', medley_list)
                        self.parts[wid]['medley_list'] = medley_list

        write_log(
                release_id,
                'info',
                'New works: ids: %s, names: %s, attributes: %s',
                new_workIds,
                new_works,
                attributes_list)

        artists = get_artists(
            options,
            release_id,
            {},
            relations,
            'work')['artists']
        # artist_types = ['arranger', 'instrument arranger', 'orchestrator', 'composer', 'writer', 'lyricist',
        #                 'librettist', 'revised by', 'translator', 'reconstructed by', 'vocal arranger']

        write_log(release_id, 'info', "ARTISTS %s", artists)

        workItems = (new_workIds, new_works, attributes_list)
        itemsFound = [workItems, artists]
        return itemsFound

    @staticmethod
    def album_add_request(release_id, album):
        """
        To keep track as to whether all lookups have been processed
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :return:
        """
        album._requests += 1
        write_log(
                release_id,
                'debug',
                "Added album request - requests: %s",
                album._requests)

    @staticmethod
    def album_remove_request(release_id, album):
        """
        To keep track as to whether all lookups have been processed
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :return:
        """
        album._requests -= 1
        write_log(
                release_id,
                'debug',
                "Removed album request - requests: %s",
                album._requests)

    ##################################################
    # SECTION 3 - Organise tracks and works in album #
    ##################################################

    def process_album(self, release_id, album):
        """
        Top routine to run end-of-album processes
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :return:
        """
        write_log(release_id, 'debug', "PROCESS ALBUM %s", album)
        release_status[release_id]['done-lookups'] = datetime.now()
        # De-duplicate names in self.parts, maintaining order (in case part names have been arrived at via multiple paths)
        for part_item in self.parts:
            if 'name' in self.parts[part_item]:
                self.parts[part_item]['name'] = list(collections.OrderedDict.fromkeys(str_to_list(self.parts[part_item]['name'])))
        # populate the inverse hierarchy
        write_log(release_id, 'info', "Cache: %s", self.works_cache)
        write_log(release_id, 'info', "Work listing %s", self.work_listing)
        alias_tag_list = config.setting['cwp_aliases_tag_text'].split(',')
        for i, tag_item in enumerate(alias_tag_list):
            alias_tag_list[i] = tag_item.strip()
        for workId in self.work_listing[album]:
            if workId in self.parts:
                write_log(
                    release_id,
                    'info',
                    'Processing workid: %s',
                    workId)
                write_log(
                    release_id,
                    'info',
                    'self.work_listing[album]: %s',
                    self.work_listing[album])
                if len(workId) > 1:
                    # fix the order of names using ordering keys gathered in
                    # work_process
                    if 'order' in self.parts[workId]:
                        seq = []
                        for idx in workId:
                            if idx in self.parts[workId]['order']:
                                seq.append(self.parts[workId]['order'][idx])
                            else:
                                # for the possibility of workids not part of
                                # the same parent and not all ordered
                                seq.append(999)
                        zipped_names = zip(self.parts[workId]['name'], seq)
                        sorted_tups = sorted(zipped_names, key=lambda x: x[1])
                        self.parts[workId]['name'] = [x[0]
                                                      for x in sorted_tups]
                # use aliases where appropriate
                # name is a list - need a string to test for Latin chars
                name_string = '; '.join(self.parts[workId]['name'])
                if config.setting['cwp_aliases']:
                    if config.setting['cwp_aliases_all'] or (
                        config.setting['cwp_aliases_greek'] and not only_roman_chars(name_string)) or (
                        'tags' in self.parts[workId] and any(
                            x in self.parts[workId]['tags'] for x in alias_tag_list)):
                        if 'alias' in self.parts[workId] and self.parts[workId]['alias']:
                            self.parts[workId]['name'] = self.parts[workId]['alias'][:]
                topId = None
                write_log(
                        release_id,
                        'info',
                        'Works_cache: %s',
                        self.works_cache)
                if workId in self.works_cache:
                    parentIds = tuple(self.works_cache[workId])
                    # for parentId in parentIds:
                    write_log(
                            release_id,
                            'debug',
                            "Create inverses: %s, %s",
                            workId,
                            parentIds)
                    if parentIds in self.partof[album]:
                        if workId not in self.partof[album][parentIds]:
                            self.partof[album][parentIds].append(workId)
                    else:
                        self.partof[album][parentIds] = [workId]
                    write_log(release_id, 'info', "Partof: %s",
                                  self.partof[album][parentIds])
                    if 'no_parent' in self.parts[parentIds]:
                        # to handle case if album includes works already in
                        # cache from a different album
                        if self.parts[parentIds]['no_parent']:
                            topId = parentIds
                else:
                    topId = workId
                if topId:
                    if album in self.top:
                        if topId not in self.top[album]:
                            self.top[album].append(topId)
                    else:
                        self.top[album] = [topId]
        # work out the full hierarchy and part levels
        height = 0
        write_log(
                release_id,
                'info',
                "TOP: %s, \nALBUM: %s, \nTOP[ALBUM]: %s",
                self.top,
                album,
                self.top[album])
        if len(self.top[album]) > 1:
            single_work_album = 0
        else:
            single_work_album = 1
        for topId in self.top[album]:
            self.create_trackback(release_id, album, topId)
            write_log(
                    release_id,
                    'info',
                    "Top id = %s, Name = %s",
                    topId,
                    self.parts[topId]['name'])
            write_log(
                    release_id,
                    'info',
                    "Trackback before levels: %s",
                    self.trackback[album][topId])
            work_part_levels = self.level_calc(
                release_id, self.trackback[album][topId], height)
            write_log(
                    release_id,
                    'info',
                    "Trackback after levels: %s",
                    self.trackback[album][topId])
            # determine the level which will be the principal 'work' level
            if work_part_levels >= 3:
                ref_level = work_part_levels - single_work_album
            else:
                ref_level = work_part_levels
            # extended metadata scheme won't display more than 3 work levels
            # ref_level = min(3, ref_level)
            ref_height = work_part_levels - ref_level
            top_info = {
                'levels': work_part_levels,
                'id': topId,
                'name': self.parts[topId]['name'],
                'single': single_work_album}
            # set the metadata in sequence defined by the work structure
            answer = self.process_trackback(
                release_id,
                album,
                self.trackback[album][topId],
                ref_height,
                top_info)
            ##
            #     trackback is a tree in the form {album: {id: , children:{id: , children{},
            #                                                             id: etc},
            #                                             id: etc} }
            #     process_trackback uses the trackback tree to derive title and level_0 based hierarchies
            #     from the structure. It also returns a tuple (id, tracks), where tracks has the structure
            #     {'track': [(track, height), (track, height), ...tuples...]
            #     'work': [[worknames], [worknames], ...lists...]
            #     'tracknumber': [num, num, ...floats of form n.nnn = disc.track...]
            #     'title':  [title, title, ...strings...]}
            #     each list is the same length - i.e. the number of tracks for the top work
            #     there can be more than one workname for a track
            #     height is the number of part levels for the related track
            ##
            if answer:
                tracks = sorted(zip(answer[1]['track'], answer[1]['tracknumber']), key=lambda x: x[1])
                # need them in tracknumber sequence for the movement numbers to be correct
                write_log(release_id, 'info', "TRACKS: %s", tracks)
                # work_part_levels = self.trackback[album][topId]['depth']
                movement_count = 0
                prev_movementgroup = None
                for track, _ in tracks:
                    movement_count += 1
                    track_meta = track[0]
                    tm = track_meta.metadata
                    if '~cwp_workid_0' in tm:
                        workIds = tuple(str_to_list(tm['~cwp_workid_0']))
                        if workIds:
                            count = 0
                            self.process_work_artists(
                                release_id, album, track_meta, workIds, tm, count)
                    title_work_levels = 0
                    if '~cwp_title_work_levels' in tm:
                        title_work_levels = int(tm['~cwp_title_work_levels'])
                    movementgroup = self.extend_metadata(
                        release_id,
                        top_info,
                        track_meta,
                        ref_height,
                        title_work_levels)  # revise for new data
                    if track_meta not in self.tracks[album]:
                        self.tracks[album][track_meta] = {}
                    if movementgroup:
                        if movementgroup != prev_movementgroup:
                            movement_count = 1
                        write_log(
                            release_id,
                            'debug',
                            "processing movements for track: %s - movement-group is %s",
                            track, movementgroup)
                        self.tracks[album][track_meta]['movement-group'] = movementgroup
                        self.tracks[album][track_meta]['movement-number'] = movement_count
                        self.parts[tuple(movementgroup)]['movement-total'] = movement_count
                    prev_movementgroup = movementgroup

                write_log(
                        release_id,
                        'debug',
                        "FINISHED TRACK PROCESSING FOR Top work id: %s",
                        topId)
        # Need to redo the loop so that all album-wide tm is updated before
        # publishing
        for track, movement_info in self.tracks[album].items():
            self.publish_metadata(release_id, album, track, movement_info)
        # #
        # The messages below are normally commented out as they get VERY long if there are a lot of albums loaded
        # For extreme debugging, remove the comments and just run one or a few albums
        # Do not forget to comment out again.
        # #
        # write_log(release_id, 'info', 'Self.parts: %s', self.parts)
        # write_log(release_id, 'info', 'Self.trackback: %s', self.trackback)

        # tidy up
        self.trackback[album].clear()
        # Finally process the orphan tracks
        if album in self.orphan_tracks:
            for track in self.orphan_tracks[album]:
                tm = track.metadata
                options = self.options[track]
                if options['cwp_derive_works_from_title']:
                    work, movt, inter_work = self.derive_from_title(release_id, track, tm['title'])
                    tm['~cwp_extended_work'] = tm['~cwp_extended_groupheading'] = tm['~cwp_title_work'] = \
                        tm['~cwp_title_groupheading'] = tm['~cwp_work'] = tm['~cwp_groupheading']= work
                    tm['~cwp_part'] = tm['~cwp_extended_part'] = tm['~cwp_title_part_0'] = movt
                    tm['~cwp_inter_work'] = tm['~cwp_extended_inter_work'] = tm['~cwp_inter_title_work'] = inter_work
                self.publish_metadata(release_id, album, track)
        write_log(release_id, 'debug', "PROCESS ALBUM function complete")

    def create_trackback(self, release_id, album, parentId):
        """
        Create an inverse listing of the work-parent relationships
        :param release_id:
        :param album:
        :param parentId:
        :return: trackback for a given parentId
        """
        write_log(release_id, 'debug', "Create trackback for %s", parentId)
        if parentId in self.partof[album]:  # NB parentId is a tuple
            for child in self.partof[album][parentId]:  # NB child is a tuple
                if child in self.partof[album]:
                    child_trackback = self.create_trackback(
                        release_id, album, child)
                    self.append_trackback(
                        release_id, album, parentId, child_trackback)
                else:
                    self.append_trackback(
                        release_id, album, parentId, self.trackback[album][child])
            return self.trackback[album][parentId]
        else:
            return self.trackback[album][parentId]

    def append_trackback(self, release_id, album, parentId, child):
        """
        Recursive process to populate trackback
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param parentId:
        :param child:
        :return:
        """
        write_log(release_id, 'debug', "In append_trackback...")
        if parentId in self.trackback[album]:  # NB parentId is a tuple
            if 'children' in self.trackback[album][parentId]:
                if child not in self.trackback[album][parentId]['children']:
                    write_log(release_id, 'info', "TRYING TO APPEND...")
                    self.trackback[album][parentId]['children'].append(child)
                    write_log(
                            release_id,
                            'info',
                            "...PARENT %s - ADDED %s as child",
                            self.parts[parentId]['name'],
                            child)
                else:
                    write_log(
                            release_id,
                            'info',
                            "Parent %s already has %s as child",
                            parentId,
                            child)
            else:
                self.trackback[album][parentId]['children'] = [child]
                write_log(
                        release_id,
                        'info',
                        "Existing PARENT %s - ADDED %s as child",
                        self.parts[parentId]['name'],
                        child)
        else:
            self.trackback[album][parentId]['id'] = parentId
            self.trackback[album][parentId]['children'] = [child]
            write_log(
                release_id,
                'info',
                "New PARENT %s - ADDED %s as child",
                self.parts[parentId]['name'],
                child)
            write_log(
                release_id,
                'info',
                "APPENDED TRACKBACK: %s",
                self.trackback[album][parentId])
        return self.trackback[album][parentId]

    def level_calc(self, release_id, trackback, height):
        """
        Recursive process to determine the max level for a work
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param trackback:
        :param height: number of levels above this one
        :return:
        """
        write_log(release_id, 'debug', 'In level_calc process')
        if 'children' not in trackback:
            write_log(release_id, 'info', "Got to bottom")
            trackback['height'] = height
            trackback['depth'] = 0
            return 0
        else:
            trackback['height'] = height
            height += 1
            max_depth = 0
            for child in trackback['children']:
                write_log(release_id, 'info', "CHILD: %s", child)
                depth = self.level_calc(release_id, child, height) + 1
                write_log(release_id, 'info', "DEPTH: %s", depth)
                max_depth = max(depth, max_depth)
            trackback['depth'] = max_depth
            return max_depth

        ###########################################
        # SECTION 4 - Process tracks within album #
        ###########################################

    def process_trackback(
            self,
            release_id,
            album_req,
            trackback,
            ref_height,
            top_info):
        """
        Set work structure metadata & govern other metadata-setting processes
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album_req:
        :param trackback:
        :param ref_height:
        :param top_info:
        :return:
        """
        write_log(
                release_id,
                'debug',
                "IN PROCESS_TRACKBACK. Trackback = %s",
                trackback)
        tracks = collections.defaultdict(dict)
        process_now = False
        if 'meta' in trackback:
            for track, album in trackback['meta']:
                if album_req == album:
                    process_now = True
        if process_now or 'children' not in trackback:
            if 'meta' in trackback and 'id' in trackback and 'depth' in trackback and 'height' in trackback:
                write_log(release_id, 'info', "Processing level 0")
                depth = trackback['depth']
                height = trackback['height']
                workId = tuple(trackback['id'])
                if depth != 0:
                    if 'children' in trackback:
                        child_response = self.process_trackback_children(
                            release_id, album_req, trackback, ref_height, top_info, tracks)
                        tracks = child_response[1]
                    write_log(
                            release_id,
                            'info',
                            'Bottom level for this trackback is higher level elsewhere - adjusting levels')
                    depth = 0
                write_log(release_id, 'info', "WorkId: %s, Work name: %s", workId, self.parts[workId]['name'])
                for track, album in trackback['meta']:
                    if album == album_req:
                        write_log(release_id, 'info', "Track: %s", track)
                        tm = track.metadata
                        write_log(
                                release_id, 'info', "Track metadata = %s", tm)
                        tm['~cwp_workid_' + str(depth)] = workId
                        self.write_tags(release_id, track, tm, workId)
                        self.make_annotations(release_id, track, workId)
                        # strip leading and trailing spaces from work names
                        if isinstance(self.parts[workId]['name'], str):
                            worktemp = self.parts[workId]['name'].strip()
                        else:
                            for index, it in enumerate(
                                    self.parts[workId]['name']):
                                self.parts[workId]['name'][index] = it.strip()
                            worktemp = self.parts[workId]['name']
                        if isinstance(top_info['name'], str):
                            toptemp = top_info['name'].strip()
                        else:
                            for index, it in enumerate(top_info['name']):
                                top_info['name'][index] = it.strip()
                            toptemp = top_info['name']
                        tm['~cwp_work_' + str(depth)] = worktemp
                        tm['~cwp_part_levels'] = str(height)
                        tm['~cwp_work_part_levels'] = str(top_info['levels'])
                        tm['~cwp_workid_top'] = top_info['id']
                        tm['~cwp_work_top'] = toptemp
                        tm['~cwp_single_work_album'] = top_info['single']
                        write_log(
                                release_id, 'info', "Track metadata = %s", tm)
                        if 'track' in tracks:
                            tracks['track'].append((track, height))
                        else:
                            tracks['track'] = [(track, height)]
                        tracks['tracknumber'] = [int(tm['discnumber']) + (int(tm['tracknumber']) / 1000)]
                        # Hopefully no more than 999 tracks per disc!
                        write_log(release_id, 'info', "Tracks: %s", tracks)

                response = (workId, tracks)
                write_log(release_id, 'debug', "LEAVING PROCESS_TRACKBACK")
                write_log(
                        release_id,
                        'info',
                        "depth %s Response = %s",
                        depth,
                        response)
                return response
            else:
                return None
        else:
            response = self.process_trackback_children(
                release_id, album_req, trackback, ref_height, top_info, tracks)
            return response

    def process_trackback_children(
            self,
            release_id,
            album_req,
            trackback,
            ref_height,
            top_info,
            tracks):
        """
        TODO add some better documentation!
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album_req:
        :param trackback:
        :param ref_height:
        :param top_info:
        :param tracks:
        :return:
        """
        if 'id' in trackback and 'depth' in trackback and 'height' in trackback:
            write_log(
                    release_id,
                    'debug',
                    'In process_children_trackback for trackback %s',
                    trackback)
            depth = trackback['depth']
            height = trackback['height']
            parentId = tuple(trackback['id'])
            parent = self.parts[parentId]['name']
            width = 0
            for child in trackback['children']:
                width += 1
                write_log(
                        release_id,
                        'info',
                        "child trackback = %s",
                        child)
                answer = self.process_trackback(
                    release_id, album_req, child, ref_height, top_info)
                if answer:
                    workId = answer[0]
                    child_tracks = answer[1]['track']
                    for track in child_tracks:
                        track_meta = track[0]
                        track_height = track[1]
                        part_level = track_height - height
                        write_log(
                                release_id,
                                'debug',
                                "Calling set metadata %s",
                                (part_level,
                                 workId,
                                 parentId,
                                 parent,
                                 track_meta))
                        self.set_metadata(
                            release_id, part_level, workId, parentId, parent, track_meta)
                        if 'track' in tracks:
                            tracks['track'].append(
                                (track_meta, track_height))
                        else:
                            tracks['track'] = [(track_meta, track_height)]
                        tm = track_meta.metadata
                        # ~cwp_title if composer had to be removed
                        title = tm['~cwp_title'] or tm['title']
                        if 'title' in tracks:
                            tracks['title'].append(title)
                        else:
                            tracks['title'] = [title]
                        # to make sure we get it as a list
                        work = tm.getall('~cwp_work_0')
                        if 'work' in tracks:
                            tracks['work'].append(work)
                        else:
                            tracks['work'] = [work]
                        if 'tracknumber' not in tm:
                            tm['tracknumber'] = 0
                        if 'discnumber' not in tm:
                            tm['discnumber'] = 0
                        if 'tracknumber' in tracks:
                            tracks['tracknumber'].append(
                                int(tm['discnumber']) + (int(tm['tracknumber']) / 1000))
                        else:
                            tracks['tracknumber'] = [
                                int(tm['discnumber']) + (int(tm['tracknumber']) / 1000)]
            if tracks and 'track' in tracks:
                track = tracks['track'][0][0]
                # NB this will only be the first track of tracks, but its
                # options will be used for the structure
                self.derive_from_structure(
                    release_id, top_info, tracks, height, depth, width, 'title')
                if self.options[track]["cwp_level0_works"]:
                    # replace hierarchical works with those from work_0 (for
                    # consistency)
                    self.derive_from_structure(
                        release_id, top_info, tracks, height, depth, width, 'work')

                write_log(
                        release_id,
                        'info',
                        "Trackback result for %s = %s",
                        parentId,
                        tracks)
                response = parentId, tracks
                write_log(
                        release_id,
                        'debug',
                        "LEAVING PROCESS_CHILD_TRACKBACK depth %s Response = %s",
                        depth,
                        response)
                return response
            else:
                return None
        else:
            return None

    def derive_from_structure(
            self,
            release_id,
            top_info,
            tracks,
            height,
            depth,
            width,
            name_type):
        """
        Derive title (or work level-0) components from MB hierarchical work structure
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param top_info:
         {'levels': work_part_levels,'id': topId,'name': self.parts[topId]['name'],'single': single_work_album}
        :param tracks:
         {'track':[(track1, height1), (track2, height2), ...], 'work': [work1, work2,...],
          'title': [title1, title2, ...], 'tracknumber': [tracknumber1, tracknumber2, ...]}
          where height is the number of levels in total in the branch for that track (i.e. height 1 => work_0 & work_1)
        :param height: number of levels above the current one
        :param depth: maximum number of levels
        :param width: number of siblings
        :param name_type: work or title
        :return:
        """
        if 'track' in tracks:
            track = tracks['track'][0][0]
            # NB this will only be the first track of tracks, but its
            # options will be used for the structure
            single_work_track = False  # default
            write_log(
                release_id,
                'debug',
                "Deriving info for %s from structure for tracks %s",
                name_type,
                tracks['track'])
            write_log(
                release_id,
                'info',
                '%ss are %r',
                name_type,
                tracks[name_type])
            if 'tracknumber' in tracks:
                sorted_tracknumbers = sorted(tracks['tracknumber'])
            else:
                sorted_tracknumbers = None
            write_log(
                    release_id,
                    'info',
                    "SORTED TRACKNUMBERS: %s",
                    sorted_tracknumbers)
            common_len = 0
            if name_type in tracks:
                meta_str = "_title" if name_type == 'title' else "_X0"
                # in case of works, could be a list of lists
                name_list = tracks[name_type]
                write_log(
                        release_id,
                        'info',
                        "%s list %s",
                        name_type,
                        name_list)
                if len(name_list) == 1:  # only one track in this work so try and extract using colons
                    single_work_track = True
                    track_height = tracks['track'][0][1]
                    if track_height - height > 0:  # track_height - height == part_level
                        if name_type == 'title':
                            write_log(
                                    release_id,
                                    'debug',
                                    "Single track work. Deriving directly from title text: %s",
                                    track)
                            ti = name_list[0]
                            common_subset = self.derive_from_title(
                                release_id, track, ti)[0]
                        else:
                            common_subset = ""
                    else:
                        common_subset = name_list[0]
                    write_log(
                            release_id,
                            'info',
                            "%s is single-track work. common_subset is set to %s",
                            tracks['track'][0][0],
                            common_subset)
                    if common_subset:
                        common_len = len(common_subset)
                    else:
                        common_len = 0
                else:  # NB if names are lists of lists, we'll assume they all start the same way
                    if isinstance(name_list[0], list):
                        compare = name_list[0][0].split()
                    else:
                        # a list of the words in the first name
                        compare = name_list[0].split()
                    for name_item in name_list:
                        if isinstance(name_item, list):
                            name = name_item[0]
                        else:
                            name = name_item
                        lcs = longest_common_sequence(compare, name.split())
                        compare = lcs['sequence']
                        if not compare:
                            common_len = 0
                            break
                        if lcs['length'] > 0:
                            common_subset = " ".join(compare)
                            write_log(
                                    release_id,
                                    'info',
                                    "Common subset from %ss at level %s, item name %s ..........",
                                    name_type,
                                    tracks['track'][0][1] -
                                    height,
                                    name)
                            write_log(
                                    release_id, 'info', "..........is %s", common_subset)
                            common_len = len(common_subset)

                write_log(
                        release_id,
                        'info',
                        "checked for common sequence - length is %s",
                        common_len)
            for track_index, track_item in enumerate(tracks['track']):
                track_meta = track_item[0]
                tm = track_meta.metadata
                top_level = int(tm['~cwp_part_levels'])
                part_level = track_item[1] - height
                if common_len > 0:
                    self.create_work_levels(release_id, name_type, tracks, track, track_index,
                                            track_meta, tm, meta_str, part_level, depth, width, common_len)

                else:  # (no common substring at this level)
                    if name_type == 'work':
                        write_log(release_id, 'info',
                                  'single track work - indicator = %s. track = %s, part_level = %s, top_level = %s',
                                  single_work_track, track_item, part_level, top_level)
                        if part_level >= top_level:  # so it won't be covered by top-down action
                            for level in range(
                                    0, part_level + 1):  # fill in the missing work names from the canonical list
                                if '~cwp' + meta_str + '_work_' + \
                                        str(level) not in tm:
                                    tm['~cwp' +
                                       meta_str +
                                       '_work_' +
                                       str(level)] = tm['~cwp_work_' +
                                                        str(level)]
                                    if level > 0:
                                        self.level0_warn(release_id, tm, level)
                                if '~cwp' + meta_str + '_part_' + \
                                        str(level) not in tm and '~cwp_part_' + str(level) in tm:
                                    tm['~cwp' +
                                       meta_str +
                                       '_part_' +
                                       str(level)] = tm['~cwp_part_' +
                                                        str(level)]
                                    if level > 0:
                                        self.level0_warn(release_id, tm, level)


    def create_work_levels(self, release_id, name_type, tracks, track, track_index,
                           track_meta, tm, meta_str, part_level, depth, width, common_len):
        """
        For a group of tracks with common metadata in the title/level0 work, create the work structure
        for that metadata, using the structure in the MB database
        :param release_id:
        :param name_type: title or work
        :param tracks: {'track':[(track1, height1), (track2, height2), ...], 'work': [work1, work2,...],
          'title': [title1, title2, ...], 'tracknumber': [tracknumber1, tracknumber2, ...]}
          where height is the number of levels in total in the branch for that track (i.e. height 1 => work_0 & work_1)
        :param track:
        :param track_index: index of track in tracks
        :param track_meta:
        :param tm: track meta (dup?)
        :param meta_str: string created from name_type
        :param part_level: The level of the current item in the works hierarchy
        :param depth: The number of levels below the current item
        :param width: The number of children of the current item
        :param common_len: length of the common text
        :return:
        """
        allow_repeats = True
        write_log(
            release_id,
            'info',
            "Use %s info for track: %s at level %s",
            name_type,
            track_meta,
            part_level)
        name = tracks[name_type][track_index]
        if isinstance(name, list):
            work = name[0][:common_len]
        else:
            work = name[:common_len]
        work = work.rstrip(":,.;- ")
        if self.options[track]["cwp_removewords_p"]:
            removewords = self.options[track]["cwp_removewords_p"].split(
                ',')
        else:
            removewords = []
        write_log(
            release_id,
            'info',
            "Prefixes (in %s) = %s",
            name_type,
            removewords)
        for prefix in removewords:
            prefix2 = str(prefix).lower().rstrip()
            if prefix2[0] != " ":
                prefix2 = " " + prefix2
            write_log(
                release_id, 'info', "checking prefix %s", prefix2)
            if work.lower().endswith(prefix2):
                if len(prefix2) > 0:
                    work = work[:-len(prefix2)]
                    common_len = len(work)
                    work = work.rstrip(":,.;- ")
            if work.lower() == prefix2.strip():
                work = ''
                common_len = 0
        write_log(
            release_id,
            'info',
            "work after prefix strip %s",
            work)
        write_log(release_id, 'info', "Prefixes checked")

        tm['~cwp' + meta_str + '_work_' +
           str(part_level)] = work

        if part_level > 0 and name_type == "work":
            write_log(
                release_id,
                'info',
                'checking if %s is repeated name at part_level = %s',
                work,
                part_level)
            write_log(release_id, 'info', 'lower work name is %s',
                      tm['~cwp' + meta_str + '_work_' + str(part_level - 1)])
        # fill in missing names caused by no common string at lower levels
        # count the missing levels and push the current name
        # down to the lowest missing level
        missing_levels = 0
        fill_level = part_level - 1
        while '~cwp' + meta_str + '_work_' + \
                str(fill_level) not in tm:
            missing_levels += 1
            fill_level -= 1
            if fill_level < 0:
                break
        write_log(
            release_id,
            'info',
            'there is/are %s missing level(s)',
            missing_levels)
        if missing_levels > 0:
            allow_repeats = True
        for lev in range(
                part_level - missing_levels, part_level):

            if lev > 0:  # not filled_lowest and lev > 0:
                tm['~cwp' + meta_str +
                   '_work_' + str(lev)] = work
                tm['~cwp' +
                   meta_str +
                   '_part_' +
                   str(lev - 1)] = self.strip_parent_from_work(track,
                                                               release_id,
                                                               interpret(tm['~cwp' + meta_str + '_work_'
                                                                            + str(lev - 1)]),
                                                               tm['~cwp' + meta_str + '_work_' + str(lev)],
                                                               lev - 1, False)[0]
            else:
                tm['~cwp' + meta_str + '_work_' + str(lev)] = tm['~cwp_work_' + str(lev)]

        if missing_levels > 0:
            write_log(release_id, 'info', 'lower work name is now %r', tm.getall(
                '~cwp' + meta_str + '_work_' + str(part_level - 1)))
        # now fix the repeated work name at this level
        if work == tm['~cwp' + meta_str + '_work_' +
                      str(part_level - 1)] and not allow_repeats:
            tm['~cwp' +
               meta_str +
               '_work_' +
               str(part_level)] = tm['~cwp_work_' +
                                     str(part_level)]
            self.level0_warn(release_id, tm, part_level)
        tm['~cwp' +
           meta_str +
           '_part_' +
           str(part_level -
               1)] = self.strip_parent_from_work(track,
                                                 release_id,
                                                 tm.getall('~cwp' + meta_str + '_work_' + str(part_level - 1)),
                                                 tm['~cwp' + meta_str + '_work_' + str(part_level)],
                                                 part_level - 1, False)[0]
        if part_level == 1:
            if isinstance(name, list):
                movt = [x[common_len:].strip().lstrip(":,.;- ")
                        for x in name]
            else:
                movt = name[common_len:].strip().lstrip(":,.;- ")
            write_log(
                release_id, 'info', "%s - movt = %s", name_type, movt)
            tm['~cwp' + meta_str + '_part_0'] = movt
        write_log(
            release_id,
            'info',
            "%s Work part_level = %s",
            name_type,
            part_level)
        if name_type == 'title':
            if '~cwp_title_work_' + str(part_level - 1) in tm and tm['~cwp_title_work_' + str(
                    part_level)] == tm['~cwp_title_work_' + str(part_level - 1)] and width == 1:
                pass  # don't count higher part-levels which are not distinct from lower ones
                #  when the parent work has only one child
            else:
                tm['~cwp_title_work_levels'] = depth
                tm['~cwp_title_part_levels'] = part_level
        write_log(
            release_id,
            'info',
            "Set new metadata for %s OK",
            name_type)

    def level0_warn(self, release_id, tm, level):
        """
        Issue warnings if inadequate level 0 data
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param tm:
        :param level:
        :return:
        """
        write_log(
            release_id,
            'warning',
            'Unable to use level 0 as work name source in level %s - using hierarchy instead',
            level)
        if self.WARNING:
            self.append_tag(
                release_id,
                tm,
                '~cwp_warning',
                '5. Unable to use level 0 as work name source in level ' +
                str(level) +
                ' - using hierarchy instead')

    def set_metadata(
            self,
            release_id,
            part_level,
            workId,
            parentId,
            parent,
            track):
        """
        Set the names of works and parts
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param part_level:
        :param workId:
        :param parentId:
        :param parent:
        :param track:
        :return:
        """
        write_log(
                release_id,
                'debug',
                "SETTING METADATA FOR TRACK = %r, parent = %s, part_level = %s",
                track,
                parent,
                part_level)
        tm = track.metadata
        if parentId:
            self.write_tags(release_id, track, tm, parentId)
            self.make_annotations(release_id, track, parentId)
            if 'annotations' in self.parts[workId]:
                work_annotations = self.parts[workId]['annotations']
                self.parts[workId]['stripped_annotations'] = work_annotations
            else:
                work_annotations = []
            if 'annotations' in self.parts[parentId]:
                parent_annotations = self.parts[parentId]['annotations']
            else:
                parent_annotations = []
            if parent_annotations:
                work_annotations = [
                    z for z in work_annotations if z not in parent_annotations]
                self.parts[workId]['stripped_annotations'] = work_annotations

            tm['~cwp_workid_' + str(part_level)] = parentId
            tm['~cwp_work_' + str(part_level)] = parent
            # maybe more than one work name
            work = self.parts[workId]['name']
            write_log(release_id, 'info', "Set work name to: %s", work)
            works = []
            # in case there is only one and it isn't in a list
            if isinstance(work, str):
                works.append(work)
            else:
                works = work[:]
            stripped_works = []
            for work in works:
                extend = True
                strip = self.strip_parent_from_work(
                    track, release_id, work, parent, part_level, extend, parentId, workId)

                stripped_works.append(strip[0])
                write_log(
                        release_id,
                        'info',
                        "Parent: %s, Stripped works = %s",
                        parent,
                        stripped_works)
                # now == parent, after removing full_parent logic
                full_parent = strip[1]
                if full_parent != parent:
                    tm['~cwp_work_' +
                       str(part_level)] = full_parent.strip()
                    self.parts[parentId]['name'] = full_parent
                    if 'no_parent' in self.parts[parentId]:
                        if self.parts[parentId]['no_parent']:
                            tm['~cwp_work_top'] = full_parent.strip()
            tm['~cwp_part_' + str(part_level - 1)] = stripped_works
            self.parts[workId]['stripped_name'] = stripped_works
        write_log(release_id, 'debug', "GOT TO END OF SET_METADATA")

    def write_tags(self, release_id, track, tm, workId):
        """
        write genre-related tags from internal variables
        :param track:
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param tm: track metadata
        :param workId: MBID of current work
        :return: None - just writes tags
        """
        options = self.options[track]
        candidate_genres = []
        if options['cwp_genres_use_folks'] and 'folks_genres' in self.parts[workId]:
            candidate_genres += self.parts[workId]['folks_genres']
        if options['cwp_genres_use_worktype'] and 'worktype_genres' in self.parts[workId]:
            candidate_genres += self.parts[workId]['worktype_genres']
            self.append_tag(
                release_id,
                tm,
                '~cwp_worktype_genres',
                self.parts[workId]['worktype_genres'])
        self.append_tag(
            release_id,
            tm,
            '~cwp_candidate_genres',
            candidate_genres)
        self.append_tag(release_id, tm, '~cwp_keys', self.parts[workId]['key'])
        self.append_tag(release_id, tm, '~cwp_composed_dates',
                        self.parts[workId]['composed_dates'])
        self.append_tag(release_id, tm, '~cwp_published_dates',
                        self.parts[workId]['published_dates'])
        self.append_tag(release_id, tm, '~cwp_premiered_dates',
                        self.parts[workId]['premiered_dates'])

    def make_annotations(self, release_id, track, wid):
        """
        create an 'annotations' entry in the 'parts' dict, as dictated by options, from dates and keys
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param track: the current track
        :param wid: the current work MBID
        :return:
        """
        write_log(
                release_id,
                'debug',
                "Starting module %s",
                'make_annotations')
        options = self.options[track]
        if options['cwp_workdate_include']:
            if options['cwp_workdate_source_composed'] and 'composed_dates' in self.parts[wid] and self.parts[wid]['composed_dates']:
                workdates = self.parts[wid]['composed_dates']
            elif options['cwp_workdate_source_published'] and 'published_dates' in self.parts[wid] and self.parts[wid]['published_dates']:
                workdates = self.parts[wid]['published_dates']
            elif options['cwp_workdate_source_premiered'] and 'premiered_dates' in self.parts[wid] and self.parts[wid]['premiered_dates']:
                workdates = self.parts[wid]['premiered_dates']
            else:
                workdates = []
        else:
            workdates = []
        keys = []
        if options['cwp_key_include'] and 'key' in self.parts[wid] and self.parts[wid]['key']:
            keys = self.parts[wid]['key']
        elif options['cwp_key_contingent_include'] and 'key' in self.parts[wid] and self.parts[wid]['key']\
                and 'name' in self.parts[wid]:
            write_log(
                    release_id,
                    'info',
                    'checking for key. keys = %s, names = %s',
                    self.parts[wid]['key'],
                    self.parts[wid]['name'])
            # add all the parent names to the string for checking -
            work_name = list_to_str(self.parts[wid]['name'])
            work_chk = wid
            while work_chk in self.works_cache:
                parent_chk = tuple(self.works_cache[work_chk])
                if parent_chk in self.parts and self.parts[parent_chk] and 'name' in self.parts[parent_chk] and self.parts[parent_chk]['name']:
                    parent_name = list_to_str(self.parts[parent_chk]['name'])
                    p_name_orig = self.parts[parent_chk]['name']
                    p_chk = self.parts[parent_chk]
                    work_name = parent_name + ': ' + work_name
                work_chk = parent_chk
            # now see if the key has been mentioned in the work or its parents
            for key in self.parts[wid]['key']:
                # if not any([key.lower() in x.lower() for x in
                # str_to_list(work_name)]): #  TODO remove
                if not key.lower() in work_name.lower():
                    keys.append(key)
        annotations = keys + workdates
        if annotations:
            self.parts[wid]['annotations'] = annotations
        else:
            if 'annotations' in self.parts[wid]:
                del self.parts[wid]['annotations']
        write_log(
                release_id,
                'info',
                'make annotations has set id %s on track %s with annotation %s',
                wid,
                track,
                annotations)
        write_log(
                release_id,
                'debug',
                "Ending module %s",
                'make_annotations')

    @staticmethod
    def derive_from_title(release_id, track, title):
        """
        Attempt to parse title to get components
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param track:
        :param title:
        :return:
        """
        write_log(
                release_id,
                'info',
                "DERIVING METADATA FROM TITLE for track: %s",
                track)
        tm = track.metadata
        movt = title
        work = ""
        colons = title.count(": ")
        inter_work = None
        if '~cwp_part_levels' in tm:
            part_levels = int(tm['~cwp_part_levels'])
            if int(tm['~cwp_work_part_levels']
                   ) > 0:  # we have a work with movements
                if colons > 0:
                    title_split = title.split(': ', 1)
                    title_rsplit = title.rsplit(': ', 1)
                    if part_levels >= colons:
                        work = title_rsplit[0]
                        movt = title_rsplit[1]
                    else:
                        work = title_split[0]
                        movt = title_split[1]
        else:
            # No works found so try and just get parts from title
            if colons > 0:
                title_split = title.rsplit(': ', 1)
                work = title_split[0]
                if colons > 1:
                    colon_ind = work.rfind(':')
                    inter_work = work[colon_ind + 1:].strip()
                    work = work[:colon_ind]
                movt = title_split[1]
        write_log(release_id, 'info', "Work %s, Movt %s", work, movt)
        return work, movt, inter_work

    def process_work_artists(
            self,
            release_id,
            album,
            track,
            workIds,
            tm,
            count):
        """
        Carry out the artist processing that needs to be done in the PartLevels class
        as it requires XML lookups of the works
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param track:
        :param workIds:
        :param tm:
        :param count:
        :return:
        """
        if not self.options[track]['classical_extra_artists']:
            write_log(
                    release_id,
                    'debug',
                    'Not processing work_artists as ExtraArtists not selected to be run')
            return None
        write_log(
                release_id,
                'debug',
                'In process_work_artists for track: %s, workIds: %s',
                track,
                workIds)
        write_log(
                release_id,
                'debug',
                'In process_work_artists for track: %s, self.parts: %s',
                track,
                self.parts)
        if workIds in self.parts and 'arrangers' in self.parts[workIds]:
            write_log(
                    release_id,
                    'info',
                    'Arrangers = %s',
                    self.parts[workIds]['arrangers'])
            set_work_artists(
                self,
                release_id,
                album,
                track,
                self.parts[workIds]['arrangers'],
                tm,
                count)
        if workIds in self.works_cache:
            count += 1
            self.process_work_artists(release_id, album, track, tuple(
                self.works_cache[workIds]), tm, count)

    #################################################
    # SECTION 5 - Extend work metadata using titles #
    #################################################

    def extend_metadata(self, release_id, top_info, track, ref_height, depth):
        """
        Combine MB work and title data according to user options
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param top_info:
        :param track:
        :param ref_height:
        :param depth:
        :return:
        """
        write_log(release_id, 'debug', 'IN EXTEND_METADATA')
        tm = track.metadata
        options = self.options[track]
        movementgroup = ()
        if '~cwp_part_levels' not in tm:
            write_log(
                    release_id,
                    'debug',
                    'NO PART LEVELS. Metadata = %s',
                    tm)
            return None
        part_levels = int(tm['~cwp_part_levels'])
        write_log(
                release_id,
                'debug',
                "Extending metadata for track: %s, ref_height: %s, depth: %s, part_levels: %s",
                track,
                ref_height,
                depth,
                part_levels)
        write_log(release_id, 'info', "Metadata = %s", tm)

        # previously: ref_height = work_part_levels - ref_level,
        # where this ref-level is the level for the top-named work
        # so ref_height is effectively the "single work album" indicator (1 or 0) -
        #   i.e. where all tracks are part of one work which is implicitly the album
        #   without there being a groupheading for it
        ref_level = part_levels - ref_height
        # work_ref_level = work_part_levels - ref_height # not currently used

        # replace works and parts by those derived from the level 0 work, where
        # required, available and appropriate, but only use work names based on
        # level 0 text if it doesn't cause ambiguity

        # before embellishing with partial / arrangement etc
        vanilla_part = tm['~cwp_part_0']

        # Fix text for arrangements, partials and medleys (Done here so that
        # cache can be used)
        if options['cwp_arrangements'] and options["cwp_arrangements_text"]:
            for lev in range(
                    0,
                    ref_level):  # top level will not be an arrangement else there would be a higher level
                # needs to be a tuple to match
                if '~cwp_workid_' + str(lev) in tm:
                    tup_id = tuple(str_to_list(tm['~cwp_workid_' + str(lev)]))
                    if 'arrangement' in self.parts[tup_id] and self.parts[tup_id]['arrangement']:
                        update_list = ['~cwp_work_', '~cwp_part_']
                        if options["cwp_level0_works"] and '~cwp_X0_work_' + \
                                str(lev) in tm:
                            update_list += ['~cwp_X0_work_', '~cwp_X0_part_']
                        for item in update_list:
                            tm[item + str(lev)] = options["cwp_arrangements_text"] + \
                                ' ' + tm[item + str(lev)]

        if options['cwp_partial'] and options["cwp_partial_text"]:
            if '~cwp_workid_0' in tm:
                work0_id = tuple(str_to_list(tm['~cwp_workid_0']))
                if 'partial' in self.parts[work0_id] and self.parts[work0_id]['partial']:
                    update_list = ['~cwp_work_0', '~cwp_part_0']
                    if options["cwp_level0_works"] and '~cwp_X0_work_0' in tm:
                        update_list += ['~cwp_X0_work_0', '~cwp_X0_part_0']
                    for item in update_list:
                        meta_item = tm.getall(item)
                        if isinstance(
                                meta_item, list):  # it should be a list as I think getall always returns a list
                            if meta_item == []:
                                meta_item.append(options["cwp_partial_text"])
                            else:
                                for ind, w in enumerate(meta_item):
                                    meta_item[ind] = options["cwp_partial_text"] + ' ' + w
                            write_log(
                                release_id, 'info', 'now meta item is %s', meta_item)
                            tm[item] = meta_item
                        else:
                            tm[item] = options["cwp_partial_text"] + \
                                ' ' + tm[item]
                            write_log(
                                release_id, 'info', 'meta item is not a list')

        # fix "type 1" medley text
        if options['cwp_medley']:
            for lev in range(0, ref_level + 1):
                if '~cwp_workid_' + str(lev) in tm:
                    tup_id = tuple(str_to_list(tm['~cwp_workid_' + str(lev)]))
                    if 'medley_list' in self.parts[tup_id] and self.parts[tup_id]['medley_list']:
                        medley_list = self.parts[tup_id]['medley_list']
                        tm['~cwp_work_' + str(lev)] += " (" + options["cwp_medley_text"] + \
                            ': ' + ', '.join(medley_list) + ")"
                        if '~cwp_part_' + str(lev) in tm:
                            tm['~cwp_part_' + str(
                                lev)] = "(" + options["cwp_medley_text"] + ") " + tm['~cwp_part_' + str(lev)]

        # add any annotations for dates and keys
        if options['cwp_workdate_include'] or options['cwp_key_include'] or options['cwp_key_contingent_include']:
            if options["cwp_titles"] and part_levels == 0:
                # ~cwp_title_work_0 will not have been set, but need it to hold any annotations
                tm['~cwp_title_work_0'] = tm['~cwp_title'] or tm['title']
            for lev in range(0, part_levels + 1):
                if '~cwp_workid_' + str(lev) in tm:
                    tup_id = tuple(str_to_list(tm['~cwp_workid_' + str(lev)]))
                    if 'annotations' in self.parts[tup_id]:
                        write_log(
                                release_id,
                                'info',
                                'in extend_metadata, annotations for id %s on track %s are %s',
                                tup_id,
                                track,
                                self.parts[tup_id]['annotations'])
                        tm['~cwp_work_' + str(lev)] += " (" + \
                            ', '.join(self.parts[tup_id]['annotations']) + ")"
                        if options["cwp_level0_works"] and '~cwp_X0_work_' + \
                                str(lev) in tm:
                            tm['~cwp_X0_work_' + str(lev)] += " (" + ', '.join(
                                self.parts[tup_id]['annotations']) + ")"
                        if options["cwp_titles"] and '~cwp_title_work_' + \
                                str(lev) in tm:
                            tm['~cwp_title_work_' + str(lev)] += " (" + ', '.join(
                                self.parts[tup_id]['annotations']) + ")"
                        if lev < part_levels:
                            if 'stripped_annotations' in self.parts[tup_id]:
                                if self.parts[tup_id]['stripped_annotations']:
                                    tm['~cwp_part_' + str(lev)] += " (" + ', '.join(
                                        self.parts[tup_id]['stripped_annotations']) + ")"
                                    if options["cwp_level0_works"] and '~cwp_X0_part_' + \
                                            str(lev) in tm:
                                        tm['~cwp_X0_part_' + str(lev)] += " (" + ', '.join(
                                            self.parts[tup_id]['stripped_annotations']) + ")"
                                    if options["cwp_titles"] and '~cwp_title_part_' + \
                                            str(lev) in tm:
                                        tm['~cwp_title_part' + str(lev)] += " (" + ', '.join(
                                            self.parts[tup_id]['stripped_annotations']) + ")"

        part = []
        work = []
        for level in range(0, part_levels):
            part.append(tm['~cwp_part_' + str(level)])
            work.append(tm['~cwp_work_' + str(level)])
        work.append(tm['~cwp_work_' + str(part_levels)])

        # Use level_0-derived names if applicable
        if options["cwp_level0_works"]:
            for level in range(0, part_levels + 1):
                if '~cwp_X0_work_' + str(level) in tm:
                    work[level] = tm['~cwp_X0_work_' + str(level)]
                else:
                    if level != 0:
                        work[level] = ''
                if part and len(part) > level:
                    if '~cwp_X0_part_' + str(level) in tm:
                        part[level] = tm['~cwp_X0_part_' + str(level)]
                    else:
                        if level != 0:
                            part[level] = ''

        # set up group heading and part
        if part_levels > 0:
            groupheading = work[1]
            work_main = work[ref_level]
            inter_work = None
            work_titles = tm['~cwp_title_work_' + str(ref_level)]
            if ref_level > 1:
                for r in range(1, ref_level):
                    if inter_work:
                        inter_work = ': ' + inter_work
                    inter_work = part[r] + (inter_work or '')
                groupheading = work[ref_level] + ':: ' + (inter_work or '')
        else:
            groupheading = work[0]
            work_main = groupheading
            inter_work = None
            work_titles = None

        # determine movement grouping (highest level that is not a collection)
        if '~cwp_workid_top' in tm:
            movementgroup = tuple(str_to_list(tm['~cwp_workid_top']))
            n = part_levels
            write_log(
                    release_id,
                    'debug',
                    "In extend. self.parts[%s]['is_collection']: %s",
                    movementgroup,
                    self.parts[movementgroup]['is_collection'])
            while self.parts[movementgroup]['is_collection']:
                n -= 1
                if n < 0:
                    # shouldn't happen in theory as bottom level can't be a collection, but just in case...
                    break
                if '~cwp_workid_'  + str(n) in tm:
                    movementgroup = tuple(str_to_list(tm['~cwp_workid_'  + str(n)]))
                else:
                    break

        # set part text (initially)
        if part:
            part_main = part[0]
        else:
            part_main = work[0]
        tm['~cwp_part'] = part_main

        # fix medley text for "type 2" medleys
        type2_medley = False
        if self.parts[tuple(str_to_list(tm['~cwp_workid_0']))
                      ]['medley'] and options['cwp_medley']:
            if options["cwp_medley_text"]:
                if part_levels > 0:
                    medleyheading = groupheading + ':: ' + part[0]
                else:
                    medleyheading = groupheading
                groupheading = medleyheading + \
                    ' (' + options["cwp_medley_text"] + ')'
            type2_medley = True

        tm['~cwp_groupheading'] = groupheading
        tm['~cwp_work'] = work_main
        tm['~cwp_inter_work'] = inter_work
        tm['~cwp_title_work'] = work_titles
        write_log(
                release_id,
                'debug',
                "Groupheading set to: %s",
                groupheading)
        # extend group heading from title metadata
        if groupheading:
            ext_groupheading = groupheading
            title_groupheading = None
            ext_work = work_main
            ext_inter_work = inter_work
            inter_title_work = ""

            if '~cwp_title_work_levels' in tm:

                title_depth = int(tm['~cwp_title_work_levels'])
                write_log(
                        release_id,
                        'info',
                        "Title_depth: %s",
                        title_depth)
                diff_work = [""] * ref_level
                diff_part = [""] * ref_level
                title_tag = [""]
                # level 0 work for title # was 'x'  # to avoid errors, reset
                # before used
                tw_str_lower = 'title'
                max_d = min(ref_level, title_depth) + 1
                for d in range(1, max_d):
                    tw_str = '~cwp_title_work_' + str(d)
                    write_log(release_id, 'info', "TW_STR = %s", tw_str)
                    if tw_str in tm:
                        title_tag.append(tm[tw_str])
                        title_work = title_tag[d]
                        work_main = ''
                        for w in range(d, ref_level + 1):
                            work_main += (work[w] + ' ')
                        diff_work[d - 1] = self.diff_pair(
                            release_id, track, tm, work_main, title_work)
                        if diff_work[d - 1]:
                            diff_work[d - 1] = diff_work[d - 1].strip('.;:-,')
                            if diff_work[d - 1] == '…':
                                diff_work[d - 1] = ''
                        if d > 1 and tw_str_lower in tm:
                            title_part = self.strip_parent_from_work(
                                track, release_id, tm[tw_str_lower], tm[tw_str], 0, False)[0]
                            if title_part:
                                title_part = title_part.strip(' .;:-,')
                            tm['~cwp_title_part_' +
                                str(d - 1)] = title_part
                            part_n = part[d - 1]
                            diff_part[d - 1] = self.diff_pair(
                                release_id, track, tm, part_n, title_part) or ""
                            if diff_part[d - 1] == '…':
                                diff_part[d - 1] = ''
                    else:
                        title_tag.append('')
                    tw_str_lower = tw_str
                # remove duplicate items at lower levels in diff_work:
                for w in range(ref_level - 2, -1, -1):
                    for higher in range(1, ref_level - w):
                        if diff_work[w] and diff_work[w + higher]:
                            diff_work[w] = diff_work[w].replace(
                                diff_work[w + higher], '').strip(' .;:-,\u2026')
                            # if diff_work[w] == '…':
                            #     diff_work[w] = ''
                write_log(
                        release_id,
                        'info',
                        "diff list for works: %s",
                        diff_work)
                write_log(
                        release_id,
                        'info',
                        "diff list for parts: %s",
                        diff_part)
                if not diff_work or len(diff_work) == 0:
                    if part_levels > 0:
                        ext_groupheading = groupheading
                else:
                    write_log(
                            release_id,
                            'debug',
                            "Now calc extended groupheading...")
                    write_log(
                            release_id,
                            'info',
                            "depth = %s, ref_level = %s, title_depth = %s",
                            depth,
                            ref_level,
                            title_depth)
                    write_log(
                            release_id,
                            'info',
                            "diff_work = %s, diff_part = %s",
                            diff_work,
                            diff_part)
                    # remove duplications:
                    for lev in range(1, ref_level):
                        for diff_list in [diff_work, diff_part]:
                            if diff_list[lev] and diff_list[lev - 1]:
                                diff_list[lev - 1] = self.diff_pair(
                                    release_id, track, tm, diff_list[lev], diff_list[lev - 1])
                                if diff_list[lev - 1] == '…':
                                    diff_list[lev - 1] = ''
                    write_log(
                            release_id,
                            'info',
                            "Removed duplication. Revised diff_work = %s, diff_part = %s",
                            diff_work,
                            diff_part)
                    if part_levels > 0 and depth >= 1:
                        addn_work = []
                        addn_part = []
                        for stripped_work in diff_work:
                            if stripped_work:
                                write_log(
                                        release_id, 'info', "Stripped work = %s", stripped_work)
                                addn_work.append(" {" + stripped_work + "}")
                            else:
                                addn_work.append("")
                        for stripped_part in diff_part:
                            if stripped_part and stripped_part != "":
                                write_log(release_id, 'info', "Stripped part = %s", stripped_part)
                                addn_part.append(" {" + stripped_part + "}")
                            else:
                                addn_part.append("")
                        write_log(
                                release_id,
                                'info',
                                "addn_work = %s, addn_part = %s",
                                addn_work,
                                addn_part)
                        ext_groupheading = work[1] + addn_work[0]
                        ext_work = work[ref_level] + addn_work[ref_level - 1]
                        ext_inter_work = ""
                        inter_title_work = ""
                        title_groupheading = tm['~cwp_title_work_1']
                        if ref_level > 1:
                            for r in range(1, ref_level):
                                if ext_inter_work:
                                    ext_inter_work = ': ' + ext_inter_work
                                ext_inter_work = part[r] + \
                                    addn_work[r - 1] + ext_inter_work
                            ext_groupheading = work[ref_level] + \
                                addn_work[ref_level - 1] + ':: ' + ext_inter_work
                        if title_depth > 1 and ref_level > 1:
                            for r in range(1, min(title_depth, ref_level)):
                                if inter_title_work:
                                    inter_title_work = ': ' + inter_title_work
                                inter_title_work = tm['~cwp_title_part_' +
                                                      str(r)] + inter_title_work
                            title_groupheading = tm['~cwp_title_work_' + str(
                                min(title_depth, ref_level))] + ':: ' + inter_title_work

                    else:
                        ext_groupheading = groupheading  # title will be in part
                        ext_work = work_main
                        ext_inter_work = inter_work
                        inter_title_work = ""

                    write_log(release_id, 'debug', ".... ext_groupheading done")

            if ext_groupheading:
                write_log(
                        release_id,
                        'info',
                        "EXTENDED GROUPHEADING: %s",
                        ext_groupheading)
                tm['~cwp_extended_groupheading'] = ext_groupheading
                tm['~cwp_extended_work'] = ext_work
                if ext_inter_work:
                    tm['~cwp_extended_inter_work'] = ext_inter_work
                if inter_title_work:
                    tm['~cwp_inter_title_work'] = inter_title_work
                if title_groupheading:
                    tm['~cwp_title_groupheading'] = title_groupheading
                    write_log(
                            release_id,
                            'info',
                            "title_groupheading = %s",
                            title_groupheading)
        # extend part from title metadata
        write_log(
                release_id,
                'debug',
                "NOW EXTEND PART...(part = %s)",
                part_main)
        if part_main:
            if '~cwp_title_part_0' in tm:
                movement = tm['~cwp_title_part_0']
            else:
                movement = tm['~cwp_title_part_0'] or tm['~cwp_title'] or tm['title']
            if '~cwp_extended_groupheading' in tm:
                work_compare = tm['~cwp_extended_groupheading'] + \
                    ': ' + part_main
            elif '~cwp_work_1' in tm:
                work_compare = work[1] + ': ' + part_main
            else:
                work_compare = work[0]
            diff = self.diff_pair(
                release_id, track, tm, work_compare, movement)
            # compare with the fullest possible work name, not the stripped one
            #  - to maximise the duplication elimination
            reverse_diff = self.diff_pair(
                release_id, track, tm, movement, vanilla_part)
            # for the reverse comparison use the part name without any work details or annotation
            if diff and reverse_diff and self.parts[tuple(str_to_list(tm['~cwp_workid_0']))]['partial']:
                diff = movement
            # for partial tracks, do not eliminate the title text as it is
            # frequently deliberately a component of the the overall work txt
            # (unless it is identical)
            fill_part = options['cwp_fill_part']
            # To fill part with title text if it
            # would otherwise have no text other than arrangement or partial
            # annotations
            if not diff and not vanilla_part and part_levels > 0 and fill_part:
                # In other words the movement will have no text other than
                # arrangement or partial annotations
                diff = movement
            write_log(release_id, 'info', "DIFF PART - MOVT. ti =%s", diff)
            write_log(release_id,
                          'info',
                          'medley indicator for %s is %s',
                          tm['~cwp_workid_0'],
                          self.parts[tuple(str_to_list(tm['~cwp_workid_0']))]['medley'])

            if type2_medley:
                tm['~cwp_extended_part'] = "{" + movement + "}"
            else:
                if diff:
                    tm['~cwp_extended_part'] = part_main + \
                        " {" + diff.strip() + "}"
                else:
                    tm['~cwp_extended_part'] = part_main
                if part_levels == 0:
                    if tm['~cwp_extended_groupheading']:
                        del tm['~cwp_extended_groupheading']

        # remove unwanted groupheadings (needed them up to now for adding
        # extensions)
        if '~cwp_groupheading' in tm and tm['~cwp_groupheading'] == tm['~cwp_part']:
            del tm['~cwp_groupheading']
        if '~cwp_title_groupheading' in tm and tm['~cwp_title_groupheading'] == tm['~cwp_title_part']:
            del tm['~cwp_title_groupheading']
        # clean up groupheadings (may be stray separators if level 0  or title
        # options used)
        if '~cwp_groupheading' in tm:
            tm['~cwp_groupheading'] = tm['~cwp_groupheading'].strip(
                ':').strip(
                options['cwp_single_work_sep']).strip(
                options['cwp_multi_work_sep'])
        if '~cwp_extended_groupheading' in tm:
            tm['~cwp_extended_groupheading'] = tm['~cwp_extended_groupheading'].strip(
                ':').strip(
                options['cwp_single_work_sep']).strip(
                options['cwp_multi_work_sep'])
        if '~cwp_title_groupheading' in tm:
            tm['~cwp_title_groupheading'] = tm['~cwp_title_groupheading'].strip(
                ':').strip(
                options['cwp_single_work_sep']).strip(
                options['cwp_multi_work_sep'])
        write_log(release_id, 'debug', "....done")
        return movementgroup

    ##########################################################
    # SECTION 6- Write metadata to tags according to options #
    ##########################################################

    def publish_metadata(self, release_id, album, track, movement_info={}):
        """
        Write out the metadata according to user options
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param album:
        :param track:
        :param movement_info: format is {'movement-group': movementgroup, 'movement-number': movementnumber}
        :return:
        """
        write_log(release_id, 'debug', "IN PUBLISH METADATA for %s", track)
        options = self.options[track]
        tm = track.metadata
        tm['~cwp_version'] = PLUGIN_VERSION

        # set movement grouping tags (hidden vars)
        if movement_info:
            movementtotal = self.parts[tuple(movement_info['movement-group'])]['movement-total']
            if movementtotal > 1:
                tm['~cwp_movt_num'] = movement_info['movement-number']
                tm['~cwp_movt_tot'] = movementtotal

        # album composers needed by map_tags (set in set_work_artists)
        if 'composer_lastnames' in self.album_artists[album]:
            last_names = seq_last_names(self, album)
            self.append_tag(
                release_id,
                tm,
                '~cea_album_composer_lastnames',
                last_names)

        write_log(release_id, 'info', "Check options")
        if options["cwp_titles"]:
            write_log(release_id, 'info', "titles")
            part = tm['~cwp_title_part_0'] or tm['~cwp_title_work_0']or tm['~cwp_title'] or tm['title']
            # for multi-level work display
            groupheading = tm['~cwp_title_groupheading'] or ""
            # for single-level work display
            work = tm['~cwp_title_work'] or ""
            inter_work = tm['~cwp_inter_title_work'] or ""
        elif options["cwp_works"]:
            write_log(release_id, 'info', "works")
            part = tm['~cwp_part']
            groupheading = tm['~cwp_groupheading'] or ""
            work = tm['~cwp_work'] or ""
            inter_work = tm['~cwp_inter_work'] or ""
        else:
            # options["cwp_extended"]
            write_log(release_id, 'info', "extended")
            part = tm['~cwp_extended_part']
            groupheading = tm['~cwp_extended_groupheading'] or ""
            work = tm['~cwp_extended_work'] or ""
            inter_work = tm['~cwp_extended_inter_work'] or ""
        write_log(release_id, 'info', "Done options")
        p1 = RE_ROMANS_AT_START
        # Matches positive integers with punctuation
        p2 = re.compile(r'^\W*\d+[.):-]')
        movt = part
        for _ in range(
                0, 5):  # in case of multiple levels
            movt = p2.sub('', p1.sub('', movt)).strip()
        write_log(release_id, 'info', "Done movt")
        movt_inc_tags = options["cwp_movt_tag_inc"].split(",")
        movt_inc_tags = [x.strip(' ') for x in movt_inc_tags]
        movt_exc_tags = options["cwp_movt_tag_exc"].split(",")
        movt_exc_tags = [x.strip(' ') for x in movt_exc_tags]
        movt_inc_1_tags = options["cwp_movt_tag_inc1"].split(",")
        movt_inc_1_tags = [x.strip(' ') for x in movt_inc_1_tags]
        movt_exc_1_tags = options["cwp_movt_tag_exc1"].split(",")
        movt_exc_1_tags = [x.strip(' ') for x in movt_exc_1_tags]
        movt_no_tags = options["cwp_movt_no_tag"].split(",")
        movt_no_tags = [x.strip(' ') for x in movt_no_tags]
        movt_no_sep = options["cwp_movt_no_sep"]
        movt_tot_tags = options["cwp_movt_tot_tag"].split(",")
        movt_tot_tags = [x.strip(' ') for x in movt_tot_tags]
        gh_tags = options["cwp_work_tag_multi"].split(",")
        gh_tags = [x.strip(' ') for x in gh_tags]
        gh_sep = options["cwp_multi_work_sep"]
        work_tags = options["cwp_work_tag_single"].split(",")
        work_tags = [x.strip(' ') for x in work_tags]
        work_sep = options["cwp_single_work_sep"]
        top_tags = options["cwp_top_tag"].split(",")
        top_tags = [x.strip(' ') for x in top_tags]

        write_log(
                release_id,
                'info',
                "Done splits. gh_tags: %s, work_tags: %s, movt_inc_tags: %s, movt_exc_tags: %s, movt_no_tags: %s",
                gh_tags,
                work_tags,
                movt_inc_tags,
                movt_exc_tags,
                movt_no_tags)

        for tag in gh_tags + work_tags + movt_inc_tags + movt_exc_tags + movt_no_tags:
            tm[tag] = ""
        for tag in gh_tags:
            if tag in movt_inc_tags + movt_exc_tags + movt_no_tags:
                self.append_tag(release_id, tm, tag, groupheading, gh_sep)
            else:
                self.append_tag(release_id, tm, tag, groupheading)
        for tag in work_tags:
            if tag in movt_inc_1_tags + movt_exc_1_tags + movt_no_tags:
                self.append_tag(release_id, tm, tag, work, work_sep)
            else:
                self.append_tag(release_id, tm, tag, work)
            if '~cwp_part_levels' in tm and int(tm['~cwp_part_levels']) > 0:
                self.append_tag(
                    release_id,
                    tm,
                    'show work movement',
                    '1')  # original tag for iTunes, kept for backwards compatibility
                self.append_tag(
                    release_id,
                    tm,
                    'showmovement',
                    '1')  # new tag for iTunes & MusicBee, consistent with Picard tag docs
        for tag in top_tags:
            if '~cwp_work_top' in tm:
                self.append_tag(release_id, tm, tag, tm['~cwp_work_top'])

        if '~cwp_movt_num' in tm and len(tm['~cwp_movt_num']) > 0:
            movt_num_punc = tm['~cwp_movt_num'] + movt_no_sep + ' '
        else:
            movt_num_punc = ''

        for tag in movt_no_tags:
            if tag not in movt_inc_tags + movt_exc_tags + movt_inc_1_tags + movt_exc_1_tags:
                self.append_tag(release_id, tm, tag, tm['~cwp_movt_num'])

        for tag in movt_tot_tags:
            self.append_tag(release_id, tm, tag, tm['~cwp_movt_tot'])

        for tag in movt_exc_tags:
            if tag in movt_no_tags:
                movt = movt_num_punc + movt
            self.append_tag(release_id, tm, tag, movt)

        for tag in movt_inc_tags:
            if tag in movt_no_tags:
                part = movt_num_punc + part
            self.append_tag(release_id, tm, tag, part)


        for tag in movt_inc_1_tags + movt_exc_1_tags:
            if tag in movt_inc_1_tags:
                pt = part
            else:
                pt = movt
            if tag in movt_no_tags:
                pt = movt_num_punc + pt
            if inter_work and inter_work != "":
                if tag in movt_exc_tags + movt_inc_tags and tag != "":
                    write_log(
                        release_id,
                        'warning',
                        "Tag %s will have multiple contents",
                        tag)
                    if self.WARNING:
                        self.append_tag(release_id, tm, '~cwp_warning', '6. Tag ' +
                                    tag +
                                    ' has multiple contents')
                self.append_tag(
                    release_id,
                    tm,
                    tag,
                    inter_work +
                    work_sep +
                    " " +
                    pt)
            else:
                self.append_tag(release_id, tm, tag, pt)

        for tag in movt_exc_tags + movt_inc_tags + movt_exc_1_tags + movt_inc_1_tags:
            if tag in movt_no_tags:
                # i.e treat as one item, not multiple
                tm[tag] = "".join(re.split('|'.join(self.SEPARATORS), tm[tag]))

        # write "SongKong" tags
        if options['cwp_write_sk']:
            write_log(release_id, 'debug', "Writing SongKong work tags")
            if '~cwp_part_levels' in tm:
                part_levels = int(tm['~cwp_part_levels'])
                for n in range(0, part_levels + 1):
                    if '~cwp_work_' + \
                            str(n) in tm and '~cwp_workid_' + str(n) in tm:
                        source = tm['~cwp_work_' + str(n)]
                        source_id = list(
                            tuple(str_to_list(tm['~cwp_workid_' + str(n)])))
                        if n == 0:
                            self.append_tag(
                                release_id, tm, 'musicbrainz_work_composition', source)
                            for source_id_item in source_id:
                                self.append_tag(
                                    release_id, tm, 'musicbrainz_work_composition_id', source_id_item)
                        if n == part_levels:
                            self.append_tag(
                                release_id, tm, 'musicbrainz_work', source)
                            if 'musicbrainz_workid' in tm:
                                del tm['musicbrainz_workid']
                            # Delete the Picard version of this tag before
                            # replacing it with the SongKong version
                            for source_id_item in source_id:
                                self.append_tag(
                                    release_id, tm, 'musicbrainz_workid', source_id_item)
                        if n != 0 and n != part_levels:
                            self.append_tag(
                                release_id, tm, 'musicbrainz_work_part_level' + str(n), source)
                            for source_id_item in source_id:
                                self.append_tag(
                                    release_id,
                                    tm,
                                    'musicbrainz_work_part_level' +
                                    str(n) +
                                    '_id',
                                    source_id_item)

        # carry out tag mapping
        tm['~cea_works_complete'] = "Y"
        map_tags(options, release_id, album, tm)

        write_log(release_id, 'debug', "Published metadata for %s", track)
        if options['cwp_options_tag'] != "":
            self.cwp_options = collections.defaultdict(
                lambda: collections.defaultdict(dict))

            for opt in plugin_options('workparts') + plugin_options('genres'):
                if 'name' in opt:
                    if 'value' in opt:
                        if options[opt['option']]:
                            self.cwp_options['Classical Extras']['Works options'][opt['name']] = opt['value']
                    else:
                        self.cwp_options['Classical Extras']['Works options'][opt['name']
                                                                              ] = options[opt['option']]

            write_log(release_id, 'info', "Options %s", self.cwp_options)
            if options['ce_version_tag'] and options['ce_version_tag'] != "":
                self.append_tag(release_id, tm, options['ce_version_tag'], str(
                    'Version ' + tm['~cwp_version'] + ' of Classical Extras'))
            if options['cwp_options_tag'] and options['cwp_options_tag'] != "":
                self.append_tag(release_id, tm, options['cwp_options_tag'] +
                                ':workparts_options', json.loads(
                    json.dumps(
                        self.cwp_options)))
        if self.ERROR and "~cwp_error" in tm:
            for error in str_to_list(tm['~cwp_error']):
                code = error[0]
                self.append_tag(release_id, tm, '001_errors:' + code, error)
        if self.WARNING and "~cwp_warning" in tm:
            for warning in str_to_list(tm['~cwp_warning']):
                wcode = warning[0]
                self.append_tag(release_id, tm, '002_warnings:' + wcode, warning)


    def append_tag(self, release_id, tm, tag, source, sep=None):
        """
        pass to main append routine
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param tm:
        :param tag:
        :param source:
        :param sep: separators may be used to split string into list on appending
        :return:
        """
        write_log(
                release_id,
                'info',
                "In append_tag (Work parts). tag = %s, source = %s, sep =%s",
                tag,
                source,
                sep)
        append_tag(release_id, tm, tag, source, self.SEPARATORS)
        write_log(
                release_id,
                'info',
                "Appended. Resulting contents of tag: %s are: %s",
                tag,
                tm[tag])

    ################################################
    # SECTION 7 - Common string handling functions #
    ################################################

    def strip_parent_from_work(
            self,
            track,
            release_id,
            work,
            parent,
            part_level,
            extend,
            parentId=None,
            workId=None):
        """
        Remove common text
        :param track:
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param work: could be a list of works, all of which require stripping
        :param parent:
        :param part_level:
        :param extend:
        :param parentId:
        :param workId:
        :return:
        """
        # extend=True is used [ NO LONGER to find "full_parent" names] + (with parentId)
        #  to trigger recursion if unable to strip parent name from work and also to look for common subsequences
        # extend=False is used when this routine is called for other purposes
        # than strict work: parent relationships
        options = self.options[track]
        write_log(
            release_id,
            'debug',
            "STRIPPING HIGHER LEVEL WORK TEXT FROM PART NAMES")
        write_log(
            release_id,
            'info',
            'PARAMS: WORK = %r, PARENT = %s, PART_LEVEL = %s, EXTEND= %s',
            work,
            parent,
            part_level,
            extend)
        if isinstance(work, list):
            result = []
            for w, work_item in enumerate(work):
                if workId and isinstance(workId, list):
                    sub_workId = workId[w]
                else:
                    sub_workId = workId
                result.append(
                    self.strip_parent_from_work(
                        track,
                        release_id,
                        work_item,
                        parent,
                        part_level,
                        extend,
                        parentId,
                        sub_workId)[0])
            return result, parent
        if not isinstance(parent, str):
            # in case it is a list - make sure it is a string
            parent = '; '.join(parent)
        if not isinstance(work, str):
            work = '; '.join(work)

        # replace any punctuation or numbers, with a space (to remove any
        # inconsistent punctuation and numbering) - (?u) specifies the
        # re.UNICODE flag in sub
        clean_parent = re.sub("(?u)[\W]", ' ', parent)
        # now allow the spaces to be filled with up to 2 non-letters
        pattern_parent = clean_parent.replace(" ", "\W{0,2}")
        pattern_parent = "(^|.*?\s)(\W*" + pattern_parent + "\W?)(.*)"
        # (removed previous alternative pattern for extend=true, owing to catastrophic backtracking)
        write_log(
                release_id,
                'info',
                "Pattern parent: %s, Work: %s",
                pattern_parent,
                work)
        p = re.compile(pattern_parent, re.IGNORECASE | re.UNICODE)
        m = p.search(work)
        if m:
            write_log(release_id, 'info', "Matched...")
            if m.group(1):
                stripped_work = m.group(1) + u"\u2026" + m.group(3)
            else:
                stripped_work = m.group(3)
            # may not have a full work name in the parent (missing op. no.
            # etc.)
            stripped_work = stripped_work.lstrip(":;,.- ")
        else:
            write_log(release_id, 'info', "No match...")
            stripped_work = work

            if extend and options['cwp_common_chars'] > 0:
                # try stripping out a common substring (multiple times until
                # nothing more stripped)
                prev_stripped_work = ''
                counter = 1
                while prev_stripped_work != stripped_work:
                    if counter > 20:
                        break  # in case something went awry
                    prev_stripped_work = stripped_work
                    parent_tuples = self.listify(release_id, track, parent)
                    parent_words = parent_tuples['s_tuple']
                    clean_parent_words = list(parent_tuples['s_test_tuple'])
                    for w, word in enumerate(clean_parent_words):
                        clean_parent_words[w] = self.boil(release_id, word)
                    work_tuples = self.listify(
                        release_id, track, stripped_work)
                    work_words = work_tuples['s_tuple']
                    clean_work_words = list(work_tuples['s_test_tuple'])
                    for w, word in enumerate(clean_work_words):
                        clean_work_words[w] = self.boil(release_id, word)
                    common_dets = longest_common_substring(
                        clean_work_words, clean_parent_words)
                    # this is actually a list, not a string, since list
                    # arguments were supplied
                    common_seq = common_dets['string']
                    seq_length = common_dets['length']
                    seq_start = common_dets['start']
                    # the original items (before 'cleaning')
                    full_common_seq = [
                        x.group() for x in work_words[seq_start:seq_start + seq_length]]
                    # number of words in common_seq
                    full_seq_length = sum([len(x.split())
                                           for x in full_common_seq])
                    write_log(
                        release_id,
                        'info',
                        'Checking common sequence between parent and work, iteration %s ... parent_words = %s',
                        counter,
                        parent_words)
                    write_log(
                        release_id,
                        'info',
                        '... longest common sequence = %s',
                        common_seq)
                    if full_seq_length > 0:
                        potential_stripped_work = stripped_work
                        if seq_start > 0:
                            ellipsis = ' ' + u"\u2026" + ' '
                        else:
                            ellipsis = ''
                        if counter > 1:
                            potential_stripped_work = stripped_work.rstrip(
                                ' :,-\u2026')
                            potential_stripped_work = potential_stripped_work.replace(
                                '(\u2026)', '').rstrip()
                        potential_stripped_work = potential_stripped_work[:work_words[seq_start].start(
                        )] + ellipsis + potential_stripped_work[work_words[seq_start + seq_length - 1].end():]
                        potential_stripped_work = potential_stripped_work.lstrip(
                            ' :,-')
                        potential_stripped_work = re.sub(
                            r'(\W*…\W*)(\W*…\W*)', ' … ', potential_stripped_work)
                        potential_stripped_work = strip_excess_punctuation(
                            potential_stripped_work)

                        if full_seq_length >= options['cwp_common_chars'] \
                                or potential_stripped_work == '' and options['cwp_allow_empty_parts']:
                            # Make sure it is more than the required min (it will be > 0 anyway)
                            # unless a full strip will result anyway (and blank
                            # part names are allowed)
                            stripped_work = potential_stripped_work
                            if not stripped_work or stripped_work == '':
                                if workId and \
                                        ('arrangement' in self.parts[workId] and self.parts[workId]['arrangement']
                                         and options['cwp_arrangements'] and options['cwp_arrangements_text']) \
                                        or ('partial' in self.parts[workId] and self.parts[workId]['partial']
                                            and options['cwp_partial'] and options['cwp_partial_text']) \
                                        and options['cwp_allow_empty_parts']:
                                    pass
                                else:
                                    stripped_work = prev_stripped_work  # do not allow empty parts
                    counter += 1
            stripped_work = strip_excess_punctuation(stripped_work)
            write_log(
                    release_id,
                    'info',
                    'stripped_work = %s',
                    stripped_work)
            if extend and parentId and parentId in self.works_cache:
                write_log(
                        release_id,
                        'info',
                        "Looking for match at next level up")
                grandparentIds = tuple(self.works_cache[parentId])
                grandparent = self.parts[grandparentIds]['name']
                stripped_work = self.strip_parent_from_work(
                    track,
                    release_id,
                    stripped_work,
                    grandparent,
                    part_level,
                    True,
                    grandparentIds,
                    workId)[0]

        write_log(
                release_id,
                'info',
                "Finished strip_parent_from_work, Work: %s",
                work)
        write_log(release_id, 'info', "Stripped work: %s", stripped_work)
        # Changed full_parent to parent after removal of 'extend' logic above
        stripped_work = strip_excess_punctuation(stripped_work)
        write_log(release_id, 'info', "Stripped work after punctuation removal: %s", stripped_work)
        return stripped_work, parent

    def diff_pair(
            self,
            release_id,
            track,
            tm,
            mb_item,
            title_item,
            remove_numbers=True):
        """
        Removes common text (or synonyms) from title item
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param track:
        :param tm:
        :param mb_item:
        :param title_item:
        :param remove_numbers: remove movement numbers when comparing (not currently called with False by anything)
        :return: Reduced title item
        """
        write_log(release_id, 'debug', "Inside DIFF_PAIR")
        mb = mb_item.strip()
        write_log(release_id, 'info', "mb = %s", mb)
        write_log(release_id, 'info', "title_item = %s", title_item)
        if not mb:
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    None)
            return None
        ti = title_item.strip(" :;-.,")
        if ti.count('"') == 1:
            ti = ti.strip('"')
        if ti.count("'") == 1:
            ti = ti.strip("'")
        write_log(release_id, 'info', "ti (amended) = %s", ti)
        if not ti:
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    None)
            return None

        if self.options[track]["cwp_removewords_p"]:
            removewords = self.options[track]["cwp_removewords_p"].split(',')
        else:
            removewords = []
        write_log(release_id, 'info', "Prefixes = %s", removewords)
        # remove numbers, roman numerals, part etc and punctuation from the
        # start
        write_log(release_id, 'info', "checking prefixes")
        found_prefix = True
        i = 0
        while found_prefix:
            if i > 20:
                break  # safety valve
            found_prefix = False
            for prefix in removewords:
                if prefix[0] != " ":
                    prefix2 = str(prefix).lower().lstrip()
                    write_log(
                            release_id, 'info', "checking prefix %s", prefix2)
                    if mb.lower().startswith(prefix2):
                        found_prefix = True
                        mb = mb[len(prefix2):]
                    if ti.lower().startswith(prefix2):
                        found_prefix = True
                        ti = ti[len(prefix2):]
            mb = mb.strip()
            ti = ti.strip()
            i += 1
            write_log(
                    release_id,
                    'info',
                    "pairs after prefix strip iteration %s. mb = %s, ti = %s",
                    i,
                    mb,
                    ti)
        write_log(release_id, 'info', "Prefixes checked")

        #  replacements
        replacements = self.replacements[track]
        write_log(release_id, 'info', "Replacement: %s", replacements)
        for tup in replacements:
            for ind in range(0, len(tup) - 1):
                ti = re.sub(tup[ind], tup[-1], ti, flags=re.IGNORECASE)
        write_log(
                release_id,
                'debug',
                'Looking for any new words in the title')

        write_log(
                release_id,
                'info',
                "Check before splitting: mb = %s, ti = %s",
                mb,
                ti)

        ti_tuples = self.listify(release_id, track, ti)
        ti_tuple = ti_tuples['s_tuple']
        ti_test_tuple = ti_tuples['s_test_tuple']

        mb_tuples = self.listify(release_id, track, mb)
        mb_test_tuple = mb_tuples['s_test_tuple']

        write_log(
                release_id,
                'info',
                "Check after splitting: mb_test = %s, ti = %s, ti_test = %s",
                mb_test_tuple,
                ti_tuple,
                ti_test_tuple)

        ti_stencil = self.stencil(release_id, ti_tuple, ti)
        ti_list = ti_stencil['match list']
        ti_list_punc = ti_stencil['gap list']
        ti_test_list = list(ti_test_tuple)
        if ti_stencil['dummy']:
            # to deal with case where stencil has added a dummy item at the
            # start
            ti_test_list.insert(0, '')
        write_log(release_id, 'info', 'ti_test_list = %r', ti_test_list)
        # zip is an iterable, not a list in Python 3, so make it re-usable
        ti_zip_list = list(zip(ti_list, ti_list_punc))

        # len(ti_list) should be = len(ti_test_list) as only difference should
        # be synonyms which are each one 'word'
        # However, because of the grouping of some words via regex, it is possible that inconsistencies might arise
        # Therefore, there is a test here to check for equality and produce an
        # error message (but continue processing)
        if len(ti_list) != len(ti_test_list):
            write_log(
                    release_id,
                    'error',
                    'Mismatch in title list after canonization/synonymization')
            write_log(
                release_id,
                'error',
                'Orig. title list = %r. Test list = %r',
                ti_list,
                ti_test_list)
        # mb_test_tuple = self.listify(release_id, track, mb_test)
        mb_list2 = list(mb_test_tuple)
        for index, mb_bit2 in enumerate(mb_list2):
            mb_list2[index] = self.boil(release_id, mb_bit2)
            write_log(
                    release_id,
                    'info',
                    "mb_list2[%s] = %s",
                    index,
                    mb_list2[index])
        ti_new = []
        ti_rich_list = []
        for i, ti_bit_test in enumerate(ti_test_list):
            if i <= len(ti_list) - 1:
                ti_bit = ti_zip_list[i]
                # NB ti_bit is a tuple where the word (1st item) is grouped
                # with its following punctuation (2nd item)
            else:
                ti_bit = ('', '')
            write_log(
                    release_id,
                    'info',
                    "i = %s, ti_bit_test = %s, ti_bit = %s",
                    i,
                    ti_bit_test,
                    ti_bit)
            ti_rich_list.append((ti_bit, True))
            # Boolean to indicate whether ti_bit is a new word

            if ti_bit_test == '':
                ti_rich_list[i] = (ti_bit, False)
            else:
                if self.boil(release_id, ti_bit_test) in mb_list2:
                    ti_rich_list[i] = (ti_bit, False)

        if remove_numbers:  # Only remove numbers at the start if they are not new items
            p0 = re.compile(r'\b\w+\b')
            p1 = RE_ROMANS
            p2 = re.compile(r'^\d+')  # Matches positive integers
            starts_with_numeral = True
            while starts_with_numeral:
                starts_with_numeral = False
                if ti_rich_list and p0.match(ti_rich_list[0][0][0]):
                    start_word = p0.match(ti_rich_list[0][0][0]).group()
                    if p1.match(start_word) or p2.match(start_word):
                        if not ti_rich_list[0][1]:
                            starts_with_numeral = True
                            ti_rich_list.pop(0)
                            ti_test_list.pop(0)

        write_log(
                release_id,
                'info',
                "ti_rich_list before removing singletons = %s. length = %s",
                ti_rich_list,
                len(ti_rich_list))

        s = 0
        index = 0
        change = ()
        for i, (t, n) in enumerate(ti_rich_list):
            if n:
                s += 1
                index = i
                change = t  # NB this is a tuple

        p = self.options[track]["cwp_proximity"]
        ep = self.options[track]["cwp_end_proximity"]
        # NB these may be modified later

        if s == 1:
            if 0 < index < len(ti_rich_list) - 1:
                # ignore singleton new words in middle of title unless they are
                # within "cwp_end_proximity" from the start or end
                write_log(
                    release_id, 'info', 'item length is %s', len(
                        change[0].split()))
                # also make sure that the item is just one word before
                # eliminating
                if ep < index < len(ti_rich_list) - ep - \
                        1 and len(change[0].split()) == 1:
                    ti_rich_list[index] = (change, False)
                    s = 0

        # remove prepositions
        write_log(
                release_id,
                'info',
                "ti_rich_list before removing prepositions = %s. length = %s",
                ti_rich_list,
                len(ti_rich_list))
        if self.options[track]["cwp_prepositions"]:
            prepositions_fat = self.options[track]["cwp_prepositions"].split(
                ',')
            prepositions = [w.strip() for w in prepositions_fat]
            for i, ti_bit_test in enumerate(
                    reversed(ti_test_list)):  # Need to reverse it to check later prepositions first
                if ti_bit_test.lower().strip() in prepositions:
                    # NB i is counting up while traversing the list backwards
                    j = len(ti_rich_list) - i - 1
                    if i == 0 or not ti_rich_list[j + 1][1]:
                        # Don't make it false if it is preceded by a
                        # non-preposition new word
                        if not (j > 0 and ti_rich_list[j -
                                                       1][1] and ti_test_list[j -
                                                                              1].lower() not in prepositions):
                            ti_rich_list[j] = (ti_rich_list[j][0], False)

        # create comparison for later usage
        compare_string = ''
        for item in ti_rich_list:
            if item[1]:
                compare_string += item[0][0]
        ti_compare = self.boil(release_id, compare_string)
        compare_length = len(ti_compare)

        write_log(
                release_id,
                'info',
                "ti_rich_list before gapping (True indicates a word in title not in MB work) = %s. length = %s",
                ti_rich_list,
                len(ti_rich_list))
        if s > 0:
            d = p - ep
            start = True  # To keep track of new words at the start of the title
            for i, (ti_bit, new) in enumerate(ti_rich_list):
                if not new:
                    write_log(
                            release_id,
                            'info',
                            "item(i = %s) val = %s - not new. proximity param = %s, end_proximity param = %s",
                            i,
                            ti_bit,
                            p,
                            ep)
                    if start:
                        prox_test = ep
                    else:
                        prox_test = p
                    if prox_test > 0:
                        for j in range(0, prox_test + 1):
                            write_log(release_id, 'info', "item(i) = %s, look-ahead(j) = %s", i, j)
                            if i + j < len(ti_rich_list):
                                if ti_rich_list[i + j][1]:
                                    write_log(
                                            release_id, 'info', "Set to true..")
                                    ti_rich_list[i] = (ti_bit, True)
                                    write_log(
                                            release_id, 'info', "...set OK")
                            else:
                                if j <= p - d:
                                    ti_rich_list[i] = (ti_bit, True)
                else:
                    p = self.options[track]["cwp_proximity"]
                    start = False
                if not ti_rich_list[i][1]:
                    p -= 1
                    ep -= 1
        write_log(
                release_id,
                'info',
                "ti_rich_list after gapping (True indicates new words plus infills) = %s",
                ti_rich_list)
        nothing_new = True
        for (ti_bit, new) in ti_rich_list:
            if new:
                nothing_new = False
                new_prev = True
                break
        if nothing_new:
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    None)
            return None
        else:
            new_prev = False
            for i, (ti_bit, new) in enumerate(ti_rich_list):
                write_log(release_id, 'info', "Create new for %s?", ti_bit)
                if new:
                    write_log(release_id, 'info', "Yes for %s", ti_bit)
                    if not new_prev:
                        if i > 0:
                            # check to see if the last char of the prev
                            # punctuation group needs to be added first
                            if len(ti_rich_list[i - 1][0][1]) > 1:
                                # i.e. ti_bit[1][-1] of previous loop
                                ti_new.append(ti_rich_list[i - 1][0][1][-1])
                    ti_new.append(ti_bit[0])
                    if len(ti_bit[1]) > 1:
                        if i < len(ti_rich_list) - 1:
                            if ti_rich_list[i + 1][1]:
                                ti_new.append(ti_bit[1])
                            else:
                                ti_new.append(ti_bit[1][:-1])
                        else:
                            ti_new.append(ti_bit[1])
                    else:
                        ti_new.append(ti_bit[1])
                    write_log(
                            release_id,
                            'info',
                            "appended %s. ti_new is now %s",
                            ti_bit,
                            ti_new)
                else:
                    write_log(release_id, 'info', "Not for %s", ti_bit)
                    if new != new_prev:
                        ti_new.append(u"\u2026" + ' ')

                new_prev = new
        if ti_new:
            write_log(release_id, 'info', "ti_new %s", ti_new)
            ti = ''.join(ti_new)
            write_log(release_id, 'info', "New text from title = %s", ti)
        else:
            write_log(release_id, 'info', "New text empty")
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    None)
            return None
        # see if there is any significant difference between the strings
        if ti:
            nopunc_ti = ti_compare  # was  = self.boil(release_id, ti)
            # not necessary as already set?
            nopunc_mb = self.boil(release_id, mb)
            # ti_len = len(nopunc_ti) use compare_length instead (= len before
            # removals and additions)
            substring_proportion = float(
                self.options[track]["cwp_substring_match"]) / 100
            sub_len = compare_length * substring_proportion
            if substring_proportion < 1:
                write_log(release_id, 'info', "test sub....")
                lcs = longest_common_substring(nopunc_mb, nopunc_ti)['string']
                write_log(
                        release_id,
                        'info',
                        "Longest common substring is: %s. Threshold length is %s",
                        lcs,
                        sub_len)
                if len(lcs) >= sub_len:
                    write_log(
                            release_id,
                            'info',
                            'End of DIFF_PAIR. Returning %s',
                            None)
                    return None
            write_log(release_id, 'info', "...done, ti =%s", ti)
        # remove duplicate successive words (and remove first word of title
        # item if it duplicates last word of mb item)
        if ti:
            ti_list_new = re.split(' ', ti)
            ti_list_ref = ti_list_new
            ti_bit_prev = None
            for i, ti_bit in enumerate(ti_list_ref):
                if ti_bit != "...":

                    if i > 1:
                        if self.boil(
                                release_id, ti_bit) == self.boil(
                                release_id, ti_bit_prev):
                            dup = ti_list_new.pop(i)
                            write_log(release_id, 'info', "...removed dup %s", dup)

                ti_bit_prev = ti_bit
            if ti_list_new and mb_list2:
                write_log(release_id,
                          'info',
                          "1st word of ti = %s. Last word of mb = %s",
                          ti_list_new[0],
                          mb_list2[-1])
                if self.boil(release_id, ti_list_new[0]) == mb_list2[-1]:
                    write_log(release_id, 'info', "Removing 1st word from ti...")
                    first = ti_list_new.pop(0)
                    write_log(release_id, 'info', "...removed %s", first)
            else:
                write_log(
                        release_id,
                        'info',
                        'End of DIFF_PAIR. Returning %s',
                        None)
                return None
            if ti_list_new:
                ti = ' '.join(ti_list_new)
            else:
                write_log(
                        release_id,
                        'info',
                        'End of DIFF_PAIR. Returning %s',
                        None)
                return None
        # remove excess brackets and punctuation
        if ti:
            ti = strip_excess_punctuation(ti)
            write_log(release_id, 'info', "stripped punc ok. ti = %s", ti)
        write_log(
                release_id,
                'debug',
                "DIFF_PAIR is returning ti = %s",
                ti)
        if ti and len(ti) > 0:
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    ti)
            return ti
        else:
            write_log(
                    release_id,
                    'info',
                    'End of DIFF_PAIR. Returning %s',
                    None)
            return None


    @staticmethod
    def canonize_opus(release_id, track, s):
        """
        make opus numbers etc. into one-word items
        :param release_id:
        :param track:
        :param s: A string
        :return:
        """
        write_log(release_id, 'debug', 'Canonizing: %s', s)
        # Canonize catalogue & opus numbers (e.g. turn K. 126 into K126 or K
        # 345a into K345a or op. 144 into op144):
        regex = re.compile(
            r'\b((?:op|no|k|kk|kv|L|B|Hob|S|D|M)|\w+WV)\W?\s?(\d+\-?\u2013?\u2014?\d*\w*)\b',
            re.IGNORECASE)
        regex_match = regex.search(s)
        s_canon = s
        if regex_match and len(regex_match.groups()) == 2:
            pt1 = regex_match.group(1) or ''
            pt2 = regex_match.group(2) or ''
            if regex_match.group(1) and regex_match.group(2):
                pt1 = re.sub(
                    r'^\W*no\b',
                    '',
                    regex_match.group(1),
                    flags=re.IGNORECASE)
            s_canon = pt1 + pt2
        write_log(release_id, 'info', 'canonized item = %s', s_canon)
        return s_canon

    @staticmethod
    def canonize_key(release_id, track, s):
        """
        make keys into standardized one-word items
        :param release_id:
        :param track:
        :param s: A string
        :return:
        """
        write_log(release_id, 'debug', 'Canonizing: %s', s)
        match = RE_KEYS.search(s)
        s_canon = s
        if match:
            if match.group(2):
                k2 = re.sub(
                    r'\-sharp|\u266F',
                    'sharp',
                    match.group(2),
                    flags=re.IGNORECASE)
                k2 = re.sub(r'\-flat|\u266D', 'flat', k2, flags=re.IGNORECASE)
                k2 = k2.replace('-', '')
            else:
                k2 = ''
            if not match.group(3) or match.group(
                    3).strip() == '':  # if the scale is not given, assume it is the major key
                if match.group(1).isupper(
                ) or k2 != '':  # but only if it is upper case or has an accent
                    k3 = 'major'
                else:
                    k3 = ''
            else:
                k3 = match.group(3).strip()
            s_canon = match.group(1).strip() + k2.strip() + k3
        write_log(release_id, 'info', 'canonized item = %s', s_canon)
        return s_canon

    @staticmethod
    def canonize_synonyms(release_id, tuples, s):
        """
        make synonyms equal
        :param release_id:
        :param tuples
        :param s: A string
        :return:
        """
        write_log(release_id, 'debug', 'Canonizing: %s', s)
        s_canon = s
        syn_patterns = []
        syn_subs = []
        for syn_tup in tuples:
            syn_pattern = r'((?:^|\W)' + \
                r'(?:$|\W)|(?:^|\W)'.join(syn_tup) + r'(?:$|\W))'
            syn_patterns.append(syn_pattern)
            # to get the last synonym in the tuple - the canonical form
            syn_sub = syn_tup[-1:][0]
            syn_subs.append(syn_sub)
        for syn_ind, pattern in enumerate(syn_patterns):
            regex = re.compile(pattern, re.IGNORECASE)
            regex_match = regex.search(s)
            if regex_match:
                test_reg = regex_match.group().strip()
                s_canon = s_canon.replace(test_reg, syn_subs[syn_ind])

        write_log(release_id, 'info', 'canonized item = %s', s_canon)
        return s_canon

    def find_synonyms(self, release_id, track, reg_item):
        """
        extend regex item to include synonyms
        :param release_id:
        :param track:
        :param reg_item: A regex portion
        :return: reg_new: A replacement for reg_item that includes all its synonyms
         (if reg_item matches the last in a synonym tuple)
        """
        write_log(release_id, 'debug', 'Finding synonyms of: %s', reg_item)
        syn_others = []
        syn_all = []
        for syn_tup in self.synonyms[track]:
            # to get the last synonym in the tuple - the canonical form
            syn_last = syn_tup[-1:][0]
            if re.match(r'^\s*' + reg_item + r'\s*$', syn_last, re.IGNORECASE):
                syn_others += syn_tup[:-1]
                syn_all += syn_tup
        if syn_others:
            reg_item = '(?:' + ')|(?:'.join(syn_others) + \
                ')|(?:' + reg_item + ')'

        write_log(release_id, 'info', 'new regex item = %s', reg_item)
        return reg_item, syn_all

    def listify(self, release_id, track, s):
        """
        Turn a string into a list of 'words', where words may also be phrases which
        are then 'canonized' - i.e. turned into equivalents for comparison purposes
        :param release_id:
        :param track:
        :param s: string
        :return: s_tuple: a tuple of all the **match objects** (re words and defined phrases)
                 s_test_tuple: a tuple of the matched and canonized words and phrases (i.e. a tuple of strings, not objects)
        """
        tuples = self.synonyms[track]
        # just list anything that is a synonym (with word boundary markers)
        syn_pattern = '|'.join(
            [r'(?:^|\W|\b)' + x + r'(?:$|\W)' for y in self.synonyms[track] for x in y])
        op = self.find_synonyms(
            release_id,
            track,
            r'(?:op|no|k|kk|kv|L|B|Hob|S|D|M|\w+WV)')
        op_groups = op[0]
        op_all = op[1]
        notes = self.find_synonyms(release_id, track, r'[ABCDEFG]')
        notes_groups = notes[0]
        notes_all = notes[1]
        sharp = self.find_synonyms(release_id, track, r'sharp')
        sharp_groups = sharp[0]
        sharp_all = sharp[1]
        flat = self.find_synonyms(release_id, track, r'flat')
        flat_groups = flat[0]
        flat_all = flat[1]
        major = self.find_synonyms(release_id, track, r'major')
        major_groups = major[0]
        major_all = major[1]
        minor = self.find_synonyms(release_id, track, r'minor')
        minor_groups = minor[0]
        minor_all = minor[1]
        opus_pattern = r"(?:\b((?:(" + op_groups + \
            r"))\W?\s?\d+\-?\u2013?\u2014?\d*\w*)\b)"
        note_pattern = r"(\b" + notes_groups + r")"
        accent_pattern = r"(?:\-(" + sharp_groups + r")(?:\s+|\b)|\-(" + flat_groups + r")(?:\s+|\b)|\s(" + sharp_groups + \
                         r")(?:\s+|\b)|\s(" + flat_groups + r")(?:\s+|\b)|\u266F(?:\s+|\b)|\u266D(?:\s+|\b)|(?:[:,.]?\s+|$|\-))"
        scale_pattern = r"(?:((" + major_groups + \
            r")|(" + minor_groups + r"))?\b)"
        key_pattern = note_pattern + accent_pattern + scale_pattern
        hyphen_split_pattern = r"(?:\b|\"|\')(\w+['’]?\w*)|(?:\b\w+\b)|(\B\&\B)"
        # treat em-dash and en-dash as hyphens
        hyphen_embed_pattern = r"(?:\b|\"|\')(\w+['’\-\u2013\u2014]?\w*)|(?:\b\w+\b)|(\B\&\B)"

        # The regex is split into two iterations as putting it all together can have unpredictable consequences
        # - may match synonyms before op's even though that is later in the string

        # First match the op's and keys
        regex_1 = opus_pattern + r"|(" + key_pattern + r")"
        matches_1 = re.finditer(regex_1, s, re.UNICODE | re.IGNORECASE)
        s_list = []
        s_test_list = []
        s_scrubbed = s
        all_synonyms_lists = [
            op_all,
            notes_all,
            sharp_all,
            flat_all,
            sharp_all,
            flat_all,
            major_all,
            minor_all]
        matches_list = [2, 4, 5, 6, 7, 8, 10, 11]
        for match in matches_1:
            test_a = match.group()
            match_a = []
            match_a.append(match.group())
            for j in range(1, 12):
                match_a.append(match.group(j))
            # 0. overall match
            # 1. overall opus match
            # 2. 2-char op match
            # 3. overall key match
            # 4. note match
            # 5. hyphenated sharp match
            # 6. hyphenated flat match
            # 7. non-hyphenated sharp match
            # 8. non-hyphenated flat match
            # 9. overall scale match
            # 10. major match
            # 11. minor match
            for i, all_synonyms_list in enumerate(all_synonyms_lists):
                if all_synonyms_list and match_a[matches_list[i]]:
                    match_regex = [re.match(pattern, match_a[matches_list[i]], re.IGNORECASE).group()
                                   for pattern in all_synonyms_list
                                   if re.match(pattern, match_a[matches_list[i]], re.IGNORECASE)]
                    if match_regex:
                        match_a[matches_list[i]] = self.canonize_synonyms(
                            release_id, tuples, match_a[matches_list[i]])
                        test_a = re.sub(r"\b" + match_regex[0] + r"(?:\b|$|\s|\.)",
                                        match_a[matches_list[i]],
                                        test_a, flags=re.IGNORECASE)
            if match_a[1]:
                clean_opus = test_a.strip(' ,.:;/-?"')
                test_a = re.sub(
                    re.escape(clean_opus),
                    self.canonize_opus(
                        release_id,
                        track,
                        clean_opus),
                    test_a,
                    flags=re.IGNORECASE)
            if match_a[3]:
                clean_key = test_a.strip(' ,.:;/-?"')
                test_a = re.sub(
                    re.escape(clean_key),
                    self.canonize_key(
                        release_id,
                        track,
                        clean_key),
                    test_a,
                    flags=re.IGNORECASE)

            s_test_list.append(test_a)
            s_list.append(match)
            s_scrubbed_list = list(s_scrubbed)
            for char in range(match.start(), match.end()):
                if len(s_scrubbed_list) >= match.end():  # belt and braces
                    s_scrubbed_list[char] = '#'
            s_scrubbed = ''.join(s_scrubbed_list)

        # Then match the synonyms and remaining words
        if self.options[track]["cwp_split_hyphenated"]:
            regex_2 = r"(" + syn_pattern + r")|" + hyphen_split_pattern
            # allow ampersands and non-latin characters as word characters. Treat apostrophes as part of words.
            # Treat opus and catalogue entries - e.g. K. 657 or OP.5 or op. 35a or CD 144 or BWV 243a - as one word
            # also treat ranges of opus numbers (connected by dash, en dash or
            # em dash) as one word
        else:
            regex_2 = r"(" + syn_pattern + r")|" + hyphen_embed_pattern
            # as previous but also treat embedded hyphens as part of words.
        matches_2 = re.finditer(
            regex_2, s_scrubbed, re.UNICODE | re.IGNORECASE)
        for match in matches_2:
            if match.group(1) and match.group(1) == match.group():
                s_test_list.append(
                    self.canonize_synonyms(
                        release_id,
                        tuples,
                        match.group(1)))  # synonym
            else:
                s_test_list.append(match.group())
            s_list.append(match)
        if s_list:
            s_zip = list(zip(s_list, s_test_list))
            s_list, s_test_list = zip(
                *sorted(s_zip, key=lambda tup: tup[0].start()))
        s_tuple = tuple(s_list)
        s_test_tuple = tuple(s_test_list)
        return {'s_tuple': s_tuple, 's_test_tuple': s_test_tuple}

    def get_text_tuples(self, release_id, track, text_type):
        """
        Return synonym or 'replacement' tuples
        :param release_id:
        :param track:
        :param text_type: 'replacements' or 'synonyms'
        Note that code in this method refers to synonyms (as that was written first), but applies equally to replacements and ui_tags
        :return:
        """
        tm = track.metadata
        strsyns = re.split(r'(?<!\\)/',
                           self.options[track]["cwp_" + text_type])
        synonyms = []
        for syn in strsyns:
            tup_match = re.search(r'\((.*)\)', syn)
            if tup_match:
                # to ignore escaped commas
                tup = re.split(r'(?<!\\),', tup_match.group(1))
            else:
                tup = ''
            if len(tup) >= 2:
                for i, ts in enumerate(tup):
                    tup[i] = ts.strip("' ").strip('"')
                    if len(
                            tup[i]) > 4 and tup[i][0] == "!" and tup[i][1] == "!" and tup[i][-1] == "!" and tup[i][-2] == "!":
                        # we have a reg ex inside - this deals with legacy
                        # replacement text where enclosure in double-shouts was
                        # required
                        tup[i] = tup[i][2:-2]
                    if (i < len(tup) - 1 or text_type ==
                            'synonyms') and not tup[i]:
                        write_log(
                            release_id,
                            'warning',
                            '%s: entries must not be blank - error in %s',
                            text_type,
                            syn)
                        if self.WARNING:
                            self.append_tag(
                            release_id,
                            tm,
                            '~cwp_warning',
                            '7. ' + text_type + ': entries must not be blank - error in ' + syn)
                        tup[i] = "**BAD**"
                    elif [tup for t in synonyms if tup[i] in t]:
                        write_log(
                            release_id,
                            'warning',
                            '%s: keys cannot duplicate any in existing %s - error in %s '
                            '- omitted from %s. To fix, place all %s in one tuple.',
                            text_type,
                            text_type,
                            syn,
                            text_type,
                            text_type)
                        if self.WARNING:
                            self.append_tag(release_id, tm, '~cwp_warning',
                                        '7. ' + text_type + ': keys cannot duplicate any in existing ' + text_type + ' - error in ' +
                                        syn + ' - omitted from ' + text_type + '. To fix, place all ' + text_type + ' in one tuple.')
                        tup[i] = "**BAD**"
                if "**BAD**" in tup:
                    continue
                else:
                    synonyms.append(tup)
            else:
                write_log(
                    release_id,
                    'warning',
                    'Error in %s format for %s',
                    text_type,
                    syn)
                if self.WARNING:
                    self.append_tag(
                    release_id,
                    tm,
                    '~cwp_warning',
                    '7. Error in ' +
                    text_type +
                    ' format for ' +
                    syn)
        write_log(release_id, 'info', "%s: %s", text_type, synonyms)
        return synonyms

    @staticmethod
    def stencil(release_id, matches_tuple, test_string):
        """
        Produce lists of matching items, AND the items in between, in equal length lists
        :param release_id:
        :param matches_tuple: tuple of regex matches
        :param test_string: original string used in regex
        :return: 'match list' - list of matched strings, 'gap list' - list of strings in gaps between matches
        """
        match_items = []
        gap_items = []
        dummy = False
        pointer = 0
        write_log(
                release_id,
                'debug',
                'In fn stencil. test_string = %s. matches_tuple = %s',
                test_string,
                matches_tuple)
        for match_num, match in enumerate(matches_tuple):
            start = match.start()
            end = match.end()
            if start > pointer:
                if pointer == 0:
                    # add a null word item at start to keep the lists the same
                    # length
                    match_items.append('')
                    dummy = True
                gap_items.append(test_string[pointer:start])
            else:
                if pointer > 0:
                    # shouldn't happen, but just in case there are two word
                    # items with no gap
                    gap_items.append('')
            match_items.append(test_string[start:end])
            pointer = end
            if match_num + 1 == len(matches_tuple):
                # pick up any punc items at end
                gap_items.append(test_string[pointer:])
        return {
            'match list': match_items,
            'gap list': gap_items,
            'dummy': dummy}

    def boil(self, release_id, s):
        """
        Remove punctuation, spaces, capitals and accents for string comparisons
        :param release_id: name for log file - usually =musicbrainz_albumid
        unless called outside metadata processor
        :param s:
        :return:
        """
        write_log(release_id, 'debug', "boiling %s", s)
        s = s.lower()
        s = replace_roman_numerals(s)
        s = s.replace('sch', 'sh')\
            .replace(u'\xdf', 'ss')\
            .replace('sz', 'ss')\
            .replace(u'\u0153', 'oe')\
            .replace('oe', 'o')\
            .replace(u'\u00fc', 'ue')\
            .replace('ue', 'u')\
            .replace(u'\u00e6', 'ae')\
            .replace('ae', 'a')\
            .replace(u'\u266F', 'sharp')\
            .replace(u'\u266D', 'flat')\
            .replace(u'\u2013', '-')\
            .replace(u'\u2014', '-')
        # first term above is to remove the markers used for synonyms, to
        # enable a true comparison
        punc = re.compile(r'\W*', re.ASCII)
        s = ''.join(
            c for c in unicodedata.normalize(
                'NFD',
                s) if unicodedata.category(c) != 'Mn')
        boiled = punc.sub('', s).strip().lower().rstrip("s'")
        write_log(release_id, 'debug', "boiled result = %s", boiled)
        return boiled


################
# OPTIONS PAGE #
################

class ClassicalExtrasOptionsPage(OptionsPage):
    NAME = "classical_extras"
    TITLE = "Classical Extras"
    PARENT = "plugins"
    HELP_URL = "http://music.highmossergate.co.uk/symphony/tagging/classical-extras/"
    opts = plugin_options('artists') + plugin_options('tag') + plugin_options('tag_detail') +\
        plugin_options('workparts') + plugin_options('genres') + plugin_options('other')

    options = [
        IntOption("persist", 'ce_tab', 0)
    ]
    # custom logging for non-album-related messages is written to session.log
    for opt in opts:
        if 'type' in opt:
            if 'default' in opt:
                default = opt['default']
            else:
                default = ""
            if opt['type'] == 'Boolean':
                options.append(BoolOption("setting", opt['option'], default))
            elif opt['type'] == 'Text' or opt['type'] == 'Combo' or opt['type'] == 'PlainText':
                options.append(TextOption("setting", opt['option'], default))
            elif opt['type'] == 'Integer':
                options.append(IntOption("setting", opt['option'], default))
            else:
                write_log(
                    "session",
                    'error',
                    "Error in setting options for option = %s",
                    opt['option'])

    def __init__(self, parent=None):
        super(ClassicalExtrasOptionsPage, self).__init__(parent)
        self.ui = Ui_ClassicalExtrasOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        """
        Load the options - NB all options are set in plugin_options, so this just parses that
        :return:
        """
        opts = plugin_options('artists') + plugin_options('tag') + plugin_options('tag_detail') +\
            plugin_options('workparts') + plugin_options('genres') + plugin_options('other')

        # To force a toggle so that signal given
        toggle_list = ['use_cwp',
                       'use_cea',
                       'cea_override',
                       'cwp_override',
                       'cea_ra_use',
                       'cea_split_lyrics',
                       'cwp_partial',
                       'cwp_arrangements',
                       'cwp_medley',
                       'cwp_use_muso_refdb',
                       'ce_show_ui_tags',]

        # open at last used tab
        if 'ce_tab' in config.persist:
            cfg_val = config.persist['ce_tab'] or 0
            if 0 <= cfg_val <= 5:
                self.ui.tabWidget.setCurrentIndex(cfg_val)
        else:
            self.ui.tabWidget.setCurrentIndex(0)

        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
            else:
                ui_name = opt['option']
            if ui_name in toggle_list:
                not_setting = not self.config.setting[opt['option']]
                self.ui.__dict__[ui_name].setChecked(not_setting)

            if opt['type'] == 'Boolean':
                self.ui.__dict__[ui_name].setChecked(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Text':
                self.ui.__dict__[ui_name].setText(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'PlainText':
                self.ui.__dict__[ui_name].setPlainText(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Combo':
                self.ui.__dict__[ui_name].setEditText(
                    self.config.setting[opt['option']])
            elif opt['type'] == 'Integer':
                self.ui.__dict__[ui_name].setValue(
                    self.config.setting[opt['option']])
            else:
                write_log(
                    'session',
                    'error',
                    "Error in loading options for option = %s",
                    opt['option'])

    def save(self):
        opts = plugin_options('artists') + plugin_options('tag') + plugin_options('tag_detail') +\
            plugin_options('workparts') + plugin_options('genres') + plugin_options('other')

        # save tab setting
        config.persist['ce_tab'] = self.ui.tabWidget.currentIndex()

        for opt in opts:
            if opt['option'] == 'classical_work_parts':
                ui_name = 'use_cwp'
            elif opt['option'] == 'classical_extra_artists':
                ui_name = 'use_cea'
            else:
                ui_name = opt['option']
            if opt['type'] == 'Boolean':
                self.config.setting[opt['option']] = self.ui.__dict__[
                    ui_name].isChecked()
            elif opt['type'] == 'Text':
                self.config.setting[opt['option']] = str(
                    self.ui.__dict__[ui_name].text())
            elif opt['type'] == 'PlainText':
                self.config.setting[opt['option']] = str(
                    self.ui.__dict__[ui_name].toPlainText())
            elif opt['type'] == 'Combo':
                self.config.setting[opt['option']] = str(
                    self.ui.__dict__[ui_name].currentText())
            elif opt['type'] == 'Integer':
                self.config.setting[opt['option']
                                    ] = self.ui.__dict__[ui_name].value()
            else:
                write_log(
                    'session',
                    'error',
                    "Error in saving options for option = %s",
                    opt['option'])


#################
# MAIN ROUTINE  #
#################

# custom logging for non-album-related messages is written to session.log
write_log('session', 'basic', 'Loading ' + PLUGIN_NAME)

# SET UI COLUMNS FOR PICARD RHS
if config.setting['ce_show_ui_tags'] and config.setting['ce_ui_tags']:
    from picard.ui.itemviews import MainPanel
    UI_TAGS = get_ui_tags().items()
    for heading, tag_names in UI_TAGS:
        heading_tag = '~' + heading + '_VAL'
        MainPanel.columns.append((N_(heading), heading_tag))
    write_log('session', 'info', 'UI_TAGS')
    write_log('session', 'info', UI_TAGS)


# set defaults for certain options that MUST be manually changed by the
# user each time they are to be over-ridden
config.setting['use_cache'] = True
config.setting['ce_options_overwrite'] = False
config.setting['track_ars'] = True
config.setting['release_ars'] = True


# REFERENCE DATA
REF_DICT = get_references_from_file(
    'session',
    config.setting['cwp_muso_path'],
    config.setting['cwp_muso_refdb'])
write_log('session', 'info', 'External references (Muso):')
write_log('session', 'info', REF_DICT)
COMPOSER_DICT = REF_DICT['composers']
if config.setting['cwp_muso_classical'] and not COMPOSER_DICT:
    write_log('session', 'error', 'No composer roster found')
for cd in COMPOSER_DICT:
    cd['lc_name'] = [c.lower() for c in cd['name']]
    cd['lc_sort'] = [c.lower() for c in cd['sort']]
PERIOD_DICT = REF_DICT['periods']
if (config.setting['cwp_muso_dates']
        or config.setting['cwp_muso_periods']) and not PERIOD_DICT:
    write_log('session', 'error', 'No period map found')
GENRE_DICT = REF_DICT['genres']
if config.setting['cwp_muso_genres'] and not GENRE_DICT:
    write_log('session', 'error', 'No classical genre list found')

# API CALLS
register_track_metadata_processor(PartLevels().add_work_info)
register_track_metadata_processor(ExtraArtists().add_artist_info)
register_options_page(ClassicalExtrasOptionsPage)

# END
write_log('session', 'basic', 'Finished intialisation')
