import argparse
import json

from eva_sub_cli.semantic_metadata import SemanticMetadataChecker


def main():
    arg_parser = argparse.ArgumentParser(description='Perform semantic checks on the metadata')
    arg_parser.add_argument('--metadata_json', required=True, dest='metadata_json', help='EVA metadata json file')
    arg_parser.add_argument('--output_yaml', required=True, dest='output_yaml',
                            help='Path to the location of the results')
    args = arg_parser.parse_args()

    with open(args.metadata_json) as open_json:
        metadata = json.load(open_json)
        checker = SemanticMetadataChecker(metadata)
        checker.check_all()
        checker.write_result_yaml(args.output_yaml)
