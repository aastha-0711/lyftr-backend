from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional
import hmac
import hashlib
import re
import time

from app.config import WEBHOOK_SECRET
from app.models import init_db, get_db
import app.storage as storage
from app.logging_utils import log_request
from app.metrics import inc, snapshot


app = FastAPI(
    title="Lyftr AI – Backend Assignment",
    description=(
        "A production-style FastAPI service for ingesting signed webhooks, "
        "storing messages idempotently, and exposing analytics endpoints."
    ),
    version="1.0.0",
)


# ---------- Startup ----------
@app.on_event("startup")
def startup():
    init_db()


# ---------- Root ----------
@app.get("/")
def root():
    return {
        "service": "Lyftr AI – Backend Assignment",
        "status": "running",
        "docs": "/docs",
        "health": {
            "live": "/health/live",
            "ready": "/health/ready"
        },
        "endpoints": {
            "webhook": "POST /webhook",
            "messages": "GET /messages",
            "stats": "GET /stats",
            "metrics": "GET /metrics"
        }
    }


# ---------- Models ----------
class WebhookMessage(BaseModel):
    message_id: str = Field(min_length=1)
    from_: str = Field(alias="from")
    to: str
    ts: str
    text: Optional[str] = Field(default=None, max_length=4096)

    @staticmethod
    def is_valid_msisdn(value: str) -> bool:
        return bool(re.fullmatch(r"\+\d+", value))


# ---------- Helpers ----------
def verify_signature(raw_body: bytes, signature: str) -> bool:
    computed = hmac.new(
        WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


# ---------- Webhook ----------
@app.post("/webhook")
async def webhook(request: Request):
    start = time.time()
    inc("webhook_requests_total")

    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    if not signature or not verify_signature(raw_body, signature):
        inc("webhook_invalid_signature_total")
        log_request(
            request,
            401,
            start,
            level="WARN",
            result="invalid_signature",
        )
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    WebhookMessage(**payload)

    message_id = payload["message_id"]

    if (
        not WebhookMessage.is_valid_msisdn(payload.get("from", ""))
        or not WebhookMessage.is_valid_msisdn(payload.get("to", ""))
    ):
        inc("webhook_invalid_msisdn_total")
        log_request(
            request,
            422,
            start,
            level="WARN",
            message_id=message_id,
            result="invalid_msisdn",
        )
        raise HTTPException(status_code=422, detail="Invalid MSISDN format")

    result = storage.insert_message(payload)

    if result == "duplicate":
        inc("webhook_duplicates_total")
    else:
        inc("webhook_created_total")

    log_request(
        request,
        200,
        start,
        level="INFO",
        message_id=message_id,
        dup=(result == "duplicate"),
        result=result,
    )

    return {"status": "ok"}


# ---------- Health ----------
@app.get("/health/live")
def health_live():
    return {"status": "live"}


@app.get("/health/ready")
def health_ready():
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="WEBHOOK_SECRET not set")

    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")

    return {"status": "ready"}


# ---------- Messages ----------
@app.get("/messages")
def get_messages(
    limit: int = 50,
    offset: int = 0,
    from_: Optional[str] = None,
    since: Optional[str] = None,
    q: Optional[str] = None,
):
    inc("messages_requests_total")

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")

    data, total = storage.list_messages(
        limit=limit,
        offset=offset,
        from_msisdn=from_,
        since=since,
        q=q,
    )

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------- Stats ----------
@app.get("/stats")
def stats():
    inc("stats_requests_total")
    return storage.get_stats()


# ---------- Metrics (text/plain) ----------
@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    data = snapshot()
    return "\n".join(f"{k} {v}" for k, v in data.items())
