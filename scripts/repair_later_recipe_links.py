"""Relink ingredients of recipes 55-124 that the old LIKE-substring lookup got wrong, from a reviewed mapping table.

These 70 recipes have no seed script in the repo, so their intended ingredient names are not recorded. The mapping in
scripts/fixes/ingredient_links_recipes_55_124.csv was reviewed row by row (quantity, unit, notes, the recipe's
instructions and the dish); each `relink` row names the recipe, the wrongly linked ingredient, the row's quantity and
unit, the intended ingredient and the reason. `keep` rows record candidates that were looked at and left as they are.

Guards: the intended name must be contained in the wrong one (that is the only way the old lookup could produce it),
and each relink row must match exactly one recipe_ingredients row while it is still wrong; afterwards it matches none,
so running the script again changes nothing. The intended ingredient is found by exact name or created, as
db_operations.find_or_create_ingredient_id() does.

Run: python scripts/repair_later_recipe_links.py [--db recipe_collection.db] [--dry-run]
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_operations import find_or_create_ingredient_id  # noqa: E402

MAPPING = ROOT / "scripts" / "fixes" / "ingredient_links_recipes_55_124.csv"


def mapping(action: str = "relink") -> list[dict]:
    with open(MAPPING, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["action"] == action]


def pending(conn: sqlite3.Connection) -> list[tuple]:
    """(row id, mapping row) for every relink still to do; raises if the table and database disagree."""
    out = []
    for m in mapping():
        if m["new"].lower() not in m["old"].lower():
            raise ValueError(f"{m['recipe']}: '{m['new']}' is not contained in '{m['old']}'")
        ids = [r[0] for r in conn.execute(
            "SELECT ri.id FROM recipe_ingredients ri JOIN recipes r ON r.recipe_id = ri.recipe_id "
            "JOIN ingredients i ON i.ingredient_id = ri.ingredient_id WHERE r.name = ? AND i.name = ? "
            "AND COALESCE(ri.quantity, '') = ? AND COALESCE(ri.unit, '') = ?",
            (m["recipe"], m["old"], m["quantity"], m["unit"]))]
        if len(ids) > 1:
            raise ValueError(f"{m['recipe']}: {len(ids)} rows match '{m['old']}' {m['quantity']} {m['unit']}")
        if ids:
            out.append((ids[0], m))
    return out


def repair(db_path: str, dry_run: bool = False) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        todo = pending(conn)
        if not dry_run:
            cur = conn.cursor()
            for row_id, m in todo:
                cur.execute("UPDATE recipe_ingredients SET ingredient_id = ? WHERE id = ?",
                            (find_or_create_ingredient_id(cur, m["new"]), row_id))
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
    for _id, m in todo:
        print(f"{m['recipe']}: {m['old']} -> {m['new']}")
    print(f"{len(todo)} of {len(mapping())} mapped rows {'would be ' if args.dry_run else ''}relinked; "
          f"{len(mapping('keep'))} reviewed candidates kept")


if __name__ == "__main__":
    main()
