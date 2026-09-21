# Incident AI Platform

A small "smart inbox for bugs/incidents" — webhooks and manual reports flow in,
an AI worker classifies severity and writes a summary, and a Vue dashboard
shows live-updating tickets plus analytics.

Built to demonstrate: FastAPI, JWT auth + RBAC, webhook signature verification,
async processing between two services via Redis, an LLM in a real pipeline
(not just a chatbot), pagination/filtering, WebSockets, and D3/Chart.js.

## What this actually does (plain English)

Imagine a support inbox that sorts itself. Here's the story, step by step:

1. **A bug report comes in** — either someone fills out a form on the
   dashboard, or another system (like GitHub) automatically pings this app
   the moment an issue is filed.
2. **It's saved immediately**, tagged "not yet reviewed." The person doesn't
   wait around — the ticket shows up on the dashboard right away.
3. **A separate background worker picks it up** from a queue, sends the
   title and description to an AI model, and asks two things: *how serious
   is this, and can you summarize it in one sentence?*
4. **The AI's answer gets saved back** to that same ticket, and the
   dashboard updates itself **live**, no page refresh — everyone watching
   the dashboard sees the severity tag and summary appear a couple seconds
   later, automatically.
5. **A stats page** turns all of this into charts: how many tickets per
   day, how severe they are on average, how fast the team resolves them.

The interesting engineering problem this solves: reading a ticket with AI
takes a couple of seconds, but nobody should have to *wait* a couple of
seconds just to submit a bug report. So ticket creation and AI classification
are split into two separate processes that talk to each other through a
queue, instead of one doing the other's job inline. That's the "why" behind
most of the architecture below.

## Architecture

```
                    ┌─────────────┐
  GitHub-style  ───▶│             │
  webhook            │             │  ticket_queue  ┌──────────┐
                     │ core-service│───────────────▶│  Redis   │
  Vue dashboard ◀───▶│  (FastAPI)  │◀───────────────┤          │
  (REST + WS)        │             │ ticket_events   └────┬─────┘
                     └──────┬──────┘ (pub/sub)             │
                            │                               │
                            ▼                               ▼
                     ┌─────────────┐                 ┌─────────────┐
                     │  Postgres   │◀────────────────│  ai-worker  │
                     │             │  writes results  │ (Python)    │──▶ Groq API
                     └─────────────┘                 └─────────────┘   (LLM)
```

Two independent services (`core-service`, `ai-worker`), each with their own
process/container, communicating through Redis in two different ways:

- **`ticket_queue`** (a Redis list) hands off *work*: core-service pushes a
  ticket ID when one is created; ai-worker blocks on it (`BLPOP`) and picks
  jobs up one at a time.
- **`ticket_events`** (a Redis pub/sub channel) hands off *announcements*:
  once ai-worker finishes classifying a ticket, it publishes a small event;
  core-service is subscribed to that channel in a background task and
  relays the event to every connected WebSocket client, so the dashboard
  updates the moment classification finishes — no polling, no refresh.

`core-service` never blocks on the LLM call — tickets appear immediately
with `severity: unclassified` and get updated live once the AI worker is
done, via this pub/sub relay.

> **A real bug I hit and fixed:** the first version of the pub/sub listener
> used `asyncio.create_task(...)` without keeping a reference to the task.
> Python's garbage collector silently killed it a moment after startup —
> the log showed `Task was destroyed but it is pending!`. Fixed by storing
> the task on `app.state` so it stays alive for the life of the app. Good
> example of why "it looks like it's running" isn't the same as "it's
> actually running."

## Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, JWT (access + refresh), bcrypt
- **AI**: Groq API (free tier — currently using `openai/gpt-oss-20b`, configurable via `GROQ_MODEL` in `.env`) — swap `GROQ_MODEL`/`GROQ_URL` in `ai-worker/worker.py` for a different provider or Ollama. Worth noting: AI providers deprecate model names over time (this project's original model, `llama-3.1-8b-instant`, was retired mid-build) — the model name lives in an env var rather than hardcoded, specifically so swapping it doesn't need a code change.
- **Frontend**: Vue 3, Pinia, Vue Router, Chart.js, D3.js, native WebSocket
- **Infra**: Docker Compose (Postgres, Redis, core-service, ai-worker)

Everything runs on free tiers / local containers — no paid services required.

## Getting started

```bash
cp .env.example .env
# edit .env: set JWT_SECRET_KEY, WEBHOOK_SECRET, and GROQ_API_KEY
# (get a free Groq key at https://console.groq.com/keys)

docker compose up --build
```

Backend runs at `http://localhost:8000` (docs at `/docs`).

Frontend (separate terminal, not yet containerized — run locally for dev):
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`. The first user you register becomes `admin`
automatically; everyone after that is an `agent`.

### Simulating webhook traffic

```bash
pip install requests
python seed_demo_data.py
```
This sends signed sample "GitHub issue" webhooks to `/webhooks/issues` and
lets you watch tickets appear live on the dashboard, then get classified by
the AI worker a few seconds later.

## What I intentionally scoped out (and why)

This is a 2-week, evenings/weekends portfolio project, not a production
system. Things I'd add with more time, and why I didn't build them now:

- **More microservices** (separate auth/notification services) — two
  services already demonstrate the async-communication pattern; more would
  mostly add Docker Compose complexity, not new skills.
- **Kafka/RabbitMQ instead of Redis** — Redis lists give the same "queue
  between services" pattern with far less operational overhead for a
  single-node demo.
- **Alembic migrations** — using `Base.metadata.create_all()` for now;
  Alembic is the obvious next step before this touched a real production DB.
- **Email/Slack notifications** — the WebSocket live-update already proves
  the real-time piece; a notification service would be additive, not new.
- **Kubernetes** — Docker Compose is the honest choice for a single-node
  portfolio demo; a k8s manifest would be cosplay at this scale.

## API overview

| Endpoint | Method | Auth | Notes |
|---|---|---|---|
| `/auth/register` | POST | — | first user becomes admin |
| `/auth/login` | POST | — | returns access + refresh JWT |
| `/auth/refresh` | POST | — | rotate access token |
| `/tickets` | GET | required | paginated, filter by `status`/`severity` |
| `/tickets` | POST | required | create a ticket manually |
| `/tickets/{id}` | PATCH | agent/admin | update status/severity |
| `/webhooks/issues` | POST | HMAC signature | ingest external issue, dedup by `external_id` |
| `/analytics/summary` | GET | required | volume, severity breakdown, resolution time, AI confidence |
| `/ws/tickets` | WS | — | live `ticket_created` / `ticket_updated` / `ticket_ai_processed` events |

## Demo video

_(Add a link here once recorded — a 60–90s walkthrough showing: login →
running `seed_demo_data.py` → tickets appearing live via WebSocket → AI
summaries filling in → analytics dashboard with the D3 chart.)_