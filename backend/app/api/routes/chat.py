from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.ai.chat_service import ChatService
from app.services.property_service import PropertyService


router = APIRouter()
chat_service = ChatService()
property_service = PropertyService()


@router.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(payload: ChatQueryRequest, db: Session = Depends(db_session)):
    f, parser_source = await chat_service.nl_to_filter_with_source(payload.message)
    known_locations = property_service.list_locations(db)
    f = await chat_service.refine_location_scope(payload.message, f, known_locations)
    results, f = property_service.search_from_query(db, payload.message, f)
    return {
        "interpreted_filter": f,
        "parser_source": parser_source,
        "results": [
            {
                "id": p.id,
                "title": p.title,
                "location": p.location,
                "price": p.price,
                "area_sqft": p.area_sqft,
                "property_type": p.property_type,
                "description": p.description,
            }
            for p in results
        ],
    }
