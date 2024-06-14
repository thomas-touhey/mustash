.. _guide-creating-processors:

Creating processors
===================

.. py:currentmodule:: mustash.core

In order to create Mustash processors, you need to create a new class
inheriting from either :py:class:`Processor`, :py:class:`FieldProcessor`,
or another existing processor.

In this guide, we will walk through steps to create sample processors
exploiting each case.

.. _guide-creating-field-processors:

Creating field processors
-------------------------

If the processor you're trying to create takes a value from one field, applies
some logic to it, and then updates the document with the result either on
the same field, or to a separate field, it is recommended to inherit from
:py:class:`FieldProcessor` directly:

* It defines all of the settings you may want for such a use case, including:

  - :py:attr:`FieldProcessor.field`: the field from which to read the value;
  - :py:attr:`FieldProcessor.ignore_missing`: whether to just not apply the
    processor if the source field is not present in the document;
  - :py:attr:`FieldProcessor.target_field`: the target field to which the
    result should be applied, if the source field shouldn't be updated
    in-place;
  - :py:attr:`FieldProcessor.remove_if_successful`: whether to remove the
    source field if the target field is different and the processor has been
    applied successfully.
* It is able to validate the type of the value present in the source field,
  with a simple syntax tweak;
* It implements :py:meth:`Processor.apply`, and defines a more appropriate
  :py:meth:`FieldProcessor.process` method you can override.

Let's assume we want to create a processor for adding ``, haha`` to a field
assumed to contain a string. There are two options on the inheritance:

1. We can inherit from ``FieldProcessor`` directly, and implement the type
   checking on the source field ourselves in :py:meth:`FieldProcessor.process`;
2. We can inherit from ``FieldProcessor[str]``, and let the parent class handle
   type checking.

For ease of implementation, we prefer to use option 2. We can now define our
class with the appropriate method:

.. code-block:: python

    from mustash.core import FieldProcessor


    class HahaProcessor(FieldProcessor[str]):
        """Processor for adding ``", haha"`` to a field."""

        async def process(self, value: str, /) -> str:
            return value + ", haha"

In order to test our processor, we can create our sample document and check
the result. Here's a full snippet on how to do so:

.. literalinclude:: haha_processor.py

The script above prints the following:

.. code-block:: text

    {'my_field': 'hello, world, haha'}

If we don't systematically want to add ``, haha`` as a suffix, but also others,
we can add an additional option on the processor called ``suffix``.
A complete snippet for doing precisely this and testing it is the following:

.. literalinclude:: suffix_processor.py

This snippet prints the following:

.. code-block:: text

    {'my_field': 'hello, world, wow'}

.. _guide-creating-more-complex-processors:

Creating more complex processors
--------------------------------

If your processor has a logic more complex than a simple field processor,
especially if it has multiple inputs and/or multiple outputs, you will need
to inherit from :py:class:`Processor`, define your settings and override
:py:meth:`Processor.apply`.

Let's assume we want to create a processor that computes the sum of two
fields and places the result in a third one. We will need to define options
to provide the path to all three fields, using :py:class:`FieldPath`:

.. code-block:: python

    from mustash.core import FieldPath, Processor


    class SumProcessor(Processor):
        """Processor for computing the sum of two fields into a third one."""

        first_field: FieldPath
        """Path to the first field."""

        second_field: FieldPath
        """Path to the second field."""

        target_field: FieldPath
        """Path to the target field, to set with the sum."""

If you want to ensure all fields are different, you can use a
`model validator`_:

.. code-block:: python

    from typing import Self

    from mustash.core import FieldPath, Processor
    from pydantic import model_validator


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

.. note::

    When using model validators with built-in processors to Mustash,
    contributors usually prefix them with an underscore so that they won't
    appear in the Sphinx documentation.

You must then override :py:meth:`Processor.apply` to make your validations
and operations on a provided document:

.. code-block:: python

    from mustash.core import Document


    class SumProcessor:
        ...

        async def apply(self, document: Document, /) -> None:
            first = self.first_field.get(document, cls=int)
            second = self.second_field.get(document, cls=int)
            self.target_field.set(document, first + second)

.. note::

    :py:meth:`Processor.apply` should be written in a naive manner, as
    exceptions are handled by either :py:meth:`Processor.__call__`, or
    the function above.

You can now test your processor using a sample document! Here's a full
snippet you can run:

.. literalinclude:: sum_processor.py

This snippet prints the following:

.. code-block:: text

    {'farm': 'Old MacDonalds', 'animals': {'chickens': 4, 'cows': 7, 'total': 11}}

.. _model validator:
    https://docs.pydantic.dev/latest/concepts/validators/#model-validators
