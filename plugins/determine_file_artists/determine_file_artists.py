PLUGIN_NAME = "Determine file artists"
PLUGIN_AUTHOR = "Daniel Oaks <daniel@danieloaks.net>"
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "CC0-1.0"
PLUGIN_LICENSE_URL = "https://creativecommons.org/share-your-work/public-domain/cc0/"
PLUGIN_DESCRIPTION = '''Tries to determine all artists, and store them in a way that other tools can read (by separating artists with a semicolon).

This can be used as part of your first pass over new files, but **double-check the results before saving them.** This plugin has to guess what is and isn't an artist's name, and because of that may mangle some values.

Retrieves artist names from:
- Existing `artist` / `artists` tags.
- **ft. SomeArtist** or **feat. SomeArtist** in the title.
- **(SomeArtist cover)** or **(SomeArtist remix)** in the title.

Artist names are split on commas, **`&`**, and the text **"and"**. We also depend on whitespace existing around the separators for safety. Basically we try to split artists from each other (hopefully) without running into too many cases where we unintentionally split a single artist's name into two.

We also ignore artist names like 'acoustic', 'bass boosted', etc. Just in case someone e.g. has **(acoustic cover)** in the title.

Future improvements:
- Split on semicolons as well, to catch cases where artist tag already has split names in it?
- Split by "ft." etc in the artist field as well, because some people put this info into the artist field.
- Match "featuring SomeArtist" as well.
- Match multiple types of brackets. Some people like square brackets!
- Handle artist names that contain semicolons a bit better (can we escape these?).
- Maybe have a popup so users can choose which matchers to allow/not when determining the artists, to allow for different title setups.
- Confirm how we handle titles with multiple matchers, and/or when spaces are missing (e.g. **"Coolest Song Ever (feat.Artist1 + Artist2) (Artist3 Remix)"**
'''

import re

from picard.file import File
from picard.ui.itemviews import BaseAction, register_file_action

# how we split artist names from each other!
# could do " x " as wellbut that's especially risky, so I'll put that in
#  the future improvements basket
artist_splitter = re.compile(r'''(?:\,| \& | \+ | and | vs )''', re.IGNORECASE)

# this is where the magic happens – these regexes extract artist names
#  from the title of each file!
# todo: should we match (Artist1 edit) too?
feat_artist_matcher = re.compile(r'''(?:\(fe?a?t?\. ([^\)]+)\)| f?e?a?t?\. (['"$%^&*#@!?\d\w ]+))''', re.IGNORECASE)
produced_artist_matcher = re.compile(r'''(?:\(prod\. ([^\)]+)\)| prod\. (['"$%^&*#@!?\d\w ]+))''', re.IGNORECASE)
coveremix_artist_matcher = re.compile(r'''\(([^\)]+) (?:cover|remix)\)''', re.IGNORECASE)
title_matchers = (feat_artist_matcher, produced_artist_matcher, coveremix_artist_matcher)

# I don't think this should be necessary... but safety!!!
# we can add more names / types of mixes / etc here to improve the
#  chances the coveremix matcher doesn't catch any incorrect info.
#
# note, I'm adding these with the expectation that we may match
#  for parts like "(X mix)" one day, so these may seem broad now. 
ignored_artist_names = (
    'acapella', 'acoustic', 'album', 'bass boosted', 'bass-boosted',
    'instrumental', 'original', 'remastered', 'vocal', 'vocals'

    # ignore 'dance remix' etc.
    'club', 'dance', 'edm', 'electronic', 'hard', 'hardcore',
    'jazz', 'orchestral', 'techno',
)

class DetermineFileArtists(BaseAction):
    NAME = 'Determine file artists'

    def callback(self, objs):
        for this_file in objs:
            if isinstance(this_file, File):
                # get the list of artist strings to parse through.
                # do the artist and artists fields first, before the
                #  featured artists get added to the end!
                artist_name_strings = []

                for field in ('artist', 'artists'):
                    ans = this_file.metadata.get(field, default='')
                    if ans and ans not in artist_name_strings:
                        artist_name_strings.append(ans)

                # try:
                title = this_file.metadata.get('title', default='')
                for matcher in title_matchers:
                    matches = matcher.search(title)
                    if matches:
                        for match in matches.groups():
                            if match and match.strip():
                                artist_name_strings.append(match.strip())
                # except BaseException as err:
                #     this_file.metadata.set('err', str(err))

                # extract artists!!
                artists = []
                for ans in artist_name_strings:
                    for new_artist in artist_splitter.split(ans):
                        new_artist = new_artist.strip()
                        if new_artist and new_artist not in artists and new_artist.lower() not in ignored_artist_names:
                            artists.append(new_artist)

                # set new artist field
                if artists:
                    this_file.metadata.delete('artists')
                    this_file.metadata.set('artist', ';'.join(artists))

register_file_action(DetermineFileArtists())
