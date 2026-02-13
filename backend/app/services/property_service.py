import difflib
import re

from sqlalchemy.orm import Session

from app.repositories.property_repo import PropertyRepository
from app.schemas.chat import PropertyFilter
from app.schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self, repo: PropertyRepository | None = None) -> None:
        self.repo = repo or PropertyRepository()

    def create(self, db: Session, data: PropertyCreate):
        data = data.model_copy(update={"location": data.location.strip()})
        return self.repo.create(db, data)

    def get(self, db: Session, property_id: int):
        return self.repo.get(db, property_id)

    def list_all(self, db: Session):
        return self.repo.list_all(db)

    def list_locations(self, db: Session) -> list[str]:
        return self.repo.list_locations(db)

    def update(self, db: Session, property_id: int, data: PropertyUpdate):
        obj = self.repo.get(db, property_id)
        if not obj:
            return None
        if data.location is not None:
            data = data.model_copy(update={"location": data.location.strip()})
        return self.repo.update(db, obj, data)

    def delete(self, db: Session, property_id: int) -> bool:
        obj = self.repo.get(db, property_id)
        if not obj:
            return False
        self.repo.delete(db, obj)
        return True

    def search(self, db: Session, f: PropertyFilter):
        # normalize
        if f.location:
            f = f.model_copy(update={"location": f.location.strip()})
        if f.locations:
            f = f.model_copy(
                update={"locations": [x.strip() for x in f.locations if isinstance(x, str) and x.strip()]}
            )
        if f.property_type:
            f = f.model_copy(update={"property_type": f.property_type.strip()})
        f = self.normalize_location_from_query(db, query="", f=f)
        return self.repo.search(db, f)

    def search_from_query(self, db: Session, query: str, f: PropertyFilter):
        # normalize
        if f.location:
            f = f.model_copy(update={"location": f.location.strip()})
        if f.locations:
            f = f.model_copy(
                update={"locations": [x.strip() for x in f.locations if isinstance(x, str) and x.strip()]}
            )
        if f.property_type:
            f = f.model_copy(update={"property_type": f.property_type.strip()})
        f = self.normalize_location_from_query(db, query=query, f=f)
        return self.repo.search(db, f), f

    def normalize_location_from_query(self, db: Session, query: str, f: PropertyFilter) -> PropertyFilter:
        """
        Dynamic location normalization with DB-driven fuzzy matching.
        Uses distinct locations from DB (no static city list).
        """
        locations = self.repo.list_locations(db)
        if not locations:
            return f

        # Respect explicit multi-location scope chosen upstream.
        if f.locations:
            valid = [loc for loc in f.locations if any(loc.lower() == k.lower() for k in locations)]
            if valid:
                updates = {"locations": valid}
                if f.keyword:
                    nk = re.sub(r"[^a-z0-9]+", " ", f.keyword.lower()).strip()
                    if any(nk == re.sub(r"[^a-z0-9]+", " ", v.lower()).strip() for v in valid):
                        updates["keyword"] = None
                return f.model_copy(update=updates)

        def _norm(s: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

        norm_to_loc = {_norm(loc): loc for loc in locations if _norm(loc)}
        norm_locations = list(norm_to_loc.keys())

        candidates: list[str] = []
        if f.location:
            candidates.append(f.location)
        if f.keyword:
            candidates.append(f.keyword)

        q = (query or "").lower()
        # Try extracting likely location phrase after common prepositions.
        for m in re.finditer(r"\b(?:in|at|near|around|from)\s+([a-z][a-z\s\-]{1,40})", q):
            phrase = m.group(1)
            phrase = re.split(
                r"\b(under|below|above|over|between|with|for|and|or|upto|max|min|at least|at most)\b",
                phrase,
                maxsplit=1,
            )[0].strip()
            if phrase:
                candidates.append(phrase)

        # Also consider individual words for misspellings like "delh".
        candidates.extend(re.findall(r"[a-z]{3,}", q))

        best_loc = None
        best_score = 0.0
        for c in candidates:
            nc = _norm(c)
            if not nc:
                continue
            if nc in norm_to_loc:
                best_loc = norm_to_loc[nc]
                best_score = 1.0
                break

            # containment usually indicates abbreviations/partials
            for nl in norm_locations:
                if nc in nl or nl in nc:
                    score = 0.92
                    if score > best_score:
                        best_score = score
                        best_loc = norm_to_loc[nl]

            # fuzzy similarity for typos
            for nl in norm_locations:
                score = difflib.SequenceMatcher(None, nc, nl).ratio()
                if score > best_score:
                    best_score = score
                    best_loc = norm_to_loc[nl]

        # conservative threshold to avoid random false positives
        if not best_loc or best_score < 0.80:
            return f

        updates = {"location": best_loc}
        if f.keyword:
            nk = _norm(f.keyword)
            nl = _norm(best_loc)
            if nk == nl or nk in nl or difflib.SequenceMatcher(None, nk, nl).ratio() >= 0.85:
                # keyword is actually location text; drop it to avoid over-filtering
                updates["keyword"] = None
        return f.model_copy(update=updates)
