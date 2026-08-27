from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional
from database import init_db, save_ticket, get_all_tickets
from classifier import (
    classify_ticket,
    classify_image_type,
    classify_product_category,
    describe_screenshot
)
from anomaly_detector import run_anomaly_detection
from pdf_handler import extract_text_from_pdf

app = FastAPI()

init_db()

MAX_PDF_CHARS = 2000


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

    result = classify_ticket(subject, body, image_context=image_context)

    ticket_id = save_ticket(
        sender=sender,
        subject=subject,
        body=body,
        category=result.get("category"),
        summary=result.get("summary"),
        draft_reply=result.get("draft_reply")
    )

    return {
        "id": ticket_id,
        "status": "received",
        "sender": sender,
        "category": result.get("category"),
        "summary": result.get("summary"),
        "draft_reply": result.get("draft_reply"),
        "attachment_received": attachment_info
    }


@app.get("/tickets")
def list_tickets():
    return get_all_tickets()