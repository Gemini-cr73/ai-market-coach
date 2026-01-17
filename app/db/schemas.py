from typing import Any, Dict

from pydantic import BaseModel, EmailStr, Field


class SessionCreate(BaseModel):
    email: EmailStr
    ticker: str = Field(min_length=1, max_length=16)
    period: str = Field(default="1y", max_length=32)
    metrics_json: Dict[str, Any]


class SessionOut(BaseModel):
    id: int
    ticker: str
    period: str
    metrics_json: Dict[str, Any]

    class Config:
        from_attributes = True
