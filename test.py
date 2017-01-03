import os
import pytest
from fluxx_wrapper import Fluxx


@pytest.fixture
def client():
    return Fluxx(
        os.environ['INSTANCE'],
        os.environ['CLIENT'],
        os.environ['SECRET'],
        version='v2',
        style='full'
    )


def test_client(client):
    assert isinstance(client, Fluxx)
