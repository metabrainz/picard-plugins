import os
import glob
import json
import shutil
import tempfile
import unittest
from generate import build_json, zip_files


class GenerateTestCase(unittest.TestCase):

    """Run tests"""

    # The file that contains json data
    PLUGIN_FILE = "plugins.json"

    # The directory which contains plugin files
    PLUGIN_DIR = "plugins"

    def setUp(self):

        # Destination directory
        self.dest_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dest_dir)
        self.plugin_file = os.path.join(self.dest_dir, self.PLUGIN_FILE)

    def test_generate_json(self):
        """
        Generates the json data from all the plugins
        and asserts that all plugins are accounted for.
        """

        print("\n#########################################\n")

        build_json(self.dest_dir)

        # Load the json file
        with open(self.plugin_file, "r") as in_file:
            plugin_json = json.load(in_file)["plugins"]

        # All top level directories in plugin_dir
        plugin_folders = next(os.walk(self.PLUGIN_DIR))[1]

        # Number of entries in the json should be equal to the
        # number of folders in plugin_dir
        self.assertEqual(len(plugin_json), len(plugin_folders))

    def test_generate_zip(self):
        """
        Generates zip files for all folders and asserts
        that all folders are accounted for.
        """

        print("\n\n#########################################\n")

        zip_files(self.dest_dir)

        # All zip files in plugin_dir
        plugin_zips = glob.glob(os.path.join(self.dest_dir, "*.zip"))

        # All top level directories in plugin_dir
        plugin_folders = next(os.walk(self.PLUGIN_DIR))[1]

        # Number of folders should be equal to number of zips
        self.assertEqual(len(plugin_zips), len(plugin_folders))

    def test_valid_json(self):
        """
        Asserts that the json data contains all the fields
        for all the plugins.
        """

        print("\n#########################################\n")

        build_json(self.dest_dir)

        # Load the json file
        with open(self.plugin_file, "r") as in_file:
            plugin_json = json.load(in_file)["plugins"]

        # All plugins should contain all required fields
        for module_name, data in plugin_json.items():
            self.assertIsInstance(data['name'], str)
            self.assertIsInstance(data['api_versions'], list)
            self.assertIsInstance(data['author'], str)
            self.assertIsInstance(data['description'], str)
            self.assertIsInstance(data['version'], str)




if __name__ == '__main__':
    unittest.main()
