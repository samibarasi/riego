"""

"""

from yoyo import step

__depends__ = {'20210127_03_Idfdx'}

steps = [
    step("ALTER TABLE valves RENAME COLUMN channel TO topic",
    "ALTER TABLE valves RENAME COLUMN topic TO channel")
]
