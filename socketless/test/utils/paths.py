# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

import os, sys

project_root = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(project_root) != 'socketless':
    if project_root == '/':
        raise Exception('Project root not found!')
    project_root = os.path.dirname(project_root)
project_container_dir = os.path.dirname(project_root)

sys.path.append(project_container_dir)

def path(_path):
    """docstring for path"""
    return os.path.join(project_root, _path)
