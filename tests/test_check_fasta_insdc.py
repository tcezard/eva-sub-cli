import os
from unittest import TestCase

# TODO Remove once deployed to prod
import bin.check_fasta_insdc as check_fasta_insdc
check_fasta_insdc.CONTIG_ALIAS_SERVER = 'https://wwwdev.ebi.ac.uk/eva/webservices/contig-alias/v1/chromosomes/md5checksum'

from bin.check_fasta_insdc import assess_fasta, get_insdc_from_metadata


class TestFastaChecker(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def test_assess_fasta_is_insdc(self):
        input_fasta = os.path.join(self.resource_dir, 'fasta_files', 'Saccharomyces_cerevisiae_I.fa')
        results = assess_fasta(input_fasta, None)
        assert results == {
            'all_insdc': True,
            'sequences': [{'sequence_name': 'I', 'sequence_md5': '6681ac2f62509cfc220d78751b8dc524', 'insdc': True}],
            'possible_assemblies': {'GCA_000146045.2'}
        }
        input_fasta = os.path.join(self.resource_dir, 'fasta_files', 'input_passed.fa')
        results = assess_fasta(input_fasta, None)
        assert results == {
            'all_insdc': False,
            'sequences': [{'sequence_name': 'chr1', 'sequence_md5': 'd2b3f22704d944f92a6bc45b6603ea2d', 'insdc': False}],
            'possible_assemblies': set()
        }

    def test_assess_fasta_matches_metadata(self):
        input_fasta = os.path.join(self.resource_dir, 'fasta_files', 'Saccharomyces_cerevisiae_I.fa')
        results = assess_fasta(input_fasta, 'GCA_000146045.2')
        assert results == {
            'all_insdc': True,
            'sequences': [
                {'sequence_name': 'I', 'sequence_md5': '6681ac2f62509cfc220d78751b8dc524', 'insdc': True}],
            'possible_assemblies': {'GCA_000146045.2'},
            'metadata_assembly_compatible': True
        }
        results = assess_fasta(input_fasta, 'GCA_002915635.1')
        assert results == {
            'all_insdc': True,
            'sequences': [
                {'sequence_name': 'I', 'sequence_md5': '6681ac2f62509cfc220d78751b8dc524', 'insdc': True}],
            'possible_assemblies': {'GCA_000146045.2'},
            'metadata_assembly_compatible': False
        }

    def test_get_insdc_from_metadata(self):
        metadata_json = os.path.join(self.resource_dir, 'sample_checker', 'metadata.json')
        vcf_file = os.path.join(self.resource_dir, 'sample_checker', 'example1.vcf.gz')
        reference = get_insdc_from_metadata(vcf_file, metadata_json)
        assert reference == 'GCA_000001405.27'
