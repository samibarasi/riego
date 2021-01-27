"""

"""

from yoyo import step

__depends__ = {'20210127_01_ha5ql'}

steps = [
        step(
        '''CREATE TABLE "x_valves" (
            "id"	INTEGER,
            "name"	TEXT,
            "remark"	TEXT,
            "box_id"	INTEGER NOT NULL,
            "channel"	TEXT NOT NULL,
            "duration"	INTEGER DEFAULT 0,
            "interval"	INTEGER DEFAULT 0,
            "last_run"	INTEGER DEFAULT '1970-01-01 00:000:00',
            "is_running"	INTEGER DEFAULT 0,
            "is_enabled"	INTEGER DEFAULT 0,
            "last_shedule" TEXT,
            "hide" INT,
            UNIQUE("channel","box_id"),
            PRIMARY KEY("id"))''',
        """DROP TABLE x_valves;"""
        ),
        step(
        """INSERT INTO x_valves SELECT * FROM valves;""",
        """INSERT INTO valves SELECT * FROM x_valves;"""
        ),
        step(
        """DROP TABLE valves;""",
        '''CREATE TABLE "valves" (
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
            "last_shedule" TEXT,
            "hide2 INT,
            UNIQUE("channel","box_id"),
            PRIMARY KEY("id"))'''
        ),
        step(
        """ALTER TABLE x_valves RENAME TO valves;""",
        """ALTER TABLE valves RENAME TO x_valves;"""
        )
    
    
    
    
]
