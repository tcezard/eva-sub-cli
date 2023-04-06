import os.path
import pprint
from unittest import TestCase

from cli.validator import Validator


class Testvalidator(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def test__collect_validation_workflow_results(self):
        output_dir = os.path.join(self.resource_dir, 'validation_output')
        validator = Validator(['input_passed.vcf'], output_dir)
        validator._collect_validation_workflow_results()
        pprint.pprint(validator.results)

