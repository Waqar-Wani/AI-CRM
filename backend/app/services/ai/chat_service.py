import json
import re

from app.schemas.chat import PropertyFilter
from app.services.ai.llm_client import LLMClient
from app.services.ai.parser import parse_property_filter
from app.services.ai.prompt import SYSTEM_PROMPT_NL_TO_FILTER, user_prompt


def _heuristic_fallback(query: str) -> PropertyFilter:
    """
    Demo fallback when no API key is set.
    Extracts a couple of common patterns (city, type, under/over, sqft).
    """
    q = query.lower()
    location = None
    for city in ["mumbai", "delhi", "pune", "bengaluru", "bangalore", "hyderabad", "chennai"]:
        if city in q:
            location = "Bengaluru" if city in ["bengaluru", "bangalore"] else city.title()
            break

    ptype = None
    if "villa" in q:
        ptype = "Villa"
    elif "apartment" in q or "flat" in q:
        ptype = "Apartment"
    elif "plot" in q:
        ptype = "Plot"

    # price: crude INR handling for demo; expects explicit digits + optional crore/lakh.
    max_price = None
    min_price = None
    m = re.search(r"(under|below|max)\s+([\d\.]+)\s*(crore|cr|lakh|lac)?", q)
    if m:
        val = float(m.group(2))
        unit = m.group(3)
        mult = 1
        if unit in ["crore", "cr"]:
            mult = 10_000_000
        elif unit in ["lakh", "lac"]:
            mult = 100_000
        max_price = int(val * mult)

    m = re.search(r"(above|over|min)\s+([\d\.]+)\s*(crore|cr|lakh|lac)?", q)
    if m:
        val = float(m.group(2))
        unit = m.group(3)
        mult = 1
        if unit in ["crore", "cr"]:
            mult = 10_000_000
        elif unit in ["lakh", "lac"]:
            mult = 100_000
        min_price = int(val * mult)

    min_area = None
    max_area = None
    m = re.search(r"above\s+(\d+)\s*(sqft|sq ft|square feet)", q)
    if m:
        min_area = int(m.group(1))
    m = re.search(r"under\s+(\d+)\s*(sqft|sq ft|square feet)", q)
    if m:
        max_area = int(m.group(1))

    # simple keyword extraction for phrases like "near metro"
    keyword = None
    m = re.search(r"near\s+([a-z0-9 ]+)", q)
    if m:
        # take first word after "near"
        keyword = m.group(1).strip().split()[0]

    return PropertyFilter(
        location=location,
        property_type=ptype,
        min_price=min_price,
        max_price=max_price,
        min_area_sqft=min_area,
        max_area_sqft=max_area,
        keyword=keyword,
    )


class ChatService:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    async def nl_to_filter(self, query: str) -> PropertyFilter:
        f, _ = await self.nl_to_filter_with_source(query)
        return f

    async def nl_to_filter_with_source(self, query: str) -> tuple[PropertyFilter, str]:
        try:
            raw = await self.llm.nl_to_json(SYSTEM_PROMPT_NL_TO_FILTER, user_prompt(query))
            f = parse_property_filter(raw)
            parser_source = "llm"
        except Exception:
            # For demo reliability: fallback when key missing / API fails / parsing fails.
            f = _heuristic_fallback(query)
            parser_source = "heuristic"

        # Post-process: if keyword is still empty, try to infer one heuristically
        if not f.keyword:
            f = self._add_keyword_from_query(f, query)
        return f, parser_source

    async def refine_location_scope(
        self, query: str, f: PropertyFilter, known_locations: list[str]
    ) -> PropertyFilter:
        """
        LLM-assisted geo resolution against known DB locations.
        - Maps regional/typo geo terms to a known location when possible.
        - Expands broad country/state intent to multiple known locations.
        """
        if not known_locations:
            return f

        # If we already have an exact known location and no geo-keyword conflict, keep it.
        if f.location and any(f.location.lower() == loc.lower() for loc in known_locations):
            return f

        system_prompt = (
            "You resolve geographic scope for real-estate search.\n"
            "Given a user query, current parsed filter, and known DB locations, return ONLY JSON:\n"
            '{"scope":"single|many|all|none","location":string|null,"locations":[string],'
            '"clear_keyword":boolean}\n'
            "Rules:\n"
            "- scope=single: choose exactly one location from known_locations and set location.\n"
            "- scope=many: choose multiple locations from known_locations when query targets "
            "a broader geography (country/state/region).\n"
            "- scope=all: use only when query clearly means entire inventory across known_locations.\n"
            "- scope=none: no clear geography intent.\n"
            "- location must be null unless scope=single.\n"
            "- locations must be an array of values from known_locations when scope=many or scope=all.\n"
            "- clear_keyword=true only when current keyword is geographic and should not be used "
            "as text keyword filter.\n"
            "- If query mentions a geography not present as exact location, infer best matching "
            "subset from known_locations.\n"
            "- Output strictly valid JSON and nothing else."
        )
        user_content = json.dumps(
            {
                "query": query,
                "current_filter": f.model_dump(),
                "known_locations": known_locations,
            },
            ensure_ascii=True,
        )

        try:
            raw = await self.llm.nl_to_json(system_prompt, user_content)
            out = json.loads(raw)
        except Exception:
            return f

        scope = str(out.get("scope", "")).strip().lower()
        chosen_location = out.get("location")
        chosen_locations = out.get("locations")
        clear_keyword = bool(out.get("clear_keyword", False))

        updates: dict = {}
        if scope == "single" and isinstance(chosen_location, str):
            # Accept only locations known to DB.
            match = next(
                (loc for loc in known_locations if loc.lower() == chosen_location.strip().lower()),
                None,
            )
            if match:
                updates["location"] = match
                updates["locations"] = None
        elif scope in {"many", "all"} and isinstance(chosen_locations, list):
            valid_many = []
            seen = set()
            for candidate in chosen_locations:
                if not isinstance(candidate, str):
                    continue
                match = next(
                    (loc for loc in known_locations if loc.lower() == candidate.strip().lower()),
                    None,
                )
                if match and match.lower() not in seen:
                    valid_many.append(match)
                    seen.add(match.lower())
            if scope == "all" and not valid_many:
                valid_many = known_locations[:]
            if valid_many:
                updates["location"] = None
                updates["locations"] = valid_many

        if clear_keyword:
            updates["keyword"] = None

        return f.model_copy(update=updates) if updates else f

    @staticmethod
    def _add_keyword_from_query(f: PropertyFilter, query: str) -> PropertyFilter:
        """
        Best-effort extraction of a generic keyword when the model didn't set one.
        This helps queries like "Milkiyat" or "properties on Milkiyat" still filter.
        """
        q = query.lower()
        tokens = re.findall(r"[a-z0-9]+", q)
        stop = {
            "show",
            "me",
            "properties",
            "property",
            "under",
            "below",
            "above",
            "over",
            "between",
            "and",
            "or",
            "in",
            "near",
            "with",
            "without",
            "the",
            "a",
            "an",
            "sqft",
            "square",
            "feet",
            "flat",
            "flats",
            "villa",
            "villas",
            "apartment",
            "apartments",
            "plot",
            "plots",
            "lakh",
            "lac",
            "crore",
            "cr",
        }
        cities = {"mumbai", "delhi", "pune", "bengaluru", "bangalore", "hyderabad", "chennai"}
        for t in tokens:
            if t.isdigit():
                continue
            if t in stop or t in cities:
                continue
            # use first non-stopword as keyword
            return f.model_copy(update={"keyword": t})
        return f
