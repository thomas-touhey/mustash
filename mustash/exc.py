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
"""Error definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .core import Document, Processor  # type: ignore[attr-defined]


class MustashException(Exception):
    """An error has occurred in a Mustash function."""

    __slots__ = ()

    def __init__(self, message: str, /) -> None:
        super().__init__(message)


class DropException(MustashException):
    """A document should be dropped."""

    __slots__ = ()

    def __init__(self, /) -> None:
        super().__init__("Document should be dropped")


class PipelineFailureException(MustashException):
    """A pipeline has failed on a provided document.

    This exception may be raised by :py:meth:`Pipeline.apply`, to provide
    more context on the execution.
    """

    __slots__ = ("document", "exception", "processor")

    document: Document
    """State of the document at exception time."""

    exception: Exception
    """Exception that has occurred on the pipeline."""

    processor: Processor
    """Processor on which"""

    def __init__(
        self,
        /,
        *,
        document: Document,
        processor: Processor,
        exception: Exception,
    ) -> None:
        super().__init__(f"Pipeline has failed: {exception}")
        self.document = document
        self.processor = processor
        self.exception = exception
