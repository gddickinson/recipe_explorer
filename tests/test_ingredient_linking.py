"""Regression tests: a recipe ingredient must link to the ingredient of the same name.

The old lookup used `name LIKE '%<name>%'` without ORDER BY, so SQLite returned the alphabetically first name
*containing* the text (via the UNIQUE name index): "Onion" linked to "Green Onions", "Milk" to "Coconut Milk",
"Sugar" to "Brown Sugar", "Chicken" to "Chicken Bones". All tests work on temporary databases.

Run: python -m pytest -q tests/test_ingredient_linking.py
"""
import ast
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_operations import RecipeDAO  # noqa: E402
from recipe_database import RecipeDatabase  # noqa: E402


def seed_recipes() -> list[dict]:
    """The recipes_data literal from recipe_database.populate_recipes (the seed data's source of truth)."""
    tree = ast.parse((ROOT / "recipe_database.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "recipes_data":
            return ast.literal_eval(node.value)
    raise AssertionError("recipes_data not found")


def test_fresh_database_links_ingredients_by_exact_name(tmp_path):
    db = tmp_path / "fresh.db"
    RecipeDatabase(str(db)).initialize_database()
    conn = sqlite3.connect(db)
    wrong = []
    for recipe_id, recipe in enumerate(seed_recipes(), 1):
        linked = [r[0] for r in conn.execute(
            "SELECT i.name FROM recipe_ingredients ri JOIN ingredients i USING (ingredient_id) "
            "WHERE ri.recipe_id = ? ORDER BY ri.id", (recipe_id,))]
        want = [ing[0] for ing in recipe["ingredients"]]
        wrong += [(recipe["name"], w, g) for w, g in zip(want, linked) if w.lower() != g.lower()]
        assert len(linked) == len(want), recipe["name"]
    conn.close()
    assert wrong == []


def test_dao_find_or_create_ingredient_prefers_exact_name(tmp_path):
    db = tmp_path / "dao.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ingredients (ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,"
                 " category TEXT)")
    conn.executemany("INSERT INTO ingredients (name, category) VALUES (?, ?)",
                     [("Onion", "Vegetables"), ("Green Onions", "Other"), ("Coconut Milk", "Other")])
    conn.commit()
    conn.close()
    dao = RecipeDAO(str(db))
    dao.connect()
    try:
        assert dao.find_or_create_ingredient("Onion") == 1
        assert dao.find_or_create_ingredient("green onions") == 2
        milk = dao.find_or_create_ingredient("Milk")  # not "Coconut Milk": a new ingredient
        assert milk not in (1, 2, 3)
        assert dao.conn.execute("SELECT name FROM ingredients WHERE ingredient_id = ?", (milk,)).fetchone()[0] == "Milk"
        assert dao.find_or_create_ingredient("Milk") == milk
    finally:
        dao.close()


def test_repair_script_relinks_a_copy_of_the_committed_database(tmp_path):
    import shutil
    sys.path.insert(0, str(ROOT / "scripts"))
    import repair_ingredient_links as rep
    db = tmp_path / "copy.db"
    shutil.copy(ROOT / "recipe_collection.db", db)
    rep.repair(str(db))
    conn = sqlite3.connect(db)
    try:
        assert rep.mislinked(conn) == []
    finally:
        conn.close()
    assert rep.repair(str(db), dry_run=True) == []


def test_committed_database_has_no_mislinked_seed_ingredients():
    sys.path.insert(0, str(ROOT / "scripts"))
    import repair_ingredient_links as rep
    conn = sqlite3.connect(f"file:{ROOT / 'recipe_collection.db'}?mode=ro", uri=True)
    try:
        assert rep.mislinked(conn) == []
    finally:
        conn.close()
