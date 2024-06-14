Tweaking the ElasticSearch pipeline parser
==========================================

.. py:currentmodule:: mustash.es

Your ElasticSearch ingest pipeline execution context may have more, or less,
processors available, or you could have written your own ingest processors
running on the target ElasticSearch instance; see `Writing Your Own Ingest
Processor For ElasticSearch`_ for more information.

If this is your case, this guide is for you!

Making your own parser instance
-------------------------------

In any case, you must make your own parser instance with your custom list of
processors. For this, two options are available:

* You can derive the default ElasticSearch instance, add your custom processors
  and remove processors you don't want available, by using
  :py:meth:`ESIngestPipelineParser.copy`. For example:

  .. code-block:: python

      from mustash.es import DEFAULT_INGEST_PIPELINE_PARSER

      my_parser = DEFAULT_INGEST_PIPELINE_PARSER.copy(
          # `with_processors` can be set with the processors you want to add
          # or replace. This parameter is optional.
          with_processors={"example": ESExampleProcessor, ...},

          # `without_processors` can be set with a sequence of names
          # representing the processors you want to remove compared to the
          # default parser. This parameter is optional.
          without_processors=["pipeline", ...],
      )

* You can start from scratch by defining your own parser instance,
  using :py:class:`ESIngestPipelineParser` directly, and add the processors
  you want. For example:

  .. code-block:: python

      from mustash.es import ESIngestPipelineParser

      my_parser = ESIngestPipelineParser(processors={
          "example": ESExampleProcessor,
          ...
      })

You can then use this parser with both the validation and parsing functions,
using the ``parser`` keyword parameter:

.. code-block:: python

    parse_ingest_pipeline(..., parser=my_parser)
    validate_ingest_pipeline(..., parser=my_parser)

Creating a custom ElasticSearch processor
-----------------------------------------

.. note::

    ElasticSearch processors in Mustash are only a unit of representation.
    They do not actually define any transformation, as they are either
    validated immediately, or converted to Mustash processors for rendering
    and/or execution.

You can make an ElasticSearch processor by making a class inheriting from
:py:class:`ESProcessor`, which defines the common properties for all
ElasticSearch processors.

If you want to allow converting the processor to a Mustash processor, you
can override :py:meth:`ESProcessor.convert` and call
:py:meth:`ESProcessor.build` with the processor class and keyword
parameters.

For example, an example ElasticSearch processor could be defined by this
snippet:

.. code-block:: python

    from mustash.core import Processor
    from mustash.es import ESProcessor

    class ESExampleProcessor(ESProcessor):
        hello: str

        def convert(self, /) -> Processor:
            return self.build(
                ExampleProcessor,
                hello=self.hello,
            )

.. _Writing Your Own Ingest Processor For ElasticSearch:
    https://www.elastic.co/fr/blog/
    writing-your-own-ingest-processor-for-elasticsearch
