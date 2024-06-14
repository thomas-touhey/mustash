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
"""Date and time format parsers and formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
import re
from typing import Annotated, ClassVar

from annotated_types import MinLen
from pydantic import BaseModel, ConfigDict

from .core import Element


class DateTimeFormatter(BaseModel, ABC):
    """Date and time parser and formatter."""

    model_config = ConfigDict(extra="forbid")
    """Model configuration."""

    @abstractmethod
    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """

    @abstractmethod
    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """


class FallbackDateTimeFormatter(DateTimeFormatter):
    """Date and time formatter using multiple subformatters, with fallback."""

    formatters: Annotated[list[DateTimeFormatter], MinLen(1)]
    """Date and time formatters to use, as a chain."""

    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """
        for formatter in self.formatters:
            try:
                return formatter.parse(value)
            except ValueError:
                continue

        raise ValueError(
            "None of the formatters have successfully extracted the "
            + "date and time.",
        )

    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """
        return self.formatters[0].format(value)


class JavaDateTimeFormatter(DateTimeFormatter):
    """Java date and time formatter."""

    pattern: str
    """Java time pattern to extract the date and time with.

    See `Java time pattern`_ for more information.

    .. _Java time pattern:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        mapping-date-format.html
    """

    # TODO


class ISO8601DateTimeFormatter(DateTimeFormatter):
    """ISO 8601 date and time formatter."""

    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """
        if not isinstance(value, str):
            raise TypeError()

        return datetime.fromisoformat(value)

    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """
        return value.isoformat()


class UNIXDateTimeFormatter(DateTimeFormatter):
    """UNIX timestamp formatter with second granularity."""

    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """
        value = float(value)  # type: ignore
        return datetime.fromtimestamp(value, UTC)

    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """
        return int(value.timestamp())


class UNIXMSDateTimeFormatter(DateTimeFormatter):
    """UNIX timestamp formatter with millisecond granularity."""

    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """
        value = int(float(value)) / 1000  # type: ignore
        return datetime.fromtimestamp(value, UTC)

    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """
        return int(value.timestamp() * 1000)


class ESTAI64NDateTimeFormatter(DateTimeFormatter):
    """TAI64N (ElasticSearch variant) date and time formatter.

    A TAI64N timestamp is composed of three parts:

    * A big endian 63-bit signed integer (using `two's complement`_)
      represented as a 16-digit hexadecimal sequence optionally prefixed by
      "@", being the number of seconds since the Epoch on the
      "Temps Atomique International" (international atomic time).
    * A big endian 32-bit unsigned integer represented as an 8-digit
      hexadecimal sequence, being the number of nanoseconds between 0
      and 10^9-1 inclusive.

    .. note::

        The highest bit of the seconds count is reserved for future extensions.

    As for UNIX timestamps, the Epoch is 1970, January 1st at midnight.
    The TAI does NOT normally include leap seconds, which means one
    usually needs to keep an updated list of leap seconds to accurately
    convert between UNIX timestamps and TAI64 variations.

    `ElasticSearch's TAI64N implementation`_ has two main twists on the TAI64N
    format definition:

    * It takes leap seconds into account when parsing and formatting TAI64.
    * It considers nanosecond counts greater than ``10^9 - 1`` valid, and adds
      whole seconds (while the standard does not describe the behaviour to
      adopt in such case).

    This formatter implements TAI64N with the ElasticSearch twists.

    See `TAI64, TAI64N, and TAI64NA`_ for more information regarding the
    TAI64 family of date and time formats.

    .. _`two's complement`: https://en.wikipedia.org/wiki/Two%27s_complement
    .. _`ElasticSearch's TAI64N implementation`:
        https://github.com/elastic/elasticsearch/blob/
        b78efa0babd5c347f3943ecd6025d5fea6318004/modules/ingest-common/
        src/main/java/org/elasticsearch/ingest/common/DateFormat.java#L57
    .. _`TAI64, TAI64N, and TAI64NA`: https://cr.yp.to/libtai/tai64.html
    """

    _PATTERN: ClassVar[re.Pattern] = re.compile(
        r"@?([0-9a-fA-F]{16})([0-9a-fA-F]{8})",
    )
    """Pattern used for parsing raw elements."""

    def parse(self, value: Element, /) -> datetime:
        """Extract a date and time from a value.

        :param value: Value to extract the date and time from.
        :return: Timezone-aware date and time.
        """
        if not isinstance(value, str):
            raise TypeError()

        match = self._PATTERN.fullmatch(value)
        if match is None:
            raise ValueError()

        seconds = int(match[1], 16)
        if seconds & 9223372036854775808:  # 2^63, reserved.
            raise ValueError()
        if seconds & 4611686018427387904:  # 2^62, negative.
            seconds -= 9223372036854775808

        nanoseconds = int(match[2], 16)
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            seconds=seconds,
            microseconds=nanoseconds / 1000,
        )

    def format(self, value: datetime, /) -> Element:
        """Format a date and time.

        :param value: Date and time to format.
        :return: Formatted date and time.
        """
        seconds = int(value.timestamp())
        if seconds < 0:
            seconds += 9223372036854775808

        microseconds = value.microsecond * 1000

        return f"@{seconds.to_bytes(8).hex()}{microseconds.to_bytes(4).hex()}"
