"""

"""

from yoyo import step

__depends__ = {'__init__'}

steps = [
    step(
    '''CREATE TABLE "boxes" (
	"id"	            INTEGER,
	"topic"	            VARCHAR NOT NULL,
	"name"	            VARCHAR,
	"hostname"	        VARCHAR,
	"remark"	        VARCHAR,
	"first_seen"	    timestamp DEFAULT CURRENT_TIMESTAMP,
	"online_since"  	timestamp DEFAULT CURRENT_TIMESTAMP,
	"hw_type"	        VARCHAR,
	"hw_version"    	VARCHAR,
	"sw_type"	        VARCHAR,
	"sw_version"	    VARCHAR,
	"fallback_topic"    VARCHAR,
	"group_topic"	    VARCHAR,
	"ip_address"	    VARCHAR,
	"created_at"	    timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "topic_uc" UNIQUE("topic"),
    PRIMARY KEY("id"))''',
    '''DROP TABLE "boxes" '''
    ),
    step(
    '''CREATE TABLE "events" (
	"id"	        INTEGER,
	"duration"	    INTEGER DEFAULT 0,
	"water_amount"	INTEGER,
	"valve_id"	    INTEGER NOT NULL REFERENCES "valves"("id") ON DELETE CASCADE,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY("id"))''',
    '''DROP TABLE "events" '''
    ),
    step(
    '''CREATE TABLE "parameters" (
	"id"	        INTEGER,
	"key"	        VARCHAR NOT NULL,
	"value"	        VARCHAR,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "key_uc" UNIQUE("key"),
    PRIMARY KEY("id"))''',
     '''DROP TABLE "parameters" '''
    ),
    step(
    '''INSERT INTO "parameters" (key,value) VALUES ("start_time_1", "19:00") ''',
    '''DELETE FROM "parameters" WHERTE key = "start_time_1" '''    
    ),
    step(
    '''INSERT INTO "parameters" (key,value) VALUES ("max_duration", "180") ''',
    '''DELETE FROM "parameters" WHERTE key = "max_duration" '''    
    ),
    step(
    '''CREATE TABLE "valves" (
	"id"	        INTEGER,
	"name"	        VARCHAR,
	"remark"	    VARCHAR DEFAULT '',
	"channel_nr"	INTEGER NOT NULL,
	"duration"	    INTEGER DEFAULT 0,
	"interval"	    INTEGER DEFAULT 4,
	"last_shedule"	timestamp DEFAULT '1970-01-01 00:00:00',
    "last_run"	    timestamp DEFAULT '1970-01-01 00:00:00',
	"is_running"	INTEGER DEFAULT 0,
	"is_enabled"	INTEGER DEFAULT 0,
	"is_hidden"	    INTEGER DEFAULT 1,
	"prio"	        INTEGER DEFAULT 9,
	"box_id"	    INTEGER NOT NULL REFERENCES "boxes"("id") ON DELETE CASCADE,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT "channel_nr_box_id_uc" UNIQUE("channel_nr","box_id"),
    PRIMARY KEY("id"))''',
    '''DROP TABLE "valves" '''
    )
]
