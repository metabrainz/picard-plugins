# -*- coding: UTF-8 -*-

#
# Licensing
#
# Add Album Column, Add the Album column to the main window panel
# Copyright (C) 2019 Evandro Coan <https://github.com/evandrocoan>
#
#  Redistributions of source code must retain the above
#  copyright notice, this list of conditions and the
#  following disclaimer.
#
#  Redistributions in binary form must reproduce the above
#  copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials
#  provided with the distribution.
#
#  Neither the name Evandro Coan nor the names of any
#  contributors may be used to endorse or promote products
#  derived from this software without specific prior written
#  permission.
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
PLUGIN_DESCRIPTION = """Add the Album column to the main window panel.
<br /><br />
WARNING: This plugin cannot be disabled. See:
<a href="https://github.com/metabrainz/picard-plugins/pull/195">
github.com/metabrainz/picard-plugins/pull/195
</a>.
"""

PLUGIN_VERSION = "1.01"
PLUGIN_API_VERSIONS = ["2.0"]
PLUGIN_LICENSE = "GPL-3.0-or-later"
PLUGIN_LICENSE_URL = "http://www.gnu.org/licenses/"

from picard.ui.itemviews import MainPanel
MainPanel.columns.append((N_('Album'), 'album'))
