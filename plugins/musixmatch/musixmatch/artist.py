"""
artist.py
   by Amelie Anglade and Thierry Bertin-Mahieux
      amelie.anglade@gmail.com & tb2332@columbia.edu

Class and functions to query MusixMatch regarding an artist.

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


class Artist(object):
	"""
	Class to query the musixmatch API artists
	If the class is constructed with a MusixMatch ID (default),
	we assume the ID exists.
	The constructor can find the track from a musicbrainz ID.
	Then, one can search for charts.
	"""

	#artist.get in API
	def __init__(self, artist_id, musicbrainz=False,
		     artistdata=None):
		"""
		Create an Artist object based on a given ID.
		If musicbrainz is True, search for the song.
		Takes a musixmatch ID (if musicbrainz is False) or musicbrainz id
		Raises an exception if the track is not found.
		INPUT
		   artist_id     - artist id (from whatever service)
		   musicbrainz  - set to True if artist_id from musicbrainz
		   artistdata    - if you already have the information about
		                  the artist (after a search), bypass API call
		"""
		if artistdata is None:
			if musicbrainz:
				params = {'musicbrainz_id': artist_id}
			else:
				params = {'artist_id': artist_id}
			# url call
			body = util.call('artist.get', params)
			artistdata = body['artist']
		# save result
		for k in artistdata.keys():
			self.__setattr__(k, artistdata[k])

	def __str__(self):
		""" pretty printout """
		return 'MusixMatch Artist: ' + str(self.__dict__)


#artist.search in API
def search(**args):
	"""
	Parameters:
	q: a string that will be searched in every data field
	   (q_track, q_artist, q_lyrics)
	q_track: words to be searched among track titles
	q_artist: words to be searched among artist names
	q_lyrics: words to be searched into the lyrics
	page: requested page of results
	page_size: desired number of items per result page
	f_has_lyrics: exclude tracks without an available lyrics
	              (automatic if q_lyrics is set)
	f_artist_id: filter the results by the artist_id
	f_artist_mbid: filter the results by the artist_mbid
	"""
	artist_list = list()
	params = dict((k, v) for k, v in args.iteritems() if not v is None)
	body = util.call('artist.search', params)
	artist_list_dict = body["artist_list"]
	for artist_dict in artist_list_dict:
		t = Artist(-1, artistdata=artist_dict["artist"])
		artist_list.append(t)
	return artist_list


#artist.chart.get in API
def chart(**args):
	"""
	Parameters:
	page: requested page of results
	page_size: desired number of items per result page
	country: the country code of the desired country chart
	"""
	artist_list = list()
	params = dict((k, v) for k, v in args.iteritems() if not v is None)
	body = util.call('artist.chart.get', params)
	artist_list_dict = body["artist_list"]
	for artist_dict in artist_list_dict:
		t = Artist(-1, artistdata=artist_dict["artist"])
		artist_list.append(t)
	return artist_list
