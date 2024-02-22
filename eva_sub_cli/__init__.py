import os


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This is your Project Root
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
NEXTFLOW_DIR = os.path.join(PACKAGE_DIR, 'nextflow')
ETC_DIR = os.path.join(PACKAGE_DIR, 'etc')
LSRI_CLIENT_ID = "aa0fcc42-096a-4f9d-b871-aceb1a97d174"

__version__ = open(os.path.join(PACKAGE_DIR, 'VERSION')).read().strip()

SUB_CLI_CONFIG_FILE = ".eva_sub_cli_config.yml"

# Environment variable
SUBMISSION_WS_VAR = 'SUBMISSION_WS_URL'
ENA_WEBIN_ACCOUNT_VAR = 'ENA_WEBIN_ACCOUNT'
ENA_WEBIN_PASSWORD_VAR = 'ENA_WEBIN_PASSWORD'


def is_submission_dir_writable(submission_dir):
    if not os.path.exists(submission_dir):
        os.makedirs(submission_dir)
    if not os.path.isdir(submission_dir):
        return False
    if not os.access(submission_dir, os.W_OK):
        return False
    return True
