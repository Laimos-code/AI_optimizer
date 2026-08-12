from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
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
    key_prefix = Column(String, nullable=False)
    name = Column(String, nullable=False)          # human label e.g. "my-app"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)) 

class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    metric = Column(String, nullable=False)
    threshold = Column(Float, nullable=False)
    period      = Column(String, nullable=False, default="daily")   # daily | weekly | monthly
    # WHAT to scope it to
    scope_type  = Column(String, nullable=True)                     # None | "model" | "provider"
    scope_value = Column(String, nullable=True)                     # e.g. "gpt-4o"
    # WHERE to send it
    channel     = Column(String, nullable=False)                    # "slack" | "email"
    target      = Column(String, nullable=False)                    # webhook URL or email address
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))    

class TriggeredAlert(Base):
    __tablename__ = "triggered_alerts"

    id         = Column(Integer, primary_key=True, index=True)
    rule_id    = Column(Integer, ForeignKey("alert_rules.id"), nullable=False, index=True)
    period_key = Column(String, nullable=False, index=True)   # "2026-07-29" — see below
    spend_usd  = Column(Float, nullable=False)                # what spend was when it fired
    fired_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    delivered  = Column(Boolean, default=False)               # did Slack/email actually accept it?
    is_read    = Column(Boolean, default=False)               # your unread-inbox idea