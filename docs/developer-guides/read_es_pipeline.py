from __future__ import annotations

from mustash.es import parse_ingest_pipeline


raw = {"name": "my-pipeline", "processors": [{"json": {"field": "raw"}}]}
pipeline = parse_ingest_pipeline(raw)
