"""Read-only access to recipe_collection.db for the web app, through the repo's own db_operations.RecipeDAO.

Reads always use a SQLite `mode=ro` connection, so browsing can never change the file; the only writes are the
local-only endpoints in writes.py. RECIPE_DB overrides the database path (the tests point it at a temporary copy).
If the tracked file is missing (fresh checkout without the .db), it is built once with the repo's
RecipeDatabase.initialize_database() in a temporary directory, never in the repo.
"""
import json
import os
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path

from db_operations import RecipeDAO
from recipe_database import RecipeDatabase

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "recipe_collection.db"


def db_path() -> str:
    env = os.environ.get("RECIPE_DB")
    if env:
        return env
    if DB_PATH.exists():
        return str(DB_PATH)
    cache = Path(tempfile.gettempdir()) / "recipe_explorer_web" / "recipe_collection.db"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        RecipeDatabase(str(cache)).initialize_database()
    return str(cache)


@contextmanager
def reader():
    """A RecipeDAO on a read-only connection."""
    dao = RecipeDAO(db_path())
    dao.conn = sqlite3.connect("file:" + Path(dao.db_path).as_posix() + "?mode=ro", uri=True, check_same_thread=False)
    dao.conn.row_factory = sqlite3.Row
    try:
        yield dao
    finally:
        dao.close()


def _links(dao) -> tuple[dict, dict]:
    """recipe_id -> ingredient names, recipe_id -> equipment names (in the DAO's order)."""
    ings: dict = {}
    for rid, name in dao.conn.execute("SELECT ri.recipe_id, i.name FROM recipe_ingredients ri JOIN ingredients i "
                                      "ON ri.ingredient_id = i.ingredient_id ORDER BY ri.id"):
        ings.setdefault(rid, []).append(name)
    equip: dict = {}
    for rid, name in dao.conn.execute("SELECT re.recipe_id, e.name FROM recipe_equipment re JOIN equipment e "
                                      "ON re.equipment_id = e.equipment_id ORDER BY re.optional, e.name"):
        equip.setdefault(rid, []).append(name)
    return ings, equip


LIST_FIELDS = ("recipe_id", "name", "cuisine", "category", "difficulty", "prep_time", "cook_time", "total_time",
               "servings", "description", "instructions", "dietary_tags", "rating")


def recipes() -> list[dict]:
    """Every recipe (sorted by name, as the desktop list) with its ingredient and equipment names for searching."""
    with reader() as dao:
        rows = dao.get_recipes()
        ings, equip = _links(dao)
    return [{**{k: r[k] for k in LIST_FIELDS}, "ingredients": ings.get(r["recipe_id"], []),
             "equipment": equip.get(r["recipe_id"], [])} for r in rows]


def nutrition(text):
    """The nutritional_info JSON as a dict (the desktop app shows the raw text if it is not JSON)."""
    if not text:
        return None
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else {"info": str(v)}
    except (ValueError, TypeError):
        return {"info": text}


def recipe(recipe_id: int) -> dict | None:
    with reader() as dao:
        r = dao.get_recipe(recipe_id)
        if r is None:
            return None
        ings = dao.get_recipe_ingredients(recipe_id)
        equip = dao.get_recipe_equipment(recipe_id)
    return {**r, "nutrition": nutrition(r.get("nutritional_info")), "ingredients": ings,
            "equipment": [{**e, "optional": bool(e["optional"])} for e in equip]}


def ingredients() -> list[dict]:
    with reader() as dao:
        rows = dao.get_ingredients()
        counts = dict(dao.conn.execute("SELECT ingredient_id, COUNT(DISTINCT recipe_id) FROM recipe_ingredients "
                                       "GROUP BY ingredient_id").fetchall())
    return [{**r, "recipes": counts.get(r["ingredient_id"], 0)} for r in rows]


def equipment() -> list[dict]:
    with reader() as dao:
        rows = dao.get_equipment()
        counts = dict(dao.conn.execute("SELECT equipment_id, COUNT(DISTINCT recipe_id) FROM recipe_equipment "
                                       "GROUP BY equipment_id").fetchall())
    return [{**r, "essential": bool(r["essential"]), "recipes": counts.get(r["equipment_id"], 0)} for r in rows]


def cuisines() -> list[dict]:
    with reader() as dao:
        rows = dao.get_cuisines()
        counts = dict(dao.conn.execute("SELECT cuisine, COUNT(*) FROM recipes GROUP BY cuisine").fetchall())
    return [{**r, "recipes": counts.get(r["name"], 0)} for r in rows]


def _recipe_cards(sql: str, arg) -> list[dict]:
    with reader() as dao:
        rows = dao.conn.execute(sql, (arg,)).fetchall()
    return [dict(r) for r in rows]


CARD = "r.recipe_id, r.name, r.cuisine, r.category, r.difficulty, r.total_time, r.description, r.rating"


def recipes_with_ingredient(ingredient_id: int) -> list[dict]:
    return _recipe_cards(f"SELECT DISTINCT {CARD}, ri.quantity, ri.unit, ri.notes FROM recipes r JOIN recipe_ingredients"
                         " ri ON r.recipe_id = ri.recipe_id WHERE ri.ingredient_id = ? ORDER BY r.name", ingredient_id)


def recipes_with_equipment(equipment_id: int) -> list[dict]:
    return _recipe_cards(f"SELECT DISTINCT {CARD} FROM recipes r JOIN recipe_equipment re ON r.recipe_id = re.recipe_id"
                         " WHERE re.equipment_id = ? ORDER BY r.name", equipment_id)


def recipes_in_cuisine(name: str) -> list[dict]:
    return _recipe_cards(f"SELECT {CARD} FROM recipes r WHERE r.cuisine = ? ORDER BY r.name", name)


def stats() -> dict:
    with reader() as dao:
        counts = dao.get_counts()
        counts["categories"] = dao.conn.execute("SELECT COUNT(DISTINCT category) FROM recipes").fetchone()[0]
        counts["recipe_cuisines"] = dao.conn.execute("SELECT COUNT(DISTINCT cuisine) FROM recipes").fetchone()[0]
    return counts
