from riego.model.base import Base

from sqlalchemy import (
    Column, ForeignKey,
    Integer, DateTime
)
from sqlalchemy.sql import func


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    duration = Column(Integer, default=0)
    water_amount = Column(Integer, default=0)
    valve_id = Column(Integer, ForeignKey('valves.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Event(created_at= '%s', valve_id='%s', duration='%s')>" % (
            self.created_at, self.valve_id, self.duration)
