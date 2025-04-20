from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatisticsResponse(BaseModel):
    total_users: int
    total_sellers: int
    total_buyers: int
    active_sellers: int  # users who have items
    active_buyers: int  # users who have orders
    total_orders: int
    yearly_orders: int
    monthly_orders: int
    total_profit: float
    yearly_profit: float
    monthly_profit: float
    last_updated: datetime 