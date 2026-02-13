from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[int] = mapped_column(Integer, index=True)
    area_sqft: Mapped[int] = mapped_column(Integer, index=True)
    property_type: Mapped[str] = mapped_column(String(30), index=True)  # Apartment/Villa/Plot
    description: Mapped[str] = mapped_column(Text)
