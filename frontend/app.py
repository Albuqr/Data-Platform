import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, g, make_response, redirect, render_template, request

from i18n import DATA_LABELS, JS_KEYS, MONTHS, MONTHS_SHORT, STRINGS

load_dotenv()

app = Flask(__name__)
PLATFORM_API = os.environ.get("PLATFORM_API_URL", "")

LANGUAGES = ("en", "pt")
CURRENCIES = ("BRL", "USD")
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
PAYLOAD_CACHE_SECONDS = 60
FX_CACHE_SECONDS = 10 * 60
FX_RETRY_SECONDS = 60
STATUS_ORDER = {"OVERDUE": 0, "DUE_SOON": 1, "OK": 2}


# ---------- Security headers ----------

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ---------- Upstream ----------

class UpstreamError(Exception):
    pass


# All visitors share this server's address against the API's per-address rate
# limit, so a short cache keeps several simultaneous visitors from exhausting it.
_payload_cache = {}


def _get_payload(path):
    now = time.monotonic()
    cached = _payload_cache.get(path)
    if cached and now < cached[0]:
        return cached[1]
    try:
        response = requests.get(PLATFORM_API + path, timeout=10)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        raise UpstreamError(path)
    _payload_cache[path] = (now + PAYLOAD_CACHE_SECONDS, payload)
    return payload


def _rows(payload):
    return payload["data"] if isinstance(payload, dict) else payload


_fx_cache = {"value": None, "expires": 0.0}


def _get_fx():
    now = time.monotonic()
    if now < _fx_cache["expires"]:
        return _fx_cache["value"]
    try:
        value = _get_payload("/api/fx-rate")
        if not value.get("rate"):
            raise UpstreamError("/api/fx-rate")
        _fx_cache.update(value=value, expires=now + FX_CACHE_SECONDS)
    except (UpstreamError, AttributeError):
        _fx_cache.update(expires=now + FX_RETRY_SECONDS)
    return _fx_cache["value"]


# ---------- Visitor preferences ----------

@app.before_request
def load_preferences():
    lang = request.cookies.get("lang")
    g.lang = lang if lang in LANGUAGES else "en"
    g.fx = None if request.endpoint in ("static", "preferences") else _get_fx()
    currency = request.cookies.get("currency")
    g.currency = "USD" if currency == "USD" and g.fx else "BRL"


def t(key, **values):
    text = STRINGS[g.lang].get(key) or STRINGS["en"].get(key, key)
    return text.format(**values) if values else text


@app.context_processor
def inject_globals():
    return {
        "t": t,
        "lang": g.lang,
        "currency": g.currency,
        "fx": g.fx,
        "js_strings": {key: t(key) for key in JS_KEYS},
    }


@app.route("/preferences", methods=["POST"])
def preferences():
    target = request.form.get("next", "/")
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        target = "/"
    response = make_response(redirect(target, code=303))
    options = {
        "max_age": COOKIE_MAX_AGE,
        "samesite": "Lax",
        "httponly": True,
        "secure": request.is_secure,
    }
    if request.form.get("lang") in LANGUAGES:
        response.set_cookie("lang", request.form["lang"], **options)
    if request.form.get("currency") in CURRENCIES:
        response.set_cookie("currency", request.form["currency"], **options)
    return response


# ---------- Formatting ----------

def _number(value, decimals=0):
    text = f"{value:,.{decimals}f}"
    if g.lang == "pt":
        text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return text


@app.template_filter("num")
def num_filter(value, decimals=0):
    return "—" if value is None else _number(value, decimals)


@app.template_filter("money")
def money_filter(brl, decimals=2):
    if brl is None:
        return "—"
    if g.currency == "USD":
        return f"≈ US$ {_number(brl / g.fx['rate'])}"
    return f"R$ {_number(brl, decimals)}"


@app.template_filter("signed_pct")
def signed_pct_filter(value):
    sign = "+" if value >= 0 else "−"
    return f"{sign}{_number(abs(value), 1)}%"


def _parse_date(value):
    try:
        return datetime.fromisoformat(str(value)[:19])
    except ValueError:
        return None


@app.template_filter("date")
def date_filter(value):
    parsed = _parse_date(value) if value else None
    if not parsed:
        return "—"
    return f"{parsed.day} {MONTHS_SHORT[g.lang][parsed.month - 1]} {parsed.year}"


@app.template_filter("datetime")
def datetime_filter(value):
    parsed = _parse_date(value) if value else None
    if not parsed:
        return "—"
    return f"{date_filter(value)}, {parsed:%H:%M}"


@app.template_filter("month")
def month_filter(month_key):
    if not month_key or len(str(month_key)) != 6:
        return month_key or "—"
    key = str(month_key)
    name = MONTHS[g.lang][int(key[4:]) - 1]
    return f"{name} {key[:4]}" if g.lang == "en" else f"{name} de {key[:4]}"


@app.template_filter("label")
def label_filter(value):
    labels = DATA_LABELS.get(value)
    return labels[g.lang] if labels else value


# ---------- Data shaping ----------

def _remap_alert(a):
    return {
        "transaction_id": a.get("transaction_id"),
        "cost_center": a.get("cost_center"),
        "amount_brl": a.get("amount"),
        "mean_amount_brl": a.get("mean"),
        "deviation_pct": round((a.get("deviation") or 0) * 100, 1),
        "detected_at": a.get("timestamp"),
        "status": "pending" if not a.get("reviewed") else "reviewed",
    }


def _remap_equipment(m):
    return {
        "machine_id": str(m.get("item_id", "")),
        "machine_type": m.get("machine_type"),
        "production_line": m.get("production_line"),
        "last_maintenance": m.get("maintenance_date"),
        "next_due": m.get("next_due_date"),
        "days_until_due": m.get("days_until_due"),
        "status": m.get("maintenance_status"),
    }


def _load_equipment():
    payload = _get_payload("/api/equipment_status")
    rows = [_remap_equipment(m) for m in _rows(payload)]
    rows.sort(key=lambda m: (STATUS_ORDER.get(m["status"], 3), m["days_until_due"] or 0))
    reference_date = payload.get("reference_date") if isinstance(payload, dict) else None
    return rows, reference_date


def _load_budget():
    rows = _rows(_get_payload("/api/budget-variance"))
    latest = max((b.get("month_key") or "" for b in rows), default=None)
    rows = [dict(b) for b in rows if b.get("month_key") == latest]
    rows.sort(key=lambda b: -(b.get("budget_amount_brl") or 0))
    total = sum(b.get("budget_amount_brl") or 0 for b in rows)
    largest = rows[0]["budget_amount_brl"] if rows else 0
    for b in rows:
        amount = b.get("budget_amount_brl") or 0
        b["share_pct"] = amount / total * 100 if total else 0
        b["bar_pct"] = amount / largest * 100 if largest else 0
    return rows, total, latest


def _load_alerts():
    rows = [_remap_alert(a) for a in _rows(_get_payload("/api/get_alerts"))]
    rows.sort(key=lambda a: -abs(a["deviation_pct"]))
    as_of = max((a["detected_at"] for a in rows if a["detected_at"]), default=None)
    return rows, as_of


def _pending_ids(alerts):
    return [a["transaction_id"] for a in alerts if a["status"] == "pending"]


def _status_counts(equipment):
    total = len(equipment)
    rows = [
        {
            "status": status,
            "count": count,
            "pct": count / total * 100 if total else 0,
        }
        for status, count in (
            (s, sum(1 for m in equipment if m["status"] == s)) for s in ("OVERDUE", "DUE_SOON", "OK")
        )
    ]
    # Donut geometry on a pathLength=100 circle: each visible arc is its share
    # minus a small gap, starting half a gap in so gaps are centred on the joins.
    visible = [r for r in rows if r["count"]]
    gap = 1.2 if len(visible) > 1 else 0
    start = 0.0
    for r in rows:
        r["dash"] = r["offset"] = 0
        if r["count"]:
            r["dash"] = round(max(r["pct"] - gap, 0.01), 3)
            r["offset"] = round(-(start + gap / 2), 3)
            start += r["pct"]
    return rows


# ---------- Routes ----------

@app.route("/")
def index():
    equipment, reference_date = _load_equipment()
    budget, total_budget, month = _load_budget()
    alerts, alerts_as_of = _load_alerts()
    counts = _status_counts(equipment)
    backlog = [m for m in equipment if m["status"] in ("OVERDUE", "DUE_SOON")]
    return render_template(
        "index.html",
        total_machines=len(equipment),
        counts=counts,
        eq_overdue=counts[0]["count"],
        eq_due_soon=counts[1]["count"],
        backlog=backlog[:8],
        backlog_total=len(backlog),
        budget=budget,
        total_budget=total_budget,
        month=month,
        alerts=[a for a in alerts if a["status"] == "pending"],
        alerts_as_of=alerts_as_of,
        reference_date=reference_date,
        pending_ids=_pending_ids(alerts),
    )


@app.route("/equipment")
def equipment():
    data, reference_date = _load_equipment()
    alerts, _ = _load_alerts()
    counts = _status_counts(data)
    return render_template(
        "equipment.html",
        data=data,
        counts=counts,
        reference_date=reference_date,
        types=sorted({m["machine_type"] for m in data if m["machine_type"]}),
        lines=sorted({m["production_line"] for m in data if m["production_line"]}),
        pending_ids=_pending_ids(alerts),
    )


@app.route("/budget")
def budget():
    data, total_budget, month = _load_budget()
    alerts, _ = _load_alerts()
    return render_template(
        "budget.html",
        data=data,
        total_budget=total_budget,
        month=month,
        pending_ids=_pending_ids(alerts),
    )


@app.route("/alerts")
def alerts():
    data, as_of = _load_alerts()
    return render_template(
        "alerts.html",
        data=data,
        alerts_as_of=as_of,
        pending_ids=_pending_ids(data),
    )


@app.route("/case-study")
def case_study():
    try:
        alerts_data, _ = _load_alerts()
        pending_ids = _pending_ids(alerts_data)
    except UpstreamError:
        pending_ids = []
    return render_template("case_study.html", pending_ids=pending_ids)


@app.errorhandler(UpstreamError)
def handle_upstream_error(e):
    return render_template("error.html", pending_ids=[]), 502


if __name__ == "__main__":
    app.run(debug=False)
