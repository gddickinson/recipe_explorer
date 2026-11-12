"""Repair of recipes 55-124's ingredient links (scripts/repair_later_recipe_links.py + its reviewed mapping table).

Run: python -m pytest -q tests/test_later_recipe_links.py
"""
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import repair_later_recipe_links as rep  # noqa: E402


def _rows(db, table):
    conn = sqlite3.connect(db)
    try:
        return set(conn.execute(f"SELECT * FROM {table}"))
    finally:
        conn.close()


def test_mapping_table_is_complete_and_consistent():
    relinks = rep.mapping()
    assert len(relinks) == 75 and rep.mapping("keep")
    for m in relinks:
        assert m["recipe"] and m["old"] and m["new"] and m["reason"], m
        assert m["new"].lower() in m["old"].lower(), m  # the only way the old LIKE lookup could produce 'old'


def test_repair_on_a_copy_is_limited_and_idempotent(tmp_path):
    db = tmp_path / "copy.db"
    shutil.copy(ROOT / "recipe_collection.db", db)
    before = {t: _rows(db, t) for t in ("recipes", "ingredients", "recipe_ingredients", "equipment", "recipe_equipment")}
    rep.repair(str(db))
    assert rep.repair(str(db)) == []  # second run changes nothing
    after = {t: _rows(db, t) for t in before}
    assert after["recipes"] == before["recipes"] and after["equipment"] == before["equipment"]
    assert after["recipe_equipment"] == before["recipe_equipment"]
    assert before["ingredients"] <= after["ingredients"]  # only additions (e.g. Lamb, Lemon, Oil, Tonkatsu)
    changed = before["recipe_ingredients"] - after["recipe_ingredients"]
    assert all(row[1] > 54 for row in changed)  # recipe_id: the seed recipes are untouched
    conn = sqlite3.connect(db)
    try:
        assert rep.pending(conn) == []
        osso = conn.execute("SELECT i.name FROM recipe_ingredients ri JOIN recipes r USING (recipe_id) JOIN ingredients i "
                            "USING (ingredient_id) WHERE r.name = 'Osso Buco'").fetchall()
        assert ("Onion",) in osso and ("Green Onions",) not in osso and ("Lemon",) in osso
    finally:
        conn.close()


def test_committed_database_is_repaired():
    conn = sqlite3.connect(f"file:{ROOT / 'recipe_collection.db'}?mode=ro", uri=True)
    try:
        assert rep.pending(conn) == []
    finally:
        conn.close()
