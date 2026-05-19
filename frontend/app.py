import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
PLATFORM_API = os.environ.get("PLATFORM_API_URL", "")


# ---------- Template filters ----------

@app.template_filter("br_int")
def br_int_filter(n):
    if n is None:
        return "—"
    # Format with period as thousands separator (pt-BR style)
    return f"{int(n):,}".replace(",", ".")


@app.template_filter("br")
def br_filter(n):
    if n is None:
        return "—"
    # Format as pt-BR: periods for thousands, comma for decimal
    formatted = f"{n:,.2f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- Helpers ----------

def _get(path):
    return requests.get(PLATFORM_API + path, timeout=10).json()["data"]


def _alerts_unreviewed(alerts_data):
    return sum(1 for a in alerts_data if a.get("status") == "pending")


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S BRT")


def _run_id():
    return datetime.now().strftime("%Y%m_%d")


# ---------- Routes ----------

@app.route("/")
def index():
    equipment = _get("/api/equipment_status")
    budget    = _get("/api/budget-variance")
    alerts    = _get("/api/get_alerts")

    eq_ok       = sum(1 for m in equipment if m["status"] == "OK")
    eq_due_soon = sum(1 for m in equipment if m["status"] == "DUE_SOON")
    eq_overdue  = sum(1 for m in equipment if m["status"] == "OVERDUE")
    total_budget = sum(b["budget_amount_brl"] for b in budget)

    backlog = sorted(
        [m for m in equipment if m["status"] in ("OVERDUE", "DUE_SOON")],
        key=lambda m: m["days_until_due"],
    )[:8]

    top_alerts = sorted(
        [a for a in alerts if a.get("status") == "pending"],
        key=lambda a: -a["deviation_pct"],
    )[:4]

    return render_template(
        "index.html",
        equipment=equipment,
        budget=budget,
        top_alerts=top_alerts,
        backlog=backlog,
        eq_ok=eq_ok,
        eq_due_soon=eq_due_soon,
        eq_overdue=eq_overdue,
        total_budget=total_budget,
        alerts_unreviewed=_alerts_unreviewed(alerts),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/equipment")
def equipment():
    data   = _get("/api/equipment_status")
    alerts = _get("/api/get_alerts")
    return render_template(
        "equipment.html",
        data=data,
        alerts_unreviewed=_alerts_unreviewed(alerts),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/budget")
def budget():
    data   = _get("/api/budget-variance")
    alerts = _get("/api/get_alerts")
    return render_template(
        "budget.html",
        data=data,
        alerts_unreviewed=_alerts_unreviewed(alerts),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/alerts")
def alerts():
    data = _get("/api/get_alerts")
    return render_template(
        "alerts.html",
        data=data,
        alerts_unreviewed=_alerts_unreviewed(data),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/api/post_resolutions", methods=["POST"])
def post_resolutions():
    body = request.get_json() or {}
    transaction_id = body.get("transaction_id")
    resolution = body.get("resolution", "")
    is_legitimate = resolution == "legitimate"
    resp = requests.post(
        PLATFORM_API + "/api/post_resolutions",
        json={"transaction_id": transaction_id, "is_legitimate": is_legitimate},
        timeout=10,
    )
    return jsonify(resp.json()), resp.status_code


if __name__ == "__main__":
    app.run(debug=True)
