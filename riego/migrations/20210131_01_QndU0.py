"""

"""

from yoyo import step

__depends__ = {'__init__'}

steps = [
    step(
    """CREATE TABLE "boxes" (
	"id"	INTEGER PRIMARY KEY,
	"topic"	VARCHAR NOT NULL,
	"name"	VARCHAR,
	"hostname"	VARCHAR,
	"remark"	VARCHAR DEAFULT '',
	"first_seen"	timestamp DEFAULT CURRENT_TIMESTAMP,
	"online_since"	timestamp DEFAULT CURRENT_TIMESTAMP,
	"hw_type"	VARCHAR,
	"hw_version"	VARCHAR,
	"sw_type"	VARCHAR,
	"sw_version"	VARCHAR,
	"fallback_topic"	VARCHAR,
	"group_topic"	VARCHAR,
	"ip_address"	VARCHAR,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "topic_uc" UNIQUE("topic")
)"""
    ),(
    """DROP TABLE boxes"""
    ),
    step(
    """CREATE TABLE "events" (
	"id"	INTEGER PRIMARY KEY,
	"duration"	INTEGER DEFAULT 0,
	"water_amount"	INTEGER,
	"valve_id"	INTEGER NOT NULL REFERENCES "valves"("id") ON DELETE CASCADE,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP
)"""
    ),(
    """DROP TABLE events"""
    ),
    step(
    """CREATE TABLE "parameters" (
	"id"	INTEGER PRIMARY KEY,
	"key"	VARCHAR NOT NULL,
	"value"	VARCHAR,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "key_uc" UNIQUE("key")
)"""
    ),(
     """DROP TABLE parameters"""
    ),
    step(
    """CREATE TABLE "valves" (
	"id"	INTEGER PRIMARY KEY,
	"name"	VARCHAR,
	"remark"	VARCHAR DEFAULT '',
	"channel_nr"	INTEGER NOT NULL,
	"duration"	INTEGER DEFAULT 0,
	"interval"	INTEGER DEFAULT 4,
	"last_shedule"	DATETIME DEFAULT '1970-01-01 00:00:00.000000',
	"is_running"	INTEGER DEFAULT 0,
	"is_enabled"	INTEGER DEFAULT 0,
	"is_hidden"	INTEGER DEFAULT 1,
	"prio"	INTEGER DEFAULT 9,
	"box_id"	INTEGER NOT NULL REFERENCES "boxes"("id") ON DELETE CASCADE,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "channel_nr_box_id_uc" UNIQUE("channel_nr","box_id")
)"""
    ),(
    """DROP TABLE valves"""
    )
]
