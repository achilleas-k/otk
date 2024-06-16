import argparse
import json
import pathlib

import pytest
from otk.main import process_include


@pytest.mark.parametrize("src_yaml", (pathlib.Path(__file__).parent / "data/base").glob("*.yaml"))
def test_command_compile_on_base_examples(tmp_path, src_yaml):
    expected = json.load(src_yaml.with_suffix(".json").open())
    actual = process_include(src_yaml, {}, ".")
    assert expected == actual
