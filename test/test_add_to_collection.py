import os
from itertools import chain
from unittest.mock import ANY, patch

from picard.collection import Collection, user_collections
from picard.file import File
from picard.file import _file_post_save_processors as post_save_processors
from picard.ui.options import _pages as option_pages
from plugin_test_case import PluginTestCase


class TestAddToCollection(PluginTestCase):
    SAVE_FILE_SETTINGS = {
        "dont_write_tags": True,
        "rename_files": False,
        "move_files": False,
        "delete_empty_dirs": False,
        "save_images_to_files": False,
        "clear_existing_tags": False,
        "compare_ignore_tags": [],
    }

    def install_plugin(self) -> None:
        self.plugin = self._test_plugin_install(
            "Add to Collection", "add_to_collection"
        )

    def create_file(self, file_name: str, album_id: str) -> File:
        file_path = os.path.join(self.tmp_directory, file_name)
        file = File(file_path)
        file.metadata["musicbrainz_albumid"] = album_id
        self.tagger.files[file_path] = file
        return file

    def tearDown(self) -> None:
        user_collections.clear()
        return super().tearDown()

    def test_hooks_installed(self) -> None:
        self.install_plugin()

        self.assertIn(
            self.plugin.post_save_processor.post_save_processor,
            list(chain.from_iterable(post_save_processors.functions.values())),
        )

        self.assertIn(
            self.plugin.options.AddToCollectionOptionsPage, list(option_pages)
        )

    def test_file_save(self) -> None:
        self.install_plugin()

        self.set_config_values(
            setting={
                **self.SAVE_FILE_SETTINGS,
                "add_to_collection_id": "test_collection_id",
            }
        )

        file = self.create_file(file_name="test.mp3", album_id="test_album_id")
        user_collections["test_collection_id"] = Collection(
            collection_id="test_collection_id", name="Test Collection", size=0
        )
        with patch("picard.collection.Collection.add_releases") as add_releases:
            file.save()
            add_releases.assert_called_with(set(["test_album_id"]), callback=ANY)

    def test_two_files_save(self) -> None:
        self.install_plugin()

        self.set_config_values(
            setting={
                **self.SAVE_FILE_SETTINGS,
                "add_to_collection_id": "test_collection_id",
            }
        )

        collection = Collection(
            collection_id="test_collection_id", name="Test Collection", size=0
        )
        user_collections["test_collection_id"] = collection
        with patch(
            "picard.collection.Collection.add_releases",
            side_effect=lambda ids, callback: collection.releases.update(ids),
        ) as add_releases:
            for i in range(2):
                file = self.create_file(
                    file_name=f"test{i}.mp3", album_id="test_album_id"
                )
                file.save()
            # only added once
            add_releases.assert_called_once_with(set(["test_album_id"]), callback=ANY)

    def test_no_collection_id_setting(self) -> None:
        self.install_plugin()

        self.set_config_values(setting=self.SAVE_FILE_SETTINGS)

        file = self.create_file(file_name="test.mp3", album_id="test_album_id")
        user_collections["test_collection_id"] = Collection(
            collection_id="test_collection_id", name="Test Collection", size=0
        )
        with patch("picard.collection.Collection.add_releases") as add_releases:
            file.save()
            add_releases.assert_not_called()

    def test_no_user_collection(self) -> None:
        self.install_plugin()

        self.set_config_values(
            setting={
                **self.SAVE_FILE_SETTINGS,
                "add_to_collection_id": "test_collection_id",
            }
        )

        file = self.create_file(file_name="test.mp3", album_id="test_album_id")
        with patch("picard.collection.Collection.add_releases") as add_releases:
            file.save()
            add_releases.assert_not_called()
