#!/usr/bin/env python
import csv
import os
from ebi_eva_common_pyutils.config import WritableConfig
from ebi_eva_common_pyutils.logger import logging_config

from eva_sub_cli import SUB_CLI_CONFIG_FILE, __version__
from eva_sub_cli.docker_validator import DockerValidator
from eva_sub_cli.reporter import READY_FOR_SUBMISSION_TO_EVA
from eva_sub_cli.submit import StudySubmitter

VALIDATE = 'validate'
SUBMIT = 'submit'

def get_vcf_files(mapping_file):
    vcf_files = []
    with open(mapping_file) as open_file:
        reader = csv.DictReader(open_file, delimiter=',')
        for row in reader:
            vcf_files.append(row['vcf'])
    return vcf_files


def orchestrate_process(submission_dir, vcf_files_mapping, metadata_json, metadata_xlsx, tasks, resume):
    # load config
    config_file_path = os.path.join(submission_dir, SUB_CLI_CONFIG_FILE)
    sub_config = WritableConfig(config_file_path, version=__version__)

    metadata_file = metadata_json or metadata_xlsx
    vcf_files = get_vcf_files(vcf_files_mapping)

    # Validation is mandatory so if submit is requested then VALIDATE must have run before or be requested as well
    if SUBMIT in tasks and not sub_config.get(READY_FOR_SUBMISSION_TO_EVA, False):
        if VALIDATE not in tasks:
            tasks.append(VALIDATE)

    if VALIDATE in tasks:
        with DockerValidator(vcf_files_mapping, submission_dir, metadata_json, metadata_xlsx,
                             submission_config=sub_config) as validator:
            validator.validate()
            validator.create_reports()
            validator.update_config_with_validation_result()
    if SUBMIT in tasks:
        with StudySubmitter(submission_dir, vcf_files, metadata_file, submission_config=sub_config) as submitter:
            submitter.submit(resume=resume)
