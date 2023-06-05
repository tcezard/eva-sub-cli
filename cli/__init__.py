import os

import cli

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(cli.__file__)))  # This is your Project Root

NEXTFLOW_DIR = os.path.join(os.path.dirname(os.path.abspath(cli.__file__)), 'nextflow')
ETC_DIR = os.path.join(os.path.dirname(os.path.abspath(cli.__file__)), 'etc')

__version__ = open(os.path.join(os.path.dirname(os.path.abspath(cli.__file__)), 'VERSION')).read().strip()
