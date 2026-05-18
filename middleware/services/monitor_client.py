import httpx

from config import MONITOR_API_URL


def get_alerts():
    url = MONITOR_API_URL + "/alerts"

    with httpx.Client() as client:
        response = client.get(url)

        response.raise_for_status()

        return response.json()

def post_resolutions(transaction_id, is_legitimate):
    url = MONITOR_API_URL + "/resolutions"

    with httpx.Client() as client:
        response = client.post(url, json = {"transaction_id": transaction_id, "is_legitimate": is_legitimate})

        response.raise_for_status()

        return response.json()