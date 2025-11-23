# -*- coding: utf-8 -*-

"""LRCLIB Lyrics External Save

Fetch lyrics from LRCLIB after files are saved and write them as
sidecar .lrc / .txt files next to the audio files.

Implementation notes
--------------------
* Uses Picard's file_post_save_processor hook so that the audio file
  has already been moved/renamed to its final destination.
* Performs the actual network request in a worker thread so that
  Picard's UI thread is not blocked while contacting LRCLIB.
* Uses Python's urllib with SSL verification disabled for LRCLIB,
  because the embedded Python on some macOS deployments can lack a
  proper certificate store.
* Does NOT modify any tags inside the audio file – it only writes
  external sidecar lyrics files.
"""

PLUGIN_NAME = "LRCLIB Lyrics External Save"
PLUGIN_AUTHOR = "Harmonese"
PLUGIN_DESCRIPTION = (
    "Fetch lyrics from LRCLIB based on track metadata after saving files, "
    "and write synced lyrics (.lrc) or plain lyrics (.txt) as external "
    "sidecar files in the same folder as the audio file. Does not modify "
    "audio tags."
)
PLUGIN_VERSION = "1.1.1"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6"]
PLUGIN_LICENSE = "MIT"
PLUGIN_LICENSE_URL = "https://opensource.org/licenses/MIT"

import json
import os
import ssl
import threading
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from picard import log
from picard.file import register_file_post_save_processor


# minor clean-up (reviewer comment)
LRCLIB_URL = "https://lrclib.net/api/get?"


# ============================================================
# Helpers: building the query from metadata
# ============================================================

def _build_query_from_snapshot(snapshot):
    """
    Build LRCLIB query parameters from a metadata snapshot.

    snapshot is a plain dict with at least:
        title, artist, album, ~length
    """
    title = snapshot.get("title")
    artist = snapshot.get("artist")
    album = snapshot.get("album")
    duration = None

    # parse "~length" safely
    length_str = snapshot.get("~length")
    if length_str:
        try:
            parts = length_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                duration = minutes * 60 + seconds
        except Exception as exc:
            log.warning(
                "LRCLIB SIMPLE: failed to parse '~length' %r: %r",
                length_str,
                exc,
            )

    log.info(
        "LRCLIB SIMPLE: Query → title=%r, artist=%r, album=%r, duration=%r",
        title,
        artist,
        album,
        duration,
    )

    # LRCLIB requires at least title, artist, duration
    if not (title and artist and duration):
        log.warning(
            "LRCLIB SIMPLE: Missing required metadata "
            "(title=%r, artist=%r, duration=%r). Skipping LRCLIB lookup.",
            title,
            artist,
            duration,
        )
        return None

    return {
        "track_name": title,
        "artist_name": artist,
        "album_name": album or "",
        "duration": duration,
    }


# ============================================================
# HTTP client to LRCLIB (urllib, SSL verify disabled)
# ============================================================

def _fetch_lyrics_from_lrclib(query):
    """
    Perform a synchronous HTTP GET to LRCLIB and return (lyrics, is_synced).

    Returns:
        (lyrics_text, True)   if syncedLyrics is available
        (lyrics_text, False)  if only plainLyrics is available
        (None, None)          on failure or no lyrics
    """
    url = LRCLIB_URL + urlencode(query)
    log.info("LRCLIB SIMPLE: Requesting %s", url)

    ctx = ssl._create_unverified_context()  # disable SSL verification

    try:
        req = Request(
            url,
            headers={"User-Agent": "Picard-LRCLIB-External-Save"},
        )
        with urlopen(req, context=ctx, timeout=15) as resp:
            status = getattr(resp, "status", None)
            log.info("LRCLIB SIMPLE: HTTP status=%r", status)
            data = resp.read()
    except Exception as exc:
        log.error("LRCLIB SIMPLE: HTTP request failed: %r", exc)
        return None, None

    try:
        text = data.decode("utf-8", errors="replace")
        obj = json.loads(text)
    except Exception as exc:
        log.error("LRCLIB SIMPLE: JSON decode failed: %r", exc)
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
# Sidecar writer
# ============================================================

def _write_sidecar_for_path(audio_path, lyrics, is_synced):
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
# Worker thread logic
# ============================================================

def _worker_for_file(audio_path, snapshot):
    """
    Background worker: build query from metadata snapshot, fetch lyrics,
    and write the sidecar file.
    """
    try:
        log.info("LRCLIB SIMPLE: Worker started for %s", audio_path)

        query = _build_query_from_snapshot(snapshot)
        if not query:
            return

        lyrics, is_synced = _fetch_lyrics_from_lrclib(query)
        if not lyrics:
            log.info("LRCLIB SIMPLE: No lyrics found for %s", audio_path)
            return

        _write_sidecar_for_path(audio_path, lyrics, is_synced)

    except Exception as exc:
        log.error(
            "LRCLIB SIMPLE: Worker unexpected error for %s: %r",
            audio_path,
            exc,
        )


# ============================================================
# Picard hook: file_post_save_processor
# ============================================================

def lrclib_simple_file_post_save(file):
    """
    Called by Picard after a file has been saved (and moved/renamed).
    """
    try:
        audio_path = file.filename
    except Exception as exc:
        log.error("LRCLIB SIMPLE: Cannot read file filename: %r", exc)
        return

    try:
        md = file.metadata
        snapshot = {
            "title": md.get("title"),
            "artist": md.get("artist"),
            "album": md.get("album"),
            "~length": md.get("~length"),
        }
        log.info(
            "LRCLIB SIMPLE: Post-save → %s (title=%r, artist=%r)",
            audio_path,
            snapshot.get("title"),
            snapshot.get("artist"),
        )
    except Exception as exc:
        log.error("LRCLIB SIMPLE: Cannot snapshot metadata: %r", exc)
        return

    try:
        t = threading.Thread(
            target=_worker_for_file,
            args=(audio_path, snapshot),
            daemon=True,
        )
        t.start()
    except Exception as exc:
        log.error("LRCLIB SIMPLE: Failed to start worker thread: %r", exc)


register_file_post_save_processor(lrclib_simple_file_post_save)
