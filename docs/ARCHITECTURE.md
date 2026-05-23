# Architecture

## Components

```mermaid
flowchart LR
  subgraph Client
    UI[Next.js dashboard]
  end

  subgraph API[FastAPI]
    R[Routes]
    MW[Middleware: request_id, rate_limit, CORS]
    AG[LangGraph workflow]
  end

  subgraph Workers[Celery]
    BEAT[Beat]
    W[Worker]
  end

  subgraph Data
    PG[(Postgres)]
    RD[(Redis)]
    CH[(Chroma)]
  end

  GMAIL[Gmail API]
  LLM[Anthropic API]

  UI -- "Bearer JWT" --> R
  R --> MW
  MW --> AG
  AG -- "classify / draft" --> LLM
  AG -- "retrieve / upsert" --> CH
  AG -- "users, emails, drafts" --> PG
  AG -- "checkpoints" --> PG
  R -- "OAuth state" --> RD
  R -- "rate-limit counters" --> RD
  BEAT --> W
  W -- "sync, follow-ups" --> GMAIL
  W -- "LLM decisions" --> LLM
  W -- "writes" --> PG
  AG -- "send" --> GMAIL
```

## Agent workflow (LangGraph)

```mermaid
flowchart TD
  START((start)) --> ER[email_reader]
  ER --> CL[classifier]
  CL -- "is_spam" --> LOG[logger]
  CL -- "else" --> RE[retriever]
  RE --> RG[response_generator]
  RG -- "auto_approve" --> SEND[sender]
  RG -- "else" --> AG{{approval_gate ⏸ interrupt}}
  AG -- "approved" --> SEND
  AG -- "rejected" --> LOG
  SEND --> LOG
  LOG --> END((end))
```

Pause point: `interrupt_before=["approval_gate"]`. On resume, the API calls
`graph.aupdate_state(...)` to set `approval_status`, then `graph.ainvoke(None, config)`
to continue.

## Data model

```mermaid
erDiagram
  USERS ||--o{ EMAILS : "owns"
  USERS ||--o{ DRAFTS : "owns"
  USERS ||--o{ FOLLOWUPS : "owns"
  USERS ||--o{ ACTIVITY_LOGS : "owns"
  EMAILS ||--o{ DRAFTS : "replied by"
  EMAILS ||--o{ FOLLOWUPS : "scheduled for"
  DRAFTS ||--o{ FOLLOWUPS : "linked draft"

  USERS {
    uuid id PK
    string email UK
    string google_refresh_token "Fernet-encrypted"
    bool auto_send_enabled
    float auto_send_threshold
  }
  EMAILS {
    uuid id PK
    uuid user_id FK
    string message_id UK
    string thread_id
    string category
    string urgency
    jsonb entities
  }
  DRAFTS {
    uuid id PK
    uuid user_id FK
    uuid email_id FK
    string status "pending_approval, approved, sent, rejected"
    float confidence_score
    string tone
  }
  FOLLOWUPS {
    uuid id PK
    uuid email_id FK
    uuid draft_id FK
    timestamp scheduled_for
    string status
  }
  ACTIVITY_LOGS {
    uuid id PK
    uuid email_id FK
    uuid draft_id FK
    string category
    string approval_status
    bool sent
    jsonb payload
  }
```

## Request lifecycle

1. Client sends `Authorization: Bearer <JWT>` to `/api/...`.
2. `RequestContextMiddleware` generates a `request_id` (or honors incoming `X-Request-ID`),
   binds it to the structlog contextvars, logs `http.request.start`.
3. `SlowAPIMiddleware` evaluates the per-route limit (counter in Redis when configured).
4. CORS middleware applies origin checks.
5. Route handler executes; for protected routes, `get_current_user` validates the JWT
   and loads the user from Postgres.
6. On completion, middleware appends `X-Request-ID` and logs `http.request.end` with
   `status_code` and `elapsed_ms`.

## Token security

- Google `refresh_token` is encrypted with Fernet before being stored on the `users` row.
- The Fernet key is derived from `APP_SECRET_KEY` via SHA-256 → base64. Rotating
  `APP_SECRET_KEY` invalidates all stored tokens — users must re-authorize.
- JWT (HS256) is signed with the same `APP_SECRET_KEY`; default TTL 7 days.
- OAuth `state` is single-use, Redis-backed with a 10-minute TTL (falls back to
  in-process memory only when Redis is unreachable; log line surfaces the misconfig).
