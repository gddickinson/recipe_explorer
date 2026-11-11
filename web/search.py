"""Search and filter rules for every list endpoint.

Mirrored exactly by web/static/search_engine.js, which answers the same queries on the static site from the exported
full lists (tests/test_web.py checks both give the same ids). Rules:
- `q`: split into words; every word must occur (case-insensitive substring) in the row's searchable text. For recipes
  that is the desktop search (name, description, instructions) plus cuisine, category, dietary tags, ingredient and
  equipment names.
- exact: the column equals the value. max: the column is a number <= the value (rows without one are dropped, like
  SQL `total_time <= ?`). member: the value is one of the row's list items (case-insensitive). terms: the value is one
  of the comma-separated terms of a text column (case-insensitive; "Vegetarian, contains dairy" has the terms
  "vegetarian" and "contains dairy", so "can be vegan" is not "vegan"). flag: "1" keeps true rows, "0" false rows.
"""

SPECS = {
    "recipes": {"text": ["name", "description", "instructions", "cuisine", "category", "dietary_tags", "ingredients",
                         "equipment"],
                "exact": {"cuisine": "cuisine", "category": "category", "difficulty": "difficulty"},
                "max": {"max_time": "total_time"}, "member": {"ingredient": "ingredients", "equipment": "equipment"},
                "terms": {"diet": "dietary_tags"}, "flag": {}, "id": "recipe_id"},
    "ingredients": {"text": ["name", "category", "description", "substitutes", "nutritional_notes", "allergen_info",
                             "season"],
                    "exact": {"category": "category"}, "max": {}, "member": {}, "terms": {}, "flag": {},
                    "id": "ingredient_id"},
    "equipment": {"text": ["name", "category", "description", "substitutes", "care_tips"],
                  "exact": {"category": "category"}, "max": {}, "member": {}, "terms": {},
                  "flag": {"essential": "essential"}, "id": "equipment_id"},
    "cuisines": {"text": ["name", "region", "description", "characteristics", "common_ingredients", "popular_dishes"],
                 "exact": {"region": "region"}, "max": {}, "member": {}, "terms": {}, "flag": {}, "id": "cuisine_id"},
}
# Dietary terms offered as filters ("contains ..." and "can be ..." terms stay searchable through q).
DIET_TERMS = ("vegetarian", "vegan", "gluten-free", "dairy-free")


def terms(text) -> list[str]:
    return [t.strip().lower() for t in str(text or "").split(",") if t.strip()]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _text(row: dict, fields: list[str]) -> str:
    parts = []
    for f in fields:
        v = row.get(f)
        parts.append(" ".join(str(x) for x in v) if isinstance(v, list) else str(v if v is not None else ""))
    return " ".join(parts).lower()


def _keep(spec: dict, r: dict, params: dict, words: list[str]) -> bool:
    for p, col in spec["exact"].items():
        if params.get(p) not in (None, "") and str(r.get(col)) != str(params[p]):
            return False
    for p, col in spec["max"].items():
        limit = _num(params.get(p))
        if limit is not None and (_num(r.get(col)) is None or _num(r.get(col)) > limit):
            return False
    for p, col in spec["member"].items():
        if params.get(p) and str(params[p]).lower() not in [str(x).lower() for x in r.get(col) or []]:
            return False
    for p, col in spec["terms"].items():
        if params.get(p) and str(params[p]).lower() not in terms(r.get(col)):
            return False
    for p, col in spec["flag"].items():
        v = str(params.get(p) or "")
        if (v == "1" and not r.get(col)) or (v == "0" and r.get(col)):
            return False
    if words:
        text = _text(r, spec["text"])
        return all(w in text for w in words)
    return True


def filter_rows(kind: str, rows: list[dict], params: dict) -> list[dict]:
    spec = SPECS[kind]
    words = str(params.get("q") or "").lower().split()
    return [r for r in rows if _keep(spec, r, params, words)]


def _count(values) -> dict:
    out: dict = {}
    for v in values:
        if v not in (None, ""):
            out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


def facets(kind: str, rows: list[dict]) -> dict:
    """{param: {value: count}} for the drop-down filters of a kind."""
    spec = SPECS[kind]
    out = {p: _count(r.get(col) for r in rows) for p, col in spec["exact"].items()}
    for p, col in spec["member"].items():
        out[p] = _count(x for r in rows for x in dict.fromkeys(r.get(col) or []))
    for p, col in spec["terms"].items():
        counts = _count(t for r in rows for t in dict.fromkeys(terms(r.get(col))))
        out[p] = {t: counts[t] for t in DIET_TERMS if t in counts}
    return out
