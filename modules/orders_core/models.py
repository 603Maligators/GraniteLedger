from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

ShippingTier = Literal["Free", "Priority", "HomeDelivery"]
OrderStatus = Literal[
    "New", "Printed", "Addressed", "Bags Pulled",
    "Ship Method Chosen", "Shipped", "Completed"
]


class Buyer(BaseModel):
    name: str
    email: Optional[str] = None


class Destination(BaseModel):
    zip: str
    city: str
    state: str
    country: str = "US"


class Item(BaseModel):
    sku: str
    name: str
    qty: int = 1
    weight: float = 0.0  # pounds per-unit


class ShipMethod(BaseModel):
    carrier: str
    service: str
    cost: float
    eta_days: int
    rationale: str


class MoneyTotals(BaseModel):
    subtotal: float = 0.0
    shipping: float = 0.0
    tax: float = 0.0
    grand_total: float = 0.0


class HistoryEntry(BaseModel):
    ts: datetime = Field(default_factory=datetime.utcnow)
    event: str
    detail: str = ""


class Order(BaseModel):
    id: str
    external_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    buyer: Buyer
    destination: Destination
    items: List[Item] = Field(default_factory=list)

    shipping_tier: ShippingTier = "Free"
    computed_weight: float = 0.0

    status: OrderStatus = "New"

    proposed_shipping_method: Optional[ShipMethod] = None
    approved_shipping_method: Optional[ShipMethod] = None
    tracking_number: Optional[str] = None

    totals: MoneyTotals = Field(default_factory=MoneyTotals)
    history: List[HistoryEntry] = Field(default_factory=list)

    test_flag: bool = False

