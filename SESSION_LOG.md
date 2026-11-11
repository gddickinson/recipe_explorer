# Session Log

## 2026-11-11 -- Web interface, static GitHub Pages site and two bug fixes (branch `web-interface`)
- Bug fix (own commit): ingredient lookup used `name LIKE '%<name>%'`, which returned the alphabetically first
  containing name ("Onion" -> "Green Onions", "Milk" -> "Coconut Milk", "Chicken" -> "Chicken Bones"). The seed
  script, the desktop import dialog and `RecipeDAO` now share `db_operations.find_or_create_ingredient_id()` (exact,
  case-insensitive). Regression tests in `tests/test_ingredient_linking.py`.
- Data fix (own commit): `scripts/repair_ingredient_links.py` relinked the 34 mislinked rows of the 54 seed recipes in
  `recipe_collection.db` (adds ingredients Chicken, Pork, Water, Onions). The other 70 recipes (no seed script in the
  repo) show the same pattern (e.g. Osso Buco "1 large Green Onions") but were left alone: needs George's decision.
- README corrections (own commit): search scope, no ingredient list in the Add form, no reviews, current counts.
- Web app (`web/`, `run_web.py`, port 8115) + static site (`scripts/build_static.py`, `.github/workflows/pages.yml`):
  home, recipes (search + 7 filters), recipe detail (servings scaling, US/metric), shopping list (localStorage,
  combined or per recipe, export/print), ingredients, equipment, cuisines, search, about; add/edit/rate local-only.
- New pure module `recipe_scaling.py` (scaling was a ROADMAP item; the desktop app does not use it yet), ported to
  `web/static/scaling_engine.js`; fixture `tests/fixtures/scaling_fixture.json` (1904 cases + 10 shopping lists).
- `RecipeDAO` gained `get_recipe`, `update_recipe`, `replace_recipe_ingredients`, ids in the recipe-ingredient and
  recipe-equipment queries, and `parse_ingredient_line()` (the import dialog now uses it; also accepts "q | unit | name | notes").
- Data is generic starter recipes (no personal entries), so all of it is exported to the static site.
- Local environment: tests need `DYLD_LIBRARY_PATH=/opt/anaconda3/pkgs/libsqlite-3.53.3-h1b79a29_0/lib` (venv's
  anaconda base lacks libsqlite).
- Tests: `python -m pytest -q tests/` 535 passed; node tests ok; screenshots static 20 routes + server 15 routes ok,
  no phone overflow; local add/edit/rate exercised in a browser against a temporary copy of the database.
