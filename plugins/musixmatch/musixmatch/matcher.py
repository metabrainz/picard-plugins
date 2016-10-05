"""
matcher.py
   by Amelie Anglade and Thierry Bertin-Mahieux
      amelie.anglade@gmail.com & tb2332@columbia.edu

Class and functions to use the new musiXmatch API call:
    matcher.track.get
NOTE: as this API call just came out (April 4th, 2011),
we don't know if the matcher will include more search types,
e.g. artists, albums, ... This ignorance influenced the design.

(c) 2011, A. Anglade and T. Bertin-Mahieux

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import util
from track import Track


# matcher.track.get in API
def track(**args):
    """
    Parameters
    * q_track: words to be searched among track titles
    * q_artist: words to be searched among artist names
    Note
       if no track is found, it returns mxm error 404
       that we don't catch
    Return
       one track, the best match according to musiXmatch
    """
    # sanity check
    valid_params = ('q_track', 'q_artist', 'apikey')
    for k in args.keys():
        if not k in valid_params:
            errmsg = 'Invalid matcher.track param: ' + str(k)
            raise util.MusixMatchAPIError(-1, errmsg)
    # good, let's call
    params = dict((k, v) for k, v in args.iteritems() if not v is None)
    body = util.call('matcher.track.get', params)
    t = Track(-1, trackdata=body["track"])
    return t
