"""Desktop recipe view: the servings spinbox and metric checkbox scale the ingredient list (recipe_scaling.py).

Runs the real Tkinter app on a temporary copy of the database; skipped where no display is available (e.g. CI).
Run: python -m pytest -q tests/test_desktop_scaling.py
"""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def gui(tmp_path, monkeypatch):
    tk = pytest.importorskip("tkinter")
    shutil.copy(ROOT / "recipe_collection.db", tmp_path / "recipe_collection.db")
    monkeypatch.chdir(tmp_path)  # the app opens "recipe_collection.db" in the working directory
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"no display: {e}")
    root.withdraw()
    import recipe_explorer as rx
    monkeypatch.setattr(rx.messagebox, "showinfo", lambda *a, **k: None)
    app = rx.RecipeExplorerApp(root)
    yield app
    root.destroy()


def select(app, name):
    i = [r["name"] for r in app.recipe_data].index(name)
    app.recipes_listbox.selection_clear(0, "end")
    app.recipes_listbox.selection_set(i)
    app.on_recipe_select(None)


def details(app):
    return app.recipe_details_text.get("1.0", "end")


def test_servings_and_metric(gui):
    select(gui, "Classic Spaghetti Carbonara")
    assert gui.servings_var.get() == "4"
    assert "• 1 lb Spaghetti" in details(gui) and "scaled to" not in details(gui)
    gui.servings_var.set("8")
    gui.refresh_recipe_details()
    assert "Ingredients (scaled to 8 servings)" in details(gui)
    assert "• 2 lbs Spaghetti" in details(gui) and "• 8 large Eggs" in details(gui)
    gui.metric_var.set(True)
    gui.refresh_recipe_details()
    assert "• 905 g Spaghetti" in details(gui) and "• 475 ml Cheese" in details(gui)
    gui.servings_var.set("lots")  # invalid -> the recipe's own servings
    gui.refresh_recipe_details()
    assert "• 455 g Spaghetti" in details(gui)


def test_shopping_list_uses_scaled_amounts_and_optional_equipment_shown(gui):
    select(gui, "Classic Spaghetti Carbonara")
    gui.servings_var.set("2")
    gui.add_recipe_to_shopping_list()
    spaghetti = next(i for i in gui.shopping_list if i["name"] == "Spaghetti")
    assert (spaghetti["quantity"], spaghetti["unit"]) == ("1/2", "lb")
    select(gui, "Butter Chicken")
    assert gui.servings_var.get() == "6" and "• Blender (optional)" in details(gui)
