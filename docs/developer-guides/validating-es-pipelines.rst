Validating ElasticSearch pipelines
==================================

.. py:currentmodule:: mustash.es

Sometimes you only want to validate ElasticSearch pipelines without converting
them into Mustash processors for later rendering. In order to do this, you
can call :py:func:`validate_ingest_pipeline`.

An example snippet doing precisely this is the following:

.. literalinclude:: validate_es_pipeline.py

The snippet above prints the following:

.. code-block:: text

    [{'json': {'field': 'message'}}]
