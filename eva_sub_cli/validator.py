import csv
import os

from eva_sub_cli.reporter import Reporter


VALIDATION_OUTPUT_DIR = "validation_output"


class Validator(Reporter):

    def __init__(self, mapping_file, output_dir, metadata_json=None, metadata_xlsx=None, submission_config=None):
        super().__init__(mapping_file, os.path.join(output_dir, VALIDATION_OUTPUT_DIR),
                         submission_config=submission_config)
        self.metadata_json = metadata_json
        self.metadata_xlsx = metadata_xlsx

    def check_if_file_missing(self):
        files_missing = False
        missing_files_list = []
        with open(self.mapping_file) as open_file:
            reader = csv.DictReader(open_file, delimiter=',')
            for row in reader:
                if not os.path.exists(row['vcf']):
                    files_missing = True
                    missing_files_list.append(row['vcf'])
                if not os.path.exists(row['fasta']):
                    files_missing = True
                    missing_files_list.append(row['fasta'])
                if not os.path.exists(row['report']):
                    files_missing = True
                    missing_files_list.append(row['report'])
        return files_missing, missing_files_list
