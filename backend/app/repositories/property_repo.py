from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.property import Property
from app.schemas.chat import PropertyFilter
from app.schemas.property import PropertyCreate, PropertyUpdate


class PropertyRepository:
    def create(self, db: Session, data: PropertyCreate) -> Property:
        obj = Property(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, property_id: int) -> Property | None:
        return db.get(Property, property_id)

    def list_all(self, db: Session) -> list[Property]:
        return list(db.execute(select(Property).order_by(Property.id.desc())).scalars().all())

    def list_locations(self, db: Session) -> list[str]:
        rows = db.execute(select(Property.location).distinct()).scalars().all()
        return [r for r in rows if r]

    def update(self, db: Session, obj: Property, data: PropertyUpdate) -> Property:
        patch = data.model_dump(exclude_unset=True)
        for k, v in patch.items():
            setattr(obj, k, v)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: Property) -> None:
        db.delete(obj)
        db.commit()

    def search(self, db: Session, f: PropertyFilter) -> list[Property]:
        stmt = select(Property)

        if f.locations:
            stmt = stmt.where(Property.location.in_(f.locations))
        if f.location:
            stmt = stmt.where(Property.location.ilike(f"%{f.location}%"))
        if f.property_type:
            stmt = stmt.where(Property.property_type.ilike(f"%{f.property_type}%"))
        if f.min_price is not None:
            stmt = stmt.where(Property.price >= f.min_price)
        if f.max_price is not None:
            stmt = stmt.where(Property.price <= f.max_price)
        if f.min_area_sqft is not None:
            stmt = stmt.where(Property.area_sqft >= f.min_area_sqft)
        if f.max_area_sqft is not None:
            stmt = stmt.where(Property.area_sqft <= f.max_area_sqft)

        if f.keyword:
            kw = f"%{f.keyword}%"
            stmt = stmt.where(
                or_(
                    Property.title.ilike(kw),
                    Property.description.ilike(kw),
                )
            )

        stmt = stmt.order_by(Property.id.desc())
        return list(db.execute(stmt).scalars().all())
