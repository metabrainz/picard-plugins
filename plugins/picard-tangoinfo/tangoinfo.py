"""
Get genre, performed date and (soon) vocalists and instrumentalists from tango.info
Uses web scraping since opendata is disabled for now
"""

PLUGIN_NAME = 'ix5 tango.info'
PLUGIN_AUTHOR = 'ix5'
PLUGIN_DESCRIPTION = 'change <em>genre</em> and <em>year</em> fields'
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ["0.9.0", "0.12", "1.0.0"]

from picard import log
from picard.metadata import register_track_metadata_processor
import re,os

from bs4 import BeautifulSoup
import urllib2

scraped_data = {}

def scrape_page(barcode):
    url = ("https://tango.info/0" + str(barcode))
    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page, "lxml")
    table = soup.findAll("table")[3]
    x = (len(table.findAll('tr')) -1)


    for row in table.findAll('tr')[1:]:
        col = row.findAll('td')
        genre = col[3].getText().capitalize()
        perf_date = col[6].getText()
        # checks
        info = col[-1].find('a').get('href').split('/')[1] # get TINT
        #track_tint = "0" + str(int(metadata["barcode"])) + "-" + str(mydiscnumber) + "-" + metadata["tracknumber"]
        scraped_data[info] = {"genre": genre, "year": perf_date}
        #: Data expected to be in this format:
        # ["Side", "Tracknr", "Title", "Genre", "Instrumentalists", "Vocalists", "Perf Date", "Duration", "Info"]

_discnumber_re = re.compile(r"\s+\(disc (\d+)(?::\s+([^)]+))?\)")

def get_discnumber(metadata):
    retval = 1
    if (is_integer(metadata["discnumber"])):
        if metadata["discnumber"]>0:
            retval = metadata["discnumber"]
        else:	
            matches = _discnumber_re.search(metadata["album"])
            if matches:
                retval = matches.group(1)
    return retval

def is_integer(testinteger):
	try:
		int(testinteger)
		return True
	except:
		return False	


def set_data(tagger, metadata, release, track):
    mydiscnumber = get_discnumber(metadata)
    tangoinfo_tint = str("00" + str(int(metadata["barcode"])) + "-" + str(mydiscnumber) + "-" + metadata["tracknumber"])
    #: prefixing 00 is weird, but should work
    scrape_page(metadata["barcode"])
    metadata['genre'] = scraped_data[tangoinfo_tint]['genre']
    log.debug("Set genre %s" % scraped_data[tangoinfo_tint]['genre'])
    metadata['year'] = scraped_data[tangoinfo_tint]['year']
    log.debug("Set year: %s" % scraped_data[tangoinfo_tint]['year'])

register_track_metadata_processor(set_data)
