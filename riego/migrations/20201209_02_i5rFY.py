"""

"""

from yoyo import step

__depends__ = {'20201209_01_8Z7Jg'}

steps = [
    step(
	"""ALTER TABLE valves ADD COLUMN remark TEXT""",
	"""ALTER TABLE valves DROP COLUMN remark"""
	)
]
