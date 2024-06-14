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

from datetime import UTC, datetime, timedelta, timezone

import pytest

from mustash.time import (
    ESTAI64NDateTimeFormatter,
    FallbackDateTimeFormatter,
    ISO8601DateTimeFormatter,
    UNIXDateTimeFormatter,
    UNIXMSDateTimeFormatter,
)


CEST = timezone(timedelta(seconds=7200))


def test_iso_8601() -> None:
    """Test the ISO 8601 formatter."""
    assert ISO8601DateTimeFormatter().parse(
        "2024-07-05T16:33:27.097796+00:00",
    ) == datetime(2024, 7, 5, 16, 33, 27, 97796, tzinfo=UTC)
    assert ISO8601DateTimeFormatter().parse(
        "2024-07-05T18:34:57.665119+02:00",
    ) == datetime(2024, 7, 5, 18, 34, 57, 665119, tzinfo=CEST)

    with pytest.raises(TypeError):
        ISO8601DateTimeFormatter().parse(123)

    with pytest.raises(ValueError):
        ISO8601DateTimeFormatter().parse("hello, world")

    assert (
        ISO8601DateTimeFormatter().format(
            datetime(2024, 7, 5, 16, 33, 27, 97796, tzinfo=UTC),
        )
        == "2024-07-05T16:33:27.097796+00:00"
    )
    assert (
        ISO8601DateTimeFormatter().format(
            datetime(2024, 7, 5, 18, 34, 57, 665119, tzinfo=CEST),
        )
        == "2024-07-05T18:34:57.665119+02:00"
    )


def test_unix_date_time_formatter() -> None:
    """Test the UNIX timestamp formatter."""
    assert UNIXDateTimeFormatter().parse(123.450) == datetime(
        1970,
        1,
        1,
        0,
        2,
        3,
        450000,
        tzinfo=UTC,
    )
    assert UNIXDateTimeFormatter().parse("123.450") == datetime(
        1970,
        1,
        1,
        0,
        2,
        3,
        450000,
        tzinfo=UTC,
    )
    assert (
        UNIXDateTimeFormatter().format(
            datetime(1970, 1, 1, 0, 2, 3, 450000, tzinfo=UTC),
        )
        == 123
    )


def test_unix_ms_date_time_formatter() -> None:
    """Test the UNIX MS timestamp formatter."""
    assert UNIXMSDateTimeFormatter().parse(123450) == datetime(
        1970,
        1,
        1,
        0,
        2,
        3,
        450000,
        tzinfo=UTC,
    )
    assert UNIXMSDateTimeFormatter().parse("123450") == datetime(
        1970,
        1,
        1,
        0,
        2,
        3,
        450000,
        tzinfo=UTC,
    )
    assert (
        UNIXMSDateTimeFormatter().format(
            datetime(1970, 1, 1, 0, 2, 3, 450000, tzinfo=UTC),
        )
        == 123450
    )


def test_estai64n() -> None:
    """Test the ElasticSearch TAI64N variant formatter."""
    assert ESTAI64NDateTimeFormatter().parse(
        "@0000000000000e51075bcd15",
    ) == datetime(1970, 1, 1, 1, 1, 5, 123457, tzinfo=UTC)
    assert ESTAI64NDateTimeFormatter().parse(
        "7ffffffffffff1af00000000",
    ) == datetime(1969, 12, 31, 22, 58, 55, 0, tzinfo=UTC)
    assert ESTAI64NDateTimeFormatter().parse(
        "000000006688323a23ba00bc",
    ) == datetime(2024, 7, 5, 17, 49, 46, 599392, tzinfo=UTC)
    assert (
        # Same as before, except ms >= 1_000_000_000
        ESTAI64NDateTimeFormatter().parse("00000000668832389aef94bc")
        == datetime(2024, 7, 5, 17, 49, 46, 599392, tzinfo=UTC)
    )

    with pytest.raises(TypeError):
        ESTAI64NDateTimeFormatter().parse(123)

    with pytest.raises(ValueError):
        ESTAI64NDateTimeFormatter().parse("hello, world")

    with pytest.raises(ValueError):
        ESTAI64NDateTimeFormatter().parse("f00000000000000000000000")

    assert (
        # NOTE: Different than before because datetime only has precision
        # going to microseconds only, while TAI64N supports nanoseconds.
        ESTAI64NDateTimeFormatter().format(
            datetime(2024, 7, 5, 17, 49, 46, 599392, tzinfo=UTC),
        )
        == "@000000006688323a23b9ff00"
    )
    assert (
        ESTAI64NDateTimeFormatter().format(
            datetime(1969, 12, 31, 22, 58, 55, 0, tzinfo=UTC),
        )
        == "@7ffffffffffff1af00000000"
    )


def test_fallback() -> None:
    """Test the fallback date and time formatter."""
    fmt = FallbackDateTimeFormatter(
        formatters=(
            ESTAI64NDateTimeFormatter(),
            UNIXDateTimeFormatter(),
        ),
    )
    assert fmt.parse(
        "@0000000000000e51075bcd15",
    ) == datetime(1970, 1, 1, 1, 1, 5, 123457, tzinfo=UTC)
    assert fmt.parse(
        "123.45",
    ) == datetime(1970, 1, 1, 0, 2, 3, 450000, tzinfo=UTC)

    with pytest.raises(ValueError, match=r"None of the formatters"):
        fmt.parse("hello, world")

    assert (
        fmt.format(
            datetime(2024, 7, 5, 17, 49, 46, 599392, tzinfo=UTC),
        )
        == "@000000006688323a23b9ff00"
    )
