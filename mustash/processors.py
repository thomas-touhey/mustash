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
"""Processors defined by Mustash."""

from __future__ import annotations

from csv import (
    Dialect as CSVDialect,
    DictReader as CSVDictReader,
    QUOTE_MINIMAL as CSV_QUOTE_MINIMAL,
)
from datetime import tzinfo
from io import StringIO
from ipaddress import IPv4Address, IPv6Address
import re
import struct
from typing import Annotated, ClassVar, Literal, Self

from annotated_types import Ge, Lt
from pydantic import StringConstraints, model_validator
from pydantic_core import from_json

from .core import Document, Element, FieldPath, FieldProcessor, Processor
from .exc import DropException
from .time import DateTimeFormatter
from .utils import CommunityID, CommunityIDTransport


class AppendProcessor(Processor):
    """Processor for adding values to a list / array."""

    field: FieldPath
    """Field with which to get the array."""

    values: list[Element]
    """Value to add to the document."""

    allow_duplicates: bool = True
    """Whether to allow duplicates in the target list."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        lst = self.field.get(document)
        if not isinstance(lst, list):
            raise ValueError(
                f"Targeted field was of type {type(lst)}, not a list",
            )

        if self.allow_duplicates:
            lst.extend(self.values)
        else:
            for value in self.values:
                if value not in lst:
                    lst.append(value)


class BooleanProcessor(FieldProcessor):
    """Processor for converting a value into a boolean."""

    async def process(self, value: Element, /) -> bool:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        if isinstance(value, str):
            if value.casefold() == "true":
                return True
            elif value.casefold() == "false":
                return False

        raise ValueError(f"Could not convert to boolean: {value!r}")


class BytesProcessor(FieldProcessor[str]):
    """Processor for converting human-readable byte values into a number.

    This processor parses the field as a string representing a size with
    a number and unit, e.g. ``123 MB``, and converts it into their
    numeric value in bytes.

    For more information, see `Bytes processor (ElasticSearch)`_ and
    `bytes mutation (Logstash)`_.

    .. _Bytes processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        bytes-processor.html
    .. _bytes mutation (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-bytes.html
    """

    _UNIT_FACTORS: ClassVar[dict[str, int]] = {
        "k": 2**10,
        "kb": 2**10,
        "m": 2**20,
        "mb": 2**20,
        "g": 2**30,
        "gb": 2**30,
        "t": 2**40,
        "tb": 2**40,
        "p": 2**50,
        "pb": 2**50,
        "b": 1,
    }
    """Available unit factors for bytes."""

    async def process(self, value: str, /) -> int:
        """Get the number of bytes from the given field.

        This method is equivalent to parseBytesSizeValue_.

        .. _parseBytesSizeValue:
            https://github.com/elastic/elasticsearch/blob/main/server/src/main/
            java/org/elasticsearch/common/unit/ByteSizeValue.java#L211

        :param value: Value to process.
        :return: Processed value.
        """
        if value in ("0", "-1"):
            # Units are required for all values except these.
            return int(value)

        value = value.casefold()
        for unit, factor in self._UNIT_FACTORS.items():
            if value.endswith(unit):
                break
        else:
            raise ValueError(f"Missing or unrecognized unit: {value}")

        value = value[: -len(unit)].rstrip()

        try:
            return int(value) * factor
        except ValueError:
            return int(float(value) * factor)


class CommunityIDProcessor(Processor):
    """Processor for computing the community ID for network flow data.

    Community ID is defined in the `Community ID Flow Hashing Specification`_.

    For more information, see `Community ID processor (ElasticSearch)`_.

    .. _Community ID Flow Hashing Specification:
        https://github.com/corelight/community-id-spec
    .. _Community ID processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        community-id-processor.html
    """

    target_field: FieldPath = FieldPath("network.community_id")
    """Output field for the community identifier."""

    source_ip_field: FieldPath = FieldPath("source.ip")
    """Path to the field containing the source IP address."""

    source_port_field: FieldPath = FieldPath("source.port")
    """Path to the field containing the source port."""

    destination_ip_field: FieldPath = FieldPath("destination.ip")
    """Path to the field containing the destination IP address."""

    destination_port_field: FieldPath = FieldPath("destination.port")
    """Path to the field containing the destination port."""

    iana_number_field: FieldPath = FieldPath("network.iana_number")
    """Path to the field containing the IANA number of the transport protocol.

    Such numbers are defined in the `Protocol Numbers`_ registry.

    .. _Protocol Numbers:
        https://www.iana.org/assignments/protocol-numbers/
        protocol-numbers.xhtml
    """

    transport_field: FieldPath = FieldPath("network.transport")
    """Path to the field containing the name of the transport protocol.

    This is only used if the field referenced by :py:attr:`iana_number_field`
    is not present in the document.
    """

    icmp_type_field: FieldPath = FieldPath("icmp.type")
    """Field containing the ICMP type."""

    icmp_code_field: FieldPath = FieldPath("icmp.code")
    """Field containing the ICMP code."""

    seed: Annotated[int, Ge(0), Lt(65536)] = 0
    """Seed for the community ID hash.

    This seed can prevent hash collisions between network domains, such as
    staging and production network that use the same addressing scheme.
    """

    ignore_missing: bool = False
    """Whether not to fail if the field is not present in the document."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        try:
            source_ip = self.source_ip_field.get(document)
            source_port = self.source_port_field.get(document, cls=int)
            destination_ip = self.destination_ip_field.get(document)
            destination_port = self.destination_port_field.get(
                document,
                cls=int,
            )

            try:
                transport = CommunityIDTransport.from_iana_number(
                    self.iana_number_field.get(document, cls=int),
                )
            except KeyError:
                transport = CommunityIDTransport.from_name(
                    self.transport_field.get(document),
                )

            if transport.is_icmp():
                icmp_type = self.icmp_type_field.get(document)
                icmp_code = self.icmp_code_field.get(document)
            else:
                icmp_type = None
                icmp_code = None
        except KeyError:
            if self.ignore_missing:
                return

            raise

        community_id = CommunityID(
            source_ip=source_ip,
            source_port=source_port,
            destination_ip=destination_ip,
            destination_port=destination_port,
            transport=transport,
            icmp_type=icmp_type,
            icmp_code=icmp_code,
            seed=self.seed,
        ).compute()

        self.target_field.set(document, community_id, override=True)


class CopyProcessor(Processor):
    """Processor for appending values to an existing array.

    For more information, see `Set processor (ElasticSearch)`_ and
    `copy mutation (Logstash)`_.

    .. _Set processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        set-processor.html
    .. _copy mutation (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-mutate.html#plugins-filters-mutate-copy
    """

    field: FieldPath
    """Field from which to get the size."""

    target_field: FieldPath
    """Target field to set with the result."""

    ignore_empty_value: bool = False
    """Whether not to set an empty value."""

    override: bool = True
    """Whether to override the field if already exists."""

    remove_if_successful: bool = False
    """Whether to remove the source field after processing it."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        try:
            value = self.field.get(document)
        except KeyError:
            if self.ignore_empty_value:
                return

            raise

        if self.ignore_empty_value and (value is None or value == ""):
            return

        if not self.override:
            try:
                self.target_field.get(document)
            except KeyError:
                pass
            else:
                return

        self.target_field.set(document, value)

        if self.remove_if_successful:
            self.field.delete(document)


class CSVProcessor(Processor):
    """Processor for parsing a singleCSV line.

    For more information, see `CSV processor (ElasticSearch)`_ and
    `csv filter (Logstash)`_.

    .. _CSV processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        csv-processor.html
    .. _csv filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-csv.html
    """

    field: FieldPath
    """Field to extract data from."""

    target_fields: list[FieldPath]
    """Array of fields to assign extracted values to."""

    separator: Annotated[
        str,
        StringConstraints(min_length=1, max_length=1),
    ] = ","
    """Single-character separator used in CSV."""

    quote: Annotated[str, StringConstraints(min_length=1, max_length=1)] = '"'
    """Single-character quote used in CSV."""

    ignore_missing: bool = False
    """Whether to raise an error if the source field does not exist."""

    trim: bool = False
    """Whether to trim whitespaces in the unquoted fields."""

    empty_value: str = ""
    """Value used to fill empty fields."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        try:
            raw_line = self.field.get(document)
        except KeyError:
            if self.ignore_missing:
                return

            raise

        class dialect(CSVDialect):
            delimiter = self.separator
            quotechar = self.quote
            lineterminator = "\n"
            quoting = CSV_QUOTE_MINIMAL

        reader = CSVDictReader(
            StringIO(raw_line),
            fieldnames=self.target_fields,
            dialect=dialect,
        )
        result = next(reader)
        if None in result:
            del result[None]

        for field, value in result.items():
            field.set(document, value)


class DateProcessor(FieldProcessor):
    """Processor for parsing dates and adding a timestamp.

    For more information, see `Date processor (ElasticSearch)`_
    and `date filter (Logstash)`_.

    .. _Date processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        date-processor.html
    .. _date filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-date.html
    """

    parse_handler: DateTimeFormatter
    """Date and time parsing handler."""

    output_handler: DateTimeFormatter
    """Date and time format handler."""

    timezone: tzinfo
    """Timezone to use when parsing the date."""

    async def process(self, value: Element, /) -> Element:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        dt = self.parse_handler.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.timezone)

        return self.output_handler.format(dt)


class DropProcessor(Processor):
    """Processor for dropping the current document."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        raise DropException()


class FloatingPointProcessor(FieldProcessor):
    """Processor for converting a value into a floating-point number."""

    precision: Literal["half", "double"]
    """Precision expected for the target field."""

    async def process(self, value: Element, /) -> float:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        float_value = float(value)  # type: ignore

        # If the precision is half, we need to force the precision.
        if self.precision == "half":
            (float_value,) = struct.unpack("f", struct.pack("f", float_value))

        return float_value


class IntegerProcessor(FieldProcessor):
    """Processor for converting a value into an integer."""

    max: int | None = None
    """Maximum accepted number, included."""

    min: int | None = None
    """Minimum accepted number, included."""

    async def process(self, value: Element, /) -> int:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        value = int(value)  # type: ignore

        if (self.min is not None and value < self.min) or (
            self.max is not None and value > self.max
        ):
            if self.min is None:
                raise ValueError(
                    f"Value must be less than or equal to {self.min}",
                )
            elif self.max is None:
                raise ValueError(
                    f"Value must be greater than or equal to {self.max}",
                )
            else:
                raise ValueError(
                    f"Value must be between {self.min} and {self.max} "
                    + "included.",
                )

        return value


class IPAddressProcessor(FieldProcessor):
    """Processor for converting a value into an IPv4 or IPv6 address."""

    async def process(self, value: Element, /) -> IPv4Address | IPv6Address:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        try:
            return IPv4Address(value)
        except ValueError:
            return IPv6Address(value)


class JsonProcessor(Processor):
    """Processor for parsing raw JSON from a field into another, or root."""

    field: FieldPath
    """Field from which to read raw JSON."""

    target_field: FieldPath | None = None
    """Field to populate with the parsed JSON data."""

    add_to_root: bool = False
    """Whether to add the parsed data to root rather than in a target field.

    This must not be defined to :py:data:`True` if :py:attr:`target_field`
    is defined.
    """

    @model_validator(mode="after")
    def _validate(self) -> Self:
        """Validate the processor.

        :return: Validated object.
        """
        if self.target_field is not None and self.add_to_root:
            raise ValueError(
                "target_field must not be defined if add_to_root is set "
                + "to true.",
            )

        return self

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        value = self.field.get(document)
        if not isinstance(value, str):
            raise TypeError(
                f"Invalid type {type(value)} for field {self.field}",
            )

        result = from_json(value)
        if not isinstance(result, dict):
            raise ValueError(f"Parsed field was not an array: {result}")

        if self.add_to_root:
            for key, value in result.items():
                # TODO: allow_duplicates?
                document[key] = value
        elif self.target_field is not None:
            self.target_field.set(document, result)
        else:
            self.field.set(document, result)


class KeepProcessor(Processor):
    """Processor for only keeping some fields.

    For more information, see `Remove processor (ElasticSearch)`_
    and `prune filter (Logstash)`_.

    .. _Remove processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        remove-processor.html
    .. _prune filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-prune.html
    """

    fields: set[FieldPath]
    """Fields to keep."""

    @model_validator(mode="after")
    def _validate(self, /) -> Self:
        """Validate the model.

        We want to obtain a subset of the paths to avoid paths containing
        each other here, and only keep the greatest scope.
        """
        fields: set[FieldPath] = set()
        for field in self.fields:
            # Two cases here:
            # * If we find a path in the already added paths that is contained
            #   by the new path, we remove it.
            # * If we find a path that contains the new path, we just discard
            #   the new path.
            for sub_field in list(fields):
                if field in sub_field:
                    # We treat this case first, as if field == sub_field,
                    # we want to prioritize discarding the new field.
                    break
                elif sub_field in field:
                    fields.remove(sub_field)
            else:
                fields.add(field)

        self.fields = fields
        return self

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        raise NotImplementedError()  # TODO


class LowercaseProcessor(FieldProcessor[str]):
    """Processor for converting a string to its lowercase equivalent.

    For more information, see `Lowercase processor (ElasticSearch)`_
    and `lowercase mutation (Logstash)`_.

    .. _Lowercase processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        lowercase-processor.html
    .. _lowercase mutation (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-mutate.html#plugins-filters-mutate-lowercase
    """

    async def process(self, value: str, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        return value.lower()


class RemoveProcessor(Processor):
    """Processor for removing one or more fields.

    For more information, see `Remove processor (ElasticSearch)`_
    and `prune filter (Logstash)`_.

    .. _Remove processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        remove-processor.html
    .. _prune filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-prune.html
    """

    fields: set[FieldPath]
    """Fields to remove."""

    ignore_missing: bool = False
    """Whether to ignore any field to remove missing from the document."""

    @model_validator(mode="after")
    def _validate(self, /) -> Self:
        """Validate the model.

        We want to obtain a subset of the paths to avoid paths containing
        each other here, and only keep the greatest scope.
        """
        fields: set[FieldPath] = set()
        for field in self.fields:
            # Two cases here:
            # * If we find a path in the already added paths that is contained
            #   by the new path, we remove it.
            # * If we find a path that contains the new path, we just discard
            #   the new path.
            for sub_field in list(fields):
                if field in sub_field:
                    # We treat this case first, as if field == sub_field,
                    # we want to prioritize discarding the new field.
                    break
                elif sub_field in field:
                    fields.remove(sub_field)
            else:
                fields.add(field)

        self.fields = fields
        return self

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        if not self.ignore_missing:
            for field in self.fields:
                # Check that the field is indeed defined.
                try:
                    field.get(document)
                except KeyError as exc:
                    raise ValueError(
                        f"No field to delete at {exc.args[0]}",
                    ) from exc

        for field in self.fields:
            try:
                field.delete(document)
            except KeyError:
                # If ignore_missing is True, we do not care about
                # any error here.
                # If ignore_missing is False, we have already raised an
                # error before, so this should not occur.
                continue


class SetProcessor(Processor):
    """Processor for setting a field to a value."""

    field: FieldPath
    """Field with which to get the array."""

    value: Element
    """Value to add to the document."""

    override: bool = True
    """Whether to override the field if already exists."""

    ignore_empty_value: bool = False
    """Whether not to set an empty value."""

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        if self.ignore_empty_value and (
            self.value is None or self.value == ""
        ):
            return

        self.field.set(document, self.value, override=self.override)


class SortProcessor(FieldProcessor[list]):
    """Processor for sorting an array.

    For more information, see `Sort processor (ElasticSearch)`_.

    .. _Sort processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        sort-processor.html
    """

    order: Literal["asc", "desc"] = "asc"
    """Order in which the array should be sorted."""

    async def process(self, value: list, /) -> list:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        return sorted(value, reverse=self.order == "desc")


class RegexpSplitProcessor(FieldProcessor[str]):
    """Processor for splitting a string into an array.

    For more information, see `Split processor (ElasticSearch)`_ and
    `split filter (Logstash)`_.

    .. _Split processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        split-processor.html
    .. _split filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-split.html
    """

    separator: re.Pattern
    """Separator pattern."""

    preserve_trailing: bool = False
    """Whether to preserve empty trailing fields, if any."""

    async def process(self, value: str, /) -> list[str]:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        last_index = 0
        values: list[str] = []

        for match in self.separator.finditer(value):
            values.append(value[last_index : match.start()])
            last_index = match.end()

        values.append(value[last_index:])

        if not self.preserve_trailing:
            try:
                last_not_empty_index = next(
                    i
                    for i, value in zip(
                        range(len(values) - 1, -1, -1),
                        values[::-1],
                    )
                    if value
                )
            except StopIteration:
                values[:] = []
            else:
                values[last_not_empty_index + 1 :] = []

        return values


class StringProcessor(FieldProcessor):
    """Processor for converting a value into a string."""

    async def process(self, value: Element, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        return str(value)


class TrimProcessor(FieldProcessor[str | list[str]]):
    """Processor for trimming a string.

    For more information, see `Trim processor (ElasticSearch)`_
    and `strip mutation (Logstash)`_.

    .. _Trim processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        trim-processor.html
    .. _strip mutation (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-mutate.html#plugins-filters-mutate-strip
    """

    async def process(self, value: str | list[str], /) -> str | list[str]:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        if isinstance(value, list):
            return [x.strip() for x in value]

        return value.strip()


class UppercaseProcessor(FieldProcessor[str]):
    """Processor for converting a string to its uppercase equivalent.

    For more information, see `Uppercase processor (ElasticSearch)`_
    and `uppercase mutation (Logstash)`_.

    .. _Uppercase processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        uppercase-processor.html
    .. _uppercase mutation (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-mutate.html#plugins-filters-mutate-uppercase
    """

    async def process(self, value: str, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        return value.upper()


class URIPartsProcessor(FieldProcessor[str]):
    """Processor for parsing an URI to extract parts.

    For more information, see `URI parts processor (ElasticSearch)`_.

    .. _URI parts processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        uri-parts-processor.html
    """

    keep_original: bool = True
    """Whether to keep the original URI as ``<target_field>.original``."""

    async def process(self, value: str, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        raise NotImplementedError()  # TODO


class URLDecodeProcessor(FieldProcessor[str]):
    """Processor for decoding an URL.

    For more information, see `URL decode processor (ElasticSearch)`
    and `urldecode filter (Logstash)`_.

    .. _URL decode processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        urldecode-processor.html
    .. _urldecode filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-urldecode.html
    """

    async def process(self, value: str, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        raise NotImplementedError()  # TODO


class UserAgentProcessor(FieldProcessor[str]):
    """Processor for parsing a user agent.

    For more information, see `User agent processor (ElasticSearch)`_
    and `useragent filter (Logstash)`_.

    .. _User agent processor (ElasticSearch):
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        user-agent-processor.html
    .. _useragent filter (Logstash):
        https://www.elastic.co/guide/en/logstash/current/
        plugins-filters-useragent.html
    """

    regex_file: str | None = None
    """Name of the file containing the regular expressions for parsing."""

    properties: list[str] = [
        "name",
        "major",
        "minor",
        "patch",
        "build",
        "os",
        "os_name",
        "os_major",
        "os_minor",
        "device",
    ]
    """Properties to add to the target."""

    async def process(self, value: str, /) -> str:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
        raise NotImplementedError()  # TODO
