from __future__ import annotations

import asyncio

from mustash.core import Document, FieldProcessor


class HahaProcessor(FieldProcessor[str]):
    """Processor for adding ``", haha"`` to a field."""

    async def process(self, value: str, /) -> str:
        return value + ", haha"


d: Document = {"my_field": "hello, world"}
processor = HahaProcessor(field="my_field")
asyncio.run(processor.apply(d))
print(d)
