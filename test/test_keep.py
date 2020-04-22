#!/usr/bin/env python
# coding: utf-8
import unittest

from picard.metadata import Metadata
from picard.script import ScriptParser
from plugins.keep.keep import keep  # noqa: F401 pylint: disable=unused-import


class TestKeep(unittest.TestCase):
    def setUp(self):
        self.parser = ScriptParser()

    def test_keep_simple(self):
        meta = Metadata(
            {
                "foo": "foo",
                "bar": "bar"
            })

        sc = """$keep(bar)"""
        self.parser.eval(sc, meta)
        self.assertEqual(meta["bar"], "bar")
        self.assertEqual(len(meta.keys()), 1)
        self.assertNotIn("foo", meta)

    def test_keep_mbid(self):
        meta = Metadata(
            {
                "foo": "foo",
                "bar": "bar",
                "musicbrainz_albumid": "albumid",
            })

        sc = """$keep(bar)"""
        self.parser.eval(sc, meta)
        self.assertEqual(meta["musicbrainz_albumid"], "albumid")
        self.assertEqual(len(meta.keys()), 2)

    def test_keep_nonfiletags(self):
        meta = Metadata(
            {
                "foo": "foo",
                "bar": "bar",
                "~baz": "baz",
            })

        sc = """$keep(bar)"""
        self.parser.eval(sc, meta)
        self.assertEqual(meta["~baz"], "baz")
        self.assertEqual(len(meta.keys()), 2)

    def _description_test(self, tagname):
        meta = Metadata(
            {
                "foo": "foo",
                "bar": "bar",
                tagname: tagname
            })

        tag_without_description = tagname.split(":")[0]
        sc = """$keep({tag})""".format(tag=tag_without_description)
        self.parser.eval(sc, meta)
        self.assertEqual(meta[tagname], tagname)
        self.assertEqual(len(meta.keys()), 1)

    def test_keep_performer(self):
        self._description_test("performer:vocal")
        self._description_test("performer:")

    def test_keep_lyrics(self):
        self._description_test("lyrics:foo")
        self._description_test("lyrics:")

    def test_keep_comment(self):
        self._description_test("comment:foo")
        self._description_test("comment:")

    def test_keep_with_description(self):
        meta = Metadata(
            {
                "foo": "foo",
                "bar": "bar",
                "performer:vocal": "performer:vocal",
                "performer:guitar": "performer:guitar"
            })

        sc = """$keep(performer:vocal)"""
        self.parser.eval(sc, meta)
        self.assertEqual(meta["performer:vocal"], "performer:vocal")
        self.assertEqual(len(meta.keys()), 1)
