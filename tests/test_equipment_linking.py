"""Regression tests: every piece of equipment a seed recipe names must be linked to it.

The seed script only linked equipment whose exact name was already in the equipment table and silently dropped the
rest ("Rolling Pin", "Pastry Brush", "Piping Bag", "Steamer", ...). Names ending in " (optional)" are links with
optional = 1 to the equipment without the suffix. All tests work on temporary databases or read-only.

Run: python -m pytest -q tests/test_equipment_linking.py
"""
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from db_operations import split_optional  # noqa: E402
from recipe_database import RecipeDatabase  # noqa: E402
from repair_ingredient_links import seed_recipes  # noqa: E402


def missing_equipment(conn) -> list:
    """(recipe, equipment name) for every seed equipment entry that has no matching link."""
    out = []
    for recipe in seed_recipes():
        row = conn.execute("SELECT recipe_id FROM recipes WHERE name = ?", (recipe["name"],)).fetchone()
        linked = {(n.lower(), bool(o)) for n, o in conn.execute(
            "SELECT e.name, re.optional FROM recipe_equipment re JOIN equipment e USING (equipment_id) "
            "WHERE re.recipe_id = ?", (row[0],))}
        for name in recipe["equipment"]:
            base, optional = split_optional(name)
            if (name.lower(), False) not in linked and (base.lower(), optional) not in linked:
                out.append((recipe["name"], name))
    return out


def test_split_optional():
    assert split_optional("Rolling Pin (optional)") == ("Rolling Pin", True)
    assert split_optional("Pastry Brush") == ("Pastry Brush", False)


def test_fresh_database_links_every_seed_equipment(tmp_path):
    db = tmp_path / "fresh.db"
    RecipeDatabase(str(db)).initialize_database()
    conn = sqlite3.connect(db)
    try:
        assert missing_equipment(conn) == []
        names = {r[0] for r in conn.execute("SELECT name FROM equipment")}
        assert {"Rolling Pin", "Pastry Brush", "Piping Bag", "Steamer"} <= names
        assert "Rolling Pin (optional)" not in names and "Blender (optional)" not in names
        opt = conn.execute("SELECT re.optional FROM recipe_equipment re JOIN equipment e USING (equipment_id) "
                           "JOIN recipes r USING (recipe_id) WHERE r.name = 'Butter Chicken' AND e.name = 'Blender'"
                           ).fetchone()
        assert opt == (1,)
    finally:
        conn.close()


def test_repair_script_links_a_copy_of_the_committed_database(tmp_path):
    import repair_equipment_links as rep
    db = tmp_path / "copy.db"
    shutil.copy(ROOT / "recipe_collection.db", db)
    rep.repair(str(db))
    conn = sqlite3.connect(db)
    try:
        assert missing_equipment(conn) == []
    finally:
        conn.close()
    assert rep.repair(str(db), dry_run=True) == []


def test_committed_database_has_no_missing_seed_equipment():
    conn = sqlite3.connect(f"file:{ROOT / 'recipe_collection.db'}?mode=ro", uri=True)
    try:
        assert missing_equipment(conn) == []
    finally:
        conn.close()
