# General Information
This is version 0.6 of "classical_extras". It only works currently with FLAC and mp3 files.
It populates hidden variables in Picard with information from the MusicBrainz database about the recording, artists and work(s), and of any containing works, passing up through mutiple work-part levels until the top is reached.
The "Options" page (Options->Options->Plugins->Classical Extras) allows the user to determine how these hidden variables are written to file tags, as well as a variety of other options.
This plugin is particularly designed to assist with tagging of classical music so that players or library managers which can display multiple work levels and different artist types can have access to them.

All hidden variables produced by this plugin are prefixed with "_cwp_" or  "_cea_" depending on which section of the plugin (i.e.which Class) created them. Full details of these variables are given in a later section.
Tags are output depending on the choices specified by the user in the Options Page. Defaults are provided for these tags which needed to be added to / modified / deleted according to user requirements. 
If the Options Page does not provide sufficient flexibility, users familiar with scripting can write Tagger Scripts to access the hidden variables directly.

# Installation
Instal the zip file in your plugins folder in the usual fashion

# Usage
After installation, go to the Options Page and modify choices as required. There are 3 tabs - "Artists", "Works and parts" and "Advanced". The subsections below describe each of these.

## Artists tab
There are four coloured sections as shown in the screen image below:

![Artist options](https://github.com/MetaTunes/picard-plugins/blob/master/plugins/classical_extras/artist_options.jpg)

1. "Create extra artist metadata" should be selected otherwise this section will not run. This is the default.

    "Name album as 'Composer Last Name(s): Album Name'" will add the composer(s) last name(s) before the album name if the name(s) does not already appear in the album name. MB style is to exclude the composer name unless it is actually part of the album name, but it can be useful to add it for library organisation. The default is checked.

2. "Remove Picard-generated tags before applying subsequent actions?". Any tags specified in the next two rows will be blanked before applying the tag sources described in the following section. NB this applies only to Picard-generated tags, not to other tags which might pre-exist on the file: to blank those, use the main Options->Tags page. Comma-separate the tag names within the rows and note that these names are case-sensitive.

3. "Tag mapping". This section permits the contents of any hidden variable or tag to be written to one or more tags.

    * **Sources**:
The most useful sources are available from the drop-down list and are as follows:
Most of the names are for artist data and are sourced from hidden variables (prefixed with "_cea_")
      - soloists : List of performers (with instruments in brackets), who are NOT ensembles or conductors, separated by semi-colons. Note they may not strictly be "soloists" in that they may be part of an ensemble.
      - soloist_names : Names of the above (i.e. no instruments).
      - ensembles : List of performers which are ensembles (with type / instruments - e.g. "orchestra" - in brackets), separated by semi-colons.
      - ensemble_names : Names of the above (i.e. no instruments).
      - album_soloists : Sub-list of soloist_names who are also album artists
      - album_conductors : List of conductors who are also album artists
      - album_ensembles: Sub-list of ensemble_names who are also album artists
      - album_composers : List of composers who are also album artists
      - album_composer_lastnames : Last names of composers of ANY track on the album who are also album artists. This is the source used to prefix the album name (when that option is selected).
      - support_performers : Sub-list of soloist_names who are NOT album artists
      - composer : Note that, if "Fix cyrillic names" in the last section is checked, this is based on sort name, to avoid non-latin language problems (if translation is not already made via locale choices).
      - conductor : Note that, if "Fix cyrillic names" in the last section is checked, this is based on sort name, to avoid non-latin language problems (if translation is not already made via locale choices).

      The last item in the drop-down list is "work_type" which only has content if the "Infer work types" box in the last coloured section is checked.
Any Picard tag names can also be typed in as sources. Hidden variables may also be used. Any source names which are not recognised will be treated as string constants; blanks may also be used.

    * **Tags**:
Enter the (comma-separated) tag names into which the sources should be written (case sensitive). Note that this will result in the source data being APPENDED in the tag - it will not overwrite the existing contents. Check "Conditional?" if the tag is only to be updated if it is previously blank. The lines will be applied in the order shown. Users should be able to achieve most requirements via a combination of blanking tags, using the right source order and "conditional" flags. For example, to overwrite a tag sourced from "composer" with "conductor", specify "conductor" first, then "composer" as conditional.

4. "Include arrangers from all work levels, plus instrument arrangers". This will gather together any arranger information from the recording, work or parent works and place it in the "arranger" tag. If you want to add arrangers as composers, do so in the previous section. (Note that Picard does not natively pick up all arrangers)

"Infer work types (map to genre using tag mapping or script as req'd)". This attempts to create a "work_type" tag based on information in the artist-related tags. It does not (currently) use the "work-type" data for MB works as this is not well populated and is under review at present. Values provided are:
Orchestral, Concerto, Instrumental, Vocal, Choral, Opera, Duet, Aria, Song. For concerto and solo performances the instrument is also given where possible.

Use "work_type" as a source in the prvious section to (e.g.) map to the genre tag. For more complex treatment, use scripts.

"Fix cyrillic names (where possible and if not fixed by locale settings)" attempts to provide English version of composers, conductors and performers where the script is non-Latin and the relevant locale settings (Options->Metadata) have not fixed this. For performers, the tags are updated directly, but for composers and conductors, the original tag is left and can be updated by adding lines in the previous section (map composer->composer etc.)

## Work and parts tab

There three coloured sections as shown in the screen print below:
![Works and parts options](https://github.com/MetaTunes/picard-plugins/blob/master/plugins/classical_extras/work_parts_options.jpg)

1. "Include all work levels" should be selected otherwise this section will not run.

    "Use cache (if available)" prevents excessive look-ups of the MB database. Every look-up of a parent work needs to be performed separately (hopefully the MB database might make this easier some day). Network usage constraints by MB means that each look-up tales a minimum of 1 second. Once a release has been looked-up, the works are retained in cache, significantly reducing the time required if, say, the options are changed and the data refreshed. However, if the user edits the works in the MB database then the cache will need to be turned off temporarily for the refresh to find the new/changed works.

2. "Tagging style". This section determines how the hierarchy of works will be sourced.

    * **Works source**: There are 3 options for determing the principal source of the works metadata
      - "Use only metadata from title text". The plugin will atempt to extract the hierarchy of works from the track title by looking for repetitions and patterns. If the title does not contain all the work names in the hierarchy then obviously this will limit what can be provided.
      - "Use only metadata from canonical works". The hierarchy in the MB database will be used. Assuming the work is correctly entered in MB, this should provide all the data. However the text may differ from the track titles and will be the same for all recordings. It may also be in the language of the composer whereas the titles will be in the language of the release.
      - "Use canonical work metadata enhanced with title text". This supplements the canonical data with text from the titles **where it is significantly different**. The supplementary data will be in curly brackets. This is clearly the most complete metadata style of the three but may lead to long descriptions. See image below for an example (using the Muso library manager).
      ![Respighi](https://github.com/MetaTunes/picard-plugins/blob/master/plugins/classical_extras/Respighi.jpg)

    * **Source of canonical work text**. Where either of the second two options above are chosen, there is a further choice to be made:
      - "Full MusicBrainz work hierarchy". The names of each level of work are used to populate the relevant tags. I.e. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast, JB 1:112", not "Má vlast".
      - "Consistent with lowest level work description (where possible)". The names of the level 0 work are used to populate the relevant tags. I.e. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast", not "Má vlast, JB 1:112". This frequently looks better, but not always, particularly if the level 0 work name does not contain all the parent work detail. If selected, this choice will only be implemented where the level 0 work name appears to have the parent work names within it.

3. "Tags to create" sets the names of the tags that will be created from the sources described above.

    * **Movement/Part tags**

## Work parts and levels
- _cwp_work_n, where n is an integer >=0 : The work name at level n. For n=0, the tag is the same as the current standard Picard tag "work"
- _cwp_work_top : The top work name (i.e. for maximal n). Thus, if max n = N, _cwp_work_top = _cwp_work_N.
- _cwp_workid_n : The matching work id for each work name. For n=0, the tag is the same as the standard Picard tag "MusicBrainz Work Id"
- _cwp_workid_top : The matching work id for the top work name.
- _cwp_part_n : A "stripped" version of _cwp_work_n, where higher-level work text has been removed wherever possible, to avoid duplication on display.
	Thus in theory, _cwp_work_0 will be the same as "_cwp_work_top: _cwp_part_(N-1): ...: _cwp_part_0" (punctuation excepted), but may differ in more complex situations where there is not an exact hierarchy of text as the work levels are traversed.
- _cwp_part_levels : The number of work levels attached to THIS TRACK. Should be equal to N = max(n) referred to above.
- _cwp_work_part_levels : The maximum number of levels for ANY TRACK in the album which has the same top work as this track.
- _cwp_single_work_album : A flag = 1 if there is only one top work in this album, else = 0.

If there is more than one work at the bottom level, then _cwp_work_0 and _cwp_workid_0 will have multiple entries. However, only the first workId is used to find a parent work. This should be OK in 99% of cases, since the existence of multiple works at the bottom level is because they are not broken into separate tracks on the recording and thus they are children of a common parent. Another common situation is that a "bottom level" work is spread across more than one track. Rather than artificially split the work into sub-parts, this is often shown in MusicBrainz as a track being a "partial recording of" a work. The plugin deals with this by creating a notional lowest-level with the suffix " (part)" appended to the work it is a partial recording of. In order that this notional part can be separately identified from the full work, the musicbrainz_trackid is used as the identifier rather than the workid.
If there is more than one "parent" work of a lower level work, the plugin CURRENTLY uses the one with the longest name, on the grounds that the longest-named is likely to be the lowest level (but not necessarily); this is scheduled for improvement.

As well as variables derived from MB's work structure, some variables are produced which are derived from the track title. Typically titles may be in the format "Work: Movement". Sometimes the title is prefixed by the name of the composer; in this case the variable
- _cwp_title
is provided which excludes the composer name and subsequent processing is carried out using this rather than the full title. The plugin will attempt to extract the work and movement into:
- _cwp_title_work, and
- _cwp_title_movement
This process can be a bit hit and miss as we are dependent on the naming convention of the title.
- _cwp_title_work_level is used to indicate at what level in the main structure the _cwp_title_work will be applied. Normally this is level 1.

In addition to these generic variables some custom variables are produced, particularly for Muso users, but which may be of value to others:
- _cwp_part : The movement name derived from the MB work names - to populate Muso's Title field.
- _cwp_groupheading : For multi-level works, this is intended to be imported to Muso's Group Header field. For two or more levels, the sub-header for Muso will be the text after a double colon.
- _cwp_extended_part : = _cwp_part with additional movement information from the title - given in {}.
- _cwp_extended_groupheading : = _cwp_part with additional work information from the title - given in {}.
The latter two variables can be useful where the "canonical" work names in MB are in the original language and the titles are in English (say). The user can choose which set of variables they prefer (different tagger scripts supplied). Various heuristics are used to try and add (and only add) meaningful additional information, but oddities may occur which require manual editing.

One artist tag is set in this section:
- _cwp_arranger : This is for "instrument arrangers", where Picard does not currently write them to the Arranger tag (despite style guidance saying to use specific instrument types instead of generic arranger). This might become unnecessary if Picard is fixed.

Finally, the tag _cwp_error is provided to supply warnings and error messages to the user. At present these are a warning if there is more than one work (only one parent will be followed) or if excessive "Service Unavailabilty" has caused some metadata to be omitted.

## Alternative artists
- _caa_soloists : List of performers (with instruments in brackets), who are NOT ensembles or conductors, separated by semi-colons. Note they may not strictly be "soloists" in that they may be part of an ensemble.
- _caa_soloist_names : Names of the above (i.e. no instruments).
- _caa_soloists_sort : Sort_names of the above.
- _caa_ensembles : List of performers which are ensembles (with type / instruments - e.g. "orchestra" - in brackets), separated by semi-colons.
- _caa_ensemble_names : Names of the above (i.e. no instruments).
- _caa_ensembles_sort : Sort_names of the above.
- _caa_album_soloists : Sub-list of soloist_names who are also album artists
- _caa_album_soloists_sort : Sort_names of the above.
- _caa_album_conductors : List of conductors whao are also album artists
- _caa_album_conductors_sort : Sort_names of the above.
- _caa_album_ensembles: Sub-list of ensemble_names who are also album artists
- _caa_album_ensembles_sort : Sort_names of the above.
- _caa_album_composers : List of composers who are also album artists
- _caa_album_composers_sort : Sort_names of the above.
- _caa_album_composer_lastnames : Last names of the above. (N.B. This only includes the composers of the current track - compare with _cea_album_composer_lastnames below).
- _caa_support_performers : Sub-list of soloist_names who are NOT album artists
- _caa_support_performers_sort : Sort_names of the above.
- _caa_composer : Alternative composer name, based on sort name, to avoid non-latin language problems.
- _caa_conductor : Alternative conductor name, based on sort name, to avoid non-latin language problems.

Note re non-Latin characters: These can be avoided by using the Picard option (Options->Metadata) "Translate artist names to this locale where possible". This plugin provides an alternative which will always remove middle (patronymic) names from Cyrillic-script names (but does not deal fully with other non-Latin scripts). It is based on the sort names, except for performers, where a Cyrillic-Latin transliteration is used. The Picard option only currently works properly for the Artist tag (where it uses the locale primary alias, which can be set to exclude patronyms) - other tags use the full sort name as the basis, which will generally include the patronym.

## Extra artists
- _cea_performer : An alternative to performer, based on the sort name (see note re non-Latin script above).
- _cea_arranger : Instrument arranger for the recording (not created by Picard as standard).
- _cea_album_composer_lastnames : Last names of composers of ANY track on the album who are also album artists. This can be used to prefix the album name if required. (cf _caa_album_composer_lastnames)

# Usage

## Work parts and levels
The _cwp_ prefix is used so as minimise the risk of conflicts with other variables. However, to make use of these variables, a tagger script is required to write the tags to suit the user's needs.
Note that _cwp_part_levels > 0 will indicate that the track recording is part of a work and so could be used to set other software-specific flags (e.g. for iTunes "show work movement") to indicate a multi-level "work: movement".
SongKong users may wish to map the _cwp variables to tags produced by SongKong, in which case the mappings are principally:
- _cwp_work_0 => musicbrainz_work_composition
- _cwp_workid_0 => musicbrainz_work_composition_id
- _cwp_work_n => musicbrainz_work_part_leveln, for n = 1..6
- _cwp_workid_n => musicbrainz_work_part_leveln_id, for n = 1..6
- _cwp_work_top => musicbrainz_work 
In addition, _cwp_title_work and _cwp_title_movement are intended to be equivalent to SongKong's work and movement tags, but the algorithm is less sophisticated.
(N.B. Full consistency between SongKong and Picard will also require the modification of Artist asnd related tags via Taggerscript, or the preservation of the related file tags )
For Muso users, the specific custom variables described above are provided and a choice can be made using a simple Tagger Script option.

## Artists
Again, these use prefixes (_cwp_, _caa_, or _cea_ depending on which Class in the plugin generates them) and require tagger scripts of the user's choosing to turn them into tags.

## Tagger scripts
The following tagger scripts are provided and may be modified as needed:
### for works:
- Muso works: to write the main tags for Muso to show Group Header, Sub-header and Part (import to Title).
- Extended works: as above, but makes use of the extended metadata described in the previous section.
- SongKong works: provides the same tags as SongKong/Jaikoz, including a title-derived work and movement where applicable and possible.
- CWP tags: To write out the hidden variables as explicit tags. Intended to assist script developers etc. - best not to save these tags, to avoid clutter.
### for artists:
- Alternative artists: to make use of the _caa_ variables. This is designed to make use of the display features of Muso and LMS and may need modification for other systems.
- Extra artists : to make use of the _cea_arranger and _cwp_arranger variables and to prefix the album with _cea_album_composer_lastnames.

The included jpg gives an illustration of the use of extended metadata in Muso to give dual-language information.

# Possible Enhancements
Planned enhancements (among others) are 
1. Include discrimination as to type of parts relationship (i.e. exclude irrelevant parents)
2. If a work is an arrangement of another work, look for the parent works of that other work
2. Find a better way of selecting parents where there is more than one (rather than just length of name as at present)
3. Be able to choose whether or not to use cache when refreshing (at present, if works have already been loaded as part of a previous album, they will not be associated with the new album - the only way to clear the cache is to close and re-open Picard)
4. Provide a UI to control various parameters

# Technical Matters
Issues were encountered with the Picard API in that there is not a documented way to let Picard know that it is still doing asynchronous tasks in the background and has not finished processing metadata. Many thanks to @dns_server for assistance in dealing with this and to @sophist for the albumartist_website code which I have used extensively. I have tried to add some more comments to help any others trying the same techniques.
Issues were also encountered with "Service unavailable" responses from the XML web service. Up to 6 re-tries are made before flagging an error in _cwp_error.
A variety of releases were used to test this plugin, but there may still be bugs, so further testing is welcome. The following release was particularly complex and useful for testing: https://musicbrainz.org/release/ec519fde-94ee-4812-9717-659d91be11d4

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