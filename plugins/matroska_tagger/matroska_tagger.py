# -*- coding: utf-8 -*-

PLUGIN_NAME = "Matroska Tagger"
PLUGIN_AUTHOR = "Ben McLean"
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = [
	"2.0",
	"2.1",
	"2.2",
	"2.3",
	"2.4",
	"2.5",
	"2.6",
	"2.7",
	"2.8",
	"2.9",
	"2.10",
	"2.11",
	"2.12",
	"2.13",
]
PLUGIN_DESCRIPTION = (
	"Adds support for reading and writing tags in Matroska (.mkv, .mka) files via MKVToolNix "
	"(https://mkvtoolnix.download)."
)
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

import json
import os
import subprocess
import sys
import tempfile
from picard import config, log
from picard.config import BoolOption, TextOption
from picard.file import File
from picard.formats import register_format
from picard.metadata import Metadata
from picard.ui.options import register_options_page, OptionsPage

from PyQt5.QtWidgets import (
	QCheckBox,
	QFileDialog,
	QFormLayout,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QVBoxLayout,
)
from PyQt5.QtCore import (
	QBuffer,
	QFile,
	QIODevice,
	QXmlStreamReader,
	QXmlStreamWriter,
	Qt,
)

_AlignTop = Qt.AlignTop


# ---------------------------------------------------------------------------
# Tag mappings
# ---------------------------------------------------------------------------

# Picard internal name → Matroska tag name, for track-level tags (TargetTypeValue=30)
_TRACK_TAGS = {
	"title": "TITLE",
	"artist": "ARTIST",
	"comment": "COMMENT",
	"lyrics": "LYRICS",
	"isrc": "ISRC",
	"bpm": "BPM",
	"key": "INITIAL_KEY",
	"language": "LANGUAGE",  # undocumented in spec but used by MP3Tag
	"subtitle": "SUBTITLE",
	"remixer": "REMIXED_BY",
	"conductor": "CONDUCTOR",
	"lyricist": "LYRICIST",
	"composer": "COMPOSER",
	"engineer": "SOUND_ENGINEER",
	"mixer": "MIXED_BY",
	"djmixer": "DJMIXED_BY",
	"producer": "PRODUCER",
	"mood": "MOOD",
	"artists": "ARTISTS",
	"grouping": "GROUPING",
	# titlesort/artistsort/composersort emitted as SORT_WITH nested inside TITLE/ARTIST/COMPOSER
	"website": "WEBSITE",
	"license": "LICENSE",
	"copyright": "COPYRIGHT",
	# originalartist emitted as ORIGINAL/ARTIST nested structure
	"musicbrainz_recordingid": "MUSICBRAINZ_TRACKID",
	"musicbrainz_trackid": "MUSICBRAINZ_RELEASETRACKID",
	"musicbrainz_workid": "MUSICBRAINZ_WORKID",
	"musicbrainz_artistid": "MUSICBRAINZ_ARTISTID",
	"musicbrainz_composerid": "MUSICBRAINZ_COMPOSERID",
	"musicbrainz_originalartistid": "MUSICBRAINZ_ORIGINALARTISTID",
	"acoustid_id": "ACOUSTID_ID",
	"acoustid_fingerprint": "ACOUSTID_FINGERPRINT",
	"replaygain_track_gain": "REPLAYGAIN_GAIN",
	"replaygain_track_peak": "REPLAYGAIN_PEAK",
	"replaygain_track_range": "REPLAYGAIN_TRACK_RANGE",
	"genre": "GENRE",
}

# Picard internal name → Matroska tag name, for album-level tags (TargetTypeValue=50)
_ALBUM_TAGS = {
	"album": "TITLE",
	"albumartist": "ARTIST",
	"date": "DATE_RELEASED",
	"label": "LABEL",
	"catalognumber": "CATALOG_NUMBER",
	"barcode": "BARCODE",
	"script": "SCRIPT",
	"media": "ORIGINAL_MEDIA_TYPE",
	"releasestatus": "RELEASE_STATUS",
	"releasecountry": "RELEASE_COUNTRY",
	"releasetype": "RELEASE_TYPE",
	"asin": "ASIN",
	"compilation": "COMPILATION",
	# albumsort/albumartistsort emitted as SORT_WITH nested inside TITLE/ARTIST
	"musicbrainz_albumid": "MUSICBRAINZ_ALBUMID",
	"musicbrainz_releasegroupid": "MUSICBRAINZ_RELEASEGROUPID",
	"musicbrainz_albumartistid": "MUSICBRAINZ_ALBUMARTISTID",
	"musicbrainz_discid": "MUSICBRAINZ_DISCID",
	"musicbrainz_originalalbumid": "MUSICBRAINZ_ORIGINALALBUMID",
	"replaygain_album_gain": "REPLAYGAIN_GAIN",
	"replaygain_album_peak": "REPLAYGAIN_PEAK",
	"replaygain_album_range": "REPLAYGAIN_ALBUM_RANGE",
	"replaygain_reference_loudness": "REPLAYGAIN_REFERENCE_LOUDNESS",
}

# Picard internal name → Matroska tag name, for disc-level tags (TargetTypeValue=60)
_DISC_TAGS = {
	"discnumber": "PART_NUMBER",
	"totaldiscs": "TOTAL_PARTS",
}

# Sort companions: maps the main Picard field to its sort field, per level.
# These are emitted as SORT_WITH nested inside the parent Simple element.
_TRACK_SORT = {"title": "titlesort", "artist": "artistsort", "composer": "composersort"}
_ALBUM_SORT = {"album": "albumsort", "albumartist": "albumartistsort"}

# Reverse maps for loading: Matroska tag name → Picard internal name (per level)
_R_TRACK_TAGS = {v: k for k, v in _TRACK_TAGS.items()}
_R_ALBUM_TAGS = {v: k for k, v in _ALBUM_TAGS.items()}
_R_DISC_TAGS = {v: k for k, v in _DISC_TAGS.items()}

# All Picard internal tag names that this format can store.
_SUPPORTED_TAGS = (
    set(_TRACK_TAGS)
    | set(_ALBUM_TAGS)
    | set(_DISC_TAGS)
    | set(_TRACK_SORT.values())   # titlesort, artistsort, composersort
    | set(_ALBUM_SORT.values())   # albumsort, albumartistsort
    | {"tracknumber", "totaltracks", "originalartist", "originaldate"}
)


# ---------------------------------------------------------------------------
# Tool path helpers
# ---------------------------------------------------------------------------


def _tool_path(name, tooldir):
	"""Return the full path to a MKVToolNix executable."""
	if sys.platform == "win32":
		name = name + ".exe"
	if tooldir:
		return os.path.join(tooldir, name)
	return name  # rely on PATH


def _subprocess_flags():
	"""Return extra kwargs for subprocess.run to suppress console windows on Windows."""
	flags = {}
	if sys.platform == "win32":
		flags["creationflags"] = subprocess.CREATE_NO_WINDOW
	return flags


def _run(args, **kwargs):
	"""Run a subprocess, returning CompletedProcess. Raises on non-zero exit."""
	log.debug("MkvPlugin: running %r", args)
	already_captured = "capture_output" in kwargs or "stdout" in kwargs
	if not already_captured:
		kwargs["capture_output"] = True
	result = subprocess.run(args, check=True, **_subprocess_flags(), **kwargs)
	if not already_captured:
		if result.stdout:
			for line in result.stdout.decode("utf-8", errors="replace").splitlines():
				log.debug("MkvPlugin stdout: %s", line)
		if result.stderr:
			for line in result.stderr.decode("utf-8", errors="replace").splitlines():
				log.debug("MkvPlugin stderr: %s", line)
	return result


def _get_tooldir():
	return config.setting["mkvtoolnix_dir"].strip()


# ---------------------------------------------------------------------------
# XML generation (Picard Metadata → Matroska tags XML)
# ---------------------------------------------------------------------------


def _write_simple(w, name, value):
	w.writeStartElement("Simple")
	w.writeTextElement("Name", name)
	w.writeTextElement("String", str(value))
	w.writeEndElement()


def _write_simple_with_sort(w, name, value, sort_value=None):
	"""Write a Simple element, with an optional nested SORT_WITH child."""
	w.writeStartElement("Simple")
	w.writeTextElement("Name", name)
	w.writeTextElement("String", str(value))
	if sort_value:
		w.writeStartElement("Simple")
		w.writeTextElement("Name", "SORT_WITH")
		w.writeTextElement("String", str(sort_value))
		w.writeEndElement()
	w.writeEndElement()


def _write_original_artist(w, value):
	"""Write originalartist as a nested ORIGINAL/ARTIST structure per spec."""
	w.writeStartElement("Simple")
	w.writeTextElement("Name", "ORIGINAL")
	w.writeStartElement("Simple")
	w.writeTextElement("Name", "ARTIST")
	w.writeTextElement("String", str(value))
	w.writeEndElement()
	w.writeEndElement()


def _sort_field_for(mkv_name, target_type_value):
	"""Return the Picard sort field for a SORT_WITH element nested under mkv_name."""
	if target_type_value < 50:
		return {
			"TITLE": "titlesort",
			"ARTIST": "artistsort",
			"COMPOSER": "composersort",
		}.get(mkv_name)
	if target_type_value < 60:
		return {"TITLE": "albumsort", "ARTIST": "albumartistsort"}.get(mkv_name)
	return None


def _tags_xml(metadata):
	"""Combined XML with level-50 (album), level-60 (disc), and level-30 (track) Tag blocks.

	All blocks have no UID in their Targets, which is the spec-correct form for
	a single-track file.  mkvpropedit writes them via --tags global:, and FFmpeg
	routes all no-UID tags to s->metadata regardless of TargetTypeValue.

	Because the level-30 block is written last, level-30 TITLE/ARTIST overwrite
	the level-50 values in fctx->metadata — giving Kodi the track title and track
	artist in its title/artist fields as desired.

	ALBUM, ALBUM_ARTIST, and DATE are Kodi compatibility aliases.  They have no
	level-30 counterparts, so they survive in fctx->metadata after level-30
	processing.  Kodi reads these case-insensitively and maps them to its album,
	albumartist, and date fields respectively.

	TargetType string is omitted from all blocks: FFmpeg uses it as a key prefix
	on global tags (e.g. "ALBUM/TITLE"), which breaks Kodi's exact-match lookup.
	TargetTypeValue is still written for spec-compliant readers.
	"""
	buf = QBuffer()
	buf.open(QIODevice.WriteOnly)
	w = QXmlStreamWriter(buf)
	w.setAutoFormatting(True)
	w.writeStartDocument()

	w.writeStartElement("Tags")

	# --- Level 50: album ---
	w.writeStartElement("Tag")
	w.writeStartElement("Targets")
	w.writeTextElement("TargetTypeValue", "50")
	w.writeEndElement()  # Targets
	for picard_name, mkv_name in _ALBUM_TAGS.items():
		sort_key = _ALBUM_SORT.get(picard_name)
		sort_val = metadata.get(sort_key, "") if sort_key else ""
		for value in metadata.getall(picard_name):
			if value:
				_write_simple_with_sort(w, mkv_name, value, sort_val or None)
	for value in metadata.getall("totaltracks"):
		if value:
			_write_simple(w, "TOTAL_PARTS", value)
	# Kodi compat aliases: no level-30 equivalents so they persist in fctx->metadata
	for value in metadata.getall("album"):
		if value:
			_write_simple(w, "ALBUM", value)
	for value in metadata.getall("albumartist"):
		if value:
			_write_simple(w, "ALBUM_ARTIST", value)
	_date_field = "originaldate" if config.setting["mkv_use_original_date"] else "date"
	for value in metadata.getall(_date_field):
		if value:
			_write_simple(w, "DATE", value)
	w.writeEndElement()  # Tag (album)

	# --- Level 60: disc (omitted when no disc data is present) ---
	disc_num = metadata.get("discnumber", "")
	total_discs = metadata.get("totaldiscs", "")
	if disc_num or total_discs:
		w.writeStartElement("Tag")
		w.writeStartElement("Targets")
		w.writeTextElement("TargetTypeValue", "60")
		w.writeEndElement()  # Targets
		if disc_num:
			_write_simple(w, "PART_NUMBER", disc_num)
		if total_discs:
			_write_simple(w, "TOTAL_PARTS", total_discs)
		w.writeEndElement()  # Tag (disc)

	# --- Level 30: track ---
	w.writeStartElement("Tag")
	w.writeStartElement("Targets")
	w.writeTextElement("TargetTypeValue", "30")
	w.writeEndElement()  # Targets
	for picard_name, mkv_name in _TRACK_TAGS.items():
		sort_key = _TRACK_SORT.get(picard_name)
		sort_val = metadata.get(sort_key, "") if sort_key else ""
		for value in metadata.getall(picard_name):
			if value:
				_write_simple_with_sort(w, mkv_name, value, sort_val or None)
	for value in metadata.getall("originalartist"):
		if value:
			_write_original_artist(w, value)
	for value in metadata.getall("tracknumber"):
		if value:
			_write_simple(w, "PART_NUMBER", value)
	w.writeEndElement()  # Tag (track)

	w.writeEndElement()  # Tags
	w.writeEndDocument()
	buf.close()
	return bytes(buf.data()).decode("utf-8")


# ---------------------------------------------------------------------------
# XML parsing (Matroska tags XML → Picard Metadata)
# ---------------------------------------------------------------------------


def _parse_tags_xml(xml_path, metadata):
	"""Read a Matroska tags XML file and populate a Metadata object."""
	f = QFile(xml_path)
	if not f.open(QIODevice.ReadOnly):
		log.warning("MkvPlugin: failed to open tags XML %r", xml_path)
		return

	reader = QXmlStreamReader(f)
	target_type_value = 50
	in_tag = False
	in_targets = False
	in_ttv = False
	ttv_text = ""
	# Stack of open Simple elements; each frame: {name, value, reading_name, reading_string}
	simple_stack = []

	while not reader.atEnd():
		token = reader.readNext()
		if token == QXmlStreamReader.StartElement:
			el = reader.name()
			if el == "Tag":
				in_tag = True
				target_type_value = 50
			elif el == "Targets" and in_tag:
				in_targets = True
			elif el == "TargetTypeValue" and in_targets:
				in_ttv = True
				ttv_text = ""
			elif el == "Simple" and in_tag:
				simple_stack.append(
					{
						"name": "",
						"value": "",
						"reading_name": False,
						"reading_string": False,
					}
				)
			elif el == "Name" and simple_stack:
				simple_stack[-1]["reading_name"] = True
			elif el == "String" and simple_stack:
				simple_stack[-1]["reading_string"] = True
		elif token == QXmlStreamReader.EndElement:
			el = reader.name()
			if el == "Tag":
				in_tag = False
				simple_stack.clear()
			elif el == "Targets":
				in_targets = False
			elif el == "TargetTypeValue":
				in_ttv = False
				try:
					target_type_value = int(ttv_text)
				except ValueError:
					pass
			elif el == "Name" and simple_stack:
				simple_stack[-1]["reading_name"] = False
			elif el == "String" and simple_stack:
				simple_stack[-1]["reading_string"] = False
			elif el == "Simple" and simple_stack:
				frame = simple_stack.pop()
				mkv_name = frame["name"].upper()
				value = frame["value"]

				if simple_stack:
					# Nested Simple: handle SORT_WITH and ORIGINAL/ARTIST
					parent_name = simple_stack[-1]["name"].upper()
					if mkv_name == "SORT_WITH" and value:
						sort_field = _sort_field_for(parent_name, target_type_value)
						if sort_field:
							metadata.add(sort_field, value)
					elif parent_name == "ORIGINAL" and mkv_name == "ARTIST" and value:
						metadata.add("originalartist", value)
				else:
					# Top-level Simple
					if target_type_value >= 60:
						if value and mkv_name in _R_DISC_TAGS:
							metadata.add(_R_DISC_TAGS[mkv_name], value)
					elif target_type_value >= 50:
						if value:
							if mkv_name == "TOTAL_PARTS":
								metadata.add("totaltracks", value)
							elif mkv_name in _R_ALBUM_TAGS:
								metadata.add(_R_ALBUM_TAGS[mkv_name], value)
					else:
						if mkv_name == "PART_NUMBER":
							if value:
								if "/" in value:
									parts = value.split("/", 1)
									metadata.add("tracknumber", parts[0].strip())
									metadata.add("totaltracks", parts[1].strip())
								else:
									metadata.add("tracknumber", value)
						elif value and mkv_name in _R_TRACK_TAGS:
							metadata.add(_R_TRACK_TAGS[mkv_name], value)

		elif token == QXmlStreamReader.Characters:
			text = reader.text()
			if in_ttv:
				ttv_text += text
			elif simple_stack:
				frame = simple_stack[-1]
				if frame["reading_name"]:
					frame["name"] += text
				elif frame["reading_string"]:
					frame["value"] += text

	f.close()
	if reader.hasError():
		log.warning(
			"MkvPlugin: failed to parse tags XML %r: %s", xml_path, reader.errorString()
		)


# ---------------------------------------------------------------------------
# Matroska file format base class
# ---------------------------------------------------------------------------


class _MatroskaFileBase(File):
	"""
	Handles both reading and writing of Matroska tags via MKVToolNix.

	_load()  uses mkvmerge --identify for duration/codec info and mkvextract tags for existing tag values.
	_save()  generates a Matroska tags XML and feeds it to mkvpropedit.
	"""

	@classmethod
	def supports_tag(cls, name):
		return name in _SUPPORTED_TAGS

	def _load(self, filename):
		log.debug("MkvPlugin: loading %r", filename)
		tooldir = _get_tooldir()
		metadata = Metadata()

		# Read file info (duration, codec) via mkvmerge --identify
		mkvmerge = _tool_path("mkvmerge", tooldir)
		try:
			result = _run(
				[mkvmerge, "--identify", "--identification-format", "json", filename],
				capture_output=True,
				text=True,
				encoding="utf-8",
			)
			info = json.loads(result.stdout)
			duration_ns = (
				info.get("container", {}).get("properties", {}).get("duration", 0)
			)
			if duration_ns:
				metadata.length = duration_ns // 1_000_000  # ns → ms
		except FileNotFoundError:
			raise Exception(
				f"mkvmerge not found at {mkvmerge!r}. "
				"Install MKVToolNix and set the folder path in "
				"Options > Plugins > Matroska Tagger."
			)
		except subprocess.CalledProcessError as e:
			log.warning("MkvPlugin: mkvmerge failed on %r: %s", filename, e)
		except (json.JSONDecodeError, KeyError) as e:
			log.warning(
				"MkvPlugin: could not parse mkvmerge output for %r: %s", filename, e
			)

		# Read existing tags via mkvextract tags
		mkvextract = _tool_path("mkvextract", tooldir)
		tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xml", prefix="picard_mkv_")
		os.close(tmp_fd)
		try:
			# mkvextract returns 0 (clean) or 1 (warnings but still valid output).
			# check=True would treat exit code 1 as failure, so we check manually.
			result = subprocess.run(
				[mkvextract, filename, "tags", tmp_path],
				capture_output=True,
				**_subprocess_flags(),
			)
			if result.returncode >= 2:
				raise subprocess.CalledProcessError(result.returncode, result.args)
			if os.path.getsize(tmp_path) > 0:
				_parse_tags_xml(tmp_path, metadata)
		except FileNotFoundError:
			raise Exception(
				f"mkvextract not found at {mkvextract!r}. "
				"Install MKVToolNix and set the folder path in "
				"Options > Plugins > Matroska Tagger."
			)
		except subprocess.CalledProcessError as e:
			log.warning("MkvPlugin: mkvextract failed on %r: %s", filename, e)
		finally:
			try:
				os.unlink(tmp_path)
			except OSError:
				pass

		return metadata

	def _save(self, filename, metadata):
		log.debug("MkvPlugin: saving %r", filename)
		tooldir = _get_tooldir()
		mkvpropedit = _tool_path("mkvpropedit", tooldir)

		tags_xml = _tags_xml(metadata)
		log.debug("MkvPlugin: tags XML: %s", tags_xml)

		tags_fd, tags_path = tempfile.mkstemp(suffix=".xml", prefix="picard_mkv_")
		try:
			with os.fdopen(tags_fd, "w", encoding="utf-8") as f:
				f.write(tags_xml)

			try:
				if config.setting["mkv_strip_chapters"]:
					_run([mkvpropedit, filename, "--chapters", ""])

				title = metadata.get("title", "")
				_run(
					[
						mkvpropedit,
						filename,
						"--edit",
						"info",
						"--set",
						f"title={title}",
						"--edit",
						"track:a1",
						"--set",
						f"name={title}",
						"--tags",
						"all:",
						"--tags",
						f"global:{tags_path}",
					]
				)
			except FileNotFoundError:
				raise Exception(
					f"mkvpropedit not found at {mkvpropedit!r}. "
					"Install MKVToolNix and set the folder path in "
					"Options > Plugins > Matroska Tagger."
				)
			except subprocess.CalledProcessError as e:
				raise Exception(f"mkvpropedit failed: {e}")
		finally:
			try:
				os.unlink(tags_path)
			except OSError:
				pass


# ---------------------------------------------------------------------------
# Concrete format classes — one per extension so Picard treats them separately
# ---------------------------------------------------------------------------


class MKVFile(_MatroskaFileBase):
	NAME = "Matroska Video (MKV)"
	EXTENSIONS = [".mkv"]


class MKAFile(_MatroskaFileBase):
	NAME = "Matroska Audio (MKA)"
	EXTENSIONS = [".mka"]


# ---------------------------------------------------------------------------
# Options page
# ---------------------------------------------------------------------------


class _MkvOptionsPage(OptionsPage):
	NAME = "matroska_tagger"
	TITLE = "Matroska Tagger"
	PARENT = "plugins"
	SORT_ORDER = 100

	def __init__(self, parent=None):
		super().__init__(parent)

		layout = QVBoxLayout(self)
		layout.setAlignment(_AlignTop)

		desc = QLabel(
			"Path to the folder containing MKVToolNix executables "
			"(mkvpropedit, mkvmerge, mkvextract). "
			"Leave empty to use the system PATH."
		)
		desc.setWordWrap(True)
		layout.addWidget(desc)

		form = QFormLayout()

		path_row = QHBoxLayout()
		self._path_edit = QLineEdit()
		if sys.platform == "win32":
			self._path_edit.setPlaceholderText(r"e.g. C:\Program Files\MKVToolNix")
		else:
			self._path_edit.setPlaceholderText("e.g. /usr/bin  (leave empty for PATH)")
		path_row.addWidget(self._path_edit)

		browse_btn = QPushButton("Browse…")
		browse_btn.clicked.connect(self._browse)
		path_row.addWidget(browse_btn)

		form.addRow("MKVToolNix folder:", path_row)
		layout.addLayout(form)

		test_row = QHBoxLayout()
		self._test_btn = QPushButton("Test")
		self._test_btn.clicked.connect(self._test_tools)
		test_row.addWidget(self._test_btn)
		self._test_label = QLabel("")
		test_row.addWidget(self._test_label)
		test_row.addStretch()
		layout.addLayout(test_row)

		self._strip_chapters_cb = QCheckBox("Remove chapter data when saving")
		layout.addWidget(self._strip_chapters_cb)

		self._use_original_date_cb = QCheckBox(
			"Use original release date as DATE tag (instead of this release's date)"
		)
		layout.addWidget(self._use_original_date_cb)

	def _browse(self):
		folder = QFileDialog.getExistingDirectory(
			self, "Select MKVToolNix folder", self._path_edit.text()
		)
		if folder:
			self._path_edit.setText(folder)

	def _test_tools(self):
		tooldir = self._path_edit.text().strip()
		results = []
		for name in ("mkvpropedit", "mkvmerge", "mkvextract"):
			path = _tool_path(name, tooldir)
			try:
				_run([path, "--version"], capture_output=True)
				results.append(f"✓ {name}")
			except FileNotFoundError:
				results.append(f"✗ {name} not found")
			except subprocess.CalledProcessError as e:
				results.append(f"✗ {name} error ({e.returncode})")
		self._test_label.setText("  ".join(results))

	def load(self):
		self._path_edit.setText(config.setting["mkvtoolnix_dir"])
		self._strip_chapters_cb.setChecked(config.setting["mkv_strip_chapters"])
		self._use_original_date_cb.setChecked(config.setting["mkv_use_original_date"])

	def save(self):
		config.setting["mkvtoolnix_dir"] = self._path_edit.text().strip()
		config.setting["mkv_strip_chapters"] = self._strip_chapters_cb.isChecked()
		config.setting["mkv_use_original_date"] = self._use_original_date_cb.isChecked()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def _default_tooldir():
	if sys.platform == "win32":
		prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
		candidate = os.path.join(prog_files, "MKVToolNix")
		if os.path.isdir(candidate):
			return candidate
	return ""


TextOption("setting", "mkvtoolnix_dir", _default_tooldir())
BoolOption("setting", "mkv_strip_chapters", False)
BoolOption("setting", "mkv_use_original_date", True)
register_format(MKVFile)
register_format(MKAFile)
register_options_page(_MkvOptionsPage)
log.info("MkvPlugin: Matroska Tagger enabled (MKV + MKA)")
