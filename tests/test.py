import unittest
from unittest import mock
from test.support import EnvironmentVarGuard

from fluxx.core import FluxxClient
from fluxx.core import ENV_INSTANCE_SUFFIX
from fluxx.core import ENV_APPLICATION_ID_SUFFIX
from fluxx.core import ENV_SECRET_SUFFIX


class TestFluxx(unittest.TestCase):
    """Docstring for FluxxTest. """

    def setUp(self):
        # TODO
        self.env = EnvironmentVarGuard()
        self.env.set('TEST_{}'.format(ENV_INSTANCE_SUFFIX), 'test')
        self.env.set('TEST_{}'.format(ENV_APPLICATION_ID_SUFFIX), 'test')
        self.env.set('TEST_{}'.format(ENV_SECRET_SUFFIX), 'test')

        self.client = FluxxClient()

    def test_client(self):
        self.assertIsInstance(self.client, FluxxClient)
