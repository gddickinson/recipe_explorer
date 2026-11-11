"""Local-only writes for the web app: add a recipe, edit a recipe, rate a recipe.

They go through the repo's db_operations.RecipeDAO (the same insert/update code the desktop app's data layer uses) on
the database the server reads (RECIPE_DB, else recipe_collection.db). They are never exported to, or possible on, the
static GitHub Pages site. Validation follows the desktop Add Recipe form: name, cuisine, category and instructions
are required; times and servings are whole numbers; total time = prep + cook.
"""
from db_operations import RecipeDAO, parse_ingredient_line

from .data import db_path

DIFFICULTIES = ("Easy", "Medium", "Hard")


def _int(value, label: str, low: int = 0) -> int:
    try:
        v = int(str(value).strip() or 0)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number")
    if v < low:
        raise ValueError(f"{label} must be at least {low}")
    return v


def clean(form: dict) -> dict:
    """Validated recipe fields plus parsed ingredient rows; raises ValueError with a message for the user."""
    f = {k: str(form.get(k) or "").strip() for k in ("name", "cuisine", "category", "difficulty", "description",
                                                    "instructions", "tips")}
    if not all(f[k] for k in ("name", "cuisine", "category", "instructions")):
        raise ValueError("Please fill in all required fields: name, cuisine, category and instructions")
    if f["difficulty"] and f["difficulty"] not in DIFFICULTIES:
        raise ValueError("Difficulty must be Easy, Medium or Hard")
    f["difficulty"] = f["difficulty"] or "Medium"
    f["prep_time"] = _int(form.get("prep_time"), "Prep time")
    f["cook_time"] = _int(form.get("cook_time"), "Cook time")
    f["servings"] = _int(form.get("servings") or 4, "Servings", 1)
    f["total_time"] = f["prep_time"] + f["cook_time"]
    rows, bad = [], []
    for line in str(form.get("ingredients") or "").splitlines():
        if line.strip():
            parsed = parse_ingredient_line(line)
            (rows if parsed else bad).append(parsed or line.strip())
    if bad:
        raise ValueError("Could not read ingredient line(s): " + "; ".join(bad))
    f["rows"] = rows
    return f


def _dao() -> RecipeDAO:
    dao = RecipeDAO(db_path())
    dao.connect()
    return dao


FIELDS = ("name", "cuisine", "category", "difficulty", "prep_time", "cook_time", "total_time", "servings",
          "description", "instructions", "tips")


def add_recipe(form: dict) -> int:
    f = clean(form)
    dao = _dao()
    try:
        rid = dao.insert_recipe(*(f[k] for k in FIELDS), source="Web app")
        dao.replace_recipe_ingredients(rid, f["rows"])
        return rid
    finally:
        dao.close()


def edit_recipe(recipe_id: int, form: dict) -> None:
    f = clean(form)
    dao = _dao()
    try:
        if dao.get_recipe(recipe_id) is None:
            raise LookupError(f"unknown recipe {recipe_id}")
        dao.update_recipe(recipe_id, *(f[k] for k in FIELDS))
        dao.replace_recipe_ingredients(recipe_id, f["rows"])
    finally:
        dao.close()


def rate_recipe(recipe_id: int, rating) -> float:
    try:
        r = float(rating)
    except (TypeError, ValueError):
        raise ValueError("Rating must be 1-5")
    if not 1 <= r <= 5:
        raise ValueError("Rating must be 1-5")
    dao = _dao()
    try:
        if dao.get_recipe(recipe_id) is None:
            raise LookupError(f"unknown recipe {recipe_id}")
        dao.update_recipe_rating(recipe_id, r)
        return r
    finally:
        dao.close()
