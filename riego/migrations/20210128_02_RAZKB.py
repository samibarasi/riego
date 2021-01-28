"""

"""

from yoyo import step

__depends__ = {'20210128_01_zr0ze'}

steps = [
    step("""ALTER TABLE valves ADD COLUMN channel_nr INTEGER""",
        """ALTER TABLE valves DROP COLUMN channel_nr""")
   
]
