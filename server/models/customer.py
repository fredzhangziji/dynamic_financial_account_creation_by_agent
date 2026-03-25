"""Customer data model."""

from __future__ import annotations

from pydantic import BaseModel


class CustomerInfo(BaseModel):
    name: str | None = None
    id_type: str = "身份证"
    id_number: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    occupation: str | None = None
    annual_income: str | None = None
