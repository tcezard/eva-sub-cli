import glob
from distutils.core import setup
from os.path import join, abspath, dirname

import setuptools
from setuptools import find_packages
#
# base_dir = abspath(dirname(__file__))
# requirements_txt = join(base_dir, 'requirements.txt')
# requirements = [l.strip() for l in open(requirements_txt) if l and not l.startswith('#')]
#
# version = open(join(base_dir, 'eva_sub_cli', 'VERSION')).read().strip()
#
# setup(
#     name='eva_sub_cli',
#     packages=find_packages(),
#     package_data={'eva_sub_cli': ['nextflow/*', 'etc/*', 'VERSION', 'jinja_templates/*']},
#     use_scm_version={'write_to': 'eva_sub_cli/_version.py'},
#     license='Apache',
#     description='EBI EVA - validation and submission command line tool',
#     url='https://github.com/EBIvariation/eva-sub-cli',
#     keywords=['ebi', 'eva', 'python', 'submission', 'validation'],
#     install_requires=requirements,
#     setup_requires=['setuptools_scm'],
#     classifiers=[
#         'Development Status :: 5 - Production/Stable',
#         'Intended Audience :: Science/Research',
#         'Topic :: Communications :: File Sharing',
#         'License :: OSI Approved :: Apache Software License',
#         'Programming Language :: Python :: 3'
#     ],
#     scripts=glob.glob(join(dirname(__file__), 'bin', '*.py'))
# )

if __name__ == "__main__":
    setuptools.setup()
