"""Day 19: a pretend "Port API" that is busy on purpose, to watch retries live.

Run:   python -m uvicorn tools.fake_port:app --port 9000
Each blueprint read answers: 429 (Retry-After: 2), 429 (Retry-After: 1), 503, then 200.
POST /reset starts the sequence again.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="fake-port")
SCRIPT = [(429, {"Retry-After": "2"}), (429, {"Retry-After": "1"}), (503, {}), (200, {})]
state = {"calls": 0}


@app.post("/v1/auth/access_token")
def token() -> dict:
    return {"accessToken": "fake-token", "expiresIn": 3600}


@app.get("/v1/blueprints/{identifier}")
def blueprint(identifier: str):
    status, headers = SCRIPT[min(state["calls"], len(SCRIPT) - 1)]
    state["calls"] += 1
    if status != 200:
        return JSONResponse({"error": "busy"}, status_code=status, headers=headers)
    return {"ok": True, "blueprint": {"identifier": identifier, "title": identifier.title()}}


@app.post("/reset")
def reset() -> dict:
    state["calls"] = 0
    return {"reset": True}
