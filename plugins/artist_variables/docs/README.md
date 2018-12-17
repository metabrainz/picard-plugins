# Artist Variables \[[Download](https://github.com/rdswift/picard-plugins/raw/2.0_RDS_Plugins/plugins/artist_variables/artist_variables.zip)\]

## Overview

This plugin provides specialized album and track variables for use in naming scripts. It combines the
functionality of the "Album Artist Extension" and "RDS Naming Variables" plugins, although the variables
are provided with different names.  This will require changes to existing scripts when switching from the
previous plugins.

---

## What it Does

This plugin reads the album and track metadata provided to Picard and exposes the information in a number
of additional variables for use in Picard scripts.  The plugin has been designed such that the information
is presented consistently regardless of whether or not the `Use standardized artist names` option is selected.
This means that some of the information available through the standard Picard tags will be duplicated in the
variables provided by this plugin.

***NOTE:*** There are no additional calls to the MusicBrainz website api for additional information.

### Album Variables

* **_PriAArtistID** - The ID of the primary / first album artist listed
* **_PriAArtistStd** - The primary / first album artist listed (standardized)
* **_PriAArtistCred** - The primary / first album artist listed (as credited)
* **_PriAArtistSort** - The primary / first album artist listed (sort name)
* **_AdditionalAArtistID** - The IDs of all album artists listed except for the primary / first artist, separated by a semicolon and space
* **_AdditionalAArtistStd** - All album artists listed (standardized) except for the primary / first artist, separated with strings provided from the release entry
* **_AdditionalAArtistCred** - All album artists listed (as credited) except for the primary / first artist, separated with strings provided from the release entry
* **_FullAArtistStd** - All album artists listed (standardized), separated with strings provided from the release entry
* **_FullAArtistCred** - All album artists listed (as credited), separated with strings provided from the release entry
* **_FullAArtistSort** - All album artists listed (sort names), separated with strings provided from the release entry
* **_FullAArtistPriSort** - The primary / first album artist listed (sort name) followed by all additional album artists (standardized), separated with strings provided from the release entry
* **_AArtistCount** - The number of artists listed as album artists

### Track Variables

* **_PriTArtistID** - The ID of the primary / first track artist listed
* **_PriTArtistStd** - The primary / first track artist listed (standardized)
* **_PriTArtistCred** - The primary / first track artist listed (as credited)
* **_PriTArtistSort** - The primary / first track artist listed (sort name)
* **_AdditionalTArtistID** - The IDs of all track artists listed except for the primary / first artist, separated by a semicolon and space
* **_AdditionalTArtistStd** - All track artists listed (standardized) except for the primary / first artist, separated with strings provided from the track entry
* **_AdditionalTArtistCred** - All track artists listed (as credited) except for the primary / first artist, separated with strings provided from the track entry
* **_FullTArtistStd** - All track artists listed (standardized), separated with strings provided from the track entry
* **_FullTArtistCred** - All track artists listed (as credited), separated with strings provided from the track entry
* **_FullTArtistSort** - All track artists listed (sort names), separated with strings provided from the track entry
* **_FullTArtistPriSort** - The primary / first track artist listed (sort name) followed by all additional track artists (standardized), separated with strings provided from the track entry
* **_TArtistCount** - The number of artists listed as track artists

---

## Examples

The following are some examples using actual information from MusicBrainz:

### Example 1:

Using the single "[Fairytale of New York](https://musicbrainz.org/release/e428018c-5536-47f7-aca7-581e748b6fd5)"
by [Walk Off The Earth](https://musicbrainz.org/artist/e2a5eaeb-7de7-4ffe-a519-e18e427a5060) (credited as
"Gianni and Sarah"), the additional artist variables created are:

* **_PriAArtistID** = e2a5eaeb-7de7-4ffe-a519-e18e427a5060
* **_PriAArtistStd** = Walk Off The Earth
* **_PriAArtistCred** = Gianni and Sarah
* **_PriAArtistSort** = Walk Off The Earth
* **_FullAArtistStd** = Walk Off The Earth
* **_FullAArtistCred** = Gianni and Sarah
* **_FullAArtistSort** = Walk Off The Earth
* **_FullAArtistPriSort** = Walk Off The Earth
* **_AArtistCount** = 1
* **_PriTArtistID** = e2a5eaeb-7de7-4ffe-a519-e18e427a5060
* **_PriTArtistStd** = Walk Off The Earth
* **_PriTArtistCred** = Gianni and Sarah
* **_PriTArtistSort** = Walk Off The Earth
* **_FullTArtistStd** = Walk Off The Earth
* **_FullTArtistCred** = Gianni and Sarah
* **_FullTArtistSort** = Walk Off The Earth
* **_FullTArtistPriSort** = Walk Off The Earth
* **_TArtistCount** = 1

Because there is only one artist associated with this single, the **_AdditionalAArtistID**, **_AdditionalAArtistStd**, 
**_AdditionalAArtistCred**, **_AdditionalTArtistID**, **_AdditionalTArtistStd** and **_AdditionalTArtistCred** variables
are not created.


### Example 2:

Using the single "[Wrecking Ball](https://musicbrainz.org/release/8c759d7a-2ade-4201-abc2-a2a7c1a6ad6c)" by
[Sarah Blackwood](https://musicbrainz.org/artist/af7e5ea9-bd58-4346-8f78-d672e9f297f7),
[Jenni Pleau](https://musicbrainz.org/artist/07fa21a9-c253-4ed0-b711-d63f7965b723) &
[Emily Bones](https://musicbrainz.org/artist/541d331c-f041-4895-b8f2-7db9e27dc5ab), the additional artist variables
created are:

* **_PriAArtistID** = af7e5ea9-bd58-4346-8f78-d672e9f297f7
* **_PriAArtistStd** = Sarah Blackwood
* **_PriAArtistCred** = Sarah Blackwood
* **_PriAArtistSort** = Blackwood, Sarah
* **_AdditionalAArtistID** = 07fa21a9-c253-4ed0-b711-d63f7965b723; 541d331c-f041-4895-b8f2-7db9e27dc5ab
* **_AdditionalAArtistStd** = Jenni Pleau & Emily Bones
* **_AdditionalAArtistCred** = Jenni Pleau & Emily Bones
* **_FullAArtistStd** = Sarah Blackwood, Jenni Pleau & Emily Bones
* **_FullAArtistCred** = Sarah Blackwood, Jenni Pleau & Emily Bones
* **_FullAArtistSort** = Blackwood, Sarah, Pleau, Jenni & Bones, Emily
* **_FullAArtistPriSort** = Blackwood, Sarah, Jenni Pleau & Emily Bones
* **_AArtistCount** = 3
* **_PriTArtistID** = af7e5ea9-bd58-4346-8f78-d672e9f297f7
* **_PriTArtistStd** = Sarah Blackwood
* **_PriTArtistCred** = Sarah Blackwood
* **_PriTArtistSort** = Blackwood, Sarah
* **_AdditionalTArtistID** = 07fa21a9-c253-4ed0-b711-d63f7965b723; 541d331c-f041-4895-b8f2-7db9e27dc5ab
* **_AdditionalTArtistStd** = Jenni Pleau & Emily Bones
* **_AdditionalTArtistCred** = Jenni Pleau & Emily Bones
* **_FullTArtistStd** = Sarah Blackwood, Jenni Pleau & Emily Bones
* **_FullTArtistCred** = Sarah Blackwood, Jenni Pleau & Emily Bones
* **_FullTArtistSort** = Blackwood, Sarah, Pleau, Jenni & Bones, Emily
* **_FullTArtistPriSort** = Blackwood, Sarah, Jenni Pleau & Emily Bones
* **_TArtistCount** = 3

Because there are multiple artists associated with both the album and the track, all artist variables are created.

### Example 3:

Using the album "[Kermit Unpigged](https://musicbrainz.org/release/860fd92f-6899-4b31-a205-d6b746da734e)" by
[The Muppets](https://musicbrainz.org/artist/2ca340a6-e8f2-489d-90c2-f37c5c802d49), the additional artist variables
created for track 4, "[All I Have to Do Is Dream](https://musicbrainz.org/recording/5d98e4d4-be42-4412-94ad-f19562faa416)"
by [Linda Ronstadt](https://musicbrainz.org/artist/498f2581-be21-4eef-8756-fbb89d79b1c0) and
[Kermit the Frog](https://musicbrainz.org/artist/992a7ea8-96c1-4058-ba96-f811c8d01c77), are:


* **_PriAArtistID** = 2ca340a6-e8f2-489d-90c2-f37c5c802d49
* **_PriAArtistStd** = The Muppets
* **_PriAArtistCred** = The Muppets
* **_PriAArtistSort** = Muppets, The
* **_FullAArtistStd** = The Muppets
* **_FullAArtistCred** = The Muppets
* **_FullAArtistSort** = Muppets, The
* **_FullAArtistPriSort** = Muppets, The
* **_AArtistCount** = 1

### Track Variables

* **_PriTArtistID** = 498f2581-be21-4eef-8756-fbb89d79b1c0
* **_PriTArtistStd** = Linda Ronstadt
* **_PriTArtistCred** = Linda Ronstadt
* **_PriTArtistSort** = Ronstadt, Linda
* **_AdditionalTArtistID** = 992a7ea8-96c1-4058-ba96-f811c8d01c77
* **_AdditionalTArtistStd** = Kermit the Frog
* **_AdditionalTArtistCred** = Kermit the Frog
* **_FullTArtistStd** = Linda Ronstadt and Kermit the Frog
* **_FullTArtistCred** = Linda Ronstadt and Kermit the Frog
* **_FullTArtistSort** = Ronstadt, Linda and Kermit the Frog
* **_FullTArtistPriSort** = Ronstadt, Linda and Kermit the Frog
* **_TArtistCount** = 2

Because there is only one artist associated with the album the **_AdditionalAArtistID**, **_AdditionalAArtistStd** and
**_AdditionalAArtistCred** variables are not created.
