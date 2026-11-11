"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# --- Recipe Collection Explorer: project-specific API tests ---------------------------------------------------------
import hashlib  # noqa: E402
import json  # noqa: E402

from web import data  # noqa: E402
from web.app import LISTS  # noqa: E402
from web.search import SPECS  # noqa: E402


def _md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def _counts():
    import sqlite3
    conn = sqlite3.connect(f"file:{data.DB_PATH}?mode=ro", uri=True)
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("recipes", "ingredients", "equipment", "cuisines")}
    finally:
        conn.close()


def test_counts_match_database():
    s = client.get("/api/stats").json()
    assert {k: s[k] for k in ("recipes", "ingredients", "equipment", "cuisines")} == _counts()
    for kind in LISTS:
        assert len(client.get(f"/api/{kind}").json()) == _counts()[kind]


def test_database_opened_read_only():
    before = _md5(data.DB_PATH)
    with data.reader() as dao:
        with pytest.raises(Exception):
            dao.conn.execute("UPDATE recipes SET name = 'x'")
    for path in STATIC_ENDPOINTS[:40]:
        client.get("/api" + path)
    client.get("/api/shopping", params={"r": "1:8,2"})
    assert _md5(data.DB_PATH) == before


def test_filters():
    it = client.get("/api/recipes", params={"cuisine": "Italian"}).json()
    assert it and all(r["cuisine"] == "Italian" for r in it)
    quick = client.get("/api/recipes", params={"max_time": "30"}).json()
    assert quick and all(r["total_time"] <= 30 for r in quick)
    vegan = client.get("/api/recipes", params={"diet": "vegan"}).json()
    assert vegan and all("vegan" in [t.strip().lower() for t in r["dietary_tags"].split(",")] for r in vegan)
    milk = {r["name"] for r in client.get("/api/recipes", params={"ingredient": "milk"}).json()}
    assert "Mac and Cheese" in milk and "Moussaka" in milk  # after the ingredient-link repair
    wok = client.get("/api/recipes", params={"equipment": "Wok or Large Skillet"}).json()
    assert wok and all("Wok or Large Skillet" in r["equipment"] for r in wok)
    ess = client.get("/api/equipment", params={"essential": "1"}).json()
    assert ess and all(e["essential"] for e in ess)
    assert client.get("/api/recipes", params={"q": "zzzz-none"}).json() == []
    res = client.get("/api/search", params={"q": "basil"}).json()
    assert set(res) == set(LISTS) and res["recipes"] and res["ingredients"]
    assert client.get("/api/search", params={"q": " "}).json() == {k: [] for k in LISTS}


def test_details_and_links():
    for path in ("/api/recipes/99999", "/api/ingredients/99999", "/api/equipment/99999", "/api/cuisines/99999"):
        assert client.get(path).status_code == 404
    mac = next(r for r in client.get("/api/recipes").json() if r["name"] == "Mac and Cheese")
    d = client.get(f"/api/recipes/{mac['recipe_id']}").json()
    assert [i["name"] for i in d["ingredients"]][:4] == ["Macaroni", "Butter", "Flour", "Milk"]
    assert d["nutrition"]["calories"] and d["servings_shown"] == d["servings"]
    milk = next(i for i in client.get("/api/ingredients", params={"q": "milk"}).json() if i["name"] == "Milk")
    used = {r["name"] for r in client.get(f"/api/ingredients/{milk['ingredient_id']}").json()["used_in"]}
    assert "Mac and Cheese" in used
    italian = next(c for c in client.get("/api/cuisines").json() if c["name"] == "Italian")
    assert len(client.get(f"/api/cuisines/{italian['cuisine_id']}").json()["recipe_list"]) == italian["recipes"]


def test_recipe_scaling_and_units():
    carbonara = next(r for r in client.get("/api/recipes").json() if r["name"] == "Classic Spaghetti Carbonara")
    d = client.get(f"/api/recipes/{carbonara['recipe_id']}", params={"servings": 8}).json()
    lines = {i["name"]: (i["quantity"], i["unit"]) for i in d["ingredients"]}
    assert d["servings"] == 4 and d["servings_shown"] == 8
    assert lines["Spaghetti"] == ("2", "lbs") and lines["Eggs"] == ("8", "large") and lines["Salt"] == ("to taste", "")
    m = client.get(f"/api/recipes/{carbonara['recipe_id']}", params={"servings": 2, "units": "metric"}).json()
    lines = {i["name"]: (i["quantity"], i["unit"]) for i in m["ingredients"]}
    assert lines["Spaghetti"] == ("225", "g") and lines["Cheese"] == ("120", "ml") and lines["Black Pepper"] == ("4.9", "ml")
    bad = client.get(f"/api/recipes/{carbonara['recipe_id']}", params={"servings": "lots"}).json()
    assert bad["servings_shown"] == 4


def test_shopping_list_combines_recipes():
    names = {r["name"]: r["recipe_id"] for r in client.get("/api/recipes").json()}
    r = client.get("/api/shopping", params={"r": f"{names['Classic Spaghetti Carbonara']}:4,"
                                                 f"{names['Quiche Lorraine']}:12,999999,x"}).json()
    assert [c["name"] for c in r["recipes"]] == ["Classic Spaghetti Carbonara", "Quiche Lorraine"]
    eggs = [i for i in r["items"] if i["name"] == "Eggs"]
    assert len(eggs) == 1 and set(eggs[0]["recipes"]) == {"Classic Spaghetti Carbonara", "Quiche Lorraine"}
    assert client.get("/api/shopping").json()["items"] == []


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Point the app at a temporary copy of the database (the repo's file must never change in tests)."""
    copy = tmp_path / "recipes.db"
    shutil.copy(data.DB_PATH, copy)
    monkeypatch.setenv("RECIPE_DB", str(copy))
    before = _md5(data.DB_PATH)
    yield copy
    assert _md5(data.DB_PATH) == before


FORM = {"name": "Test Toast", "cuisine": "American", "category": "Breakfast", "difficulty": "Easy", "prep_time": "5",
        "cook_time": "3", "servings": "2", "description": "Toast.", "instructions": "1. Toast the bread.",
        "tips": "", "ingredients": "2 | slices | Bread | thick\n1 tbsp Butter\n1 | pinch | Sea Salt |"}


def test_add_edit_and_rate_recipe_local_only(temp_db):
    r = client.post("/api/recipes", json=FORM)
    assert r.status_code == 200, r.text
    rid = r.json()["recipe_id"]
    d = client.get(f"/api/recipes/{rid}").json()
    assert d["total_time"] == 8 and d["source"] == "Web app" and d["rating"] == 3.0
    assert [(i["original"]["quantity"], i["original"]["unit"], i["name"], i["notes"]) for i in d["ingredients"]] == [
        ("2", "slices", "Bread", "thick"), ("1", "tbsp", "Butter", ""), ("1", "pinch", "Sea Salt", "")]
    ids = {i["name"]: i["ingredient_id"] for i in d["ingredients"]}
    assert ids["Butter"] == next(i["ingredient_id"] for i in client.get("/api/ingredients").json() if i["name"] == "Butter")
    edit = {**FORM, "name": "Better Toast", "servings": "4", "ingredients": "4 | slices | Bread |"}
    assert client.post(f"/api/recipes/{rid}", json=edit).status_code == 200
    d = client.get(f"/api/recipes/{rid}").json()
    assert d["name"] == "Better Toast" and d["servings"] == 4 and len(d["ingredients"]) == 1
    assert client.post(f"/api/recipes/{rid}/rating", json={"rating": 5}).json()["rating"] == 5
    assert client.get(f"/api/recipes/{rid}").json()["rating"] == 5
    assert client.get("/api/stats").json()["recipes"] == _counts()["recipes"] + 1


@pytest.mark.parametrize("change, status", [({"name": ""}, 400), ({"instructions": " "}, 400), ({"prep_time": "abc"}, 400),
                                            ({"servings": "0"}, 400), ({"difficulty": "Extreme"}, 400),
                                            ({"ingredients": "justoneword"}, 400)])
def test_add_recipe_validation(temp_db, change, status):
    assert client.post("/api/recipes", json={**FORM, **change}).status_code == status
    assert client.get("/api/stats").json()["recipes"] == _counts()["recipes"]


def test_write_errors(temp_db):
    assert client.post("/api/recipes/99999", json=FORM).status_code == 404
    assert client.post("/api/recipes/1/rating", json={"rating": 9}).status_code == 400
    assert client.post("/api/recipes/99999/rating", json={"rating": 4}).status_code == 404


def test_static_export_is_read_only(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    exported = {p.relative_to(tmp_path / "site" / "api").as_posix() for p in (tmp_path / "site" / "api").rglob("*.json")}
    assert "recipes.json" in exported and "shopping.json" not in exported and not any("rating" in p for p in exported)
    assert len([p for p in exported if p.startswith("recipes/")]) == _counts()["recipes"]


def test_scaling_fixture_is_current():
    """tests/fixtures/scaling_fixture.json (used by scaling_engine.test.mjs) matches recipe_scaling.py today.

    Outputs are recomputed from the fixture's own inputs, so adding recipes to the database does not make it stale.
    """
    import recipe_scaling as rs
    have = json.loads((ROOT / "tests" / "fixtures" / "scaling_fixture.json").read_text(encoding="utf-8"))
    want = {"scale": [{"in": c["in"], "out": rs.scale_item(*c["in"])} for c in have["scale"]],
            "combine": [{"items": c["items"], "metric": c["metric"], "out": rs.combine(c["items"], c["metric"])}
                        for c in have["combine"]]}

    def same(a, b):
        if isinstance(a, float) or isinstance(b, float):
            return a is not None and b is not None and abs(a - b) <= 1e-9 * max(1.0, abs(b))
        if isinstance(a, dict):
            return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, list):
            return isinstance(b, list) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        return a == b
    assert same(want, have), "run python scripts/make_scaling_fixture.py"


def _node(script: str) -> object:
    r = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


PARITY = [("recipes", {"cuisine": "Thai"}), ("recipes", {"q": "chicken garlic"}), ("recipes", {"max_time": "45", "diet": "vegetarian"}),
          ("recipes", {"ingredient": "Garlic", "category": "Main Course"}), ("recipes", {"equipment": "Whisk"}),
          ("recipes", {"difficulty": "Hard", "q": "dough"}), ("recipes", {"diet": "gluten-free", "max_time": "60"}),
          ("ingredients", {"category": "Spices"}), ("ingredients", {"q": "vitamin"}),
          ("equipment", {"essential": "0"}), ("equipment", {"category": "Knives", "q": "knife"}),
          ("cuisines", {"region": "East Asia"}), ("cuisines", {"q": "rice"})]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_static_search_parity(tmp_path):
    """static_api.js filtering (search_engine.js) returns the same ids as the server for the same queries."""
    full = {kind: client.get(f"/api/{kind}").json() for kind in LISTS}
    (tmp_path / "full.json").write_text(json.dumps(full))
    (tmp_path / "cases.json").write_text(json.dumps(PARITY))
    js = _node(f"import {{ filterRows, SPECS }} from {json.dumps((STATIC / 'search_engine.js').as_uri())};\n"
               "import { readFileSync } from 'node:fs';\n"
               f"const full = JSON.parse(readFileSync({json.dumps(str(tmp_path / 'full.json'))}, 'utf8'));\n"
               f"const cases = JSON.parse(readFileSync({json.dumps(str(tmp_path / 'cases.json'))}, 'utf8'));\n"
               "console.log(JSON.stringify(cases.map(([k, q]) => filterRows(k, full[k], q).map(r => r[SPECS[k].id]))));")
    for (kind, q), got in zip(PARITY, js):
        want = [row[SPECS[kind]["id"]] for row in client.get(f"/api/{kind}", params=q).json()]
        assert got == want, (kind, q)
        assert want, (kind, q)  # every case should exercise a non-empty result


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_static_scaling_parity_on_every_recipe(tmp_path):
    """The static site's scaling (exported recipe + scaling_engine.js) equals the server's for every recipe."""
    ids = [r["recipe_id"] for r in client.get("/api/recipes").json()]
    base = {i: client.get(f"/api/recipes/{i}").json() for i in ids}
    (tmp_path / "base.json").write_text(json.dumps(base))
    variants = [(1, "us"), (3, "metric"), (10, "us"), (7, "metric")]
    js = _node(f"import {{ scaleRecipeIngredients }} from {json.dumps((STATIC / 'scaling_engine.js').as_uri())};\n"
               "import { readFileSync } from 'node:fs';\n"
               f"const base = JSON.parse(readFileSync({json.dumps(str(tmp_path / 'base.json'))}, 'utf8'));\n"
               f"const variants = {json.dumps(variants)};\n"
               "const out = {};\n"
               "for (const [id, r] of Object.entries(base)) out[id] = variants.map(([s, u]) => scaleRecipeIngredients(\n"
               "  r.ingredients.map(i => ({ ...i, quantity: i.original.quantity, unit: i.original.unit })), r.servings || 1, s, u === 'metric')\n"
               "  .map(i => [i.quantity, i.unit]));\n"
               "console.log(JSON.stringify(out));")
    for i in ids:
        for (s, u), got in zip(variants, js[str(i)]):
            want = client.get(f"/api/recipes/{i}", params={"servings": s, "units": u}).json()["ingredients"]
            assert got == [[w["quantity"], w["unit"]] for w in want], (i, s, u)
