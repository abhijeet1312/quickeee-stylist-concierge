from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "INR"
    image_url: str = ""
    category: str  # "tops" or "bottoms"
    sub_category: str = ""  # "t-shirt", "shirt", "pants", "shorts"
    color: str = ""
    description: str = ""
    source: str = ""  # "h&m" or "myntra"
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_searchable_text(self) -> str:
        """Combine all fields into a single searchable string."""
        parts = [
            self.name,
            self.category,
            self.sub_category,
            self.color,
            self.description,
            f"{self.price} {self.currency}",
            self.source,
        ]
        return " ".join(p for p in parts if p)

    def to_metadata(self) -> dict:
        """Extract metadata for vector DB filtering."""
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "category": self.category,
            "sub_category": self.sub_category,
            "color": self.color,
            "source": self.source,
            "image_url": self.image_url,
        }
