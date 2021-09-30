# Search Engine Lookup \[[Download](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/search_engine_lookup.zip)\]

## Overview

This plugin adds a right click option on a cluster, providing the ability to lookup the cluster using a search engine in a browser window.
It also provides a right click option on album and track items in the right-hand Album pane, allowing a search engine lookup for the cover art
associated with the selected album or track.

When you right-click on the cluster, album or track, the lookup option is found under the "Plugins" section of the context list.

## Settings

A settings screen is available in Picard's options settings, under the Plugins section.  This allows the user to select their preferred
search engine provider, and any additional words to provide with the cluster search.  You can also add, edit or remove search engine providers.

![options image](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/options.jpg)

When adding or editing a provider, checkmarks to the right of each field indicate whether or not the information in the field is valid.
The title is valid when it contains at least two non-space characters, does not begin or end with a space, and is not the same as the
title of another existing provider.  The URL is valid when it contains the search replacement parameter ``%search%`` and does not begin
or end with, or contain any spaces.  The "Save" button will be disabled until both fields are valid.

![options edit image](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/search_engine_lookup/options_edit.jpg)

---
