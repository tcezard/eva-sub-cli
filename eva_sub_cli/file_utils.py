import os
import shutil


def is_submission_dir_writable(submission_dir):
    if not os.path.exists(submission_dir):
        os.makedirs(submission_dir)
    if not os.path.isdir(submission_dir):
        return False
    if not os.access(submission_dir, os.W_OK):
        return False
    return True


def backup_file_or_directory(file_name, max_backups=None):
    """
    Rename a file or directory by adding a '.1' at the end. If the '.1' file exists it move it to a '.2' and so on.
    Keep at most the specified number of backups, if None will keep all.
    """
    suffix = 1
    backup_name = f'{file_name}.{suffix}'
    while os.path.exists(backup_name):
        suffix += 1
        backup_name = f'{file_name}.{suffix}'

    for i in range(suffix, 1, -1):
        if max_backups and i > max_backups:
            if os.path.isfile(file_name):
                os.remove(f'{file_name}.{i - 1}')
            else:
                shutil.rmtree(f'{file_name}.{i - 1}')
        else:
            os.rename(f'{file_name}.{i - 1}', f'{file_name}.{i}')
    os.rename(file_name, file_name + '.1')
