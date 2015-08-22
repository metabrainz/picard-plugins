#!/usr/bin/env python

import os
import re
import sys
import json

import zipfile
import zlib

from hashlib import md5
from subprocess import call

from get_plugin_data import get_plugin_data


def build_json():
    """
    Traverse the plugins directory to generate json data.
    """

    # Read the existing data
    if os.path.isfile(plugin_file):
        with open(plugin_file, "r") as in_file:
            plugins = json.load(in_file)["plugins"]
    else:
        plugins = {}

    # All top level directories in plugin_dir are plugins
    for dirname in next(os.walk(plugin_dir))[1]:

        files = {}
        data = {}

        if dirname in [".git"]:
            continue

        dirpath = os.path.join(plugin_dir, dirname)
        for root, dirs, filenames in os.walk(dirpath):
            for filename in filenames:
                ext = os.path.splitext(filename)[1]

                if ext not in [".pyc"]:
                    file_path = os.path.join(root, filename)
                    with open(file_path, "rb") as md5file:
                        md5Hash = md5(md5file.read()).hexdigest()
                    files[file_path.split(os.path.join(dirpath, ''))[1]] = md5Hash

                    if ext in ['.py'] and not data:
                        data = get_plugin_data(os.path.join(plugin_dir, dirname, filename))

        if dirname in plugins:
            print("Updated: " + dirname)
            if data:
                for key, value in data.items():
                    plugins[dirname][key] = value
            plugins[dirname]["files"] = files
        else:
            print("Added: " + dirname)
            data['files'] = files
            plugins[dirname] = data

    with open(plugin_file, "w") as out_file:
        json.dump({"plugins": plugins}, out_file, sort_keys=True, indent=2)


def zip_files():
    """
    Zip up plugin folders
    """

    for dirname in next(os.walk(plugin_dir))[1]:
        archive_path = os.path.join(plugin_dir, dirname)
        archive = zipfile.ZipFile(archive_path + ".zip", "w")

        dirpath = os.path.join(plugin_dir, dirname)
        for root, dirs, filenames in os.walk(dirpath):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                archive.write(file_path,
                              file_path.split(os.path.join(dirpath, ''))[1],
                              compress_type=zipfile.ZIP_DEFLATED)

        print("Created: " + dirname + ".zip")


# The file that contains json data
plugin_file = "plugins.json"

# The directory which contains plugin files
plugin_dir = "plugins"

if __name__ == '__main__':
    if 1 in sys.argv:
        if sys.argv[1] == "pull":
            call(["git", "pull", "-q"])
        elif sys.argv[1] == "json":
            build_json()
        elif sys.argv[1] == "zip":
            zip_files()
    else:
        # call(["git", "pull", "-q"])
        build_json()
        zip_files()
