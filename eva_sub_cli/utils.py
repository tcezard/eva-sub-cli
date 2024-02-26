import os


def is_submission_dir_writable(submission_dir):
    if not os.path.exists(submission_dir):
        os.makedirs(submission_dir)
    if not os.path.isdir(submission_dir):
        return False
    if not os.access(submission_dir, os.W_OK):
        return False
    return True
