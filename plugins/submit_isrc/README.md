# Submit ISRC

## Overview

This plugin adds a right click option on an album to submit the ISRCs to the MusicBrainz server specified in the Option settings.

To use this function, you must first match your files to the appropriate tracks for a release.  Once this is done, but before you save your files if you have Picard set to overwrite the `isrc` tag in your files, right-click the release and select "Submit ISRCs" in the "Plugins" section.  For each file that has a single valid ISRC in its metadata, the ISRC will be added to the recording on the release if it does not already exist.  Once all tracks for the release have been processed, the missing ISRCs will be submitted to MusicBrainz.

If a file's metadata contains multiple ISRCs, such as if the file has already been tagged, then no ISRCs will be submitted for that file.

If one of the files contains an invalid ISRC, or if the same ISRC appears in the metadata for two or more files, then a notice will be displayed and the submission process will be aborted.

When ISRCs have been submitted, a notice will be displayed showing whether or not the submission was successful.

---
