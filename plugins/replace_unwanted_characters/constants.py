# -*- coding: utf-8 -*-



DEFAULT_TAGS = ["album", "artist", "title", "albumartist", "releasetype", "label"]

DEFAULT_CHAR_MAPPING = {
    ":": "∶", "/": "⁄", "*": "∗", "?": "？", '"': '″',
    '\\': '⧵', '.': '․', '|': 'ǀ', '<': '‹', '>': '›'
}
CONFIG_NAME_FILTER_TAGS = "replace_unwanted_characters_filter_tags"
CONFIG_NAME_PER_TAG_TABLES = "replace_unwanted_characters_per_tag_tables"
CONFIG_NAME_CHAR_TABLE = "replace_unwanted_characters_char_table"
