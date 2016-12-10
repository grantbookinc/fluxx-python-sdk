import os
import logging
logging.basicConfig(level=logging.DEBUG)

import pytest
from fluxx import Fluxx

@pytest.fixture
def fluxx_client():
    return Fluxx(
        os.environ['INSTANCE'],
        os.environ['CLIENT'],
        os.environ['SECRET'],
        version='v2',
        style='full'
    )


def test_client(fluxx_client):
    assert isinstance(fluxx_client)
    fluxx_client.grant_request.list({'cols': '["id"]'})
