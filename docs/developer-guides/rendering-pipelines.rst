Rendering pipelines
===================

In order to use a pipeline, you can either execute it in Python for simulating
how a document can be processed, or export it to another format for other
software to execute the pipeline.

Install a pipeline on an ElasticSearch instance, as an ingest pipeline
----------------------------------------------------------------------

.. todo:: This feature is not supported by Mustash as of today.

Render a pipeline as an ElasticSearch ingest pipeline
-----------------------------------------------------

.. py:currentmodule:: mustash.es

.. todo:: This section is provisional, and the feature is not implemented yet.

In order to render a pipeline as an ElasticSearch ingest pipeline, you can
use :py:func:`render_as_ingest_pipeline`.

Render a pipeline as a Logstash filter configuration
----------------------------------------------------

.. py:currentmodule:: mustash.logstash

.. todo:: This section is provisional, and the feature is not implemented yet.

In order to render a pipeline as a Logstash filter configuration, you can
use :py:func:`render_as_filter`.
