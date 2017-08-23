import unittest

from fluxx import FluxxClient


class TestFluxx(unittest.TestCase):
    """Docstring for FluxxTest. """

    def setUp(self):
        # TODO
        self.client = FluxxClient()

    def test_client(self):
        self.assertIsInstance(self.client, FluxxClient)
