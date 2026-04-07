from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from src.kaven.kaven import LOG_DIR, run_once

app = FastAPI(title="Kaven Web API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kaven-web-api"}


@app.get("/runs/latest")
def latest_run() -> dict[str, Any]:
    today_file = LOG_DIR / f"maven_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
    if not today_file.exists():
        raise HTTPException(status_code=404, detail="No run log found for today")

    last_line = None
    with today_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last_line = line

    if not last_line:
        raise HTTPException(status_code=404, detail="Log file is empty")

    return json.loads(last_line)


@app.post("/runs/once")
async def trigger_run_once() -> dict[str, Any]:
    return await run_once()


@app.get("/runs/files")
def list_run_files() -> dict[str, list[str]]:
    files = sorted([p.name for p in Path(LOG_DIR).glob("maven_*.jsonl")])
    return {"files": files}
