import os
import json
import re
import base64
import random
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLASSIFICATION_PROMPT = """You are a support ticket triage assistant. Analyze the following support request and respond with ONLY a JSON object, no other text, in exactly this format:

{{
  "category": "billing" or "technical" or "access" or "general",
  "urgency": "low" or "medium" or "high",
  "summary": "one line summary of what the person wants",
  "draft_reply": "a short, professional draft reply addressing their request",
  "confidence": "high" or "medium" or "low"
}}

"category" describes the TOPIC of the request. "urgency" describes how time-sensitive it is, independent of topic.

Use this calibration for urgency, and default to "low" unless the ticket clearly meets a higher bar:
- "low": routine questions, general inquiries, single-user minor inconveniences, requests with no stated deadline or business impact. This should be the default for most tickets.
- "medium": a real problem affecting the individual customer's ability to use the product or get what they paid for, but not affecting other users and not described as actively ongoing right now.
- "high": ONLY for active outages, security incidents, issues affecting multiple users/customers simultaneously, or explicitly stated business-critical deadlines. The ticket must describe the problem as currently happening and causing real impact, not just being annoying.

Most tickets are "low". Reserve "high" for genuinely urgent situations only, do not inflate urgency just because a customer is writing to support.

"category" describes the TOPIC of the request. "urgency" describes how time-sensitive it is, independent of topic, a billing question can be low urgency, and a billing issue affecting many customers right now can be high urgency, at the same time.

Report "low" or "medium" confidence honestly whenever EITHER the category OR the urgency is genuinely ambiguous, not just when the category is unclear. Don't default to "high" just to seem certain.
{examples_block}
Support request:
Subject: {subject}
Body: {body}
"""

MVTEC_CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid", "hazelnut",
    "leather", "metal_nut", "pill", "screw", "tile", "toothbrush",
    "transistor", "wood", "zipper"
]

RANDOM_SAMPLE_RATE = 0.1


def extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def build_examples_block(past_corrections: list) -> str:
    if not past_corrections:
        return ""

    lines = ["\nHere are some past tickets a human corrected, for reference:"]
    for ex in past_corrections:
        parts = []
        if ex.get("corrected_category"):
            parts.append(f'category: {ex["corrected_category"]}')
        if ex.get("corrected_urgency"):
            parts.append(f'urgency: {ex["corrected_urgency"]}')
        correction_str = ", ".join(parts)
        lines.append(
            f'- Subject: "{ex["subject"]}" Body: "{ex["body"]}" -> correct {correction_str}'
        )
    return "\n".join(lines) + "\n"


def classify_ticket(subject: str, body: str, image_context: str = None, past_corrections: list = None) -> dict:
    examples_block = build_examples_block(past_corrections or [])

    extra_context = ""
    if image_context:
        extra_context = f"\n\nAdditional context from an attached image: {image_context}"

    prompt = CLASSIFICATION_PROMPT.format(
        subject=subject, body=body, examples_block=examples_block
    ) + extra_context

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    raw_text = response.content[0].text
    cleaned_text = extract_json(raw_text)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("RAW CLAUDE OUTPUT (failed to parse):")
        print(raw_text)
        result = {
            "category": "general",
            "urgency": "low",
            "summary": "Could not parse classification",
            "draft_reply": "",
            "confidence": "low"
        }

    confidence = result.get("confidence", "medium")

    needs_review = False
    review_reason = None

    if confidence in ("low", "medium"):
        needs_review = True
        review_reason = "low_confidence"
    elif random.random() < RANDOM_SAMPLE_RATE:
        needs_review = True
        review_reason = "random_sample"

    result["needs_review"] = needs_review
    result["review_reason"] = review_reason

    return result


def classify_image_type(image_bytes: bytes, media_type: str) -> str:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Is this a photo of a physical product/object, or a screenshot of software/an app/an error message? Reply with only one word: 'product' or 'screenshot'."
                    }
                ]
            }
        ]
    )

    answer = response.content[0].text.strip().lower()
    return "product_photo" if "product" in answer else "screenshot"


def classify_product_category(image_bytes: bytes, media_type: str) -> str:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    categories_list = ", ".join(MVTEC_CATEGORIES)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": f"Which of these product categories does this image most closely resemble: {categories_list}? If none fit reasonably well, reply 'unknown'. Reply with only the single category word, nothing else."
                    }
                ]
            }
        ]
    )

    answer = response.content[0].text.strip().lower()
    return answer if answer in MVTEC_CATEGORIES else "unknown"


def describe_screenshot(image_bytes: bytes, media_type: str) -> str:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Describe what this screenshot shows in 2-3 plain sentences, no markdown formatting, no headers, no bullet points. Include any visible error messages or error codes verbatim if present."
                    }
                ]
            }
        ]
    )

    return response.content[0].text.strip()
