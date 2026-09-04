import os
import re
import base64
import requests
from urlextract import URLExtract
from dotenv import load_dotenv

load_dotenv()

VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
VT_URL_ENDPOINT = "https://www.virustotal.com/api/v3/urls"

extractor = URLExtract()


def extract_urls(text: str) -> list:
    
    urls = extractor.find_urls(text)
    return list(set(urls))  # dedupe


def check_url_reputation(url: str) -> dict:
    
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    response = requests.get(f"{VT_URL_ENDPOINT}/{url_id}", headers=headers)

    if response.status_code == 404:
        # VirusTotal hasn't seen this URL before, submit it for analysis
        submit_response = requests.post(
            VT_URL_ENDPOINT,
            headers=headers,
            data={"url": url}
        )
        if submit_response.status_code not in (200, 201):
            return {
                "url": url,
                "status": "error",
                "detail": "Could not submit URL for analysis"
            }
        return {
            "url": url,
            "status": "unknown",
            "detail": "URL submitted for analysis, no verdict yet"
        }

    if response.status_code != 200:
        return {
            "url": url,
            "status": "error",
            "detail": f"VirusTotal API returned {response.status_code}"
        }

    data = response.json()
    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
    malicious_count = stats.get("malicious", 0)
    suspicious_count = stats.get("suspicious", 0)

    if malicious_count > 0 or suspicious_count > 0:
        return {
            "url": url,
            "status": "flagged",
            "malicious_votes": malicious_count,
            "suspicious_votes": suspicious_count
        }

    return {
        "url": url,
        "status": "clean",
        "malicious_votes": 0,
        "suspicious_votes": 0
    }


def check_links_in_text(text: str) -> dict:
    
    urls = extract_urls(text)

    if not urls:
        return {
            "urls_found": [],
            "any_flagged": False,
            "results": []
        }

    results = [check_url_reputation(url) for url in urls]
    any_flagged = any(r["status"] == "flagged" for r in results)

    return {
        "urls_found": urls,
        "any_flagged": any_flagged,
        "results": results
    }
