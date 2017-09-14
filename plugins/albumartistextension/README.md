# AlbumArtist Extension
This plugin provides ***standardized***, ***credited*** and ***sorted*** artist information for the album artist.  This is useful when your tagging or renaming scripts require both the standardized artist name and the credited artist name, or more detailed information about the album artists.

## Output
The information is provided in the following variables:

* **\_aaeStdAlbumArtists** = The standardized version of the album artists

* **\_aaeCredAlbumArtists** = The credited version of the album artists

* **\_aaeSortAlbumArtists** = The sorted version of the album artists

* **\_aaeStdPrimaryAlbumArtist** = The standardized version of the first (primary) album artist.

* **\_aaeCredPrimaryAlbumArtist** = The credited version of the first (primary) album artist.

* **\_aaeSortPrimaryAlbumArtist** = The sorted version of the first (primary) album artist.

* **\_aaeAlbumArtistCount** = The number of artists comprising the album artist.

**PLEASE NOTE:** Tagger scripts are required to make use of these hidden variables. Please see the notes on "Usage" below.

## Usage
The following are examples of simple Picard file naming scripts to illustrate the use of the variables provided by this plugin.

### Example 1
File the album in a subdirectory of the standardized name of the first artist listed in the AlbumArtist tag.

    %_aaeStdPrimaryAlbumArtist_0%/%album%/%title%

### Example 2
File the album in a subdirectory of the standardized names of all artists listed in the AlbumArtist tag.  This is similar to using the AlbumArtist tag with the 'Use standardized artist name' option checked in Picard.

    %_aaeStdAlbumArtists%/%album%/%title%

### Example 3
File the album in a subdirectory of the credited name of the first artist listed in the AlbumArtist tag.

    %_aaeCredPrimaryAlbumArtist/%album%/%title%

### Example 4
File the album in a subdirectory of the credited names of all artists listed in the AlbumArtist tag.  This is similar to using the AlbumArtist tag with the 'Use standardized artist name' option unchecked in Picard.

    %_aaeCredAlbumArtists%/%album%/%title%

### Example 5
File the album in a subdirectory of the sort name of the first artist listed in the AlbumArtist tag.

    %_aaeSortPrimaryAlbumArtist/%album%/%title%


### Example 6
File the album in a subdirectory of the sort names of all artists listed in the AlbumArtist tag.  This is similar to using the AlbumArtistSort tag.

    %_aaeStdAlbumArtists%/%album%/%title%

### Example 7
File the album in a custom subdirectory if there are more than two album artists.

    %_aaeCredPrimaryAlbumArtist%$if($gt(%_aae_AlbumArtistCount,2), (et al.))/%album%/%title%

### Example 8
File the album in a subdirectory of the first character of the sort name of the first artist listed in the AlbumArtist tag, filing by the standardized name of the first album artist.

    $upper($firstalphachar(%_aaeSortPrimaryAlbumArtist%,nonalpha="#"))/%_aaeStdPrimaryAlbumArtist%/%album%/%title%

## Technical Notes
This plugin does not require any additional calls to the MusicBrainz servers.  It uses the information already provided with the original call, including items that are subsequently discarded by Picard.

The plugin is registered at a ***priority=LOW*** setting so that it is executed later in the queue, thus allowing any other artist information processing to finish before this processing starts.  This way the most up-to-date values are used by AlbumArtist Extension when creating its output variables.
