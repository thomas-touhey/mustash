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
"""Unit tests for the ``mustash.es_dissect`` module."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel
import pytest

from mustash.es_dissect import (
    ESDissectKey,
    ESDissectKeyModifier,
    ESDissectPattern,
)


@pytest.mark.parametrize(
    "raw,prefix,pairs",
    (
        (
            "_%{hello}_+%{+no}sfx",
            "_",
            (
                (ESDissectKey(name="hello"), "_+"),
                (
                    ESDissectKey(
                        name="no",
                        modifier=ESDissectKeyModifier.APPEND,
                    ),
                    "sfx",
                ),
            ),
        ),
        (
            "%{+a->}",
            "",
            (
                (
                    ESDissectKey(
                        name="a",
                        modifier=ESDissectKeyModifier.APPEND,
                        skip_right_padding=True,
                    ),
                    "",
                ),
            ),
        ),
        (
            "%{+/a/12}%{?a}x",
            "",
            (
                (
                    ESDissectKey(
                        name="a",
                        modifier=ESDissectKeyModifier.APPEND_WITH_ORDER,
                        append_position=12,
                    ),
                    "",
                ),
                (
                    ESDissectKey(
                        name="a",
                        modifier=ESDissectKeyModifier.NAMED_SKIP,
                        skip=True,
                    ),
                    "x",
                ),
            ),
        ),
    ),
)
def test_parse_pattern(
    raw: str,
    prefix: str,
    pairs: Sequence[tuple[ESDissectKey, str]],
) -> None:
    """Check that we can parse a pattern."""

    class MyModel(BaseModel):
        pattern: ESDissectPattern

    pattern = MyModel(pattern=raw).pattern
    assert (pattern.prefix, tuple(pattern.pairs)) == (prefix, tuple(pairs))


def test_parse_pattern_with_no_key() -> None:
    """Check that parsing a pattern with no key produces an error."""
    with pytest.raises(ValueError, match=r"does not contain keys"):
        ESDissectPattern("hello, world")


def test_parse_pattern_with_multiple_modifiers() -> None:
    """Check that parsing a pattern with multiple modifiers."""
    with pytest.raises(ValueError, match=r"ultiple modifiers"):
        ESDissectPattern("%{+?hello}")


def test_parse_pattern_obj() -> None:
    """Check that we can coalesce a pattern object."""

    class MyModel(BaseModel):
        pattern: ESDissectPattern

    pattern = ESDissectPattern("%{}")
    assert pattern == MyModel(pattern=pattern).pattern
    assert pattern != MyModel(pattern="%{x}").pattern
    assert pattern == "%{}"
    assert pattern != "%{x}"
    assert pattern != 5


@pytest.mark.parametrize("pattern", ("%{x}", "%{+x->}"))
def test_format_pattern(pattern: str) -> None:
    """Check that the pattern works."""
    assert str(ESDissectPattern(pattern)) == pattern
