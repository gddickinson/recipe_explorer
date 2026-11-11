"""Recipe scaling (servings), US-to-metric unit conversion and shopping-list totals. Pure Python, no GUI.

Quantities in the database are text: "2", "1.5", "1/2", "1 1/2", ranges such as "8-10", or words such as "to taste".
Numbers (and both ends of a range) are scaled; words are kept as written. Units are free text too; the US kitchen
units below can be shown in metric. "oz" is taken as a weight ounce (the recipes use it for solids such as cheese,
bacon and canned tomatoes).

web/static/scaling_engine.js is an exact JavaScript port (checked by tests/fixtures/scaling_fixture.json, made by
scripts/make_scaling_fixture.py). Keep the two in step: rounding is always floor(x + 0.5), never round(), because
Python rounds halves to even and JavaScript does not.
"""
import math
import re

# Spellings of the same unit -> one canonical name (used for conversion and for adding up shopping-list lines).
UNIT_ALIASES = {
    "cups": "cup", "lbs": "lb", "pound": "lb", "pounds": "lb", "ounce": "oz", "ounces": "oz",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "teaspoon": "tsp", "teaspoons": "tsp",
    "cans": "can", "sheets": "sheet",
}
# Canonical unit -> plural shown when the amount is above 1.
PLURALS = {"cup": "cups", "lb": "lbs", "can": "cans", "sheet": "sheets"}
# Canonical US unit -> (metric base unit, factor).
METRIC = {"tsp": ("ml", 4.92892), "tbsp": ("ml", 14.7868), "cup": ("ml", 236.588),
          "oz": ("g", 28.3495), "lb": ("g", 453.592)}
BIG = {"ml": "L", "g": "kg"}
FRACTIONS = [(0.0, ""), (1 / 8, "1/8"), (1 / 4, "1/4"), (1 / 3, "1/3"), (3 / 8, "3/8"), (1 / 2, "1/2"), (5 / 8, "5/8"),
             (2 / 3, "2/3"), (3 / 4, "3/4"), (7 / 8, "7/8"), (1.0, "")]

_NUM = re.compile(r"^(\d+(?:\.\d+)?)$")
_FRAC = re.compile(r"^(\d+)/(\d+)$")
_MIXED = re.compile(r"^(\d+)\s+(\d+)/(\d+)$")


def round_to(x: float, decimals: int) -> float:
    k = 10 ** decimals
    return math.floor(x * k + 0.5) / k


def _trim(s: str) -> str:
    return s.rstrip("0").rstrip(".") if "." in s else s


def fmt_decimal(x: float, decimals: int) -> str:
    return _trim(f"{round_to(x, decimals):.{decimals}f}")


def parse_amount(text: str):
    """'2' -> 2.0, '1.5' -> 1.5, '1/2' -> 0.5, '1 1/2' -> 1.5; anything else -> None."""
    t = text.strip()
    m = _NUM.match(t)
    if m:
        return float(m.group(1))
    m = _FRAC.match(t)
    if m:
        return int(m.group(1)) / int(m.group(2)) if int(m.group(2)) else None
    m = _MIXED.match(t)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3)) if int(m.group(3)) else None
    return None


def parse_quantity(text):
    """Quantity text -> (low, high) numbers (equal unless a range such as '8-10'), or None for words/blank."""
    t = str(text or "").strip()
    if not t:
        return None
    parts = re.split(r"\s*(?:-|–|\bto\b)\s*", t)
    if len(parts) == 2:
        lo, hi = parse_amount(parts[0]), parse_amount(parts[1])
        return (lo, hi) if lo is not None and hi is not None else None
    v = parse_amount(t)
    return (v, v) if v is not None else None


def format_amount(x: float) -> str:
    """Kitchen-style number: whole part plus the nearest eighth or third (within 0.02), else up to 2 decimals."""
    if x <= 0:
        return "0"
    whole = math.floor(x + 1e-9)
    frac = x - whole
    best, label = FRACTIONS[0]
    for v, lab in FRACTIONS[1:]:
        if abs(frac - v) < abs(frac - best):
            best, label = v, lab
    if abs(frac - best) > 0.02:
        return fmt_decimal(x, 2)
    if best == 1.0:
        whole += 1
    if not label:
        return str(whole)
    return f"{whole} {label}" if whole else label


def norm_unit(unit) -> str:
    u = str(unit or "").strip().lower()
    return UNIT_ALIASES.get(u, u)


def us_unit(unit, amount: float) -> str:
    """The recipe's own unit text, switched between singular and plural for the common US units."""
    nu = norm_unit(unit)
    if nu in PLURALS and str(unit or "").strip().lower() in (nu, PLURALS[nu]):
        return PLURALS[nu] if amount > 1 + 1e-9 else nu
    return str(unit or "")


def metric_value(x: float) -> str:
    if x >= 100:
        return str(int(math.floor(x / 5 + 0.5) * 5))
    if x >= 10:
        return str(int(math.floor(x + 0.5)))
    return fmt_decimal(x, 1)


def _metric(lo: float, hi: float, base: str):
    """(lo, hi) in ml or g -> (text, unit, lo, hi) in ml/g or, from 1000 up, L/kg."""
    if hi >= 1000:
        lo, hi = lo / 1000, hi / 1000
        text = fmt_decimal(lo, 2) if lo == hi else f"{fmt_decimal(lo, 2)}-{fmt_decimal(hi, 2)}"
        return text, BIG[base], lo, hi
    text = metric_value(lo) if lo == hi else f"{metric_value(lo)}-{metric_value(hi)}"
    return text, base, lo, hi


def _us(lo: float, hi: float, unit):
    text = format_amount(lo) if lo == hi else f"{format_amount(lo)}-{format_amount(hi)}"
    return text, us_unit(unit, hi), lo, hi


def scale_item(quantity, unit, factor: float = 1.0, metric: bool = False) -> dict:
    """One ingredient line scaled by `factor` (new servings / recipe servings), optionally in metric units.

    Returns {quantity, unit, low, high}: the display text and unit, and the numbers behind them (None for words).
    """
    q = parse_quantity(quantity)
    if q is None:
        return {"quantity": str(quantity or ""), "unit": str(unit or ""), "low": None, "high": None}
    lo, hi = q[0] * factor, q[1] * factor
    nu = norm_unit(unit)
    if metric and nu in METRIC:
        base, f = METRIC[nu]
        text, u, lo, hi = _metric(lo * f, hi * f, base)
    else:
        text, u, lo, hi = _us(lo, hi, unit)
    return {"quantity": text, "unit": u, "low": lo, "high": hi}


def scale_recipe_ingredients(ingredients: list, servings_from, servings_to, metric: bool = False) -> list:
    """Each ingredient dict ({name, quantity, unit, ...}) with its quantity/unit replaced by the scaled values."""
    factor = servings_to / servings_from if servings_from and servings_to else 1.0
    out = []
    for ing in ingredients:
        s = scale_item(ing.get("quantity"), ing.get("unit"), factor, metric)
        out.append({**ing, **s, "original": {"quantity": ing.get("quantity"), "unit": ing.get("unit")}})
    return out


def combine(items: list, metric: bool = False) -> list:
    """Shopping-list totals. items: [{name, quantity, unit, factor, recipe}].

    Lines with the same ingredient and the same (canonical; in metric mode: base) unit are added up; words such as
    "to taste" are listed once per distinct text. Sorted by ingredient name, then unit.
    """
    groups: dict = {}
    order = []
    for it in items:
        name = str(it.get("name") or "")
        factor = it.get("factor") or 1.0
        q = parse_quantity(it.get("quantity"))
        nu = norm_unit(it.get("unit"))
        if q is None:
            key = (name.lower(), nu, "text:" + str(it.get("quantity") or "").strip().lower())
        elif metric and nu in METRIC:
            key = (name.lower(), METRIC[nu][0], "num")
        else:
            key = (name.lower(), nu, "num")
        g = groups.get(key)
        if g is None:
            g = groups[key] = {"name": name, "unit": it.get("unit") or "", "quantity": it.get("quantity") or "",
                               "low": 0.0, "high": 0.0, "numeric": q is not None, "recipes": [],
                               "base": METRIC[nu][0] if metric and q is not None and nu in METRIC else None}
            order.append(key)
        if q is not None:
            f = METRIC[nu][1] if metric and nu in METRIC else 1.0
            g["low"] += q[0] * factor * f
            g["high"] += q[1] * factor * f
        rec = it.get("recipe")
        if rec and rec not in g["recipes"]:
            g["recipes"].append(rec)
    out = []
    for key in order:
        g = groups[key]
        if not g["numeric"]:
            text, unit, lo, hi = str(g["quantity"]), str(g["unit"]), None, None
        elif g["base"]:
            text, unit, lo, hi = _metric(g["low"], g["high"], g["base"])
        else:
            text, unit, lo, hi = _us(g["low"], g["high"], g["unit"])
        out.append({"name": g["name"], "quantity": text, "unit": unit, "low": lo, "high": hi, "recipes": g["recipes"]})
    out.sort(key=lambda r: (r["name"].lower(), r["unit"].lower()))
    return out
