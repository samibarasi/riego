"""

"""

from yoyo import step

__depends__ = {'20201223_01_mDHp6'}

steps = [
    step(
	"""ALTER TABLE valves ADD COLUMN last_error INTEGER DEFAULT 0""",
	"""ALTER TABLE valves DROP COLUMN last_error"""
	), step(
	"""ALTER TABLE valves ADD COLUMN last_water_amount INTEGER DEFAULT 0""",
	"""ALTER TABLE valves DROP COLUMN last_water_amount"""
	), step(
	"""ALTER TABLE valves ADD COLUMN normal_water_amount INTEGER DEFAULT 0""",
	"""ALTER TABLE valves DROP COLUMN normal_water_amount"""
	), step(
	"""ALTER TABLE valves ADD COLUMN last_duration INTEGER DEFAULT 0""",
	"""ALTER TABLE valves DROP COLUMN last_duration"""
	), step(
	"""ALTER TABLE valves ADD COLUMN last_sheduled timestamp""",
	"""ALTER TABLE valves DROP COLUMN last_sheduled"""
	), 

]
