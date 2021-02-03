from datetime import datetime


from sqlalchemy import (
    Column, UniqueConstraint,
    Integer, String, DateTime
)
from sqlalchemy.orm import relationship

from riego.model.base import Base
from riego.model.valves import Valve


class Box(Base):
    __tablename__ = 'boxes'

    id = Column(Integer, primary_key=True)
    topic = Column(String)
    name = Column(String)
    hostname = Column(String)
    remark = Column(String)
    config_version = Column(String)
    first_seen = Column(DateTime, default=datetime.now())
    online_since = Column(DateTime, default=datetime.now())
    hw_type = Column(String)
    hw_version = Column(String)
    sw_type = Column(String)
    sw_version = Column(String)
    fallback_topic = Column(String)
    group_topic = Column(String)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    valves = relationship(Valve, backref='box',
                          cascade="all, delete, delete-orphan")

    __table_args__ = (
        UniqueConstraint('topic', name='topic_uc'),
    )

    def __repr__(self):
        return "<Box(topic='%s', name='%s')>" % (self.topic, self.name)
