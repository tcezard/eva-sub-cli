import os
from argparse import ArgumentParser

from ebi_eva_common_pyutils.config import WritableConfig
from ebi_eva_common_pyutils.logger import logging_config

from cli import SUB_CLI_CONFIG_FILE, __version__
from cli.docker_validator import DockerValidator, docker_path, container_image
from cli.submit import StudySubmitter

VALIDATION_OUTPUT_DIR = "validation_output"
VALIDATE = 'validate'
SUBMIT = 'submit'
RESUME = 'resume'

logging_config.add_stdout_handler()


def get_docker_validator(vcf_files_mapping, output_dir, metadata_json, metadata_xlsx,
                         arg_container, arg_docker, sub_config):
    docker = arg_docker or docker_path
    container = arg_container or container_image
    validation_output_dir = os.path.join(output_dir, VALIDATION_OUTPUT_DIR)
    return DockerValidator(vcf_files_mapping, validation_output_dir, metadata_json, metadata_xlsx,
                           container, docker, sub_config)


if __name__ == "__main__":
    argparser = ArgumentParser(description='EVA SUB CLI - to validate and submit a submission')
    argparser.add_argument('--task', required=True, choices=[VALIDATE, SUBMIT, RESUME],
                           help='Select a task to perform')
    argparser.add_argument('--submission_dir', required=True, type=str,
                           help='Full path to the directory where all processing will be done and submission info is/will be stored')
    argparser.add_argument("--docker_path", help="Full path to the docker installation, "
                                                 "not required if docker is available on path", required=False)
    argparser.add_argument("--container_name", help="Name of the docker container", required=False)
    argparser.add_argument("--vcf_files_mapping", required=False,
                           help="csv file with the mappings for vcf files, fasta and assembly report")
    group = argparser.add_mutually_exclusive_group(required=False)
    group.add_argument("--metadata_json",
                       help="Json file that describe the project, analysis, samples and files")
    group.add_argument("--metadata_xlsx",
                       help="Excel spreadsheet  that describe the project, analysis, samples and files")

    args = argparser.parse_args()

    # load config
    config_file_path = os.path.join(args.submission_dir, SUB_CLI_CONFIG_FILE)
    sub_config = WritableConfig(config_file_path, version=__version__)

    if args.task == RESUME:
        submitter = StudySubmitter(args.submission_dir, submission_config=sub_config)
        submitter.upload_submission()

    if args.task == VALIDATE or args.task == SUBMIT:
        if not args.vcf_files_mapping:
            raise Exception(f"Please provide csv file with the mappings of vcf files using --vcf_files_mapping")
        if not args.metadata_json and not args.metadata_xlsx:
            raise Exception(f"Please provide the file that describes the project, analysis, samples and files "
                            f"using either --metadata_json or --metadata_xlsx")
        docker_validator = get_docker_validator(args.vcf_files_mapping, args.submission_dir, args.metadata_json,
                                                args.metadata_xlsx, args.container_name, args.docker_path, sub_config)
        docker_validator.validate()
        docker_validator.create_reports()

        if args.task == SUBMIT:
            docker_validator.update_config_with_validation_result()
            submitter = StudySubmitter(args.submission_dir)
            submitter.submit(args.submission_dir, submission_config=sub_config)
