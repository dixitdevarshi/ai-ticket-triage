from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://ticket_admin:ticket_pass_dev@localhost:5432/ticket_triage"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    sender = Column(String)
    subject = Column(String)
    body = Column(String)
    category = Column(String)
    urgency = Column(String)
    summary = Column(String)
    draft_reply = Column(String)
    confidence = Column(String)
    needs_review = Column(Integer, default=0)
    review_reason = Column(String)
    corrected_category = Column(String)
    corrected_urgency = Column(String)
    reviewed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)