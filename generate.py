#!/usr/bin/env python3

from __future__ import print_function
import argparse
import os
import json
import zipfile

from hashlib import md5
from subprocess import call

from get_plugin_data import get_plugin_data

VERSION_TO_BRANCH = {
    None: 'master',
    '1.0': 'master',
    '2.0': '2.0',
}


def build_json(dest_dir):
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
    out_path = os.path.join(dest_dir, plugin_file)
    with open(out_path, "w") as out_file:
        json.dump({"plugins": plugins}, out_file, sort_keys=True, indent=2)


def zip_files(dest_dir):
    """
    Zip up plugin folders
    """

    for dirname in next(os.walk(plugin_dir))[1]:
        archive_path = os.path.join(dest_dir, dirname)
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
    parser.add_argument('version', nargs='?', help="Build output files for the specified version")
    parser.add_argument('--build_dir', default="build", help="Path for the build output. DEFAULT = %(default)s")
    parser.add_argument('--pull', action='store_true', dest='pull', help="Pulls the remote origin and updates the files before building")
    parser.add_argument('--no-zip', action='store_false', dest='zip', help="Do not generate the zip files in the build output")
    parser.add_argument('--no-json', action='store_false', dest='json', help="Do not generate the json file in the build output")
    args = parser.parse_args()
    # Work around in order to checkout the plugins folder from another branch
    # A simple git checkout does not remove folders removed from another branch
    # but it does add new nodes.
    call(["rm", "-rf", plugin_dir+"/*"])
    call(["git", "checkout", "-q", VERSION_TO_BRANCH[args.version], "--", plugin_dir])
    dest_dir = os.path.abspath(os.path.join(args.build_dir, args.version or ''))
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    if args.pull:
        call(["git", "pull", "-q"])
    if args.json:
        build_json(dest_dir)
    if args.zip:
        zip_files(dest_dir)
    # Resetting the plugins folder for cleanup
    call(["git", "reset", "-q", plugin_dir])
