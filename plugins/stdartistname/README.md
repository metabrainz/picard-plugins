# Standardized Album Artist
This plugin provides ***standardized*** and ***credited*** artist information for the album artist.  This is useful when your tagging or renaming scripts require both the standardized artist name and the credited artist name.


## Output
The information is provided in the following variables:

* **\_saStdAlbumArtists** = The standardized version of album artist(s)

* **\_saCredAlbumArtists** = The credited version of album artist(s)

* **\_saAlbumArtistCount** = The number of artists comprising the album artist.

* **\_saStdAlbumArtists\_n** = The standardized version of the album artists, where **n** is the number of the artist in the list starting at **0**.  If there are two artists in the AlbumArtist tag, then they will be available in the **\_saStdAlbumArtist\_0** and **\_saStdAlbumArtist\_1** variables. 

* **\_saCredAlbumArtists\_n** = The credited version of the album artists, where **n** is the number of the artist in the list starting at **0**.  If there are two artists in the AlbumArtist tag, then they will be available in the **\_saCredAlbumArtist\_0** and **\_saCredAlbumArtist\_1** variables.

* **\_saJoinPhrases\_n** = The phrases used to join the album artists, where **n** is the number of the phrase in the list starting at **0**.  **NOTE:** This variable will not be provided if there is only one artist in the AlbumArtist tag.  The user should check that **\_saAlbumArtistCount** is greater than one before using this variable.

**PLEASE NOTE:** Tagger scripts are required to make use of these hidden variables. Please see the notes on "Usage" below.

## Usage
### Example 1
File the album in a subdirectory of the standardized name of the first artist listed in the AlbumArtist tag.

    Test of the code element

### Example 2
File the album in a subdirectory of the standardized names of all artists listed in the AlbumArtist tag.  This is similar to using the AlbumArtist tag with the 'Use standardized artist name' option checked in Picard.

    Test of the code element

# Technical Notes
This plugin does not require any additional calls to the MusicBrainz servers.  It uses the information already provided with the original call, including items that are subsequently discarded by Picard.

# Updates
v0.4
- Added logic to remove composer name from title
- Improved processing of works with only one part
- Improved logic to deal with parent works which are not completely named (e.g. no opus number in parent, but is in child)
- Improved extended metadata logic

v0.5 
- Get artist-rels as well as work-rels on work lookup and populate "instrument arranger" metadata
- Improved heuristics for extending metadata based on titles
- "Alternative" and "Extra" artist metadata (the former just uses metadata whereas the latter does an XML lookup of the recording)