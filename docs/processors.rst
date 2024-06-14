Processor and conversion reference
==================================

.. py:currentmodule:: mustash.processors

One of the main features of Mustash is conversion between pipeline
representations, for execution in different contexts. A basic tool for
converting ingest pipelines from ElasticSearch to Logstash is implemented with
``bin/ingest-convert.sh``, a tool documented in `Converting Ingest Node
Pipelines`_ (see `Ingest converter source`_ for more information).
Mustash builds upon that concept.

The available processors are the following:

.. list-table::
    :header-rows: 1

    * - Mustash processor
      - ElasticSearch ingest pipeline processor
      - Logstash filter option
    * - :py:class:`AppendProcessor`
      - `Append processor (ElasticSearch)`_
      -
    * - :py:class:`BytesProcessor`
      - `Bytes processor (ElasticSearch)`_
      - `bytes filter (Logstash)`_
    * - :py:class:`CommunityIDProcessor`
      - `Community ID processor (ElasticSearch)`_
      -
    * - :py:class:`BooleanProcessor`, :py:class:`FloatingPointProcessor`,
        :py:class:`IntegerProcessor`, :py:class:`StringProcessor`
      - `Convert processor (ElasticSearch)`_
      - `convert mutation (Logstash)`_
    * - :py:class:`CSVProcessor`
      - `CSV processor (ElasticSearch)`_
      - `csv filter (Logstash)`_
    * - :py:class:`DateProcessor`
      - `Date processor (ElasticSearch)`_
      - `date filter (Logstash)`_
    * -
      - `Date index name processor (ElasticSearch)`_
      -
    * -
      - `Dissect processor (ElasticSearch)`_
      - `dissect filter (Logstash)`_
    * -
      - `Dot expander processor (ElasticSearch)`_
      -
    * -
      - `Drop processor (ElasticSearch)`_
      - `drop filter (Logstash)`_
    * -
      - `Fail processor (ElasticSearch)`_
      -
    * -
      - `Fingerprint processor (ElasticSearch)`_
      - `fingerprint filter (Logstash)`_
    * -
      - `GeoIP processor (ElasticSearch)`_
      - `geoip filter (Logstash)`_
    * -
      - `Grok processor (ElasticSearch)`_
      - `grok filter (Logstash)`_
    * -
      - `Gsub processor (ElasticSearch)`_
      - `gsub mutation (Logstash)`_
    * -
      - `HTML strip processor (ElasticSearch)`_
      -
    * -
      - `Join processor (ElasticSearch)`_
      -
    * - :py:class:`JsonProcessor`
      - `JSON processor (ElasticSearch)`_
      - `json filter (Logstash)`_
    * -
      - `KV processor (ElasticSearch)`_
      -
    * - :py:class:`LowercaseProcessor`
      - `Lowercase processor (ElasticSearch)`_
      - `lowercase mutation (Logstash)`_
    * -
      - `Network direction processor (ElasticSearch)`_
      -
    * -
      - `Redact processor (ElasticSearch)`_
      -
    * -
      - `Registered domain processor (ElasticSearch)`_
      -
    * - :py:class:`KeepProcessor`, :py:class:`RemoveProcessor`
      - `Remove processor (ElasticSearch)`_
      - `prune filter (Logstash)`_
    * -
      - `Rename processor (ElasticSearch)`_
      - `rename mutation (Logstash)`_
    * -
      - `Reroute processor (ElasticSearch)`_
      -
    * -
      - `Script processor (ElasticSearch)`_
      -
    * - :py:class:`SetProcessor`, :py:class:`CopyProcessor`
      - `Set processor (ElasticSearch)`_
      - `add_field mutation (Logstash)`_,
        `copy mutation (Logstash)`_
    * -
      - `Set security user processor (ElasticSearch)`_
      -
    * - :py:class:`SortProcessor`
      - `Sort processor (ElasticSearch)`_
      -
    * - :py:class:`RegexpSplitProcessor`
      - `Split processor (ElasticSearch)`_
      - `split filter (Logstash)`_
    * - :py:class:`TrimProcessor`
      - `Trim processor (ElasticSearch)`_
      - `strip mutation (Logstash)`_
    * - :py:class:`UppercaseProcessor`
      - `Uppercase processor (ElasticSearch)`_
      - `uppercase mutation (Logstash)`_
    * - :py:class:`URLDecodeProcessor`
      - `URL decode processor (ElasticSearch)`_
      - `urldecode filter (Logstash)`_
    * - :py:class:`URIPartsProcessor`
      - `URI parts processor (ElasticSearch)`_
      -
    * - :py:class:`UserAgentProcessor`
      - `User agent processor (ElasticSearch)`_
      - `useragent filter (Logstash)`_

.. _Converting Ingest Node Pipelines:
    https://www.elastic.co/guide/en/logstash/current/ingest-converter.html
.. _Ingest converter source:
    https://github.com/elastic/logstash/tree/
    881f7605f11637f89462d2a272bf715a2c718b79/tools/ingest-converter/
    src/main/java/org/logstash/ingest

.. _Append processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    append-processor.html
.. _Bytes processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    bytes-processor.html
.. _CSV processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    csv-processor.html
.. _Community ID processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    community-id-processor.html
.. _Convert processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    convert-processor.html
.. _Date processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    date-processor.html
.. _Date index name processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    date-index-name-processor.html
.. _Dissect processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    dissect-processor.html
.. _Dot expander processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    dot-expand-processor.html
.. _Drop processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    drop-processor.html
.. _Fail processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    fail-processor.html
.. _Fingerprint processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    fingerprint-processor.html
.. _Foreach processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    foreach-processor.html
.. _GeoIP processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    geoip-processor.html
.. _Grok processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    grok-processor.html
.. _Gsub processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    gsub-processor.html
.. _HTML strip processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    htmlstrip-processor.html
.. _Join processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    join-processor.html
.. _JSON processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    json-processor.html
.. _KV processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    kv-processor.html
.. _Lowercase processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    lowercase-processor.html
.. _Network direction processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    network-direction-processor.html
.. _Redact processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    redact-processor.html
.. _Registered domain processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    registered-domain-processor.html
.. _Remove processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    remove-processor.html
.. _Rename processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    rename-processor.html
.. _Reroute processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    reroute-processor.html
.. _Script processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    script-processor.html
.. _Set processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    set-processor.html
.. _Set security user processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    ingest-node-set-security-user-processor.html
.. _Sort processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    sort-processor.html
.. _Split processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    split-processor.html
.. _Trim processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    trim-processor.html
.. _Uppercase processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    uppercase-processor.html
.. _URL decode processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    urldecode-processor.html
.. _URI parts processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    uri-parts-processor.html
.. _User agent processor (ElasticSearch):
    https://www.elastic.co/guide/en/elasticsearch/reference/current/
    user-agent-processor.html

.. _add_field mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-add_field
.. _bytes filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-bytes.html
.. _convert mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-convert
.. _copy mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-copy
.. _csv filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-csv.html#plugins-filters-csv-options
.. _date filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-date.html
.. _dissect filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-dissect.html
.. _drop filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-drop.html
.. _fingerprint filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-fingerprint.html
.. _geoip filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-geoip.html
.. _grok filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-grok.html
.. _gsub mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-gsub
.. _json filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-json.html
.. _lowercase mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-lowercase
.. _prune filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-prune.html
.. _rename mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-rename
.. _split filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/plugins-filters-split.html
.. _strip mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-uppercase
.. _uppercase mutation (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-mutate.html#plugins-filters-mutate-uppercase
.. _urldecode filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-urldecode.html
.. _useragent filter (Logstash):
    https://www.elastic.co/guide/en/logstash/current/
    plugins-filters-useragent.html
