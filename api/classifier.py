import os
import json
import re
import base64
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLASSIFICATION_PROMPT = """You are a support ticket triage assistant. Analyze the following support request and respond with ONLY a JSON object, no other text, in exactly this format:

{{
  "category": "billing" or "technical" or "access" or "general" or "urgent",
  "summary": "one line summary of what the person wants",
  "draft_reply": "a short, professional draft reply addressing their request"
}}

Support request:
Subject: {subject}
Body: {body}
"""

MVTEC_CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid", "hazelnut",
    "leather", "metal_nut", "pill", "screw", "tile", "toothbrush",
    "transistor", "wood", "zipper"
]


def extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def classify_ticket(subject: str, body: str, image_context: str = None) -> dict:
    extra_context = ""
    if image_context:
        extra_context = f"\n\nAdditional context from an attached image: {image_context}"

    prompt = CLASSIFICATION_PROMPT.format(subject=subject, body=body) + extra_context

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
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
            "summary": "Could not parse classification",
            "draft_reply": ""
        }

    return result


def classify_image_type(image_bytes: bytes, media_type: str) -> str:
    """
    Returns 'product_photo' or 'screenshot' based on what Claude sees.
    """
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
    """
    Returns the closest matching MVTec category, or 'unknown' if none fit well.
    """
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
    """
    Asks Claude to describe the content of a screenshot, including any visible error text.
    """
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