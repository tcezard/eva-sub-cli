import copy
import logging
import sys
from unittest import TestCase
from unittest.mock import patch, Mock


from eva_sub_cli import orchestrator
from eva_sub_cli.executables import cli


class TestCli(TestCase):

    def test_main(self):
        args = Mock(submission_dir='.', vcf_files=[], reference_fasta='', metadata_json=None, metadata_xlsx='',
                    tasks='validate', executor='native', debug=False)
        with patch('eva_sub_cli.executables.cli.parse_args', return_value=args), \
                patch('eva_sub_cli.orchestrator.orchestrate_process'):
            cli.main()
            # Check that the debug message is shown
            logger = orchestrator.logger
            logger.debug('test')

    def test_validate_args(self):
        cmd_args = [
            '--submission_dir', '.',
            '--vcf_files', 'test.vcf',
            '--reference_fasta', 'test.fasta',
            '--metadata_json', 'test.json',
            '--tasks', 'validate',
            '--executor', 'native',
            '--debug'
        ]
        args = cli.parse_args(cmd_args)
        assert args.submission_dir == '.'


        with patch('sys.exit') as m_exit:
            cli.parse_args(cmd_args[:2]+cmd_args[4:])
            m_exit.assert_called_once_with(1)
