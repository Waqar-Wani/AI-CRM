from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import Base, engine, SessionLocal
from app.models.property import Property


SEED_PROPERTIES: list[dict] = [
    {
        "title": "Modern 2BHK Apartment near Metro",
        "location": "Delhi",
        "price": 8500000,
        "area_sqft": 1150,
        "property_type": "Apartment",
        "description": "Well-lit 2BHK with modular kitchen, close to metro and market.",
    },
    {
        "title": "Spacious 3BHK Apartment with Balcony",
        "location": "Delhi",
        "price": 12500000,
        "area_sqft": 1450,
        "property_type": "Apartment",
        "description": "Family-friendly society, power backup, gym, and security.",
    },
    {
        "title": "South Delhi Residential Plot",
        "location": "Delhi",
        "price": 9500000,
        "area_sqft": 1800,
        "property_type": "Plot",
        "description": "Clear-title plot in a developed pocket with metro access and wide road frontage.",
    },
    {
        "title": "Luxury Villa with Garden",
        "location": "Mumbai",
        "price": 9800000,
        "area_sqft": 1800,
        "property_type": "Villa",
        "description": "Independent villa with private garden, parking, and premium finishes.",
    },
    {
        "title": "Premium Sea-view Villa",
        "location": "Mumbai",
        "price": 18000000,
        "area_sqft": 2600,
        "property_type": "Villa",
        "description": "Sea-view, private terrace, and high-end interiors in a gated community.",
    },
    {
        "title": "Residential Plot near Highway",
        "location": "Pune",
        "price": 4200000,
        "area_sqft": 2200,
        "property_type": "Plot",
        "description": "Clear title plot, good connectivity, ideal for custom construction.",
    },
    {
        "title": "Compact Studio Apartment",
        "location": "Bengaluru",
        "price": 5200000,
        "area_sqft": 650,
        "property_type": "Apartment",
        "description": "Ideal for working professionals, near tech parks and cafes.",
    },
    # LLM-needed scenarios:
    # - City not in heuristic city whitelist (e.g., Gurugram/Noida)
    # - "between/upto/at least" style queries where fallback is weak
    {
        "title": "Skyline Corner Residence",
        "location": "Gurugram",
        "price": 12300000,
        "area_sqft": 1425,
        "property_type": "Apartment",
        "description": "Corner unit with city skyline view, premium clubhouse and co-working lounge.",
    },
    {
        "title": "Canal-side Family Villa",
        "location": "Noida",
        "price": 10500000,
        "area_sqft": 2100,
        "property_type": "Villa",
        "description": "Large villa with double-height living room, landscaped courtyard and EV charging.",
    },
    {
        "title": "Quiet Budget Villa",
        "location": "Noida",
        "price": 7600000,
        "area_sqft": 1650,
        "property_type": "Villa",
        "description": "Gated lane home with terrace deck, utility room and two-car parking.",
    },
    {
        "title": "Lakefront Midrise Homes",
        "location": "Thane",
        "price": 13200000,
        "area_sqft": 1380,
        "property_type": "Apartment",
        "description": "3BHK with podium amenities, jogging track and co-working lounge.",
    },
    {
        "title": "Heritage Courtyard Villa",
        "location": "Jaipur",
        "price": 16800000,
        "area_sqft": 2400,
        "property_type": "Villa",
        "description": "Independent home with private courtyard, servant room and rooftop sit-out.",
    },
    {
        "title": "Riverbend Residential Plot",
        "location": "Ahmedabad",
        "price": 5900000,
        "area_sqft": 2600,
        "property_type": "Plot",
        "description": "Clear-title parcel near arterial road with wide frontage and clean zoning.",
    },
    {
        "title": "Dal View Premium Apartment",
        "location": "Srinagar",
        "price": 9200000,
        "area_sqft": 1280,
        "property_type": "Apartment",
        "description": "Lake-facing apartment with cedar interiors, winter heating and covered parking.",
    },
    {
        "title": "Zabarwan Hillside Villa",
        "location": "Srinagar",
        "price": 15800000,
        "area_sqft": 2350,
        "property_type": "Villa",
        "description": "Independent villa near hillside trails with orchard patch and mountain-facing deck.",
    },
    {
        "title": "Jhelum Riverside Plot",
        "location": "Srinagar",
        "price": 6800000,
        "area_sqft": 2100,
        "property_type": "Plot",
        "description": "Residential plot in a calm riverside pocket with clear approach road and legal papers.",
    },
    {
        "title": "Hudson View Apartment",
        "location": "New York",
        "price": 250000000,
        "area_sqft": 980,
        "property_type": "Apartment",
        "description": "High-rise apartment with skyline views, concierge and subway connectivity.",
    },
    {
        "title": "Brooklyn Townhouse Villa",
        "location": "New York",
        "price": 340000000,
        "area_sqft": 2200,
        "property_type": "Villa",
        "description": "Renovated townhouse with private backyard, basement studio and two-car garage.",
    },
    {
        "title": "Clifton Sea Breeze Apartment",
        "location": "Karachi",
        "price": 42000000,
        "area_sqft": 1500,
        "property_type": "Apartment",
        "description": "Sea-facing apartment near Clifton with secure parking and backup power.",
    },
    {
        "title": "Defence Family Villa Karachi",
        "location": "Karachi",
        "price": 89000000,
        "area_sqft": 3000,
        "property_type": "Villa",
        "description": "Spacious villa in DHA with servant quarter, lawn and rooftop seating.",
    },
    {
        "title": "Canary Wharf Executive Flat",
        "location": "London",
        "price": 175000000,
        "area_sqft": 1100,
        "property_type": "Apartment",
        "description": "Modern apartment close to transport links, riverwalk and business district.",
    },
    {
        "title": "Palm Jumeirah Luxury Villa",
        "location": "Dubai",
        "price": 520000000,
        "area_sqft": 4800,
        "property_type": "Villa",
        "description": "Waterfront villa with private beach access, infinity pool and smart-home system.",
    },
]


def _seed_missing(db: Session) -> None:
    existing_titles = set(db.execute(select(Property.title)).scalars().all())
    inserted = False
    for row in SEED_PROPERTIES:
        if row["title"] in existing_titles:
            continue
        db.add(Property(**row))
        inserted = True
    if inserted:
        db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_missing(db)
    finally:
        db.close()
