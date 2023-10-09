#!/usr/bin/env python
import os
from urllib.parse import urljoin

import requests
from ebi_eva_common_pyutils.config import WritableConfig
from ebi_eva_common_pyutils.logger import logging_config

from cli import SUB_CLI_CONFIG_FILE, __version__
from cli.auth import get_auth
from cli.docker_validator import READY_FOR_SUBMISSION_TO_EVA

logger = logging_config.get_logger(__name__)
SUB_CLI_CONFIG_KEY_SUBMISSION_ID = "submission_id"
SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL = "submission_upload_url"
SUBMISSION_INITIATE_URL = "http://www.ebi.ac.uk/eva/v1/submission/initiate"


class StudySubmitter:
    def __init__(self, submission_dir, submission_initiate_url=SUBMISSION_INITIATE_URL, submission_config: WritableConfig = None):
class StudySubmitter(AppLogger):
    def __init__(self, vcf_files, metadata_file, submission_initiate_url=SUBMISSION_INITIATE_URL):
        self.auth = get_auth()
        self.submission_initiate_url = submission_initiate_url
        if submission_config:
            self.sub_config = submission_config
        else:
            config_file = os.path.join(submission_dir, SUB_CLI_CONFIG_FILE)
            self.sub_config = WritableConfig(config_file, version=__version__)

    def update_config_with_submission_id_and_upload_url(self, submission_id, upload_url):
        self.sub_config.set(SUB_CLI_CONFIG_KEY_SUBMISSION_ID, value=submission_id)
        self.sub_config.set(SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL, value=upload_url)
        self.sub_config.backup()
        self.sub_config.write()

    # TODO
    def upload_submission(self, submission_id=None, submission_upload_url=None):
        if not self.sub_config or self.sub_config.is_empty():
            raise Exception(f'Cannot resume submission. Config file is empty')

        if not self.sub_config[READY_FOR_SUBMISSION_TO_EVA]:
            raise Exception(f'There are still validation errors that needs to be addressed. '
                            f'Please review, address and re-validate before uploading.')

        if not submission_id or not submission_upload_url:
            submission_id = self.sub_config[SUB_CLI_CONFIG_KEY_SUBMISSION_ID]
            submission_upload_url = self.sub_config[SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL]
        pass
    def upload_submission(self, submission_dir, submission_upload_url=None):
        if not submission_upload_url:
            submission_id, submission_upload_url = self.get_submission_id_and_upload_url(submission_dir)
        for f in self.vcf_files:
            self.upload_file(submission_upload_url, f)
        self.upload_file(submission_upload_url, self.metadata_file)

    @retry(tries=5, delay=10, backoff=5)
    def upload_file(self, submission_upload_url, input_file):
        base_name = os.path.basename(input_file)
        self.info(f'Transfer {base_name} to EVA FTP')
        r = requests.put(urljoin(submission_upload_url, base_name), data=open(input_file, 'rb'))
        r.raise_for_status()
        self.info(f'Upload of {base_name} completed')

    def verify_submission_dir(self, submission_dir):
        if not os.path.exists(submission_dir):
            os.makedirs(submission_dir)
        if not os.access(submission_dir, os.W_OK):
            raise Exception(f"The directory '{submission_dir}' does not have write permissions.")

    def submit(self, submission_dir):
        if not self.sub_config[READY_FOR_SUBMISSION_TO_EVA]:
            raise Exception(f'There are still validation errors that need to be addressed. '
                            f'Please review, address and re-validate before submitting.')

        self.verify_submission_dir(submission_dir)
        response = requests.post(self.submission_initiate_url,
                                 headers={'Accept': 'application/hal+json',
                                          'Authorization': 'Bearer ' + self.auth.token})
        response.raise_for_status()
        response_json = response.json()
        logger.info("Submission ID {} received!!".format(response_json["submissionId"]))

        # update config with submission id and upload url
        self.update_config_with_submission_id_and_upload_url(response_json["submissionId"], response_json["uploadUrl"])

        # upload submission
        self.upload_submission(response_json["submissionId"], response_json["uploadUrl"])
