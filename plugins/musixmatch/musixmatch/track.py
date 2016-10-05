"""
track.py
   by Amelie Anglade and Thierry Bertin-Mahieux
      amelie.anglade@gmail.com & tb2332@columbia.edu

Class and functions to query MusixMatch regarding a track
(find the track, get lyrics, chart info, ...)

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


class Track(object):
	"""
	Class to query the musixmatch API tracks
	If the class is constructed with a MusixMatch ID (default),
	we assume the ID exists.
	The constructor can find the track from a musicbrainz ID
	or Echo Nest track ID.
	Then, one can search for lyrics or charts.
	"""

	#track.get in API
	def __init__(self, track_id, musicbrainz=False, echonest=False,
		     trackdata=None):
		"""
		Create a Track object based on a given ID.
		If musicbrainz or echonest is True, search for the song.
		Takes a musixmatch ID (if both musicbrainz and echonest are False)
		or musicbrainz id or echo nest track id
		Raises an exception if the track is not found.
		INPUT
		   track_id     - track id (from whatever service)
		   musicbrainz  - set to True if track_id from musicbrainz
		   echonest     - set to True if track_id from The Echo Nest
		   trackdata    - if you already have the information about
		                  the track (after a search), bypass API call
		"""
		if musicbrainz and echonest:
			msg = 'Creating a Track, only musicbrainz OR echonest can be True.'
			raise ValueError(msg)
		if trackdata is None:
			if musicbrainz:
				# params = {'musicbrainz_id': track_id}
				# amin
				params = {'track_mbid': track_id}
			elif echonest:
				params = {'echonest_track_id': track_id}
			else:
				params = {'track_id': track_id}
			# url call
			body = util.call('track.get', params)
			trackdata = body['track']
		# save result
		for k in trackdata.keys():
			self.__setattr__(k, trackdata[k])

	# track.lyrics.get in the API
	def lyrics(self):
		"""
		Get the lyrics for that track.
		RETURN
		   dictionary containing keys:
		       - 'lyrics_body'   (main data)
		       - 'lyrics_id'
		       - 'lyrics_language'
		       - 'lyrics copyright'
		       - 'pixel_tracking_url'
		       - 'script_tracking_url'
		"""
		body = util.call('track.lyrics.get', {'track_id': self.track_id})
		return body["lyrics"]

	#track.subtitle.get in API
	def subtitles(self):
		"""
		Get subtitles, available for a few songs as of 02/2011
		Returns dictionary.
		"""
		body = util.call('track.subtitle.get', {'track_id': self.track_id})
		return body["subtitle"]

	#track.lyrics.feedback.post
	def feedback(self, feedback):
		"""
		To leave feedback about lyrics for this track.
		PARAMETERS
		'feedback' can be one of:
		* wrong_attribution: the lyrics shown are not by the artist that I selected.
		* bad_characters: there are strange characters and/or words
		                  that are partially scrambled.
		* lines_too_long: the text for each verse is too long!
		* wrong_verses: there are some verses missing from the beginning
		                or at the end.
		* wrong_formatting: the text looks horrible, please fix it!
		"""
		params = {'track_id': self.track_id, 'lyrics_id': self.lyrics_id,
			  'feedback': feedback}
		body = util.call('track.lyrics.feedback.post', params)

	def __str__(self):
		""" pretty printout """
		return 'MusixMatch Track: ' + str(self.__dict__)


#track.search in API
def search(**args):
	"""
	Parameters:
	q: a string that will be searched in every data field
	   (q_track, q_artist, q_lyrics)
	q_track: words to be searched among track titles
	q_artist: words to be searched among artist names
	q_track_artist: words to be searched among track titles or artist names
	q_lyrics: words to be searched into the lyrics
	page: requested page of results
	page_size: desired number of items per result page
	f_has_lyrics: exclude tracks without an available lyrics
	              (automatic if q_lyrics is set)
	f_artist_id: filter the results by the artist_id
	f_artist_mbid: filter the results by the artist_mbid
	quorum_factor: only works together with q and q_track_artist parameter.
	               Possible values goes from 0.1 to 0.9
	               A value of 0.9 means: 'match at least 90 percent of the words'.
	"""
	# sanity check
	valid_params = ('q', 'q_track', 'q_artist', 'q_track_artist', 'q_lyrics',
			'page', 'page_size', 'f_has_lyrics', 'f_artist_id',
			'f_artist_mbid', 'quorum_factor', 'apikey')
	for k in args.keys():
		if not k in valid_params:
			raise util.MusixMatchAPIError(-1, 'Invalid track search param: ' + str(k))
	# call and gather a list of tracks
	track_list = list()
	params = dict((k, v) for k, v in args.iteritems() if not v is None)
	body = util.call('track.search', params)
	track_list_dict = body["track_list"]
	for track_dict in track_list_dict:
		t = Track(-1, trackdata=track_dict["track"])
		track_list.append(t)
	return track_list


#track.chart.get in API
def chart(**args):
	"""
	Parameters:
	page: requested page of results
	page_size: desired number of items per result page
	country: the country code of the desired country chart
	f_has_lyrics: exclude tracks without an available lyrics
	              (automatic if q_lyrics is set)
	"""
	# sanity check
	valid_params = ('page', 'page_size', 'country', 'f_has_lyrics', 'apikey')
	for k in args.keys():
		if not k in valid_params:
			raise util.MusixMatchAPIError(-1, 'Invalid chart param: ' + str(k))
	# do the call and gather track list
	track_list = list()
	params = dict((k, v) for k, v in args.iteritems() if not v is None)
	body = util.call('track.chart.get', params)
	track_list_dict = body["track_list"]
	for track_dict in track_list_dict:
		t = Track(-1, trackdata=track_dict["track"])
		track_list.append(t)
	return track_list
