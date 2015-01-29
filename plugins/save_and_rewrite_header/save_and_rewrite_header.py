#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

PLUGIN_NAME = "Save and rewrite header"
PLUGIN_AUTHOR = "Nicolas Cenerario"
PLUGIN_DESCRIPTION = "This plugin adds a context menu action to save files and rewrite their header."
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["0.9.0", "0.10", "0.15"]

from _functools import partial
from mutagen import File as MFile
from picard.ui.itemviews import BaseAction, register_album_action, register_cluster_action, register_clusterlist_action, register_track_action, register_file_action
from picard.metadata import Metadata
from picard.util import thread

class save_and_rewrite_header(BaseAction):

	NAME = "Save and rewrite header"

	def __init__(self):
		super(save_and_rewrite_header, self).__init__()
		register_file_action(self)
		register_track_action(self)
		register_album_action(self)
		register_cluster_action(self)
		register_clusterlist_action(self)

	def callback(self, obj):
		def save(pf):
			metadata = Metadata()
			metadata.copy(pf.metadata)
			mf = MFile(pf.filename)
			if mf is not None:
				mf.delete()
			return pf._save_and_rename(pf.filename, metadata)
		for f in self.tagger.get_files_from_objects(obj, save=True):
			f.set_pending()
			thread.run_task(partial(save, f), f._saving_finished, priority=2, thread_pool=f.tagger.save_thread_pool)

save_and_rewrite_header()
