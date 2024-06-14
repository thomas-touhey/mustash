Defining or reading pipelines
=============================

In order to obtain a pipeline, you can either define one manually, or read it
from a source in various formats. This guide explores all options built in
Mustash.

Gather an ingest pipeline from an ElasticSearch instance
--------------------------------------------------------

.. todo:: This feature is not supported by Mustash as of today.

Read a JSON document or blob representing an ingest pipeline
------------------------------------------------------------

.. py:currentmodule:: mustash.es

In order to read a pipeline from a raw ElasticSearch pipeline or list of
ingest processors, you can use :py:func:`parse_ingest_pipeline`.
For example, here's a snippet that reads the pipeline from the raw pipeline
definition:

.. literalinclude:: read_es_pipeline.py

Read a pipeline from a Logstash configuration
---------------------------------------------

.. py:currentmodule:: mustash.logstash

.. todo:: This section is provisional, and the feature is not implemented yet.

In order to read a pipeline from the filter plugin settings in a Logstash
configuration, you can use :py:func:`parse_from_config`.
For example, here's a snippet that reads the pipeline from a raw Logstash
configuration:

.. literalinclude:: read_logstash_filter.py

Define a pipeline manually
--------------------------

.. py:currentmodule:: mustash.core

In order to define a pipeline manually, you must use :py:class:`Pipeline`
and subclasses of :py:class:`Processor` or :py:class:`FieldProcessor`.
For example, here's a snippet that defines a pipeline that parses a JSON field:

.. literalinclude:: define_pipeline.py
