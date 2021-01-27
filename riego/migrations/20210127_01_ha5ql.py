"""

"""

from yoyo import step

__depends__ = {'20210125_01_RxBRy'}

steps = [
    step( """ALTER TABLE valves ADD COLUMN last_shedule TEXT""",
	"""ALTER TABLE valves DROP COLUMN last_shedule"""
	),
    step ("""ALTER TABLE valves ADD COLUMN hide INT""",
	"""ALTER TABLE valves DROP COLUMN hide"""
	),
    step("ALTER TABLE boxes RENAME COLUMN display_name TO name",
	"ALTER TABLE boxes REANME COLUMN name TO display_name"
	),

]
