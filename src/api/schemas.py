from typing import Optional
from pydantic import BaseModel, field_validator


class StyleRequest(BaseModel):
    prompt: str


class RecommendedItem(BaseModel):
    id: str = ""
    name: str = ""
    category: str = ""
    color: str = ""
    price: float = 0.0
    image_url: str = ""
    source: str = ""

    @field_validator("image_url", "id", "name", "category", "color", "source", mode="before")
    @classmethod
    def none_to_empty(cls, v):
        return v if v is not None else ""

    @field_validator("price", mode="before")
    @classmethod
    def none_price(cls, v):
        return v if v is not None else 0.0


class StyleResponse(BaseModel):
    recommended_items: list[RecommendedItem]
    total_price: float = 0.0
    currency: str = "INR"
    stylist_note: str = ""
    agent_reasoning: list[str] = []
