"""Account data model."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class AccountType(str, Enum):
    STOCK = "stock"
    FUND = "fund"
    MARGIN = "margin"

    @property
    def label(self) -> str:
        return {
            "stock": "普通股票账户",
            "fund": "基金账户",
            "margin": "融资融券账户",
        }[self.value]


class AccountRecord(BaseModel):
    account_number: str
    account_type: AccountType
    customer_name: str
    status: str = "active"
