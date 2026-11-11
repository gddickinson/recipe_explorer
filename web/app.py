"""FastAPI web app for Recipe Collection Explorer: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8115, local only). Data is read through web/data.py (read-only
RecipeDAO). `scripts/build_static.py` exports every path in STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep
that list in step with the GET routes below. Query-string variants (filters, ?servings=, /shopping) are answered on
the static site by static_api.js with the same rules (search_engine.js, scaling_engine.js). The POST routes (add, edit
and rate recipes) are local-only.
"""
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import recipe_scaling  # noqa: E402

from . import data, writes  # noqa: E402
from .search import SPECS, facets, filter_rows  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Recipe Collection Explorer")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

LISTS = {"recipes": data.recipes, "ingredients": data.ingredients, "equipment": data.equipment,
         "cuisines": data.cuisines}


def listing(kind: str, params: dict) -> list[dict]:
    return filter_rows(kind, LISTS[kind](), params)


def one(kind: str, item_id: int) -> dict:
    pk = SPECS[kind]["id"]
    row = next((r for r in LISTS[kind]() if r[pk] == item_id), None)
    if row is None:
        raise HTTPException(404, f"unknown {kind} id {item_id}")
    return row


def _servings(value, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return v if 1 <= v <= 1000 else default


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/stats")
def stats():
    return data.stats()


@app.get("/api/facets")
def all_facets():
    """Filter options with counts for every list page."""
    return {kind: facets(kind, fn()) for kind, fn in LISTS.items()}


@app.get("/api/recipes")
def recipes(request: Request):
    return listing("recipes", dict(request.query_params))


@app.get("/api/recipes/{recipe_id}")
def recipe(recipe_id: int, servings: str = "", units: str = "us"):
    """One recipe with its ingredients scaled to `servings` (default: the recipe's own) in US or metric units."""
    r = data.recipe(recipe_id)
    if r is None:
        raise HTTPException(404, f"unknown recipe id {recipe_id}")
    base = r["servings"] or 1
    shown = _servings(servings, base)
    metric = units == "metric"
    r["ingredients"] = recipe_scaling.scale_recipe_ingredients(r["ingredients"], base, shown, metric)
    return {**r, "servings_shown": shown, "units": "metric" if metric else "us"}


@app.get("/api/ingredients")
def ingredients(request: Request):
    return listing("ingredients", dict(request.query_params))


@app.get("/api/ingredients/{item_id}")
def ingredient(item_id: int):
    return {**one("ingredients", item_id), "used_in": data.recipes_with_ingredient(item_id)}


@app.get("/api/equipment")
def equipment(request: Request):
    return listing("equipment", dict(request.query_params))


@app.get("/api/equipment/{item_id}")
def equipment_item(item_id: int):
    return {**one("equipment", item_id), "used_in": data.recipes_with_equipment(item_id)}


@app.get("/api/cuisines")
def cuisines(request: Request):
    return listing("cuisines", dict(request.query_params))


@app.get("/api/cuisines/{item_id}")
def cuisine(item_id: int):
    c = one("cuisines", item_id)
    return {**c, "recipe_list": data.recipes_in_cuisine(c["name"])}


@app.get("/api/search")
def search(q: str = ""):
    """Search every list at once (empty q returns nothing)."""
    if not q.strip():
        return {kind: [] for kind in LISTS}
    return {kind: listing(kind, {"q": q}) for kind in LISTS}


def parse_selection(r: str) -> list[tuple[int, int | None]]:
    """'12:4,7' -> [(12, 4), (7, None)] (recipe id and servings; None = the recipe's own)."""
    out = []
    for part in (r or "").split(","):
        rid, _, srv = part.strip().partition(":")
        if rid.strip().isdigit():
            out.append((int(rid), int(srv) if srv.strip().isdigit() and int(srv) > 0 else None))
    return out


@app.get("/api/shopping")
def shopping(r: str = "", units: str = "us"):
    """Shopping list for chosen recipes (?r=id:servings,...): per-recipe scaled lines and combined totals."""
    metric = units == "metric"
    chosen, items = [], []
    for rid, srv in parse_selection(r):
        rec = data.recipe(rid)
        if rec is None:
            continue
        base = rec["servings"] or 1
        shown = srv or base
        chosen.append({"recipe_id": rid, "name": rec["name"], "servings": shown, "base_servings": base,
                       "ingredients": recipe_scaling.scale_recipe_ingredients(rec["ingredients"], base, shown, metric)})
        items += [{"name": i["name"], "quantity": i["quantity"], "unit": i["unit"], "factor": shown / base,
                   "recipe": rec["name"]} for i in rec["ingredients"]]
    return {"recipes": chosen, "items": recipe_scaling.combine(items, metric), "units": "metric" if metric else "us"}


# --- local-only writes (never exported; the static site shows needsServer()) ---------------------------------------
def _write(fn, *args):
    try:
        return fn(*args)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except LookupError as e:
        raise HTTPException(404, str(e))


@app.post("/api/recipes")
def recipe_add(form: dict):
    return {"recipe_id": _write(writes.add_recipe, form)}


@app.post("/api/recipes/{recipe_id}")
def recipe_edit(recipe_id: int, form: dict):
    _write(writes.edit_recipe, recipe_id, form)
    return {"recipe_id": recipe_id}


@app.post("/api/recipes/{recipe_id}/rating")
def recipe_rate(recipe_id: int, form: dict):
    return {"recipe_id": recipe_id, "rating": _write(writes.rate_recipe, recipe_id, form.get("rating"))}


def _detail_paths() -> list[str]:
    return [f"/{kind}/{row[SPECS[kind]['id']]}" for kind, fn in LISTS.items() for row in fn()]


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/stats", "/facets"] + [f"/{kind}" for kind in LISTS] + _detail_paths()
