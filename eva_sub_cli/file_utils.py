import glob
import gzip
import os
import shutil
from itertools import groupby


def resolve_single_file_path(file_path):
    files = glob.glob(file_path)
    if len(files) == 0:
        return None
    elif len(files) > 0:
        return files[0]


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


def open_gzip_if_required(input_file):
    """Open a file in read mode using gzip if the file extension says .gz"""
    if input_file.endswith('.gz'):
        return gzip.open(input_file, 'rt')
    else:
        return open(input_file, 'r')


def fasta_iter(input_fasta):
    """
    Given a fasta file. yield tuples of header, sequence
    """
    # first open the file outside
    with open_gzip_if_required(input_fasta) as open_file:
        # ditch the boolean (x[0]) and just keep the header or sequence since
        # we know they alternate.
        faiter = (x[1] for x in groupby(open_file, lambda line: line[0] == ">"))

        for header in faiter:
            # drop the ">"
            headerStr = header.__next__()[1:].strip()

            # join all sequence lines to one.
            seq = "".join(s.strip() for s in faiter.__next__())
            yield (headerStr, seq)
