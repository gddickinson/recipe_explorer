# Recipe Collection Explorer

See @INTERFACE.md for the project navigation map.

## Quick Start
```bash
python3 run_recipe_explorer.py      # desktop app (standard library only)
python run_web.py                   # web app on http://127.0.0.1:8115 (pip install -r requirements-web.txt)
```

## Testing
```bash
python -m pytest -q tests/
```
Keep `web/search.py` / `web/static/search_engine.js` and `recipe_scaling.py` / `web/static/scaling_engine.js` in step
(parity tests; regenerate the fixture with `python scripts/make_scaling_fixture.py`). Tests must never write
`recipe_collection.db`: use a temporary copy via `RECIPE_DB`.

See @SESSION_LOG.md for progress notes.
