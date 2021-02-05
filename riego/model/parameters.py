from sqlalchemy import (
    Integer, String, DateTime,
    Column, UniqueConstraint)
from sqlalchemy.sql import func

from riego.model.base import Base


class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    key = Column(String, default='')
    value = Column(String, default='')
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('key', name='key_uc'),
    )

    def __repr__(self):
        return "<Parameter(key='%s', value='%s')>" % (self.key, self.value)
