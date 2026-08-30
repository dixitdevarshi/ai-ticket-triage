import os
from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
import requests
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator
from database import (
    init_db,
    save_ticket,
    get_all_tickets,
    get_tickets_needing_review,
    submit_correction,
    get_past_corrections
)
from classifier import (
    classify_ticket,
    classify_image_type,
    classify_product_category,
    describe_screenshot
)
from anomaly_detector import run_anomaly_detection
from pdf_handler import extract_text_from_pdf
from link_checker import check_links_in_text

load_dotenv()

app = FastAPI()

init_db()

Instrumentator().instrument(app).expose(app)

MAX_PDF_CHARS = 2000
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


def notify_needs_review(ticket_id: int, sender: str, subject: str, category: str, urgency: str, reason: str):
    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set, skipping review notification")
        return
    try:
        requests.post(
            SLACK_WEBHOOK_URL,
            json={
                "text": f"Ticket #{ticket_id} needs review (reason: {reason})\nFrom: {sender}\nSubject: {subject}\nPredicted category: {category} | Predicted urgency: {urgency}\nCorrect it via POST /tickets/{ticket_id}/correct"
            },
            timeout=5
        )
    except Exception as e:
        print(f"Failed to send review notification: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tickets")
async def create_ticket(
    sender: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    attachment: Optional[UploadFile] = File(None)
):
    attachment_info = None
    image_context = None

    link_check = check_links_in_text(body)

    if link_check["any_flagged"]:
        ticket_id = save_ticket(
            sender=sender,
            subject=subject,
            body=body,
            category="security_review",
            urgency="high",
            summary="Ticket contains a link flagged as malicious or suspicious. Routed for manual review.",
            draft_reply=""
        )
        return {
            "id": ticket_id,
            "status": "flagged_for_review",
            "sender": sender,
            "category": "security_review",
            "urgency": "high",
            "summary": "Ticket contains a link flagged as malicious or suspicious. Routed for manual review.",
            "draft_reply": "",
            "link_check": link_check,
            "attachment_received": None
        }

    if attachment is not None:
        contents = await attachment.read()
        content_type = attachment.content_type or ""

        if content_type == "application/pdf":
            pdf_result = extract_text_from_pdf(contents)
            extracted = pdf_result["text"]
            truncated = extracted[:MAX_PDF_CHARS]
            was_truncated = len(extracted) > MAX_PDF_CHARS

            attachment_info = {
                "filename": attachment.filename,
                "type": "pdf_scanned" if pdf_result["used_ocr"] else "pdf_text",
                "page_count": pdf_result["page_count"],
                "extracted_chars": len(extracted),
                "truncated_for_prompt": was_truncated,
                "used_ocr": pdf_result["used_ocr"]
            }
            image_context = f"Customer attached a PDF document ({'OCR extracted' if pdf_result['used_ocr'] else 'text extracted'}). Content:\n{truncated}"

        elif content_type.startswith("image/"):
            image_type = classify_image_type(contents, content_type)

            if image_type == "product_photo":
                category_guess = classify_product_category(contents, content_type)

                if category_guess == "unknown":
                    attachment_info = {
                        "filename": attachment.filename,
                        "type": "product_photo",
                        "note": "No matching trained category, anomaly model skipped"
                    }
                    image_context = "Customer attached a product photo, but it didn't match any category the visual inspection model is trained on, so no automated defect score is available."
                else:
                    anomaly_result = run_anomaly_detection(contents, category=category_guess)

                    if anomaly_result is None:
                        attachment_info = {
                            "filename": attachment.filename,
                            "type": "product_photo",
                            "detected_category": category_guess,
                            "note": "Matched category but no trained memory bank available for it"
                        }
                        image_context = f"Customer attached a product photo that looks like a '{category_guess}', but no trained defect model is available for that category yet."
                    else:
                        score = anomaly_result["anomaly_score"]
                        attachment_info = {
                            "filename": attachment.filename,
                            "type": "product_photo",
                            "detected_category": category_guess,
                            "anomaly_score": score
                        }
                        image_context = (
                            f"Customer attached a product photo identified as '{category_guess}'. "
                            f"Automated visual inspection gave it an anomaly score of {score:.2f} "
                            f"(threshold for defect is around 30), suggesting "
                            f"{'a likely visible defect' if score > 30 else 'no obvious defect detected'}."
                        )
            else:
                description = describe_screenshot(contents, content_type)
                attachment_info = {
                    "filename": attachment.filename,
                    "type": "screenshot",
                    "description": description
                }
                image_context = f"Customer attached a screenshot. What it shows: {description}"

        else:
            attachment_info = {
                "filename": attachment.filename,
                "type": "unsupported",
                "note": f"File type '{content_type}' is not currently handled"
            }

    past_corrections = get_past_corrections(limit=3)
    result = classify_ticket(subject, body, image_context=image_context, past_corrections=past_corrections)

    ticket_id = save_ticket(
        sender=sender,
        subject=subject,
        body=body,
        category=result.get("category"),
        urgency=result.get("urgency"),
        summary=result.get("summary"),
        draft_reply=result.get("draft_reply"),
        confidence=result.get("confidence"),
        needs_review=1 if result.get("needs_review") else 0,
        review_reason=result.get("review_reason")
    )

    if result.get("needs_review"):
        notify_needs_review(
            ticket_id, sender, subject,
            result.get("category"), result.get("urgency"), result.get("review_reason")
        )

    return {
        "id": ticket_id,
        "status": "received",
        "sender": sender,
        "category": result.get("category"),
        "urgency": result.get("urgency"),
        "summary": result.get("summary"),
        "draft_reply": result.get("draft_reply"),
        "confidence": result.get("confidence"),
        "needs_review": result.get("needs_review"),
        "review_reason": result.get("review_reason"),
        "link_check": link_check,
        "attachment_received": attachment_info
    }


@app.get("/tickets")
def list_tickets():
    return get_all_tickets()


@app.get("/tickets/needs-review")
def list_tickets_needing_review():
    return get_tickets_needing_review()


@app.post("/tickets/{ticket_id}/correct")
def correct_ticket(ticket_id: int, corrected_category: Optional[str] = Form(None), corrected_urgency: Optional[str] = Form(None)):
    submit_correction(ticket_id, corrected_category, corrected_urgency)
    return {"id": ticket_id, "status": "corrected", "corrected_category": corrected_category, "corrected_urgency": corrected_urgency}
