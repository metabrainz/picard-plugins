# -*- coding: utf-8 -*-

from __future__ import print_function
import ast

KNOWN_DATA = [
    'PLUGIN_NAME',
    'PLUGIN_AUTHOR',
    'PLUGIN_VERSION',
    'PLUGIN_API_VERSIONS',
    'PLUGIN_LICENSE',
    'PLUGIN_LICENSE_URL',
    'PLUGIN_DESCRIPTION',
]


def get_plugin_data(filepath):
    """Parse a python file and return a dict with plugin metadata"""
    data = {}
    with open(filepath, 'rU', encoding='utf-8') as plugin_file:
        source = plugin_file.read()
        try:
            root = ast.parse(source, filepath)
        except:
            print("Cannot parse " + filepath)
            raise
        for node in ast.iter_child_nodes(root):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if (isinstance(target, ast.Name)
                    and isinstance(target.ctx, ast.Store)
                        and target.id in KNOWN_DATA):
                    name = target.id.replace('PLUGIN_', '', 1).lower()
                    if name not in data:
                        try:
                            data[name] = ast.literal_eval(node.value)
                        except ValueError:
                            print('Cannot evaluate value in '
                                  + filepath + ':' +
                                  ast.dump(node))
        return data
