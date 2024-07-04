import argparse
import json
import re

import requests
import yaml

from retry import retry
from ebi_eva_common_pyutils.ena_utils import download_xml_from_ena
from ebi_eva_common_pyutils.logger import logging_config


logger = logging_config.get_logger(__name__)

PARENT_PROJECT_KEY = 'parentProject'
CHILD_PROJECTS_KEY = 'childProjects'
PEER_PROJECTS_KEY = 'peerProjects'


@retry(tries=4, delay=2, backoff=1.2, jitter=(1, 3))
def check_existing_project_in_ena(project_accession):
    """Check if a project accession exists and is public in ENA"""
    try:
        download_xml_from_ena(f'https://www.ebi.ac.uk/ena/browser/api/xml/{project_accession}')
    except requests.exceptions.HTTPError:
        return False
    return True


def check_project_accession(errors, project_acc, key_name, idx=None):
    if not check_existing_project_in_ena(project_acc):
        field_name = f'/project/{key_name}'
        if idx is not None:
            field_name += f'/{idx}'
        errors[field_name] = f'{project_acc} does not exist or is private'


def write_result_yaml(output_yaml, results):
    with open(output_yaml, 'w') as open_yaml:
        yaml.safe_dump(data=results, stream=open_yaml)


def check_all_project_accessions(metadata):
    """Check that ENA project accessions exist and are public"""
    errors = {}
    project = metadata['project']
    check_project_accession(errors, project[PARENT_PROJECT_KEY], PARENT_PROJECT_KEY)
    for idx, accession in enumerate(project[CHILD_PROJECTS_KEY]):
        check_project_accession(errors, accession, CHILD_PROJECTS_KEY, idx)
    for idx, accession in enumerate(project[PEER_PROJECTS_KEY]):
        check_project_accession(errors, accession, PEER_PROJECTS_KEY, idx)
    return errors


def main():
    arg_parser = argparse.ArgumentParser(description='Perform semantic checks on the metadata')
    arg_parser.add_argument('--metadata_json', required=True, dest='metadata_json', help='EVA metadata json file')
    arg_parser.add_argument('--output_yaml', required=True, dest='output_yaml',
                            help='Path to the location of the results')
    args = arg_parser.parse_args()
    logging_config.add_stdout_handler()
    with open(args.metadata_json) as open_json:
        metadata = json.load(open_json)
        errors = check_all_project_accessions(metadata)
    # TODO other errors
    write_result_yaml(args.output_yaml, errors)


if __name__ == "__main__":
    main()
