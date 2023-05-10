import os.path
import pprint
import shutil
from unittest import TestCase

from cli.validator import Validator, vcf_check_errors_is_critical


class Testvalidator(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def setUp(self) -> None:
        output_dir = os.path.join(self.resource_dir, 'validation_reports')
        self.validator = Validator(['input_passed.vcf'], output_dir)

    def tearDown(self) -> None:
        shutil.rmtree()

    def test__collect_validation_workflow_results(self):
        self.validator._collect_validation_workflow_results()

    def test_create_report(self):
        self.validator._collect_validation_workflow_results()
        self.validator.create_reports()

    def test_vcf_check_errors_is_critical(self):
        errors = [
            'INFO AC does not match the specification Number=A (expected 1 value(s)). AC=100,37.',
            'Sample #10, field PL does not match the meta specification Number=G (expected 2 value(s)). PL=.. It must derive its number of values from the ploidy of GT (if present), or assume diploidy. Contains 1 value(s), expected 2 (derived from ploidy 1).',
            'Sample #102, field AD does not match the meta specification Number=R (expected 3 value(s)). AD=..'
        ]
        for error in errors:
            print(vcf_check_errors_is_critical(error))

