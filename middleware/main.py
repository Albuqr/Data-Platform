import os
import secrets
import sys

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

sys.path.append(os.path.join(os.path.dirname(__file__)))

from config import RESOLUTIONS_API_KEY
from services import fx_client
from services import lakehouse_client
from services import maintenance
from services import monitor_client

# ---------- Rate limiter ----------

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------- CORS ----------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://data-platform.albuqr.com",
        "http://localhost:5000",
        "http://localhost:3000",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ---------- Models ----------

class Item(BaseModel):
    transaction_id: str
    is_legitimate: bool

    @field_validator("transaction_id")
    @classmethod
    def transaction_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("transaction_id must be a non-empty string")
        return v

# ---------- Access control ----------

def require_resolutions_key(x_api_key: str | None = Header(default=None)):
    """Only key holders may change Alert data. With no key configured, nobody can."""
    if not RESOLUTIONS_API_KEY or not x_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not secrets.compare_digest(x_api_key.encode(), RESOLUTIONS_API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------- Endpoints ----------

@app.get("/api/budget-variance")
@limiter.limit("30/minute")
def budget_variance(request: Request):
    try:
        return lakehouse_client.get_budget_variance()
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@app.get("/api/equipment_status")
@limiter.limit("30/minute")
def equipment_status(request: Request):
    try:
        payload = lakehouse_client.get_equipment_status()
        rows = payload["data"] if isinstance(payload, dict) else payload
        reference_date, rows = maintenance.apply_reference_date(rows)
        return {"data": rows, "reference_date": reference_date}
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@app.get("/api/fx-rate")
@limiter.limit("30/minute")
def fx_rate(request: Request):
    try:
        return fx_client.get_usd_brl_rate()
    except Exception:
        raise HTTPException(status_code=502, detail="Exchange rate unavailable")


@app.get("/api/sku_economics")
@limiter.limit("30/minute")
def sku_economics(request: Request):
    try:
        return lakehouse_client.get_sku_economics()
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@app.get("/api/get_alerts")
@limiter.limit("30/minute")
def get_alerts(request: Request):
    try:
        return monitor_client.get_alerts()
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream service unavailable")


@app.post("/api/post_resolutions", dependencies=[Depends(require_resolutions_key)])
@limiter.limit("10/minute")
def post_resolutions(item: Item, request: Request):
    try:
        return monitor_client.post_resolutions(item.transaction_id, item.is_legitimate)
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream service unavailable")
