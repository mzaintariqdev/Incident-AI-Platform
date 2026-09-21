"""
AI worker service.

This is a standalone process (its own container) that:
  1. Blocks on a Redis list ("ticket_queue") for new ticket IDs
  2. Loads the ticket from Postgres
  3. Calls the Groq API (free tier) to classify severity + generate a summary
  4. Writes the result back to the ticket row

Run this alongside core-service via docker-compose. It's intentionally simple
(a polling loop, not Celery/Kafka) -- enough to demonstrate real async
processing between two services without adding infra you don't have time for.
"""
import json
import os
import time
import logging

import redis
import requests
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [ai-worker] %(message)s")
log = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://incident_user:incident_pass@localhost:5432/incident_db",
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

SYSTEM_PROMPT = """You are a triage assistant for a software incident/support desk.
Given a ticket title and description, respond ONLY with a JSON object, no prose,
no markdown fences, in exactly this shape:

{
  "severity": "low" | "medium" | "high" | "critical",
  "summary": "<one sentence, under 25 words, plain English>",
  "confidence": <float between 0 and 1>
}
"""


def classify_with_groq(title: str, description: str) -> dict:
    if not GROQ_API_KEY:
        # Fallback so the pipeline still works end-to-end without a key configured yet
        log.warning("GROQ_API_KEY not set, using naive fallback classification")
        return {"severity": "medium", "summary": title[:120], "confidence": 0.3}

    resp = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Title: {title}\nDescription: {description}"},
            ],
            "temperature": 0.2,
            "max_tokens": 200,
        },
        timeout=20,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(content)


def process_ticket(ticket_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT title, description FROM tickets WHERE id = :id"), {"id": ticket_id}
        ).fetchone()
        if row is None:
            log.warning(f"Ticket {ticket_id} not found, skipping")
            return

        title, description = row
        try:
            result = classify_with_groq(title, description)
        except Exception as e:
            log.error(f"AI classification failed for {ticket_id}: {e}")
            result = {"severity": "medium", "summary": "AI classification failed.", "confidence": 0.0}

        conn.execute(
            text(
                """
                UPDATE tickets
                SET severity = :severity,
                    ai_summary = :summary,
                    ai_confidence = :confidence,
                    ai_processed_at = now()
                WHERE id = :id
                """
            ),
            {
                "severity": result.get("severity", "medium"),
                "summary": result.get("summary", ""),
                "confidence": result.get("confidence", 0.5),
                "id": ticket_id,
            },
        )
    r.publish("ticket_events", json.dumps({"event": "ticket_ai_processed", "ticket_id": ticket_id}))
    log.info(f"Processed ticket {ticket_id}: severity={result.get('severity')}")


def main():
    log.info("AI worker started, listening on Redis queue 'ticket_queue'...")
    while True:
        try:
            # BLPOP blocks until a job arrives (or timeout), no busy-waiting
            job = r.blpop("ticket_queue", timeout=5)
            if job is None:
                continue
            _, payload = job
            data = json.loads(payload)
            process_ticket(data["ticket_id"])
        except Exception as e:
            log.error(f"Worker loop error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
