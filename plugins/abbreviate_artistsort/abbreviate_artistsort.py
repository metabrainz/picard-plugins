# -*- coding: utf-8 -*-

# This is the Sort Multivalue Tags plugin for MusicBrainz Picard.
# Copyright (C) 2013 Sophist
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

PLUGIN_NAME = "Abbreviate artist-sort"
PLUGIN_AUTHOR = "Sophist"
PLUGIN_DESCRIPTION = '''Abbreviate Artist-Sort and Album-Artist-Sort Tags.
e.g. "Vivaldi, Antonio" becomes "Vivaldi, A."
This is particularly useful for classical albums that can have a long list of artists.
%artistsort% is abbreviated into %_artistsort_abbrev% and
%albumartistsort% is abbreviated into %_albumartistsort_abbrev%.'''
PLUGIN_VERSION = "0.4"
PLUGIN_API_VERSIONS = ["1.0", "2.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"


from picard import log
from picard.metadata import register_track_metadata_processor

# The algorithm for this is complicated because the tags can contain multiple names separated by various characters
# As an example from http://musicbrainz.org/release/6c0cfb20-2606-46c1-9306-ee5e7cb5bfdf
#   Sorted:   Vivaldi, Antonio, Caldara, Antonio; Queyras, Jean-Guihen, Kallweit, Georg, Akademie für Alte Musik Berlin
#   Unsorted: Antonio Vivaldi, Antonio Caldara; Jean-Guihen Queyras, Georg Kallweit, Akademie für Alte Musik Berlin
# As you can see, in unsorted, names are separated by ',' as well as ';' but could be e.g. 'feat:'
# The only known is that in sorted, surname is separated from forename(s) by a ','
# It is further complicated by non-latin (e.g. japanese) script artist names
#   where unsorted is in local script, but sorted can be in latin, and names can be in local locale or general.

# If the names are just reversed, and we shift Unsorted to the right by one character (for the ',' in sorted),
# then the punctuation should start to match up:
#   Sorted:   Vivaldi, Antonio, Caldara, Antonio; Queyras, Jean-Guihen, Kallweit, Georg, Akademie für Alte Musik Berlin
#   Unsorted:  Antonio Vivaldi, Antonio Caldara; Jean-Guihen Queyras, Georg Kallweit, Akademie für Alte Musik Berlin
#                             ^
# Of course if we have non-latin or locale names, alignment could be way off:
#   Sorted: Verdi, Giuseppe, Vivaldi, Antonio
#   Unsorted: Joe Green, Antonio Vivaldi

# In the absence of an array version of the tags (PR pending)
# we need to process the tag and sorted tag together in a special way as follows:
#
# 1. Look for the first ',' in sorted and tentatively set surname to the string up to that point.
#   Case a. Sorted:   Stuff, ...
#           Unsorted: Stuff, ...
#   Case b. Sorted:   Surname, Forename(s)...
#           Unsorted: Forename(s) Surname...
#     Special case: Sorted:   Major, Major...
#                   Unsorted: Major Major...
#   Case c. Sorted:   Stuff; Surname, Forename(s)...
#           Unsorted: Stuff; Forename(s) Surname...
#   Case d. Sorted:   Latin Surname, Latin Forename(s)...
#           Unsorted: Foreign...
#   Case e. Sorted:   Beatles, The...
#           Unsorted: The Beatles...
# 2. Locate surname in unsorted:
#   Case a. unsorted starts with surname - move both to new strings
#   Case b. surname can be found in unsorted - forename(s) are what is before and match beginning of rest
#   Case c. If first word is same in sorted and unsorted, move words that match to new strings, then treat as b.
#   Case d. Try to handle without abbreviating and get to next name which might not be foreign

_abbreviate_tags = [
    ('albumartistsort', 'albumartist', '~albumartistsort_abbrev'),
    ('artistsort', 'artist', '~artistsort_abbrev'),
]
_prefixes = ["A", "The"]
_split = ", "
_abbreviate_cache = {}


def abbreviate_artistsort(tagger, metadata, track, release):

    for sortTag, unsortTag, sortTagNew in _abbreviate_tags:
        if not (sortTag in metadata and unsortTag in metadata):
            continue

        sorts = list(metadata.getall(sortTag))
        unsorts = list(metadata.getall(unsortTag))
        for i in range(0, min(len(sorts), len(unsorts))):
            sort = sorts[i]
            log.debug("%s: Trying to abbreviate '%s'." % (PLUGIN_NAME, sort))
            if sort in _abbreviate_cache:
                log.debug("  Using abbreviation found in cache: '%s'." % (_abbreviate_cache[sort]))
                sorts[i] = _abbreviate_cache[sort]
                continue
            unsort = unsorts[i]
            new_sort = ""
            new_unsort = ""

            while len(sort) > 0 and len(unsort) > 0:

                if not _split in sort:
                    log.debug("  Ending without separator '%s' - moving '%s'." % (_split, sort))
                    new_sort += sort
                    new_unsort += unsort
                    sort = unsort = ""
                    continue

                surname, rest = sort.split(_split, 1)
                if rest == "":
                    log.debug("  Ending with separator '%s' - moving '%s'." % (_split, surname))
                    new_sort += sort
                    new_unsort += unsort
                    sort = unsort = ""
                    continue

                # Move leading whitespace
                new_unsort += unsort[0:len(unsort) - len(unsort.lstrip())]
                unsort = unsort.lstrip()

                # Sorted:   Stuff, ...
                # Unsorted: Stuff, ...
                temp = surname + _split
                l = len(temp)
                if unsort[:l] == temp:
                    log.debug("  No forename - moving '%s'." % (surname))
                    new_sort += temp
                    new_unsort += temp
                    sort = sort[l:]
                    unsort = unsort[l:]
                    continue

                # Sorted:   Stuff; Surname, Forename(s)...
                # Unsorted: Stuff; Forename(s) Surname...
                # Move matching words plus white-space one by one
                if unsort.find(' ' + surname) == -1:
                    while surname.split(None, 1)[0] == unsort.split(None, 1)[0]:
                        x = unsort.split(None, 1)[0]
                        log.debug("  Moving matching word '%s'." % (x))
                        new_sort += x
                        new_unsort += x
                        surname = surname[len(x):]
                        unsort = unsort[len(x):]
                        new_sort += surname[0:len(surname) - len(surname.lstrip())]
                        surname = surname.lstrip()
                        new_unsort += unsort[0:len(unsort) - len(unsort.lstrip())]
                        unsort = unsort.lstrip()

                # If we still can't find surname then we are up a creek...
                pos = unsort.find(' ' + surname)
                if pos == -1:
                    log.debug(
                        _("%s: Track %s: Unable to abbreviate surname '%s' - not matched in unsorted %s: '%s'."),
                        PLUGIN_NAME,
                        metadata['tracknumber'],
                        surname,
                        unsortTag,
                        unsort[i],
                    )
                    log.warning("  Could not match surname (%s) in remaining unsorted:" % (surname, unsort))
                    break

                # Sorted:   Surname, Forename(s)...
                # Unsorted: Forename(s) Surname...
                forename = unsort[:pos]
                if rest[:len(forename)] != forename:
                    log.debug(
                        _("%s: Track %s: Unable to abbreviate surname (%s) - forename (%s) not matched in unsorted %s: '%s'."),
                        PLUGIN_NAME,
                        metadata['tracknumber'],
                        surname,
                        forename,
                        unsortTag,
                        unsort[i],
                    )
                    log.warning("  Could not match forename (%s) for surname (%s) in remaining unsorted (%s):" % (forename, surname, unsort))
                    break

                inits = ' '.join([x[0] + '.' for x in forename.split()])

                # Sorted:   Beatles, The...
                # Unsorted: The Beatles...
                if forename in _prefixes:
                    inits = forename

                new_sort += surname + _split + inits
                sort = rest[len(forename):]
                new_sort += sort[0:len(sort) - len(sort[1:].lstrip())]
                sort = sort[1:].lstrip()
                new_unsort += forename
                unsort = unsort[len(forename):]
                new_unsort += unsort[0:len(unsort) - len(unsort.lstrip())]
                unsort = unsort.lstrip()
                new_unsort += surname
                unsort = unsort[len(surname):]
                new_unsort += unsort[0:len(unsort) - len(unsort[1:].lstrip())]
                unsort = unsort[1:].lstrip()

                if forename != inits:
                    log.debug(
                        _("%s: Abbreviated surname (%s, %s) to (%s, %s) in '%s'."),
                        PLUGIN_NAME,
                        surname,
                        forename,
                        surname,
                        inits,
                        sortTag,
                    )
                    log.debug("Abbreviated (%s, %s) to (%s, %s)." % (surname, forename, surname, inits))
            else:  # while loop ended without a break i.e. no errors
                if unsorts[i] != new_unsort:
                    log.error(
                        _("%s: Track %s: Logic error - mangled %s from '%s' to '%s'."),
                        PLUGIN_NAME,
                        metadata['tracknumber'],
                        unsortTag,
                        unsorts[i],
                        new_unsort,
                    )
                    log.warning("Error: Unsorted text for %s has changed from '%s' to '%s'!" % (unsortTag, unsorts[i], new_unsort))
                _abbreviate_cache[sorts[i]] = new_sort
                log.debug("  Abbreviated and cached (%s) as (%s)." % (sorts[i], new_sort))
                if sorts[i] != new_sort:
                    log.debug(_("%s: Abbreviated tag '%s' to '%s'."),
                              PLUGIN_NAME,
                              sorts[i],
                              new_sort,
                              )
                    sorts[i] = new_sort
        metadata[sortTagNew] = sorts

register_track_metadata_processor(abbreviate_artistsort)
