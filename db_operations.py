"""
Database operations (DAO layer) for Recipe Collection Explorer.

Centralizes all SQLite queries so the GUI code does not embed SQL directly.
"""

import sqlite3
from typing import List, Dict, Optional, Any
from pathlib import Path


def find_or_create_ingredient_id(cursor: sqlite3.Cursor, name: str, category: str = "Other") -> int:
    """Return the id of the ingredient called `name` (exact, case-insensitive), inserting it if missing.

    Shared by the seed script, the DAO and the desktop import dialog. Names are capped at 50 characters, as the
    import dialog always did. (A `LIKE '%name%'` lookup used to link e.g. "Onion" to "Green Onions".)
    The caller commits.
    """
    name = name.strip()[:50]
    cursor.execute("SELECT ingredient_id FROM ingredients WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO ingredients (name, category) VALUES (?, ?)", (name, category))
    return cursor.lastrowid


OPTIONAL_SUFFIX = " (optional)"


def split_optional(name: str):
    """'Rolling Pin (optional)' -> ('Rolling Pin', True); 'Whisk' -> ('Whisk', False)."""
    name = name.strip()
    if name.lower().endswith(OPTIONAL_SUFFIX):
        return name[: -len(OPTIONAL_SUFFIX)].strip(), True
    return name, False


def find_or_create_equipment_id(cursor: sqlite3.Cursor, name: str, category: str = "Other"):
    """(equipment_id, optional) for an equipment name as a recipe lists it; missing equipment is added.

    An exact (case-insensitive) match wins, so the existing "Electric Mixer (optional)" row is still used. Otherwise a
    trailing " (optional)" marks an optional link to the equipment without the suffix ("Blender (optional)" ->
    Blender, optional). Equipment not in the table yet is inserted (category "Other", not essential) instead of being
    dropped, as the seed script used to do. The caller commits.
    """
    cursor.execute("SELECT equipment_id FROM equipment WHERE name = ? COLLATE NOCASE", (name.strip(),))
    row = cursor.fetchone()
    if row:
        return row[0], False
    base, optional = split_optional(name)
    cursor.execute("SELECT equipment_id FROM equipment WHERE name = ? COLLATE NOCASE", (base,))
    row = cursor.fetchone()
    if row:
        return row[0], optional
    cursor.execute("INSERT INTO equipment (name, category, essential) VALUES (?, ?, 0)", (base, category))
    return cursor.lastrowid, optional


def parse_ingredient_line(line: str):
    """One ingredient line -> (quantity, unit, name, notes), or None if it cannot be read.

    "qty | unit | name | notes" (pipe-separated, unit and notes may be empty) keeps every field; a plain line uses
    the desktop import dialog's rule: "2 cups flour" -> ("2", "cups", "flour", ""), "3 eggs" -> ("3", "", "eggs", "").
    """
    line = (line or "").strip()
    if not line:
        return None
    if "|" in line:
        parts = [p.strip() for p in line.split("|")] + ["", "", ""]
        qty, unit, name, notes = parts[0], parts[1], parts[2], "|".join(parts[3:]).strip("| ").strip()
        return (qty, unit, name, notes) if name else None
    parts = line.split(maxsplit=2)
    if len(parts) < 2:
        return None
    if len(parts) > 2:
        return parts[0], parts[1], parts[2], ""
    return parts[0], "", parts[1], ""


class RecipeDAO:
    """Data Access Object for the recipe database."""

    def __init__(self, db_path: str = "recipe_collection.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open the database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Recipes
    # ------------------------------------------------------------------

    def get_recipes(self, search_term: str = "", cuisine: str = "All",
                    category: str = "All", difficulty: str = "All",
                    max_time: str = "Any") -> List[Dict]:
        """Fetch recipes matching filters."""
        query = "SELECT * FROM recipes WHERE 1=1"
        params: List[Any] = []

        if search_term:
            query += " AND (name LIKE ? OR description LIKE ? OR instructions LIKE ?)"
            pat = f"%{search_term}%"
            params.extend([pat, pat, pat])
        if cuisine != "All":
            query += " AND cuisine = ?"
            params.append(cuisine)
        if category != "All":
            query += " AND category = ?"
            params.append(category)
        if difficulty != "All":
            query += " AND difficulty = ?"
            params.append(difficulty)
        if max_time != "Any":
            query += " AND total_time <= ?"
            params.append(int(max_time))

        query += " ORDER BY name"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_recipe_ingredients(self, recipe_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.name, ri.quantity, ri.unit, ri.notes, i.ingredient_id
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.recipe_id = ?
            ORDER BY ri.id
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recipe_equipment(self, recipe_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT e.name, re.optional, e.equipment_id
            FROM recipe_equipment re
            JOIN equipment e ON re.equipment_id = e.equipment_id
            WHERE re.recipe_id = ?
            ORDER BY re.optional, e.name
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recipe(self, recipe_id: int) -> Optional[Dict]:
        row = self.conn.execute("SELECT * FROM recipes WHERE recipe_id = ?", (recipe_id,)).fetchone()
        return dict(row) if row else None

    def update_recipe(self, recipe_id: int, name, cuisine, category, difficulty,
                      prep_time, cook_time, total_time, servings,
                      description, instructions, tips):
        """Update a recipe's editable fields (the ones the Add Recipe form has)."""
        self.conn.execute("""
            UPDATE recipes SET name = ?, cuisine = ?, category = ?, difficulty = ?, prep_time = ?,
                cook_time = ?, total_time = ?, servings = ?, description = ?, instructions = ?, tips = ?
            WHERE recipe_id = ?
        """, (name, cuisine, category, difficulty, prep_time, cook_time, total_time, servings,
              description, instructions, tips, recipe_id))
        self.conn.commit()

    def replace_recipe_ingredients(self, recipe_id: int, rows) -> None:
        """Replace a recipe's ingredient list with rows of (quantity, unit, name, notes)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        for qty, unit, name, notes in rows:
            ing_id = find_or_create_ingredient_id(cursor, name)
            cursor.execute("""
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (recipe_id, ing_id, qty, unit, notes))
        self.conn.commit()

    def update_recipe_rating(self, recipe_id: int, rating: float):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE recipes SET rating = ? WHERE recipe_id = ?",
            (rating, recipe_id),
        )
        self.conn.commit()

    def insert_recipe(self, name, cuisine, category, difficulty,
                      prep_time, cook_time, total_time, servings,
                      description, instructions, tips,
                      source: str = "") -> int:
        """Insert a recipe and return the new recipe_id."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO recipes (
                name, cuisine, category, difficulty, prep_time, cook_time,
                total_time, servings, description, instructions, tips,
                created_date, rating, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 3.0, ?)
        """, (name, cuisine, category, difficulty, prep_time, cook_time,
              total_time, servings, description, instructions, tips, source))
        self.conn.commit()
        return cursor.lastrowid

    # ------------------------------------------------------------------
    # Ingredients
    # ------------------------------------------------------------------

    def get_ingredients(self, search_term: str = "", category: str = "All") -> List[Dict]:
        query = "SELECT * FROM ingredients WHERE 1=1"
        params: List[Any] = []
        if search_term:
            query += " AND name LIKE ?"
            params.append(f"%{search_term}%")
        if category != "All":
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY name"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def insert_ingredient(self, name, category, description,
                          storage_tips, season) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO ingredients (name, category, description, storage_tips, season)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, description, storage_tips, season))
        self.conn.commit()
        return cursor.lastrowid

    def find_or_create_ingredient(self, name: str, category: str = "Other") -> int:
        """Find an ingredient by exact (case-insensitive) name, or create a new one."""
        ing_id = find_or_create_ingredient_id(self.conn.cursor(), name, category)
        self.conn.commit()
        return ing_id

    def insert_recipe_ingredient(self, recipe_id, ingredient_id,
                                 quantity, unit, notes=""):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (recipe_id, ingredient_id, quantity, unit, notes))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Equipment
    # ------------------------------------------------------------------

    def get_equipment(self, search_term: str = "", category: str = "All",
                      essential: str = "All") -> List[Dict]:
        query = "SELECT * FROM equipment WHERE 1=1"
        params: List[Any] = []
        if search_term:
            query += " AND name LIKE ?"
            params.append(f"%{search_term}%")
        if category != "All":
            query += " AND category = ?"
            params.append(category)
        if essential == "Essential Only":
            query += " AND essential = 1"
        elif essential == "Optional Only":
            query += " AND essential = 0"
        query += " ORDER BY essential DESC, name"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def insert_equipment(self, name, category, description,
                         essential, price_range) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO equipment (name, category, description, essential, price_range)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, description, essential, price_range))
        self.conn.commit()
        return cursor.lastrowid

    # ------------------------------------------------------------------
    # Cuisines
    # ------------------------------------------------------------------

    def get_cuisines(self, search_term: str = "") -> List[Dict]:
        query = "SELECT * FROM cuisines WHERE 1=1"
        params: List[Any] = []
        if search_term:
            query += " AND (name LIKE ? OR region LIKE ?)"
            pat = f"%{search_term}%"
            params.extend([pat, pat])
        query += " ORDER BY name"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_cuisine_names(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM cuisines ORDER BY name")
        return [row["name"] for row in cursor.fetchall()]

    def get_recipes_by_cuisine(self, cuisine_name: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM recipes WHERE cuisine = ? ORDER BY name",
            (cuisine_name,),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_counts(self) -> Dict[str, int]:
        """Return row counts for status bar display."""
        cursor = self.conn.cursor()
        counts = {}
        for table in ("recipes", "ingredients", "equipment", "cuisines"):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        return counts
