import json
import time
import uuid
from fastapi import Request
from typing import Optional


def log_request(
    request: Request,
    status: int,
    start_time: float,
    *,
    message_id: Optional[str] = None,
    dup: Optional[bool] = None,
    result: Optional[str] = None,
    level: str = "INFO",
):
    log = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "request_id": str(uuid.uuid4()),
        "method": request.method,
        "path": request.url.path,
        "status": status,
        "latency_ms": round((time.time() - start_time) * 1000, 2),
    }

    if message_id is not None:
        log["message_id"] = message_id
    if dup is not None:
        log["dup"] = dup
    if result is not None:
        log["result"] = result

    print(json.dumps(log))
