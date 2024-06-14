from __future__ import annotations

from mustash.core import Pipeline
from mustash.processors import JsonProcessor


pipeline = Pipeline(processors=[JsonProcessor(field="raw")])
