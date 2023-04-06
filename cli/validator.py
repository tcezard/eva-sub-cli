#!/usr/bin/env python
import csv
import glob
import os


def resolve_single_file_path(file_path):
    files = glob.glob(file_path)
    if len(files) == 0:
        return None
    elif len(files) > 0:
        return files[0]


class Validator:

    def __init__(self, vcf_files, output_dir):
        self.output_dir = output_dir
        self.vcf_files = vcf_files
        self.results = {}


    def validate(self):
        self._validate()
        self._collect_validation_workflow_results()

    def _validate(self):
        raise NotImplementedError

    def parse_assembly_check_log(self, assembly_check_log):
        error_list = []
        nb_error, nb_mismatch = 0, 0
        match = total = None
        with open(assembly_check_log) as open_file:
            for line in open_file:
                if line.startswith('[error]'):
                    nb_error += 1
                    if nb_error < 11:
                        error_list.append(line.strip()[len('[error]'):])
                elif line.startswith('[info] Number of matches:'):
                    match, total = line.strip()[len('[info] Number of matches: '):].split('/')
                    match = int(match)
                    total = int(total)
        return error_list, nb_error, match, total

    def parse_assembly_check_report(self, assembly_check_report):
        mismatch_list = []
        nb_mismatch = 0
        nb_error = 0
        error_list = []
        with open(assembly_check_report) as open_file:
            for line in open_file:
                if 'does not match the reference sequence' in line:
                    nb_mismatch += 1
                    if nb_mismatch < 11:
                        mismatch_list.append(line.strip())
                elif 'Multiple synonyms' in line:
                    nb_error += 1
                    if nb_error < 11:
                        error_list.append(line.strip())
        return mismatch_list, nb_mismatch, error_list, nb_error

    def parse_vcf_check_report(self, vcf_check_report):
        valid = True
        error_list = []
        warning_count = error_count = 0
        with open(vcf_check_report) as open_file:
            for line in open_file:
                if 'warning' in line:
                    warning_count = 1
                elif line.startswith('According to the VCF specification'):
                    if 'not' in line:
                        valid = False
                else:
                    error_count += 1
                    if error_count < 11:
                        error_list.append(line.strip())
        return valid, error_list, error_count, warning_count

    def _collect_validation_workflow_results(self, ):
        # Collect information from the output and summarise in the config
        self._collect_vcf_check_results()
        self._collect_assembly_check_results()

    def _collect_vcf_check_results(self,):
        total_error = 0
        # detect output files for vcf check
        self.results['vcf_check'] = {}
        for vcf_file in self.vcf_files:
            vcf_name = os.path.basename(vcf_file)

            vcf_check_log = resolve_single_file_path(
                os.path.join(self.output_dir, 'vcf_format', vcf_name + '.vcf_format.log')
            )
            vcf_check_text_report = resolve_single_file_path(
                os.path.join(self.output_dir, 'vcf_format', vcf_name + '.*.txt')
            )
            vcf_check_db_report = resolve_single_file_path(
                os.path.join(self.output_dir, 'vcf_format', vcf_name + '.*.db')
            )

            if vcf_check_log and vcf_check_text_report and vcf_check_db_report:
                valid, error_list, error_count, warning_count = self.parse_vcf_check_report(vcf_check_text_report)
            else:
                valid, error_list, error_count, warning_count = (False, ['Process failed'], 1, 0)
            self.results['vcf_check'][vcf_name] = {
                'valid': valid,
                'error_list': error_list,
                'error_count': error_count,
                'warning_count': warning_count
            }
            total_error += error_count
            self.results['vcf_check']['total_error'] = total_error

    def _collect_assembly_check_results(self):
        # detect output files for assembly check
        total_error = 0
        self.results['assembly_check'] = {}
        for vcf_file in self.vcf_files:
            vcf_name = os.path.basename(vcf_file)

            assembly_check_log = resolve_single_file_path(
                os.path.join(self.output_dir, 'assembly_check',  vcf_name + '.assembly_check.log')
            )
            assembly_check_valid_vcf = resolve_single_file_path(
                os.path.join(self.output_dir, 'assembly_check', vcf_name + '.valid_assembly_report*')
            )
            assembly_check_text_report = resolve_single_file_path(
                os.path.join(self.output_dir, 'assembly_check', vcf_name + '*text_assembly_report*')
            )

            if assembly_check_log and assembly_check_valid_vcf and assembly_check_text_report:
                error_list_from_log, nb_error_from_log, match, total = \
                    self.parse_assembly_check_log(assembly_check_log)
                mismatch_list, nb_mismatch, error_list_from_report, nb_error_from_report = \
                    self.parse_assembly_check_report(assembly_check_text_report)
                nb_error = nb_error_from_log + nb_error_from_report
                error_list = error_list_from_log + error_list_from_report
            else:
                error_list, mismatch_list, nb_mismatch, nb_error, match, total = (['Process failed'], [], 0, 1, 0, 0)
            self.results['assembly_check'][vcf_name] = {
                'error_list': error_list,
                'mismatch_list': mismatch_list,
                'nb_mismatch': nb_mismatch,
                'nb_error': nb_error,
                'match': match,
                'total': total
            }
            total_error += nb_error + nb_mismatch
            self.results['assembly_check']['total_error'] = total_error

    def report(self):
        """Collect information from the config and write the report."""

        report_data = {
            'validation_date': self.eload_cfg.query('validation', 'validation_date'),
            'metadata_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'metadata_check')),
            'vcf_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'vcf_check')),
            'assembly_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'assembly_check')),
            'sample_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'sample_check')),
            'aggregation_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'aggregation_check')),
            'structural_variant_check': self._check_pass_or_fail(self.eload_cfg.query('validation',
                                                                                      'structural_variant_check')),
            'normalisation_check': self._check_pass_or_fail(self.eload_cfg.query('validation', 'normalisation_check')),
            'metadata_check_report': self._metadata_check_report(),
            'vcf_check_report': self._vcf_check_report(),
            'assembly_check_report': self._assembly_check_report(),
            'sample_check_report': self._sample_check_report(),
            'vcf_merge_report': self._vcf_merge_report(),
            'aggregation_report': self._aggregation_report(),
            'normalisation_check_report': self._normalisation_check_report(),
            'structural_variant_check_report': self._structural_variant_check_report()
        }

        report = """Validation performed on {validation_date}
Metadata check: {metadata_check}
VCF check: {vcf_check}
Assembly check: {assembly_check}
Sample names check: {sample_check}
Aggregation check: {aggregation_check}
Normalisation check: {normalisation_check}
Structural variant check: {structural_variant_check}
----------------------------------

Metadata check:
{metadata_check_report}
----------------------------------

VCF check:
{vcf_check_report}
----------------------------------

Assembly check:
{assembly_check_report}
----------------------------------

Sample names check:
{sample_check_report}
----------------------------------

Aggregation:
{aggregation_report}

----------------------------------

VCF merge:
{vcf_merge_report}

----------------------------------

Normalisation:
{normalisation_check_report}

----------------------------------

Structural variant check:
{structural_variant_check_report}

----------------------------------
"""
        print(report.format(**report_data))
