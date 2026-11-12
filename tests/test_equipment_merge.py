"""Overlapping equipment names are merged into one canonical item (db_operations.EQUIPMENT_ALIASES).

A fresh build links the canonical item directly; scripts/merge_equipment_aliases.py merges the committed database.
Run: python -m pytest -q tests/test_equipment_merge.py
"""
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from db_operations import EQUIPMENT_ALIASES, equipment_name  # noqa: E402
from recipe_database import RecipeDatabase  # noqa: E402


def _names(conn):
    return {r[0] for r in conn.execute("SELECT name FROM equipment")}


def _equipment_of(conn, recipe):
    return {r[0] for r in conn.execute("SELECT e.name FROM recipe_equipment re JOIN equipment e USING (equipment_id) "
                                       "JOIN recipes r USING (recipe_id) WHERE r.name = ?", (recipe,))}


def test_alias_table():
    assert equipment_name("Strainer") == ("Colander/Strainer", False)
    assert equipment_name("large skillet (optional)") == ("Skillet/Frying Pan", True)
    assert equipment_name("Whisk") == ("Whisk", False)
    for alias, canonical in EQUIPMENT_ALIASES.items():
        assert alias == alias.lower() and canonical.lower() not in EQUIPMENT_ALIASES


def test_fresh_database_uses_canonical_items(tmp_path):
    db = tmp_path / "fresh.db"
    RecipeDatabase(str(db)).initialize_database()
    conn = sqlite3.connect(db)
    try:
        assert not {n.lower() for n in _names(conn)} & set(EQUIPMENT_ALIASES)
        assert "Colander/Strainer" in _equipment_of(conn, "Tzatziki")
        assert "Skillet/Frying Pan" in _equipment_of(conn, "Paella")
    finally:
        conn.close()


def test_merge_on_a_copy_is_idempotent(tmp_path):
    import merge_equipment_aliases as merge
    db = tmp_path / "copy.db"
    shutil.copy(ROOT / "recipe_collection.db", db)
    conn = sqlite3.connect(db)
    links_before = conn.execute("SELECT COUNT(DISTINCT recipe_id) FROM recipe_equipment").fetchone()
    conn.close()
    merge.merge(str(db))
    assert merge.merge(str(db)) == []  # second run changes nothing
    conn = sqlite3.connect(db)
    try:
        assert not {n.lower() for n in _names(conn)} & set(EQUIPMENT_ALIASES)
        assert conn.execute("SELECT COUNT(DISTINCT recipe_id) FROM recipe_equipment").fetchone() == links_before
        assert conn.execute("SELECT COUNT(*) FROM recipe_equipment re LEFT JOIN equipment e USING (equipment_id) "
                            "WHERE e.equipment_id IS NULL").fetchone() == (0,)
        assert "Colander/Strainer" in _equipment_of(conn, "Tzatziki")
        assert "Skillet/Frying Pan" in _equipment_of(conn, "Classic Hamburger")
    finally:
        conn.close()


def test_committed_database_has_no_alias_items():
    conn = sqlite3.connect(f"file:{ROOT / 'recipe_collection.db'}?mode=ro", uri=True)
    try:
        assert not {n.lower() for n in _names(conn)} & set(EQUIPMENT_ALIASES)
    finally:
        conn.close()
