# Standardized Album Artist
## Revision History

### v0.3 - 2017-06-08 (rdswift)
- Provide information as variables rather than tags.

- Provide both ***standardized*** and ***credited*** artist information.  The same information is provided regardless of Picard's 'Use standardized artist name' option setting.


### v0.2 - 2017-06-01 (rdswift)
- Complete rewrite to utilize the album metadata processor rather than the track metadata processor

- Eliminate all extra calls to the ws service by using the information already available in the album xml parameter.


### v0.1 - 2017-05-31 (rdswift)
- Initial version based primarily on the 'Album Artist Website' plugin by Sophist, with a few minor tweaks to get the standardized artist name rather than the artist official home page.
