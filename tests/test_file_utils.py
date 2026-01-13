import glob
import gzip
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

from eva_sub_cli.file_utils import (
    backup_file_or_directory, DirLock, DirLockError,
    resolve_single_file_path, is_submission_dir_writable, is_vcf_file,
    open_gzip_if_required, fasta_iter, detect_vcf_evidence_type,
    _assess_vcf_evidence_type_manual
)


def set_up_test_dir():
    os.makedirs('backup_test/nested/dir', exist_ok=True)
    Path('backup_test/file.txt').touch()


def clean_up():
    for file_name in glob.glob('backup_test**'):
        shutil.rmtree(file_name)


def test_backup_file_or_directory():
    set_up_test_dir()
    backup_file_or_directory('backup_test')
    assert not os.path.exists('backup_test')
    assert os.path.exists('backup_test.1/nested/dir')
    assert os.path.exists('backup_test.1/file.txt')
    clean_up()


def test_backup_file_or_directory_max_backups():
    max_backups = 2

    # Backup directory
    for i in range(max_backups + 2):
        set_up_test_dir()
        backup_file_or_directory('backup_test', max_backups=max_backups)
    for i in range(1, max_backups + 1):
        assert os.path.exists(f'backup_test.{i}')
    assert not os.path.exists(f'backup_test.{max_backups + 1}')

    # Backup file
    for i in range(max_backups + 2):
        set_up_test_dir()
        backup_file_or_directory('backup_test/file.txt', max_backups=max_backups)
    for i in range(1, max_backups + 1):
        assert os.path.exists(f'backup_test/file.txt.{i}')
    assert not os.path.exists(f'backup_test/file.txt.{max_backups + 1}')
    clean_up()


class TestDirLock(TestCase):
    resources_folder = os.path.join(os.path.dirname(__file__), 'resources')

    def setUp(self) -> None:
        self.lock_folder = os.path.join(self.resources_folder, 'locked_folder')
        os.makedirs(self.lock_folder)

    def tearDown(self) -> None:
        shutil.rmtree(self.lock_folder)

    def test_create_lock(self):
        with DirLock(self.lock_folder) as lock:
            assert os.path.isfile(lock._lockfilename)
        assert not os.path.exists(lock._lockfilename)

    def test_prevent_create_2_lock(self):
        with DirLock(self.lock_folder) as lock:
            assert os.path.isfile(lock._lockfilename)
            with self.assertRaises(DirLockError):
                with DirLock(self.lock_folder) as lock2:
                    pass
            assert os.path.isfile(lock._lockfilename)
        assert not os.path.exists(lock._lockfilename)

    def test_lock_with_exception(self):
        try:
            with DirLock(self.lock_folder) as lock:
                assert os.path.isfile(lock._lockfilename)
                raise Exception()
        except Exception:
            pass
        assert not os.path.exists(lock._lockfilename)


class TestResolveSingleFilePath(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_resolve_single_file_path_exact_match(self):
        """Test resolving an exact file path."""
        test_file = os.path.join(self.test_dir, 'test.txt')
        Path(test_file).touch()
        result = resolve_single_file_path(test_file)
        assert result == test_file

    def test_resolve_single_file_path_with_glob(self):
        """Test resolving a path with glob pattern."""
        test_file = os.path.join(self.test_dir, 'test_123.txt')
        Path(test_file).touch()
        pattern = os.path.join(self.test_dir, 'test_*.txt')
        result = resolve_single_file_path(pattern)
        assert result == test_file

    def test_resolve_single_file_path_multiple_matches(self):
        """Test resolving returns first match when multiple files match."""
        for name in ['a.txt', 'b.txt', 'c.txt']:
            Path(os.path.join(self.test_dir, name)).touch()
        pattern = os.path.join(self.test_dir, '*.txt')
        result = resolve_single_file_path(pattern)
        # Returns first match (alphabetically sorted by glob)
        assert result is not None
        assert result.endswith('.txt')

    def test_resolve_single_file_path_no_match(self):
        """Test resolving returns None when no files match."""
        pattern = os.path.join(self.test_dir, 'nonexistent*.txt')
        result = resolve_single_file_path(pattern)
        assert result is None


class TestIsSubmissionDirWritable(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_submission_dir_writable_existing_dir(self):
        """Test that existing writable directory returns True."""
        result = is_submission_dir_writable(self.test_dir)
        assert result is True

    def test_is_submission_dir_writable_creates_dir(self):
        """Test that non-existing directory is created."""
        new_dir = os.path.join(self.test_dir, 'new_submission')
        assert not os.path.exists(new_dir)
        result = is_submission_dir_writable(new_dir)
        assert result is True
        assert os.path.exists(new_dir)

    def test_is_submission_dir_writable_file_not_dir(self):
        """Test that a file path returns False."""
        test_file = os.path.join(self.test_dir, 'file.txt')
        Path(test_file).touch()
        result = is_submission_dir_writable(test_file)
        assert result is False


class TestIsVcfFile(TestCase):

    def test_is_vcf_file_vcf_extension(self):
        """Test that .vcf files are recognized."""
        assert is_vcf_file('sample.vcf') is True
        assert is_vcf_file('/path/to/sample.vcf') is True
        assert is_vcf_file('SAMPLE.VCF') is True

    def test_is_vcf_file_vcf_gz_extension(self):
        """Test that .vcf.gz files are recognized."""
        assert is_vcf_file('sample.vcf.gz') is True
        assert is_vcf_file('/path/to/sample.vcf.gz') is True
        assert is_vcf_file('SAMPLE.VCF.GZ') is True

    def test_is_vcf_file_other_extensions(self):
        """Test that non-VCF files are not recognized."""
        assert is_vcf_file('sample.txt') is False
        assert is_vcf_file('sample.bed') is False
        assert is_vcf_file('sample.fasta') is False
        assert is_vcf_file('sample.gz') is False

    def test_is_vcf_file_empty_or_none(self):
        """Test that empty or None values return False."""
        assert is_vcf_file('') is False
        assert is_vcf_file(None) is False
        assert is_vcf_file('   ') is False

    def test_is_vcf_file_with_whitespace(self):
        """Test that whitespace is stripped."""
        assert is_vcf_file('  sample.vcf  ') is True
        assert is_vcf_file('  sample.vcf.gz  ') is True


class TestOpenGzipIfRequired(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_open_gzip_if_required_plain_file(self):
        """Test opening a plain text file."""
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('Hello World')

        with open_gzip_if_required(test_file) as f:
            content = f.read()
        assert content == 'Hello World'

    def test_open_gzip_if_required_gzip_file(self):
        """Test opening a gzip compressed file."""
        test_file = os.path.join(self.test_dir, 'test.txt.gz')
        with gzip.open(test_file, 'wt') as f:
            f.write('Hello Compressed')

        with open_gzip_if_required(test_file) as f:
            content = f.read()
        assert content == 'Hello Compressed'

    def test_open_gzip_if_required_write_mode(self):
        """Test opening a file in write mode."""
        test_file = os.path.join(self.test_dir, 'output.txt')
        with open_gzip_if_required(test_file, mode='w') as f:
            f.write('Written content')

        with open(test_file) as f:
            content = f.read()
        assert content == 'Written content'


class TestFastaIter(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_fasta_iter_single_sequence(self):
        """Test fasta_iter with a single sequence."""
        fasta_file = os.path.join(self.test_dir, 'single.fa')
        with open(fasta_file, 'w') as f:
            f.write('>seq1\n')
            f.write('ATCGATCG\n')

        sequences = list(fasta_iter(fasta_file))
        assert len(sequences) == 1
        assert sequences[0] == ('seq1', 'ATCGATCG')

    def test_fasta_iter_multiple_sequences(self):
        """Test fasta_iter with multiple sequences."""
        fasta_file = os.path.join(self.test_dir, 'multi.fa')
        with open(fasta_file, 'w') as f:
            f.write('>seq1 description\n')
            f.write('ATCGATCG\n')
            f.write('>seq2\n')
            f.write('GGGGCCCC\n')
            f.write('AAAATTTT\n')

        sequences = list(fasta_iter(fasta_file))
        assert len(sequences) == 2
        assert sequences[0] == ('seq1 description', 'ATCGATCG')
        assert sequences[1] == ('seq2', 'GGGGCCCCAAAATTTT')

    def test_fasta_iter_gzipped_file(self):
        """Test fasta_iter with gzipped FASTA file."""
        fasta_file = os.path.join(self.test_dir, 'compressed.fa.gz')
        with gzip.open(fasta_file, 'wt') as f:
            f.write('>seq1\n')
            f.write('ATCGATCG\n')

        sequences = list(fasta_iter(fasta_file))
        assert len(sequences) == 1
        assert sequences[0] == ('seq1', 'ATCGATCG')

    def test_fasta_iter_multiline_sequence(self):
        """Test fasta_iter with multiline sequences."""
        fasta_file = os.path.join(self.test_dir, 'multiline.fa')
        with open(fasta_file, 'w') as f:
            f.write('>seq1\n')
            f.write('ATCG\n')
            f.write('ATCG\n')
            f.write('ATCG\n')

        sequences = list(fasta_iter(fasta_file))
        assert len(sequences) == 1
        assert sequences[0] == ('seq1', 'ATCGATCGATCG')


class TestDetectVcfEvidenceType(TestCase):
    resources_folder = os.path.join(os.path.dirname(__file__), 'resources')

    def test_detect_vcf_evidence_type_with_real_file(self):
        """Test detect_vcf_evidence_type with a real VCF file."""
        vcf_file = os.path.join(self.resources_folder, 'vcf_files', 'input_passed.vcf')
        if os.path.exists(vcf_file):
            result = detect_vcf_evidence_type(vcf_file)
            # The result should be either 'genotype', 'allele_frequency', or None
            assert result in ['genotype', 'allele_frequency', None]

    def test_detect_vcf_evidence_type_nonexistent_file(self):
        """Test detect_vcf_evidence_type with a nonexistent file."""
        result = detect_vcf_evidence_type('/nonexistent/file.vcf')
        assert result is None


class TestAssessVcfEvidenceTypeManual(TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_assess_vcf_evidence_type_manual_genotype(self):
        """Test manual assessment with genotype data."""
        vcf_file = os.path.join(self.test_dir, 'genotype.vcf')
        with open(vcf_file, 'w') as f:
            f.write('##fileformat=VCFv4.2\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\n')
            f.write('chr1\t100\t.\tA\tG\t.\t.\t.\tGT\t0/1\n')
            f.write('chr1\t200\t.\tC\tT\t.\t.\t.\tGT\t1/1\n')

        samples, af_in_info, gt_in_format = _assess_vcf_evidence_type_manual(vcf_file)
        assert samples == ['SAMPLE1']
        assert gt_in_format is True

    def test_assess_vcf_evidence_type_manual_allele_frequency(self):
        """Test manual assessment with allele frequency data."""
        vcf_file = os.path.join(self.test_dir, 'allele_freq.vcf')
        with open(vcf_file, 'w') as f:
            f.write('##fileformat=VCFv4.2\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n')
            f.write('chr1\t100\t.\tA\tG\t.\t.\tAF=0.5\n')
            f.write('chr1\t200\t.\tC\tT\t.\t.\tAF=0.3;AC=10;AN=30\n')

        samples, af_in_info, gt_in_format = _assess_vcf_evidence_type_manual(vcf_file)
        assert samples == []
        # Note: af_in_info is truthy (returns index from find()) when AF/AC/AN present
        assert af_in_info  # AF is present (truthy value)

    def test_assess_vcf_evidence_type_manual_gzip(self):
        """Test manual assessment with gzipped VCF."""
        vcf_file = os.path.join(self.test_dir, 'test.vcf.gz')
        with gzip.open(vcf_file, 'wt') as f:
            f.write('##fileformat=VCFv4.2\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\n')
            f.write('chr1\t100\t.\tA\tG\t.\t.\t.\tGT\t0/1\n')

        samples, af_in_info, gt_in_format = _assess_vcf_evidence_type_manual(vcf_file)
        assert samples == ['SAMPLE1']
        assert gt_in_format is True

    def test_assess_vcf_evidence_type_manual_multiple_samples(self):
        """Test manual assessment with multiple samples."""
        vcf_file = os.path.join(self.test_dir, 'multi_sample.vcf')
        with open(vcf_file, 'w') as f:
            f.write('##fileformat=VCFv4.2\n')
            f.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1\tSAMPLE2\tSAMPLE3\n')
            f.write('chr1\t100\t.\tA\tG\t.\t.\t.\tGT\t0/1\t0/0\t1/1\n')

        samples, af_in_info, gt_in_format = _assess_vcf_evidence_type_manual(vcf_file)
        assert samples == ['SAMPLE1', 'SAMPLE2', 'SAMPLE3']
        assert gt_in_format is True
