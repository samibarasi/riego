"""

"""

from yoyo import step

__depends__ = {'__init__'}

steps = [
    step(
    """CREATE TABLE boxes (
	id INTEGER NOT NULL, 
	topic VARCHAR, 
	name VARCHAR, 
	hostname VARCHAR, 
	remark VARCHAR, 
	first_seen DATETIME, 
	online_since DATETIME, 
	hw_type VARCHAR, 
	hw_version VARCHAR, 
	sw_type VARCHAR, 
	sw_version VARCHAR, 
	fallback_topic VARCHAR, 
	group_topic VARCHAR, 
	ip_address VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT topic_uc UNIQUE (topic)
    )"""
    ),(
    """DROP TABLE boxes"""
    ),
    step(
    """CREATE TABLE events (
	id INTEGER NOT NULL, 
	duration INTEGER, 
	water_amount INTEGER, 
	valve_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(valve_id) REFERENCES valves (id)
    )"""
    ),(
    """DROP TABLE events"""
    ),
    step(
    """CREATE TABLE parameters (
	id INTEGER NOT NULL, 
	"key" VARCHAR, 
	value VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT key_uc UNIQUE ("key")
    )"""
    ),(
     """DROP TABLE parameters"""
    ),
    step(
    """CREATE TABLE valves (
	id INTEGER NOT NULL, 
	name VARCHAR, 
	remark VARCHAR, 
	channel_nr INTEGER NOT NULL, 
	duration INTEGER, 
	interval INTEGER, 
	last_shedule DATETIME, 
	is_running INTEGER, 
	is_enabled INTEGER, 
	is_hidden INTEGER, 
	prio INTEGER, 
	box_id INTEGER NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT channel_nr_box_id_uc UNIQUE (channel_nr, box_id), 
	FOREIGN KEY(box_id) REFERENCES boxes (id)
    )"""
    ),(
    """DROP TABLE valves"""
    )
]
