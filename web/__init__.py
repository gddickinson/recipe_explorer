"""Web interface for Recipe Collection Explorer (FastAPI + plain ES modules; see INTERFACE.md).

- app.py     routes under /api, STATIC_ENDPOINTS exported to the GitHub Pages site
- data.py    read-only database access through db_operations.RecipeDAO (SQLite mode=ro)
- search.py  search/filter rules for the list pages (mirrored by static/search_engine.js)
- writes.py  local-only writes: add/edit a recipe, rate a recipe (never on the static site)
- static/    front end (index.html, core.js router, one module per page, scaling and search engines)
"""
