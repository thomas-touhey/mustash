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
"""Utilities for Mustash."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Any

from annotated_types import Ge, Lt
from pydantic import BaseModel
from pydantic._internal._generics import (
    get_args as get_typing_args,
    get_origin as get_typing_origin,
)


class Runk(BaseModel):
    """Ronald's universal number kounter.

    This counts lines, columns and offsets.
    """

    line: int = 1
    """Line number, counting from 1."""

    column: int = 1
    """Column number, counting from 1."""

    offset: int = 0
    """Offset in the string, counting from 0."""

    def count(self, raw: str, /) -> None:
        """Add a string to the count.

        :param raw: Raw string to take into account.
        """
        self.offset += len(raw)
        try:
            newline_offset = raw.rindex("\n")
        except ValueError:
            self.column += len(raw)
        else:
            self.line += raw.count("\n")
            self.column = len(raw) - newline_offset


class NoValueType:
    """Type for the NO_VALUE constant."""

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        """Create or return the NO_VALUE constant."""
        try:
            return cls.__unique_value__
        except AttributeError:
            value = super().__new__(cls, *args, **kwargs)
            cls.__unique_value__ = value
            return value

    def __repr__(self):
        return "NO_VALUE"


NO_VALUE = NoValueType()
"""Constant representing the absence of a value.

The type of this value is a singleton.
"""


def get_generic_args(
    generic: Any,
    value: Any,
    /,
) -> tuple[Any, ...]:
    """Get the generic arguments.

    :param generic: The generic class to detect and extract parameters from.
    :param value: The value from which to get the generic class parameters.
    :return: The generic class parameters.
    :raises TypeError: The value is not an instance of the generic class.
    """
    try:
        bases = list(value.__class__.__orig_bases__)
        bases.extend(value.__class__.__bases__)
    except AttributeError:
        pass
    else:
        while bases:
            new_bases = []
            for base in bases:
                if base is generic:
                    break

                origin = get_typing_origin(base)
                if origin is generic:
                    return get_typing_args(base)

                try:
                    new_bases.extend(base.__orig_bases__)
                except AttributeError:
                    pass

            bases = new_bases

    raise TypeError(f"Value {value!r} is not an instance of {generic!r}.")


def get_generic_arg(
    generic: Any,
    value: Any,
    /,
    *,
    default: type | NoValueType = NO_VALUE,
) -> Any:
    """Get the generic argument.

    :param generic: The generic class to detect and extract parameters from.
    :param value: The value from which to get the generic class parameters.
    :param default: Default value to return.
    :return: The generic class parameters.
    :raises TypeError: The value is not an instance of the generic class.
    """
    try:
        (arg,) = get_generic_args(generic, value)
    except TypeError:
        if isinstance(default, NoValueType):
            raise

        return default
    else:
        return arg


class CommunityIDTransport(BaseModel):
    """Details regarding the community ID transport."""

    @classmethod
    def from_iana_number(cls, number: int, /) -> CommunityIDTransport:
        """Get transport details from the IANA protocol number.

        :param number: IANA number of the protocol.
        :return: Transport details.
        """
        raise NotImplementedError()  # TODO

    @classmethod
    def from_name(cls, name: str, /) -> CommunityIDTransport:
        """Get transport details from the protocol name.

        :param name: Name of the protocol.
        :return: Transport details.
        """
        raise NotImplementedError()  # TODO

    def is_icmp(self, /) -> bool:
        """Check if the transport is ICMP."""
        raise NotImplementedError()  # TODO


class CommunityID(BaseModel):
    """Details regarding a community ID to compute.

    See `Community ID Flow Hashing Specification`_ for more information.

    .. _Community ID Flow Hashing Specification:
        https://github.com/corelight/community-id-spec
    """

    source_ip: IPv4Address | IPv6Address
    """Source IP address."""

    source_port: Annotated[int, Ge(0), Lt(65536)]
    """Source port."""

    destination_ip: IPv4Address | IPv6Address
    """Destination IP address."""

    destination_port: Annotated[int, Ge(0), Lt(65536)]
    """Destination port."""

    transport: CommunityIDTransport
    """Transport protocol."""

    icmp_type: str | None = None
    """ICMP packet type, if relevant."""

    icmp_code: str | None = None
    """ICMP packet code, if relevant."""

    seed: Annotated[int, Ge(0), Lt(65536)] = 0
    """Seed for the community ID hash.

    This seed can prevent hash collisions between network domains, such as
    staging and production network that use the same addressing scheme.
    """

    def compute(self, /) -> str:
        """Compute the community ID out of the provided details.

        :return: Community ID.
        """
        raise NotImplementedError()  # TODO
