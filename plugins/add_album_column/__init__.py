# -*- coding: UTF-8 -*-

#
# Licensing
#
# Channel Manager Main, Create and maintain channel files
# Copyright (C) 2017 Evandro Coan <https://github.com/evandrocoan>
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

PLUGIN_NAME = u"Add Album Column"
PLUGIN_AUTHOR = u"Evandro Coan"
PLUGIN_DESCRIPTION = "Add the Album column to the main window panel."

PLUGIN_VERSION = "1.0"
PLUGIN_API_VERSIONS = ["1.4.0"]
PLUGIN_LICENSE = "GPLv3"
PLUGIN_LICENSE_URL = "http://www.gnu.org/licenses/"

from picard.ui.itemviews import MainPanel
MainPanel.columns.append((N_('Album'), 'album'))
