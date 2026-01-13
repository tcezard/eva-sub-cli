import os
import subprocess
import tempfile
import shutil
from unittest import TestCase
from unittest.mock import patch

from eva_sub_cli.validators.native_validator import NativeValidator
from eva_sub_cli.validators.validator import VCF_CHECK, ASSEMBLY_CHECK, METADATA_CHECK, SAMPLE_CHECK


class TestNativeValidator(TestCase):
    resources_folder = os.path.join(os.path.dirname(__file__), 'resources')
    vcf_files = os.path.join(resources_folder, 'vcf_files')
    fasta_files = os.path.join(resources_folder, 'fasta_files')
    assembly_reports = os.path.join(resources_folder, 'assembly_reports')

    def setUp(self):
        self.test_run_dir = tempfile.mkdtemp()
        self.mapping_file = os.path.join(self.test_run_dir, 'vcf_files_metadata.csv')
        self.metadata_json = os.path.join(self.test_run_dir, 'metadata.json')

        # Create a minimal mapping file
        with open(self.mapping_file, 'w') as f:
            f.write('vcf,fasta,report\n')
            f.write(f'{os.path.join(self.vcf_files, "input_passed.vcf")},'
                    f'{os.path.join(self.fasta_files, "input_passed.fa")},'
                    f'{os.path.join(self.assembly_reports, "input_passed.txt")}\n')

        # Create a minimal metadata.json file
        with open(self.metadata_json, 'w') as f:
            f.write('{"project": {}, "analysis": [], "sample": [], "files": []}')

    def tearDown(self):
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)

    def test_init_with_defaults(self):
        """Test NativeValidator initialization with default parameters."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        assert validator.mapping_file == self.mapping_file
        assert validator.submission_dir == self.test_run_dir
        assert validator.project_title == 'Test Project'
        assert validator.metadata_json == self.metadata_json
        assert validator.vcf_validator_path == 'vcf_validator'
        assert validator.assembly_checker_path == 'vcf_assembly_checker'
        assert validator.biovalidator_path == 'biovalidator'
        assert validator.nextflow_config is None

    def test_init_with_custom_paths(self):
        """Test NativeValidator initialization with custom executable paths."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            vcf_validator_path='/custom/path/vcf_validator',
            assembly_checker_path='/custom/path/vcf_assembly_checker',
            biovalidator_path='/custom/path/biovalidator',
            nextflow_config='/custom/nextflow.config'
        )
        assert validator.vcf_validator_path == '/custom/path/vcf_validator'
        assert validator.assembly_checker_path == '/custom/path/vcf_assembly_checker'
        assert validator.biovalidator_path == '/custom/path/biovalidator'
        assert validator.nextflow_config == '/custom/nextflow.config'

    def test_get_validation_cmd_with_json_metadata(self):
        """Test validation command generation with JSON metadata."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        cmd = validator.get_validation_cmd()

        assert 'nextflow run' in cmd
        assert 'validation.nf' in cmd
        assert f'--vcf_files_mapping {self.mapping_file}' in cmd
        assert f'--metadata_json {self.metadata_json}' in cmd
        assert f'--output_dir {validator.output_dir}' in cmd
        assert '--executable.vcf_validator vcf_validator' in cmd
        assert '--executable.vcf_assembly_checker vcf_assembly_checker' in cmd
        assert '--executable.biovalidator biovalidator' in cmd

    def test_get_validation_cmd_with_xlsx_metadata(self):
        """Test validation command generation with XLSX metadata."""
        xlsx_file = os.path.join(self.resources_folder, 'EVA_Submission_test.xlsx')
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_xlsx=xlsx_file,
            metadata_xlsx_version='2.0.0'
        )
        cmd = validator.get_validation_cmd()

        assert f'--metadata_xlsx {xlsx_file}' in cmd
        assert '--conversion_configuration_name spreadsheet2json_conf_V2.yaml' in cmd
        assert '--metadata_json' not in cmd

    def test_get_validation_cmd_with_xlsx_metadata_v3(self):
        """Test validation command generation with XLSX metadata version 3."""
        xlsx_file = os.path.join(self.resources_folder, 'EVA_Submission_test.xlsx')
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_xlsx=xlsx_file,
            metadata_xlsx_version='3.0.0'
        )
        cmd = validator.get_validation_cmd()

        assert f'--metadata_xlsx {xlsx_file}' in cmd
        assert '--conversion_configuration_name spreadsheet2json_conf.yaml' in cmd

    def test_get_validation_cmd_with_shallow_validation(self):
        """Test validation command includes shallow_validation flag when enabled."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            shallow_validation=True,
            validation_tasks=[VCF_CHECK]
        )
        cmd = validator.get_validation_cmd()
        assert '--shallow_validation true' in cmd

    def test_get_validation_cmd_without_shallow_validation(self):
        """Test validation command without shallow_validation flag."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            shallow_validation=False
        )
        cmd = validator.get_validation_cmd()
        assert '--shallow_validation' not in cmd

    def test_get_validation_cmd_with_nextflow_config(self):
        """Test validation command includes nextflow config when specified."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            nextflow_config='/path/to/nextflow.config'
        )
        cmd = validator.get_validation_cmd()
        assert '-c /path/to/nextflow.config' in cmd

    def test_get_validation_cmd_with_specific_tasks(self):
        """Test validation command with specific validation tasks."""
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            validation_tasks=[VCF_CHECK, METADATA_CHECK]
        )
        cmd = validator.get_validation_cmd()
        assert '--tasks vcf_check,metadata_check' in cmd

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    def test_verify_executables_installed_success(self, mock_run_command):
        """Test that verify_executables_installed succeeds when all executables are available."""
        mock_run_command.return_value = None

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        # Should not raise any exception
        validator.verify_executables_installed()

        # Verify that all three executables were checked
        assert mock_run_command.call_count == 3

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    def test_verify_executables_installed_vcf_validator_missing(self, mock_run_command):
        """Test that verify_executables_installed raises error when vcf_validator is missing."""
        mock_run_command.side_effect = subprocess.CalledProcessError(1, 'vcf_validator --version')

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        with self.assertRaises(RuntimeError) as context:
            validator.verify_executables_installed()

        assert 'vcf-validator' in str(context.exception)

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    def test_verify_executables_installed_assembly_checker_missing(self, mock_run_command):
        """Test that verify_executables_installed raises error when assembly_checker is missing."""
        def side_effect(description, command, **kwargs):
            if 'vcf_assembly_checker' in command:
                raise subprocess.CalledProcessError(1, command)
            return None

        mock_run_command.side_effect = side_effect

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        with self.assertRaises(RuntimeError) as context:
            validator.verify_executables_installed()

        assert 'vcf-assembly-checker' in str(context.exception)

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    def test_verify_executables_installed_biovalidator_missing(self, mock_run_command):
        """Test that verify_executables_installed raises error when biovalidator is missing."""
        def side_effect(description, command, **kwargs):
            if 'biovalidator' in command:
                raise subprocess.CalledProcessError(1, command)
            return None

        mock_run_command.side_effect = side_effect

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        with self.assertRaises(RuntimeError) as context:
            validator.verify_executables_installed()

        assert 'biovalidator' in str(context.exception)

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    @patch('eva_sub_cli.validators.native_validator.NativeValidator.verify_executables_installed')
    def test_run_validator_success(self, mock_verify, mock_run_command):
        """Test that run_validator executes correctly."""
        mock_verify.return_value = None
        mock_run_command.return_value = None

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        original_cwd = os.getcwd()

        validator.run_validator()

        # Verify that verify_executables_installed was called
        mock_verify.assert_called_once()

        # Verify that the validation command was executed
        mock_run_command.assert_called_once()
        call_args = mock_run_command.call_args
        assert 'Run Validation using Nextflow' in call_args[0][0]
        assert 'nextflow run' in call_args[0][1]

        # Verify that the working directory is restored
        assert os.getcwd() == original_cwd

    @patch('eva_sub_cli.validators.native_validator.NativeValidator._run_quiet_command')
    @patch('eva_sub_cli.validators.native_validator.NativeValidator.verify_executables_installed')
    def test_run_validator_nextflow_failure(self, mock_verify, mock_run_command):
        """Test that run_validator handles Nextflow failure gracefully."""
        mock_verify.return_value = None
        mock_run_command.side_effect = subprocess.CalledProcessError(1, 'nextflow')

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        original_cwd = os.getcwd()

        # Should not raise, just log the error
        validator.run_validator()

        # Verify that the working directory is restored even after failure
        assert os.getcwd() == original_cwd

    @patch('eva_sub_cli.validators.native_validator.NativeValidator.run_validator')
    def test_validate_calls_run_validator(self, mock_run_validator):
        """Test that _validate method calls run_validator."""
        mock_run_validator.return_value = None

        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        validator._validate()

        mock_run_validator.assert_called_once()

    def test_validation_tasks_passed_to_command(self):
        """Test that validation tasks are correctly passed to the command."""
        all_tasks = [VCF_CHECK, ASSEMBLY_CHECK, METADATA_CHECK, SAMPLE_CHECK]
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json,
            validation_tasks=all_tasks
        )
        cmd = validator.get_validation_cmd()
        assert '--tasks vcf_check,assembly_check,metadata_check,sample_check' in cmd

    def test_inherits_from_validator(self):
        """Test that NativeValidator inherits from Validator."""
        from eva_sub_cli.validators.validator import Validator
        validator = NativeValidator(
            mapping_file=self.mapping_file,
            submission_dir=self.test_run_dir,
            project_title='Test Project',
            metadata_json=self.metadata_json
        )
        assert isinstance(validator, Validator)
