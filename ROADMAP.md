# Recipe Collection Explorer -- Roadmap

## Current State
A Tkinter-based GUI application for managing recipes, ingredients, and kitchen equipment with SQLite storage. Three files: `recipe_explorer.py` (main GUI app, `RecipeExplorerApp` class), `recipe_database.py` (database initialization with 60+ recipes), `run_recipe_explorer.py` (launcher). Uses standard library only (tkinter, sqlite3). Functional with search, filtering, shopping list generation, CSV export, and web recipe search. The `recipe_explorer.py` is likely a very large monolithic file given it builds 5+ tabs with full CRUD functionality in a single class.

## Short-term Improvements
- [ ] Split `recipe_explorer.py` into separate modules: `tabs/recipes_tab.py`, `tabs/ingredients_tab.py`, `tabs/equipment_tab.py`, `tabs/cuisines_tab.py`, `tabs/shopping_tab.py`
- [ ] Extract database operations from `RecipeExplorerApp` into a dedicated `db_operations.py` DAO layer
- [ ] Add error handling for database corruption (currently suggests deleting and recreating)
- [ ] Add input validation when adding new recipes (required fields, numeric ranges for times/servings)
- [ ] Add unit tests for database queries and recipe filtering logic
- [ ] Add `requirements.txt` (even though stdlib-only, document Python version requirement)
- [ ] Rename `RECIPE_README.md` to just use `README.md` as the project README

## Feature Enhancements
- [ ] Implement recipe scaling (adjust ingredient quantities by serving count)
- [ ] Add meal planning calendar with weekly view and drag-drop recipe assignment
- [ ] Implement recipe import from URLs (parse structured data from common recipe sites)
- [ ] Add photo attachments for recipes using file dialogs and thumbnail display
- [ ] Implement ingredient inventory tracking (mark what you have, show what you need)
- [ ] Add nutritional calculator that sums per-ingredient data for full recipe totals
- [ ] Add recipe collections/tags for organizing beyond cuisine and category
- [ ] Implement cost-per-serving calculator with ingredient price tracking

## Long-term Vision
- [ ] Migrate from Tkinter to a modern framework (CustomTkinter, PyQt6, or web-based with Flask)
- [ ] Add recipe sharing via export to PDF with formatted layout
- [ ] Build a REST API backend for multi-device access
- [ ] Implement recommendation engine ("if you liked X, try Y") based on shared ingredients
- [ ] Add cooking timer integration with step-by-step guided cooking mode
- [ ] Publish as a standalone app with PyInstaller/cx_Freeze
- [ ] Add grocery store aisle organization for shopping lists

## Technical Debt
- [ ] `recipe_explorer.py` is almost certainly >500 lines -- must split into modules (see Short-term)
- [ ] `recipe_database.py` mixes schema definition with seed data -- separate into `schema.py` and `seed_data.py`
- [ ] Database path is hardcoded as `"recipe_collection.db"` -- make configurable
- [ ] No separation between data layer and presentation layer -- all in one class
- [ ] JSON used for complex fields (nutritional info) inside SQLite -- consider normalizing
- [ ] No database migration strategy -- schema changes require full rebuild
- [ ] Shopping list state is in-memory only (`self.shopping_list = []`) -- persist to database
