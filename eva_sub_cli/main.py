#!/usr/bin/env python
import csv
import os
from ebi_eva_common_pyutils.config import WritableConfig

from eva_sub_cli import SUB_CLI_CONFIG_FILE, __version__
from eva_sub_cli.validators.docker_validator import DockerValidator
from eva_sub_cli.validators.native_validator import NativeValidator
from eva_sub_cli.validators.validator import READY_FOR_SUBMISSION_TO_EVA
from eva_sub_cli.submit import StudySubmitter

VALIDATE = 'validate'
SUBMIT = 'submit'
DOCKER = 'docker'
NATIVE = 'native'


def get_vcf_files(mapping_file):
    vcf_files = []
    with open(mapping_file) as open_file:
        reader = csv.DictReader(open_file, delimiter=',')
        for row in reader:
            vcf_files.append(row['vcf'])
    return vcf_files


def create_vcf_files_mapping(submission_dir, vcf_files, assembly_fasta):
    mapping_file = os.path.join(submission_dir, 'vcf_mapping_file.csv')
    with open(mapping_file, 'w') as open_file:
        writer = csv.writer(open_file, delimiter=',')
        writer.writerow(['vcf', 'fasta', 'report'])
        for vcf_file in vcf_files:
            writer.writerow([os.path.abspath(vcf_file), os.path.abspath(assembly_fasta)])
    return mapping_file


def orchestrate_process(submission_dir, vcf_files_mapping, vcf_files, assembly_fasta, metadata_json, metadata_xlsx,
                        tasks, executor, resume, username=None, password=None, **kwargs):
    # load config
    config_file_path = os.path.join(submission_dir, SUB_CLI_CONFIG_FILE)
    sub_config = WritableConfig(config_file_path, version=__version__)

    # Get the provided metadata
    metadata_file = metadata_json or metadata_xlsx

    # Get the provided VCF and assembly
    if vcf_files and assembly_fasta:
        vcf_files_mapping = create_vcf_files_mapping(submission_dir, vcf_files, assembly_fasta)
    vcf_files = get_vcf_files(vcf_files_mapping)

    # Validation is mandatory so if submit is requested then VALIDATE must have run before or be requested as well
    if SUBMIT in tasks and not sub_config.get(READY_FOR_SUBMISSION_TO_EVA, False):
        if VALIDATE not in tasks:
            tasks.append(VALIDATE)

    if VALIDATE in tasks:
        if executor == DOCKER:
            validator = DockerValidator(vcf_files_mapping, submission_dir, metadata_json, metadata_xlsx,
                                        submission_config=sub_config)
        # default to native execution
        else:
            validator = NativeValidator(vcf_files_mapping, submission_dir, metadata_json, metadata_xlsx,
                                        submission_config=sub_config)
        with validator:
            validator.validate_and_report()
            if not metadata_json:
                metadata_json = os.path.join(validator.output_dir, 'metadata.json')
            sub_config.set('metadata_json', value=metadata_json)
            sub_config.set('vcf_files', value=vcf_files)

    if SUBMIT in tasks:
        with StudySubmitter(submission_dir, submission_config=sub_config, username=username, password=password) as submitter:
            submitter.submit(resume=resume)
