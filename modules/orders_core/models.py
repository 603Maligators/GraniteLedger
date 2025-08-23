from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Buyer(BaseModel):
    name: str
    email: Optional[str] = None


class Destination(BaseModel):
    zip: str
    city: str
    state: str
    country: str


class Item(BaseModel):
    sku: str
    name: str
    qty: int = 1
    weight: float


class MoneyTotals(BaseModel):
    subtotal: float
    shipping: float
    tax: float
    grand_total: float


class ShipMethod(BaseModel):
    carrier: str
    service: str
    cost: float
    eta_days: int
    rationale: Optional[str] = None


class HistoryEntry(BaseModel):
    ts: datetime
    event: str
    detail: str


class Order(BaseModel):
    id: str
    external_id: Optional[str] = None
    created_at: datetime
    buyer: Buyer
    destination: Destination
    items: List[Item]
    shipping_tier: str
    computed_weight: float = 0.0
    status: str = "New"
    proposed_shipping_method: Optional[ShipMethod] = None
    approved_shipping_method: Optional[ShipMethod] = None
    tracking_number: Optional[str] = None
    totals: MoneyTotals
    history: List[HistoryEntry] = Field(default_factory=list)
