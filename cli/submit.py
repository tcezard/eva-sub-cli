#!/usr/bin/env python
import json
import requests

from ebi_eva_common_pyutils.logger import logging_config
from cli.auth import get_auth

logger = logging_config.get_logger(__name__)
SUBMISSION_INITIATE_URL = "http://www.ebi.ac.uk/eva/v1/submission/initiate"


class StudySubmitter:
    def __init__(self, submission_initiate_url=SUBMISSION_INITIATE_URL):
        self.auth = get_auth()
        self.submission_initiate_url = submission_initiate_url

    # TODO
    def upload_submission(self, submission_id, submission_upload_url):
        pass

    def submit(self):
        response = requests.post(self.submission_initiate_url,
                                 headers={'Accept': 'application/hal+json',
                                          'Authorization': 'Bearer ' + self.auth.token()})
        response_json = json.loads(response.text)
        logger.info("Submission ID {} received!!".format(response_json["submissionId"]))
        self.upload_submission(response_json["submissionId"], response_json["uploadUrl"])


if __name__ == "__main__":
    logging_config.add_stdout_handler()
    submitter = StudySubmitter()
    submitter.submit()
