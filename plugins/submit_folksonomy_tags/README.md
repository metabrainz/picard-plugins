# Submit Folksonomy Tags - Picard Plugin

A plugin that lets the user submit tags from their tracks' tags - defaults to `genre` and `mood` - to their respective MusicBrainz pages' folksonomy tags via MusicBrainz Picard. Useful for music geeks who are meticulous with their genre tagging.

**This plugin requires that you log into MusicBrainz via Picard.** The option to do so is in _Options > Options > General_.

To use, right click on a track or release, then go to _Plugins > Submit [x] tags to MusicBrainz_ - there are multiple options depending on if you want to submit tags to the recording, release, release group or release artist associated with the track/s or album/s you've right-clicked. The tags will be applied from the track tags you have configured.

Uses code from rswift's "Submit ISRC" plugin (specifically, the handling of the network response)

## Features
It does what it says on the tin: submits any tags you have in the genre tags of whichever files you drop into Picard to the respective pages. Right now the following entities are supported:

  - recordings
  - releases
  - release groups
  - artists (by release)

The plugin can also replace certain tags if your tags don't match up with MusicBrainz's standard tags, notably with their allowed genre list (e.g. if you use "synthpop" and not "synth-pop", or you use the full name "electronic dance music" and not the abbreviated "edm").

## Limitations
Right now, this plugin only submits tags. No tags are _retrieved_ for comparison yet, meaning I've opted to implement two modes based on how the MusicBrainz API works: maintain the tags that are already saved or overwrite _all_ of your tags. For anyone using the MusicBrainz API, choosing to keep your tags is basically sending the "upvote" attribute with every user tag, and choosing to overwrite doesn't do that, which MusicBrainz will respond by clearing old tags. See the [tags section of the MusicBrainz API for more details.](https://musicbrainz.org/doc/MusicBrainz_API#tags)

Submitting for releases, release artists and release groups will also trigger an alert if your tags are not consistently the same across all tracks in an album. This is to prevent spamming of tags, purposeful or accidental, and is based on the standard already set for years by digital music sites and CD ripper utilities where an album would have the same genres tagged across all tracks.
