import json, os
from dataclasses import dataclass
from typing import Dict, Any, Tuple

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

@dataclass
class EsrsItem:
    code: str
    schema: Dict[str, Any]

_registry: Dict[str, EsrsItem] = {}

def load_registry() -> Dict[str, EsrsItem]:
    global _registry
    if _registry:
        return _registry
    if not os.path.isdir(SCHEMA_DIR):
        return _registry
    for fn in os.listdir(SCHEMA_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(SCHEMA_DIR, fn), "r", encoding="utf-8") as f:
                data = json.load(f)
                _registry[data["code"]] = EsrsItem(code=data["code"], schema=data)
    return _registry

def validate_value(code: str, value) -> Tuple[bool, str | None]:
    reg = load_registry()
    item = reg.get(code)
    if not item:
        return False, f"Unbekannter esrs_code: {code}"
    for r in item.schema.get("rules", []):
        if r["name"] == "non_negative":
            if value is not None and value < r["value"]:
                return False, "Wert muss >= 0 sein."
    return True, None
