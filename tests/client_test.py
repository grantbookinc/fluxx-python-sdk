import unittest
from unittest import mock
import json

from fluxx.core import FluxxClient

auth_json = {'access_token': '1234'}


def _create_mock_session(return_json):
    resp_mock = mock.Mock()
    resp_mock.json.return_value = return_json
    return mock.MagicMock(post=mock.MagicMock(return_value=resp_mock))


class ClientTest(unittest.TestCase):
    @mock.patch('requests.Session')
    def setUp(self, mocked_session):
        mocked_session.return_value = _create_mock_session(auth_json)
        self.client = FluxxClient('test_instance', 'test_client', 'test_secret')

    def test_initialization(self):
        self.assertIsInstance(self.client, FluxxClient)
        self.assertEqual(self.client.auth_token, '1234')
        self.assertEqual(self.client.base_url, 'https://test_instance.fluxx.io/api/rest/v2/')
