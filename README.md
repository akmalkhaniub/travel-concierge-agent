# Travel Concierge Agent

A consumer-facing voice agent that calls airlines or hotels on behalf of users, navigates IVR menus, waits on hold, and bridges the user to a live representative once a human answers.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                     │
│        (App or SMS: "Change my flight from Monday to Tuesday")           │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │  POST /requests
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    REQUEST HANDLER (FastAPI)                              │
│                                                                          │
│  POST /requests          — submit a hold-for-me request                  │
│  GET  /requests/:id      — check status                                  │
│  POST /requests/:id/cancel — abort the call                              │
│                                                                          │
│         ┌───────────────────────────────────────────┐                   │
│         │           AUTOGEN ORCHESTRATOR             │                   │
│         │                                            │                   │
│         │  Agent 1: IVR Navigator                    │                   │
│         │  Agent 2: Hold Monitor                     │                   │
│         │  Agent 3: Bridge Controller                │                   │
│         └──────────────────┬─────────────────────────┘                  │
│                            │                                             │
│                            ▼                                             │
│              ┌───────────────────────────┐                              │
│              │  OUTBOUND CALL            │                              │
│              │  (MessageBird)            │                              │
│              │                           │                              │
│              │  Dial airline/hotel       │                              │
│              │  customer service number  │                              │
│              └─────────────┬─────────────┘                             │
│                            │                                             │
│                            ▼                                             │
│              ┌───────────────────────────┐                              │
│              │  IVR NAVIGATION           │                              │
│              │                           │                              │
│              │  LLM listens to prompts   │                              │
│              │  "Press 1 for Support"    │                              │
│              │  Sends correct DTMF tones │                              │
│              └─────────────┬─────────────┘                             │
│                            │  reaches hold queue                        │
│                            ▼                                             │
│              ┌───────────────────────────┐                              │
│              │  HOLD MONITOR             │                              │
│              │  (AssemblyAI LeMUR)       │                              │
│              │                           │                              │
│              │  Detect: hold music       │──▶ continue waiting          │
│              │  Detect: silence burst    │                              │
│              │  Detect: "Hello, how      │──▶ HUMAN DETECTED            │
│              │          can I help?"     │                              │
│              └─────────────┬─────────────┘                             │
│                            │  human agent answers                       │
│                            ▼                                             │
│              ┌───────────────────────────┐                              │
│              │  USER CALLBACK            │                              │
│              │  (MessageBird)            │                              │
│              │                           │                              │
│              │  Call user's phone        │                              │
│              │  Bridge both calls        │                              │
│              │  User ◀──▶ Representative │                              │
│              └───────────────────────────┘                              │
│                                                                          │
│  ┌───────────────────┐                                                  │
│  │  Playwright        │  Backup: search flight info                     │
│  │  Browser Agent     │  if phone system is unavailable                 │
│  └───────────────────┘                                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python | ML ecosystem for audio intelligence |
| Agent Framework | Microsoft AutoGen | Multi-agent orchestration (IVR, hold, bridge) |
| Telephony | MessageBird | Outbound calls and call bridging |
| Audio Intelligence | AssemblyAI LeMUR | Real-time audio classification (music vs. speech) |
| TTS | Azure Cognitive Services | Neural voice for IVR navigation responses |
| Browser Automation | Playwright | Fallback flight/hotel search via web |

## Quick Start

```bash
cd travel-concierge-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Configure via environment variables:

```bash
export MESSAGEBIRD_API_KEY=...
export ASSEMBLYAI_API_KEY=...
export AZURE_SPEECH_KEY=...
export AZURE_SPEECH_REGION=eastus
```

## API Examples

### Submit a hold-for-me request
```bash
curl -X POST http://localhost:8000/requests \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+15551234567",
    "target_number": "+18005551234",
    "task": "Change flight AA1234 from Monday May 12 to Tuesday May 13",
    "provider": "american_airlines"
  }'
```

### Check request status
```bash
curl http://localhost:8000/requests/req_abc123
```

## Design Decisions

- **AutoGen multi-agent**: IVR navigation, hold monitoring, and call bridging are separate agents, each with focused responsibilities and independent retry logic.
- **AssemblyAI LeMUR for hold detection**: Classifies audio in real time to distinguish hold music from a human greeting, which is the critical transition point in the entire flow.
- **MessageBird over Twilio**: MessageBird's Programmable Voice API supports call bridging natively, simplifying the two-leg conference when a human answers.
- **Playwright fallback**: If the airline phone system is down or wait times exceed a threshold, the agent falls back to web-based flight management via browser automation.
