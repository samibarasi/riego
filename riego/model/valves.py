from datetime import datetime
from sqlalchemy import (
    Column, ForeignKey, UniqueConstraint,
    Integer, String, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from riego.model.base import Base
from riego.model.events import Event


class Valve(Base):
    __tablename__ = 'valves'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='')
    remark = Column(String, default='')
    channel_nr = Column(Integer, nullable=False)
    duration = Column(Integer, default=0)
    interval = Column(Integer, default=7)
    last_shedule = Column(DateTime, default=datetime.fromtimestamp(0))
    is_running = Column(Integer, default=0)
    is_enabled = Column(Integer, default=0)
    is_hidden = Column(Integer, default=1)
    prio = Column(Integer, default=9)
    box_id = Column(Integer, ForeignKey('boxes.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    events = relationship(Event, backref='valve',
                          cascade="all, delete, delete-orphan")

    __table_args__ = (
        UniqueConstraint('channel_nr', 'box_id', name='channel_nr_box_id_uc'),
    )

    def __repr__(self):
        return "<Valve(name='%s', id='%s')>" % (self.name, self.id)
