# Remove Soundtrack Plugin for Picard

**Remove Soundtrack** is a plugin for [MusicBrainz Picard](https://picard.musicbrainz.org/) that removes soundtrack-related information from album titles.

| Original                                                              | Edited                            |
| --------------------------------------------------------------------- | --------------------------------- |
| The Hobbit: An Unexpected Journey: Original Motion Picture Soundtrack | The Hobbit: An Unexpected Journey |
| Snapshot: OST                                                         | Snapshot                          |
| Turbo: Music From the Motion Picture                                  | Turbo                             |


## Known limitations:

Does not work if there is no clear distinction between the title and soundtrack addition. The example “Broken Sword Shadow of the Templars (Director's Cut) Original Soundtrack” would not be changed.


## Features
- Only works with albums that are specified as soundtracks in the release type (releasetype)
- Removes common soundtrack patterns (e.g., "Soundtrack", "OST", "Score").
- Supports **custom regex patterns** via the plugin settings.
- Includes a **reset-to-default** button for easy recovery.

## Usage
1. Open the plugin settings via `Options > Remove Soundtrack`.
2. Adjust the regex pattern if needed (default works for most cases).
3. Click **OK** to save changes.

## Default Regex
```regex
(\s*(?::|-|–|—|\(|\[)(?:\s*(?:Original|Album|Movie|Motion|Picture|Soundtrack|Score|OST|Music|Edition|Inspired|by|from|the|TV|Series|Video|Game|Film|Show)){1,}(?:\)|\])?){1,}
```