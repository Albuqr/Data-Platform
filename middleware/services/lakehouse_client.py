import httpx

from config import LAKEHOUSE_API_URL


def get_budget_variance():
    url = LAKEHOUSE_API_URL + "/budget-variance"

    with httpx.Client() as client:
        response = client.get(url)

        response.raise_for_status()

        return response.json()

def get_equipment_status():
    url = LAKEHOUSE_API_URL + "/equipment_status"

    with httpx.Client() as client:
        response = client.get(url)

        response.raise_for_status()

        return response.json()

def get_sku_economics():
    url = LAKEHOUSE_API_URL + "/sku_economics"

    with httpx.Client() as client:
        response = client.get(url)

        response.raise_for_status()

        return response.json()