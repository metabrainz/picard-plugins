# General Information
This is version 0.8.7 of "classical_extras". It has only been tested with FLAC and mp3 files. It does work with m4a files, but Picard does not write all m4a tags (see further notes for iTunes users at the end of the "works and parts tab" section).
It populates hidden variables in Picard with information from the MusicBrainz database about the recording, artists and work(s), and of any containing works, passing up through mutiple work-part levels until the top is reached.
The "Options" page (Options->Options->Plugins->Classical Extras) allows the user to determine how these hidden variables are written to file tags, as well as a variety of other options.

This plugin is particularly designed to assist with tagging of classical music so that player or library manager software which can display multiple work levels and different artist types, can have access to these details.  
It has two main components "Extra Artists" and "Work Parts" which can be used independently or together. "Work Parts" will take at least as many seconds to process as there are works to look up (owing to MB throttling) so users who only want the extra artist information and not the work details may turn it off (e.g. perhaps for 'popular' music).

Hidden metadata variables produced by this plugin are (mostly) prefixed with "\_cwp\_" or  "\_cea\_" depending on which component of the plugin created them. Full details of these variables are given in a later section.
Tags are output depending on the choices specified by the user in the Options Page. Defaults are provided for these tags which can be added to / modified / deleted according to user requirements. 
If the Options Page does not provide sufficient flexibility, users familiar with scripting can write Tagger Scripts to access the hidden variables directly.

## Updates
Version 0.8.8: Fixes to allow for (1) disabling of 'use_cache' across releases which may share works and (2) works which might appear in their own right and also have arrangements. Also, re-set certain important options to defaults on starting Picard, namely: 'use_cache' set to True, 'log_debug', 'log_info' and 'options_overwrite' set to False; the user will need to deliberately re-set these on starting Picard if required - this is to prevent inadvertently leaving these flags in an abnormal state.

Version 0.8.7: Revised treatment of "conditional" tag mapping. Previously, if multiple sources were specified for a tag mapping and the "conditional" flag set, only the first non-empty source was used. Now all sources will be mapped to a tag if it was empty before executing the current tag mapping line. This is considered to be more intuitive and leads to less complex mapping lines. However, it some cases it may be necessary to split a line from a previous version if the previous behaviour was specifically desired. Improved algorithms for extending metadata with title info. Bug fixes.

Version 0.8.6: More consistent approach to sort tags and hidden variables. Bug fixes.

Version 0.8.5: Improved handling of instruments. Bug fixes.

Version 0.8.4: Improved UI, bug fixes and code improvements.

Version 0.8.3: Ability to use aliases of work names instead of the MusicBrainz standard names. Various options to use aliases and as-credited names for performers and writers (i.e. relationship artists). Option to use recording artists as well as (or instead of) track artists. All relationship artists are now tagged for all work levels (with some special processing for lyricists). New UI layout to separate tag mapping from artist options. Option to split lyrics into common (release) and unique (track) components. Various code improvements as well as bug fixes.

Version 0.8.2: Improved algorithms and a few minor bug fixes.

Version 0.8.1: Bug fixes and minor enhancements - including revison and extension of "synonyms" section on the "advanced" tab.

Version 0.8: Handle multiple recordings and/or multiple parents of a work. 
Handle multiple albumartist composers for one track. 
Option to use "credited as" name for artists (inc. performers and composers) who are "release artist" or "track artist". 
Option to exclude "solo" from instrument types. 
Option to over-ride plugin options with those used when the album was last saved. 
Option to keep (and append to) specified existing file tags - furthermore if "is_classical" is present, the work-type variable will include "Classical". 
Option to use (and write) SongKong-compatible work tags (saves processing time if SongKong is used to pre-process large numbers of files). 
Include the work (and its parents) of which a work is an arrangement (as a "pseudo-parent"). 
Include medleys in movement/part description (as [Medley of:...] or other descriptor specified in options). 
Allow for multiple parents of recordings and works (and multiple parents of those) - multiples are given as multiple tag instances, where permitted, otherwise separated by semi-colons. 
Option as to whether to include parent works where the relationship attribute is "part of collection". 
Plus minor enhancements and bug fixes too numerous to mention!
(Note that some old versions of the plugin may say v0.8 when they are only v0.7)

Version 0.7: Bug fixes. Pull request issued for this version.

Version 0.6.6: Bug fixes and algorithm improvements. Allow multiple sources for a tag (each will be appended) and use + as separator for concantenating sources, not a comma, to distinguish from the use of comma to separate multiples. Provide additional hidden variables ("sources") for vocalists and instrumentalists. Option to include intermediate work levels in a movement tag (for systems which cannot display multiple work levels).

Version 0.6.5: Include ability to use multiple (concatenated) sources in tag mapping (see notes under "tag mapping"). All artist "sources" using hidden variables (\_cea\_...) are now consistently in the plural, to distinguish from standard tags. Note that if "album" is used as a source in tag mapping, it will now be the revised name, where composer prefixing is used. To use the original name, use "release" as the source. Also various bug fixes, notably to ensure that all arrangers get picked up for use in tag mapping.

Version 0.6.4: Write out version number to user-specified tag. Provide default comment tags for writing ui options. Provide better m4a and iTunes compatibility (see notes). Added functionality for chorus master, orchestrator and concert master (leader). Re-arranged artist tab in ui. Various bug fixes.

Version 0.6.3: Bug fixes. Modified ui default options.

Version 0.6.2: Bug fixes. More flexible handling of artists (can blank and then add back later). Modified ui default options.

Version 0.6.1: Amended regex to permit non-Latin characters in work text.

# Installation
Install the zip file in your plugins folder in the usual fashion

# Usage
After installation, go to the Options Page and modify choices as required. There are 4 tabs - "Artists", "Tag mapping", Works and parts" and "Advanced". The sections below describe each of these. If the options provided do not allow sufficient flexibility for a user's need (hopefully unlikely!) then Tagger Scripts may be used to process the hidden variables or other tags. Alternatively, it may be possible to achieve the required result by running and saving twice (or more!) with different options each time. This is not recommended for more than a one-off - a script would be better.

**Important**: 
1.  The plugin **will not work fully unless** you have enabled "Use release relationships" and "Use track relationships" in Picard->Options->Metadata. However, it may be that the MusicBrainz database has conflicting data between track and release relationships, in which case fix the incorrect data using "Edit relationships" in MusicBrainz.
2.  It is recommended only to use the plugin on one or a few release(s) at a time, particularly for initial tagging and if the "Works and parts" function is being used. The plugin is not designed to do "bulk tagging" of untagged files - it may be better to use a tool such as SongKong for that and then use the plugin to enhance the results as required. However, once you have tagged files (either in Picard or, say, SongKong) such that they all at least have MusicBrainz IDs, you should be able to re-tag multiple releases by dragging the containing folder into Picard; this is useful to pick up changed MusicBrainz data or if you change the Classical Extras version or options (but bear in mind that the "Works and parts" function will still take at least 1 second per track and **make sure you have "debug" and "info" logging turned OFF** - in the "Advanced" tab). If you do want to try uising Picard / Classical Extras to tag a large number of files, then **make sure you also turn off "warning" logging**.
3.  If you are just changing option settings then you can usually "use cache" (see "work and parts" tab section 1) to avoid the 1-second per work delay. However, if the works data in MusicBrainz has been changed then obviously you will need to do a full look-up, so disable cache. If the work structure has been fundamentally changed (i.e. a different hierarchy of existing works) - either within the MusicBrainz database or by selecting/deselecting the "include collection relations", partial" or "arrangements" options - then you will need to quit and restart Picard to correctly pick up the new structure.
3.  Keep a backup of your picard.ini file (AppData->Roaming->MusicBrainz) in case you erase your settings or Picard crashes and loses them for you.

## Artists tab
There are five coloured sections as shown in the screen image below:

![Artist options](https://i.imgur.com/oQYry4D.jpg)

1. "Create extra artist metadata" should be selected otherwise this section (and the tag mapping section) will not run. This is the default.

	"Infer work types (map to genre using tag mapping or script as req'd)". This attempts to create a "work_type" tag based on information in the artist-related tags. It does not (currently) use the "work-type" data associated with MB works as this is not well populated and is under review at present. Values provided are:
	Orchestral, Concerto, Instrumental, Voice, Choral, Opera, Duet, Aria, Song. For concerto, solo and duet performances the instrument is also given where possible. If the track is a recorded work with a composer artist in MusicBrainz and the "Works and parts" section has "Include all work levels" selected, the tag will also include "Classical". Use "work_type" as a source in the tag mapping section below section to (e.g.) map to the genre tag. For more complex treatment, use scripts.

2. "Work-artist/performer naming options". 
  This section deals primarily with the application of aliases and credited_as names to replace the MusicBrainz standard names. The first box allows you to choose whether to replace MusicBrainz standard  names by aliases - either for all work-artists/performers or only work-artists (writers, composers, arrangers, lyricists etc.). The second box sets the usage of "as-credited" names: the first part of this lists all the places where as-credited names can occur (really!) and the second part allows you to apply these to performing artists and/or work-artists.  
  N.B. if more than one release is loaded in Picard, any available alias names loaded so far will be available and used. However, as-credited names will only be used from the current release.

   The bottom box then (a) allows a choice as to whether aliases will over-ride as-credited names or vice versa and (b) whether if there are still some names in non-Latin script, whether these should be replaced (this will always remove middle [patronymic] names from Cyrillic-script names [but does not deal fully with other non-Latin scripts]; it is based on the sort names wherever possible).

   Note that **none of this processing affects the contents of the "artist or "album_artist" tags**. These tags may be either work-artists or performing artists. Their contents are determined by the standard Picard options "translate artist names" and "use standardized artist names" in Options-->Metadata. If "translate name" is selected, the name will be the alias or (if no alias) the 'unsorted' sort-name; otherwise the name will be the MusicBrainz name if "use standardized artist names" is selected or the as-credited name (if available) if it is not selected.

3. "Recording artist options".
  In MusicBrainz, the recording artist may be different from the track artist. For classical music, the MusicBrainz guidelines state that the track artist should be the composer; however the recording artist(s) is/are usually the principal performer(s).  
  Because, in classical music (in MusicBrainz), recording artists will usually be performers whereas track artists are composers, by default, the naming convention for performers (set in the previous section) will be used (although only the as-credited name set for the recording artist will be applied). Alternatively, the naming convention for track artists can be used - which is determined by the main Picard metadata options.

  Classical Extras puts the recording artists into 'hidden variables' (as a minimum) using the chosen naming convention.
  There is also option to allow you to replace the track artist by the recording artist (or to merge them). The chosen action will be applied to the 'artist', 'artists', 'artistsort' and 'artists_sort' tags. Note that 'artist' is a single-valued string whereas 'artists' is a list and may be multi-valued. Lists are properly merged, but because the 'artist' string may have different join-phrases etc, a merged tag may have the recording artist(s) in brackets after the track artist(s). Obviously, for classical music, if you use "merge" then the artist tag will have both the composer and the recording artists: this may be desirable for simple players (with no composer recognition) but otherwise may look odd.

   Note that, if the original track artist is required in tag mapping (i.e. as it was before replacement/merge with recording artist), it is available through the hidden variable _cea_MB_artists.

   Note also that, if @loujin's browser script has been used to fill the recording artist data, this will be the same as the performing artists in the Recording-Artist relationship - i.e. it may be a lengthy list rather than the principal artist for the track.

4. "Other artist options":

  "Modify host tags and include annotations" (Previously called "Include arrangers from all work levels"). This will gather together, for example, any arranger-type information from the recording, work or parent works and place it in the "arranger" tag ('host' tag), with the annotation (see below) in brackets. All arranger types will also be put in a hidden variable, e.g. _cwp_orchestrators. The table below shows the artist types, host tag and hidden variable for each artist type.

   | Artist type | Host tag | Hidden variable |
   | --- | --- | --- |
   | writer | composer | writers |
   | lyricist | lyricist | lyricists |
   | librettist | lyricist | librettists |
   | revised by | arranger | revisors |
   | translator | lyricist | translators |
   | arranger | arranger | arrangers |
   | reconstructed by | arranger | reconstructors |
   | orchestrator | arranger | orchestrators |
   | instrument arranger | arranger | arrangers (with instrument type in brackets) |
   | vocal arranger | arranger | arrangers (with voice type in brackets) |
   | chorus master | conductor | chorusmasters |
   | concertmaster | performer (with annotation as a sub-key) | leaders |

   If you want to be more selective in what is included in host tags, then disable this option and use the tag mapping section to get the data from the hidden variables. If you want to add arrangers as composers, do so in the tag mapping section also. 

   (Note that Picard does not natively pick up all arrangers, but that the plugin will do so, provided the "Works and parts" section is run.)

   "Name album as 'Composer Last Name(s): Album Name'" will add the composer(s) last name(s) before the album name, if they are listed as album artists. If there is more than one composer, they will be listed in the descending order of the length of their music on the release. MusicBrainz style is to exclude the composer name unless it is actually part of the album name, but it can be useful to add it for library organisation. The default is checked.


   "Do not write 'lyricist' tag if no vocal performers". Hopefully self-evident. This applies to both the Picard 'lyricist' tag and the related internal plugin hidden variables '_cwp_lyricists' etc. 

   Note that the plugin will search for lyricists at all work levels (bottom up), but will stop after finding the first one (unless that was just a translator).

   "Do not include attributes in an instrument type" (previously just referred to the attribute 'solo'). MusicBrainz permits the use of "solo", "guest" and "additional" as instrument attributes although, for classical music, its use should be fairly rare - usually only if explicitly stated as a "solo" on the the sleevenotes. Classical Extras provides the option to exclude these attributes (the default), but you may wish to enable them for certain releases or non-Classical / cross-over releases.

   "Annotations": The chosen text will be used to annotate the artist type within the host tag (see table above for host tags), but only if "Modify host tags" is selected.

   Please note that the use of the word "master" is the MusicBrainz term and is not intended to be gender-specific. Users can specify whatever text they please.

5. "Lyrics". **Please note that this section operates on the underlying input file tags, not the Picard-generated tags (MusicBrainz does not have lyrics)**
  Sometimes "lyrics" tags can contain album notes (repeated for every track in an album) as well as track notes and lyrics. This section will filter out the common text for a release and place it in a different tag from the text which is unique to each track.

   "Split lyrics tag": enables this section.

   "Incoming lyrics tag": The name of the lyrics file tag in the input file (normally just 'lyrics').

   "Tag for album notes": The name of the tag where common text should be placed.

   "Tag for track notes": The name of the tag where notes/lyrics unique to a track should be placed.

   Note that if the 'output' tags are not specified, then internal 'hidden' variables will still be available for use in the tag-mapping section (called album_notes and track_notes).

## Tag mapping tab
There are three coloured sections as shown in the screen image below:

![Tag mapping options](https://i.imgur.com/XKhm0kb.jpg)

Note that the "Create extra artist metadata" option needs to be selected on the Artist tab for these sections to run.

1. "Keep file tags": This refers to the tags which already exist on files which have been matched to MusicBrainz in the right-hand panel, not the tags generated by Picard from the MusicBrainz database. Normally, Picard cannot process these tags - either it will overwrite them (if it creates a similarly named tag), clear them (if 'Clear existing tags' is specified in the main Options->Tags screen) or keep them (if 'Preserve these tags...' is specified after the 'Clear existing tags' option). Classical Extras allows a further option - for the tags to be appended to in the tag mapping section (see below). List file tags which will be appended to rather than over-written by tag mapping (NB this will keep tags even if "Clear existing tags" is selected on main options). In addition, certain existing tags may be used by Classical Extras - in particular "is_classical" (which is set by SongKong to '1' if the track is deemed to be classical, based on an extensive database) is used to add 'classical' to the variable "_cea_worktype", if "Infer work types" is selected in the first section of the Artists tab.

   Note that if "Split lyrics tag" is specified (see the Artists tab), then the tag named there will be included in the 'Keep file tags' list and does not need to be added in this section.

2. "Remove Picard-generated tags before applying subsequent actions?". Any tags specified in the next two rows will be blanked before applying the tag sources described in the following section. NB this applies only to Picard-generated tags, not to other tags which might pre-exist on the file: to blank those, use the main Options->Tags page. Comma-separate the tag names within the rows and note that these names are case-sensitive.

3. "Tag mapping". This section permits the contents of any hidden variable or tag to be written to one or more tags.

    * **Sources**:
	Some of the most useful sources are available from the drop-down list. Otherwise they can simply be typed in the box. Click on the "source from" button to enable entry. Some useful names are:

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
      - leaders : AKA concertmasters.
      - chorusmasters : as distinct from conductors (chorus masters may rehearse the choir but not conduct the performance).

	   Note that the Classical Extras sources for all artist types are spelled in the plural (to differentiate from the native Picard tags). Most of the names are for artist data and are sourced from hidden variables (prefixed with "_cea_" or "_cwp_"). In specifying the source, the prefix is not necessary - e.g. "arrangers" will pick up all data in _cea_arrangers and _cwp_arrangers (covering those with recording and work relationships respectively). Using the prefix will only get the specific variable.

	   In addition, the drop-down contains some typical combinations of multiple sources (see note on multiple sources below).

       Any Picard tag names can also be typed in as sources. Any hidden variables may also be used. Any source names which are prefixed by a backslash will be treated as string constants; blanks may also be used.

       It is possible to specify multiple sources. If these are separated by a comma, then each will be appended to the mapped tag(s) (if not already filled or if not "conditional"). So, for example, a source of "album_soloists, album_conductors, album_ensembles" mapped to a tag of "artist" with "conditional" ticked will fill artist (if blanked) by album_soloists, if any, otherwise album_conductors etc. Sources separated by a + will be concatenated before being used to fill the mapped tags. The concatenated result **will only be applied if the contents of each of the sources to be concatenated is non-blank** (note that this constraint only applies to **concatenation** of multiple sources). No spaces will be added on concatenation, so these have to be added explicitly by concatenating "\ ".  So, for example "ensemble_names + \ (conducted by + conductors +\), ensemble_names", with "Conditional" selected, will yield something like "BBC Symphony Orchestra (conducted by Walter Weller)" or just "BBC Symphony Orchestra" if there is no conductor. **Do not use any commas in text strings**.

       Another example: to add the leader's name in brackets to the tag with the performing orchestra, put "\\ (leader +leaders+\\)" in the source box and the tag containing the orchestra in the tag box. If there is no leader, the text will not be appended.

     The tag mapping section is not restricted to artist metadata. For example, in the default drop-down list are "work_type" which only has content if the "Infer work types" box in the first section of the Artists tab is checked, and "release" which contains the album name before prefixing with composer last names if that option was chosen.

    * **Tags**:
	   Enter the (comma-separated) "destination" tag names into which the sources should be written (case sensitive). Note that this will result in the source data being APPENDED in the tag - it will not overwrite the existing contents. Check "Conditional?" if the tag is only to be updated if it is previously blank (all non-empty sources in the current line will be applied). The lines will be applied in the order shown. Users should be able to achieve most requirements via a combination of blanking tags, using the right source order and "conditional" flags. For example, to overwrite a tag sourced from "composer" with "conductor", specify "conductor" first, then "composer" as conditional. Note that, for example, to demote the MB-supplied artist to only appear if no other listed choices are present, blank the artist tag and then add it as a conditional source at the end of the list.

    * **"Also populate sort tags"**:
     If a sort tag is associated with the source tag then the sort names will be placed in a sort tag corresponding to the destination tag. Note that the only explicit sort tags written by Picard are for artist, albumartist and composer. Piacrd also writes hidden variables '_artists_sort' and 'albumartists_sort' (note the plurals - these are the sort tags for multi-valued alternatives 'artists' and '_albumartists'). To be consistent with this approach, the plugin writes hidden variables for other tags - e.g. '_arranger_sort'. The plugin also writes hidden sort variables for the various hidden artist variables - e.g. '_cwp_librettists' has a matching sort variable '_cwp_librettists_sort'. Therefore most artist-type sources **will** have a sort tag/variable associated with them and these will be placed in a destination sort tag if this option is selected - **in other words, selecting this option will cause most destination tags to have associated sort tags. Furthermore, any hidden sort variables associated with tags which are not listed explicitly in the tag mapping section will also be written out as tags** (i.e. even if the related tags are not included as destination tags). Note, however, that composite sources (e.g. " ensemble_names + \;  + conductors") do not have sort tags associated with them.

      If this option is not selected, no additional sort tags will be written, but the hidden variables will still be available, so if a sort tag is required explicitly, just map the sort tag directly - e.g. map 'conductors_sort' to 'conductor_sort'.

  More complex operations can be built using tagger scripts. If required, these can be set to run conditionally by setting a tag or hidden variable in this section and then testing it in the script.

## Work and parts tab

There six coloured sections as shown in the screen print below:

![Works and parts options](https://i.imgur.com/Yv95BIR.jpg)

1. "Include all work levels" should be selected otherwise this section will not run. This is the default.

    "Include collection relationships" (selected by default) will include parent works where the relationship has the attribute 'part of collection'. See [Discussion](https://community.metabrainz.org/t/levels-in-the-structure-of-works/293047/109) for the background to this. Note that only "work" entity types will be included, not "series" entities. If this option is changed, it will not take effect on releases already loaded in Picard - you will need to quit and restart.

    "Use cache (if available)" prevents excessive look-ups of the MB database. Every look-up of a parent work needs to be performed separately (hopefully the MB database might make this easier some day). Network usage constraints by MB means that each look-up takes a minimum of 1 second. Once a release has been looked-up, the works are retained in cache, significantly reducing the time required if, say, the options are changed and the data refreshed. However, if the user edits the works in the MB database then the cache will need to be turned off temporarily for the refresh to find the new/changed works. Also some types of work (e.g. arrangements) will require a full look-up if options have been changed. **Do not leave this option turned off** as it will make the plugin slower and may cause problems. This option will always be set on when Picard is started, regardless of how it was left when it was last closed.

2. "Tagging style". This section determines how the hierarchy of works will be sourced.

    * **Works source**: There are 3 options for determing the principal source of the works metadata
      - "Use only metadata from title text". The plugin will attempt to extract the hierarchy of works from the track title by looking for repetitions and patterns. If the title does not contain all the work names in the hierarchy then obviously this will limit what can be provided.
      - "Use only metadata from canonical works". The hierarchy in the MB database will be used. Assuming the work is correctly entered in MB, this should provide all the data. However the text may differ from the track titles and will be the same for all recordings. It may also be in the language of the composer whereas the titles will probably be in the language of the release. (This language issue can also be addressed by using aliases - see below).
      - "Use canonical work metadata enhanced with title text". This supplements the canonical data with text from the titles **where it is significantly different**. The supplementary title data will be in curly brackets. This is clearly the most complete metadata style of the three but may lead to long descriptions. It is particularly useful for providing translations - see image below for an example (using the Muso library manager).

      ![Respighi](http://i.imgur.com/QqulDPG.jpg)

    * **Source of canonical work text**. Where either of the second two options above are chosen, there is a further choice to be made:
      - "Full MusicBrainz work hierarchy". The names of each level of work are used to populate the relevant tags. E.g. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast, JB 1:112", not "Má vlast". So, while accurate, this option might be more verbose.
      - "Consistent with lowest level work description". The names of the level 0 work are used to populate the relevant tags. I.e. if "Má vlast: I. Vyšehrad, JB 1:112/1" (level 0) is part of "Má vlast, JB 1:112" (level 1) then the parent work will be tagged as "Má vlast", not "Má vlast, JB 1:112". This frequently looks better, but not always, **particularly if the level 0 work name does not contain all the parent work detail**. If the full structure is not implicit in the level 0 name then a warning will be logged and written to the "warning" tag.

   **Strategy for setting style:** *It is suggested that you start with "extended/enhanced" style and the "Consistent with lowest level work description" as the source (this is the default). If this does not give acceptable results, try switching to "Full MusicBrainz work hierarchy". If the "enhanced" details in curly brackets (from the track title) give odd results then switch the style to "canonical works" only. Any remaining oddities are then probably in the MusicBrainz data, which may require editing.*

3. "Aliases"

     "Replace work names by aliases" will use **primary** aliases for the chosen locale instead of standard MusicBrainz work names. To choose the locale, use the drop-down under "translate artist names" in the main Picard Options-->Metadata page. Note that this option is not saved as a file tag since, if different choices are made for different releases, different work names may be stored and therefore cannot be grouped together in your player/library manager. The sub-options then allow either the replacement of all work names, where a primary alias exists, just the replacement of work names which are in non-Latin script, or only replace those which are flagged with user "Folksonomy" tags. The tag text needs to be included in the text box, in which case flagged works will be 'aliased' as well as non-Latin script works, if the second sub-option is chosen. Note that the tags may either be anyone's tags ("Look in all tags") or the user's own tags. If selecting "Look in user's own tags only" you **must** be logged in to your MusicBrainz user account (in the Picard Options->General page), otherwise repeated dialogue boxes may be generated and you may need to force restart Picard.

4. "Tags to create" sets the names of the tags that will be created from the sources described above. All these tags will be blanked before filling as specified. Tags specified against more than one source will have later sources appended in the sequence specified, separated by separators as specified.

    * **Work tags**:
      - "Tags for Work - for software with 2-level capability". Some software (notably Muso) can display a 2-level work hierarchy as well as the work-movement hierarchy. This tag can be use to store the 2-level work name (a double colon :: is used to separate the levels within the tag).
      - "Tags for Work - for software with 1-level capability". Software which can display a movement and work (but no higher levels) could use any tags specified here. Note that if there are multiple work levels, the intermediate levels will not be tagged. Users wanting all the information should use the tags from the previous option (but it may cause some breaks in the display if levels change) - alternatively the missing work levels can be included in a movement tag (see below).
      - "Tags for top-level (canonical) work". This is the top-level work held in MB. This can be useful for cataloguing and searching (if the library software is capable).

    * **Movement/Part tags**:
      (a) "Tags for(computed) movement number". This is not necessarily the embedded movt/part number, but is the sequence number of the movement within its parent work **on the current release**.  
      (b) "Tags for Movement - excluding embedded movt/part numbers". As below, but without the movement part/number prefix (if applicable)  
      (c) "Tags for Movement - including embedded movt/part numbers". This tag(s) will contain the full lowest-level part name extracted from the lowest-level work name, according to the chosen tagging style.  
      For options (b) and (c), the tags can either be filled "for use with multi-level work tags" or "for use with 1-level work tags (intermediate works will prefix movement)" - or different tags for each column.  The latter option will include any intermediate work levels which are missing from a single-level work tag. Use different tag names for these, from the multi-level version, otherwise both versions will be appended, creating a multi-valued tag (a warning will be given).  
      Note that if a tag is included in (a) and either of (b) or (c), the movement number will be prepended at the beginning of the tag, followed by the selected separator.

   **Strategy for setting tags:** *It is suggested that initially you just use the multi-level work tag and related movement tags, even if your software only has a single-level work capability. This may result in work names being repeated in work headings, but may look better than the alternative of having work names repeated in movement names. This is the default.* 

   *If this does not look good you can then compare it with the alternative approach and change as required for specific releases. If your software does not have any "work" capability, then you can still get the full work details by, for example, specifying "title" as both a work and a movement tag.*

5. "Partial recordings, arrangements and medleys" gives various options where recordings are not just simply of a named complete work.

    * **Partial recordings**:
      If this option is selected, partial recordings will be treated as a sub-part of the whole recording and will have the related text (in the adjacent box) included in its name. Note that this text is at the end of the canonical name, but the latter will probably be stripped from the sub-part as it duplicates the recording work name; any title text will be appended to the whole. Note that, if "Consistent with lowest level work description" is chosen in section 2, the text may be treated as a "prefix" similar to those in the "Advanced" tab. If this eliminates other similar prefixes and has unwanted effects, then either change the desired text slightly (e.g. surround with brackets) or use the "Full MusicBrainz work hierarchy" option in section 2.  Note that similar text between the partial work and its 'parent' will be removed which will frequently result in no text other than the specified 'partial text', unless extended metadata is used resulting in appended text in {}.

    * **Arrangements**:
      If this option is selected, works which are arrangements of other works will have the latter treated in the same manner as "parent" works, except that the arrangement work name will be prefixed by the text provided. Note that similar text between the arranged work and its parent will be removed unless this results in no text, in which case a stricter comparison (as for the derivation of 'part' names from works) will be used.
      
    **Important note:** *If the Partial or Arrangement options are changed (i.e. selected/deselected) then quit and restart Picard as the work structure is fundamentally different. If the related text (only) is changed then the release can simply be refreshed.*

    * **Medleys**
      These can occur in two ways in MusicBrainz: (a) the recording is described as a "medley of" a number of works and (b) the track is described as (more than one) "medley including a recording of" a work. See [Homecoming](https://musicbrainz.org/release/393913a2-7fde-4ed5-8be6-ca5c2c0ccf0d) for examples of both (tracks 8, 9 and 11). In the first case, the specified text will be included in brackets after the work name, whereas in the second case, the track will be treated as a recording of multiple works and the specified text will appear in the parent work name.

6. "SongKong-compatible tag usage".

    "Use work tags on file (no look up on MB) if Use Cache selected": This will enable the existing work tags on the file to be used in preference to looking up on MusicBrainz, if those tags are SongKong-compatible (which should be the case if SongKong has been used or if the SongKong tags have been previously written by this plugin). If present, this can speed up processing considerably, but obviously any new data on MusicBrainz will be missed. For the option to operate, "Use cache" also needs to be selected. Although faster, some of the subtleties of a full look-up will be missed - for example, parent works which are arrangements will not be highlighted as such, some arrangers or composers of original works may be omitted and some medley information may be missed. **In general, therefore, the use of this option will result in poorer metadata than allowing the full database look-up to run. It is not recommended unless speed is more important than quality.**

    "Write SongKong-compatible work tags" does what it says. These can then be used by the previous option, if the release is subsequently reloaded into Picard, to speed things up (assuming the reload was not to pick up new work data).

    The default for both these options is unchecked.

    Note that Picard and SongKong use the tag musicbrainz_workid to mean different things. If Picard has overwritten the SongKong tag (not a problem if this plugin is used) then a warning will be given and the works will be looked up on MusicBrainz. Also note that once a release is loaded, subsequent refreshes will use the cache (if option is ticked) in preference to the file tags.

**Note for iTunes users:** *iTunes and Picard do not work well together. iTunes can display work and movement for m4a(mp4) files, but Picard does not write the movement tag. To work round this, write the movement to the "subtitle" tag assuming that is not otherwise used, and use a simple Mp3tag action to convert it to MOVEMENTNAME before importing to iTunes. If you are writing to a FLAC file which will subsequently be converted to m4a then different tag names may be required; e.g. using dBpoweramp, write the movement to "movement name". In both cases use "work" for the work. To store the top_work, use "grouping" if writing directly to m4a, but "style" if writing to FLAC followed by dBpoweramp conversion. You can put multiple tags into the boxes described above so that your options are multi-purpose. N.B. if work tags are specified and the work has at least one level (i.e. at least work: movement), then the tag "show work movement" will be set to 1. This is used by iTunes to trigger the hierarchical display and should work both directly with m4a files and indirectly via files which are subsequently converted.*

## Advanced tab

Hopefully, this tab should not be much used. In any case, it should not need to be changed frequently. There are five sections as shown in the sceeen print below:

![Advanced options](https://i.imgur.com/H2YLAmA.jpg)

1. "Artists". This has only one subsection - "Ensemble strings" - which permits the listing of strings by which ensembles of different types may be identified. This is used by the plugin to place performer details in the relevant hidden variables and thus make them available for use in the "Tag mapping" tab as sources for any required tags. 
If it is important that only whole words are to be matched, be sure to include a space after the string.

2. "Work levels". This section has parameters applicable to the "works and parts" functions.

	* **Max number of re-tries to access works (in case of server errors)**. Sometimes MB lookups fail. Unfortunately Picard (currently) has no automatic "retry" function. The plugin will attempt to retry for the specified number of attempts. If it still fails, the hidden variable _cwp_error will be set with a message; if error logging is checked in section 4, an error message will be written to the log and the contents of _cwp_error will be written out to a special tag called "001_errors" which should appear prominently in the bottom pane of Picard. The problem may be resolved by refreshing, otherwise there may be a problem with the MB database availability. It is unlikely to be a software problem with the plugin.

	* **How title metadata should be included in extended metadata**. This subsection contains various parameters affecting the processing of strings in titles. Because titles are free-form, not all circumstances can be anticipated. Detailed documentation of these is beyond the scope of this Readme as the effects can be quite complex and subtle and may require an understanding of the plugin code (which is of course open-source) to acsertain them. If pure canonical works are used ("Use only metadata from canonical works" and, if necessary, "Full MusicBrainz work hierarchy" on the Works and parts tab, section 2) then this processing should be irrelevant, but no text from titles will be included. Some explanations are given below:

  "Proximity of new words". When using extended metadata - i.e. "metadata enhanced with title text", the plugin will attempt to remove similar words in the canonical work name (in MusicBrainz) and the title before extending the canonical name. After removing such words, a rather "bitty" result may occur. To avoid this, any new words with the specified proximity will have the words between them (or up to the end) included even if they repeat words in the work name.

  "Prefixes". When using "metadata from titles" or extended metadata, the structure of the works in MusicBrainz is used to infer the structure in the title text, so strings that are repeated between tracks which are part of the same MusicBrainz work will be treated as "higher level". This can lead to anomalies if, for instance, the titles are "Work name: Part 1", "Work name: Part 2", "Part" will be treated as part of the parent work name. Specifying such words in "Prefixes" will prevent this.

  "Synonyms". These words will be considered equivalent when comparing work name and title text. Thus if one word appears in the work name, that and its synonym will be removed from the title in extending the metadata (subject to the proximity setting above).

  "Replacements". These words/phrases will be replaced in the title text in extended metadata, regardless of the text in the work name.


3. "Logging options". These options are in addition to the options chosen in Picard's "Help->View error/debug log" settings. They only affect messages written by this plugin. To enable debug messages to be shown, the flag needs to be set here and "Debug mode" needs to be turned on in the log. **It is strongly advised to keep the "debug" and "info" flags unchecked unless debugging is required** as they slow up processing significantly and may even cause Picard to crash on large releases - do not load multiple releases with them turned on or Picard will almost certainly hang. The "debug" and "info" flags will always be off when Picard is first started, regardless of how they were left when it was last closed. The "error" and "warning" flags should be left checked, unless it is required to suppress messages written out to tags (the messages are also written to the tags 001_errors and 002_warnings).

4. "Save plugin details and options in a tag?" can be used so that the user has a record of the version of Classical Extras which generated the tags and which options were selected to achieve the resulting tags. Note that the tags will be blanked first so this will only show the last options used on a particular file. The same tag can be used for both sets of options, resulting in a multi-valued tag. 

   The tag contents are in dict format. These tags can then be used to over-ride the displayed options subsequently (see below).

5. "Over-ride plugin options displayed in UI with options from local file tags". If options have previously been saved (see above), selecting these will cause the saved options to be used in preference to the displayed options. The displayed options will not be affected and will be used if no saved options are present. The default is for no over-ride. ***Note that very occasionally (if the tag containing the options has been corrupted) use of this option may cause an error. In such a case you will need to deselect the "over-ride" option and set the required options manually; then save the resulting tags and the corrupted tag should be over-written***

   The last checkbox, "Overwrite options in Options Pages", is for **VERY CAREFUL USE ONLY**. It will cause any options read from the saved tags (if the relevant box has been ticked) to over-write the options on the plugin Options Page UI. The intended use of this is if for some reason the user's preferred options have been erased/reverted to default - by using this option, the previously-used choices from a reliable filed album can be used to populate the Options Page. The box will automatically be unticked after loading/refreshing one album, and will always be turned off when starting Picard, to prevent inadvertant use. Far better is to make a **backup copy** of the picard.ini file.

# Information on hidden variables

This section is for users who want to write their own scripts. The definition and source of each hidden variable is listed. Apologies if there are errors and omissions in this section - to double check the actual hidden variables, use the plugin "View script variables".

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

If there is more than one work any level, then _cwp_work_n and _cwp_workid_n will have multiple entries. Another common situation is that a "bottom level" work is spread across more than one track. Rather than artificially split the work into sub-parts, this is often shown in MusicBrainz as a track being a "partial recording of" a work. The plugin deals with this by creating a notional lowest-level with the suffix " (part)" appended to the work it is a partial recording of. In order that this notional part can be separately identified from the full work, the musicbrainz_recordingid is used as the identifier rather than the workid.
If there is more than one "parent" work of a lower level work, multi-valued tags are generated.

- _cwp_X0_part_0 : A "stripped" version of _cwp_work_0 (see above), where elements of _cwp_work_0 which repeat within level 1 have been stripped.
- _cwp_X0_work_n : The elements of _cwp_work_0 which repeat within level n

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

Artist tags which derive from work-artist relationships are also set in this section:
- _cwp_composers
- _cwp_writers
- _cwp_arrangers : This is for arrangers of the work and also "instrument arrangers" and "vocal arrangers" with appropriate annotation for instrument and voice types. (Picard does not currently write the latter to the Arranger tag if they are part of the work-artists relationship, despite style guidance saying to use specific instrument types instead of generic arranger.) 
- _cwp_orchestrators
- _cwp_reconstructors - 'reconstructed by' relationships
- _cwp_revisors - 'revised by' relationships
- _cwp_lyricists
- _cwp_librettists
- _cwp_translators

Finally, the tags _cwp_error and_cwp_warning are provided to supply warnings and error messages to the user.

## Artists

All the additional hidden variables for artists written by Classical Extras are prefixed by _cea_. Note that these are generally in the plural, whereas the standard tags are singular. If the user blanks a tag then the original value is stored in the singular with the _cea_ prefix. Thus _cea_arranger would be the contents of the Picard tag "arranger" before blanking, whereas _cea_arrangers is hidden variable created by Classical Extras.

- _cea_recording_artist : The artist credited with the recording (not necessarily the track artist). Note that this is the only "_cea_" tag which is singular, because it is in the same format as the 'artist' tag, whereas...
- _cea_recording_artists : The list/multiple value version of the above. (This follows the approach in Picard for 'artist' and 'artists', being the track artists.)
- _cea_MB_artists: The original track artists per MusicBrainz before any replacement by / merging with recording artists.
- _cea_soloists : List of performers (with instruments in brackets), who are NOT ensembles or conductors, separated by semi-colons. Note they may not strictly be "soloists" in that they may be part of an ensemble.
- _cea_recording_artistsort : Sort names of _cea_recording_artist
- _cea_recording_artists_sort : Sort names of _cea_recording_artists
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
- _cea_arrangers : All arrangers for the **recording** with instrument/voice type in brackets, if provided. If the work and parts functionality has also been selected, the arrangers of works, which Picard also currently omits will be put in _cwp_arrangers.
- _cea_orchestrators : Arrangers (per Picard) included in the MB database as type "orchestrator".
- _cea_chorusmasters : A person who (per Picard) is a conductor, but is "chorus master" in the MB database (i.e. not necessarily conducting the performance).
- _cea_leaders : The leader of the orchestra ("concertmaster" in MusicBrainz) - not created by Picard as standard. 
- _cea_work_type : Although not strictly an artist field, this is derived from artist and performer metadata. This is the variable populated if "Infer work types" is selected on the Artists tab.

# Software-specific notes

Note that _cwp_part_levels > 0 will indicate that the track recording is part of a work and so could be used to set other software-specific flags (e.g. for iTunes "show work movement") to indicate a multi-level "work: movement".

## SongKong

SongKong users may wish to map the _cwp variables to tags produced by SongKong if consistency is desired, in which case the mappings are principally:
- _cwp_work_0 => musicbrainz_work_composition
- _cwp_workid_0 => musicbrainz_work_composition_id
- _cwp_work_n => musicbrainz_work_part_leveln, for n = 1..6
- _cwp_workid_n => musicbrainz_work_part_leveln_id, for n = 1..6
- _cwp_work_top => musicbrainz_work

These mappings are carried out automatically if the relevant options on the "Work and parts" tab are selected.  
In addition, _cwp_title_work and _cwp_title_part_0 are intended to be equivalent to SongKong's work and part tags.
(N.B. Full consistency between SongKong and Picard may also require the modification of Artist and related tags via a script, or the preservation of the related file tags)

## Muso

The tag "groupheading" should be set as the "Tags for Work - for software with 2-level capability". Muso will use this directly and extract the levels from it (split by the double colon). Muso permits a variety of import options which should be capable of combination with the tagging options in this plugin to achieve most desired effects. To avoid the use of import options in Muso, set the output tags from the plugin to be the native ones used by Muso (NB "title" may include or exclude groupheading - Muso should recognise it and extract it).

## Players with no "work" capability

Leave the "title" tag unchanged or make it a combination of work and movement.


# Possible Enhancements
Planned enhancements (among others) are 
1. Include information regarding dates (e.g. date composed, recording date).
2. Improved genre capability, possibly with specific tags for instruments and periods.

# Technical Matters
Issues were encountered with the Picard API in that there is not a documented way to let Picard know that it is still doing asynchronous tasks in the background and has not finished processing metadata. Many thanks to @dns_server for assistance in dealing with this and to @sophist for the albumartist_website code which I have borrowed from. I have tried to add some more comments to help any others trying the same techniques.

Also, the documentation of the XML lookup (tagger.xmlws) is virtually non-existent. The response is an XmlNode object (not a dict, although it is represented as one). Each node has a name with {attribs, text, children} values. The structure is more clearly understood if the web-based lookup is used (which is well documented at https://musicbrainz.org/doc/Development/XML_Web_Service/Version_2) as this gives an XML response. I wrote a function (parse_data) to parse XmlNode objects, or lists thereof, for a (parameterised) hierarchy of nodes (and optional attribs value tests) in order to extract required data from the response. This may be of use to other plugin authors.

To get the whole picture, in XML, for a release, use (for example) https://musicbrainz.org/ws/2/release/f3bb4fdd-5db0-43a8-be73-7a1747f6c2ef?inc=release-groups+media+recordings+artist-credits+artists+aliases+labels+isrcs+collections+artist-rels+release-rels+url-rels+recording-rels+work-rels+recording-level-rels+work-level-rels. This simulates the response given by Picard with the "Use release relationships" and "Use track relationships" options selected. Note that the Picard album_metadata_processor returns releaseXmlNode which is everything from the Release node of the XML downwards, whereas track_metadata_processor returns trackXmlNode which is everything from a Track node downwards (release -> medium-list -> medium -> track-list is above track). Replace all hyphens in XML with underscores when parsing the Python object.

A large variety of releases were used to test this plugin, but there may still be bugs, so further testing is welcome. The following release was particularly complex and useful for testing: https://musicbrainz.org/release/ec519fde-94ee-4812-9717-659d91be11d4