"""

"""

from yoyo import step

__depends__ = {'20201209_03_YHuBM'}

steps = [
    step(
	"""CREATE TABLE boxes
            (id  	INTEGER PRIMARY KEY AUTOINCREMENT,
            name	TEXT UNIQUE,
			remark	TEXT,
            first_seen	timestamp DEFAULT CURRENT_TIMESTAMP,
            has_config	INTEGER DEFAULT 0,
			is_online	INTEGER)""",
	"""DROP TABLE boxes"""
	)
	
	
]
