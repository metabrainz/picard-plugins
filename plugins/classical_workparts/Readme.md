# General Information
This is version 0.3 of "classical_workparts.py" (renamed from workparts.py to make the intended use clearer). It only works currently with FLAC and mp3 files.
It populates hidden variables in Picard with information from the MusicBrainz database about the work(s) of which the track is a recording, and the work(s) of which they are a part, passing up through mutiple work-part levels until the top is reached.
This is particularly designed to assist with tagging of classical music so that players or library managers which can display multiple work levels can have access to them.
** PLEASE NOTE ** A tagger script is required to make use of these hidden variables. Please see the notes on "Usage" below.

# Output 
All variables produced by this plugin are prefixed with "_cwp_". The basic variables are as follows:
- _cwp_work_n, where n is an integer >=0 : The work name at level n. For n=0, the tag is the same as the current standard Picard tag "work"
- _cwp_work_top : The top work name (i.e. for maximal n). Thus, if max n = N, _cwp_work_top = _cwp_work_N.
- _cwp_workid_n : The matching work id for each work name. For n=0, the tag is the same as the standard Picard tag "MusicBrainz Work Id"
- _cwp_workid_top : The matching work id for the top work name.
- _cwp_part_n : A "stripped" version of _cwp_work_n, where higher-level work text has been removed wherever possible, to avoid duplication on display.
	Thus in theory, _cwp_work_0 will be the same as "_cwp_work_top: _cwp_part_(N-1): ...: _cwp_part_0" (punctuation excepted), but may differ in more complex situations where there is not an exact hierarchy of text as the work levels are traversed.
- _cwp_part_levels : The number of work levels attached to THIS TRACK. Should be equal to N = max(n) referred to above.
- _cwp_work_part_levels : The maximum number of levels for ANY TRACK in the album which has the same top work as this track.
- _cwp_single_work_album : A flag = 1 if there is only one top work in this album, else = 0.

If there is more than one work at the bottom level, then _cwp_work_0 and _cwp_workid_0 will have multiple entries. However, only the first workId is used to find a parent work. This should be OK in 99% of cases, since the existence of multiple works at the bottom level is because they are not broken into separate tracks on the recording and thus they are children of a common parent.
If there is more than one "parent" work of a lower level work, the plugin CURERENTLY uses the one with the longest name, on the grounds that the longest-named is likely to be the lowest level (but not necessarily); this is scheduled for improvement.

As well as variables derived from MB's work structure, some variables are produced which are derived from the track title. Typically titles may be in the format "Work: Movement". The plugin will sttempt to extract the work and movement into:
- _cwp_title_work, and
- _cwp_title_movement
This process can be a bit hit and miss. The variables will only be produced if there is a parent work.

In addition to these generic variables some custom variables are produced, particularly for Muso users, but which may be of value to others:
- _cwp_part : The movement name derived from the MB work names - to populate Muso's Title field.
- _cwp_groupheading : For multi-level works, this is intended to be imported to Muso's Group Header field. For two or more levels, the sub-header for Muso will be the text after a double colon.
- _cwp_extended_part : = _cwp_part with additional movement information from the title - given in {}.
- _cwp_extended_groupheading : = _cwp_part with additional work information from the title - given in {}.
The latter two variables can be useful where the "canonical" work names in MB are in the original language and the titles are in English (say). The user can choose which set of variables they prefer (different tagger scripts supplied).

Finally, the tag _cwp_error is provided to supply warnings and error messages to the user. At present these are a warning if there is more than one work (only one parent will be followed) or if excessive "Service Unavailabilty" has caused some metadata to be omitted.


# Usage
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

The following tagger scripts are provided and may be modified as needed:
- Muso works: to write the main tags for Muso to show Group Header, Sub-header and Part (import to Title).
- Muso extended works: as above, but makes use of the extended metadata described in the previous section.
- SongKong works: provides the same tags as SongKong/Jaikoz, including a title-derived work and movement where applicable and possible.
- CWP tags: To write out the hidden variables as explicit tags. Intended to assist script developers etc. - best not to save these tags, to avoid clutter.
There is also another script, which is nothing to do with works, but which is included if needed to provide a degree of consistency between Picard artist conventions and those in SongKOng and Muso (call "Muso artists").

The included jpg gives an illustration of the use of extended metadata in Muso to give dual-language information.

# Possible Enhancements
Planned enhancements (among others) are 
1. to include discrimination as to type of parts relationship (i.e. exclude irrelevant parents)
2. to find a better way of selecting parents rather than just length of name

# Technical Matters
Issues were encountered with the Picard API in that there is not a documented way to let Picard know that it is still doing asynchronous tasks in the background and has not finished processing metadata. Many thanks to @dns_server for assistance in dealing with this and to @sophist for the albumartist_website code which I have used extensively. I have tried to add some more comments to help any others trying the same techniques.
Issues were also encountered with "Service unavailable" responses from the XML web service. Up to 6 re-tries are made before flagging an error in _cwp_error.
A variety of releases were used to test this plugin, but there may still be bugs, so further testing is welcome. The following release was particularly complex and useful for testing: https://musicbrainz.org/release/ec519fde-94ee-4812-9717-659d91be11d4