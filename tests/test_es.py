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
"""Unit tests for the ``mustash.es`` module."""

from __future__ import annotations

import pytest

from mustash.es import parse_ingest_pipeline
from mustash.processors import Processor, RemoveProcessor, SetProcessor


@pytest.mark.parametrize(
    "raw,expected",
    (
        (
            [{"set": {"field": "a.b", "value": "hello"}}],
            [SetProcessor(field="a.b", value="hello")],
        ),
        (
            [
                {
                    "remove": {
                        "field": "a",
                        "on_failure": [
                            {"set": {"field": "b", "value": "ohno"}},
                        ],
                    },
                },
            ],
            [
                RemoveProcessor(
                    fields=["a"],
                    on_failure=[SetProcessor(field="b", value="ohno")],
                ),
            ],
        ),
    ),
)
def test_parse(raw: list, expected: list[Processor]) -> None:
    """Test ElasticSearch ingest pipeline parsing."""
    assert parse_ingest_pipeline(raw).processors == expected
