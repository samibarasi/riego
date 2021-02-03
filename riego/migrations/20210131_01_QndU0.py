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
            config_version VARCHAR, 
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
        """CREATE TABLE event_logs (
            id INTEGER NOT NULL, 
            message VARCHAR, 
            level INTEGER, 
            valve_id INTEGER NOT NULL, 
            created_at DATETIME, 
            PRIMARY KEY (id), 
            FOREIGN KEY(valve_id) REFERENCES valves (id)
        )"""
    ),(
        """DROP TABLE event_logs"""
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
        """INSERT INTO parameters (key,value) VALUES('maxDuration','240')"""
    ),
    step(
        """INSERT INTO parameters (key,value) VALUES('startTime','19:00')"""
    ),
    step(
        """CREATE TABLE valves (
            id INTEGER NOT NULL, 
            name VARCHAR, 
            remark VARCHAR, 
            channel_nr INTEGER NOT NULL, 
            duration INTEGER, 
            interval INTEGER, 
            last_run DATETIME, 
            last_shedule DATETIME, 
            is_running BOOLEAN, 
            is_enabled BOOLEAN, 
            is_hidden BOOLEAN, 
            prio INTEGER, 
            box_id INTEGER NOT NULL, 
            created_at DATETIME, 
            PRIMARY KEY (id), 
            CONSTRAINT channel_nr_box_id_uc UNIQUE (channel_nr, box_id), 
            CHECK (is_running IN (0, 1)), 
            CHECK (is_enabled IN (0, 1)), 
            CHECK (is_hidden IN (0, 1)), 
            FOREIGN KEY(box_id) REFERENCES boxes (id)
        )"""
    ),(
        """DROP TABLE valves"""
    )
]
