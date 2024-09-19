import glob
import os
import shutil
import time
from pathlib import Path
from unittest import TestCase

from eva_sub_cli.file_utils import backup_file_or_directory, DirLock, DirLockError


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
