# tango.info plugin for MusicBrainz Picard
Automatically get *genre, date and singers* from **tango.info**, right inside of MusicBrainz Picard.

## Usage
Then open Picard, navigate to `Options -> Options -> Plugins` and enable
the one called `Tango.info Adapter`, then restart and use Picard
like you usually would.

If(and **only if**) there is a valid `barcode` tag for your files, the plugin
will try to look up the corresponding album on *tango.info* and fill in the
`genre`(capitalized), `vocal`(for Singers) and `date` tags for you.

## How it works
The plugin looks up the barcode of an album, constructs the url for the corresponding
*tango.info* album('product'/'TINP') page, parses the HTML, looks for the
`tracks` table and extracts `genre`, `Perf date` and `Vocalist(s)`.

## What is a TINT
See [tango.info wiki: TINT](https://tango.info/wiki/TINT)
`<TINP>-<Side#>-<Track#>`, example: `TINT:00743216335725-1-5`.

[tango.info wiki: TINP](https://tango.info/wiki/TINP) - *Tango Info Number
for a Product* is a 14-digit numeric tango.info code used by tango.info and
others.

## Future
Provided tango.info's [Tobias Conradi](https://tango.info/tangoinfo/eng/contact)
does not change the page structure in a manner that breaks this plugin, you
might be able to map instrumentalists and vocalists to the id3 tags of your
liking, or download cover art. Just construct the respective regex and change a
few lines.

## License: GPLv2
Copyright (C) 2016-2022  **Felix Elsner**, Sambhav Kothari, Philipp Wolfer

With help from **Sophist-UK**, whose albumartist_website plugin, to be found
[here](https://github.com/Sophist-UK/sophist-picard-plugins),
this work heavily draws upon

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
