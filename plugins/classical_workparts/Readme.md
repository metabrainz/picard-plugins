GENERAL INFORMATION
This is version 0.3 of "classical_workparts.py" (renamed from workparts.py to make the intended use clearer).
It populates the metadata tags with information from the MusicBrainz database about the work(s) of which the track is a recording, and the work(s) of which they are a part, passing up through mutiple work-part levels until the top is reached.
This is particularly designed to assist with tagging of classical music so that players or library managers which can display multiple work levels can have access to them.

OUTPUT 
All custom tags produced by this plugin are prefixed with "CWP_". The basic tags are as follows:
	CWP_work_n, where n is an integer >=0 : The work name at level n. For n=0, the tag is the same as the standard Picard tag "work"
	CWP_work_top : The top work name (i.e. for maximal n). Thus, if max n = N, CWP_work_top = CWP_work_N.
	CWP_workId_n : The matching work id for each work name. For n=0, the tag is the same as the standard Picard tag "MusicBrainz Work Id"
	CWP_workId_top : The matching work id for the top work name.
	CWP_part_n : A "stripped" version of CWP_work_n, where higher-level work text has been removed wherever possible, to avoid duplication on display.
		Thus in theory, CWP_work_0 will be the same as "CWP_work_top: CWP_part_(N-1): ...: CWP_part_0" (punctuation excepted), but may differ in more complex situations wher there is not an exact hierarchy of text as the work levels are traversed.
	CWP_part_levels : The number of work levels attached to THIS TRACK. Should be equal to N = max(n) referred to above.
	CWP_work_part_levels : The maximum number of levels for ANY TRACK in the album which has the same top work as this track.
	CWP_single_work_album : A flag = 1 if there is only one top work in this album, else = 0.
If there is more than one work at the bottom level, then CWP_work_0 and CWP_workId_0 will have multiple entries. However, only the first workId is used to find a parent work. This should be OK in 99% of cases, since the existence of multiple works at the bottom level is because they are not broken into separate tracks on the recording and thus they are children of a common parent. 
If there is more than one "parent" work of a lower level work, the plugin uses the one with the longest name, on the grounds that the longest-named is likely to be the lowest level (but not necessarily); this might possibly be improved.

As well as tags derived from MB's work structure, some tags are produced which are derived from the track title. Typically titles may be in the format "Work: Movement". The plugin will sttempt to extract the work and movement into:
	CWP_title_work, and
	CWP_title_movement
This process can be a bit hit and miss. The tags will only be produced if there is a parent work.

In addition to these generic tags some custom tags are produced, particularly for Muso users, but which may be of value to others:
	CWP_part : The movement name derived from the MB work names - to populate Muso's Title field.
	CWP_groupheading : For multi-level works, this is intended to be imported to Muso's Group Header field. For two or more levels, the sub-header for Muso will be the text after a double colon.
	CWP_extended_part : = CWP_part with additional movement information from the title - given in {}.
	CWP_extended_groupheading : = CWP_part with additional work information from the title - given in {}.
The latter two tags can be useful where the "canonical" work names in MB are in the original language and the titles are in English (say). The user can choose which set of tags they prefer.


USAGE
The CWP_ prefix is used so as minimise the risk of conflicts with other tags. However, unless the player / library manager has a custom tag import capability, the tags output might not be capable of direct use. Also, users may wish to construct slightly different tags for their purposes. Therefore it is recommended to use Picard's "Taggerscript" to re-work the tags as required.
Note that CWP_part_levels > 0 will indicate that the track reording is part of a work and so could be used to set other software-specific flags (e.g. for iTunes "show work movement") to indicate a multi-level "work: movement".
SongKong users may wish to map the CWP tags to those produced by SongKong, in which case the mappings are simply:
	CWP_work_0 => musicbrainz_work_composition
	CWP_workId_0 => musicbrainz_work_composition_id
	CWP_work_n => musicbrainz_work_part_leveln, for n = 1..6
	CWP_workId_n => musicbrainz_work_part_leveln_id, for n = 1..6
	CWP_work_top => musicbrainz_work 
In addition, CWP_title_work and CWP_title_movement are intended to be equivalent to SongKong's work and movement tags, but the algorithm is less sophisticated.
(N.B. Full consistency between SongKong and Picard will also require the modification of Artist asnd related tags via Taggerscript, or the preservation of the related file tags )
For Muso users, the specific custom tags described above are provided and a choice can be made using a simple Tagger Script option.

POSSIBLE ENHANCEMENTS
Planned enhancements (among others) are 
(a) to include discrimination as to type of parts relationship (i.e. exclude irrelevant parents)
(b) to find a better way of selecting parents rather than just length of name
[(c) to add specific arranger and any other relevant metadata relating to a work which is not in the standard Picard tags] On hold as may be addressed in Picard main code.

TECHNICAL MATTERS
Issues were encountered with the Picard API in that there is not a documented way to let Picard know that it is still doing asynchronous tasks in the background and has not finished processing metadata. Many thanks to Daniel Sobey for assistance in dealing with this and to Sophist for the albumartist_website code which I have used extensively. I have tried to add some more comments to help any others trying the same techniques.
A variety of releases were used to test this plugin, but there may still be bugs, so further testing is welcome. The following release was particularly complex and useful for testing: https://musicbrainz.org/release/ec519fde-94ee-4812-9717-659d91be11d4