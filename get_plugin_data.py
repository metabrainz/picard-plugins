# -*- coding: utf-8 -*-

from __future__ import print_function
import ast

known_data = [
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
    with open(filepath, 'r') as plugin_file:
        source = plugin_file.read()
        try:
            root = ast.parse(source, filepath)
        except Exception as e:
            print("Cannot parse " + filepath)
            raise e
        for node in ast.iter_child_nodes(root):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if (isinstance(target, ast.Name)
                    and isinstance(target.ctx, ast.Store)
                    and target.id in known_data):
                    name = target.id.replace('PLUGIN_', '', 1).lower()
                    if name not in data:
                        try:
                            data[name] = ast.literal_eval(node.value)
                        except ValueError as e:
                            print(filepath + ':' + ast.dump(node))
                            pass
        return data
