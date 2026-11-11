"""Relink seed recipes whose ingredients were linked by the old LIKE-substring lookup (see db_operations).

For every recipe in recipe_database.py's `recipes_data` (matched by name), each ingredient row is compared, in order,
with the seed entry; where the linked ingredient's name differs (e.g. "Green Onions" for "Onion"), the row is pointed
at the ingredient with the seed's exact name (created if missing, like a fresh build would). Nothing else changes.
Recipes that are not in recipes_data (added later by other means) are left alone: their intended names are unknown.

Run: python scripts/repair_ingredient_links.py [--db recipe_collection.db] [--dry-run]
"""
import argparse
import ast
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_operations import find_or_create_ingredient_id  # noqa: E402


def seed_recipes() -> list[dict]:
    """The `recipes_data` literal from recipe_database.populate_recipes."""
    tree = ast.parse((ROOT / "recipe_database.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "recipes_data":
            return ast.literal_eval(node.value)
    raise RuntimeError("recipes_data not found in recipe_database.py")


def mislinked(conn: sqlite3.Connection) -> list[tuple]:
    """(row id, recipe name, linked name, seed name) for every seed ingredient row linked to the wrong name."""
    out = []
    for recipe in seed_recipes():
        row = conn.execute("SELECT recipe_id FROM recipes WHERE name = ?", (recipe["name"],)).fetchone()
        if not row:
            continue
        links = conn.execute("SELECT ri.id, i.name FROM recipe_ingredients ri JOIN ingredients i USING (ingredient_id)"
                             " WHERE ri.recipe_id = ? ORDER BY ri.id", (row[0],)).fetchall()
        for (link_id, linked), ing in zip(links, recipe["ingredients"]):
            if linked.lower() != ing[0].lower():
                out.append((link_id, recipe["name"], linked, ing[0]))
    return out


def repair(db_path: str, dry_run: bool = False) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        bad = mislinked(conn)
        if not dry_run:
            cur = conn.cursor()
            for link_id, _recipe, _linked, name in bad:
                cur.execute("UPDATE recipe_ingredients SET ingredient_id = ? WHERE id = ?",
                            (find_or_create_ingredient_id(cur, name), link_id))
            conn.commit()
        return bad
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(ROOT / "recipe_collection.db"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    bad = repair(args.db, args.dry_run)
    for _id, recipe, linked, name in bad:
        print(f"{recipe}: {linked} -> {name}")
    print(f"{len(bad)} ingredient rows {'would be ' if args.dry_run else ''}relinked")


if __name__ == "__main__":
    main()
