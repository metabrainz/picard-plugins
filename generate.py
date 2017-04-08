#!/usr/bin/env python

from __future__ import print_function
import argparse
import os
import json
import zipfile

from hashlib import md5
from subprocess import call

from get_plugin_data import get_plugin_data


def build_json(build_dir, version=None):
    """
    Traverse the plugins directory to generate json data.
    """

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

        if files and data:
            print("Added: " + dirname)
            data['files'] = files
            plugins[dirname] = data
    out_path = plugin_file
    if version:
        out_path = os.path.join(build_dir, version, plugin_file)
    with open(out_path, "w") as out_file:
        json.dump({"plugins": plugins}, out_file, sort_keys=True, indent=2)


def zip_files(build_dir, version=None):
    """
    Zip up plugin folders
    """

    for dirname in next(os.walk(plugin_dir))[1]:
        if version:
            archive_path = os.path.join(os.path.dirname(plugin_dir), build_dir, version, dirname)
        else:
            archive_path = os.path.join(plugin_dir, dirname)
        archive = zipfile.ZipFile(archive_path + ".zip", "w")

        dirpath = os.path.join(plugin_dir, dirname)
        plugin_files = []

        for root, dirs, filenames in os.walk(dirpath):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                plugin_files.append(file_path)

        if len(plugin_files) == 1:
            # There's only one file, put it directly into the zipfile
            archive.write(plugin_files[0],
                          os.path.basename(plugin_files[0]),
                          compress_type=zipfile.ZIP_DEFLATED)
        else:
            for filename in plugin_files:
                # Preserve the folder structure relative to plugin_dir
                # in the zip file
                name_in_zip = os.path.join(os.path.relpath(filename,
                                                           plugin_dir))
                archive.write(filename,
                              name_in_zip,
                              compress_type=zipfile.ZIP_DEFLATED)

        print("Created: " + dirname + ".zip")


# The file that contains json data
plugin_file = "plugins.json"

# The directory which contains plugin files
plugin_dir = "plugins"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plugin files for Picard website.')
    parser.add_argument('version', nargs='?')
    parser.add_argument('--build_dir', default="build")
    parser.add_argument('--pull', action='store_true', dest='pull')
    parser.add_argument('--no-zip', action='store_false', dest='zip')
    parser.add_argument('--no-json', action='store_false', dest='json')
    args = parser.parse_args()
    if args.version == 'v1' or args.version is None:
        call(["git", "checkout", "-q", 'master', '--', 'plugins'])
    else:
        call(["git", "checkout", "-q", args.version, '--', 'plugins'])
    if args.version and not os.path.exists(os.path.join(args.build_dir, args.version)):
        os.makedirs(os.path.join(args.build_dir, args.version))
    if args.pull:
        call(["git", "pull", "-q"])
    if args.json:
        build_json(args.build_dir, args.version)
    if args.zip:
        zip_files(args.build_dir, args.version)
