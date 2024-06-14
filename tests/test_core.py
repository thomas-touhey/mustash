#!/usr/bin/env python
# *****************************************************************************
# Copyright (C) 2024 Thomas Touhey <thomas@touhey.fr>
#
# This software is governed by the CeCILL-C license under French law and
# abiding by the rules of distribution of free software. You can use, modify
# and/or redistribute the software under the terms of the CeCILL-C license
# as circulated by CEA, CNRS and INRIA at the following
# URL: https://cecill.info
#
# As a counterpart to the access to the source code and rights to copy, modify
# and redistribute granted by the license, users are provided only with a
# limited warranty and the software's author, the holder of the economic
# rights, and the successive licensors have only limited liability.
#
# In this respect, the user's attention is drawn to the risks associated with
# loading, using, modifying and/or developing or reproducing the software by
# the user in light of its specific status of free software, that may mean
# that it is complicated to manipulate, and that also therefore means that it
# is reserved for developers and experienced professionals having in-depth
# computer knowledge. Users are therefore encouraged to load and test the
# software's suitability as regards their requirements in conditions enabling
# the security of their systems and/or data to be ensured and, more generally,
# to use and operate it in the same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-C license and that you accept its terms.
# *****************************************************************************
"""Unit tests for the ``mustash.core`` module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
import pytest

from mustash.core import (
    Document,
    FieldPath,
    FieldProcessor,
    Pipeline,
    Processor,
)


def test_field_path() -> None:
    """Test field paths."""
    assert FieldPath("hello") / "world.wow" == FieldPath("hello.world.wow")
    assert FieldPath(("hello", "world")) / FieldPath("wow") == FieldPath(
        "hello.world.wow",
    )
    assert FieldPath(FieldPath("hello.world")).parts == ("hello", "world")
    assert FieldPath("hello.world") != FieldPath("hello.universe")
    assert FieldPath("hello.world") != 5

    assert str(FieldPath("hello.world")) == "hello.world"
    assert repr(FieldPath("hello.world")) == "FieldPath('hello.world')"
    assert hash(FieldPath("hello.world")) == hash("hello.world")

    class MyModel(BaseModel):
        path: FieldPath

    assert MyModel(path="hello").path == FieldPath("hello")
    assert MyModel(path=FieldPath("hello")).path == FieldPath("hello")


def test_invalid_field_path_initializations() -> None:
    """Test everything is well validated."""
    with pytest.raises(ValueError):
        FieldPath(["hello.world"])

    with pytest.raises(ValueError):
        FieldPath(["hello."])

    with pytest.raises(ValueError):
        FieldPath("hello.")

    with pytest.raises(ValueError):
        FieldPath(".")

    with pytest.raises(ValueError):
        FieldPath("")


def test_field_path_contains() -> None:
    """Test that the "in" operator works correctly."""
    assert "a.b.c" in FieldPath("a.b")
    assert "a.b" in FieldPath("a.b")
    assert "a.c" not in FieldPath("a.b")
    assert "a" not in FieldPath("a.b")
    assert 5 not in FieldPath("a.b")


def test_field_path_parent() -> None:
    """Test that ``FieldPath.parent`` yields the correct result."""
    assert FieldPath("hello.world.yay").parent == FieldPath("hello.world")
    assert FieldPath("hello").parent == FieldPath("hello")


def test_field_path_get() -> None:
    """Test that ``FieldPath.get`` works."""
    assert FieldPath("hello.world").get({"hello": {"world": 5}}) == 5
    assert FieldPath("l.1").get({"l": [5, 10, 15]}) == 10

    with pytest.raises(KeyError, match=r"'a'"):
        FieldPath("a.b.c").get({})

    with pytest.raises(KeyError, match=r"'a.b"):
        FieldPath("a.b.c").get({"a": {}})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b.c").get({"a": [5, 10, 15]})

    with pytest.raises(KeyError, match=r"'a.-1'"):
        FieldPath("a.-1.c").get({"a": [5, 10, 15]})

    with pytest.raises(KeyError, match=r"'a.3'"):
        FieldPath("a.3.c").get({"a": [5, 10, 15]})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b.c").get({"a": 1})

    assert FieldPath("a.b.c").get({}, default="wow") == "wow"
    assert FieldPath("a.b.c").get({"a": {}}, default="wow") == "wow"
    assert FieldPath("a.b.c").get({"a": [5, 10, 15]}, default="wow") == "wow"
    assert FieldPath("a.-1.c").get({"a": [5, 10, 15]}, default="wow") == "wow"
    assert FieldPath("a.3.c").get({"a": [5, 10, 15]}, default="wow") == "wow"
    assert FieldPath("a.b.c").get({"a": 1}, default="wow") == "wow"


def test_field_path_set() -> None:
    """Test that ``FieldPath.set`` works."""
    d: Document = {"a": {}}
    FieldPath("a.b.c").set(d, 5)
    assert d == {"a": {"b": {"c": 5}}}

    d = {"a": [{}]}
    FieldPath("a.0.b").set(d, 5)
    assert d == {"a": [{"b": 5}]}

    d = {"a": [1, 2, 3]}
    FieldPath("a.0").set(d, 4)
    assert d == {"a": [4, 2, 3]}

    with pytest.raises(KeyError, match=r"'a.-5'"):
        FieldPath("a.-5.b").set({"a": []}, 5)

    with pytest.raises(KeyError, match=r"'a.1'"):
        FieldPath("a.1.b").set({"a": []}, 5)

    with pytest.raises(KeyError, match=r"'a.1'"):
        FieldPath("a.1.b").set({"a": 2}, 5)

    with pytest.raises(KeyError, match=r"'a.-5'"):
        FieldPath("a.-5").set({"a": []}, 5)

    with pytest.raises(KeyError, match=r"'a.3'"):
        FieldPath("a.3").set({"a": [1, 2, 3]}, 5)

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b").set({"a": 2}, 5)


def test_field_path_delete() -> None:
    """Test that ``FieldPath.delete`` works."""
    d: Document = {"a": [{"b": 1}]}
    FieldPath("a.0.b").delete(d)
    assert d == {"a": [{}]}

    d = {"a": [1, 2, 3]}
    FieldPath("a.1").delete(d)
    assert d == {"a": [1, 3]}

    with pytest.raises(KeyError, match=r"'a'"):
        FieldPath("a.b").delete({})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b").delete({"a": {}})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b.c").delete({"a": []})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b").delete({"a": []})

    with pytest.raises(KeyError, match=r"'a.1'"):
        FieldPath("a.1.c").delete({"a": []})

    with pytest.raises(KeyError, match=r"'a.1'"):
        FieldPath("a.1").delete({"a": []})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b.c").delete({"a": 5})

    with pytest.raises(KeyError, match=r"'a.b'"):
        FieldPath("a.b").delete({"a": 5})


@pytest.mark.asyncio
async def test_pipeline_apply() -> None:
    """Test that a pipeline can apply."""

    class MyProcessor(Processor):
        async def apply(self, document: Document, /) -> None:
            document["hello"] = "world"

    pipeline = Pipeline(processors=[MyProcessor()])
    document: Document = {}
    await pipeline.apply(document)
    assert document == {"hello": "world"}


@pytest.mark.asyncio
async def test_field_processor() -> None:
    """Test field processors."""

    class MyGenericFieldProcessor(FieldProcessor):
        async def process(self, value: Any) -> int:
            assert value == {"b": 5}
            return 101

    d: Document = {"a": {"b": 5}}
    await MyGenericFieldProcessor(field="a").apply(d)
    assert d == {"a": 101}

    d = {"a": {"b": 5}}
    await MyGenericFieldProcessor(field="a", target_field="a.d").apply(d)
    assert d == {"a": {"b": 5, "d": 101}}

    with pytest.raises(KeyError):
        await MyGenericFieldProcessor(field="a").apply({})

    d = {"c": 2}
    await MyGenericFieldProcessor(field="a", ignore_missing=True).apply(d)
    assert d == {"c": 2}

    d = {"a": {"b": 5}, "c": 2}
    await MyGenericFieldProcessor(
        field="a",
        target_field="b",
        remove_if_successful=True,
    ).apply(d)
    assert d == {"b": 101, "c": 2}

    d = {"a": {"b": 5}, "c": 2}
    await MyGenericFieldProcessor(
        field="a",
        remove_if_successful=True,
    ).apply(d)
    assert d == {"a": 101, "c": 2}
