from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from datetime import datetime

from riego.model.base import Base


class Parameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    key = Column(String)
    value = Column(String)
    created_at = Column(DateTime, default=datetime.now())

    __table_args__ = (
        UniqueConstraint('key', name='key_uc'),
    )

    def __repr__(self):
        return "<Parameter(key='%s', value='%s')>" % (self.key, self.value)
