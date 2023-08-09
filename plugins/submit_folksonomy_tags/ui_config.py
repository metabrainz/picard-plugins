from PyQt5.QtCore import (
    QSize,
    Qt
    )

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    )

class TagSubmitPluginOptionsUI():

    def __init__(self, page):
        self.main_container = QVBoxLayout()

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        # Group box: tag saving
        self.tag_save_groupbox = QGroupBox()
        sizePolicy.setHeightForWidth(self.tag_save_groupbox.sizePolicy().hasHeightForWidth())
        self.tag_save_groupbox.setSizePolicy(sizePolicy)
        self.tag_save_groupbox_layout = QGridLayout(self.tag_save_groupbox)
        # Label: tag saving description
        self.tag_save_description = QLabel(self.tag_save_groupbox)
        sizePolicy.setHeightForWidth(self.tag_save_description.sizePolicy().hasHeightForWidth())
        self.tag_save_description.setSizePolicy(sizePolicy)
        self.tag_save_description.setMinimumSize(QSize(0, 56))
        self.tag_save_description.setWordWrap(True)
        self.tag_save_groupbox_layout.addWidget(self.tag_save_description, 0, 0, 1, 1)
        self.tag_save_groupbox.setTitle("Tag Saving")
        self.tag_save_description.setText(u"<html><head/><body><p>There are two modes to tag saving via this plugin right now: keep all existing saved tags (only adding on tags) or overwrite them. If you are not in a position where replacing your saved tags online is a good idea, it is recommended to keep this option unchanged.</p></body></html>")
        self.main_container.addWidget(self.tag_save_groupbox)
        self.tag_save_groupbox_layout.addWidget(self.tag_save_description, 0, 0, 1, 1)

        self.tags_to_save_groupbox = QGroupBox()
        sizePolicy.setHeightForWidth(self.tags_to_save_groupbox.sizePolicy().hasHeightForWidth())
        self.tags_to_save_groupbox.setSizePolicy(sizePolicy)
        self.tags_to_save_groupbox_layout = QGridLayout(self.tags_to_save_groupbox)
        self.tags_to_save_groupbox.setTitle("Tags to Submit")
        self.tags_to_save_description = QLabel(self.tags_to_save_groupbox)
        sizePolicy.setHeightForWidth(self.tags_to_save_description.sizePolicy().hasHeightForWidth())
        self.tags_to_save_textbox = QLineEdit()
        self.tags_to_save_description.setText("<html><head/><body><p>List the tags that you want to submit to MusicBrainz via the plugin in the text box below. Separate each tag with a semi-colon. (e.g. genre; mood)</p></body></html>")
        self.tags_to_save_groupbox_layout.addWidget(self.tags_to_save_description)
        self.tags_to_save_textbox.setPlaceholderText("Tags you want to submit (separated by semicolons - e.g. genre; mood)")
        self.tags_to_save_groupbox_layout.addWidget(self.tags_to_save_textbox)
        self.main_container.addWidget(self.tags_to_save_groupbox)

        # Radio buttons for tag saving options (on the plugin as "destructive")
        self.keep_radio_button = QRadioButton(self.tag_save_groupbox)
        self.keep_radio_button.setText("Keep existing online saved tags")
        self.tag_save_groupbox_layout.addWidget(self.keep_radio_button, 1, 0, 1, 1)
        self.overwrite_radio_button = QRadioButton(self.tag_save_groupbox)
        self.overwrite_radio_button.setText("Overwrite all online saved tags")
        self.tag_save_groupbox_layout.addWidget(self.overwrite_radio_button, 2, 0, 1, 1)

        # Group box: tag aliases
        self.tag_alias_groupbox = QGroupBox()
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.tag_alias_groupbox.sizePolicy().hasHeightForWidth())
        self.tag_alias_groupbox.setSizePolicy(sizePolicy1)
        self.tag_alias_groupbox.setCheckable(True)
        self.tag_alias_groupbox.setChecked(False)
        self.tag_alias_groupbox_layout = QVBoxLayout(self.tag_alias_groupbox)
        self.tag_alias_groupbox.setTitle("Tag Aliases")
        self.tag_alias_description = QLabel()
        self.tag_alias_description.setText("<html><head/><body><p>There may be cases where you prefer one tag on your files to be saved as another on MusicBrainz (e.g. if your genre tags don't align with MusicBrainz's standard genre tags). In such cases, the plugin can substitute your tags with whichever tags you want when submitting.</p><p>Anything listed here is case-insensitive, as MusicBrainz will process them in lowercase anyway.</p></body></html>")
        self.tag_alias_description.setMinimumSize(QSize(0, 42))
        self.tag_alias_description.setWordWrap(True)
        self.tag_alias_groupbox_layout.addWidget(self.tag_alias_description)

        # Tag alias table
        self.tag_alias_table = QTableWidget()
        self.tag_alias_table.setColumnCount(2)
        __find_column = QTableWidgetItem()
        __find_column.setText("Find...")
        self.tag_alias_table.setHorizontalHeaderItem(0, __find_column)
        __replace_column = QTableWidgetItem()
        __replace_column.setText("Replace...")
        self.tag_alias_table.setHorizontalHeaderItem(1, __replace_column)
        self.tag_alias_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tag_alias_groupbox_layout.addWidget(self.tag_alias_table)

        # Tag alias buttons
        self.table_button_layout = QHBoxLayout()
        self.add_row_button = QPushButton()
        self.delete_row_button = QPushButton()
        self.add_row_button.setText("Add tag alias")
        self.add_row_button.clicked.connect(self.add_row)
        self.delete_row_button.setText("Delete selected tag aliases")
        self.delete_row_button.clicked.connect(self.delete_rows)
        self.table_button_layout.addWidget(self.add_row_button)
        self.table_button_layout.addWidget(self.delete_row_button)
        self.tag_alias_groupbox_layout.addLayout(self.table_button_layout)
        self.main_container.addWidget(self.tag_alias_groupbox)

        page.setLayout(self.main_container)

    def add_row(self, find_entry="", replace_entry=""):
        """
        Adds a row to the table. Accepts input.
        """
        row_pos = self.tag_alias_table.rowCount()
        self.tag_alias_table.insertRow(row_pos)

        find_tableitem = QTableWidgetItem(find_entry)
        replace_tableitem = QTableWidgetItem(replace_entry)

        self.tag_alias_table.setItem(row_pos, 0, find_tableitem)
        self.tag_alias_table.setItem(row_pos, 1, replace_tableitem)

    def delete_rows(self):
        """
        Self-explanatory - removes the selected rows.
        """
        for row in self.tag_alias_table.selectionModel().selectedRows():
            self.tag_alias_table.removeRow(row.row())

    def rows_to_tuple_list(self):
        """
        Converts filled in rows to a list of tuples for the alias list setting.
        """

        tuple_list = []
        row_count = self.tag_alias_table.rowCount()
        for row in range(row_count):
            find_tableitem = self.tag_alias_table.item(row, 0).text()
            replace_tableitem = self.tag_alias_table.item(row, 1).text()
            if find_tableitem and replace_tableitem:
                tuple_list.append((find_tableitem, replace_tableitem))
        return tuple_list
