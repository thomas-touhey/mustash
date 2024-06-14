Concepts
========

.. py:currentmodule:: mustash.core

Mustash is centered around pipelines that transform a document.

The following sections explore these concepts more in depth.
Note that all of these elements are defined in :py:mod:`mustash.core`.

.. _concept-documents:

Documents
---------

Documents are a single unit of data on which processors can apply.
They are arrays associating keys with document elements, which in turn
can be associative arrays, or other types.

Documents are represented in Mustash using :py:class:`Document`.
Document elements, on the other hand, are represented using
:py:class:`Element`.

.. _concept-pipelines:

Pipelines
---------

Pipelines are an algorithm through which a document may get transformed.
They are constituted of a series of processors, that each define a step of
the transformation.

Each processor may have a condition which, if found falsy, leads to the
processor not being applied to the concerned document.

Each processor, when applied to the document, may raise a failure.
A processor instance can be configured to ignore failures, or execute another
series of processors in such a case.

Pipelines are closely related to their counterparts in other platforms, such
as `ElasticSearch ingest pipelines`_, `Logstash filters`_ or
`Splunk ingest pipelines`_.

They are represented in Mustash using :py:class:`Pipeline`, and are composed
of a series of processors represented using :py:class:`Processor`, which
may bear a condition represented using :py:class:`Condition`.

.. _concept-field-paths:

Field paths
-----------

Field paths are textual representations of the location of an element within
a document.

They are represented in Mustash using :py:class:`FieldPath`.

.. _ElasticSearch ingest pipelines:
    https://www.elastic.co/guide/en/elasticsearch/reference/current/ingest.html
.. _Logstash filters:
    https://www.elastic.co/guide/en/logstash/current/filter-plugins.html
.. _Splunk ingest pipelines:
    https://docs.splunk.com/Documentation/SplunkCloud/9.2.2403/
    IngestProcessor/CreatePipeline
