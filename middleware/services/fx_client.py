import time

import httpx

FX_URL = "https://api.frankfurter.dev/v1/latest"
CACHE_SECONDS = 6 * 60 * 60
RETRY_AFTER_FAILURE_SECONDS = 5 * 60

_cached = None
_next_fetch_at = 0.0


def get_usd_brl_rate():
    """Return the daily USD to BRL reference rate, or raise if none has been fetched.

    A failed refresh keeps serving the last known rate, which carries its own date.
    """
    global _cached, _next_fetch_at

    now = time.monotonic()
    if now < _next_fetch_at:
        if _cached is None:
            raise RuntimeError("Exchange rate unavailable")
        return _cached

    try:
        response = httpx.get(FX_URL, params={"base": "USD", "symbols": "BRL"}, timeout=5)
        response.raise_for_status()
        payload = response.json()
        _cached = {
            "base": "USD",
            "quote": "BRL",
            "rate": payload["rates"]["BRL"],
            "date": payload["date"],
            "source": "Frankfurter",
        }
        _next_fetch_at = now + CACHE_SECONDS
    except Exception:
        _next_fetch_at = now + RETRY_AFTER_FAILURE_SECONDS
        if _cached is None:
            raise
    return _cached
