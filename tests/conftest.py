import json
from pathlib import Path
import pytest


@pytest.fixture
def config():
    return json.loads((Path(__file__).parents[1] / "examples/constrained.json").read_text())
