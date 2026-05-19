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
    result = requests.get(PLATFORM_API + path, timeout=10).json()
    return result["data"] if isinstance(result, dict) else result


def _remap_alert(a):
    deviation = a.get("deviation", 1) or 1
    reviewed  = a.get("reviewed", 0)
    return {
        "transaction_id": a.get("transaction_id"),
        "cost_center":    a.get("cost_center"),
        "amount_brl":     a.get("amount"),
        "mean_amount_brl": a.get("mean"),
        "deviation_pct":  round((deviation - 1) * 100, 1),
        "detected_at":    a.get("timestamp"),
        "status":         "pending" if reviewed == 0 else "reviewed",
        "resolution":     None,
    }


def _remap_equipment(m):
    maint_date = m.get("maintenance_date", "") or ""
    if "T" in maint_date:
        maint_date = maint_date.split("T")[0]
    return {
        "machine_id":      str(m.get("item_id", "")),
        "machine_type":    m.get("machine_type"),
        "production_line": m.get("production_line"),
        "last_maintenance": maint_date,
        "next_due":        m.get("next_due_date"),
        "days_until_due":  m.get("days_until_due"),
        "status":          m.get("maintenance_status"),
    }


def _remap_budget(b):
    return {
        "cost_center":       b.get("cost_center"),
        "cost_center_label": b.get("cost_center"),   # API has no separate label
        "budget_amount_brl": b.get("budget_amount_brl"),
        "actual_amount_brl": None,
        "variance_brl":      b.get("variance_brl"),
        "status":            b.get("status_flag"),
        "month":             b.get("month_key"),
    }


def _alerts_unreviewed(alerts_data):
    return sum(1 for a in alerts_data if a.get("status") == "pending")


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S BRT")


def _run_id():
    return datetime.now().strftime("%Y%m_%d")


# ---------- Routes ----------

@app.route("/")
def index():
    equipment = [_remap_equipment(m) for m in _get("/api/equipment_status")]
    budget    = [_remap_budget(b)    for b in _get("/api/budget-variance")]
    alerts    = [_remap_alert(a)     for a in _get("/api/get_alerts")]

    eq_ok       = sum(1 for m in equipment if m["status"] == "OK")
    eq_due_soon = sum(1 for m in equipment if m["status"] == "DUE_SOON")
    eq_overdue  = sum(1 for m in equipment if m["status"] == "OVERDUE")
    total_budget = sum(b["budget_amount_brl"] for b in budget)

    backlog = sorted(
        [m for m in equipment if m["status"] in ("OVERDUE", "DUE_SOON")],
        key=lambda m: m["days_until_due"],
    )[:8]

    top_alerts = sorted(
        [a for a in alerts if a["status"] == "pending"],
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
    data   = [_remap_equipment(m) for m in _get("/api/equipment_status")]
    alerts = [_remap_alert(a)     for a in _get("/api/get_alerts")]
    return render_template(
        "equipment.html",
        data=data,
        alerts_unreviewed=_alerts_unreviewed(alerts),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/budget")
def budget():
    data   = [_remap_budget(b) for b in _get("/api/budget-variance")]
    alerts = [_remap_alert(a)  for a in _get("/api/get_alerts")]
    return render_template(
        "budget.html",
        data=data,
        alerts_unreviewed=_alerts_unreviewed(alerts),
        last_updated=_now(),
        run_id=_run_id(),
    )


@app.route("/alerts")
def alerts():
    data = [_remap_alert(a) for a in _get("/api/get_alerts")]
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
