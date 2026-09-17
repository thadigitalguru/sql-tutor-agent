from pathlib import Path

import pytest
from app.sandbox.executor import Sandbox
from app.storage.repository import Repository


@pytest.fixture
def sandbox() -> Sandbox:
    return Sandbox()


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "tutor.sqlite")
