# MusicBrainz Picard Plugins

This repository hosts plugins for [MusicBrainz Picard](https://picard.musicbrainz.org/). If you're a plugin author and would like to include your plugin here, simply open a pull request.

Note that new plugins being added to the repository should be under the GNU General Public License version 2 ("GPL") or a license compatible with it. See https://www.gnu.org/licenses/license-list.html for a list of compatible licenses.

## Development Notes

The script `generate.py` will generate a file called `plugins.json`, which contains metadata about all the plugins in this repository. `plugins.json` is used by [picard-website](https://github.com/musicbrainz/picard-website) and Picard itself to display information about downloadable plugins.
