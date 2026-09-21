"""
Demo/seed script — run this against a running core-service to populate
sample data for your demo video. Also doubles as an example of how to
send a correctly-signed webhook request.

Usage:
    python seed_demo_data.py
"""
import hashlib
import hmac
import json
import time

import requests

BASE_URL = "http://localhost:8000"
WEBHOOK_SECRET = "dev-webhook-secret"  # must match .env WEBHOOK_SECRET

SAMPLE_ISSUES = [
    {"external_id": "gh-1001", "title": "Login page returns 500 on Safari",
     "description": "Users on Safari 17 get a blank page and a 500 error when submitting the login form."},
    {"external_id": "gh-1002", "title": "Typo in footer copyright year",
     "description": "Footer still says 2024 instead of 2026."},
    {"external_id": "gh-1003", "title": "Payment webhook occasionally double-charges",
     "description": "Under high load, the payment confirmation webhook fires twice, charging the customer twice."},
    {"external_id": "gh-1004", "title": "Dashboard chart flickers on resize",
     "description": "Resizing the browser window causes the D3 chart to flicker and briefly show no data."},
    {"external_id": "gh-1005", "title": "Database connection pool exhausted under load",
     "description": "During a traffic spike, the API starts returning 503s because the Postgres connection pool is exhausted."},
]


def signed_headers(body: bytes) -> dict:
    signature = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return {"Content-Type": "application/json", "X-Signature-256": f"sha256={signature}"}


def main():
    print("Sending sample webhook events to core-service...")
    for issue in SAMPLE_ISSUES:
        body = json.dumps(issue).encode()
        resp = requests.post(f"{BASE_URL}/webhooks/issues", data=body, headers=signed_headers(body))
        print(f"  {issue['external_id']}: {resp.status_code}")
        time.sleep(0.5)
    print("Done. Give the AI worker a few seconds to classify them, then check /tickets and /analytics/summary.")


if __name__ == "__main__":
    main()
