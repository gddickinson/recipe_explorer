"""Write tests/fixtures/scaling_fixture.json: recipe_scaling.py outputs that web/static/scaling_engine.js must match.

Cases: every distinct (quantity, unit) pair in recipe_collection.db (read-only) plus hand-written edge cases, at
several scale factors, in US and metric units; and shopping-list totals for a few recipe combinations.

Run: python scripts/make_scaling_fixture.py      (tests/test_web.py checks the committed file is current)
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import recipe_scaling as rs  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "scaling_fixture.json"
FACTORS = [0.25, 0.5, 1, 1.5, 2, 3, 1.75, 2 / 3]
EXTRA = [("1 1/2", "cups"), ("2 to 3", "tbsp"), ("1/0", "cup"), ("", ""), ("to taste", ""), ("3", "Tablespoons"),
         ("12", "ounces"), ("0.1", "tsp"), ("40", "cup"), ("2.5", "pounds"), ("1", "Cup"), ("7", "lb"), ("1–2", "can"),
         ("500", "g"), ("1/3", "sheets")]
# Shopping-list combinations: (recipe ids, servings per recipe as a factor).
COMBOS = [[(1, 1), (2, 2)], [(23, 1.5), (24, 1), (26, 0.5)], [(50, 2), (53, 1), (6, 1)], [(41, 1), (65, 1), (106, 3)],
          [(37, 1), (52, 2), (12, 1), (9, 0.5)]]


def pairs(conn) -> list:
    rows = conn.execute("SELECT DISTINCT quantity, unit FROM recipe_ingredients ORDER BY quantity, unit").fetchall()
    return [[q or "", u or ""] for q, u in rows] + [list(p) for p in EXTRA]


def items(conn, combo) -> list:
    out = []
    for rid, factor in combo:
        name = conn.execute("SELECT name FROM recipes WHERE recipe_id = ?", (rid,)).fetchone()[0]
        for ing, q, u in conn.execute("SELECT i.name, ri.quantity, ri.unit FROM recipe_ingredients ri JOIN ingredients i"
                                      " USING (ingredient_id) WHERE ri.recipe_id = ? ORDER BY ri.id", (rid,)):
            out.append({"name": ing, "quantity": q or "", "unit": u or "", "factor": factor, "recipe": name})
    return out


def build() -> dict:
    conn = sqlite3.connect(f"file:{ROOT / 'recipe_collection.db'}?mode=ro", uri=True)
    try:
        scale = [{"in": [q, u, f, m], "out": rs.scale_item(q, u, f, m)}
                 for q, u in pairs(conn) for f in FACTORS for m in (False, True)]
        combos = []
        for combo in COMBOS:
            its = items(conn, combo)
            combos += [{"items": its, "metric": m, "out": rs.combine(its, m)} for m in (False, True)]
    finally:
        conn.close()
    return {"scale": scale, "combine": combos}


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(data['scale'])} scaling cases, {len(data['combine'])} shopping lists -> {OUT}")
