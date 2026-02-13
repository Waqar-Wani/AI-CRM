from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.property import PropertyRead
from app.services.property_service import PropertyService


router = APIRouter()
service = PropertyService()


@router.get("/properties", response_model=list[PropertyRead])
def list_properties(db: Session = Depends(db_session)):
    return service.list_all(db)

