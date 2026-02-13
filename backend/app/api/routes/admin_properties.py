from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate
from app.services.property_service import PropertyService


router = APIRouter(prefix="/properties")
service = PropertyService()


@router.get("", response_model=list[PropertyRead])
def admin_list_properties(db: Session = Depends(db_session)):
    return service.list_all(db)


@router.post("", response_model=PropertyRead)
def admin_add_property(payload: PropertyCreate, db: Session = Depends(db_session)):
    return service.create(db, payload)


@router.put("/{property_id}", response_model=PropertyRead)
def admin_update_property(
    property_id: int, payload: PropertyUpdate, db: Session = Depends(db_session)
):
    obj = service.update(db, property_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return obj


@router.delete("/{property_id}")
def admin_delete_property(property_id: int, db: Session = Depends(db_session)):
    ok = service.delete(db, property_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"ok": True}

