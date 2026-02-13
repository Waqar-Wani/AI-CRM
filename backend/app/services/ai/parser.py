import json

from pydantic import ValidationError

from app.schemas.chat import PropertyFilter


def parse_property_filter(raw_text: str) -> PropertyFilter:
    """
    Parse and validate the model output into PropertyFilter.
    Keeps AI-output handling isolated from DB logic.
    """
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned non-JSON output: {e}") from e

    # Map expected nulls to None and reject extra noise by schema validation.
    try:
        return PropertyFilter.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Invalid filter JSON shape: {e}") from e

