#!/usr/bin/env python3

import glob
import os

from PyQt5 import uic


os.chdir(os.path.dirname(__file__))
plugin_dir = os.path.relpath('plugins')


def compile_ui(uifile, pyfile):
    if newer(uifile, pyfile):
        print("compiling %s -> %s" % (uifile, pyfile))
        with open(pyfile, "w") as out:
            uic.compileUi(uifile, out)
    else:
        print("skipping %s -> %s: up to date" % (uifile, pyfile))


def newer(file1, file2):
    """Returns True, if file1 has been modified after file2
    """
    if not os.path.exists(file2):
        return True
    return os.path.getmtime(file1) > os.path.getmtime(file2)


if __name__ == '__main__':
    for uifile in glob.glob(os.path.join(plugin_dir, '*/*.ui')):
        pyfile = os.path.splitext(os.path.basename(uifile))[0] + '.py'
        pyfile = os.path.join(os.path.dirname(uifile), pyfile)
        compile_ui(uifile, pyfile)
