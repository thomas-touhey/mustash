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
"""Unit tests for the ``mustash.processors`` module."""

from __future__ import annotations

from typing import Any

import pytest

from mustash.core import Document
from mustash.exc import DropException
from mustash.processors import (
    AppendProcessor,
    BooleanProcessor,
    BytesProcessor,
    DropProcessor,
    RegexpSplitProcessor,
    StringProcessor,
    TrimProcessor,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "a", "values": ["first"]},
            {"a": []},
            {"a": ["first"]},
        ),
        (
            {"field": "a", "values": ["second", "third"]},
            {"a": ["first"]},
            {"a": ["first", "second", "third"]},
        ),
        (
            {"field": "a", "values": ["second", "first"]},
            {"a": ["first"]},
            {"a": ["first", "second", "first"]},
        ),
        (
            {
                "field": "a",
                "values": ["second", "first"],
                "allow_duplicates": False,
            },
            {"a": ["first"]},
            {"a": ["first", "second"]},
        ),
    ),
)
async def test_append(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the append processor works correctly."""
    await AppendProcessor(**params).apply(document)
    assert document == expected


@pytest.mark.asyncio
async def test_append_exc() -> None:
    """Check that the append processor raises correct exceptions."""
    with pytest.raises(ValueError, match=r"not a list"):
        await AppendProcessor(
            field="hello",
            values=["hello"],
        ).apply({"hello": 42})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "hello"},
            {"hello": "true"},
            {"hello": True},
        ),
        (
            {"field": "hello"},
            {"hello": "FALSE"},
            {"hello": False},
        ),
    ),
)
async def test_boolean(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the boolean processor works correctly."""
    await BooleanProcessor(**params).apply(document)
    assert document == expected


@pytest.mark.asyncio
async def test_boolean_exc() -> None:
    """Check that the boolean processor raises correct exceptions."""
    with pytest.raises(ValueError, match=r"ould not convert"):
        await BooleanProcessor(field="hello").apply({"hello": "unknown"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "hello", "target_field": "world"},
            {"hello": "42K"},
            {"hello": "42K", "world": 43008},
        ),
        (
            {"field": "hello"},
            {"hello": "0"},
            {"hello": 0},
        ),
        (
            {"field": "hello"},
            {"hello": "42MB"},
            {"hello": 44040192},
        ),
        (
            {"field": "hello"},
            {"hello": "42.5mb"},
            {"hello": 44564480},
        ),
    ),
)
async def test_bytes(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the bytes processor works correctly."""
    await BytesProcessor(**params).apply(document)
    assert document == expected


@pytest.mark.asyncio
async def test_bytes_exc() -> None:
    """Check that the bytes processor raises correct exceptions."""
    with pytest.raises(ValueError):
        await BytesProcessor(field="a").apply({"a": "42"})


@pytest.mark.asyncio
async def test_drop() -> None:
    """Check that the drop processor works correctly."""
    with pytest.raises(DropException):
        await DropProcessor().apply({"hello": "world"})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "a", "separator": r"[,\s]+"},
            {"a": "hello, beautiful world"},
            {"a": ["hello", "beautiful", "world"]},
        ),
        (
            {"field": "a", "target_field": "b", "separator": r"a"},
            {"a": "haha aaa"},
            {"a": "haha aaa", "b": ["h", "h", " "]},
        ),
        (
            {"field": "a", "separator": r"-"},
            {"a": "---"},
            {"a": []},
        ),
        (
            {"field": "a", "separator": r"-", "preserve_trailing": True},
            {"a": "0--1--"},
            {"a": ["0", "", "1", "", ""]},
        ),
    ),
)
async def test_regexp_split(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the regexp split processor works correctly."""
    await RegexpSplitProcessor(**params).apply(document)
    assert document == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "a"},
            {"a": 42},
            {"a": "42"},
        ),
    ),
)
async def test_string(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the string processor works correctly."""
    await StringProcessor(**params).apply(document)
    assert document == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "params,document,expected",
    (
        (
            {"field": "a"},
            {"a": "  hello,  world  "},
            {"a": "hello,  world"},
        ),
        (
            {"field": "a"},
            {"a": ["  a  ", "\tb\t"]},
            {"a": ["a", "b"]},
        ),
    ),
)
async def test_trim(
    params: dict[str, Any],
    document: Document,
    expected: Document,
) -> None:
    """Check that the trim processor works correctly."""
    await TrimProcessor(**params).apply(document)
    assert document == expected
