"""

"""

from yoyo import step

__depends__ = {'__init__'}

steps = [
    step('''CREATE TABLE "valves" (
    "id"	INTEGER,
    "name"	TEXT UNIQUE,
    "remark"	TEXT,
    "box_id"	INTEGER NOT NULL,
    "channel"	TEXT NOT NULL,
    "duration"	INTEGER DEFAULT 0,
    "interval"	INTEGER DEFAULT 0,
    "last_run"	INTEGER DEFAULT '1970-01-01 00:000:00',
    "is_running"	INTEGER DEFAULT 0,
    "is_enabled"	INTEGER DEFAULT 0,
    UNIQUE("channel","box_id"),
    PRIMARY KEY("id"))''',
         '''DROP TABLE "valves" '''
         ),

    step('''CREATE TABLE "boxes" (
    "id"	INTEGER,
    "topic"	TEXT UNIQUE,
    "hostname"	TEXT,
    "display_name"	TEXT UNIQUE,
    "remark"	TEXT,
    "first_seen"	TEXT,
    "has_config"	INTEGER,
    "online_since"	TEXT,
    "hw_type"	TEXT,
    "hw_version"	TEXT,
    "sw_version"	TEXT,
    "fallback_topic"	TEXT,
    "group_topic"	TEXT,
    "ip_address"	TEXT,
    PRIMARY KEY("id"))''',
         '''DROP TABLE "boxes" '''
         ),

    step('''CREATE TABLE "parameter" (
    "id"	INTEGER,
    "key"	TEXT UNIQUE,
    "value"	TEXT,
    PRIMARY KEY("id"))''',
         '''DROP TABLE "parameter" '''
         ),

    step('''CREATE TABLE "event_log" (
    "id"	INTEGER,
    "event"	TEXT,
    "date"	TEXT,
    PRIMARY KEY("id"))''',
         '''DROP TABLE "event_log" '''
         ),

    step(
        "INSERT INTO parameter (key,value) VALUES ('startTime', '19:00')",
        "DELETE FROM parameter WHERE key = 'startTime'"
    ),
    step(
        "INSERT INTO parameter (key,value) VALUES ('maxDuration', '4')",
        "DELETE FROM parameter WHERE key = 'maxDuration'"
    ),
    step(
        "INSERT INTO parameter (key,value) VALUES ('heat', '0')",
        "DELETE FROM parameter WHERE key = 'heat'"
    ),
    step(
        "INSERT INTO parameter (key,value) VALUES ('rain', '0')",
        "DELETE FROM parameter WHERE key = 'rain'"
    ),
    step(
        "INSERT INTO parameter (key,value) VALUES ('pause', '0')",
        "DELETE FROM parameter WHERE key = 'pause'"
    ),
    step(
        "INSERT INTO parameter (key,value) VALUES ('disable', '0')",
        "DELETE FROM parameter WHERE key = 'enable'"
    )


]
