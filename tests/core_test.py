import json
import unittest
from unittest import mock

from fluxx.core import FluxxClient
from fluxx.core import format_column_name
from fluxx.core import format_write_data

AUTH_JSON = {'access_token': '1234'}


def _create_mock_session(return_json):
    resp_mock = mock.Mock()
    resp_mock.json.return_value = return_json
    return mock.MagicMock(post=mock.MagicMock(return_value=resp_mock))


class ClientTest(unittest.TestCase):
    @mock.patch('requests.Session')
    def setUp(self, mocked_session):
        mocked_session.return_value = _create_mock_session(AUTH_JSON)
        self.client = FluxxClient('test_inst', 'test_client', 'test_secret')
        self.preprod_client = FluxxClient('test_inst.preprod', 'test_client', 'test_secret')

    def test_initialization(self):
        #  test production
        self.assertIsInstance(self.client, FluxxClient)
        self.assertEqual(self.client.auth_token, '1234')
        base_url = 'https://test_inst.fluxx.io/api/rest/v2/'
        self.assertEqual(self.client.base_url, base_url)

        #  test pre production
        self.assertIsInstance(self.preprod_client, FluxxClient)
        self.assertEqual(self.preprod_client.auth_token, '1234')
        preprod_base_url = 'https://test_inst.preprod.fluxxlabs.com/api/rest/v2/'
        self.assertEqual(self.preprod_client.base_url, preprod_base_url)

    def test_column_name(self):
        cases = ('test column name ', 'Test ColuMn NaMe')

        for case in cases:
            self.assertEqual(format_column_name(case), 'test_column_name')

    def test_format_write_data(self):
        test_data = {
            'fiRSt Column': '2 3 5',
            ' SecoNd CoLUmn': 'here'
        }
        correct_result = {
            'cols': json.dumps(['first_column', 'second_column']),
            'data': json.dumps({
                'first_column': '2 3 5',
                'second_column': 'here',
            })
        }
        self.assertEqual(format_write_data(test_data), correct_result)
