"""

"""

from yoyo import step

__depends__ = {'20201209_03_YHuBM'}

steps = [
    step(
	"""CREATE TABLE boxes
            (id  	        INTEGER PRIMARY KEY AUTOINCREMENT,
            name	        TEXT UNIQUE,
			remark	        TEXT,
            first_seen	    timestamp,
            has_config	    INTEGER,
			online_since	timestamp)""",
	"""DROP TABLE boxes"""
	)
	
	
]
