from db_models import SessionLocal, Ticket
from datetime import datetime


def init_db():
    # Table creation now happens via db_models.py's Base.metadata.create_all
    # This function is kept as a no-op so main.py's existing call doesn't break
    pass


def save_ticket(sender, subject, body, category=None, urgency=None, summary=None, draft_reply=None,
                 confidence=None, needs_review=0, review_reason=None):
    session = SessionLocal()
    try:
        ticket = Ticket(
            sender=sender,
            subject=subject,
            body=body,
            category=category,
            urgency=urgency,
            summary=summary,
            draft_reply=draft_reply,
            confidence=confidence,
            needs_review=needs_review,
            review_reason=review_reason,
            created_at=datetime.utcnow()
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        ticket_id = ticket.id
        return ticket_id
    finally:
        session.close()


def get_all_tickets():
    session = SessionLocal()
    try:
        tickets = session.query(Ticket).order_by(Ticket.id.desc()).all()
        return [ticket_to_dict(t) for t in tickets]
    finally:
        session.close()


def get_tickets_needing_review():
    session = SessionLocal()
    try:
        tickets = (
            session.query(Ticket)
            .filter(Ticket.needs_review == 1, Ticket.reviewed == 0)
            .order_by(Ticket.id.desc())
            .all()
        )
        return [ticket_to_dict(t) for t in tickets]
    finally:
        session.close()


def submit_correction(ticket_id, corrected_category=None, corrected_urgency=None):
    session = SessionLocal()
    try:
        ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.corrected_category = corrected_category
            ticket.corrected_urgency = corrected_urgency
            ticket.reviewed = 1
            session.commit()
    finally:
        session.close()


def get_past_corrections(limit=3):
    session = SessionLocal()
    try:
        tickets = (
            session.query(Ticket)
            .filter(Ticket.reviewed == 1)
            .filter((Ticket.corrected_category.isnot(None)) | (Ticket.corrected_urgency.isnot(None)))
            .order_by(Ticket.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "subject": t.subject,
                "body": t.body,
                "corrected_category": t.corrected_category,
                "corrected_urgency": t.corrected_urgency
            }
            for t in tickets
        ]
    finally:
        session.close()


def ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "id": ticket.id,
        "sender": ticket.sender,
        "subject": ticket.subject,
        "body": ticket.body,
        "category": ticket.category,
        "urgency": ticket.urgency,
        "summary": ticket.summary,
        "draft_reply": ticket.draft_reply,
        "confidence": ticket.confidence,
        "needs_review": ticket.needs_review,
        "review_reason": ticket.review_reason,
        "corrected_category": ticket.corrected_category,
        "corrected_urgency": ticket.corrected_urgency,
        "reviewed": ticket.reviewed,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None
    }