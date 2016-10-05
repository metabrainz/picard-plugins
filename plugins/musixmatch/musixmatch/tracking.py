"""
tracking.py
   by Amelie Anglade and Thierry Bertin-Mahieux
      amelie.anglade@gmail.com & tb2332@columbia.edu

Functions to get the tracking script onto your page and make your
use of MusixMatch legal.

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
import md5
import urllib


#tracking.url.get in the API
def get_tracking_url(domain, apikey=None):
    """
    Get the base url for the tracking script you need to insert in your
    page to legalize your existent lyrics library.
    Parameters
    * domain: The domain of your site, e.g. www.mylyricswebsite.com
    * apikey: A valid musiXmatch API key (OPTIONAL if in your environment)
    RETURN
      a string representing a url
    """
    params = {'domain': domain}
    if not apikey is None:
        params['apikey'] = apikey
    body = util.call('tracking.url.get', params)
    return body['url']


def rights_clearance(base_url, artistname, trackname, apikey=None):
    """
    This code returns the url for the rights of one song on your domain,
    read below. If apikey is not passed in, we look for it in your
    ENVIRONMENT.
    To compute base_url, see function above: get_tracking_url

    We have implemented a fast and simple method to grant you the legal
    clearance of rights for your site, even before you migrate to a full
    musiXmatch API integration.

    In order to accomplish this and have the lyrics views of your catalog
    accurately tracked you need to insert a script into your page code.
    The script URL is made of three parts:

    * The base url
      You can obtain your base url for each of your existing domains using
      our api Tracking url get
      This operation may be performed just once for the lifetime of your
      implementation, but for security reason we suggest you to run it on
      a daily or monthly basis.
    * The parameters
      To the base URL you need to append the track_name and the artist_name
      of the lyrics as GET parameters.
    * The signature
      The signature: Calculate the md5 of this URL+apikey and add it as
      the 's' parameter
    """
    # apikey
    if apikey is None:
        apikey = os.environ['MUSIXMATCH_API_KEY']
    # quote names
    aname_quote = urllib.quote(artistname.lower())
    tname_quote = urllib.quote(trackname.lower())
    # create url
    url = base_url + '?artist_name=' + aname_quote
    url += '&track_name=' + tname_quote
    # md5 signature
    sig = md5.md5(url + apikey)
    # final url
    return url + '&s=' + sig.hexdigest()
