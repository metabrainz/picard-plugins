PLUGIN_NAME = "Albums Statistics"
PLUGIN_AUTHOR = "Echelon"
PLUGIN_DESCRIPTION = "Summarises the status of selected albums e.g. Changed?, Complete? Error?"
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['2.2']
PLUGIN_LICENSE = "GPL-2.0-or-later"
PLUGIN_LICENSE_URL = "https://www.gnu.org/licenses/gpl-2.0.html"

from PyQt5.QtWidgets import QLabel, QGridLayout, QWidget
from PyQt5.QtGui import QPixmap, QIcon

from picard.ui.itemviews import BaseAction, register_album_action

class AlbumsStats(BaseAction):
    NAME = "Albums Statistics"

    def __init__(self):
        super().__init__()

        self.grid = QGridLayout()
        self.window = QWidget()
        self.window.setLayout(self.grid)
        self.window.setGeometry(100, 100, 400, 250)
        self.window.setWindowTitle(_("Albums Statistics"))
        self.window.setWindowIcon(QIcon(":/images/16x16/org.musicbrainz.Picard.png"))
        self.window.setStyleSheet("font-size:12pt;")

    def createWidget(self):
        self.grid.addWidget(QLabel(_("The status of the selected Albums is as follows:")), 0, 0, 1, 3)
        self.addGridRow(1, ":/images/22x22/media-optical.png",
            _("Incomplete & unchanged"))
        self.addGridRow(2, ":/images/22x22/media-optical-modified.png",
            _("Incomplete & modified"))
        self.addGridRow(3, ":/images/22x22/media-optical-saved.png",
            _("Complete & unchanged"))
        self.addGridRow(4, ":/images/22x22/media-optical-saved-modified.png",
            _("Complete & modified"))
        self.addGridRow(5, ":/images/22x22/media-optical-error.png",
            _("Errored"))
        self.addGridRow(6, "",
            _("Total"))
        self.grid.addWidget(QLabel("Total"), 6, 2)

    def clearWidget(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.clear()

    def addGridRow(self, row, icon_location, description):
        icon = QLabel()
        if icon_location:
            icon.setPixmap(QPixmap(icon_location))
        self.grid.addWidget(icon, row, 0)
        self.grid.addWidget(QLabel(""), row, 1)
        self.grid.addWidget(QLabel(description), row, 2)

    def setCounter(self, row, count):
        self.grid.addWidget(QLabel(str(count)), row, 1)

    def callback(self, objs):
        incomplete_unchanged = incomplete_modified = complete_unchanged = complete_modified = errored = 0

        self.clearWidget()
        self.createWidget()

        for album in objs:
            if album.errors:
                errored += 1
            elif album.is_complete():
                if album.is_modified():
                    complete_modified += 1
                else:
                    complete_unchanged += 1
            else:
                if album.is_modified():
                    incomplete_modified += 1
                else:
                    incomplete_unchanged += 1

        total = incomplete_unchanged + incomplete_modified + complete_unchanged + complete_modified + errored

        self.setCounter(1, incomplete_unchanged)
        self.setCounter(2, incomplete_modified)
        self.setCounter(3, complete_unchanged)
        self.setCounter(4, complete_modified)
        self.setCounter(5, errored)
        self.setCounter(6, total)

        self.window.show()

register_album_action(AlbumsStats())