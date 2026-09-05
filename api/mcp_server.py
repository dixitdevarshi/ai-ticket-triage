from mcp.server import MCPServer
from database import get_tickets_needing_review, submit_correction

mcp = MCPServer("ticket-triage")


@mcp.tool()
def list_tickets_needing_review() -> list:
    """Returns all support tickets currently flagged for human review,
    either due to low model confidence or random spot-checking."""
    return get_tickets_needing_review()


@mcp.tool()
def correct_ticket(ticket_id: int, corrected_category: str = None, corrected_urgency: str = None) -> dict:
    """Submits a human correction for a flagged ticket's category and/or urgency.
    Valid categories: billing, technical, access, general.
    Valid urgency levels: low, medium, high.
    The correction is stored and used as a few-shot example for future similar tickets."""
    submit_correction(ticket_id, corrected_category, corrected_urgency)
    return {"status": "corrected", "ticket_id": ticket_id, "corrected_category": corrected_category, "corrected_urgency": corrected_urgency}


if __name__ == "__main__":
    mcp.run()