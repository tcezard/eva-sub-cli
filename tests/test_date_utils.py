import datetime
from unittest import TestCase

from eva_sub_cli.date_utils import check_date, check_date_str_format, not_provided_check_list


class TestDateUtils(TestCase):

    def test_check_date(self):
        assert check_date(datetime.date(2024, 1, 15)) is True
        assert check_date(datetime.datetime(2024, 1, 15, 12, 30, 0)) is True
        assert check_date("2024-01-15") is True
        assert check_date("2024-01") is True
        assert check_date("2024") is True

    def test_check_date_with_not_provided_values(self):
        """Test check_date with values from not_provided_check_list."""
        for value in not_provided_check_list:
            assert check_date(value) is True, f"Failed for '{value}'"

    def test_check_date_with_not_provided_values_case_insensitive(self):
        """Test check_date with not_provided values in different cases."""
        assert check_date("Not Provided") is True
        assert check_date("NOT PROVIDED") is True
        assert check_date("Not Collected") is True
        assert check_date("RESTRICTED ACCESS") is True

    def test_check_date_with_invalid_values(self):
        """Test check_date with invalid values."""
        assert check_date("invalid date") is False
        assert check_date("random string") is False
        assert check_date("01-15-2024") is False

    def test_not_provided_check_list_contents(self):
        """Test that not_provided_check_list contains expected values."""
        expected_values = [
            'not provided', 'not collected', 'restricted access',
            'missing: control sample', 'missing: sample group',
            'missing: synthetic construct', 'missing: lab stock',
            'missing: third party data', 'missing: data agreement established pre-2023',
            'missing: endangered species', 'missing: human-identifiable'
        ]
        for value in expected_values:
            assert value in not_provided_check_list, f"'{value}' not in not_provided_check_list"
