# General Information
This is version 0.8 of "classical_extras". It has only been tested with FLAC and mp3 files. It does work with m4a files, but Picard does not write all m4a tags (see further notes for iTunes users at the end of the "works and parts tab" section).
It populates hidden variables in Picard with information from the MusicBrainz database about the recording, artists and work(s), and of any containing works, passing up through mutiple work-part levels until the top is reached.
The "Options" page (Options->Options->Plugins->Classical Extras) allows the user to determine how these hidden variables are written to file tags, as well as a variety of other options.
This plugin is particularly designed to assist with tagging of classical music so that player or library manager software which can display multiple work levels and different artist types can have access to them.

It has two components "Extra Artists" and "Work Parts" which can be used independently or together. "Work Parts" will take at least as many seconds to process as there are works to look up (owing to MB throttling) so users who only want the extra artist information and not the work details may turn it off.

All hidden variables produced by this plugin are prefixed with "_cwp_" or  "_cea_" depending on which component of the plugin created them. Full details of these variables are given in a later section.
Tags are output depending on the choices specified by the user in the Options Page. Defaults are provided for these tags which can be added to / modified / deleted according to user requirements. 
If the Options Page does not provide sufficient flexibility, users familiar with scripting can write Tagger Scripts to access the hidden variables directly.

## Updates
Version 0.8: Tweak description to improve display.

Version 0.7: Bug fixes. Pull request issued for this version.

Version 0.6.6: Bug fixes and algorithm improvements. Allow multiple sources for a tag (each will be appended) and use + as separator for concantenating sources, not a comma, to distinguish from the use of comma to separate multiples. Provide additional hidden variables ("sources") for vocalists and instrumentalists. Option to include intermediate work levels in a movement tag (for systems which cannot display multiple work levels).

Version 0.6.5: Include ability to use multiple (concatenated) sources in tag mapping (see notes under "tag mapping"). All artist "sources" using hidden variables (_cea_...) are now consistently in the plural, to distinguish from standard tags. Note that if "album" is used as a source in tag mapping, it will now be the revised name, where composer prefixing is used. To use the original name, use "release" as the source. Also various bug fixes, notably to ensure that all arrangers get picked up for use in tag mapping.

Version 0.6.4: Write out version number to user-specified tag. Provide default comment tags for writing ui options. Provide better m4a and iTunes compatibility (see notes). Added functionality for chorus master, orchestrator and concert master (leader). Re-arranged artist tab in ui. Various bug fixes.

Version 0.6.3: Bug fixes. Modified ui default options.

Version 0.6.2: Bug fixes. More flexible handling of artists (can blank and then add back later). Modified ui default options.

Version 0.6.1: Amended regex to permit non-Latin characters in work text.

# Installation
Install the zip file in your plugins folder in the usual fashion

# Usage
After installation, go to the Options Page and modify choices as required. There are 3 tabs - "Artists", "Works and parts" and "Advanced". The sections below describe each of these. If the options provided do not allow sufficient flexibility for a user's need and they do not want to use scripting, then it may be possible to achieve the required result by running and saving twice (or more!) with different options each time. This is not recommended for more than a one-off - a script would be better.

**Important**: 
1.  The plugin **will not work unless** you have enabled "Use release relationships" and "Use track relationships" in Picard->Options->Metadata.
2.  It is recommended only to use the plugin on one release at a time, particularly if the "Works and parts" function is being used. The plugin is not designed to do "bulk tagging" of untagged files - use a tool such as SongKong for that and then use the plugin to enhance the results as required. However, once you have tagged files (either in Picard or, say, SongKong) such that they all have MusicBrainz IDs, you should be able to re-tag multiple releases by dragging the containing folder into Picard; this is useful to pick up changed MusicBrainz data or if you change the Classical Extras version or options (but bear in mind that the "Works and parts" function will still take at least 1 second per track and **make sure you do not have "debug" or "info" logging turned on** - in the "Advanced" tab).
3.  Keep a backup of your picard.ini file (AppData->Roaming->MusicBrainz) in case you erase your settings or Picard crashes and loses them for you.

## Artists tab
There are four coloured sections as shown in the screen image below:

![Artist options](http://i.imgur.com/sKAe38y.jpg)

1. "Create extra artist metadata" should be selected otherwise this section will not run. This is the default.

	"Infer work types (map to genre using tag mapping or script as req'd)". This attempts to create a "work_type" tag based on information in the artist-related tags. It does not (currently) use the "work-type" data associated with MB works as this is not well populated and is under review at present. Values provided are:
	Orchestral, Concerto, Instrumental, Voice, Choral, Opera, Duet, Aria, Song. For concerto, solo and duet performances the instrument is also given where possible. If the track is a recorded work with a composer artist in MusicBrainz and the "Works and parts" section has "Include all work levels" selected, the tag will also include "Classical". Use "work_type" as a source in the tag mapping section below section to (e.g.) map to the genre tag. For more complex treatment, use scripts.

2. "Name album as 'Composer Last Name(s): Album Name'" will add the composer(s) last name(s) before the album name. MB style is to exclude the composer name unless it is actually part of the album name, but it can be useful to add it for library organisation. The default is checked.

	"Fix cyrillic names (where possible and if not fixed by locale settings)" attempts to provide English version of composers, conductors and performers where the script is non-Latin and the relevant locale settings (Options->Metadata) have not fixed this. Note that the standard Picard tags may be amended if this option is chosen (the default).

	"Include arrangers from all work levels, plus instrument arrangers". This will gather together any arranger information from the recording, work or parent works and place it in the "arranger" tag, with a subkey as appropriate. All arrangers (except orchestrators who are dealt with separately) will also be put in the _cea_arrangers hidden variable. If you want to add arrangers as composers, do so in the tag mapping section - see below. (Note that Picard does not natively pick up all arrangers)

	"Annotate chorus master in conductor with ..." will place the specified text in brackets after the chorus master's name in the conductor tag (otherwise Picard will just include the name with any annotation in the MB database).

	"Annotate orchestrator in arranger tag with ..." will place the specified text in brackets after the arranger's name in the arranger tag (otherwise Picard will just include the name with any annotation in the MB database).

	"Include 'concert master' in performer tag as ..." will place the concertmaster's (leader's) name in a tag "performer:text" where the text is specified in the box. Picard does not normally provide this information. the text will be included in backets when the performer tag is written.

	Please note that the use of the word "master" is the MusicBrainz term and is not intended to be gender-specific. Users can specify whatever text they please.

3. "Remove Picard-generated tags before applying subsequent actions?". Any tags specified in the next two rows will be blanked before applying the tag sources described in the following section. NB this applies only to Picard-generated tags, not to other tags which might pre-exist on the file: to blank those, use the main Options->Tags page. Comma-separate the tag names within the rows and note that these names are case-sensitive.

4. "Tag mapping". This section permits the contents of any hidden variable or tag to be written to one or more tags.

    * **Sources**:
	The most useful sources are available from the drop-down list and are as follows:
	Most of the names are for artist data and are sourced from hidden variables (prefixed with "_cea_").
      - soloists : List of performers (with instruments in brackets), who are NOT ensembles or conductors, separated by semi-colons. Note they may not strictly be "soloists" in that they may be part of an ensemble.
      - soloist_names : Names of the above (i.e. no instruments).
      - vocalists / instrumentalists / other_soloists : Soloists who are vocalists, instrumentalists or not specified respectively.
      - vocalist_names / instrumentalist_names : Names of vocalists / instrumentalists (i.e. no instrument / voice).
      - ensembles : List of performers who are ensembles (with type / instruments - e.g. "orchestra" - in brackets), separated by semi-colons.
      - ensemble_names : Names of the above (i.e. no instruments).
      - album_soloists : Sub-list of soloist_names who are also album artists.
      - album_conductors : List of conductors who are also album artists.
      - album_ensembles: Sub-list of ensemble_names who are also album artists.
      - album_composers : List of composers who are also album artists.
      - album_composer_lastnames : Last names of composers of ANY track on the album who are also album artists. This is the source used to prefix the album name (when that option is selected).
      - support_performers : Sub-list of soloist_names who are NOT album artists.
      - composers : Note that, if "Fix cyrillic names" in the last section is checked, this is based on sort name, to avoid non-latin language problems (if translation is not already made via locale choices).
      - conductors : Note that, if "Fix cyrillic names" in the last section is checked, this is based on sort name, to avoid non-latin language problems (if translation is not already made via locale choices).
      - arrangers : Includes all arrangers  and instrument arrangers (except orchestrators) - if option above selected - standard Picard tag omits some.
      - orchestrators : Arrangers who are orchestrators.
      - leaders : AKA "Concertmaster".
      - chorusmasters : as distinct from conductors (chorus masters may rehearse the choir but not conduct the performance).

	  Note that the Classical Extras sources for all artist types are spelled in the plural (to differentiate from the native Picard tags).

	  In addition, the drop-down contains some typical combinations of multiple sources (see note on multiple sources below).

	It is possible to specify multiple sources. If these are separated by a comma, then each will be appended to the mapped tag(s) (if not already filled or if not "conditional"). So, for example, a source of "album_soloists, album_conductors, album_ensembles" mapped to a tag of "artist" with "conditional" ticked will fill artist (if blanked) by album_soloists, if any, otherwise album_conductors etc. Sources separated by a + will be concatenated before being used to fill the mapped tags; separate the desired sources with a + symbol. The concatenated result **will only be applied if the contents of each of the sources to be concatenated is non-blank** (note that this constraint only applies to **concatenation** of multiple sources). No spaces will be added on concatenation, so these have to be added explicitly by concatenating "\ ".
		For example: to add the leader's name in brackets to the tag with the performing orchestra, put "\\(leader ,leaders,\\)" in the source box and the tag containing the orchestra in the tag box. If there is no leader, the text will not be appended.

	The last items in the drop-down list are "work_type" which only has content if the "Infer work types" box in the first coloured section is checked, and "release" which contains the album name before prefixing with composer last names if that option was chosen.

	Any Picard tag names can also be typed in as sources. Hidden variables may also be used. Any source names which are not recognised will be treated as string constants; blanks may also be used.

    * **Tags**:
	Enter the (comma-separated) tag names into which the sources should be written (case sensitive). Note that this will result in the source data being APPENDED in the tag - it will not overwrite the existing contents. Check "Conditional?" if the tag is only to be updated if it is previously blank. The lines will be applied in the order shown. Users should be able to achieve most requirements via a combination of blanking tags, using the right source order and "conditional" flags. For example, to overwrite a tag sourced from "composer" with "conductor", specify "conductor" first, then "composer" as conditional. Note that, for example, to demote the MB-supplied artist to only appear if no other listed choices are present, blank the artist tag and then add it as a conditional source at the end of the list.

	Continuing the "leader" example above, that example places the leader text as an additional performer in the tag (with separating semi-colon). To completely replace the original orchestra name, blank the orchestra tag then re use it with the following source text: "performer:orchestra,\ (leader ,leaders,\\)"

## Work and parts tab

There three coloured sections as shown in the screen print below:
![Works and parts options](http://i.imgur.com/6iXgWFP.jpg)

1. "Include all work levels" should be selected otherwise this section will not run. This is the default.

    "Use cache (if available)" prevents excessive look-ups of the MB database. Every look-up of a parent work needs to be performed separately (hopefully the MB database might make this easier some day). Network usage constraints by MB means that each look-up takes a minimum of 1 second. Once a release has been looked-up, the works are retained in cache, significantly reducing the time required if, say, the options are changed and the data refreshed. However, if the user edits the works in the MB database then the cache will need to be turned off temporarily for the refresh to find the new/changed works.

2. "Tagging style". This section determines how the hierarchy of works will be sourced.

    * **Works source**: There are 3 options for determing the principal source of the works metadata
      - "Use only metadata from title text". The plugin will attempt to extract the hierarchy of works from the track title by looking for repetitions and patterns. If the title does not contain all the work names in the hierarchy then obviously this will limit what can be provided.
      - "Use only metadata from canonical works". The hierarchy in the MB database will be used. Assuming the work is correctly entered in MB, this should provide all the data. However the text may differ from the track titles and will be the same for all recordings. It may also be in the language of the composer whereas the titles will be in the language of the release.
      - "Use canonical work metadata enhanced with title text". This supplements the canonical data with text from the titles **where it is significantly different**. The supplementary data will be in curly brackets. This is clearly the most complete metadata style of the three but may lead to long descriptions. It is particularly useful for providing translations - see image below for an example (using the Muso library manager).

      ![Respighi](http://i.imgur.com/QqulDPG.jpg)

    * **Source of canonical work text**. Where either of the second two options above are chosen, there is a further choice to be made:
      - "Full MusicBrainz work hierarchy". The names of each level of work are used to populate the relevant tags. I.e. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast, JB 1:112", not "Má vlast".
      - "Consistent with lowest level work description (where possible)". The names of the level 0 work are used to populate the relevant tags. I.e. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast", not "Má vlast, JB 1:112". This frequently looks better, but not always, **particularly if the level 0 work name does not contain all the parent work detail**. If selected, this choice will only be implemented where the level 0 work name appears to have the parent work names within it.

**Strategy for setting style:** *It is suggested that you start with "extended/enhanced" style and the "Consistent with lowest level work description" as the source (this is the default). If this does not give acceptable results, try switching to "Full MusicBrainz work hierarchy". If the "enhanced" details in curly brackets (from the track title) give odd results then switch the style to "canonical works" only. Any remaining oddities are then probably in the MusicBrainz data, which may require editing.*

3. "Tags to create" sets the names of the tags that will be created from the sources described above. All these tags will be blanked before filling as specified. Tags specified against more than one source will have later sources appended in the sequence specified, separated by separators as specified.

    * **Work tags**:
      - "Tags for Work - for software with 2-level capability". Some software (notably Muso) can display a 2-level work hierarchy as well as the work-movement hierarchy. This tag can be use to store the 2-level work name (a double colon :: is used to separate the levels within the tag).
      - "Tags for Work - for software with 1-level capability". Software which can display a movement and work (but no higher levels) could use any tags specified here. Note that if there are multiple work levels, the intermediate levels will not be tagged. Users wanting all the information should use the tags from the previous option (but it may cause some breaks in the display if levels change) - alternatively the missing work levels can be included in a movement tag (see below).
      - "Tags for top-level (canonical) work". This is the top-level work held in MB. This can be useful for cataloguing and searching (if the library software is capabale).

    * **Movement/Part tags**:
      - "Tags for(computed) movement number". This is not necessarily the embedded movt/part number, but is the sequence number of the movement within its parent work **on the current release**.
      - "Tags for Movement - excluding embedded movt/part numbers". As below, but without the movement part/number prefix (if applicable)
      - "Tags for Movement - including embedded movt/part numbers". This tag(s) will contain the full lowest-level part name extracted from the lowest-level work name, according to the chosen tagging style.
      An option is also provided for tags which are to include any intermediate work levels which are missing from a single-level work tag. Use different tag names for these, from the multi-level version, otherwise both versions will be appended, creating a multi-valued tag (a warning will be given).

**Strategy for setting tags:** *It is suggested that initially you just use the multi-level work tag and related movement tags, even if your software only has a single-level work capability. This may result in work names being repeated in work headings, but may look better than the alternative of having work names repeated in movement names (this is the default). If this does not look good you can then compare it with the alternative approach and change as required for specific releases. If your software does not have any "work" capability, then you can still get the full work details by, for example, specifying "title" as both a work and a movement tag.*

**Note for iTunes users:** *iTunes and Picard do not work well together. iTunes can display work and movement for m4a(mp4) files, but Picard does not write the movement tag. To work round this, write the movement to the "subtitle" tag assuming that is not otherwise used, and use a simple Mp3tag action to convert it to MOVEMENTNAME before importing to iTunes. If you are writing to a FLAC file which will subsequently be converted to m4a then different tag names may be required; e.g. using dBpoweramp, write the movement to "movement name". In both cases use "work" for the work. To store the top_work, use "grouping" if writing directly to m4a, but "style" if writing to FLAC followed by dBpoweramp conversion. You can put multiple tags into the boxes described above so that your options are multi-purpose. N.B. if work tags are specified and the work has at least one level (i.e. at least work: movement), then the tag "show work movement" will be set to 1. This is used by iTunes to trigger the hierarchical display and should work both directly with m4a files and indirectly via files which are subsequently converted.*

## Advanced tab

Hopefully, this tab should not be much used - and even less in future versions. In any case, it should not need to be changed frequently. There are four sections as shown in the sceeen print below:
![Advanced options](http://i.imgur.com/VezMj9Y.jpg)

1. "Artists". This has only one subsection - "Ensemble strings" - which permits the listing of strings by which ensembles of different types may be identified. This is used by the plugin to place performer details in the relevant hidden variables and thus make them available for use in the "Artists" tab as sources for any required tags. 
If it is important that only whole words are to be matched, be sure to include a space after the string.

2. "Work levels". This section has parameters applicable to the "works and parts" functions.

	* **Max number of re-tries to access works (in case of server errors)**. Sometimes MB lookups fail. Unfortunately Picard (currently) has no automatic "retry" function. The plugin will attempt to retry for the specified number of attempts. If it still fails, the hidden variable _cwp_error will be set with a message; if error logging is checked in section 4, an error message will be written to the log and the contents of _cwp_error will be written out to a special tag called "An_error_has_occurred" which should appear prominently in the bottom pane of Picard. The problem may be resolved by refreshing, otherwise there may be a problem with the MB database availability. It is unlikely to be a software problem with the plugin.

	* **How title metadata should be included in extended metadata**. This subsection contains various parameters affecting the processing of strings in titles. Because titles are free-form, not all circumstances can be anticipated. Detailed documentation of these is beyond the scope of this Readme as the effects can be quite complex and subtle and may require an understanding of the plugin code (which is of course open-source) to acsertain them. If pure canonical works are used ("Use only metadata from canonical works" and, if necessary, "Full MusicBrainz work hierarchy" on the Works and parts tab, section 2) then this processing should be irrelevant, but no text from titles will be included.

3. "Logging options". These options are in addition to the options chosen in Picard's "Help->View error/debug log" settings. They only affect messages written by this plugin. To enable debug messages to be shown, the flag needs to be set here and "Debug mode" needs to be turned on in the log. It is strongly advised to keep the "debug" and "info" flags unchecked unless debugging is required as they slow up processing significantly and may even cause Picard to crash on large releases. The "error" and "warning" flags should be left checked, unless it is required to suppress messages written out to tags (the default is to write messages to the tags 001_errors and 002_warnings).

4. "Save plugin details and options in a tag?" can be used so that the user has a record of the version of Classical Extras which generated the tags and which options were selected to achieve the resulting tags. Note that the tags will be blanked first so this will only show the last options used on a particular file. The same tag can be used for both sets of options, resulting in a multi-valued tag. 

    The tag contents are in json format. In a future version, there **might** be functionality to read this tag and use the options therein.

# Information on hidden variables

This section is for users who want to write their own scripts. The definition and source of each hidden variable is listed.

## Works and parts

- _cwp_work_n, where n is an integer >=0 : The MB work name at level n. For n=0, the tag is the same as the current standard Picard tag "work"
- _cwp_work_top : The top work name (i.e. for maximal n). Thus, if max n = N, _cwp_work_top = _cwp_work_N.
- _cwp_workid_n : The matching work id for each work name. For n=0, the tag is the same as the standard Picard tag "MusicBrainz Work Id"
- _cwp_workid_top : The matching work id for the top work name.
- _cwp_part_n : A "stripped" version of _cwp_work_n, where higher-level work text has been removed wherever possible, to avoid duplication on display.
	Thus in theory, _cwp_work_0 will be the same as "_cwp_work_top: _cwp_part_(N-1): ...: _cwp_part_0" (punctuation excepted), but may differ in more complex situations where there is not an exact hierarchy of text as the work levels are traversed. (See below for the "_X0" series which attempts to address any such inconsistencies)
- _cwp_part_levels : The number of work levels attached to THIS TRACK. Should be equal to N = max(n) referred to above.
- _cwp_work_part_levels : The maximum number of levels for ANY TRACK in the album which has the same top work as this track.
- _cwp_single_work_album : A flag = 1 if there is only one top work in this album, else = 0.
- _cwp_work : the level selected by the plugin to be the source of the single-level work name if "Use only metadata from canonical works" is selected (usually the top level, but one lower in the case of a single work album).
- _cwp_groupheading : the level selected by the plugin to be the source of the multi-level work name if "Use only metadata from canonical works" is selected.
- _cwp_part : The movement name derived from the MB work names (generally = _cwp_part_0) and used as the source for the movement name used for "Tags for Movement - including embedded movt/part numbers".
- _cwp_inter_work : Intermediate works between _cwp_part and _cwp_work (if any).

If there is more than one work at the bottom level, then _cwp_work_0 and _cwp_workid_0 will have multiple entries. However, only the first workId is used to find a parent work. This should be OK in 99% of cases, since the existence of multiple works at the bottom level is because they are not broken into separate tracks on the recording and thus they are children of a common parent. Another common situation is that a "bottom level" work is spread across more than one track. Rather than artificially split the work into sub-parts, this is often shown in MusicBrainz as a track being a "partial recording of" a work. The plugin deals with this by creating a notional lowest-level with the suffix " (part)" appended to the work it is a partial recording of. In order that this notional part can be separately identified from the full work, the musicbrainz_recordingid is used as the identifier rather than the workid.
If there is more than one "parent" work of a lower level work, the plugin **currently** uses the one with the longest name, on the grounds that the longest-named is likely to be the lowest level (but not necessarily); this is an area for improvement.

- _cwp_X0_part_0 : A "stripped" version of _cwp_work_0 (see above), where elements of _cwp_work_0 which repeat within level 1 have been stripped.
- _cwp_X0_work_n : The elements of _cwp_work_0 which repeat within level n
- _cwp_X0_work_repeat : The (higher) level at which a repeated work has been found by attempting to create a hierarchy of works from the level 0 work. If any such repeats are found the attempt to use work level 0 as a text basis for all works (where "Consistent with lowest level work description" has been selected as the source for canonical work text) will be abandoned and the full MB hierarchy will be used instead. However, script writers can use the _cwp_X0_work_n variables to over-ride this behaviour, if wished.

As well as variables derived from MB's work structure, some variables are produced which are derived from the track title. Typically titles may be in the format "Work: Movement", but not always. Sometimes the title is prefixed by the name of the composer; in this case the variable
- _cwp_title
is provided which excludes the composer name and subsequent processing is carried out using this rather than the full title. 

The plugin uses a number of methods attempt to extract the works and movement from the title. The resulting variables are:
- _cwp_title_work_n, and
- _cwp_title_part_n
which mirror those for the ones based on MB works described above.
- _cwp_title_part_levels which similarly mirrors _cwp_part_levels
- _cwp_title_work_levels which similarly mirrors _cwp_work_part_levels

- _cwp_title_work is the level selected by the plugin to be the source of the single-level work name if "Use only metadata from title text" is selected (usually the top level, but one lower in the case of a single work album).
- _cwp_title_groupheading is similarly the level selected by the plugin to be the source of the multi-level work name if "Use only metadata from title text" is selected.

- _cwp_extended_part : = _cwp_part with additional movement information from the title - given in {}.
- _cwp_extended_groupheading : = _cwp_groupheading with additional work information from the title - given in {}.
- _cwp_extended_work : = _cwp_work with additional work information from the title - given in {}.
- _cwp_extended_inter_work : = _cwp_inter_work with additional work information from the title - given in {}.
The "extended" variables can be useful where the "canonical" work names in MB are in the original language and the titles are in English (say). Various heuristics are used to try and add (and only add) meaningful additional information, but oddities may occur which require manual editing.

One artist tag is set in this section:
- _cwp_arrangers : This is for arrangers of the work, which are included in the Picard "arranger" tag, and also "instrument arrangers", which Picard does not currently write  to the Arranger tag, despite style guidance saying to use specific instrument types instead of generic arranger.

Finally, the tag _cwp_error is provided to supply warnings and error messages to the user. At present these are a warning if there is more than one work (only one parent will be followed) or if excessive "Service Unavailabilty" has caused some metadata to be omitted.

## Artists

All the additional hidden variables for artists written by Classical Extras are prefixed by _cea_. Note that these are generally in the plural, whereas the standard tags are singular. If the user blanks a tag then the original value is stored in the singular with the _cea_ prefix. Thus _cea_arranger would be the contents of the Picard tag "arranger" before blanking, whereas _cea_arrangers is hidden variable created by Classical Extras.

- _cea_soloists : List of performers (with instruments in brackets), who are NOT ensembles or conductors, separated by semi-colons. Note they may not strictly be "soloists" in that they may be part of an ensemble.
- _cea_soloist_names : Names of the above (i.e. no instruments).
- _cea_soloists_sort : Sort_names of the above.
- _cea_vocalists : Soloists who are vocalists (with voice in brackets).
- _cea_vocalist_names : Names of the above (no voice).
- _cea_instrumentalists : Soloists who have instruments but are not vocalists.
- _cea_instrumentalist_names : Names of the above (no instrument).
- _cea_other_soloists : Soloists who do not have specified instrument/voice.
- _cea_ensembles : List of performers which are ensembles (with type / instruments - e.g. "orchestra" - in brackets), separated by semi-colons.
- _cea_ensemble_names : Names of the above (i.e. no instruments).
- _cea_ensembles_sort : Sort_names of the above.
- _cea_album_soloists : Sub-list of soloist_names who are also album artists
- _cea_album_soloists_sort : Sort_names of the above.
- _cea_album_conductors : List of conductors whao are also album artists
- _cea_album_conductors_sort : Sort_names of the above.
- _cea_album_ensembles: Sub-list of ensemble_names who are also album artists
- _cea_album_ensembles_sort : Sort_names of the above.
- _cea_album_composers : List of composers who are also album artists
- _cea_album_composers_sort : Sort_names of the above.
- _cea_album_track_composer_lastnames : Last names of the above. (N.B. This only includes the composers of the current track - compare with _cea_album_composer_lastnames below).
- _cea_album_composer_lastnames : Last names of composers of ANY track on the album who are also album artists. This can be used to prefix the album name if required. (cf _cea_album_track_composer_lastnames)
- _cea_support_performers : Sub-list of soloist_names who are NOT album artists
- _cea_support_performers_sort : Sort_names of the above.
- _cea_composers : Alternative composer name, based on sort name, to avoid non-latin language problems.
- _cea_conductors : Alternative conductor name, based on sort name, to avoid non-latin language problems.
- _cea_performers : An alternative to performer, based on the sort name (see note re non-Latin script below).
- _cea_arrangers : All arrangers for the recording or work, other than orchestrators(including those not created by Picard as standard). If the work and parts functionality has also been selected, it will include the arrangers of parent works, which Picard also currently omits. Work arrangers are also stored as _cwp_arrangers.
- _cea_orchestrators : Arrangers (per Picard) included in the MB database as type "orchestrator".
- _cea_chorusmasters : A person who (per Picard) is a conductor, but is "chorus master" in the MB database (i.e. not necessarily conducting the performance).
- _cea_leaders : The leader of the orchestra ("concertmaster" in MusicBrainz) - not created by Picard as standard.

Note re non-Latin characters: These can be avoided by using the Picard option (Options->Metadata "Translate artist names to this locale where possible"). This plugin provides an alternative which will always remove middle (patronymic) names from Cyrillic-script names (but does not deal fully with other non-Latin scripts). It is based on the sort names wherever possible, otherwise a Cyrillic-Latin transliteration is used. The Picard option only currently works properly for the Artist tag (where it uses the locale primary alias, which can be set to exclude patronyms) - other tags use the full sort name as the basis, which will generally include the patronym.

-cea_work_type : Although not strictly an artist field, this is derived from artist and performer metadata. This is the variable populated if "Infer work types" is selected on the Artists tab.

# Software-specific notes

Note that _cwp_part_levels > 0 will indicate that the track recording is part of a work and so could be used to set other software-specific flags (e.g. for iTunes "show work movement") to indicate a multi-level "work: movement".

## SongKong

SongKong users may wish to map the _cwp variables to tags produced by SongKong if consistency is desired, in which case the mappings are principally:
- _cwp_work_0 => musicbrainz_work_composition
- _cwp_workid_0 => musicbrainz_work_composition_id
- _cwp_work_n => musicbrainz_work_part_leveln, for n = 1..6
- _cwp_workid_n => musicbrainz_work_part_leveln_id, for n = 1..6
- _cwp_work_top => musicbrainz_work 
In addition, _cwp_title_work and _cwp_title_part_0 are intended to be equivalent to SongKong's work and part tags.
(N.B. Full consistency between SongKong and Picard may also require the modification of Artist and related tags via a script, or the preservation of the related file tags)

## Muso

The tag "groupheading" should be as the "Tags for Work - for software with 2-level capability". Muso will use this directly and extract the levels from in (split by the double colon). Muso permits a variety of import options which should be capable of combination with the tagging options in this plugin to achieve most desired effects. To avoid the use of import options in Muso, set the output tags from the plugin to be the native ones used by Muso (NB "title" may include or exclude groupheading - Muso should recognise it and extract it).

## Players with no "work" capability

Leave the "title" tag unchanged or make it a combination of work and movement.


# Possible Enhancements
Planned enhancements (among others) are 
1. Include discrimination as to type of parts relationship (i.e. exclude irrelevant parents)
2. If a work is an arrangement of another work, look for the parent works of that other work (possibly)
3. Find a better way dealing with multiple parents (rather than just select the one with the longest name as at present)

# Technical Matters
Issues were encountered with the Picard API in that there is not a documented way to let Picard know that it is still doing asynchronous tasks in the background and has not finished processing metadata. Many thanks to @dns_server for assistance in dealing with this and to @sophist for the albumartist_website code which I have used extensively. I have tried to add some more comments to help any others trying the same techniques.
A variety of releases were used to test this plugin, but there may still be bugs, so further testing is welcome. The following release was particularly complex and useful for testing: https://musicbrainz.org/release/ec519fde-94ee-4812-9717-659d91be11d4
