# Deployment guide

## Production environment variables

| Variable | Required | Notes |
|---|---|---|
| `APP_ENV` | yes | Set to `production`. Enables CORS lockdown and switches the rate limiter to Redis storage. |
| `APP_SECRET_KEY` | yes | Min 16 chars. Used for JWT signing AND Fernet token encryption — rotating it invalidates all OAuth tokens. |
| `DATABASE_URL` | yes | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | yes | `redis://host:6379/0` |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | yes | Typically separate Redis DBs (`/1`, `/2`) |
| `CHROMA_HOST` / `CHROMA_PORT` | yes | Chroma HTTP endpoint |
| `ANTHROPIC_API_KEY` | yes | LLM credentials |
| `ANTHROPIC_MODEL` | no | Defaults to `claude-sonnet-4-6` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | yes | OAuth credentials |
| `GOOGLE_REDIRECT_URI` | yes | Must match the Google Cloud Console exactly |
| `FRONTEND_URL` | yes | Where the OAuth callback redirects on success |
| `ALLOWED_ORIGINS_STR` | yes | Comma-separated list of allowed CORS origins, e.g. `https://app.example.com,https://www.example.com` |
| `RATE_LIMIT_ENABLED` | no | Defaults true. Set false to disable (do not in production). |
| `LOG_LEVEL` | no | `INFO` |
| `LOG_FORMAT` | no | `json` (recommended) or `console` |

## Build the production image

```bash
docker build -f Dockerfile.prod -t email-automation:0.1.0 .
```

The image:
- Multi-stage (wheels in builder, slim runtime).
- Non-root user (`app`).
- Includes a `/api/health` HEALTHCHECK.
- Runs uvicorn with 2 workers + `--proxy-headers` (works behind a reverse proxy).

## Running migrations

```bash
docker run --rm --env-file .env.prod email-automation:0.1.0 alembic upgrade head
```

Run this BEFORE rolling out a new image that introduces schema changes.

## Topology

A minimum production deployment uses 5 process types:

| Process | Image | Command | Replicas (start) |
|---|---|---|---|
| api | `email-automation` | `uvicorn app.main:app --workers 2` | 2+ (horizontal scale) |
| worker | `email-automation` | `celery -A app.celery_app worker --concurrency=4` | 1+ |
| beat | `email-automation` | `celery -A app.celery_app beat` | exactly 1 (schedule must not be duplicated) |
| db | `postgres:16` | – | 1 (with backups; HA via your provider) |
| redis | `redis:7` | – | 1 (with persistence or replicated) |
| chroma | `chromadb/chroma` | – | 1 (persistent volume) |
| frontend | `email-automation-frontend` | `next start` | 2+ |

Reverse proxy (nginx / Cloudflare / ELB) terminates TLS and forwards to the api +
frontend services. Set `--proxy-headers` on uvicorn so request IPs in rate-limit
counters reflect the real client.

## Scaling notes

- **API:** stateless. Horizontal scale freely. Rate-limit counters live in Redis;
  CSRF state lives in Redis — both shared across replicas.
- **Worker:** stateful per-task. `--concurrency=N` runs N parallel tasks per process.
  For LLM-heavy workloads (response_generator, follow-up decider) keep concurrency
  modest (4–8 per worker) to avoid bursting your Anthropic quota.
- **Beat:** must be exactly 1 instance, otherwise periodic tasks duplicate. Use a
  leader-elected sidecar or k8s `StatefulSet` with `replicas: 1`.
- **DB:** size primary by query load. Most write traffic is small JSON. Connection
  pool defaults to `pool_size=10, max_overflow=20` — tune per uvicorn worker count
  so total connections fit within Postgres' `max_connections`.
- **Chroma:** keep on persistent volume. For large user-bases consider Pinecone /
  Qdrant — Chroma's HTTP server is fine for low-to-medium write volume.
- **LLM:** Anthropic enforces tier-based rate limits. Budget for retries (we already
  pass `tenacity`-friendly errors) and consider per-tenant prompt-caching when
  the inbox volume gets large.

## Monitoring

- **Logs:** structlog emits JSON when `LOG_FORMAT=json`. Ship to your aggregator
  (Datadog / Loki / CloudWatch). Each log line carries `request_id`, `method`,
  `path`, `status_code`, `elapsed_ms`.
- **Health probes:**
  - `/api/health` — liveness (returns 200 immediately)
  - `/api/health/db` — DB-only readiness
  - `/api/health/ready` — comprehensive readiness (db + redis + chroma); returns
    503 if any dependency is down. Use this for k8s `readinessProbe`.
- **Metrics:** not wired by default. Drop in `prometheus-fastapi-instrumentator`
  for HTTP metrics; tag with `request_id` from middleware.
- **Tracing:** the request_id is the join key. Add OpenTelemetry by wrapping
  uvicorn and Celery — both auto-instrument with `opentelemetry-instrumentation-*`.

## Backups

- Postgres: nightly `pg_dump` minimum; PITR via WAL archiving recommended.
- Chroma: snapshot the persistent volume.
- Redis: not load-bearing for durable state (only counters + state TTL). Ephemeral
  loss costs at most one OAuth attempt and a temporarily-relaxed rate window.

## Secrets

Never put `APP_SECRET_KEY`, Google OAuth, or `ANTHROPIC_API_KEY` in the image.
Mount via env-file from your orchestrator's secret store (k8s Secret, AWS SSM,
Vault). Verify the Fernet round-trip on startup if you suspect the key changed
unintentionally — `tests/test_security.py:test_encrypt_decrypt_round_trip` is the
canary.

## Known limitations / roadmap

- **No refresh-token rotation:** Google issues long-lived refresh tokens; we do
  not rotate the encryption key automatically. To rotate, you must read all
  encrypted tokens, decrypt with the old key, encrypt with the new, and migrate.
- **No multi-tenant rate limits:** rate limits are per-IP. For SaaS use, switch
  the `key_func` in `app/core/rate_limit.py` to `user.id` (requires the limiter
  to run after auth).
- **MemorySaver fallback:** `app/core/checkpointer.py` falls back to `MemorySaver`
  if `langgraph-checkpoint-postgres` setup fails — in production, treat the
  `checkpointer.postgres.setup_failed` log line as a page-worthy alert.
