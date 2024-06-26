import logging

import pytest

from otk.context import CommonContext
from otk.error import (
    TransformVariableIndexRangeError,
    TransformVariableIndexTypeError,
    TransformVariableLookupError,
    TransformVariableTypeError,
)


def test_context():
    ctx = CommonContext()
    ctx.define("foo", "foo")

    assert ctx.variable("foo") == "foo"

    ctx.define("bar", {"bar": "foo"})

    assert ctx.variable("bar.bar") == "foo"

    ctx.define("baz", {"baz": {"baz": "foo", "0": 1, 1: "foo"}})

    assert ctx.variable("baz.baz.baz") == "foo"
    assert ctx.variable("baz.baz.0") == 1

    # TODO numeric key lookups!
    # assert ctx.variable("baz.baz.1") == "foo"

    ctx.define("boo", [1, 2])

    assert ctx.variable("boo") == [1, 2]
    assert ctx.variable("boo.0") == 1
    assert ctx.variable("boo.1") == 2


def test_context_define_subkey(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext()
    ctx.define("key", "val")
    assert ctx.variable("key") == "val"

    ctx.define("key.subkey", "subval")
    assert ctx.variable("key") == {"subkey": "subval"}
    assert len(caplog.records) == 0
    ctx.define("key.subkey2", "subval2")
    assert ctx.variable("key") == {"subkey": "subval", "subkey2": "subval2"}
    ctx.define("key", "other-val")
    assert ctx.variable("key") == "other-val"

    ctx.define("other.key.with.subkey", "subval")
    assert ctx.variable("other") == {"key": {"with": {"subkey": "subval"}}}


def test_context_warn_on_override_simple(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(duplicate_definitions_warning=True)
    ctx.define("key", "val")
    assert len(caplog.records) == 0
    ctx.define("key", "new-val")
    expected_msg = "redefinition of 'key', previous values was 'val' and new value is 'new-val'"
    assert [expected_msg] == [r.message for r in caplog.records]


def test_context_warn_on_override_nested(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(duplicate_definitions_warning=True)
    ctx.define("key.subkey.subsubkey", "subsubval")
    assert len(caplog.records) == 0
    ctx.define("key.subkey", "newsubval")
    # from dict -> str
    expected_msg1 = ("redefinition of 'key.subkey', previous values was "
                     "{'subsubkey': 'subsubval'} and new value is 'newsubval'")
    assert [expected_msg1] == [r.message for r in caplog.records]
    ctx.define("key.subkey", {"sub": "dict"})
    # from str -> dict
    expected_msg2 = ("redefinition of 'key.subkey', previous values was "
                     "'newsubval' and new value is {'sub': 'dict'}")
    assert [expected_msg1, expected_msg2] == [r.message for r in caplog.records]


def test_context_warn_on_override_nested_from_val_to_dict(caplog):
    caplog.set_level(logging.WARNING)
    ctx = CommonContext(duplicate_definitions_warning=True)
    ctx.define("key.sub", "subval")
    assert len(caplog.records) == 0
    ctx.define("key.sub.subsub.subsubsub", {"subsubsub": "val2"})
    expected_msg = ("redefinition of 'key.sub', previous values was "
                    "'subval' and new value is {'subsub.subsubsub': {'subsubsub': 'val2'}}")

    assert [expected_msg] == [r.message for r in caplog.records]


def test_context_nonexistent():
    ctx = CommonContext()

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo")

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("foo.bar")

    ctx.define("bar", {"bar": "foo"})

    with pytest.raises(TransformVariableLookupError):
        ctx.variable("bar.nonexistent")


def test_context_unhappy():
    ctx = CommonContext()
    ctx.define("foo", "foo")

    with pytest.raises(TransformVariableTypeError):
        ctx.variable("foo.bar")

    ctx.define("bar", ["bar"])

    with pytest.raises(TransformVariableIndexTypeError):
        ctx.variable("bar.bar")

    with pytest.raises(TransformVariableIndexRangeError):
        ctx.variable("bar.3")
