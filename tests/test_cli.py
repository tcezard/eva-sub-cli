import sys
from unittest import TestCase

from eva_sub_cli.executables import cli


class TestCli(TestCase):

    print(sys.argv)
    args = ['--submission_dir', '.', '--metadata_xlsx', 'test.xlsx']
    sys.argv.extend(args)

    cli.main()

