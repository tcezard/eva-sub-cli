import os
import shutil
from unittest import TestCase

import pytest

from eva_sub_cli.validators.native_validator import NativeValidator
from eva_sub_cli.validators.validator import METADATA_CHECK
from tests.test_utils import create_mapping_file


@pytest.mark.integration('You need to install java, nextflow, vcf_validator, vcf_assembly_checker, biovalidator (and md5sum, stat for mac)')
class TestNativeValidatorSampleInVCF(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')
    sample_in_vcf_dir = os.path.join(resource_dir, 'sample_in_vcf_check')
    fasta_file = os.path.join(sample_in_vcf_dir, 'fake_fasta.fa')

    def setUp(self):
        self.test_run_dir = os.path.join(self.resource_dir, 'test_native_run')
        os.makedirs(self.test_run_dir, exist_ok=True)
        self.mapping_file = os.path.join(self.test_run_dir, 'vcf_files_metadata.csv')

    def tearDown(self):
        shutil.rmtree(self.test_run_dir)

    def _build_validator(self, metadata_json, vcf_file, tasks):
        create_mapping_file(
            self.mapping_file,
            vcf_files=[vcf_file],
            fasta_files=[self.fasta_file],
            assembly_reports=None,
        )
        return NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=metadata_json,
            validation_tasks=tasks,
        )

    def _get_metadata_errors(self, validator):
        # Includes both the JSON schema (biovalidator) and the semantic check errors
        return validator.results[METADATA_CHECK]['json_errors']

    def _sample_in_vcf_errors(self, errors):
        # Missing required property errors are reported against the parent object so check the description too
        return [e for e in errors if 'sampleInVCF' in e.get('property', '') or 'sampleInVCF' in e.get('description', '')]

    def test_af_vcf_without_sample_in_vcf(self):
        """AF evidence type: omitting sampleInVCF should produce no error."""
        validator = self._build_validator(
            os.path.join(self.sample_in_vcf_dir, 'metadata_af_no_sample_in_vcf.json'),
            os.path.join(self.sample_in_vcf_dir, 'allele_freq.vcf'),
            [METADATA_CHECK]
        )
        validator.validate()
        errors = self._get_metadata_errors(validator)
        self.assertEqual(self._sample_in_vcf_errors(errors), [])

    def test_af_vcf_with_sample_in_vcf(self):
        """AF evidence type: providing sampleInVCF is permitted and should produce no error."""
        validator = self._build_validator(
            os.path.join(self.sample_in_vcf_dir, 'metadata_af_with_sample_in_vcf.json'),
            os.path.join(self.sample_in_vcf_dir, 'allele_freq.vcf'),
            [METADATA_CHECK]
        )
        validator.validate()
        errors = self._get_metadata_errors(validator)
        self.assertEqual(self._sample_in_vcf_errors(errors), [])

    def test_af_vcf_with_null_sample_in_vcf(self):
        """AF evidence type: sampleInVCF set to null (empty cell in the spreadsheet) should produce no error."""
        validator = self._build_validator(
            os.path.join(self.sample_in_vcf_dir, 'metadata_af_null_sample_in_vcf.json'),
            os.path.join(self.sample_in_vcf_dir, 'allele_freq.vcf'),
            [METADATA_CHECK]
        )
        validator.validate()
        errors = self._get_metadata_errors(validator)
        self.assertEqual(self._sample_in_vcf_errors(errors), [])

    def test_genotype_vcf_without_sample_in_vcf(self):
        """Genotype evidence type: omitting sampleInVCF must produce one error per sample."""
        validator = self._build_validator(
            os.path.join(self.sample_in_vcf_dir, 'metadata_genotype_no_sample_in_vcf.json'),
            os.path.join(self.sample_in_vcf_dir, 'genotype.vcf'),
            [METADATA_CHECK]
        )
        validator.validate()
        errors = self._get_metadata_errors(validator)
        sample_in_vcf_errors = self._sample_in_vcf_errors(errors)
        self.assertEqual(len(sample_in_vcf_errors), 3)

    def test_genotype_vcf_with_sample_in_vcf(self):
        """Genotype evidence type: providing sampleInVCF for every sample should produce no error."""
        validator = self._build_validator(
            os.path.join(self.sample_in_vcf_dir, 'metadata_genotype_with_sample_in_vcf.json'),
            os.path.join(self.sample_in_vcf_dir, 'genotype.vcf'),
            [METADATA_CHECK]
        )
        validator.validate()
        errors = self._get_metadata_errors(validator)
        self.assertEqual(self._sample_in_vcf_errors(errors), [])
