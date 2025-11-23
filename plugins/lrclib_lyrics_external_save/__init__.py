# -*- coding: utf-8 -*-

PLUGIN_NAME = "LRCLIB Lyrics External Save"
PLUGIN_AUTHOR = "Harmonese"
PLUGIN_DESCRIPTION = (
    "Fetch lyrics from LRCLIB based on track metadata after saving files, "
    "and write synced lyrics (.lrc) or plain lyrics (.txt) as external sidecar "
    "files in the same folder as the audio file. Does not modify audio tags."
)
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6"]
PLUGIN_LICENSE = "MIT"
PLUGIN_LICENSE_URL = "https://opensource.org/licenses/MIT"

import os
import json
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from picard import log
from picard.file import register_file_post_save_processor


LRCLIB_URL = "https://lrclib.net/api/get"


# ============================================================
# Build LRCLIB query from saved file metadata
# ============================================================

def _build_query_from_file(file):
    """
    Extract metadata from file.metadata (after the file is saved) and
    build a LRCLIB query dictionary.
    """
    md = file.metadata

    title = md.get("title")
    artist = md.get("artist")
    album = md.get("album")
    duration = None

    # Use ~length (mm:ss) as duration information
    length_str = md.get("~length")
    if length_str:
        try:
            parts = length_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                duration = minutes * 60 + seconds
        except Exception as exc:
            log.info(
                "LRCLIB SIMPLE: Failed to parse ~length %r: %r",
                length_str, exc,
            )

    log.info(
        "LRCLIB SIMPLE: Query → title=%r, artist=%r, album=%r, duration=%r",
        title, artist, album, duration,
    )

    if not (title and artist and duration):
        return None

    return {
        "track_name": title,
        "artist_name": artist,
        "album_name": album or "",
        "duration": duration,
    }


# ============================================================
# Request LRCLIB (SSL verification disabled for compatibility)
# ============================================================

def _fetch_lyrics_from_lrclib(query):
    """
    Send HTTP request to LRCLIB using urllib with SSL verification disabled
    (macOS Python inside Picard often lacks a certificate store).
    """
    url = LRCLIB_URL + "?" + urlencode(query)
    log.info("LRCLIB SIMPLE: Requesting %s", url)

    ctx = ssl._create_unverified_context()

    try:
        req = Request(
            url,
            headers={"User-Agent": "Picard-LRCLIB-External-Save"},
        )
        with urlopen(req, context=ctx, timeout=10) as resp:
            status = getattr(resp, "status", None)
            log.info("LRCLIB SIMPLE: HTTP status=%r", status)
            data = resp.read()
    except Exception as exc:
        log.warning("LRCLIB SIMPLE: HTTP request failed: %r", exc)
        return None, None

    # Parse JSON
    try:
        text = data.decode("utf-8", errors="replace")
        obj = json.loads(text)
    except Exception as exc:
        log.warning("LRCLIB SIMPLE: JSON decode failed: %r", exc)
        return None, None

    if isinstance(obj, list):
        if not obj:
            return None, None
        obj = obj[0]

    if not isinstance(obj, dict) or not obj.get("id"):
        return None, None

    synced = obj.get("syncedLyrics")
    plain = obj.get("plainLyrics")

    if synced:
        log.info("LRCLIB SIMPLE: Synced lyrics found (%d chars)", len(synced))
        return synced, True
    if plain:
        log.info("LRCLIB SIMPLE: Plain lyrics found (%d chars)", len(plain))
        return plain, False

    return None, None


# ============================================================
# Write sidecar files (.lrc or .txt)
# ============================================================

def _write_sidecar_for_file(file, lyrics, is_synced):
    audio_path = file.filename
    directory, fname = os.path.split(audio_path)
    stem, _ = os.path.splitext(fname)
    ext = ".lrc" if is_synced else ".txt"
    out_path = os.path.join(directory, stem + ext)

    log.info("LRCLIB SIMPLE: Writing sidecar %s", out_path)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(lyrics)
        log.info("LRCLIB SIMPLE: Successfully wrote sidecar")
    except Exception as exc:
        log.error("LRCLIB SIMPLE: Failed to write sidecar: %r", exc)


# ============================================================
# Main hook: run AFTER the file is saved
# ============================================================

def lrclib_simple_file_post_save(file):
    """
    Picard's official save hook: run after file is written and moved
    to final destination. We fetch lyrics from LRCLIB and write
    external sidecar files.
    """
    try:
        log.info("LRCLIB SIMPLE: Post-save → %s", file.filename)

        query = _build_query_from_file(file)
        if not query:
            return

        lyrics, is_synced = _fetch_lyrics_from_lrclib(query)
        if not lyrics:
            log.info("LRCLIB SIMPLE: No lyrics found")
            return

        _write_sidecar_for_file(file, lyrics, is_synced)

    except Exception as exc:
        log.error("LRCLIB SIMPLE: Unexpected error: %r", exc)


register_file_post_save_processor(lrclib_simple_file_post_save)
