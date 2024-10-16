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
"""ElasticSearch dissect pattern."""

from __future__ import annotations

from collections.abc import Sequence
from enum import IntFlag, auto
from itertools import zip_longest
import re
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler
from pydantic_core.core_schema import (
    CoreSchema,
    ValidationInfo,
    is_instance_schema,
    json_or_python_schema,
    str_schema,
    to_string_ser_schema,
    with_info_after_validator_function,
)


ESDissectPatternType = TypeVar(
    "ESDissectPatternType",
    bound="ESDissectPattern",
)

ESDissectKeyType = TypeVar("ESDissectKeyType", bound="ESDissectKey")

_APPEND_WITH_ORDER_PATTERN = re.compile(r"/([0-9]+)$")
_KEY_DELIMITER_FIELD_PATTERN = re.compile(r"%\{([^}]*)\}")


class ESDissectKeyModifier(IntFlag):
    """Key modifier for ElasticSearch dissect patterns."""

    NONE = 0
    APPEND_WITH_ORDER = auto()
    APPEND = auto()
    FIELD_NAME = auto()
    FIELD_VALUE = auto()
    NAMED_SKIP = auto()


class ESDissectKey(BaseModel):
    """Key for ElasticSearch dissect patterns."""

    DISSECT_KEY_MODIFIERS: ClassVar[dict[str, ESDissectKeyModifier]] = {
        "/": ESDissectKeyModifier.APPEND_WITH_ORDER,
        "+": ESDissectKeyModifier.APPEND,
        "*": ESDissectKeyModifier.FIELD_NAME,
        "&": ESDissectKeyModifier.FIELD_VALUE,
        "?": ESDissectKeyModifier.NAMED_SKIP,
    }
    """Dissect key modifier values by character."""

    DISSECT_KEY_MODIFIER_CHARACTERS: ClassVar[
        dict[ESDissectKeyModifier, str]
    ] = {value: key for key, value in DISSECT_KEY_MODIFIERS.items()}
    """Dissect key modifier characters by value."""

    model_config = ConfigDict(extra="forbid")
    """Model configuration."""

    name: str = ""
    """Name of the dissect key."""

    modifier: ESDissectKeyModifier = ESDissectKeyModifier.NONE
    """Modifier."""

    skip: bool = False
    """Whether to skip."""

    skip_right_padding: bool = False
    """Whether to skip right padding."""

    append_position: int = 0
    """Whether to append the position."""

    def __str__(self, /) -> str:
        fmt = "%{"
        if self.modifier != ESDissectKeyModifier.NONE:
            fmt += self.DISSECT_KEY_MODIFIER_CHARACTERS[self.modifier]

        fmt += self.name
        if self.skip_right_padding:
            fmt += "->"

        return fmt + "}"

    @classmethod
    def parse(cls: type[ESDissectKeyType], raw: str, /) -> ESDissectKeyType:
        """Parse a key for an ElasticSearch dissect pattern.

        :param raw: Raw dissect key.
        :return: Dissect key.
        """
        skip = not raw
        append_position = 0

        # Read the modifiers and remove them from the beginning of the string.
        # There can be either 0 or 1 operators, or "+/".
        modifier = ESDissectKeyModifier.NONE
        while raw[:1] in cls.DISSECT_KEY_MODIFIERS:
            prior_modifier = modifier
            modifier = cls.DISSECT_KEY_MODIFIERS[raw[:1]]
            raw = raw[1:]

            if prior_modifier == ESDissectKeyModifier.NONE:
                continue
            elif (
                modifier == ESDissectKeyModifier.APPEND_WITH_ORDER
                and prior_modifier == ESDissectKeyModifier.APPEND
            ):
                continue

            raise ValueError("Multiple modifiers are not allowed.")

        # All modifiers allow having a "->" at the end to skip right padding.
        if raw[-2:] == "->":
            name = raw[:-2]
            skip_right_padding = True
        else:
            name = raw
            skip_right_padding = False

        if modifier == ESDissectKeyModifier.NONE:
            skip = not name
        elif modifier == ESDissectKeyModifier.NAMED_SKIP:
            skip = True
        elif modifier == ESDissectKeyModifier.APPEND_WITH_ORDER:
            while True:
                match = _APPEND_WITH_ORDER_PATTERN.search(name)
                if match is None:
                    break

                append_position = int(match[1])
                name = name[: match.start()]
        elif modifier not in (  # pragma: no cover
            ESDissectKeyModifier.APPEND,
            ESDissectKeyModifier.FIELD_NAME,
            ESDissectKeyModifier.FIELD_VALUE,
        ):
            raise NotImplementedError()

        return cls(
            name=name,
            modifier=modifier,
            skip=skip,
            skip_right_padding=skip_right_padding,
            append_position=append_position,
        )


class ESDissectPattern:
    """ElasticSearch dissect pattern.

    For more information, see `Dissect processor`_ and `DissectParser.java`_.

    .. _Dissect processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        dissect-processor.html
    .. _DissectParser.java:
        https://github.com/elastic/elasticsearch/blob/main/libs/dissect/
        src/main/java/org/elasticsearch/dissect/DissectParser.java
    """

    __slots__ = ("_prefix", "_pairs")

    _prefix: str
    """Prefix."""

    _pairs: tuple[tuple[ESDissectKey, str], ...]
    """Parsing pairs in order, using."""

    def __init__(self, pattern: ESDissectPattern | str, /) -> None:
        if isinstance(pattern, ESDissectPattern):
            self._prefix = pattern._prefix
            self._pairs = pattern._pairs
            return

        matches: list[re.Match] = list(
            _KEY_DELIMITER_FIELD_PATTERN.finditer(pattern),
        )
        if not matches:
            raise ValueError("Dissect pattern does not contain keys.")

        self._prefix = pattern[: matches[0].start()]
        self._pairs = tuple(
            (
                ESDissectKey.parse(fst[1]),
                pattern[fst.end() : snd.start()]
                if snd is not None
                else pattern[fst.end() :],
            )
            for fst, snd in zip_longest(matches, matches[1:], fillvalue=None)
            if fst is not None
        )

    def __str__(self, /) -> str:
        return self._prefix + "".join(
            f"{key}{sep}" for key, sep in self._pairs
        )

    def __eq__(self, other: Any, /) -> bool:
        if isinstance(other, str):
            return str(self) == other
        if not isinstance(other, ESDissectPattern):
            return False

        return self._prefix == other._prefix and self._pairs == other._pairs

    @classmethod
    def __get_pydantic_core_schema__(
        cls: type[ESDissectPatternType],
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema.

        This allows the ElasticSearch dissect pattern type to be handled
        within pydantic classes, and imported/exported in JSON schemas.
        """
        return with_info_after_validator_function(
            cls._validate,
            json_or_python_schema(
                json_schema=str_schema(),
                python_schema=is_instance_schema((cls, str)),
                serialization=to_string_ser_schema(),
            ),
        )

    @classmethod
    def _validate(
        cls: type[ESDissectPatternType],
        value: str | ESDissectPatternType,
        info: ValidationInfo,
        /,
    ) -> ESDissectPatternType:
        """Validate a pydantic value.

        :param value: Value to validate.
        :param info: Validation information, if required.
        :return: Obtained pattern.
        """
        return cls(value)

    @property
    def prefix(self, /) -> str:
        """Get the prefix."""
        return self._prefix

    @property
    def pairs(self, /) -> Sequence[tuple[ESDissectKey, str]]:
        """Get the pairs."""
        return self._pairs
