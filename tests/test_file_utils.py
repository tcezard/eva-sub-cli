import glob
import os
import shutil
from pathlib import Path

from eva_sub_cli.file_utils import backup_file_or_directory


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
