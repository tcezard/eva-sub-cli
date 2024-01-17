import os
from unittest import TestCase

import yaml

from bin.genome_checker import compare_genome_and_name

class TestGenomeChecker(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')
    output_yaml = os.path.join(resource_dir, 'validation_output', 'sample_checker.yaml')
    os.makedirs(os.path.join(resource_dir, 'validation_output'), exist_ok=True)

    def tearDown(self) -> None:
        if os.path.exists(self.output_yaml):
            os.remove(self.output_yaml)

    def test_compare_genome_and_name(self):
        fasta_path = os.path.join(self.resource_dir, 'fasta_files', 'GCA_000146045.2.fa')
        compare_genome_and_name(genome_name='sacCer3', genome_fasta=fasta_path)
