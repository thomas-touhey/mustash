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
"""ElasticSearch ingest pipeline conversion utilities."""

from __future__ import annotations

from abc import ABC
from collections.abc import Iterable
import re
from typing import Annotated, Any, Literal, TypeVar, Union

from annotated_types import Ge, Lt
from dissec.patterns import Pattern as DissectPattern
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    create_model,
    model_validator,
)
from typing_extensions import TypeAliasType

from .core import Element, PainlessCondition, Pipeline, Processor
from .processors import (
    AppendProcessor,
    BooleanProcessor,
    BytesProcessor,
    CSVProcessor,
    CommunityIDProcessor,
    CopyProcessor,
    DateProcessor,
    FloatingPointProcessor,
    IPAddressProcessor,
    IntegerProcessor,
    JsonProcessor,
    KeepProcessor,
    LowercaseProcessor,
    RegexpSplitProcessor,
    RemoveProcessor,
    SetProcessor,
    SortProcessor,
    StringProcessor,
    TrimProcessor,
    URIPartsProcessor,
    URLDecodeProcessor,
    UppercaseProcessor,
    UserAgentProcessor,
)
from .time import (
    FallbackDateTimeFormatter,
    ISO8601DateTimeFormatter,
    JavaDateTimeFormatter,
    ESTAI64NDateTimeFormatter,
    UNIXDateTimeFormatter,
    UNIXMSDateTimeFormatter,
)


_ProcessorType = TypeVar("_ProcessorType", bound=Processor)


class _ESProcessorWrapper(BaseModel):
    """ElasticSearch processor wrapper.

    This class is used for wrappers built dynamically by the pipeline parser.
    """

    value: ESProcessor
    """Actual processor being run."""


class ESProcessor(ABC, BaseModel):
    """ElasticSearch processor.

    This class is used for parsing and rendering ElasticSearch ingest
    pipelines, in order to ensure that we check all options, forbid
    additional options, and so on.
    """

    model_config = ConfigDict(extra="forbid")
    """Model configuration."""

    description: str | None = None
    if_: Annotated[str | None, Field(alias="if")] = None
    ignore_failure: bool = False
    on_failure: list[_ESProcessorWrapper] | None = None
    tag: str | None = None

    def build(self, cls: type[_ProcessorType], /, **kwargs) -> _ProcessorType:
        """Obtain a Mustash processor out of the current processor.

        This also manages common parameters for all processors.
        """
        return cls(
            description=self.description,
            condition=(
                PainlessCondition(self.if_) if self.if_ is not None else None
            ),
            ignore_failure=self.ignore_failure,
            on_failure=(
                [proc.value.convert() for proc in self.on_failure]
                if self.on_failure is not None
                else None
            ),
            tag=self.tag,
            **kwargs,
        )

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        :raises NotImplementedError: No processor is currently available
            for this configuration of the processor.
        """
        raise NotImplementedError()


# HACK: Fix the circular dependency.
_ESProcessorWrapper.model_rebuild()


# ---
# ElasticSearch processor definitions.
# ---


class ESAppendProcessor(ESProcessor):
    """ElasticSearch append processor.

    See `Append processor`_ for more information.

    .. _Append processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        append-processor.html
    """

    field: str
    value: Element | list[Element]
    allow_duplicates: bool = True

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            AppendProcessor,
            field=self.field,
            values=self.value
            if isinstance(self.value, list)
            else [self.value],
            allow_duplicates=self.allow_duplicates,
        )


class ESBytesProcessor(ESProcessor):
    """ElasticSearch bytes processor.

    See `Bytes processor`_ for more information.

    .. _Bytes processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        bytes-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            BytesProcessor,
            field=self.field,
            target_field=self.target_field,
            ignore_missing=self.ignore_missing,
        )


class ESCommunityIDProcessor(ESProcessor):
    """ElasticSearch Community ID processor.

    See `Community ID processor`_ for more information.

    .. _Community ID processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        community-id-processor.html
    """

    source_ip: str = "source.ip"
    source_port: str = "source.port"
    destination_ip: str = "destination.ip"
    destination_port: str = "destination.port"
    iana_number: str = "network.iana_number"
    icmp_type: str = "icmp.type"
    icmp_code: str = "icmp.code"
    transport: str = "network.transport"
    target_field: str = "network.community_id"
    seed: Annotated[int, Ge(0), Lt(65536)] = 0
    ignore_missing: bool = True

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            CommunityIDProcessor,
            target_field=self.target_field,
            source_ip_field=self.source_ip,
            source_port_field=self.source_port,
            destination_ip_field=self.destination_ip,
            destination_port_field=self.destination_port,
            iana_number_field=self.iana_number,
            icmp_type_field=self.icmp_type,
            icmp_code_field=self.icmp_code_field,
            transport_field=self.transport,
            seed=self.seed,
            ignore_missing=self.ignore_missing,
        )


class ESConvertProcessor(ESProcessor):
    """ElasticSearch convert processor.

    See `Convert processor`_ for more information.

    .. _Convert processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        convert-processor.html
    """

    field: str
    target_field: str | None = None
    type: Literal[
        "integer",
        "long",
        "float",
        "double",
        "string",
        "boolean",
        "ip",
        "auto",
    ]
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        if self.type == "integer":
            return IntegerProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
                min=-(2**31),
                max=2**31 - 1,
            )
        elif self.type == "long":
            return IntegerProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
                min=-(2**63),
                max=2**63 - 1,
            )
        elif self.type == "float":
            return FloatingPointProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
                precision="half",
            )
        elif self.type == "double":
            return FloatingPointProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
                precision="double",
            )
        elif self.type == "string":
            return StringProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
            )
        elif self.type == "boolean":
            return BooleanProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
            )
        elif self.type == "ip":
            return IPAddressProcessor(
                field=self.field,
                target_field=self.target_field,
                ignore_missing=self.ignore_missing,
            )

        raise NotImplementedError()


class ESCSVProcessor(ESProcessor):
    """ElasticSearch CSV processor.

    See `CSV processor`_ for more information.

    .. _CSV processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        csv-processor.html
    """

    field: str
    target_fields: list[str]
    separator: Annotated[
        str,
        StringConstraints(min_length=1, max_length=1),
    ] = ","
    quote: Annotated[str, StringConstraints(min_length=1, max_length=1)] = '"'
    ignore_missing: bool = False
    trim: bool = False
    empty_value: str = ""

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            CSVProcessor,
            field=self.field,
            target_fields=self.target_fields,
            separator=self.separator,
            quote=self.quote,
            ignore_missing=self.ignore_missing,
            trim=self.trim,
            empty_value=self.empty_value,
        )


class ESDateProcessor(ESProcessor):
    """ElasticSearch date processor.

    See `Date processor`_ for more information.

    .. _Date processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        date-processor.html
    """

    field: str
    target_field: str = "@timestamp"
    formats: list[str]
    timezone: str = "UTC"
    locale: str = "ENGLISH"
    output_format: str = "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        parse_handlers = [
            ISO8601DateTimeFormatter()
            if value == "ISO8601"
            else UNIXDateTimeFormatter()
            if value == "UNIX"
            else UNIXMSDateTimeFormatter()
            if value == "UNIX_MS"
            else ESTAI64NDateTimeFormatter()
            if value == "TAI64N"
            else JavaDateTimeFormatter(
                pattern=value,
                locale=self.locale,
            )
            for value in self.formats
        ]
        if len(parse_handlers) == 1:
            parse_handler = parse_handlers[0]
        else:
            parse_handler = FallbackDateTimeFormatter(handlers=parse_handlers)

        return self.build(
            DateProcessor,
            field=self.field,
            target_field=self.target_field,
            parse_handler=parse_handler,
            output_handler=JavaDateTimeFormatter(
                pattern=self.output_format,
                locale=self.locale,
            ),
            timezone=self.timezone,
        )


class ESDateIndexNameProcessor(ESProcessor):
    """ElasticSearch date index name processor.

    See `Date index name processor`_ for more information.

    .. _Date index name processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        date-index-name-processor.html
    """

    field: str
    index_name_prefix: str | None = None
    date_rounding: Literal["y", "M", "w", "d", "h", "m", "s"]
    date_formats: str | list[str] = "yyyy-MM-dd'T'HH:mm:ss.SSSXX"
    timezone: str = "UTC"
    locale: str = "ENGLISH"
    index_name_format: str = "yyyy-MM-dd"


class ESDissectProcessor(ESProcessor):
    """ElasticSearch dissect processor.

    See `Dissect processor`_ for more information.

    .. _Dissect processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        dissect-processor.html
    """

    field: str
    pattern: DissectPattern
    append_separator: str = ""
    ignore_missing: bool = False


class ESDotExpander(ESProcessor):
    """ElasticSearch dot expander processor.

    See `Dot expander processor`_ for more information.

    .. _Dot expander processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        dot-expand-processor.html
    """

    field: str
    path: str | None = None
    override: bool = False


class ESDropProcessor(ESProcessor):
    """ElasticSearch drop processor.

    See `Drop processor`_ for more information.

    .. _Drop processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        drop-processor.html
    """


class ESFailProcessor(ESProcessor):
    """ElasticSearch fail processor.

    See `Fail processor`_ for more information.

    .. _Fail processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        fail-processor.html
    """

    message: str


class ESFingerprintProcessor(ESProcessor):
    """ElasticSearch fingerprint processor.

    See `Fingerprint processor`_ for more information.

    .. _Fingerprint processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        fingerprint-processor.html
    """

    fields: list[str]
    target_field: str = "fingerprint"
    salt: str | None = None
    method: Literal[
        "MD5",
        "SHA-1",
        "SHA-256",
        "SHA-512",
        "MurmurHash3",
    ] = "SHA-1"
    ignore_missing: bool = False


class ESGeoIPProcessor(ESProcessor):
    """ElasticSearch GeoIP processor.

    See `GeoIP processor`_ for more information.

    .. _GeoIP processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        geoip-processor.html
    """

    field: str
    target_field: str = "@timestamp"
    database_file: str = "GeoLite2-City.mmdb"
    properties: list[str] = [
        "continent_name",
        "country_iso_code",
        "country_name",
        "region_iso_code",
        "region_name",
        "city_name",
        "location",
    ]
    ignore_missing: bool = False
    download_database_on_pipeline_creation: bool = True


class ESGrokProcessor(ESProcessor):
    """ElasticSearch grok processor.

    See `Grok processor`_ for more information.

    .. _Grok processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        grok-processor.html
    """

    field: str
    patterns: list[str]
    pattern_definitions: dict[str, str] | None = None
    ecs_compatibility: Literal["disabled", "v1"] = "disabled"
    trace_match: bool = False
    ignore_missing: bool = False


class ESGsubProcessor(ESProcessor):
    """ElasticSearch gsub processor.

    See `Gsub processor`_ for more information.

    .. _Gsub processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        gsub-processor.html
    """

    field: str
    pattern: str
    replacement: str
    target_field: str | None = None
    ignore_missing: bool = False


class ESHTMLStripProcessor(ESProcessor):
    """ElasticSearch HTML strip processor.

    See `HTML strip processor`_ for more information.

    .. _HTML strip processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        htmlstrip-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False


class ESJoinProcessor(ESProcessor):
    """ElasticSearch join processor.

    See `Join processor`_ for more information.

    .. _Join processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        join-processor.html
    """

    field: str
    separator: str
    target_field: str | None = None


class ESJSONProcessor(ESProcessor):
    """ElasticSearch JSON processor.

    See `JSON processor`_ for more information.

    .. _JSON processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        json-processor.html
    """

    field: str
    target_field: str | None = None
    add_to_root: bool = False
    add_to_root_conflict_strategy: Literal["replace", "merge"] = "replace"
    allow_duplicate_keys: bool = False
    strict_json_parsing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        # TODO: Not all keys are transposed into the Mustash processor.
        return JsonProcessor(
            field=self.field,
            target_field=self.target_field,
            add_to_root=self.add_to_root,
        )


class ESKVProcessor(ESProcessor):
    """ElasticSearch KV processor.

    See `KV processor`_ for more information.

    .. _KV processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        kv-processor.html
    """

    field: str
    field_split: re.Pattern
    value_split: re.Pattern
    target_field: str | None = None
    include_keys: list[str] | None = None
    exclude_keys: list[str] | None = None
    ignore_missing: bool = False
    prefix: str = ""
    trim_key: str = ""
    trim_value: str = ""
    strip_brackets: bool = False


class ESLowercaseProcessor(ESProcessor):
    """ElasticSearch lowercase processor.

    See `Lowercase processor`_ for more information.

    .. _Lowercase processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        lowercase-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            LowercaseProcessor,
            field=self.field,
            target_field=self.target_field,
            ignore_missing=self.ignore_missing,
        )


class ESNetworkDirectionProcessor(ESProcessor):
    """ElasticSearch network direction processor.

    See `Network direction processor`_ for more information.

    .. _Network direction processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        network-direction-processor.html
    """

    source_ip: str = "source.ip"
    destination_ip: str = "destination.ip"
    target_field: str = "network.direction"
    internal_networks: list[str] | None = None
    internal_networks_field: str | None = None
    ignore_missing: bool = True

    @model_validator(mode="after")
    def _validate(self, /) -> ESNetworkDirectionProcessor:
        """Validate the model."""
        if (self.internal_networks is None) == (
            self.internal_networks_field is None
        ):
            raise ValueError(
                "Either internal_networks or internal_networks_field "
                + "must be defined.",
            )

        return self


class ESRedactProcessor(ESProcessor):
    """ElasticSearch redact processor.

    See `Redact processor`_ for more information.

    .. _Redact processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        redact-processor.html
    """

    field: str
    patterns: list[str]
    pattern_definitions: dict[str, str] | None = None
    prefix: str = "<"
    suffix: str = ">"
    ignore_missing: bool = False


class ESRegisteredDomainProcessor(ESProcessor):
    """ElasticSearch registered domain processor.

    See `Registered domain processor`_ for more information.

    .. _Registered domain processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        registered-domain-processor.html
    """

    field: str
    target_field: str = ""
    ignore_missing: bool = True


class ESRemoveProcessor(ESProcessor):
    """ElasticSearch remove processor.

    See `Remove processor`_ for more information.

    .. _Remove processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        remove-processor.html
    """

    field: str | list[str] | None = None
    ignore_missing: bool = False
    keep: str | list[str] | None = None

    @model_validator(mode="after")
    def _validate(self, /) -> ESRemoveProcessor:
        """Validate the model."""
        if (self.field is None) == (self.keep is None):
            raise ValueError("Either field or keep must be defined.")

        return self

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        if self.keep is not None:
            return self.build(
                KeepProcessor,
                fields=(
                    self.keep if isinstance(self.keep, list) else [self.keep]
                ),
            )
        elif self.field is not None:
            return self.build(
                RemoveProcessor,
                fields=(
                    self.field
                    if isinstance(self.field, list)
                    else [self.field]
                ),
                ignore_missing=self.ignore_missing,
            )
        else:  # pragma: no cover
            raise AssertionError("Both field and keep are not defined.")


class ESRenameProcessor(ESProcessor):
    """ElasticSearch rename processor.

    See `Rename processor`_ for more information.

    .. _Rename processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        rename-processor.html
    """

    field: str
    target_field: str
    ignore_missing: bool = False
    override: bool = False


class ESRerouteProcessor(ESProcessor):
    """ElasticSearch reroute processor.

    See `Reroute processor`_ for more information.

    .. _Reroute processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        reroute-processor.html
    """

    destination: str | None = None
    dataset: str = "{{data_stream.dataset}}"
    namespace: str = "{{data_stream.namespace}}"


class ESScriptProcessor(ESProcessor):
    """ElasticSearch script processor.

    See `Script processor`_ for more information.

    .. _Script processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        script-processor.html
    """

    # TODO: Support more than painless.
    lang: Literal["painless"] = "painless"
    id: str | None = None
    source: str | dict | None = None
    params: dict[str, Any] | None = None


class ESSetProcessor(ESProcessor):
    """ElasticSearch set processor.

    See `Set processor`_ for more information.

    .. _Set processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        set-processor.html
    """

    field: str
    value: str | None = None
    copy_from: str | None = None
    override: bool = True
    ignore_empty_value: bool = False
    media_type: str = "application/json"

    @model_validator(mode="after")
    def _validate(self, /) -> ESRemoveProcessor:
        """Validate the model."""
        if (self.value is None) == (self.copy_from is None):
            raise ValueError("Either value or copy_from must be defined.")

        return self

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        if self.value is not None:
            return self.build(
                SetProcessor,
                field=self.field,
                value=self.value,
                override=self.override,
                ignore_empty_value=self.ignore_empty_value,
            )
        elif self.copy_from is not None:
            return self.build(
                CopyProcessor,
                field=self.copy_from,
                target_field=self.field,
                override=self.override,
                ignore_empty_value=self.ignore_empty_value,
            )
        else:  # pragma: no cover
            raise ValueError("Either value or copy_from must be defined.")


class ESSetSecurityUserProcessor(ESProcessor):
    """ElasticSearch set security user processor.

    See `Set security user processor`_ for more information.

    .. _Set security user processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        ingest-node-set-security-user-processor.html
    """

    field: str
    properties: list[str] = [
        "username",
        "roles",
        "email",
        "full_name",
        "metadata",
        "api_key",
        "realm",
        "authentication_type",
    ]


class ESSortProcessor(ESProcessor):
    """ElasticSearch sort processor.

    See `Sort processor`_ for more information.

    .. _Sort processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        sort-processor.html
    """

    field: str
    order: Literal["asc", "desc"]
    target_field: str | None = None

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            SortProcessor,
            field=self.field,
            target_field=self.target_field,
            order=self.order,
        )


class ESSplitProcessor(ESProcessor):
    """ElasticSearch split processor.

    See `Split processor`_ for more information.

    .. _Split processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        split-processor.html
    """

    field: str
    separator: re.Pattern
    target_field: str | None = None
    ignore_missing: bool = False
    preserve_trailing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            RegexpSplitProcessor,
            field=self.field,
            target_field=self.target_field,
            separator=self.separator,
            ignore_missing=self.ignore_missing,
            preserve_trailing=self.preserve_trailing,
        )


class ESTrimProcessor(ESProcessor):
    """ElasticSearch trim processor.

    See `Trim processor`_ for more information.

    .. _Trim processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        trim-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            TrimProcessor,
            field=self.field,
            target_field=self.target_field,
            ignore_missing=self.ignore_missing,
        )


class ESUppercaseProcessor(ESProcessor):
    """ElasticSearch uppercase processor.

    See `Uppercase processor`_ for more information.

    .. _Uppercase processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        uppercase-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            UppercaseProcessor,
            field=self.field,
            target_field=self.target_field,
            ignore_missing=self.ignore_missing,
        )


class ESURIPartsProcessor(ESProcessor):
    """ElasticSearch URI parts processor.

    See `URI parts processor`_ for more information.

    .. _URI parts processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        uri-parts-processor.html
    """

    field: str
    target_field: str | None = None
    keep_original: bool = True
    remove_if_successful: bool = False
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            URIPartsProcessor,
            field=self.field,
            target_field=self.target_field,
            keep_original=self.keep_original,
            remove_if_successful=self.remove_if_successful,
            ignore_missing=self.ignore_missing,
        )


class ESURLDecodeProcessor(ESProcessor):
    """ElasticSearch URL decode processor.

    See `URL decode processor`_ for more information.

    .. _URL decode processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        urldecode-processor.html
    """

    field: str
    target_field: str | None = None
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            URLDecodeProcessor,
            field=self.field,
            target_field=self.target_field,
            ignore_missing=self.ignore_missing,
        )


class ESUserAgentProcessor(ESProcessor):
    """ElasticSearch user agent processor.

    See `User agent processor`_ for more information.

    .. _User agent processor:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        user-agent-processor.html
    """

    field: str
    target_field: str = "user_agent"
    regex_file: str | None = None
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
    ignore_missing: bool = False

    def convert(self, /) -> Processor:
        """Convert the ElasticSearch processor into a Mustash processor.

        :return: Converted processor.
        """
        return self.build(
            UserAgentProcessor,
            field=self.field,
            target_field=self.target_field,
            regex_file=self.regex_file,
            properties=self.properties,
            ignore_missing=self.ignore_missing,
        )


# ---
# ElasticSearch ingest pipeline conversion utilities.
# ---


class _ESPipeline(BaseModel):
    """Pipeline model."""

    name: str
    """Name of the pipeline."""

    processors: list[_ESProcessorWrapper] = []
    """Processor list."""

    on_failure: list[_ESProcessorWrapper] = []
    """Failure processor list."""


class ESIngestPipelineParser:
    """ElasticSearch ingest pipeline converter for mustash.

    :param name: Optional name with which the parser wants to be represented.
    :param processors: Processors supported by the pipeline.
    """

    __slots__ = (
        "_name",
        "_processors",
        "_processors_type_adapter",
        "_type_adapter",
    )

    _name: str | None
    """Name by which the processor wants to be represented."""

    _processors: dict[str, type[ESProcessor]]
    """Processors taken into account when parsing."""

    _type_adapter: TypeAdapter[_ESPipeline | list[ESProcessor]]
    """Type adapter with which to parse.."""

    _processors_type_adapter: TypeAdapter[list[ESProcessor]]
    """Type adapter with which to serialize processors."""

    def __init__(
        self,
        /,
        *,
        name: str | None = None,
        processors: dict[str, type[ESProcessor]] | None = None,
    ) -> None:
        processors = processors or {}

        # This bit is quite the complicated type stuff, to delegate as much
        # as we can to pydantic's parsing facilities.
        # The steps here are the following:
        #
        # 1. We define "es_processor_models" as the dictionary of names to
        #    overridden models to replace ``list[ESProcessor]`` (base class)
        #    with an indirect reference to ``es_processor_list`` we're going
        #    to define later.
        # 2. We define "es_processor_wrappers" as the sequence of
        #    models wrapping processors into a dictionary where the processor
        #    definition is indexed by the processor name, in order to match
        #    e.g. ``{"my_processor": {...}}``. The processor data will always
        #    be accessible by the key ``value``; see usage of this in
        #    :py:meth:`convert`.
        # 3. We define our "es_processor_list" type as the list of our
        #    processor wrappers.
        # 4. We rebuild the models defined at step 1 to include a concrete
        #    definition of the wrapper list.

        es_processor_models = {
            name: create_model(
                typ.__name__,
                on_failure=(
                    Union["es_processor_list", None],
                    Field(default=None),
                ),
                __base__=typ,
            )
            for name, typ in processors.items()
        }

        es_processor_wrappers = tuple(
            create_model(
                f"{typ.__name__}Wrapper",
                value=(typ, Field(alias=name)),
                __base__=_ESProcessorWrapper,
            )
            for name, typ in es_processor_models.items()
        )

        es_processor_list = TypeAliasType(
            "es_processor_list",
            list[Union[es_processor_wrappers]],  # type: ignore
        )

        for typ in es_processor_models.values():
            typ.model_rebuild()

        # We can now define our pipeline type, and actually define the
        # type adapter.
        class ESPipeline(_ESPipeline):
            """ElasticSearch pipeline, as an object to be parsed."""

            processors: es_processor_list = []
            """Processor list."""

            on_failure: es_processor_list = []
            """Failure processor list."""

        self._name = name
        self._processors = processors.copy()
        self._processors_type_adapter = TypeAdapter(es_processor_list)
        self._type_adapter = TypeAdapter(Union[ESPipeline, es_processor_list])

    def __repr__(self, /) -> str:
        return self._name or object.__repr__(self)

    def copy(
        self,
        /,
        *,
        with_processors: dict[str, ESProcessor] | None = None,
        without_processors: Iterable[str] | None = None,
    ) -> ESIngestPipelineParser:
        """Copy the parser.

        :param with_processors: Processors to add in the new parser.
            If the key exists in the current parser, the processor will be
            replaced automatically in the new parser.
        :param without_processors: Processors to remove from the
            current parser.
        :return: New parser with the modified processors.
        """
        processors = self._processors.copy()

        if without_processors is not None:
            for key in without_processors:
                processors.pop(key, None)

        if with_processors is not None:
            for key, value in with_processors.items():
                processors[key] = value

        return self.__class__(processors=processors)

    def validate_processors(self, raw: Any, /) -> list[dict]:
        """Validate the provided pipeline's processors.

        :param raw: Pipeline or processor list dictionary, or
            JSON-encoded version of the same.
        :return: Validated object, as Python.
        """
        if isinstance(raw, str):
            obj = self._type_adapter.validate_json(raw)
        else:
            obj = self._type_adapter.validate_python(raw)

        if isinstance(obj, list):
            processors = obj
        else:
            processors = obj.processors

        return self._processors_type_adapter.dump_python(
            processors,
            mode="json",
            by_alias=True,
            exclude_defaults=True,
        )

    def validate_failure_processors(self, raw: Any, /) -> list[dict]:
        """Validate the provided pipeline's failure processors.

        :param raw: Pipeline or processor list dictionary, or
            JSON-encoded version of the same.
        :return: Validated object, as Python.
        """
        if isinstance(raw, str):
            obj = self._type_adapter.validate_json(raw)
        else:
            obj = self._type_adapter.validate_python(raw)

        if isinstance(obj, list):
            processors = obj
        else:
            processors = obj.on_failure

        return self._processors_type_adapter.dump_python(
            processors,
            mode="json",
            by_alias=True,
            exclude_defaults=True,
        )

    def parse(self, raw: Any, /) -> Pipeline:
        """Convert a raw list of processors into a pipeline.

        :param raw: Pipeline or processor list dictionary, or
            JSON-encoded version of the same.
        :return: Decoded processor.
        """
        if isinstance(raw, str):
            obj = self._type_adapter.validate_json(raw)
        else:
            obj = self._type_adapter.validate_python(raw)

        if isinstance(obj, list):
            name: str | None = None
            processors = obj
        else:
            name = obj.name
            processors = obj.processors

        # TODO: Read on_failure processors.
        return Pipeline(
            name=name,
            processors=[proc.value.convert() for proc in processors],
        )


DEFAULT_INGEST_PIPELINE_PARSER = ESIngestPipelineParser(
    name="DEFAULT_INGEST_PIPELINE_PARSER",
    processors={
        "append": ESAppendProcessor,
        "bytes": ESBytesProcessor,
        "community_id": ESCommunityIDProcessor,
        "convert": ESConvertProcessor,
        "csv": ESCSVProcessor,
        "date": ESDateProcessor,
        "date_index_name": ESDateIndexNameProcessor,
        "dissect": ESDissectProcessor,
        "dot_expander": ESDotExpander,
        "drop": ESDropProcessor,
        "fail": ESFailProcessor,
        "fingerprint": ESFingerprintProcessor,
        "geoip": ESGeoIPProcessor,
        "grok": ESGrokProcessor,
        "gsub": ESGsubProcessor,
        "html_strip": ESHTMLStripProcessor,
        "join": ESJoinProcessor,
        "json": ESJSONProcessor,
        "kv": ESKVProcessor,
        "lowercase": ESLowercaseProcessor,
        "network_direction": ESNetworkDirectionProcessor,
        "redact": ESRedactProcessor,
        "registered_domain": ESRegisteredDomainProcessor,
        "remove": ESRemoveProcessor,
        "rename": ESRenameProcessor,
        "reroute": ESRerouteProcessor,
        "script": ESScriptProcessor,
        "set": ESSetProcessor,
        "set_security_user": ESSetSecurityUserProcessor,
        "sort": ESSortProcessor,
        "split": ESSplitProcessor,
        "trim": ESTrimProcessor,
        "uppercase": ESUppercaseProcessor,
        "urldecode": ESURLDecodeProcessor,
        "uri_parts": ESURIPartsProcessor,
        "user_agent": ESUserAgentProcessor,
    },
)
"""Default ElasticSearch ingest pipeline parser instance.

This instance defines all of the default processors available in all contexts,
including on ElasticSearch and in Logstash's ``elastic_integration`` filter.
"""


# ---
# Common functions.
# ---


def parse_ingest_pipeline(
    raw: Any,
    /,
    *,
    parser: ESIngestPipelineParser = DEFAULT_INGEST_PIPELINE_PARSER,
) -> Pipeline:
    """Parse an ElasticSearch ingest pipeline's processors.

    :param raw: Raw ingest pipeline to parse the processors from, either
        provided as a dictionary or a raw JSON-encoded string.
    :param parser: Parser to use to read the pipeline's processors.
    :return: Parsed ElasticSearch processors.
    """
    return parser.parse(raw)


def validate_ingest_pipeline_processors(
    raw: Any,
    /,
    *,
    parser: ESIngestPipelineParser = DEFAULT_INGEST_PIPELINE_PARSER,
) -> list[dict]:
    """Validate an ElasticSearch ingest pipeline's processors.

    :param raw: Raw ingest pipeline to validate the processors from, either
        provided as a dictionary or a raw JSON-encoded string.
    :param parser: Parser to use to validate the pipeline's processors.
    :return: Validated ElasticSearch processors.
    """
    return parser.validate_processors(raw)


def validate_ingest_pipeline_failure_processors(
    raw: Any,
    /,
    *,
    parser: ESIngestPipelineParser = DEFAULT_INGEST_PIPELINE_PARSER,
) -> list[dict]:
    """Validate an ElasticSearch ingest pipeline's failure processors.

    :param raw: Raw ingest pipeline to validate the failure processors from,
        either provided as a dictionary or a raw JSON-encoded string.
    :param parser: Parser to use to validate the pipeline's failure processors.
    :return: Validated ElasticSearch failure processors.
    """
    return parser.validate_failure_processors(raw)


def render_as_ingest_pipeline(pipeline: Pipeline, /) -> list:
    """Render a list of processors as an ElasticSearch ingest pipeline.

    :param pipeline: Pipeline to render as an ElasticSearch ingest pipeline.
    :return: Rendered pipeline.
    :raises ValueError: The pipeline is not renderable as an ElasticSearch
        ingest pipeline.
    """
    raise NotImplementedError()  # TODO
