# Plugin “Remove Release Title OST Indicator” for Picard

**Remove Release Title OST Indicator** is a plugin for [MusicBrainz Picard](https://picard.musicbrainz.org/) that removes soundtrack-related information from album titles.

| Original                                                              | Edited                            |
| --------------------------------------------------------------------- | --------------------------------- |
| The Hobbit: An Unexpected Journey: Original Motion Picture Soundtrack | The Hobbit: An Unexpected Journey |
| Snapshot: OST                                                         | Snapshot                          |
| Turbo: Music From the Motion Picture                                  | Turbo                             |
| Into the Breach Soundtrack                                            | Into the Breach                   |

## Features
- Optionally restrict to soundtracks (releasetype). Enabled by default.
- Removes common soundtrack patterns (e.g., "Soundtrack", "OST", "Score"), even without a separator at the end of the title.
- Supports **custom regex patterns** via the plugin settings.
- **Whitelist support:** Album titles in the whitelist will never be changed (case-insensitive, one title per line).
- **Regex validation:** Regex is checked live in the settings dialog for syntax validity.
- **Multi-step Undo:** Regex and Whitelist fields store the last 5 changes and can be undone stepwise.
- **Test field:** Live preview to see how a title would be changed by current settings.

## Usage
1. Open the plugin settings via `Options > RRemove Release Title OST Indicator`.
2. Adjust the regex pattern if needed (default works for most cases).
3. Decide whether the removal should only apply to releases marked as soundtracks (`releasetype`). This option is enabled by default. If you want to remove soundtrack patterns from all releases, uncheck the box "Only apply to soundtracks (releasetype)".
4. If you have album titles that should never be changed, add them to the whitelist (one per line, case-insensitive).
5. Use the test field to validate results. Changes in the Regex and Whitelist can be undone up to 5 previous steps using the Undo buttons next to each field.
6. Click **OK** to save changes.