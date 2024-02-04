#!/usr/bin/env python

from argparse import ArgumentParser

from ebi_eva_common_pyutils.logger import logging_config

from eva_sub_cli import  main
from eva_sub_cli.main import VALIDATE, SUBMIT


if __name__ == "__main__":
    argparser = ArgumentParser(description='EVA Submission CLI - validate and submit data to EVA')
    argparser.add_argument('--tasks', nargs='*', choices=[VALIDATE, SUBMIT], default=[SUBMIT],
                           help='Select a task to perform. Selecting VALIDATE will run the validation regardless of the outcome of '
                                'previous runs. Selecting SUBMIT will run validate only if the validation was not performed '
                                'successfully before and then run the submission.')
    argparser.add_argument('--submission_dir', required=True, type=str,
                           help='Full path to the directory where all processing will be done '
                                'and submission info is/will be stored')
    argparser.add_argument("--vcf_files_mapping", required=True,
                           help="csv file with the mappings for vcf files, fasta and assembly report")
    group = argparser.add_mutually_exclusive_group(required=True)
    group.add_argument("--metadata_json",
                       help="Json file that describe the project, analysis, samples and files")
    group.add_argument("--metadata_xlsx",
                       help="Excel spreadsheet  that describe the project, analysis, samples and files")
    argparser.add_argument("--username",
                           help="Username used for connecting to the ENA webin account")
    argparser.add_argument("--password",
                           help="Password used for connecting to the ENA webin account")
    argparser.add_argument("--resume", default=False, action='store_true',
                           help="Resume the process execution from where it left of. This is currently only supported "
                                "for the upload part of the SUBMIT task.")

    args = argparser.parse_args()

    logging_config.add_stdout_handler()

    main.orchestrate_process(args.submission_dir, args.vcf_files_mapping, args.metadata_json, args.metadata_xlsx,
                             args.tasks, args.resume)
