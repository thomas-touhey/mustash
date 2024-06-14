from __future__ import annotations

from mustash.es import validate_ingest_pipeline


raw_pipeline = {
    "name": "hello",
    "processors": [
        {"json": {"field": "message"}},
    ],
}

print(validate_ingest_pipeline(raw_pipeline))
