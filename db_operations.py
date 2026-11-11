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
            SELECT i.name, ri.quantity, ri.unit, ri.notes
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.recipe_id = ?
            ORDER BY ri.id
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recipe_equipment(self, recipe_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT e.name, re.optional
            FROM recipe_equipment re
            JOIN equipment e ON re.equipment_id = e.equipment_id
            WHERE re.recipe_id = ?
            ORDER BY re.optional, e.name
        """, (recipe_id,))
        return [dict(row) for row in cursor.fetchall()]

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
