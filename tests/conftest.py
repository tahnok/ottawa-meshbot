import pytest

from helpers import ReplyRecorder
from ottobot import MeshBot


@pytest.fixture
def bot() -> MeshBot:
    return MeshBot(name="ottobot")


@pytest.fixture
def reply() -> ReplyRecorder:
    return ReplyRecorder()
