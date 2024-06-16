import json
import pathlib

import pytest
from otk.main import process_include


@pytest.mark.parametrize("src_yaml", (pathlib.Path(__file__).parent / "data/base").glob("*.yaml"))
def test_command_compile_on_base_examples(tmp_path, src_yaml):
    expected = json.load(src_yaml.with_suffix(".json").open())
    actual = process_include(src_yaml, {}, ".")
    assert expected == actual


@pytest.mark.parametrize("src_yaml", (pathlib.Path(__file__).parent / "data/error").glob("*.yaml"))
def test_errors(tmp_path, src_yaml):
    expected = src_yaml.with_suffix(".err").read_text().strip()
    with pytest.raises(FileNotFoundError) as exception:
        process_include(src_yaml, {}, ".")
    assert expected in str(exception.value)
