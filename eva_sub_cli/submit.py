#!/usr/bin/env python
import functools
import hashlib
import json
import math
import os
import time

import requests
from ebi_eva_common_pyutils.config import WritableConfig
from ebi_eva_common_pyutils.logger import AppLogger
from retry import retry

from eva_sub_cli import SUB_CLI_CONFIG_FILE, __version__
from eva_sub_cli.exceptions import InvalidSubmissionException, SubmissionUploadException, RetryableUploadException, \
    FileTooLargeException
from eva_sub_cli.submission_ws import SubmissionWSClient
from eva_sub_cli.validators.validator import READY_FOR_SUBMISSION_TO_EVA

SUB_CLI_CONFIG_KEY_SUBMISSION_ID = "submission_id"
SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL = "submission_upload_url"
SUB_CLI_CONFIG_KEY_COMPLETE = "submission_complete"

# HTTP status codes that can be caused by transient conditions and are worth retrying.
# 404 is included because the Globus HTTPS server can return it when its storage backend fails during an upload,
RETRYABLE_HTTP_STATUS_CODES = {408, 404, 425, 429, 500, 502, 503, 504}
MAX_RETRY_AFTER_SECONDS = 300

# Files rejected by the upload server as too large are uploaded in parts of this size,
# below the 1 GB limit of the upload server
PART_SIZE = 512 * 1024 ** 2



class FilePart:
    """Read-only file-like view of a byte range of a file, which computes the md5 of the data read."""

    def __init__(self, path, offset, size):
        self.size = size
        self._remaining = size
        self._md5 = hashlib.md5()
        self._file = open(path, 'rb')
        self._file.seek(offset)

    def read(self, amt=-1):
        if self._remaining <= 0:
            return b''
        if amt is None or amt < 0 or amt > self._remaining:
            amt = self._remaining
        data = self._file.read(amt)
        self._remaining -= len(data)
        self._md5.update(data)
        return data

    def __len__(self):
        # Used by requests to set the Content-Length header
        return self.size

    @property
    def md5(self):
        return self._md5.hexdigest()

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StudySubmitter(AppLogger):
    def __init__(self, submission_dir, submission_config: WritableConfig = None, username=None, password=None):
        self.submission_ws_client = SubmissionWSClient(username, password)
        self.submission_dir = submission_dir
        # Parts of the files uploaded in parts during this run, per file path
        self.file_parts = {}
        if submission_config:
            self.sub_config = submission_config
        else:
            config_file = os.path.join(submission_dir, SUB_CLI_CONFIG_FILE)
            self.sub_config = WritableConfig(config_file, version=__version__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sub_config.backup()
        self.sub_config.write()

    @property
    def metadata_json_file(self):
        return self.sub_config.get('metadata_json')

    @property
    def metadata_json(self):
        with open(self.metadata_json_file) as open_file:
            return json.load(open_file)

    @property
    def vcf_files(self):
        return self.sub_config.get('vcf_files')

    def update_config_with_submission_id_and_upload_url(self, submission_id, upload_url):
        self.sub_config.set(SUB_CLI_CONFIG_KEY_SUBMISSION_ID, value=submission_id)
        self.sub_config.set(SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL, value=upload_url)

    def _upload_submission(self):
        if READY_FOR_SUBMISSION_TO_EVA not in self.sub_config or not self.sub_config[READY_FOR_SUBMISSION_TO_EVA]:
            raise InvalidSubmissionException(f'There are still validation errors that needs to be addressed. '
                                             f'Please review, address and re-validate before uploading.')

        submission_upload_url = self.sub_config[SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL]

        for f in self.vcf_files:
            try:
                self._upload_file(submission_upload_url, f)
            except FileTooLargeException:
                self.warning(f'{os.path.basename(f)} is too large to be uploaded in one go: uploading it in parts')
                self._upload_file_in_parts(submission_upload_url, f)

        # The metadata json is uploaded last so that it describes the files uploaded in parts
        self._upload_file(submission_upload_url, self._write_metadata_for_submission())

    def _upload_file(self, submission_upload_url, input_file):
        base_name = os.path.basename(input_file)
        self.debug(f'Transfer {base_name} to EVA FTP')
        self._put(os.path.join(submission_upload_url, base_name), lambda: open(input_file, 'rb'), base_name)
        self.debug(f'Upload of {base_name} completed')

    @retry(exceptions=(RetryableUploadException, requests.ConnectionError, requests.Timeout),
           tries=5, delay=10, backoff=5, max_delay=300)
    def _put(self, url, open_data, name):
        """Upload the data returned by open_data, which is called on each attempt. Returns the data object, closed."""
        with open_data() as data:
            r = requests.put(url, data=data)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            self._handle_upload_error(r, name, e)
        return data

    def _upload_file_in_parts(self, submission_upload_url, input_file):
        """Upload a file as consecutive parts of PART_SIZE.
        The parts are recorded so that they can be described in the metadata."""
        base_name = os.path.basename(input_file)
        file_size = os.path.getsize(input_file)
        try:
            parts = self._upload_parts(submission_upload_url, input_file, file_size, PART_SIZE)
        except FileTooLargeException:
            raise SubmissionUploadException(
                f'{base_name} could not be uploaded even when split into parts. Please contact EVA Helpdesk.'
            )
        if sum(part['fileSize'] for part in parts) != file_size:
            raise SubmissionUploadException(f'The parts of {base_name} do not add up to its size of {file_size} bytes')
        self.file_parts[input_file] = parts
        self.info(f'{base_name} uploaded in {len(parts)} parts')

    def _upload_parts(self, submission_upload_url, input_file, file_size, part_size):
        base_name = os.path.basename(input_file)
        number_of_parts = max(1, math.ceil(file_size / part_size))
        parts = []
        for part_index in range(number_of_parts):
            offset = part_index * part_size
            size = min(part_size, file_size - offset)
            # {base_name}.part001 - {base_name}.part999
            part_name = f'{base_name}.part{part_index + 1:0{3}d}'
            self.debug(f'Transfer {part_name} to EVA FTP')
            # Pass a factory rather than a FilePart: each retry of _put needs a new reader starting at the
            # beginning of the part, since a failed attempt consumes the reader and its md5
            data = self._put(
                os.path.join(submission_upload_url, part_name),
                functools.partial(FilePart, input_file, offset, size),
                part_name
            )
            parts.append({'fileName': part_name, 'fileSize': size, 'md5': data.md5})
        return parts

    def _metadata_for_submission(self):
        """Metadata json with the description of the parts for the files uploaded in parts."""
        metadata = self.metadata_json
        parts_per_file_name = {
            os.path.basename(vcf_file): parts
            for vcf_file, parts in self.file_parts.items() if vcf_file in self.vcf_files
        }
        for file_dict in metadata.get('files', []):
            file_name = os.path.basename(file_dict.get('fileName') or '')
            if file_name in parts_per_file_name:
                file_dict['fileParts'] = parts_per_file_name[file_name]
            else:
                file_dict.pop('fileParts', None)
        return metadata

    def _write_metadata_for_submission(self):
        """Write the metadata to upload, without modifying the metadata json provided or generated during validation."""
        upload_dir = os.path.join(self.submission_dir, '.metadata_upload_in_parts')
        os.makedirs(upload_dir, exist_ok=True)
        metadata_file = os.path.join(upload_dir, os.path.basename(self.metadata_json_file))
        with open(metadata_file, 'w') as open_file:
            json.dump(self._metadata_for_submission(), open_file)
        return metadata_file

    def _handle_upload_error(self, response, base_name, error):
        if response.status_code in RETRYABLE_HTTP_STATUS_CODES:
            retry_after = response.headers.get('Retry-After') # Wait for whatever the server says on top of the retry delay
            if retry_after and retry_after.isdigit():
                time.sleep(min(int(retry_after), MAX_RETRY_AFTER_SECONDS))
            self.warning(f'Upload of {base_name} failed with error ({error}). It will be retried.')
            raise RetryableUploadException(str(error)) from error
        if response.status_code == 413:
            raise FileTooLargeException(f'{base_name} is too large to be uploaded in one request') from error
        raise SubmissionUploadException(f'Upload of {base_name} failed: {error}') from error

    def _initiate_submission(self):
        response_json = self.submission_ws_client.initiate_submission()
        self.debug(f'Submission ID {response_json["submissionId"]} received!!')
        # update config with submission id and upload url
        self.update_config_with_submission_id_and_upload_url(response_json["submissionId"], response_json["uploadUrl"])

    def _complete_submission(self):
        self.submission_ws_client.mark_submission_uploaded(self.sub_config.get(SUB_CLI_CONFIG_KEY_SUBMISSION_ID),
                                                           self._metadata_for_submission())
        self.debug("Submission ID {} Complete".format(self.sub_config.get(SUB_CLI_CONFIG_KEY_SUBMISSION_ID)))
        # update config with completion of the submission
        self.sub_config.set(SUB_CLI_CONFIG_KEY_COMPLETE, value=True)

    def is_submission_status_open(self):
        submission_id = self.sub_config.get(SUB_CLI_CONFIG_KEY_SUBMISSION_ID)
        if submission_id:
            status = self.submission_ws_client.get_submission_status(submission_id)
            return status == 'OPEN'
        return False

    def submit(self):
        if READY_FOR_SUBMISSION_TO_EVA not in self.sub_config or not self.sub_config[READY_FOR_SUBMISSION_TO_EVA]:
            raise Exception(f'There are still validation errors that need to be addressed. '
                            f'Please review, address and re-validate before submitting.')
        if not self.sub_config.get(SUB_CLI_CONFIG_KEY_SUBMISSION_UPLOAD_URL):
            self.info(f'Initiate submission')
            self._initiate_submission()

        if not self.is_submission_status_open():
            self.warning(f'You requested the submission using {self.submission_dir}. '
                         f'This directory contains an already completed submission. '
                         f'Please create a new submission directory to resubmit.')
            return

        # upload submission
        self.info(f'Start Uploading data')
        self._upload_submission()
        self.info(f'Data Uploaded successfully')

        # Complete the submission
        self._complete_submission()
        self.info(f'Submission completed successfully')
