Validating ElasticSearch pipelines
==================================

.. py:currentmodule:: mustash.es

Sometimes you only want to validate ElasticSearch pipelines without converting
them into Mustash processors for later rendering. In order to do this, you
can call the following functions:

* :py:func:`validate_ingest_pipeline_processors` for normal processors,
  optionally present in the ``processors`` attribute;
* :py:func:`validate_ingest_pipeline_failure_processors` for processors run
  if the normal pipeline has failed, optionally present in the ``on_failure``
  attribute.

An example snippet doing this is the following:

.. literalinclude:: validate_es_pipeline.py

The snippet above prints the following:

.. code-block:: text

    [{'json': {'field': 'message'}}]
