# -*- coding: utf-8 -*-
#
# Apple Music cover art provider for MusicBrainz Picard.
#
# Uses the public iTunes Search API, which needs no account and no API key.
# Written for environments where coverartarchive.org / archive.org are not
# reachable.
#
# Copyright (C) 2026 Moshe Welcher
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

PLUGIN_NAME = 'Apple Music cover art'
PLUGIN_AUTHOR = 'MosheWelcher'
PLUGIN_DESCRIPTION = (
    'Fetches front cover art from the public iTunes Search API '
    '(itunes.apple.com), with images served from mzstatic.com.<br /><br />'
    'Needs no account and no API key. Useful when the Cover Art Archive '
    'is unreachable.<br /><br />'
    'Matching is done on artist/album text rather than MBID, so the plugin '
    'scores candidates and only accepts confident matches.'
)
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["2.0", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6",
                       "2.7", "2.8", "2.9", "2.10", "2.11", "2.12", "2.13"]
PLUGIN_LICENSE = "GPL-2.0"
PLUGIN_LICENSE_URL = "https://opensource.org/license/gpl-2.0"

import re
import unicodedata
from functools import partial

try:
    from PyQt5 import QtWidgets
    from PyQt5.QtNetwork import QNetworkReply
except ImportError:  # Picard 3.x / PyQt6
    from PyQt6 import QtWidgets
    from PyQt6.QtNetwork import QNetworkReply

from picard import log
from picard.coverart.image import CoverArtImage
from picard.coverart.providers import (
    CoverArtProvider,
    ProviderOptions,
    register_cover_art_provider,
)
from picard.config import IntOption, TextOption

ITUNES_HOST = "itunes.apple.com"
ITUNES_PORT = 443
ITUNES_PATH = "/search"

# Apple serves any square size by swapping the trailing segment of the URL.
_SIZE_RE = re.compile(r"/\d+x\d+(bb)?\.(jpg|png|jpeg)$", re.IGNORECASE)
_PAREN_RE = re.compile(r"[\(\[][^\)\]]*[\)\]]")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+", re.UNICODE)

# Suffixes that mark a different edition of the same album. Used only to
# break ties, never to reject a release outright.
_EDITION_WORDS = frozenset([
    "deluxe", "expanded", "remaster", "remastered", "anniversary",
    "explicit", "clean", "edition", "version", "bonus", "single",
    "ep", "live", "instrumental", "acoustic",
])


def _get_setting():
    """config.setting moved behind get_config() in Picard 2.4."""
    try:
        from picard.config import get_config
        return get_config().setting
    except ImportError:
        from picard import config
        return config.setting


def _normalize(text):
    """Casefold, strip accents and punctuation, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.casefold()
    text = _PUNCT_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def _base_title(text):
    """Normalized title with any bracketed suffix removed."""
    return _normalize(_PAREN_RE.sub(" ", text or ""))


def _edition_tokens(text):
    """Edition-ish words appearing in a title's bracketed suffixes."""
    tokens = set()
    for chunk in _PAREN_RE.findall(text or ""):
        tokens |= {t for t in _normalize(chunk).split() if t in _EDITION_WORDS}
    return tokens


def upscale_artwork_url(url, size):
    """Rewrite a 100x100 thumbnail URL to the requested square size."""
    return _SIZE_RE.sub("/%dx%dbb.jpg" % (size, size), url)


def score_candidate(result, album, artist, totaltracks):
    """Score an iTunes result against the tags Picard already has.

    Returns (score, reason). Scores below the configured threshold are
    discarded so a wrong cover is never silently attached.
    """
    cand_album = result.get("collectionName") or ""
    cand_artist = result.get("artistName") or ""

    want_album, got_album = _normalize(album), _normalize(cand_album)
    want_base, got_base = _base_title(album), _base_title(cand_album)

    if not got_album or not want_album:
        return (0, "missing title")

    # --- album title ---
    if got_album == want_album:
        score, reason = 100, "exact title"
    elif got_base and got_base == want_base:
        score, reason = 80, "title matches ignoring edition"
    elif got_base and want_base and (
            got_base.startswith(want_base) or want_base.startswith(got_base)):
        score, reason = 60, "title prefix"
    else:
        return (0, "title mismatch (%r vs %r)" % (cand_album, album))

    # Prefer the edition whose bracketed suffix matches ours, so a plain
    # album does not get the deluxe cover when both exist.
    want_ed, got_ed = _edition_tokens(album), _edition_tokens(cand_album)
    if want_ed == got_ed:
        score += 12
    else:
        score -= 6 * len(want_ed ^ got_ed)

    # --- artist ---
    want_artist, got_artist = _normalize(artist), _normalize(cand_artist)
    if want_artist and got_artist:
        if want_artist == got_artist:
            score += 25
        elif want_artist in got_artist or got_artist in want_artist:
            score += 12
        else:
            score -= 25
            reason += ", artist mismatch"

    # --- track count, a strong signal for picking the right edition ---
    try:
        want_tracks = int(totaltracks) if totaltracks else 0
    except (TypeError, ValueError):
        want_tracks = 0
    got_tracks = result.get("trackCount") or 0
    if want_tracks and got_tracks:
        if want_tracks == got_tracks:
            score += 20
            reason += ", %d tracks match" % want_tracks
        else:
            score -= 10
            reason += ", track count %d vs %d" % (got_tracks, want_tracks)

    return (score, reason)


class AppleMusicOptionsPage(ProviderOptions):

    _options_ui = None  # built programmatically in init_ui()

    options = [
        IntOption("setting", "applemusic_size", 1200),
        TextOption("setting", "applemusic_country", "US"),
        IntOption("setting", "applemusic_threshold", 90),
    ]

    def init_ui(self):
        # Hand-built rather than generated from a .ui file, so the plugin
        # stays a single drop-in .py.
        self.ui = type("Ui", (), {})()
        layout = QtWidgets.QVBoxLayout(self)

        box = QtWidgets.QGroupBox("Apple Music")
        form = QtWidgets.QFormLayout(box)

        self.ui.size = QtWidgets.QComboBox(box)
        for s in (600, 1200, 1400, 3000):
            self.ui.size.addItem("%d x %d" % (s, s), s)
        form.addRow("Image size:", self.ui.size)

        self.ui.country = QtWidgets.QLineEdit(box)
        self.ui.country.setMaxLength(2)
        form.addRow("Store country code:", self.ui.country)

        self.ui.threshold = QtWidgets.QSpinBox(box)
        self.ui.threshold.setRange(0, 200)
        self.ui.threshold.setToolTip(
            "Higher values reject uncertain matches. 90 requires roughly "
            "an exact title plus a matching artist.")
        form.addRow("Match confidence:", self.ui.threshold)

        layout.addWidget(box)
        layout.addStretch(1)

    def load(self):
        setting = _get_setting()
        idx = self.ui.size.findData(setting["applemusic_size"])
        self.ui.size.setCurrentIndex(idx if idx >= 0 else 1)
        self.ui.country.setText(setting["applemusic_country"])
        self.ui.threshold.setValue(setting["applemusic_threshold"])

    def save(self):
        setting = _get_setting()
        setting["applemusic_size"] = self.ui.size.currentData()
        setting["applemusic_country"] = (
            self.ui.country.text().strip().upper() or "US")
        setting["applemusic_threshold"] = self.ui.threshold.value()


class AppleMusicCoverArtImage(CoverArtImage):

    """Image from the iTunes/Apple Music catalogue."""

    support_types = True
    sourceprefix = "APPL"


class CoverArtProviderAppleMusic(CoverArtProvider):

    """Use the iTunes Search API to find front cover art."""

    NAME = "AppleMusic"
    TITLE = "Apple Music"
    OPTIONS = AppleMusicOptionsPage

    def enabled(self):
        return super().enabled() and not self.coverart.front_image_found

    def queue_images(self):
        album = self.metadata["album"]
        artist = (self.metadata["albumartist"]
                  or self.metadata["artist"] or "")
        if not album:
            log.debug("%s: no album title, skipping", PLUGIN_NAME)
            return CoverArtProvider.FINISHED

        setting = _get_setting()
        queryargs = {
            "term": ("%s %s" % (artist, album)).strip(),
            "entity": "album",
            "limit": "25",
            "media": "music",
            "country": setting["applemusic_country"] or "US",
        }

        log.debug("%s: searching for %r", PLUGIN_NAME, queryargs["term"])
        self.album.tagger.webservice.get(
            ITUNES_HOST,
            ITUNES_PORT,
            ITUNES_PATH,
            partial(self._json_downloaded, album, artist),
            priority=True,
            important=False,
            parse_response_type='json',
            queryargs=queryargs)
        self.album._requests += 1
        return CoverArtProvider.WAIT

    def _json_downloaded(self, album, artist, data, reply, error):
        self.album._requests -= 1

        if error:
            not_found = getattr(QNetworkReply, "ContentNotFoundError", None)
            if not_found is None:  # PyQt6 nests the enum
                not_found = QNetworkReply.NetworkError.ContentNotFoundError
            level = log.debug if error == not_found else log.error
            level("%s: request failed: %s", PLUGIN_NAME, error)
        else:
            try:
                self._process(data, album, artist)
            except (AttributeError, KeyError, TypeError):
                log.error("%s: failed to process response", PLUGIN_NAME,
                          exc_info=True)

        self.next_in_queue()

    def _process(self, data, album, artist):
        results = data.get("results") or []
        if not results:
            log.debug("%s: no results for %r", PLUGIN_NAME, album)
            return

        setting = _get_setting()
        threshold = setting["applemusic_threshold"]
        totaltracks = self.metadata["totaltracks"]

        scored = []
        for r in results:
            if not r.get("artworkUrl100"):
                continue
            score, reason = score_candidate(r, album, artist, totaltracks)
            scored.append((score, reason, r))

        if not scored:
            log.debug("%s: no candidates carried artwork", PLUGIN_NAME)
            return

        scored.sort(key=lambda x: x[0], reverse=True)
        score, reason, best = scored[0]

        if score < threshold:
            log.debug("%s: best candidate %r scored %d < %d (%s), rejected",
                      PLUGIN_NAME, best.get("collectionName"), score,
                      threshold, reason)
            return

        url = upscale_artwork_url(best["artworkUrl100"],
                                  setting["applemusic_size"])
        log.debug("%s: matched %r by %r, score %d (%s): %s",
                  PLUGIN_NAME, best.get("collectionName"),
                  best.get("artistName"), score, reason, url)
        self.queue_put(AppleMusicCoverArtImage(url, types=["front"]))


register_cover_art_provider(CoverArtProviderAppleMusic)
