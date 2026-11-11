"""Add the equipment links the old seed script dropped (equipment missing from the equipment table).

For every recipe in recipe_database.py's `recipes_data` (matched by name), each listed equipment name that has no link
is resolved with db_operations.find_or_create_equipment_id() (adding the equipment, e.g. "Rolling Pin", if needed;
"X (optional)" links X with optional = 1) and linked, exactly as a fresh build now does. Existing links are untouched.
Recipes not in recipes_data (added by other means) are left alone.

Run: python scripts/repair_equipment_links.py [--db recipe_collection.db] [--dry-run]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from db_operations import find_or_create_equipment_id, split_optional  # noqa: E402
from repair_ingredient_links import seed_recipes  # noqa: E402


def missing(conn: sqlite3.Connection) -> list[tuple]:
    """(recipe_id, recipe name, equipment name as listed) for every seed equipment entry without a link."""
    out = []
    for recipe in seed_recipes():
        row = conn.execute("SELECT recipe_id FROM recipes WHERE name = ?", (recipe["name"],)).fetchone()
        if not row:
            continue
        linked = {(n.lower(), bool(o)) for n, o in conn.execute(
            "SELECT e.name, re.optional FROM recipe_equipment re JOIN equipment e USING (equipment_id) "
            "WHERE re.recipe_id = ?", (row[0],))}
        for name in recipe["equipment"]:
            base, optional = split_optional(name)
            if (name.lower(), False) not in linked and (base.lower(), optional) not in linked:
                out.append((row[0], recipe["name"], name))
    return out


def repair(db_path: str, dry_run: bool = False) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        todo = missing(conn)
        if not dry_run:
            cur = conn.cursor()
            for recipe_id, _recipe, name in todo:
                equip_id, optional = find_or_create_equipment_id(cur, name)
                cur.execute("INSERT INTO recipe_equipment (recipe_id, equipment_id, optional) VALUES (?, ?, ?)",
                            (recipe_id, equip_id, int(optional)))
            conn.commit()
        return todo
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(ROOT / "recipe_collection.db"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    todo = repair(args.db, args.dry_run)
    for _id, recipe, name in todo:
        print(f"{recipe}: + {name}")
    print(f"{len(todo)} equipment links {'would be ' if args.dry_run else ''}added")


if __name__ == "__main__":
    main()
