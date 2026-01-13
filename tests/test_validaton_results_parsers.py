import os.path
import tempfile
from unittest import TestCase

from eva_sub_cli.validators.validation_results_parsers import (
    vcf_check_errors_is_critical, parse_assembly_check_log,
    parse_assembly_check_report, parse_vcf_check_report,
    parse_biovalidator_validation_results, convert_metadata_sheet,
    convert_metadata_row, convert_metadata_attribute, parse_metadata_property,
    parse_sample_metadata_property
)


class TestValidationParsers(TestCase):
    resource_dir = os.path.join(os.path.dirname(__file__), 'resources')

    def test_vcf_check_errors_is_critical(self):
        errors = [
            ('INFO AC does not match the specification Number=A (expected 1 value(s)). AC=100,37.', False),
            ('Line 124385: Sample #10, field PL does not match the meta specification Number=G (expected 2 value(s)). '
             'PL=.. It must derive its number of values from the ploidy of GT (if present), or assume diploidy. '
             'Contains 1 value(s), expected 2 (derived from ploidy 1).', False),
            ('Line 124384: Sample #102, field AD does not match the meta specification Number=R (expected 3 value(s)). AD=..', False),
            ('Line 8: SAMPLE metadata Genomes is not a valid string (maybe it contains quotes?).', True),
            ('Line 6: FORMAT GQ metadata Type is not Integer.', False),
            ('Line 7: FORMAT PL metadata Number is not G.', False),
            ('Line 10: INFO AF metadata Number is not A.', True),
            ('Line 4039: FORMAT GQ metadata Type is not Integer.', False),
            ('Line 1525: Duplicated variant NA:5:C>T found.', True),
            ('Line 8: Metadata ID contains a character different from alphanumeric, dot, underscore and dash.', True),
            ('Line 14: FORMAT metadata Number is not a number, A, G or dot.', True),
            ('Line 13: Contig is not sorted by position. Contig 1 position 5600263 found after 12313283.', True),
            ('Line 1067: INFO SVLEN must be equal to "length of ALT - length of REF" for non-symbolic alternate '
             'alleles. SVLEN=31, expected value=33.', False),
        ]
        for error, is_critical in errors:
            assert vcf_check_errors_is_critical(error) == is_critical, error

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

    def test_parse_vcf_check_report_valid(self):
        """Test parse_vcf_check_report with a valid VCF report."""
        vcf_check_report = os.path.join(
            self.resource_dir, 'validation_reports', 'validation_output',
            'vcf_format', 'input_passed.vcf.errors.1680102476854.txt'
        )
        valid, warning_count, error_count, critical_count, error_list, critical_list = parse_vcf_check_report(vcf_check_report)
        assert valid is True
        assert warning_count == 0
        assert error_count == 0
        assert critical_count == 0
        assert error_list == []
        assert critical_list == []

    def test_parse_vcf_check_report_with_errors(self):
        """Test parse_vcf_check_report with a report containing errors."""
        # Create a temporary file with errors
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('According to the VCF specification, the input file is not valid\n')
            f.write('warning: Some warning message\n')
            f.write('Line 8: SAMPLE metadata Genomes is not a valid string (maybe it contains quotes?).\n')
            f.write('Line 6: FORMAT GQ metadata Type is not Integer.\n')
            temp_file = f.name

        try:
            valid, warning_count, error_count, critical_count, error_list, critical_list = parse_vcf_check_report(temp_file)
            assert valid is False
            assert warning_count == 1
            assert error_count == 1  # FORMAT GQ is non-critical
            assert critical_count == 1  # SAMPLE metadata is critical
            assert len(critical_list) == 1
            assert 'SAMPLE metadata Genomes' in critical_list[0]
        finally:
            os.unlink(temp_file)

    def test_parse_vcf_check_report_max_errors(self):
        """Test parse_vcf_check_report respects max error limit."""
        # Create a temporary file with many errors
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('According to the VCF specification, the input file is not valid\n')
            # Add 15 critical errors (only first 10 should be reported)
            for i in range(15):
                f.write(f'Line {i}: Duplicated variant chr1:{i}:A>G found.\n')
            temp_file = f.name

        try:
            valid, warning_count, error_count, critical_count, error_list, critical_list = parse_vcf_check_report(temp_file)
            assert valid is False
            assert critical_count == 15  # Total count includes all
            assert len(critical_list) == 10  # But only first 10 reported
        finally:
            os.unlink(temp_file)

    def test_parse_biovalidator_validation_results_with_file(self):
        """Test parse_biovalidator_validation_results with a real file."""
        metadata_check_file = os.path.join(
            self.resource_dir, 'validation_reports', 'validation_output',
            'other_validations', 'metadata_validation.txt'
        )
        errors = parse_biovalidator_validation_results(metadata_check_file)
        assert errors is not None
        assert len(errors) > 0
        # Check that errors have required keys
        for error in errors:
            assert 'property' in error
            assert 'description' in error

    def test_parse_biovalidator_validation_results_none_file(self):
        """Test parse_biovalidator_validation_results with None input."""
        result = parse_biovalidator_validation_results(None)
        assert result is None

    def test_parse_biovalidator_validation_results_successful(self):
        """Test parse_biovalidator_validation_results with successful validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('Validation passed successfully.\n')
            temp_file = f.name

        try:
            errors = parse_biovalidator_validation_results(temp_file)
            assert errors == []
        finally:
            os.unlink(temp_file)

    def test_parse_biovalidator_validation_results_with_ansi_codes(self):
        """Test parse_biovalidator_validation_results strips ANSI escape codes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\x1B[1m\x1B[31m\x1B[40m Validation failed with following error(s):\n')
            f.write(' \x1B[0m\n')
            f.write('\x1B[1m\x1B[31m\x1B[40m /project/title\n')
            f.write('\tshould have required property \'title\'\n')
            f.write(' \x1B[0m\n')
            temp_file = f.name

        try:
            errors = parse_biovalidator_validation_results(temp_file)
            assert len(errors) == 1
            assert errors[0]['property'] == '/project/title'
            assert 'title' in errors[0]['description']
        finally:
            os.unlink(temp_file)


class TestMetadataConversion(TestCase):
    """Tests for metadata conversion functions."""

    def setUp(self):
        """Set up test configuration that mimics the spreadsheet2json_conf.yaml."""
        self.xls2json_conf = {
            'worksheets': {
                'Submitter Details': 'submitterDetails',
                'Project': 'project',
                'Analysis': 'analysis',
                'Sample': 'sample',
                'Files': 'files'
            },
            'Project': {
                'header_row': 3,
                'required': {
                    'Project Title': 'title'
                },
                'optional': {
                    'Description': 'description',
                    'Taxonomy ID': 'taxId'
                }
            },
            'Analysis': {
                'header_row': 2,
                'required': {
                    'Analysis Alias': 'analysisAlias',
                    'Description': 'description',
                    'Reference': 'referenceGenome'
                },
                'optional': {
                    'Platform': 'platform'
                }
            },
            'Sample': {
                'header_row': 3,
                'required': {
                    'Analysis Alias': 'analysisAlias',
                    'Sample Name in VCF': 'sampleInVCF'
                },
                'optional': {
                    'Sample Accession': 'bioSampleAccession'
                }
            }
        }

    def test_convert_metadata_sheet(self):
        """Test convert_metadata_sheet converts JSON attribute to sheet name."""
        assert convert_metadata_sheet('project', self.xls2json_conf) == 'Project'
        assert convert_metadata_sheet('analysis', self.xls2json_conf) == 'Analysis'
        assert convert_metadata_sheet('sample', self.xls2json_conf) == 'Sample'
        assert convert_metadata_sheet('files', self.xls2json_conf) == 'Files'
        assert convert_metadata_sheet('submitterDetails', self.xls2json_conf) == 'Submitter Details'

    def test_convert_metadata_sheet_none(self):
        """Test convert_metadata_sheet returns None for None input."""
        assert convert_metadata_sheet(None, self.xls2json_conf) is None

    def test_convert_metadata_sheet_not_found(self):
        """Test convert_metadata_sheet returns None for unknown attribute."""
        assert convert_metadata_sheet('unknown', self.xls2json_conf) is None

    def test_convert_metadata_row_with_header_row(self):
        """Test convert_metadata_row with header_row specified."""
        # Project has header_row: 3, so json row 0 becomes Excel row 3
        assert convert_metadata_row('Project', '0', self.xls2json_conf) == 3
        assert convert_metadata_row('Project', '1', self.xls2json_conf) == 4
        # Sample also has header_row: 3
        assert convert_metadata_row('Sample', '0', self.xls2json_conf) == 3
        assert convert_metadata_row('Sample', '2', self.xls2json_conf) == 5

    def test_convert_metadata_row_without_header_row(self):
        """Test convert_metadata_row defaults to header_row 2 when not specified."""
        # Create config without header_row
        conf = {
            'TestSheet': {
                'required': {'Field': 'field'}
            }
        }
        # Default header_row is 2, so json row 0 becomes Excel row 2
        assert convert_metadata_row('TestSheet', '0', conf) == 2
        assert convert_metadata_row('TestSheet', '1', conf) == 3

    def test_convert_metadata_row_none(self):
        """Test convert_metadata_row returns empty string for None input."""
        assert convert_metadata_row('Project', None, self.xls2json_conf) == ''

    def test_convert_metadata_attribute(self):
        """Test convert_metadata_attribute converts JSON attribute to column name."""
        # Test required attributes
        assert convert_metadata_attribute('Project', 'title', self.xls2json_conf) == 'Project Title'
        assert convert_metadata_attribute('Analysis', 'analysisAlias', self.xls2json_conf) == 'Analysis Alias'
        assert convert_metadata_attribute('Analysis', 'referenceGenome', self.xls2json_conf) == 'Reference'

        # Test optional attributes
        assert convert_metadata_attribute('Project', 'description', self.xls2json_conf) == 'Description'
        assert convert_metadata_attribute('Analysis', 'platform', self.xls2json_conf) == 'Platform'
        assert convert_metadata_attribute('Sample', 'bioSampleAccession', self.xls2json_conf) == 'Sample Accession'

    def test_convert_metadata_attribute_special_names(self):
        """Test convert_metadata_attribute handles special name mappings."""
        # 'species' maps to 'Scientific Name' and 'name' maps to 'BioSample Name'
        assert convert_metadata_attribute('Sample', 'species', self.xls2json_conf) == 'Scientific Name'
        assert convert_metadata_attribute('Sample', 'name', self.xls2json_conf) == 'BioSample Name'

    def test_convert_metadata_attribute_none(self):
        """Test convert_metadata_attribute returns empty string for None input."""
        assert convert_metadata_attribute('Project', None, self.xls2json_conf) == ''

    def test_convert_metadata_attribute_not_found(self):
        """Test convert_metadata_attribute returns None for unknown attribute."""
        result = convert_metadata_attribute('Project', 'unknownField', self.xls2json_conf)
        assert result is None


class TestMetadataPropertyParsing(TestCase):
    """Tests for metadata property parsing functions."""

    def test_parse_metadata_property_simple_path(self):
        """Test parse_metadata_property with simple path starting with dot."""
        sheet, row, col = parse_metadata_property('.files')
        assert sheet == 'files'
        assert row is None
        assert col is None

    def test_parse_metadata_property_with_index(self):
        """Test parse_metadata_property with array index."""
        sheet, row, col = parse_metadata_property('/analysis/0/description')
        assert sheet == 'analysis'
        assert row == '0'
        assert col == 'description'

    def test_parse_metadata_property_with_index_no_column(self):
        """Test parse_metadata_property with array index but no column."""
        sheet, row, col = parse_metadata_property('/sample/5')
        assert sheet == 'sample'
        assert row == '5'
        assert col is None

    def test_parse_metadata_property_simple_property(self):
        """Test parse_metadata_property with simple property path."""
        sheet, row, col = parse_metadata_property('/project/title')
        assert sheet == 'project'
        assert row is None
        assert col == 'title'

    def test_parse_metadata_property_top_level(self):
        """Test parse_metadata_property with top-level property."""
        sheet, row, col = parse_metadata_property('/files')
        assert sheet == 'files'
        assert row is None
        assert col is None

    def test_parse_metadata_property_biosample_characteristics(self):
        """Test parse_metadata_property with BioSample characteristics path."""
        sheet, row, col = parse_metadata_property('/sample/2/bioSampleObject/characteristics/taxId')
        assert sheet == 'sample'
        assert row == '2'
        assert col == 'taxId'

    def test_parse_metadata_property_biosample_name(self):
        """Test parse_metadata_property with BioSample name path."""
        sheet, row, col = parse_metadata_property('/sample/1/bioSampleObject/name')
        assert sheet == 'sample'
        assert row == '1'
        assert col == 'name'

    def test_parse_sample_metadata_property_characteristics(self):
        """Test parse_sample_metadata_property with characteristics."""
        sheet, row, col = parse_sample_metadata_property('/sample/3/bioSampleObject/characteristics/organism')
        assert sheet == 'sample'
        assert row == '3'
        assert col == 'organism'

    def test_parse_sample_metadata_property_name(self):
        """Test parse_sample_metadata_property with name."""
        sheet, row, col = parse_sample_metadata_property('/sample/0/bioSampleObject/name')
        assert sheet == 'sample'
        assert row == '0'
        assert col == 'name'

    def test_parse_sample_metadata_property_no_match(self):
        """Test parse_sample_metadata_property returns None for non-matching paths."""
        sheet, row, col = parse_sample_metadata_property('/project/title')
        assert sheet is None
        assert row is None
        assert col is None

    def test_parse_sample_metadata_property_partial_match(self):
        """Test parse_sample_metadata_property returns None for partial BioSample paths."""
        sheet, row, col = parse_sample_metadata_property('/sample/0/bioSampleObject')
        assert sheet is None
        assert row is None
        assert col is None
