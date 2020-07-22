# Search Engine Lookup \[[Download](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/search_engine_lookup.zip)\]

## Overview

This plugin adds a right click option on a cluster, providing the ability to lookup the cluster using a search engine in a browser window.
When you right-click on a cluster, the option is found under the "Plugins" section of the context list.

## Settings

A settings screen is available in Picard's options settings, under the Plugins section.  This allows the user to select their preferred
search engine provider, and any additional words to provide with the search.  You can also add, edit or remove search engine providers.

![options image](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/options.jpg)

When adding or editing a provider, checkmarks to the right of each field indicate whether or not the information in the field is valid.
The title is valid when it contains at least two non-space characters, does not bein or end with a space, and is not the same as the
title of another existing provider.  The URL is valid when it contains the search replacement parameter ``%search%`` and does not begin
or end with, or contain any spaces.  The "Save" button will be disabled until both fields are valid.

![options edit image](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/options_edit.jpg)

---

## Revision History

The following identifies the development history of the plugin, in reverse chronological order.  Each version lists the changes made for that version, along with the author of each change.

### Version 2.0.0

* Redesigned the configuration user interface to allow adding, editing and removing search engine providers. \[rdswift\]

### Version 1.0.0

* Initial release submitted to the Picard Plugins listing.

### Version 0.0.3

* Add option setting to provide additional words to use with the search. \[rdswift\]
* Add pop-up dialog to notify if an error occurred preventing the search. \[rdswift\]

### Version 0.0.2

* Add option settings to select the search engine provider to use. \[rdswift\]

### Version 0.0.1

* Initial testing release. \[rdswift\]

---
