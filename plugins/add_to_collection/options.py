from picard.collection import Collection, user_collections
from picard.ui.options import OptionsPage, register_options_page

from picard.plugins.add_to_collection import settings
from picard.plugins.add_to_collection.manifest import PLUGIN_NAME
from picard.plugins.add_to_collection.ui_add_to_collection_options import (
    Ui_AddToCollectionOptions,
)
from picard.plugins.add_to_collection.override_module import override_module


class AddToCollectionOptionsPage(OptionsPage):
    NAME = "add-to-collection"
    TITLE = PLUGIN_NAME
    PARENT = "plugins"

    options = [settings.collection_id_option()]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ui = Ui_AddToCollectionOptions()
        self.ui.setupUi(self)

    def load(self) -> None:
        self.set_collection_name(settings.collection_id())

    def save(self) -> None:
        settings.set_collection_id(self.ui.collection_name.currentData())

    def set_collection_name(self, value: str) -> None:
        self.ui.collection_name.clear()
        collection: Collection
        for collection in user_collections.values():
            self.ui.collection_name.addItem(collection.name, collection.id)
        idx = self.ui.collection_name.findData(value)
        if idx != -1:
            self.ui.collection_name.setCurrentIndex(idx)


def register_options() -> None:
    with override_module(AddToCollectionOptionsPage):
        register_options_page(AddToCollectionOptionsPage)
