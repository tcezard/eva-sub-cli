import os.path
from unittest import TestCase

from eva_sub_cli.validators.validation_results_parsers import vcf_check_errors_is_critical, parse_assembly_check_log, \
    parse_assembly_check_report


class TestValidationParsers(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def test_vcf_check_errors_is_critical(self):
        errors = [
            'INFO AC does not match the specification Number=A (expected 1 value(s)). AC=100,37.',
            'Sample #10, field PL does not match the meta specification Number=G (expected 2 value(s)). PL=.. It must derive its number of values from the ploidy of GT (if present), or assume diploidy. Contains 1 value(s), expected 2 (derived from ploidy 1).',
            'Sample #102, field AD does not match the meta specification Number=R (expected 3 value(s)). AD=..'
        ]
        expected_return = [False, True, True]
        for i, error in enumerate(errors):
            assert vcf_check_errors_is_critical(error) == expected_return[i]

    def test_parse_assembly_check_log(self):
        assembly_check_log = os.path.join(self.resource_dir, 'assembly_check', 'invalid.vcf.assembly_check.log')
        error_list, nb_error, match, total = parse_assembly_check_log(assembly_check_log)
        assert error_list == ["The assembly checking could not be completed: Contig 'chr23' not found in assembly report"]

    def test_parse_assembly_check_report(self):
        assembly_check_report = os.path.join(self.resource_dir, 'assembly_check', 'invalid.vcf.text_assembly_report.txt')
        mismatch_list, nb_mismatch, error_list, nb_error = parse_assembly_check_report(assembly_check_report)
        assert mismatch_list[0] == "Line 43: Chromosome chr1, position 955679, reference allele 'T' does not match the reference sequence, expected 'C'"
        assert nb_mismatch == 12
        assert error_list == ['Chromosome scaffold_chr1 is not present in FASTA file']
        assert nb_error == 1
