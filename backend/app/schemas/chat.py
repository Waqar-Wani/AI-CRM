from pydantic import BaseModel, Field


class PropertyFilter(BaseModel):
    location: str | None = None
    locations: list[str] | None = None
    property_type: str | None = None

    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    min_area_sqft: int | None = Field(default=None, ge=0)
    max_area_sqft: int | None = Field(default=None, ge=0)
    keyword: str | None = None


class ChatQueryRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatQueryResponse(BaseModel):
    interpreted_filter: PropertyFilter
    parser_source: str
    results: list[dict]
