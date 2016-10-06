"""
util.py
   by Amelie Anglade and Thierry Bertin-Mahieux
      amelie.anglade@gmail.com & tb2332@columbia.edu

Edited by m-yn: no urllib2, no Queue, no bisect

Set of util functions used by the MusixMatch Python API,
mostly do HMTL calls.

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
import time
import copy
import urllib
try:
    import json
except ImportError:
    import simplejson as json

# MusixMatch API key, should be an environment variable
MUSIXMATCH_API_KEY = None
if('MUSIXMATCH_API_KEY' in os.environ):
    MUSIXMATCH_API_KEY = os.environ['MUSIXMATCH_API_KEY']

# details of the website to call
API_HOST = 'api.musixmatch.com'
API_SELECTOR = '/ws/1.1/'

# cache time length (seconds)
CACHE_TLENGTH = 3600


class TimedCache():
    """
    Class to cach hashable object for a given time length
    """

    def __init__(self, verbose=0):
        """ contructor, init main dict and priority queue """
        self.stuff = {}
        self.last_cleanup = time.time()
        self.verbose = verbose

    def cache(self, query, res):
        """
        Cache a query with a given result
        Use the occasion to remove one old stuff if needed
        """
        # remove old stuff
        curr_time = time.time()
        if curr_time - self.last_cleanup > CACHE_TLENGTH:
            if self.verbose:
                print 'we cleanup cache'
            new_stuff = {}
            new_stuff.update(filter(
                lambda x: curr_time - x[1][0] < CACHE_TLENGTH,
                self.stuff.items()))
            self.stuff = new_stuff
            self.last_cleanup = curr_time
        # add object to cache (try/except should be useless now)
        try:
            hashcode = hash(query)
            if self.verbose:
                print 'cache, hashcode is:', hashcode
            self.stuff[hashcode] = (time.time(), copy.deepcopy(res))
        except TypeError, e:
            print 'Error, stuff not hashable:', e
            pass

    def query_cache(self, query):
        """
        query the cache for a given query
        Return None if not there or too old
        """
        hashcode = hash(query)
        if self.verbose:
            print 'query_cache, hashcode is:', hashcode
        if hashcode in self.stuff.keys():
            data = self.stuff[hashcode]
            if time.time() - data[0] > CACHE_TLENGTH:
                self.stuff.pop(hashcode)
                return None
            return data[1]
        return None

# instace of the cache
MXMPY_CACHE = TimedCache()


# typical API error message
class MusixMatchAPIError(Exception):
    """
    Error raised when the status code returned by
    the MusixMatch API is not 200
    """

    def __init__(self, code, message=None):
        self.mxm_code = code
        if message is None:
            message = status_code(code)
        self.args = ('MusixMatch API Error %d: %s' % (code, message),)


def call(method, params, nocaching=False):
    """
    Do the GET call to the MusixMatch API
    Paramteres
      method     - string describing the method, e.g. track.get
      params     - dictionary of params, e.g. track_id -> 123
      nocaching  - set to True to disable caching
    """
    for k, v in params.items():
        if isinstance(v, unicode):
            params[k] = v.encode('utf-8')
    # sanity checks
    params['format'] = 'json'
    if not 'apikey' in params.keys() or params['apikey'] is None:
        params['apikey'] = MUSIXMATCH_API_KEY
    if params['apikey'] is None:
        raise MusixMatchAPIError(-1, 'EMPTY API KEY, NOT IN YOUR ENVIRONMENT?')
    params = urllib.urlencode(params)
    # caching
    if not nocaching:
        cached_res = MXMPY_CACHE.query_cache(method + str(params))
        if not cached_res is None:
            return cached_res
    # encode the url request, call
    url = 'http://%s%s%s?%s' % (API_HOST, API_SELECTOR, method, params)
    #print url
    f = urllib.urlopen(url)
    response = f.read()
    # decode response into json
    response = decode_json(response)
    # return body if status is OK
    res_checked = check_status(response)
    # cache
    if not nocaching:
        MXMPY_CACHE.cache(method + str(params), res_checked)
    # done
    return res_checked


def decode_json(raw_json):
    """
    Transform the json into a python dictionary
    or raise a ValueError
    """
    try:
        response_dict = json.loads(raw_json)
    except ValueError:
        raise MusixMatchAPIError(-1, "Unknown error.")
    return response_dict


def check_status(response):
    """
    Checks the response in JSON format
    Raise an error, or returns the body of the message
    RETURN:
       body of the message in JSON
       except if error was raised
    """
    if not 'message' in response.keys():
        raise MusixMatchAPIError(-1)
    msg = response['message']
    if not 'header' in msg.keys():
        raise MusixMatchAPIError(-1)
    header = msg['header']
    if not 'status_code' in header.keys():
        raise MusixMatchAPIError(-1)
    code = header['status_code']
    if code != 200:
        raise MusixMatchAPIError(code)
    # all good, return body
    body = msg['body']
    return body


def status_code(value):
    """
    Get a value, i.e. error code as a int.
    Returns an appropriate message.
    """
    if value == 200:
        q = "The request was successful."
        return q
    if value == 400:
        q = "The request had bad syntax or was inherently impossible"
        q += " to be satisfied."
        return q
    if value == 401:
        q = "Authentication failed, probably because of a bad API key."
        return q
    if value == 402:
        q = "A limit was reached, either you exceeded per hour requests"
        q += " limits or your balance is insufficient."
        return q
    if value == 403:
        q = "You are not authorized to perform this operation / the api"
        q += " version you're trying to use has been shut down."
        return q
    if value == 404:
        q = "Requested resource was not found."
        return q
    if value == 405:
        q = "Requested method was not found."
        return q
    # wrong code?
    return "Unknown error code: " + str(value)
