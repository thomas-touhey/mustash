from __future__ import annotations

import asyncio

from mustash.core import Document, FieldProcessor


class SuffixProcessor(FieldProcessor[str]):
    """Processor for adding a suffix to a field."""

    suffix: str
    """Suffix to add to the field."""

    async def process(self, value: str, /) -> str:
        return value + self.suffix


d: Document = {"my_field": "hello, world"}
processor = SuffixProcessor(field="my_field", suffix=", wow")
asyncio.run(processor.apply(d))
print(d)
