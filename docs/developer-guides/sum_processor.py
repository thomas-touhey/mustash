from __future__ import annotations

import asyncio
from typing import Self

from pydantic import model_validator

from mustash.core import Document, FieldPath, Processor


class SumProcessor(Processor):
    """Processor for computing the sum of two fields into a third one."""

    first_field: FieldPath
    """Path to the first field."""

    second_field: FieldPath
    """Path to the second field."""

    target_field: FieldPath
    """Path to the target field, to set with the sum."""

    @model_validator(mode="after")
    def _validate(self, /) -> Self:
        if (
            self.first_field == self.second_field
            or self.first_field == self.target_field
            or self.second_field == self.target_field
        ):
            raise ValueError("All three fields must be different.")

        return self

    async def apply(self, document: Document, /) -> None:
        first = self.first_field.get(document, cls=int)
        second = self.second_field.get(document, cls=int)
        self.target_field.set(document, first + second)


d: Document = {"farm": "Old MacDonalds", "animals": {"chickens": 4, "cows": 7}}
processor = SumProcessor(
    first_field="animals.chickens",
    second_field="animals.cows",
    target_field="animals.total",
)
asyncio.run(processor.apply(d))
print(d)
