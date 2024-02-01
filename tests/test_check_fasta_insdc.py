import os
from unittest import TestCase


from bin.check_fasta_insdc import assess_fasta


class TestFastaChecker(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def test_assess_fasta(self):
        input_fasta = os.path.join(self.resource_dir, 'fasta_files', 'Saccharomyces_cerevisiae_I.fa')
        results = assess_fasta(input_fasta)
        assert results == {'sequences': [{'sequence_name': 'I', 'sequence_md5': '6681ac2f62509cfc220d78751b8dc524', 'insdc': True}]}
        input_fasta = os.path.join(self.resource_dir, 'fasta_files', 'input_passed.fa')
        results = assess_fasta(input_fasta)
        assert results == {'sequences': [{'sequence_name': 'chr1', 'sequence_md5': 'd2b3f22704d944f92a6bc45b6603ea2d', 'insdc': False}]}