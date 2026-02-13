from pydantic import BaseModel, Field


class PropertyBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=0)
    area_sqft: int = Field(ge=0)
    property_type: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, min_length=1, max_length=100)
    price: int | None = Field(default=None, ge=0)
    area_sqft: int | None = Field(default=None, ge=0)
    property_type: str | None = Field(default=None, min_length=1, max_length=30)
    description: str | None = Field(default=None, min_length=1)


class PropertyRead(PropertyBase):
    id: int

    class Config:
        from_attributes = True
