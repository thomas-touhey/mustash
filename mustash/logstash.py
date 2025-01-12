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
"""Logstash ingest pipeline conversion utilities."""

from __future__ import annotations

from .core import Pipeline


def parse_from_config(raw: str, /) -> Pipeline:
    """Parse the pipeline from a logstash pipeline.

    :param raw: Raw logstash configuration to read the processors from.
    :return: Pipeline.
    """
    raise NotImplementedError()  # TODO


def render_as_filter(pipeline: Pipeline, /) -> list:
    """Render a list of processors as a Logstash filter body.

    :param processors: Pipeline to render.
    :return: Rendered pipeline.
    :raises ValueError: The pipeline is not renderable as a Logstash pipeline.
    """
    raise NotImplementedError()  # TODO
