"""

"""

from yoyo import step

__depends__ = {'20201210_01_X1eua'}

steps = [
    step(
        """ALTER TABLE options
            RENAME TO parameter;""",
        """ALTER TABLE parameter
            RENAME TO options;"""
    )
]
