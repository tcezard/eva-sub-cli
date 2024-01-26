#!/usr/bin/env python
import csv
import os
first attempt
from ebi_eva_common_pyutils.config import WritableConfig
from ebi_eva_common_pyutils.logger import logging_config

from eva_sub_cli import SUB_CLI_CONFIG_FILE, __version__
from eva_sub_cli.docker_validator import DockerValidator, docker_path, container_image
from eva_sub_cli.reporter import READY_FOR_SUBMISSION_TO_EVA
from eva_sub_cli.submit import StudySubmitter

VALIDATE = 'validate'
SUBMIT = 'submit'


logging_config.add_stdout_handler()


def get_vcf_files(mapping_file):
    vcf_files = []
    with open(mapping_file) as open_file:
        reader = csv.DictReader(open_file, delimiter=',')
        for row in reader:
            vcf_files.append(row['vcf'])
    return vcf_files


def orchestrate_process(submission_dir, vcf_files_mapping, metadata_json, metadata_xlsx, task):
    # load config
    config_file_path = os.path.join(submission_dir, SUB_CLI_CONFIG_FILE)
    sub_config = WritableConfig(config_file_path, version=__version__)

    metadata_file = metadata_json or metadata_xlsx
    vcf_files = get_vcf_files(vcf_files_mapping)



    # Only run validate if it's been requested
    if VALIDATE in tasks:
        with DockerValidator(vcf_files_mapping, submission_dir, metadata_json, metadata_xlsx,
                             submission_config=sub_config) as validator:
            validator.validate()
            validator.create_reports()
            validator.update_config_with_validation_result()

    with StudySubmitter(submission_dir, vcf_files, metadata_file, submission_config=sub_config) as submitter:
        submitter.upload_submission()
    # if validation is not passed, process task submit (validate and submit)
    if READY_FOR_SUBMISSION_TO_EVA in sub_config and sub_config[READY_FOR_SUBMISSION_TO_EVA]:
        tasks = SUBMIT
        else:
            # if validation is passed, upload files without validating again

    if task == VALIDATE or task == SUBMIT:
        with DockerValidator(vcf_files_mapping, submission_dir, metadata_json, metadata_xlsx,
                             submission_config=sub_config) as validator:
            validator.validate()
            validator.create_reports()
            validator.update_config_with_validation_result()

    if task == SUBMIT:
        with StudySubmitter(submission_dir, vcf_files, metadata_file, submission_config=sub_config) as submitter:
            submitter.submit()
