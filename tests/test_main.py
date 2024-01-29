import json
import os
import shutil
import unittest
from unittest.mock import MagicMock, patch, Mock

import yaml
from ebi_eva_common_pyutils.config import WritableConfig

from eva_sub_cli import SUB_CLI_CONFIG_FILE
from eva_sub_cli.main import orchestrate_process, VALIDATE, SUBMIT
from eva_sub_cli.reporter import READY_FOR_SUBMISSION_TO_EVA
from eva_sub_cli.submit import StudySubmitter, SUB_CLI_CONFIG_KEY_SUBMISSION_ID, SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL


class TestMain(unittest.TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')
    test_sub_dir = os.path.join(resource_dir, 'test_sub_dir')
    config_file = os.path.join(test_sub_dir, SUB_CLI_CONFIG_FILE)

    mapping_file = os.path.join(test_sub_dir, 'vcf_files_metadata.csv')
    metadata_json = os.path.join(test_sub_dir, 'sub_metadata.json')
    metadata_xlsx = os.path.join(test_sub_dir, 'sub_metadata.xlsx')

    def test_orchestrate_validate(self):
        with patch('eva_sub_cli.main.get_vcf_files') as m_get_vcf,  \
                patch('eva_sub_cli.main.WritableConfig') as m_config, \
                patch('eva_sub_cli.main.DockerValidator') as m_docker_validator:
            orchestrate_process(
                self.test_sub_dir, self.mapping_file, self.metadata_json, self.metadata_xlsx, tasks=[VALIDATE],
                resume=False
            )
            m_get_vcf.assert_called_once_with(self.mapping_file)
            m_docker_validator.assert_any_call(
                self.mapping_file, self.test_sub_dir, self.metadata_json, self.metadata_xlsx,
                submission_config=m_config.return_value
            )
            with m_docker_validator() as validator:
                validator.validate.assert_called_once_with()
                validator.create_reports.assert_called_once_with()
                validator.update_config_with_validation_result.assert_called_once_with()


    def test_orchestrate_validate_submit(self):
        with patch('eva_sub_cli.main.get_vcf_files') as m_get_vcf, \
                patch('eva_sub_cli.main.WritableConfig') as m_config, \
                patch('eva_sub_cli.main.DockerValidator') as m_docker_validator, \
                patch('eva_sub_cli.main.StudySubmitter') as m_submitter:
            # Empty config
            m_config.return_value = {}

            orchestrate_process(
                self.test_sub_dir, self.mapping_file, self.metadata_json, self.metadata_xlsx, tasks=[SUBMIT],
                resume=False
            )
            m_get_vcf.assert_called_once_with(self.mapping_file)
            # Validate was run because the config show it was not run successfully before
            m_docker_validator.assert_any_call(
                self.mapping_file, self.test_sub_dir, self.metadata_json, self.metadata_xlsx,
                submission_config=m_config.return_value
            )
            with m_docker_validator() as validator:
                validator.validate.assert_called_once_with()
                validator.create_reports.assert_called_once_with()
                validator.update_config_with_validation_result.assert_called_once_with()

            # Submit was created
            m_submitter.assert_any_call(self.test_sub_dir, m_get_vcf.return_value, self.metadata_json,
                                        submission_config=m_config.return_value)
            with m_submitter() as submitter:
                submitter.submit.assert_called_once_with(resume=False)

    def test_orchestrate_validate_no_submit(self):
        with patch('eva_sub_cli.main.get_vcf_files') as m_get_vcf, \
                patch('eva_sub_cli.main.WritableConfig') as m_config, \
                patch('eva_sub_cli.main.DockerValidator') as m_docker_validator, \
                patch('eva_sub_cli.main.StudySubmitter') as m_submitter:
            # Empty config
            m_config.return_value = {READY_FOR_SUBMISSION_TO_EVA: True}

            orchestrate_process(
                self.test_sub_dir, self.mapping_file, self.metadata_json, self.metadata_xlsx, tasks=[SUBMIT],
                resume=False
            )
            m_get_vcf.assert_called_once_with(self.mapping_file)
            # Validate was not run because the config showed it was run successfully before
            assert m_docker_validator.call_count == 0

            # Submit was created
            m_submitter.assert_any_call(self.test_sub_dir, m_get_vcf.return_value, self.metadata_json,
                                        submission_config=m_config.return_value)
            with m_submitter() as submitter:
                submitter.submit.assert_called_once_with(resume=False)
