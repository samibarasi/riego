"""

"""

from yoyo import step

__depends__ = {}

steps = [
    step(
	"""CREATE TABLE valves
            (id  	INTEGER PRIMARY KEY AUTOINCREMENT,
            name	TEXT UNIQUE,
            topic	TEXT UNIQUE,
            duration	INTEGER DEFAULT 0,
            interval	INTEGER DEFAULT 0,
            last_run	timestamp DEFAULT CURRENT_TIMESTAMP,
            is_running	INTEGER DEFAULT 0,
            is_enabled	INTEGER DEFAULT 1)""",
	"""DROP TABLE valves"""
	),
	step(
	"""CREATE TABLE options
            (id	    INTEGER PRIMARY KEY AUTOINCREMENT,
            key	    TEXT UNIQUE,
            value   TEXT)""",
	"""DROP TABLE options"""
	)
]
