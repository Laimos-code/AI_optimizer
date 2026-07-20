from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone
from database import Base



class APICall(Base):
    __tablename__ = "api_calls"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    feature_name = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    prefix = Column(String, nullable=False)
    name = Column(String, nullable=False)          # human label e.g. "my-app"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) 

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    metric = Column(String, nullable=False)
    threshold = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))    