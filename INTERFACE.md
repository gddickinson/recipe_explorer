# Recipe Collection Explorer -- Interface Map

## Project Structure

| File / Directory | Purpose |
|------------------|---------|
| `recipe_explorer.py` | Tkinter desktop app (`RecipeExplorerApp`, `main()`): recipes (servings spinbox + metric checkbox via `recipe_scaling`: `show_recipe()`, `scaled_ingredients()`), ingredients, equipment, cuisines, shopping list tabs, add/import/export dialogs (~1920 lines; splitting it into tab modules is a ROADMAP item) |
| `recipe_database.py` | `RecipeDatabase`: schema and the 54 seed recipes, ingredients, equipment, cuisines (`initialize_database()`) |
| `db_operations.py` | `RecipeDAO` (all queries: recipes, ingredients, equipment, cuisines, insert/update/rate, ingredient rows), `find_or_create_ingredient_id()` (exact-name lookup used by the seed script, DAO and import dialog), `find_or_create_equipment_id()` / `split_optional()` (seed equipment: adds missing items, " (optional)" -> optional link), `parse_ingredient_line()` |
| `recipe_scaling.py` | Pure: `parse_quantity()`, `format_amount()` (kitchen fractions), `scale_item()`, `scale_recipe_ingredients()` (servings + US/metric), `combine()` (shopping-list totals) |
| `run_recipe_explorer.py` | Desktop launcher |
| `recipe_collection.db` | SQLite database (tracked; 124 recipes) |
| `run_web.py` | Starts the web app (uvicorn, http://127.0.0.1:8115) |
| `requirements-web.txt` | Pinned web/test dependencies |
| `web/app.py` | FastAPI: `/api/*` GET routes, `STATIC_ENDPOINTS`, `/api/shopping`, local-only POSTs (add/edit/rate) |
| `web/data.py` | Read-only data access through `RecipeDAO` on a SQLite `mode=ro` connection; `RECIPE_DB` env overrides the path |
| `web/search.py` | `SPECS`, `filter_rows()`, `facets()`: search/filter rules for every list |
| `web/writes.py` | Local-only writes: `add_recipe()`, `edit_recipe()`, `rate_recipe()` with the desktop form's validation |
| `web/static/index.html`, `style.css`, `core.js` | Shell page, shared kit theme and router (kit files; style.css/core.js unchanged) |
| `web/static/style_app.css` | Tomato/basil/saffron accents, page and print styles |
| `web/static/main.js` | Registers lazy page modules, mode line, background, starts router |
| `web/static/ui.js` | `listPage()` (filter lists synced to the URL), `kv()`, `sections()`, `crumb()`, `recipeCard()`, `stars()`, `mins()` |
| `web/static/static_api.js` | Static site: answers `api()` from exported JSON; filtering, scaling and shopping computed in the browser; writes -> error |
| `web/static/search_engine.js` | JS mirror of `web/search.py` (+ `search_engine.test.mjs`) |
| `web/static/scaling_engine.js` | JS port of `recipe_scaling.py` (+ `scaling_engine.test.mjs`, checked against `tests/fixtures/scaling_fixture.json`) |
| `web/static/shopping_store.js` | Shopping list in localStorage (recipes + servings, units, ticked items) |
| `web/static/home.js` | Pages: home, search, about |
| `web/static/recipes.js` | Pages: recipes (list), recipe (detail: scaling, units, add to list, rate/edit locally) |
| `web/static/pantry.js` | Pages: ingredients/ingredient, equipment/tool |
| `web/static/cuisines.js` | Pages: cuisines/cuisine |
| `web/static/shopping.js` | Page: shopping (combined or per-recipe, export .txt, print) |
| `web/static/editor.js` | Pages: add, edit (local only; static site shows needsServer()) |
| `web/static/background.js`, `icon.svg` | Animated background (off under reduced motion), favicon |
| `scripts/build_static.py` | Exports the static site to `site/` |
| `scripts/screenshots.py` | Playwright smoke test + README screenshots (`docs/img/`) |
| `scripts/make_scaling_fixture.py` | Writes `tests/fixtures/scaling_fixture.json` from `recipe_scaling.py` |
| `scripts/repair_ingredient_links.py` | Relinks seed-recipe ingredient rows mislinked by the old LIKE lookup (`--dry-run`) |
| `tests/test_web.py` | Web tests: endpoints, filters, read-only DB, writes on a temp copy, static build, JS tests, parity |
| `scripts/repair_equipment_links.py` | Adds seed-recipe equipment links the old seed script dropped (`--dry-run`) |
| `tests/test_ingredient_linking.py` | Regression tests for exact ingredient linking and the database repair |
| `tests/test_equipment_linking.py` | Regression tests for seed equipment linking and the database repair |
| `tests/test_desktop_scaling.py` | Desktop recipe view servings/metric (real Tk on a temp DB copy; skipped without a display) |
| `.github/workflows/pages.yml` | Test, build and publish the static site on push to main |

## Module Connections

```
run_recipe_explorer.py -> recipe_explorer.py -> db_operations (find_or_create_ingredient_id, parse_ingredient_line),
                                                 recipe_scaling.scale_recipe_ingredients
recipe_database.py -> db_operations.find_or_create_ingredient_id, find_or_create_equipment_id
run_web.py -> web/app.py -> web/data.py (-> db_operations.RecipeDAO read-only, recipe_database if the .db is missing)
                         -> web/search.py, web/writes.py (-> RecipeDAO), recipe_scaling.py
           -> web/static/main.js -> page modules -> core.js api() -> /api/* (local) or static_api.js (GitHub Pages)
static_api.js -> search_engine.js (= web/search.py), scaling_engine.js (= recipe_scaling.py)
scripts/build_static.py -> web/app.py via TestClient -> site/api/*.json
```

## Data Files

- `recipe_collection.db` -- shared by the desktop app and the web app (web: read-only except add/edit/rate)
- `tests/fixtures/scaling_fixture.json` -- Python outputs the JS scaling engine must reproduce
- `docs/img/` -- README screenshots of the web interface
