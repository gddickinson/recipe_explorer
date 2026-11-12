"""Merge overlapping equipment items into one canonical item each (db_operations.EQUIPMENT_ALIASES).

For every equipment row whose name is an alias (e.g. "Strainer" -> "Colander/Strainer", "Large Skillet" ->
"Skillet/Frying Pan"), its recipe links are re-pointed to the canonical item (a link the recipe already has is not
duplicated; it stays optional only if both were optional) and the alias row is deleted. Running it again changes
nothing. The mapping table lives in db_operations.py so fresh builds link the canonical items directly.

Run: python scripts/merge_equipment_aliases.py [--db recipe_collection.db] [--dry-run]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_operations import EQUIPMENT_ALIASES  # noqa: E402


def merge(db_path: str, dry_run: bool = False) -> list[tuple]:
    """(alias name, canonical name, links moved) for each alias item merged."""
    conn = sqlite3.connect(db_path)
    out = []
    try:
        cur = conn.cursor()
        for alias_id, alias in cur.execute("SELECT equipment_id, name FROM equipment").fetchall():
            canonical = EQUIPMENT_ALIASES.get(alias.lower())
            if not canonical:
                continue
            row = cur.execute("SELECT equipment_id FROM equipment WHERE name = ? COLLATE NOCASE", (canonical,)).fetchone()
            if row is None:
                raise ValueError(f"canonical equipment '{canonical}' is missing")
            links = cur.execute("SELECT id, recipe_id, optional FROM recipe_equipment WHERE equipment_id = ?",
                                (alias_id,)).fetchall()
            out.append((alias, canonical, len(links)))
            if dry_run:
                continue
            for link_id, recipe_id, optional in links:
                have = cur.execute("SELECT id, optional FROM recipe_equipment WHERE recipe_id = ? AND equipment_id = ?",
                                   (recipe_id, row[0])).fetchone()
                if have:
                    cur.execute("UPDATE recipe_equipment SET optional = ? WHERE id = ?",
                                (int(bool(have[1]) and bool(optional)), have[0]))
                    cur.execute("DELETE FROM recipe_equipment WHERE id = ?", (link_id,))
                else:
                    cur.execute("UPDATE recipe_equipment SET equipment_id = ? WHERE id = ?", (row[0], link_id))
            cur.execute("DELETE FROM equipment WHERE equipment_id = ?", (alias_id,))
        conn.commit()
        return out
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=str(ROOT / "recipe_collection.db"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    done = merge(args.db, args.dry_run)
    for alias, canonical, n in done:
        print(f"{alias} -> {canonical} ({n} recipe link{'s' if n != 1 else ''})")
    print(f"{len(done)} equipment items {'would be ' if args.dry_run else ''}merged")


if __name__ == "__main__":
    main()
