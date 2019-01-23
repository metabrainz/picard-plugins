# MusicBrainz Picard plugin to add an ~instruments tag.
# Copyright (C) 2019  David Mandelberg
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

PLUGIN_NAME = 'Instruments'
PLUGIN_AUTHOR = 'David Mandelberg'
PLUGIN_DESCRIPTION = """\
  Adds a multi-valued tag of all the instruments (including vocals), for use in
  scripts.
  """
PLUGIN_VERSION = '1.0'
PLUGIN_API_VERSIONS = ['2.0']
PLUGIN_LICENSE = 'GPL-3.0-or-later'
PLUGIN_LICENSE_URL = 'https://www.gnu.org/licenses/gpl-3.0.html'

from typing import Generator, Optional

from picard import metadata
from picard import plugin


def _iterate_instruments(instrument_list: str) -> Generator[str, None, None]:
  """Yields individual instruments from a string listing them.

  Args:
    instrument_list: List of instruments in the form 'A, B and C'.
  """
  remaining = instrument_list
  while remaining:
    instrument, _, remaining = remaining.partition(', ')
    if not remaining:
      instrument, _, remaining = instrument.partition(' and ')
      if ' and ' in remaining:
        raise ValueError('Instrument list contains multiple \'and\'s: {!r}'
                         .format(instrument_list))
    yield instrument


def _strip_instrument_prefixes(instrument: str) -> Optional[str]:
  """Returns the instrument name without qualifying prefixes, or None.

  Args:
    instrument: Potentially prefixed instrument name, e.g., 'solo bassoon'.

  Returns:
    The instrument name with all prefixes stripped, or None if there's nothing
    other than prefixes. The all-prefixes case can happen with relationships
    like 'guest performer'.
  """
  instrument_prefixes = {
      'additional',
      'guest',
      'solo',
  }
  remaining = instrument
  while remaining:
    prefix, sep, remaining = remaining.partition(' ')
    if prefix not in instrument_prefixes:
      return ''.join((prefix, sep, remaining))
  return None


def add_instruments(tagger, metadata_, *args):
  key_prefix = 'performer:'
  instruments = set()
  for key in metadata_.keys():
    if not key.startswith(key_prefix):
      continue
    for instrument in _iterate_instruments(key[len(key_prefix):]):
      instrument = _strip_instrument_prefixes(instrument)
      if instrument:
        instruments.add(instrument)
  metadata_['~instruments'] = list(instruments)


metadata.register_track_metadata_processor(
    add_instruments, priority=plugin.PluginPriority.HIGH)
