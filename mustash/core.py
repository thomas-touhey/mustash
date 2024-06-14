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
"""Core definitions for Mustash."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Iterable
from ipaddress import IPv4Address, IPv6Address
import re
from typing import Annotated, Any, Generic, TypeVar, Union, Self

from annotated_types import Ge, Len
from pydantic import (
    BaseModel,
    ConfigDict,
    GetCoreSchemaHandler,
    PrivateAttr,
    StringConstraints,
    TypeAdapter,
    model_validator,
)
from pydantic_core.core_schema import (
    CoreSchema,
    ValidationInfo,
    is_instance_schema,
    json_or_python_schema,
    str_schema,
    to_string_ser_schema,
    with_info_after_validator_function,
)
from typing_extensions import TypeAliasType, override

from .exc import DropException, PipelineFailureException
from .utils import NO_VALUE, NoValueType, get_generic_arg


__all__ = [
    "Document",
    "Element",
    "FieldPath",
    "Condition",
    "PainlessCondition",
    "Pipeline",
    "Processor",
    "FieldProcessor",
]


_ClsType = TypeVar("_ClsType", bound=Any)


Element = TypeAliasType(  # type: ignore
    "Element",
    Union[
        dict[str, "Element"],  # type: ignore
        list["Element"],  # type: ignore
        IPv4Address,
        IPv6Address,
        str,
        int,
        float,
        bool,
        None,
    ],
)
"""Document element.

This is a recursive type defining a document element that can represent a JSON
value with extra types supported by backends such as ElasticSearch, including:

* Dictionaries associating string keys with document elements;
* Lists of document elements;
* Strings;
* Numbers (integers, floating-point, booleans);
* None.
"""

Document = TypeAliasType("Document", dict[str, Element])  # type: ignore
"""Type representing a document to process."""

FieldType = TypeVar("FieldType", bound=Element)
FieldPathType = TypeVar("FieldPathType", bound="FieldPath")

FieldPathPart = Annotated[str, StringConstraints(pattern=r"^[^\.]+$")]
FieldPathParts = Annotated[tuple[FieldPathPart, ...], Len(min_length=1)]

# Type adapters.
field_path_parts_type_adapter = TypeAdapter(FieldPathParts)
index_type_adapter = TypeAdapter(Annotated[int, Ge(0)])

_FIELD_PATH_PART_PATTERN = re.compile(r"([^\.]+)(\.)?")
"""Pattern for a given path part.

See :py:func:`_get_parts_from_string` for usage of this pattern.
"""


def _get_parts_from_string(raw: str, /) -> Sequence[str]:
    """Get field path parts from a string.

    :param raw: Raw string from which to get field path parts.
    :return: Field path parts.
    """
    left = raw
    parts: list[str] = []

    while left:
        match = _FIELD_PATH_PART_PATTERN.match(left)
        if match is None:
            raise ValueError(f"Invalid field path: {raw}")

        left = left[match.end() :]
        if bool(left) != (match[2] == "."):
            # Either there is no string left and the path ends with a dot
            # separator, or there is string left but the path does not
            # end with a dot separator; in either case, the field
            # is not valid.
            raise ValueError(f"Invalid field path: {raw}")

        parts.append(match[1])

    return parts


class FieldPath:
    """Object representing the path to a field in a JSON document.

    This object can be used in a similar fashion to :py:class:`pathlib.Path`.
    For example, in order to create a field path out of several components,
    the following can be used:

    .. doctest::

        >>> FieldPath("hello.world")
        FieldPath('hello.world')
        >>> FieldPath("hello") / "world"
        FieldPath('hello.world')
        >>> FieldPath(["hello", "world"])
        FieldPath('hello.world')

    Field paths can also be used in Pydantic models:

    .. doctest::

        >>> from pydantic import BaseModel
        >>> class MyModel(BaseModel):
        ...     field: FieldPath
        ...
        >>> MyModel(field="hello.world")
        MyModel(field=FieldPath('hello.world'))
    """

    __slots__ = ("_parts",)

    _parts: FieldPathParts
    """Parts of the path."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls: type[FieldPathType],
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        """Get the pydantic core schema.

        This allows the field path to be handled within pydantic classes,
        and imported/exported in JSON schemas as strings.

        :param source: Source type.
        """
        return with_info_after_validator_function(
            cls._validate,
            json_or_python_schema(
                json_schema=str_schema(),
                python_schema=is_instance_schema((FieldPath, str)),
                serialization=to_string_ser_schema(),
            ),
        )

    @classmethod
    def _validate(
        cls: type[FieldPathType],
        value: str | FieldPathType,
        info: ValidationInfo,
        /,
    ) -> FieldPathType:
        """Validate a pydantic value.

        :param value: Value to validate.
        :param info: Validation information, if required.
        :return: Obtained field path.
        """
        if isinstance(value, str):
            return cls(_get_parts_from_string(value))
        if isinstance(value, cls):
            return cls(value.parts)
        raise TypeError()  # pragma: no cover

    @property
    def parent(self: FieldPathType, /) -> FieldPathType:
        """Get the field path parent.

        :return: Parent.
        """
        if len(self.parts) == 1:
            return self

        return self.__class__(self.parts[:-1])

    @property
    def parts(self, /) -> tuple[FieldPathPart, ...]:
        """Get the parts of the current path.

        :return: Parts.
        """
        return self._parts

    def __init__(self, path: FieldPath | str | Iterable[str], /) -> None:
        if isinstance(path, FieldPath):
            raw_parts: Iterable[str] = path.parts
        elif isinstance(path, str):
            raw_parts = tuple(_get_parts_from_string(path))
        else:
            raw_parts = path

        self._parts = field_path_parts_type_adapter.validate_python(raw_parts)

    def __eq__(self, other: Any, /) -> bool:
        try:
            other = FieldPath(other)
        except (ValueError, TypeError):
            return False

        return self.parts == other.parts

    def __contains__(self, other: Any, /) -> bool:
        try:
            other = FieldPath(other)
        except (ValueError, TypeError):
            return False

        # NOTE: We consider that a path contains itself, i.e. if a == b,
        # then a in b.
        return other._parts[: len(self._parts)] == self._parts

    def __str__(self, /) -> str:
        return ".".join(self.parts)

    def __repr__(self, /) -> str:
        return f"{self.__class__.__name__}({'.'.join(self.parts)!r})"

    def __truediv__(self: FieldPathType, other: Any, /) -> FieldPathType:
        if isinstance(other, FieldPath):
            return self.__class__([*self.parts, *other.parts])
        if isinstance(other, str):
            return self.__class__(
                [*self.parts, *_get_parts_from_string(other)],
            )

        raise TypeError()  # pragma: no cover

    def __hash__(self, /):
        return hash(".".join(self.parts))

    @override
    def get(  # noqa: D102
        self,
        element: Element,
        /,
        *,
        cls: None = None,
        default: Any = NO_VALUE,
    ) -> Any:
        ...

    @override  # type: ignore[no-redef]
    def get(  # noqa: D102, F811
        self,
        element: Element,
        /,
        *,
        cls: type[_ClsType],
        default: _ClsType | NoValueType = NO_VALUE,
    ) -> _ClsType:
        ...

    def get(  # type: ignore[no-redef]  # noqa: F811
        self,
        element: Element,
        /,
        *,
        cls: type | None = None,  # noqa: ANN001
        default: Any = NO_VALUE,  # noqa: ANN001
    ) -> Any:  # noqa: ANN201
        """Get the value in a document element using the path.

        An example usage with a given element is the following:

        .. doctest::

            >>> path = FieldPath("hello.world")
            >>> document = {"hello": {"world": [1, 2, 3]}}
            >>> path.get(document)
            [1, 2, 3]

        You can also set a default value, in case any intermediate element does
        not exist:

        .. doctest::

            >>> path = FieldPath("hello.world")
            >>> document = {"hello": {}}
            >>> path.get(document, default="my_default")
            'my_default'

        If you expect a specific type, such as an integer, you can also do
        set the ``cls`` parameter to the expected type, and this method will
        attempt at using pydantic to convert the value:

        .. doctest::

            >>> path = FieldPath("hello.world")
            >>> document = {"hello": {"world": "42"}}
            >>> path.get(document, cls=int)
            42

        You can also add validators to the provided class:

        .. doctest::

            >>> from annotated_types import Le
            >>> from typing import Annotated
            >>> path = FieldPath("hello")
            >>> document = {"hello": "101"}
            >>> path.get(document, cls=Annotated[int, Le(100)])
            Traceback (most recent call last):
            ...
            pydantic_core._pydantic_core.ValidationError: ...
              Input should be less than or equal to 100 [...]
                ...

        :param document: Element from which to get the value.
        :param cls: Optional type to validate the obtained value with,
            using pydantic.
        :param default: Default value to get.
        :return: Found value, or default value if one has been set.
        :raises KeyError: The key was not provided, and the value did not
            exist.
        """
        for i, part in enumerate(self._parts):
            if isinstance(element, dict):
                try:
                    element = element[part]
                except KeyError as exc:
                    if not isinstance(default, NoValueType):
                        return default

                    raise KeyError(".".join(self._parts[: i + 1])) from exc
            elif isinstance(element, list):
                try:
                    index = index_type_adapter.validate_python(part)
                except ValueError as exc:
                    if not isinstance(default, NoValueType):
                        return default

                    raise KeyError(".".join(self._parts[: i + 1])) from exc

                try:
                    element = element[index]
                except IndexError as exc:
                    if not isinstance(default, NoValueType):
                        return default

                    raise KeyError(".".join(self._parts[: i + 1])) from exc
            elif not isinstance(default, NoValueType):
                return default
            else:
                raise KeyError(".".join(self._parts[: i + 1]))

        if cls is not None:
            element = TypeAdapter(cls).validate_python(element)

        return element

    def set(
        self,
        element: Element,
        value: Element,
        /,
        *,
        override: bool = True,
    ) -> None:
        """Set the value in a document element using the path.

        An example usage with a given element is the following:

        .. doctest::

            >>> path = FieldPath("hello.world")
            >>> document = {}
            >>> path.set(document, 42)
            >>> document
            {'hello': {'world': 42}}

        :param element: Element at which to set the value.
        :param value: Value to set at the path.
        :param override: Whether to override the field if exists, or not.
        :raises KeyError: A non-indexable object was found in the way.
        """
        for i, part in enumerate(self._parts[:-1]):
            if isinstance(element, dict):
                element = element.setdefault(part, {})
            elif isinstance(element, list):
                try:
                    index = index_type_adapter.validate_python(part)
                except ValueError as exc:
                    raise KeyError(".".join(self._parts[: i + 1])) from exc

                if index >= len(element):
                    raise KeyError(".".join(self._parts[: i + 1]))

                element = element[index]
            else:
                raise KeyError(".".join(self._parts[: i + 1]))

        part = self._parts[-1]
        if isinstance(element, dict):
            if part not in element or override:
                element[part] = value
        elif isinstance(element, list):
            try:
                index = index_type_adapter.validate_python(part)
            except ValueError as exc:
                raise KeyError(".".join(self._parts)) from exc

            if index >= len(element):
                raise KeyError(".".join(self._parts))

            element[index] = value
        else:
            raise KeyError(".".join(self._parts))

    def delete(self, element: Element, /) -> None:
        """Delete the value in a document element using the path.

        An example usage with a given element is the following:

        .. doctest::

            >>> path = FieldPath("hello.world")
            >>> document = {"hello": {"world": 42}}
            >>> path.delete(document)
            >>> document
            {'hello': {}}

        :param element: Element at which to delete the value.
        :raises KeyError: A non-indexable object was found in the way.
        """
        for i, part in enumerate(self._parts[:-1]):
            if isinstance(element, dict):
                try:
                    element = element[part]
                except KeyError as exc:
                    raise KeyError(".".join(self._parts[: i + 1])) from exc
            elif isinstance(element, list):
                try:
                    index = index_type_adapter.validate_python(part)
                except ValueError as exc:
                    raise KeyError(".".join(self._parts[: i + 1])) from exc

                if index >= len(element):
                    raise KeyError(".".join(self._parts[: i + 1]))

                element = element[index]
            else:
                raise KeyError(".".join(self._parts[: i + 1]))

        part = self._parts[-1]
        if isinstance(element, dict):
            if part not in element:
                raise KeyError(".".join(self._parts))

            del element[part]
        elif isinstance(element, list):
            try:
                index = index_type_adapter.validate_python(part)
            except ValueError as exc:
                raise KeyError(".".join(self._parts)) from exc

            if index >= len(element):
                raise KeyError(".".join(self._parts))

            del element[index]
        else:
            raise KeyError(".".join(self._parts))


class Condition(BaseModel, ABC):
    """Condition to execute one or more processors."""

    model_config = ConfigDict(extra="forbid")
    """Model configuration."""

    @abstractmethod
    def verify(self, document: Document, /) -> bool:
        """Verify whether the condition is true or not.

        :param document: Document on which to verify the condition.
        :return: Whether the condition is verified or not.
        """


class PainlessCondition(Condition):
    """Condition written in Painless.

    See `Painless scripting language`_ for more information.

    .. _Painless scripting language:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/
        modules-scripting-painless.html
    """

    script: Annotated[str, StringConstraints(min_length=1)]
    """Painless script to run."""

    def verify(self, document: Document, /) -> bool:
        """Verify whether the condition is true or not.

        :param document: Document on which to verify the condition.
        :return: Whether the condition is verified or not.
        """
        raise NotImplementedError()  # TODO


class Processor(BaseModel, ABC):
    """Processor, for transforming data.

    For a guide on how to create your own processors based on this class,
    see :ref:`guide-creating-processors`.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    """Model configuration."""

    description: str | None = None
    """Optional description of the processor."""

    tag: str | None = None
    """Identifier for the processor, included in debugging and metrics."""

    condition: Condition | None = None
    """Condition depending on which the processor is executed."""

    ignore_failure: bool = False
    """Whether to ignore failures for the processor."""

    on_failure: list[Processor] | None = None
    """Processors to execute when a failure occurs."""

    @abstractmethod
    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """


class Pipeline(BaseModel):
    """Pipeline, as a set of processors and metadata."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    """Model configuration."""

    name: str | None = None
    """Name of the pipeline."""

    processors: list[Processor]
    """List of processors constituting the pipeline."""

    async def _apply_processors(
        self,
        processors: list[Processor],
        document: Document,
        /,
    ) -> None:
        """Apply a set of processors to the document.

        :param processors: Processors to apply to the document.
        :param document: Document to which the processors will apply.
        """
        for processor in processors:
            if (
                processor.condition is not None
                and not processor.condition.verify(document)
            ):
                continue

            try:
                await processor.apply(document)
            except DropException:
                raise
            except Exception as exc:
                if processor.ignore_failure:
                    pass
                elif processor.on_failure is not None:
                    await self._apply_processors(
                        processor.on_failure,
                        document,
                    )
                else:
                    raise PipelineFailureException(
                        document=document,
                        exception=exc,
                        processor=processor,
                    ) from exc

    async def apply(self, document: Document, /) -> None:
        """Apply the pipeline to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        await self._apply_processors(self.processors, document)


class FieldProcessor(Processor, Generic[FieldType]):  # type: ignore
    """Processor that processes a field, expected to be a given type.

    For a guide on how to create such processors, see
    :ref:`guide-creating-field-processors`.

    This uses the same idea as ElasticSearch's `abstract string processor`_,
    used for a few of their processors.

    .. _Abstract string processor:
        https://github.com/elastic/elasticsearch/blob/main/modules/
        ingest-common/src/main/java/org/elasticsearch/ingest/common/
        AbstractStringProcessor.java#L26
    """

    field: FieldPath
    """Field from which to get the size."""

    target_field: FieldPath | None = None
    """Target field to set with the result."""

    ignore_missing: bool = False
    """Whether not to fail if the field is not present in the document."""

    remove_if_successful: bool = False
    """Whether to remove the source field after processing it."""

    _type_adapter: Annotated[TypeAdapter, PrivateAttr]
    """Type adapter for the generic processor."""

    @model_validator(mode="after")
    def _validate(self, /) -> Self:
        """Validate the model.

        This method defines the type adapter used to validate the contents of
        the source field, and ensures that the target field, if defined, is
        not the same as the source field.
        """
        if self.target_field == self.field:
            self.target_field = None

        generic_type = get_generic_arg(
            FieldProcessor,
            self,
            default=Element,  # type: ignore
        )
        self._type_adapter = TypeAdapter(generic_type)

        return self

    async def apply(self, document: Document, /) -> None:
        """Apply the processor to the document, in-place.

        :param document: Document to which to apply the processor.
        """
        try:
            value = self.field.get(document)
        except KeyError:
            if self.ignore_missing:
                return

            raise

        result = await self.process(self._type_adapter.validate_python(value))
        if self.target_field is not None:
            self.target_field.set(document, result)
        else:
            self.field.set(document, result)

        if self.remove_if_successful and self.target_field is not None:
            self.field.delete(document)

    @abstractmethod
    async def process(self, value: FieldType, /) -> Element:
        """Process the field into the expected type.

        :param value: Value to process.
        :return: Processed value.
        """
