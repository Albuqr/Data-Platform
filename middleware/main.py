from pydantic import BaseModel
from fastapi import FastAPI
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from services import lakehouse_client
from services import monitor_client

app = FastAPI()



class Item(BaseModel):
    transaction_id: str
    is_legitimate: bool


@app.get("/api/budget-variance")
def budget_variance():
    return lakehouse_client.get_budget_variance()

@app.get("/api/equipment_status")
def equipment_status():
    return lakehouse_client.get_equipment_status()

@app.get("/api/sku_economics")
def sku_economics():
    return lakehouse_client.get_sku_economics()

@app.get("/api/get_alerts")
def get_alerts():
    return monitor_client.get_alerts()

@app.post("/api/post_resolutions")
def post_resolutions(item: Item):
    return monitor_client.post_resolutions(item.transaction_id, item.is_legitimate)