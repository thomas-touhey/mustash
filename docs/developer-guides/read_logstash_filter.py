from __future__ import annotations

from mustash.logstash import parse_from_config


raw_config = """
filter {
    json {
        source => "message"
    }
    mutate {
        add_field => {
            "@hello" => "wow"
        }
    }
}
"""

pipeline = parse_from_config(raw_config)
