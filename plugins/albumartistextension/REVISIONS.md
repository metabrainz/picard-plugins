# AlbumArtist Extension
## Revision History

### v0.6 - 2017-09-13 (rdswift)
- Rewritten to work with Picard 2.0.


### v0.5 - 2017-06-08 (rdswift)
- Use the _albumartists values when creating either the _aaeStd\* or the _aaeCred\* variables depending on the value of the 'Use standardized artist name' setting.

- Use the _albumartists_sort values when creating the _aaeSort\* variables.


### v0.4 - 2017-06-08 (rdswift)
- Simplified outputs as requested during review.  Now provides information for the complete album artist chain and the first (primary) album artist only.

- Set to run at LOW priority to allow other plugins that may alter the AlbumArtist information to complete prior to running.


### v0.3 - 2017-06-07 (rdswift)
- Changed plugin name to AlbumArtist Extension

- Provide information as variables rather than tags.

- Provide ***standardized***, ***credited*** and ***sorted*** artist information.  The same information is provided regardless of Picard's 'Use standardized artist name' option setting.

- Provide count of album artists


### v0.2 - 2017-06-01 (rdswift)
- Complete rewrite to utilize the album metadata processor rather than the track metadata processor

- Eliminate all extra calls to the ws service by using the information already available in the album xml parameter.


### v0.1 - 2017-05-31 (rdswift)
- Initial version based primarily on the 'Album Artist Website' plugin by Sophist, with a few minor tweaks to get the standardized artist name rather than the artist official home page.
