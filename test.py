import os
import shutil
import tempfile
import unittest
from picard_plugin_tools import package_folder, verify_package


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

    def package_plugins(self):
        plugin_data = {}
        for plugin in os.listdir(self.PLUGIN_DIR):
            plugin_dir = os.path.join(self.PLUGIN_DIR, plugin, plugin)
            manifest_path = os.path.join(self.PLUGIN_DIR, plugin, "MANIFEST.json")
            manifest_data = package_folder(plugin_dir, manifest_path, self.dest_dir)
            plugin_data[plugin] = manifest_data
        return plugin_data

    def test_packaging(self):
        plugin_data = self.package_plugins()

        # Number of entries in the json should be equal to the
        # number of folders in plugin_dir
        plugin_names = os.listdir(self.PLUGIN_DIR)
        packaged_plugins = os.listdir(self.dest_dir)
        self.assertEqual(len(plugin_data), len(plugin_names))
        self.assertEqual(len(packaged_plugins), len(plugin_names))
        for plugin in packaged_plugins:
            package_path = os.path.join(self.dest_dir, plugin)
            self.assertEqual(verify_package(package_path), True)


if __name__ == '__main__':
    unittest.main()
