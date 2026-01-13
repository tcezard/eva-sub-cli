import os
from unittest import TestCase
from unittest.mock import patch, MagicMock

from requests import HTTPError

from eva_sub_cli import SUBMISSION_WS_VAR
from eva_sub_cli.exceptions.submission_upload_exception import SubmissionUploadException
from eva_sub_cli.submission_ws import SubmissionWSClient


class TestSubmissionWSClient(TestCase):

    def setUp(self):
        # Ensure environment variable is not set for most tests
        if SUBMISSION_WS_VAR in os.environ:
            del os.environ[SUBMISSION_WS_VAR]

    def tearDown(self):
        # Clean up environment variable after tests
        if SUBMISSION_WS_VAR in os.environ:
            del os.environ[SUBMISSION_WS_VAR]

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_init(self, mock_get_auth):
        """Test SubmissionWSClient initialization."""
        mock_auth = MagicMock()
        mock_get_auth.return_value = mock_auth

        client = SubmissionWSClient(username='test_user', password='test_pass')

        mock_get_auth.assert_called_once_with('test_user', 'test_pass')
        assert client.auth == mock_auth
        assert client.base_url == SubmissionWSClient.SUBMISSION_WS_URL

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_submission_ws_url_default(self, mock_get_auth):
        """Test that default URL is used when environment variable is not set."""
        mock_get_auth.return_value = MagicMock()

        client = SubmissionWSClient()
        assert client._submission_ws_url == 'https://www.ebi.ac.uk/eva/webservices/submission-ws/v1/'

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_submission_ws_url_from_environment(self, mock_get_auth):
        """Test that URL from environment variable is used when set."""
        mock_get_auth.return_value = MagicMock()
        custom_url = 'https://custom.url/api/'
        os.environ[SUBMISSION_WS_VAR] = custom_url

        client = SubmissionWSClient()
        assert client._submission_ws_url == custom_url

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_submission_initiate_url(self, mock_get_auth):
        """Test URL construction for initiate submission."""
        mock_get_auth.return_value = MagicMock()

        client = SubmissionWSClient()
        expected_url = 'https://www.ebi.ac.uk/eva/webservices/submission-ws/v1/submission/initiate'
        assert client._submission_initiate_url() == expected_url

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_submission_uploaded_url(self, mock_get_auth):
        """Test URL construction for marking submission as uploaded."""
        mock_get_auth.return_value = MagicMock()

        client = SubmissionWSClient()
        submission_id = 'test-submission-123'
        expected_url = f'https://www.ebi.ac.uk/eva/webservices/submission-ws/v1/submission/{submission_id}/uploaded'
        assert client._submission_uploaded_url(submission_id) == expected_url

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_submission_status_url(self, mock_get_auth):
        """Test URL construction for submission status check."""
        mock_get_auth.return_value = MagicMock()

        client = SubmissionWSClient()
        submission_id = 'test-submission-123'
        expected_url = f'https://www.ebi.ac.uk/eva/webservices/submission-ws/v1/submission/{submission_id}/status'
        assert client._submission_status_url(submission_id) == expected_url

    @patch('eva_sub_cli.submission_ws.requests.post')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_initiate_submission_success(self, mock_get_auth, mock_post):
        """Test successful submission initiation."""
        mock_auth = MagicMock()
        mock_auth.token = 'test_token'
        mock_get_auth.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.json.return_value = {'submissionId': 'new-submission-id', 'uploadUrl': 'https://upload.url'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = SubmissionWSClient()
        result = client.initiate_submission()

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'submission/initiate' in call_args[0][0]
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_token'
        assert result == {'submissionId': 'new-submission-id', 'uploadUrl': 'https://upload.url'}

    @patch('eva_sub_cli.submission_ws.requests.post')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_initiate_submission_failure(self, mock_get_auth, mock_post):
        """Test submission initiation failure."""
        mock_auth = MagicMock()
        mock_auth.token = 'test_token'
        mock_get_auth.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError('Server error')
        mock_post.return_value = mock_response

        client = SubmissionWSClient()
        with self.assertRaises(HTTPError):
            client.initiate_submission()

    @patch('eva_sub_cli.submission_ws.requests.put')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_mark_submission_uploaded_success(self, mock_get_auth, mock_put):
        """Test successful marking of submission as uploaded."""
        mock_auth = MagicMock()
        mock_auth.token = 'test_token'
        mock_get_auth.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'uploaded'}
        mock_response.raise_for_status = MagicMock()
        mock_put.return_value = mock_response

        client = SubmissionWSClient()
        metadata_json = {'project': {'title': 'Test Project'}}
        result = client.mark_submission_uploaded('submission-123', metadata_json)

        mock_put.assert_called_once()
        call_args = mock_put.call_args
        assert 'submission/submission-123/uploaded' in call_args[0][0]
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_token'
        assert call_args[1]['json'] == metadata_json
        assert result == {'status': 'uploaded'}

    @patch('eva_sub_cli.submission_ws.requests.put')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_mark_submission_uploaded_client_error(self, mock_get_auth, mock_put):
        """Test marking submission as uploaded with 4xx error."""
        mock_auth = MagicMock()
        mock_auth.token = 'test_token'
        mock_get_auth.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad request'
        mock_put.return_value = mock_response

        client = SubmissionWSClient()
        with self.assertRaises(SubmissionUploadException):
            client.mark_submission_uploaded('submission-123', {})

    @patch('eva_sub_cli.submission_ws.requests.put')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_mark_submission_uploaded_server_error(self, mock_get_auth, mock_put):
        """Test marking submission as uploaded with 5xx error."""
        mock_auth = MagicMock()
        mock_auth.token = 'test_token'
        mock_get_auth.return_value = mock_auth

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPError('Server error')
        mock_put.return_value = mock_response

        client = SubmissionWSClient()
        with self.assertRaises(HTTPError):
            client.mark_submission_uploaded('submission-123', {})

    @patch('eva_sub_cli.submission_ws.requests.get')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_get_submission_status_success(self, mock_get_auth, mock_get):
        """Test successful retrieval of submission status."""
        mock_get_auth.return_value = MagicMock()

        mock_response = MagicMock()
        mock_response.text = 'UPLOADED'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = SubmissionWSClient()
        result = client.get_submission_status('submission-123')

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'submission/submission-123/status' in call_args[0][0]
        assert result == 'UPLOADED'

    @patch('eva_sub_cli.submission_ws.requests.get')
    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_get_submission_status_failure(self, mock_get_auth, mock_get):
        """Test submission status retrieval failure."""
        mock_get_auth.return_value = MagicMock()

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError('Not found')
        mock_get.return_value = mock_response

        client = SubmissionWSClient()
        # The retry decorator will retry 3 times before raising
        with self.assertRaises(HTTPError):
            client.get_submission_status('nonexistent-submission')

    @patch('eva_sub_cli.submission_ws.get_auth')
    def test_url_constants(self, mock_get_auth):
        """Test that URL constants are correctly defined."""
        assert SubmissionWSClient.SUBMISSION_WS_URL == 'https://www.ebi.ac.uk/eva/webservices/submission-ws/v1/'
        assert SubmissionWSClient.SUBMISSION_INITIATE_PATH == 'submission/initiate'
        assert SubmissionWSClient.SUBMISSION_UPLOADED_PATH == 'submission/{submissionId}/uploaded'
        assert SubmissionWSClient.SUBMISSION_STATUS_PATH == 'submission/{submissionId}/status'
