from datetime import date, datetime

DUE_SOON_DAYS = 7


def _to_date(value) -> date:
    return datetime.fromisoformat(str(value)[:10]).date()


def _status_for(days_until_due: int) -> str:
    if days_until_due < 0:
        return "OVERDUE"
    if days_until_due <= DUE_SOON_DAYS:
        return "DUE_SOON"
    return "OK"


def apply_reference_date(rows):
    """Measure maintenance status from the most recent maintenance record.

    The source data is static, so measuring from today would eventually mark
    every machine overdue. Returns the reference date and the recalculated rows.
    """
    recorded = [_to_date(r["maintenance_date"]) for r in rows if r.get("maintenance_date")]
    if not recorded:
        return None, rows

    reference = max(recorded)
    updated = []
    for row in rows:
        if not row.get("next_due_date"):
            updated.append(row)
            continue
        days = (_to_date(row["next_due_date"]) - reference).days
        updated.append({**row, "days_until_due": days, "maintenance_status": _status_for(days)})
    return reference.isoformat(), updated
