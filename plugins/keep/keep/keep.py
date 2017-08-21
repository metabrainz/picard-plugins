PLUGIN_NAME = "Keep tags"
PLUGIN_AUTHOR = "Wieland Hoffmann"
PLUGIN_DESCRIPTION = """
Adds a $keep() function to delete all tags except the ones that you want.
Tags beginning with `musicbrainz_` are kept automatically, as are tags
beginning with `_`."""

PLUGIN_VERSION = "1.1"
PLUGIN_API_VERSIONS = ["0.15.0", "0.15.1", "0.16.0", "1.0.0", "1.1.0", "1.2.0",
                       "1.3.0", "2.0"]
PLUGIN_LICENSE = "GPL-2.0 or later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from picard.script import register_script_function


def transltag(tag):
    if tag.startswith("~"):
        return "_" + tag[1:]
    return tag


@register_script_function
def keep(parser, *keeptags):
    tags = list(parser.context.keys())
    for tag in tags:
        if (transltag(tag) not in keeptags and
            not tag.startswith("musicbrainz_") and
                not tag[0] == "~"):
            parser.context.pop(tag, None)
    return ""
