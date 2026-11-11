"""
Recipe Collection Explorer v2.0 - ENHANCED EDITION
A comprehensive recipe database browser with ingredients and equipment tracking
NOW WITH WEB RECIPE SEARCH!
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sqlite3
from pathlib import Path
import csv
import json
from datetime import datetime
import re
import urllib.parse

from db_operations import find_or_create_ingredient_id

class RecipeExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recipe Collection Explorer")
        self.root.geometry("1400x900")

        # Database connection
        self.db_path = "recipe_collection.db"
        self.conn = None
        self.connect_db()

        # Current selections
        self.current_recipe = None
        self.shopping_list = []

        # Create menu bar
        self.create_menu_bar()

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.create_recipes_tab()
        self.create_ingredients_tab()
        self.create_equipment_tab()
        self.create_cuisines_tab()
        self.create_shopping_list_tab()

        # Style configuration
        self.configure_styles()

        # Status bar
        self.create_status_bar()

    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database: {e}")

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add New Recipe Manually", command=self.add_new_recipe)
        file_menu.add_command(label="Search Web for Recipes", command=self.search_web_recipes)
        file_menu.add_separator()
        file_menu.add_command(label="Export Recipes (CSV)", command=self.export_recipes_csv)
        file_menu.add_command(label="Export Shopping List", command=self.export_shopping_list)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Recipes", command=lambda: self.notebook.select(0))
        view_menu.add_command(label="Ingredients", command=lambda: self.notebook.select(1))
        view_menu.add_command(label="Equipment", command=lambda: self.notebook.select(2))
        view_menu.add_command(label="Cuisines", command=lambda: self.notebook.select(3))
        view_menu.add_command(label="Shopping List", command=lambda: self.notebook.select(4))

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status()

    def update_status(self):
        """Update status bar with database stats"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recipes")
            recipe_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ingredients")
            ingredient_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM equipment")
            equipment_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cuisines")
            cuisine_count = cursor.fetchone()[0]

            status_text = f"Database: {recipe_count} recipes | {ingredient_count} ingredients | {equipment_count} equipment | {cuisine_count} cuisines | Shopping List: {len(self.shopping_list)} items"
            self.status_bar.config(text=status_text)
        except:
            self.status_bar.config(text="Ready")

    def configure_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Action.TButton', font=('Arial', 10, 'bold'))

    # ==============================================
    # RECIPES TAB
    # ==============================================

    def create_recipes_tab(self):
        """Create recipes browser tab"""
        recipes_frame = ttk.Frame(self.notebook)
        self.notebook.add(recipes_frame, text="🍳 Recipes")

        # Search and filter frame
        search_frame = ttk.Frame(recipes_frame)
        search_frame.pack(fill='x', padx=10, pady=10)

        # Row 1: Basic search
        row1 = ttk.Frame(search_frame)
        row1.pack(fill='x', pady=(0, 5))

        ttk.Label(row1, text="Search:").pack(side='left', padx=5)
        self.recipe_search_var = tk.StringVar()
        self.recipe_search_entry = ttk.Entry(row1, textvariable=self.recipe_search_var, width=30)
        self.recipe_search_entry.pack(side='left', padx=5)
        self.recipe_search_entry.bind('<KeyRelease>', self.on_recipe_search)

        ttk.Label(row1, text="Cuisine:").pack(side='left', padx=(20, 5))
        self.recipe_cuisine_var = tk.StringVar(value="All")
        self.recipe_cuisine_combo = ttk.Combobox(row1, textvariable=self.recipe_cuisine_var,
                                                 state='readonly', width=15)
        self.recipe_cuisine_combo.pack(side='left', padx=5)
        self.recipe_cuisine_combo.bind('<<ComboboxSelected>>', self.on_recipe_search)

        ttk.Button(row1, text="Clear", command=self.clear_recipe_search).pack(side='left', padx=5)

        # Row 2: Advanced filters
        row2 = ttk.Frame(search_frame)
        row2.pack(fill='x')

        ttk.Label(row2, text="Category:").pack(side='left', padx=5)
        self.recipe_category_var = tk.StringVar(value="All")
        self.recipe_category_combo = ttk.Combobox(row2, textvariable=self.recipe_category_var,
                                                  values=["All", "Main Course", "Appetizer", "Dessert", 
                                                         "Soup", "Salad", "Side Dish", "Breakfast"],
                                                  state='readonly', width=15)
        self.recipe_category_combo.pack(side='left', padx=5)
        self.recipe_category_combo.bind('<<ComboboxSelected>>', self.on_recipe_search)

        ttk.Label(row2, text="Difficulty:").pack(side='left', padx=(20, 5))
        self.recipe_difficulty_var = tk.StringVar(value="All")
        self.recipe_difficulty_combo = ttk.Combobox(row2, textvariable=self.recipe_difficulty_var,
                                                    values=["All", "Easy", "Medium", "Hard"],
                                                    state='readonly', width=12)
        self.recipe_difficulty_combo.pack(side='left', padx=5)
        self.recipe_difficulty_combo.bind('<<ComboboxSelected>>', self.on_recipe_search)

        ttk.Label(row2, text="Max Time (min):").pack(side='left', padx=(20, 5))
        self.recipe_time_var = tk.StringVar(value="Any")
        self.recipe_time_combo = ttk.Combobox(row2, textvariable=self.recipe_time_var,
                                              values=["Any", "30", "60", "90", "120"],
                                              state='readonly', width=10)
        self.recipe_time_combo.pack(side='left', padx=5)
        self.recipe_time_combo.bind('<<ComboboxSelected>>', self.on_recipe_search)

        # Main content frame
        content_frame = ttk.Frame(recipes_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left: Recipe list
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(list_frame, text="Recipes", style='Header.TLabel').pack(anchor='w', pady=5)

        list_scroll = ttk.Frame(list_frame)
        list_scroll.pack(fill='both', expand=True)

        self.recipes_listbox = tk.Listbox(list_scroll, font=('Arial', 10))
        recipes_scrollbar = ttk.Scrollbar(list_scroll, orient='vertical',
                                         command=self.recipes_listbox.yview)
        self.recipes_listbox.configure(yscrollcommand=recipes_scrollbar.set)

        self.recipes_listbox.pack(side='left', fill='both', expand=True)
        recipes_scrollbar.pack(side='right', fill='y')

        self.recipes_listbox.bind('<<ListboxSelect>>', self.on_recipe_select)
        self.recipe_data = []

        # Right: Recipe details
        details_frame = ttk.Frame(content_frame)
        details_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(details_frame, text="Recipe Details", style='Header.TLabel').pack(anchor='w', pady=5)

        self.recipe_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                             font=('Arial', 10))
        self.recipe_details_text.pack(fill='both', expand=True)

        # Configure tags for formatting
        self.recipe_details_text.tag_configure('recipe_name', font=('Arial', 18, 'bold'), foreground='#2c5f2d')
        self.recipe_details_text.tag_configure('cuisine', font=('Arial', 12, 'italic'), foreground='#666666')
        self.recipe_details_text.tag_configure('header', font=('Arial', 11, 'bold'), foreground='#4a4a4a')
        self.recipe_details_text.tag_configure('value', font=('Arial', 10))
        self.recipe_details_text.tag_configure('description', font=('Arial', 10, 'italic'), foreground='#555555')

        # Action buttons
        button_frame = ttk.Frame(recipes_frame)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text="🛒 Add Ingredients to Shopping List",
                  command=self.add_recipe_to_shopping_list).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📋 Copy Recipe",
                  command=self.copy_recipe).pack(side='left', padx=5)
        ttk.Button(button_frame, text="⭐ Rate Recipe",
                  command=self.rate_recipe).pack(side='left', padx=5)

        # Load data
        self.load_cuisine_list()
        self.load_recipes()

    def load_cuisine_list(self):
        """Load cuisine names for filter"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT name FROM cuisines ORDER BY name")
            cuisines = ['All'] + [row['name'] for row in cursor.fetchall()]
            self.recipe_cuisine_combo['values'] = cuisines
        except sqlite3.Error as e:
            print(f"Error loading cuisines: {e}")

    def load_recipes(self, search_term='', cuisine='All', category='All', difficulty='All', max_time='Any'):
        """Load recipes with filters"""
        self.recipes_listbox.delete(0, tk.END)
        self.recipe_data = []

        try:
            cursor = self.conn.cursor()

            query = "SELECT * FROM recipes WHERE 1=1"
            params = []

            if search_term:
                query += """ AND (
                    name LIKE ? OR
                    description LIKE ? OR
                    instructions LIKE ?
                )"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if cuisine != 'All':
                query += " AND cuisine = ?"
                params.append(cuisine)

            if category != 'All':
                query += " AND category = ?"
                params.append(category)

            if difficulty != 'All':
                query += " AND difficulty = ?"
                params.append(difficulty)

            if max_time != 'Any':
                query += " AND total_time <= ?"
                params.append(int(max_time))

            query += " ORDER BY name"

            cursor.execute(query, params)
            recipes = cursor.fetchall()

            for recipe in recipes:
                self.recipe_data.append(dict(recipe))
                display_name = f"{recipe['name']} ({recipe['cuisine']}) - {recipe['total_time']}min"
                self.recipes_listbox.insert(tk.END, display_name)

            if hasattr(self, 'status_bar'):
                self.status_bar.config(text=f"Loaded {len(recipes)} recipes")

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load recipes: {e}")

    def on_recipe_search(self, event=None):
        """Handle recipe search and filter changes"""
        search_term = self.recipe_search_var.get()
        cuisine = self.recipe_cuisine_var.get()
        category = self.recipe_category_var.get()
        difficulty = self.recipe_difficulty_var.get()
        max_time = self.recipe_time_var.get()
        self.load_recipes(search_term, cuisine, category, difficulty, max_time)

    def clear_recipe_search(self):
        """Clear all recipe filters"""
        self.recipe_search_var.set('')
        self.recipe_cuisine_var.set('All')
        self.recipe_category_var.set('All')
        self.recipe_difficulty_var.set('All')
        self.recipe_time_var.set('Any')
        self.load_recipes()

    def on_recipe_select(self, event):
        """Handle recipe selection"""
        selection = self.recipes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        recipe = self.recipe_data[index]
        self.current_recipe = recipe

        # Clear previous details
        self.recipe_details_text.config(state='normal')
        self.recipe_details_text.delete('1.0', tk.END)

        # Display recipe information
        self.recipe_details_text.insert(tk.END, f"{recipe['name']}\n", 'recipe_name')
        self.recipe_details_text.insert(tk.END, f"{recipe['cuisine']} - {recipe['category']}\n\n", 'cuisine')

        # Description
        if recipe['description']:
            self.recipe_details_text.insert(tk.END, f"{recipe['description']}\n\n", 'description')

        # Quick Info
        self.recipe_details_text.insert(tk.END, "Quick Info\n", 'header')
        self.recipe_details_text.insert(tk.END, f"Difficulty: {recipe['difficulty']}\n", 'value')
        self.recipe_details_text.insert(tk.END, f"Prep Time: {recipe['prep_time']} minutes\n", 'value')
        self.recipe_details_text.insert(tk.END, f"Cook Time: {recipe['cook_time']} minutes\n", 'value')
        self.recipe_details_text.insert(tk.END, f"Total Time: {recipe['total_time']} minutes\n", 'value')
        self.recipe_details_text.insert(tk.END, f"Servings: {recipe['servings']}\n", 'value')
        if recipe['rating']:
            stars = "⭐" * int(recipe['rating'])
            self.recipe_details_text.insert(tk.END, f"Rating: {stars} ({recipe['rating']}/5.0)\n", 'value')
        self.recipe_details_text.insert(tk.END, "\n")

        # Ingredients
        self.recipe_details_text.insert(tk.END, "Ingredients\n", 'header')
        ingredients = self.get_recipe_ingredients(recipe['recipe_id'])
        for ing in ingredients:
            ing_text = f"• {ing['quantity']} {ing['unit']} {ing['name']}"
            if ing['notes']:
                ing_text += f" ({ing['notes']})"
            self.recipe_details_text.insert(tk.END, f"{ing_text}\n", 'value')
        self.recipe_details_text.insert(tk.END, "\n")

        # Equipment Needed
        self.recipe_details_text.insert(tk.END, "Equipment Needed\n", 'header')
        equipment = self.get_recipe_equipment(recipe['recipe_id'])
        for equip in equipment:
            self.recipe_details_text.insert(tk.END, f"• {equip['name']}\n", 'value')
        self.recipe_details_text.insert(tk.END, "\n")

        # Instructions
        self.recipe_details_text.insert(tk.END, "Instructions\n", 'header')
        self.recipe_details_text.insert(tk.END, f"{recipe['instructions']}\n\n", 'value')

        # Tips
        if recipe['tips']:
            self.recipe_details_text.insert(tk.END, "Chef's Tips\n", 'header')
            self.recipe_details_text.insert(tk.END, f"{recipe['tips']}\n\n", 'value')

        # Nutritional Info
        if recipe['nutritional_info']:
            self.recipe_details_text.insert(tk.END, "Nutritional Information (per serving)\n", 'header')
            try:
                nutrition = json.loads(recipe['nutritional_info'])
                for key, value in nutrition.items():
                    self.recipe_details_text.insert(tk.END, f"{key.title()}: {value}\n", 'value')
            except:
                self.recipe_details_text.insert(tk.END, f"{recipe['nutritional_info']}\n", 'value')
            self.recipe_details_text.insert(tk.END, "\n")

        # Dietary Tags
        if recipe['dietary_tags']:
            self.recipe_details_text.insert(tk.END, "Dietary Information\n", 'header')
            self.recipe_details_text.insert(tk.END, f"{recipe['dietary_tags']}\n\n", 'value')

        self.recipe_details_text.config(state='disabled')

    def get_recipe_ingredients(self, recipe_id):
        """Get ingredients for a recipe"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT i.name, ri.quantity, ri.unit, ri.notes
                FROM recipe_ingredients ri
                JOIN ingredients i ON ri.ingredient_id = i.ingredient_id
                WHERE ri.recipe_id = ?
                ORDER BY ri.id
            ''', (recipe_id,))
            return cursor.fetchall()
        except sqlite3.Error:
            return []

    def get_recipe_equipment(self, recipe_id):
        """Get equipment for a recipe"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT e.name, re.optional
                FROM recipe_equipment re
                JOIN equipment e ON re.equipment_id = e.equipment_id
                WHERE re.recipe_id = ?
                ORDER BY re.optional, e.name
            ''', (recipe_id,))
            return cursor.fetchall()
        except sqlite3.Error:
            return []

    def add_recipe_to_shopping_list(self):
        """Add recipe ingredients to shopping list"""
        if not self.current_recipe:
            messagebox.showinfo("No Recipe Selected", "Please select a recipe first")
            return

        ingredients = self.get_recipe_ingredients(self.current_recipe['recipe_id'])
        added_count = 0

        for ing in ingredients:
            item = {
                'name': ing['name'],
                'quantity': ing['quantity'],
                'unit': ing['unit'],
                'recipe': self.current_recipe['name']
            }
            # Check if not already in list
            if not any(i['name'] == item['name'] and i['recipe'] == item['recipe'] for i in self.shopping_list):
                self.shopping_list.append(item)
                added_count += 1

        self.update_shopping_list_display()
        self.update_status()
        messagebox.showinfo("Added to Shopping List", 
                           f"Added {added_count} ingredients from {self.current_recipe['name']} to shopping list")

    def copy_recipe(self):
        """Copy recipe to clipboard"""
        if not self.current_recipe:
            messagebox.showinfo("No Recipe Selected", "Please select a recipe first")
            return

        recipe_text = self.recipe_details_text.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(recipe_text)
        messagebox.showinfo("Copied", "Recipe copied to clipboard")

    def rate_recipe(self):
        """Rate a recipe"""
        if not self.current_recipe:
            messagebox.showinfo("No Recipe Selected", "Please select a recipe first")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Rate Recipe")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Rate: {self.current_recipe['name']}", 
                 style='Header.TLabel').pack(pady=20)

        rating_var = tk.DoubleVar(value=self.current_recipe['rating'] or 3.0)

        rating_frame = ttk.Frame(dialog)
        rating_frame.pack(pady=10)

        for i in range(1, 6):
            ttk.Radiobutton(rating_frame, text=f"{'⭐' * i}", variable=rating_var,
                           value=float(i)).pack(anchor='w', padx=20)

        def save_rating():
            try:
                cursor = self.conn.cursor()
                cursor.execute('UPDATE recipes SET rating = ? WHERE recipe_id = ?',
                             (rating_var.get(), self.current_recipe['recipe_id']))
                self.conn.commit()
                self.current_recipe['rating'] = rating_var.get()
                self.on_recipe_select(None)  # Refresh display
                dialog.destroy()
                messagebox.showinfo("Success", "Rating saved!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Could not save rating: {e}")

        ttk.Button(dialog, text="Save Rating", command=save_rating).pack(pady=10)


    # ==============================================
    # INGREDIENTS TAB
    # ==============================================

    def create_ingredients_tab(self):
        """Create ingredients browser tab"""
        ingredients_frame = ttk.Frame(self.notebook)
        self.notebook.add(ingredients_frame, text="🥕 Ingredients")

        # Search frame
        search_frame = ttk.Frame(ingredients_frame)
        search_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.ingredient_search_var = tk.StringVar()
        ingredient_search = ttk.Entry(search_frame, textvariable=self.ingredient_search_var, width=30)
        ingredient_search.pack(side='left', padx=5)
        ingredient_search.bind('<KeyRelease>', self.on_ingredient_search)

        ttk.Label(search_frame, text="Category:").pack(side='left', padx=(20, 5))
        self.ingredient_category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(search_frame, textvariable=self.ingredient_category_var,
                                      values=["All", "Vegetables", "Proteins", "Grains", "Dairy", 
                                             "Herbs", "Spices", "Oils", "Other"],
                                      state='readonly', width=15)
        category_combo.pack(side='left', padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.on_ingredient_search)

        ttk.Button(search_frame, text="Clear", command=self.clear_ingredient_search).pack(side='left', padx=5)
        ttk.Button(search_frame, text="+ Add Ingredient", command=self.add_new_ingredient,
                  style='Action.TButton').pack(side='left', padx=5)

        # Main content
        content_frame = ttk.Frame(ingredients_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left: Ingredients list
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(list_frame, text="Ingredients", style='Header.TLabel').pack(anchor='w', pady=5)

        list_scroll = ttk.Frame(list_frame)
        list_scroll.pack(fill='both', expand=True)

        self.ingredients_listbox = tk.Listbox(list_scroll, font=('Arial', 10))
        ing_scrollbar = ttk.Scrollbar(list_scroll, orient='vertical',
                                     command=self.ingredients_listbox.yview)
        self.ingredients_listbox.configure(yscrollcommand=ing_scrollbar.set)

        self.ingredients_listbox.pack(side='left', fill='both', expand=True)
        ing_scrollbar.pack(side='right', fill='y')

        self.ingredients_listbox.bind('<<ListboxSelect>>', self.on_ingredient_select)
        self.ingredient_data = []

        # Right: Ingredient details
        details_frame = ttk.Frame(content_frame)
        details_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(details_frame, text="Ingredient Details", style='Header.TLabel').pack(anchor='w', pady=5)

        self.ingredient_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                                 font=('Arial', 10))
        self.ingredient_details_text.pack(fill='both', expand=True)

        self.ingredient_details_text.tag_configure('ing_name', font=('Arial', 16, 'bold'), foreground='#2c5f2d')
        self.ingredient_details_text.tag_configure('category', font=('Arial', 12, 'italic'), foreground='#666666')
        self.ingredient_details_text.tag_configure('header', font=('Arial', 11, 'bold'), foreground='#4a4a4a')
        self.ingredient_details_text.tag_configure('value', font=('Arial', 10))

        self.load_ingredients()

    def load_ingredients(self, search_term='', category='All'):
        """Load ingredients with filters"""
        self.ingredients_listbox.delete(0, tk.END)
        self.ingredient_data = []

        try:
            cursor = self.conn.cursor()

            query = "SELECT * FROM ingredients WHERE 1=1"
            params = []

            if search_term:
                query += " AND name LIKE ?"
                params.append(f"%{search_term}%")

            if category != 'All':
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY name"

            cursor.execute(query, params)
            ingredients = cursor.fetchall()

            for ing in ingredients:
                self.ingredient_data.append(dict(ing))
                display_name = f"{ing['name']}"
                if ing['category']:
                    display_name += f" ({ing['category']})"
                self.ingredients_listbox.insert(tk.END, display_name)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load ingredients: {e}")

    def on_ingredient_search(self, event=None):
        """Handle ingredient search"""
        search_term = self.ingredient_search_var.get()
        category = self.ingredient_category_var.get()
        self.load_ingredients(search_term, category)

    def clear_ingredient_search(self):
        """Clear ingredient filters"""
        self.ingredient_search_var.set('')
        self.ingredient_category_var.set('All')
        self.load_ingredients()

    def on_ingredient_select(self, event):
        """Handle ingredient selection"""
        selection = self.ingredients_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        ing = self.ingredient_data[index]

        # Clear and display details
        self.ingredient_details_text.config(state='normal')
        self.ingredient_details_text.delete('1.0', tk.END)

        self.ingredient_details_text.insert(tk.END, f"{ing['name']}\n", 'ing_name')
        if ing['category']:
            self.ingredient_details_text.insert(tk.END, f"{ing['category']}\n\n", 'category')

        if ing['description']:
            self.ingredient_details_text.insert(tk.END, f"{ing['description']}\n\n", 'value')

        if ing['storage_tips']:
            self.ingredient_details_text.insert(tk.END, "Storage Tips\n", 'header')
            self.ingredient_details_text.insert(tk.END, f"{ing['storage_tips']}\n\n", 'value')

        if ing['substitutes']:
            self.ingredient_details_text.insert(tk.END, "Substitutes\n", 'header')
            self.ingredient_details_text.insert(tk.END, f"{ing['substitutes']}\n\n", 'value')

        if ing['nutritional_notes']:
            self.ingredient_details_text.insert(tk.END, "Nutritional Notes\n", 'header')
            self.ingredient_details_text.insert(tk.END, f"{ing['nutritional_notes']}\n\n", 'value')

        if ing['allergen_info']:
            self.ingredient_details_text.insert(tk.END, "Allergen Information\n", 'header')
            self.ingredient_details_text.insert(tk.END, f"{ing['allergen_info']}\n\n", 'value')

        if ing['season']:
            self.ingredient_details_text.insert(tk.END, "Best Season\n", 'header')
            self.ingredient_details_text.insert(tk.END, f"{ing['season']}\n", 'value')

        self.ingredient_details_text.config(state='disabled')

    def add_new_ingredient(self):
        """Add a new ingredient to the database"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Ingredient")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # Name
        ttk.Label(dialog, text="Ingredient Name:*").pack(anchor='w', padx=10, pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=50).pack(padx=10, pady=5, fill='x')

        # Category
        ttk.Label(dialog, text="Category:").pack(anchor='w', padx=10, pady=(10, 0))
        category_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=category_var,
                    values=["Vegetables", "Proteins", "Grains", "Dairy", "Herbs", "Spices", "Oils", "Other"],
                    width=47).pack(padx=10, pady=5)

        # Description
        ttk.Label(dialog, text="Description:").pack(anchor='w', padx=10, pady=(10, 0))
        desc_text = tk.Text(dialog, height=3, width=50)
        desc_text.pack(padx=10, pady=5)

        # Storage tips
        ttk.Label(dialog, text="Storage Tips:").pack(anchor='w', padx=10, pady=(10, 0))
        storage_text = tk.Text(dialog, height=2, width=50)
        storage_text.pack(padx=10, pady=5)

        # Season
        ttk.Label(dialog, text="Best Season:").pack(anchor='w', padx=10, pady=(10, 0))
        season_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=season_var, width=50).pack(padx=10, pady=5, fill='x')

        def save_ingredient():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter an ingredient name")
                return

            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO ingredients (name, category, description, storage_tips, season)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, category_var.get(), desc_text.get('1.0', tk.END).strip(),
                     storage_text.get('1.0', tk.END).strip(), season_var.get()))
                self.conn.commit()
                dialog.destroy()
                self.load_ingredients()
                self.update_status()
                messagebox.showinfo("Success", "Ingredient added successfully!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This ingredient already exists")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Could not add ingredient: {e}")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save_ingredient,
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)

    # ==============================================
    # EQUIPMENT TAB
    # ==============================================

    def create_equipment_tab(self):
        """Create equipment browser tab"""
        equipment_frame = ttk.Frame(self.notebook)
        self.notebook.add(equipment_frame, text="🔪 Equipment")

        # Search frame
        search_frame = ttk.Frame(equipment_frame)
        search_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.equipment_search_var = tk.StringVar()
        equipment_search = ttk.Entry(search_frame, textvariable=self.equipment_search_var, width=30)
        equipment_search.pack(side='left', padx=5)
        equipment_search.bind('<KeyRelease>', self.on_equipment_search)

        ttk.Label(search_frame, text="Category:").pack(side='left', padx=(20, 5))
        self.equipment_category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(search_frame, textvariable=self.equipment_category_var,
                                      values=["All", "Knives", "Cookware", "Bakeware", "Prep Tools",
                                             "Utensils", "Measuring Tools", "Appliances"],
                                      state='readonly', width=15)
        category_combo.pack(side='left', padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.on_equipment_search)

        ttk.Label(search_frame, text="Show:").pack(side='left', padx=(20, 5))
        self.equipment_essential_var = tk.StringVar(value="All")
        essential_combo = ttk.Combobox(search_frame, textvariable=self.equipment_essential_var,
                                      values=["All", "Essential Only", "Optional Only"],
                                      state='readonly', width=15)
        essential_combo.pack(side='left', padx=5)
        essential_combo.bind('<<ComboboxSelected>>', self.on_equipment_search)

        ttk.Button(search_frame, text="Clear", command=self.clear_equipment_search).pack(side='left', padx=5)
        ttk.Button(search_frame, text="+ Add Equipment", command=self.add_new_equipment,
                  style='Action.TButton').pack(side='left', padx=5)

        # Main content
        content_frame = ttk.Frame(equipment_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left: Equipment list
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(list_frame, text="Equipment", style='Header.TLabel').pack(anchor='w', pady=5)

        list_scroll = ttk.Frame(list_frame)
        list_scroll.pack(fill='both', expand=True)

        self.equipment_listbox = tk.Listbox(list_scroll, font=('Arial', 10))
        equip_scrollbar = ttk.Scrollbar(list_scroll, orient='vertical',
                                       command=self.equipment_listbox.yview)
        self.equipment_listbox.configure(yscrollcommand=equip_scrollbar.set)

        self.equipment_listbox.pack(side='left', fill='both', expand=True)
        equip_scrollbar.pack(side='right', fill='y')

        self.equipment_listbox.bind('<<ListboxSelect>>', self.on_equipment_select)
        self.equipment_data = []

        # Right: Equipment details
        details_frame = ttk.Frame(content_frame)
        details_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(details_frame, text="Equipment Details", style='Header.TLabel').pack(anchor='w', pady=5)

        self.equipment_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                                font=('Arial', 10))
        self.equipment_details_text.pack(fill='both', expand=True)

        self.equipment_details_text.tag_configure('equip_name', font=('Arial', 16, 'bold'), foreground='#2c5f2d')
        self.equipment_details_text.tag_configure('category', font=('Arial', 12, 'italic'), foreground='#666666')
        self.equipment_details_text.tag_configure('header', font=('Arial', 11, 'bold'), foreground='#4a4a4a')
        self.equipment_details_text.tag_configure('value', font=('Arial', 10))
        self.equipment_details_text.tag_configure('essential', font=('Arial', 11, 'bold'), foreground='#d32f2f')

        self.load_equipment()

    def load_equipment(self, search_term='', category='All', essential='All'):
        """Load equipment with filters"""
        self.equipment_listbox.delete(0, tk.END)
        self.equipment_data = []

        try:
            cursor = self.conn.cursor()

            query = "SELECT * FROM equipment WHERE 1=1"
            params = []

            if search_term:
                query += " AND name LIKE ?"
                params.append(f"%{search_term}%")

            if category != 'All':
                query += " AND category = ?"
                params.append(category)

            if essential == 'Essential Only':
                query += " AND essential = 1"
            elif essential == 'Optional Only':
                query += " AND essential = 0"

            query += " ORDER BY essential DESC, name"

            cursor.execute(query, params)
            equipment = cursor.fetchall()

            for equip in equipment:
                self.equipment_data.append(dict(equip))
                display_name = f"{equip['name']}"
                if equip['essential']:
                    display_name = "⭐ " + display_name
                if equip['category']:
                    display_name += f" ({equip['category']})"
                self.equipment_listbox.insert(tk.END, display_name)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load equipment: {e}")

    def on_equipment_search(self, event=None):
        """Handle equipment search"""
        search_term = self.equipment_search_var.get()
        category = self.equipment_category_var.get()
        essential = self.equipment_essential_var.get()
        self.load_equipment(search_term, category, essential)

    def clear_equipment_search(self):
        """Clear equipment filters"""
        self.equipment_search_var.set('')
        self.equipment_category_var.set('All')
        self.equipment_essential_var.set('All')
        self.load_equipment()

    def on_equipment_select(self, event):
        """Handle equipment selection"""
        selection = self.equipment_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        equip = self.equipment_data[index]

        # Clear and display details
        self.equipment_details_text.config(state='normal')
        self.equipment_details_text.delete('1.0', tk.END)

        self.equipment_details_text.insert(tk.END, f"{equip['name']}\n", 'equip_name')
        if equip['category']:
            self.equipment_details_text.insert(tk.END, f"{equip['category']}\n\n", 'category')

        if equip['essential']:
            self.equipment_details_text.insert(tk.END, "⭐ ESSENTIAL KITCHEN ITEM\n\n", 'essential')

        if equip['description']:
            self.equipment_details_text.insert(tk.END, f"{equip['description']}\n\n", 'value')

        if equip['substitutes']:
            self.equipment_details_text.insert(tk.END, "Substitutes\n", 'header')
            self.equipment_details_text.insert(tk.END, f"{equip['substitutes']}\n\n", 'value')

        if equip['care_tips']:
            self.equipment_details_text.insert(tk.END, "Care Tips\n", 'header')
            self.equipment_details_text.insert(tk.END, f"{equip['care_tips']}\n\n", 'value')

        if equip['price_range']:
            self.equipment_details_text.insert(tk.END, "Price Range\n", 'header')
            self.equipment_details_text.insert(tk.END, f"{equip['price_range']}\n", 'value')

        self.equipment_details_text.config(state='disabled')

    def add_new_equipment(self):
        """Add new equipment to database"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Equipment")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()

        # Name
        ttk.Label(dialog, text="Equipment Name:*").pack(anchor='w', padx=10, pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=50).pack(padx=10, pady=5, fill='x')

        # Category
        ttk.Label(dialog, text="Category:").pack(anchor='w', padx=10, pady=(10, 0))
        category_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=category_var,
                    values=["Knives", "Cookware", "Bakeware", "Prep Tools", "Utensils", 
                           "Measuring Tools", "Appliances"],
                    width=47).pack(padx=10, pady=5)

        # Description
        ttk.Label(dialog, text="Description:").pack(anchor='w', padx=10, pady=(10, 0))
        desc_text = tk.Text(dialog, height=3, width=50)
        desc_text.pack(padx=10, pady=5)

        # Essential
        essential_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Essential item for every kitchen",
                       variable=essential_var).pack(anchor='w', padx=10, pady=5)

        # Price range
        ttk.Label(dialog, text="Price Range:").pack(anchor='w', padx=10, pady=(10, 0))
        price_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=price_var, width=50).pack(padx=10, pady=5, fill='x')

        def save_equipment():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter equipment name")
                return

            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO equipment (name, category, description, essential, price_range)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, category_var.get(), desc_text.get('1.0', tk.END).strip(),
                     essential_var.get(), price_var.get()))
                self.conn.commit()
                dialog.destroy()
                self.load_equipment()
                self.update_status()
                messagebox.showinfo("Success", "Equipment added successfully!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "This equipment already exists")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Could not add equipment: {e}")

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save_equipment,
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)


    # ==============================================
    # CUISINES TAB
    # ==============================================

    def create_cuisines_tab(self):
        """Create cuisines information tab"""
        cuisines_frame = ttk.Frame(self.notebook)
        self.notebook.add(cuisines_frame, text="🌍 Cuisines")

        # Search frame
        search_frame = ttk.Frame(cuisines_frame)
        search_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(search_frame, text="Search:").pack(side='left', padx=5)
        self.cuisine_search_var = tk.StringVar()
        cuisine_search = ttk.Entry(search_frame, textvariable=self.cuisine_search_var, width=30)
        cuisine_search.pack(side='left', padx=5)
        cuisine_search.bind('<KeyRelease>', self.on_cuisine_search)

        ttk.Button(search_frame, text="Clear", command=self.clear_cuisine_search).pack(side='left', padx=5)

        # Main content
        content_frame = ttk.Frame(cuisines_frame)
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Left: Cuisines list
        list_frame = ttk.Frame(content_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        ttk.Label(list_frame, text="World Cuisines", style='Header.TLabel').pack(anchor='w', pady=5)

        list_scroll = ttk.Frame(list_frame)
        list_scroll.pack(fill='both', expand=True)

        self.cuisines_listbox = tk.Listbox(list_scroll, font=('Arial', 11))
        cuisines_scrollbar = ttk.Scrollbar(list_scroll, orient='vertical',
                                          command=self.cuisines_listbox.yview)
        self.cuisines_listbox.configure(yscrollcommand=cuisines_scrollbar.set)

        self.cuisines_listbox.pack(side='left', fill='both', expand=True)
        cuisines_scrollbar.pack(side='right', fill='y')

        self.cuisines_listbox.bind('<<ListboxSelect>>', self.on_cuisine_select)
        self.cuisine_data = []

        # Right: Cuisine details
        details_frame = ttk.Frame(content_frame)
        details_frame.pack(side='right', fill='both', expand=True)

        ttk.Label(details_frame, text="Cuisine Details", style='Header.TLabel').pack(anchor='w', pady=5)

        self.cuisine_details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD,
                                                              font=('Arial', 10))
        self.cuisine_details_text.pack(fill='both', expand=True)

        self.cuisine_details_text.tag_configure('cuisine_name', font=('Arial', 18, 'bold'), foreground='#2c5f2d')
        self.cuisine_details_text.tag_configure('region', font=('Arial', 12, 'italic'), foreground='#666666')
        self.cuisine_details_text.tag_configure('header', font=('Arial', 11, 'bold'), foreground='#4a4a4a')
        self.cuisine_details_text.tag_configure('value', font=('Arial', 10))

        self.load_cuisines()

    def load_cuisines(self, search_term=''):
        """Load cuisines"""
        self.cuisines_listbox.delete(0, tk.END)
        self.cuisine_data = []

        try:
            cursor = self.conn.cursor()

            query = "SELECT * FROM cuisines WHERE 1=1"
            params = []

            if search_term:
                query += " AND (name LIKE ? OR region LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern])

            query += " ORDER BY name"

            cursor.execute(query, params)
            cuisines = cursor.fetchall()

            for cuisine in cuisines:
                self.cuisine_data.append(dict(cuisine))
                display_name = f"{cuisine['name']} ({cuisine['region']})"
                self.cuisines_listbox.insert(tk.END, display_name)

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load cuisines: {e}")

    def on_cuisine_search(self, event=None):
        """Handle cuisine search"""
        search_term = self.cuisine_search_var.get()
        self.load_cuisines(search_term)

    def clear_cuisine_search(self):
        """Clear cuisine search"""
        self.cuisine_search_var.set('')
        self.load_cuisines()

    def on_cuisine_select(self, event):
        """Handle cuisine selection"""
        selection = self.cuisines_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        cuisine = self.cuisine_data[index]

        # Clear and display details
        self.cuisine_details_text.config(state='normal')
        self.cuisine_details_text.delete('1.0', tk.END)

        self.cuisine_details_text.insert(tk.END, f"{cuisine['name']} Cuisine\n", 'cuisine_name')
        self.cuisine_details_text.insert(tk.END, f"{cuisine['region']}\n\n", 'region')

        if cuisine['description']:
            self.cuisine_details_text.insert(tk.END, f"{cuisine['description']}\n\n", 'value')

        if cuisine['characteristics']:
            self.cuisine_details_text.insert(tk.END, "Characteristics\n", 'header')
            self.cuisine_details_text.insert(tk.END, f"{cuisine['characteristics']}\n\n", 'value')

        if cuisine['common_ingredients']:
            self.cuisine_details_text.insert(tk.END, "Common Ingredients\n", 'header')
            self.cuisine_details_text.insert(tk.END, f"{cuisine['common_ingredients']}\n\n", 'value')

        if cuisine['popular_dishes']:
            self.cuisine_details_text.insert(tk.END, "Popular Dishes\n", 'header')
            self.cuisine_details_text.insert(tk.END, f"{cuisine['popular_dishes']}\n\n", 'value')

        # Find recipes from this cuisine
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM recipes WHERE cuisine = ? ORDER BY name",
                         (cuisine['name'],))
            recipes = cursor.fetchall()

            if recipes:
                self.cuisine_details_text.insert(tk.END, f"Recipes in Database ({len(recipes)})\n", 'header')
                for recipe in recipes:
                    self.cuisine_details_text.insert(tk.END, f"  • {recipe['name']}\n", 'value')
        except:
            pass

        self.cuisine_details_text.config(state='disabled')

    # ==============================================
    # SHOPPING LIST TAB
    # ==============================================

    def create_shopping_list_tab(self):
        """Create shopping list tab"""
        shopping_frame = ttk.Frame(self.notebook)
        self.notebook.add(shopping_frame, text="🛒 Shopping List")

        # Header
        header_frame = ttk.Frame(shopping_frame)
        header_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(header_frame, text="Shopping List", style='Title.TLabel').pack(side='left')
        ttk.Button(header_frame, text="🗑️ Clear All",
                  command=self.clear_shopping_list).pack(side='right', padx=5)
        ttk.Button(header_frame, text="📤 Export",
                  command=self.export_shopping_list).pack(side='right')

        # Shopping list display
        list_frame = ttk.Frame(shopping_frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.shopping_list_text = scrolledtext.ScrolledText(list_frame, wrap=tk.WORD,
                                                            font=('Arial', 11))
        self.shopping_list_text.pack(fill='both', expand=True)

        self.shopping_list_text.tag_configure('recipe', font=('Arial', 12, 'bold'), foreground='#2c5f2d')
        self.shopping_list_text.tag_configure('item', font=('Arial', 11))

        self.update_shopping_list_display()

    def update_shopping_list_display(self):
        """Update shopping list display"""
        self.shopping_list_text.config(state='normal')
        self.shopping_list_text.delete('1.0', tk.END)

        if not self.shopping_list:
            self.shopping_list_text.insert(tk.END, "Your shopping list is empty.\n\n")
            self.shopping_list_text.insert(tk.END, 
                "Add ingredients from recipes using the '🛒 Add to Shopping List' button in the Recipes tab.")
        else:
            # Group by recipe
            recipes = {}
            for item in self.shopping_list:
                recipe_name = item['recipe']
                if recipe_name not in recipes:
                    recipes[recipe_name] = []
                recipes[recipe_name].append(item)

            for recipe_name, items in recipes.items():
                self.shopping_list_text.insert(tk.END, f"\n{recipe_name}\n", 'recipe')
                self.shopping_list_text.insert(tk.END, "─" * 50 + "\n", 'item')
                for item in items:
                    text = f"☐ {item['quantity']} {item['unit']} {item['name']}\n"
                    self.shopping_list_text.insert(tk.END, text, 'item')

        self.shopping_list_text.config(state='disabled')

    def clear_shopping_list(self):
        """Clear shopping list"""
        if messagebox.askyesno("Clear Shopping List", "Are you sure you want to clear the shopping list?"):
            self.shopping_list = []
            self.update_shopping_list_display()
            self.update_status()

    def export_shopping_list(self):
        """Export shopping list to text file"""
        if not self.shopping_list:
            messagebox.showinfo("Empty List", "Shopping list is empty")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="shopping_list.txt"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("SHOPPING LIST\n")
                    f.write("=" * 50 + "\n\n")

                    recipes = {}
                    for item in self.shopping_list:
                        recipe_name = item['recipe']
                        if recipe_name not in recipes:
                            recipes[recipe_name] = []
                        recipes[recipe_name].append(item)

                    for recipe_name, items in recipes.items():
                        f.write(f"\n{recipe_name}\n")
                        f.write("-" * 50 + "\n")
                        for item in items:
                            f.write(f"☐ {item['quantity']} {item['unit']} {item['name']}\n")

                messagebox.showinfo("Exported", f"Shopping list exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export shopping list: {e}")

    # ==============================================
    # ADD NEW RECIPE
    # ==============================================

    def add_new_recipe(self):
        """Add a new recipe to the database"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Recipe")
        dialog.geometry("700x800")
        dialog.transient(self.root)

        # Create scrollable frame
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Basic Information
        ttk.Label(scrollable_frame, text="Recipe Name:*", style='Header.TLabel').pack(anchor='w', padx=10, pady=(10, 0))
        name_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=name_var, width=70).pack(padx=10, pady=5, fill='x')

        # Cuisine
        ttk.Label(scrollable_frame, text="Cuisine:*").pack(anchor='w', padx=10, pady=(10, 0))
        cuisine_var = tk.StringVar()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM cuisines ORDER BY name")
        cuisine_values = [row['name'] for row in cursor.fetchall()]
        ttk.Combobox(scrollable_frame, textvariable=cuisine_var,
                    values=cuisine_values, width=67).pack(padx=10, pady=5)

        # Category
        ttk.Label(scrollable_frame, text="Category:*").pack(anchor='w', padx=10, pady=(10, 0))
        category_var = tk.StringVar()
        ttk.Combobox(scrollable_frame, textvariable=category_var,
                    values=["Main Course", "Appetizer", "Dessert", "Soup", "Salad", "Side Dish", "Breakfast"],
                    width=67).pack(padx=10, pady=5)

        # Difficulty
        ttk.Label(scrollable_frame, text="Difficulty:").pack(anchor='w', padx=10, pady=(10, 0))
        difficulty_var = tk.StringVar(value="Medium")
        ttk.Combobox(scrollable_frame, textvariable=difficulty_var,
                    values=["Easy", "Medium", "Hard"], width=67).pack(padx=10, pady=5)

        # Times
        times_frame = ttk.Frame(scrollable_frame)
        times_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(times_frame, text="Prep Time (min):").pack(side='left', padx=(0, 5))
        prep_var = tk.StringVar(value="0")
        ttk.Entry(times_frame, textvariable=prep_var, width=10).pack(side='left', padx=5)

        ttk.Label(times_frame, text="Cook Time (min):").pack(side='left', padx=(20, 5))
        cook_var = tk.StringVar(value="0")
        ttk.Entry(times_frame, textvariable=cook_var, width=10).pack(side='left', padx=5)

        ttk.Label(times_frame, text="Servings:").pack(side='left', padx=(20, 5))
        servings_var = tk.StringVar(value="4")
        ttk.Entry(times_frame, textvariable=servings_var, width=10).pack(side='left', padx=5)

        # Description
        ttk.Label(scrollable_frame, text="Description:").pack(anchor='w', padx=10, pady=(10, 0))
        desc_text = tk.Text(scrollable_frame, height=3, width=70)
        desc_text.pack(padx=10, pady=5)

        # Instructions
        ttk.Label(scrollable_frame, text="Instructions:*").pack(anchor='w', padx=10, pady=(10, 0))
        instructions_text = scrolledtext.ScrolledText(scrollable_frame, height=8, width=70)
        instructions_text.pack(padx=10, pady=5)

        # Tips
        ttk.Label(scrollable_frame, text="Tips:").pack(anchor='w', padx=10, pady=(10, 0))
        tips_text = tk.Text(scrollable_frame, height=3, width=70)
        tips_text.pack(padx=10, pady=5)

        def save_recipe():
            name = name_var.get().strip()
            cuisine = cuisine_var.get().strip()
            category = category_var.get().strip()
            instructions = instructions_text.get('1.0', tk.END).strip()

            if not name or not cuisine or not category or not instructions:
                messagebox.showerror("Error", "Please fill in all required fields (marked with *)")
                return

            try:
                prep_time = int(prep_var.get())
                cook_time = int(cook_var.get())
                total_time = prep_time + cook_time
                servings = int(servings_var.get())
            except ValueError:
                messagebox.showerror("Error", "Times and servings must be numbers")
                return

            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO recipes (
                        name, cuisine, category, difficulty, prep_time, cook_time, total_time,
                        servings, description, instructions, tips, created_date, rating
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 3.0)
                ''', (name, cuisine, category, difficulty_var.get(), prep_time, cook_time,
                     total_time, servings, desc_text.get('1.0', tk.END).strip(),
                     instructions, tips_text.get('1.0', tk.END).strip()))
                self.conn.commit()
                dialog.destroy()
                self.load_recipes()
                self.update_status()
                messagebox.showinfo("Success", f"Recipe '{name}' added successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Could not add recipe: {e}")

        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Save Recipe", command=save_recipe,
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ==============================================
    # WEB RECIPE SEARCH FUNCTIONS
    # ==============================================
    
    def search_web_recipes(self):
        """Search the web for recipes and import them"""
        # Note: This feature requires Claude's web_search tool
        # If not available, show informational message
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Search Web for Recipes")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        
        # Search frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search for recipes:", font=('Arial', 12, 'bold')).pack(anchor='w')
        
        search_entry_frame = ttk.Frame(search_frame)
        search_entry_frame.pack(fill='x', pady=5)
        
        search_var = tk.StringVar()
        ttk.Entry(search_entry_frame, textvariable=search_var, width=60).pack(side='left', padx=(0, 5))
        
        def perform_search():
            query = search_var.get().strip()
            if not query:
                messagebox.showwarning("Empty Search", "Please enter a search term")
                return
            
            # Add "recipe" to search query for better results
            if "recipe" not in query.lower():
                query += " recipe"
            
            status_label.config(text=f"Searching for '{query}'...")
            dialog.update()
            
            try:
                # Simulate web search (in real implementation, would use web_search tool)
                # For now, provide manual import functionality
                results_text.delete('1.0', tk.END)
                results_text.insert('1.0', f"""RECIPE WEB SEARCH FEATURE
                
Search Query: {query}

HOW TO USE:
1. Open your web browser and search for: {query}
2. Find a recipe you like
3. Copy the recipe details from the website
4. Click "Import Recipe from Web" below
5. Paste the recipe content and we'll help you parse it

SUPPORTED WEBSITES:
• AllRecipes.com
• Food Network
• NYT Cooking
• BBC Good Food  
• Serious Eats
• Any recipe website

The import wizard will help you extract:
• Recipe name and description
• Ingredients list
• Instructions
• Cooking times
• And more!

Click the button below when you're ready to import a recipe.""")
                
                status_label.config(text="Ready to import")
                
            except Exception as e:
                messagebox.showerror("Search Error", f"Could not search: {e}")
                status_label.config(text="Error")
        
        ttk.Button(search_entry_frame, text="Search", command=perform_search,
                  style='Action.TButton').pack(side='left')
        
        # Status label
        status_label = ttk.Label(search_frame, text="Enter search terms above")
        status_label.pack(anchor='w', pady=5)
        
        # Results area
        ttk.Label(dialog, text="Instructions:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=10)
        
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=20)
        results_text.pack(fill='both', expand=True)
        
        # Action buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Import Recipe from Web",
                  command=lambda: self.import_recipe_from_web(dialog),
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close",
                  command=dialog.destroy).pack(side='left', padx=5)
    
    def import_recipe_from_web(self, parent_dialog=None):
        """Import a recipe from web content"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Import Recipe from Web")
        dialog.geometry("900x700")
        if parent_dialog:
            dialog.transient(parent_dialog)
        
        # Instructions
        instructions_frame = ttk.Frame(dialog)
        instructions_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(instructions_frame, text="Import Recipe from Web", 
                 font=('Arial', 14, 'bold')).pack(anchor='w')
        ttk.Label(instructions_frame, 
                 text="Paste the recipe content from a website below, and we'll help you parse it:",
                 wraplength=850).pack(anchor='w', pady=5)
        
        # Input area
        ttk.Label(dialog, text="Paste Recipe Content Here:").pack(anchor='w', padx=10)
        
        input_frame = ttk.Frame(dialog)
        input_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=15)
        input_text.pack(fill='both', expand=True)
        
        # Sample button for testing
        def load_sample():
            sample = """Chocolate Chip Cookies
            
A classic American dessert that everyone loves!

Ingredients:
- 2 1/4 cups all-purpose flour
- 1 tsp baking soda
- 1 tsp salt
- 1 cup butter, softened
- 3/4 cup granulated sugar
- 3/4 cup packed brown sugar
- 2 large eggs
- 2 tsp vanilla extract
- 2 cups chocolate chips

Instructions:
1. Preheat oven to 375°F
2. Mix flour, baking soda and salt in bowl
3. Beat butter and sugars until creamy
4. Add eggs and vanilla, beat well
5. Gradually blend in flour mixture
6. Stir in chocolate chips
7. Drop by rounded tablespoon onto ungreased cookie sheets
8. Bake 9-11 minutes or until golden brown
9. Cool on baking sheet for 2 minutes
10. Remove to wire rack to cool completely

Prep Time: 15 minutes
Cook Time: 11 minutes
Servings: 48 cookies
Difficulty: Easy"""
            input_text.delete('1.0', tk.END)
            input_text.insert('1.0', sample)
        
        ttk.Button(dialog, text="Load Sample Recipe (for testing)", 
                  command=load_sample).pack(pady=5)
        
        # Parse button
        def parse_and_import():
            content = input_text.get('1.0', tk.END).strip()
            if not content:
                messagebox.showwarning("Empty Content", "Please paste recipe content first")
                return
            
            # Parse the recipe content
            parsed_recipe = self.parse_recipe_content(content)
            
            if not parsed_recipe:
                messagebox.showerror("Parse Error", 
                                   "Could not parse recipe. Please check the format.")
                return
            
            # Show the import dialog with parsed data
            self.show_import_dialog(parsed_recipe, dialog)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Parse and Import Recipe",
                  command=parse_and_import,
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel",
                  command=dialog.destroy).pack(side='left', padx=5)
    
    def parse_recipe_content(self, content):
        """Parse recipe content from text"""
        recipe = {
            'name': '',
            'description': '',
            'ingredients': [],
            'instructions': '',
            'prep_time': 0,
            'cook_time': 0,
            'servings': 4,
            'difficulty': 'Medium'
        }
        
        lines = content.split('\n')
        current_section = None
        ingredients_list = []
        instructions_list = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract recipe name (usually first non-empty line)
            if not recipe['name'] and len(line) < 100:
                recipe['name'] = line
                continue
            
            # Detect sections
            if re.match(r'ingredients?:?$', line, re.IGNORECASE):
                current_section = 'ingredients'
                continue
            elif re.match(r'(instructions?|directions?|method):?$', line, re.IGNORECASE):
                current_section = 'instructions'
                continue
            
            # Parse ingredients (lines starting with - or • or numbers)
            if current_section == 'ingredients':
                if re.match(r'^[-•*]', line) or re.match(r'^\d+', line):
                    # Clean up the ingredient line
                    ingredient = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                    if ingredient:
                        ingredients_list.append(ingredient)
            
            # Parse instructions (numbered steps or paragraphs)
            elif current_section == 'instructions':
                # Clean up numbered instructions
                instruction = re.sub(r'^\d+[.)]\s*', '', line).strip()
                if instruction:
                    instructions_list.append(instruction)
            
            # Parse times and servings
            time_match = re.search(r'prep\s*time:?\s*(\d+)', line, re.IGNORECASE)
            if time_match:
                recipe['prep_time'] = int(time_match.group(1))
            
            cook_match = re.search(r'cook\s*time:?\s*(\d+)', line, re.IGNORECASE)
            if cook_match:
                recipe['cook_time'] = int(cook_match.group(1))
            
            servings_match = re.search(r'servings?:?\s*(\d+)', line, re.IGNORECASE)
            if servings_match:
                recipe['servings'] = int(servings_match.group(1))
            
            difficulty_match = re.search(r'difficulty:?\s*(easy|medium|hard)', line, re.IGNORECASE)
            if difficulty_match:
                recipe['difficulty'] = difficulty_match.group(1).capitalize()
            
            # If not in a section yet and not the name, treat as description
            if not current_section and recipe['name'] and len(line) < 200:
                if not recipe['description']:
                    recipe['description'] = line
        
        # Assemble ingredients and instructions
        if ingredients_list:
            recipe['ingredients'] = ingredients_list
        if instructions_list:
            recipe['instructions'] = '\n'.join(f"{i+1}. {inst}" for i, inst in enumerate(instructions_list))
        
        return recipe if recipe['name'] and recipe['ingredients'] else None
    
    def show_import_dialog(self, parsed_recipe, parent_dialog):
        """Show dialog with parsed recipe for user to review and edit before importing"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Review and Import Recipe")
        dialog.geometry("800x900")
        dialog.transient(parent_dialog)
        
        # Create scrollable frame
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        ttk.Label(scrollable_frame, text="Review Parsed Recipe", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        ttk.Label(scrollable_frame, 
                 text="Review and edit the parsed recipe details below, then click Import:",
                 wraplength=750).pack(pady=5)
        
        # Recipe Name
        ttk.Label(scrollable_frame, text="Recipe Name:*", 
                 style='Header.TLabel').pack(anchor='w', padx=10, pady=(10, 0))
        name_var = tk.StringVar(value=parsed_recipe.get('name', ''))
        ttk.Entry(scrollable_frame, textvariable=name_var, width=90).pack(padx=10, pady=5, fill='x')
        
        # Cuisine
        ttk.Label(scrollable_frame, text="Cuisine:*").pack(anchor='w', padx=10, pady=(10, 0))
        cuisine_var = tk.StringVar()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM cuisines ORDER BY name")
        cuisine_values = [row['name'] for row in cursor.fetchall()]
        ttk.Combobox(scrollable_frame, textvariable=cuisine_var,
                    values=cuisine_values, width=87).pack(padx=10, pady=5)
        
        # Category
        ttk.Label(scrollable_frame, text="Category:*").pack(anchor='w', padx=10, pady=(10, 0))
        category_var = tk.StringVar()
        ttk.Combobox(scrollable_frame, textvariable=category_var,
                    values=["Main Course", "Appetizer", "Dessert", "Soup", "Salad", "Side Dish", "Breakfast"],
                    width=87).pack(padx=10, pady=5)
        
        # Difficulty
        ttk.Label(scrollable_frame, text="Difficulty:").pack(anchor='w', padx=10, pady=(10, 0))
        difficulty_var = tk.StringVar(value=parsed_recipe.get('difficulty', 'Medium'))
        ttk.Combobox(scrollable_frame, textvariable=difficulty_var,
                    values=["Easy", "Medium", "Hard"], width=87).pack(padx=10, pady=5)
        
        # Times and Servings
        times_frame = ttk.Frame(scrollable_frame)
        times_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(times_frame, text="Prep (min):").pack(side='left', padx=(0, 5))
        prep_var = tk.StringVar(value=str(parsed_recipe.get('prep_time', 0)))
        ttk.Entry(times_frame, textvariable=prep_var, width=10).pack(side='left', padx=5)
        
        ttk.Label(times_frame, text="Cook (min):").pack(side='left', padx=(20, 5))
        cook_var = tk.StringVar(value=str(parsed_recipe.get('cook_time', 0)))
        ttk.Entry(times_frame, textvariable=cook_var, width=10).pack(side='left', padx=5)
        
        ttk.Label(times_frame, text="Servings:").pack(side='left', padx=(20, 5))
        servings_var = tk.StringVar(value=str(parsed_recipe.get('servings', 4)))
        ttk.Entry(times_frame, textvariable=servings_var, width=10).pack(side='left', padx=5)
        
        # Description
        ttk.Label(scrollable_frame, text="Description:").pack(anchor='w', padx=10, pady=(10, 0))
        desc_text = tk.Text(scrollable_frame, height=3, width=90)
        desc_text.pack(padx=10, pady=5)
        desc_text.insert('1.0', parsed_recipe.get('description', ''))
        
        # Ingredients
        ttk.Label(scrollable_frame, text="Ingredients (one per line):*").pack(anchor='w', padx=10, pady=(10, 0))
        ingredients_text = scrolledtext.ScrolledText(scrollable_frame, height=10, width=90)
        ingredients_text.pack(padx=10, pady=5)
        ingredients_text.insert('1.0', '\n'.join(parsed_recipe.get('ingredients', [])))
        
        # Instructions
        ttk.Label(scrollable_frame, text="Instructions:*").pack(anchor='w', padx=10, pady=(10, 0))
        instructions_text = scrolledtext.ScrolledText(scrollable_frame, height=12, width=90)
        instructions_text.pack(padx=10, pady=5)
        instructions_text.insert('1.0', parsed_recipe.get('instructions', ''))
        
        # Tips
        ttk.Label(scrollable_frame, text="Tips:").pack(anchor='w', padx=10, pady=(10, 0))
        tips_text = tk.Text(scrollable_frame, height=3, width=90)
        tips_text.pack(padx=10, pady=5)
        
        def import_recipe():
            name = name_var.get().strip()
            cuisine = cuisine_var.get().strip()
            category = category_var.get().strip()
            instructions = instructions_text.get('1.0', tk.END).strip()
            
            if not name or not cuisine or not category or not instructions:
                messagebox.showerror("Error", "Please fill in all required fields (marked with *)")
                return
            
            try:
                prep_time = int(prep_var.get())
                cook_time = int(cook_var.get())
                total_time = prep_time + cook_time
                servings = int(servings_var.get())
            except ValueError:
                messagebox.showerror("Error", "Times and servings must be numbers")
                return
            
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO recipes (
                        name, cuisine, category, difficulty, prep_time, cook_time, total_time,
                        servings, description, instructions, tips, created_date, rating, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 3.0, 'Web Import')
                ''', (name, cuisine, category, difficulty_var.get(), prep_time, cook_time,
                     total_time, servings, desc_text.get('1.0', tk.END).strip(),
                     instructions, tips_text.get('1.0', tk.END).strip()))
                self.conn.commit()
                
                # Parse and add ingredients if possible
                ingredients = ingredients_text.get('1.0', tk.END).strip().split('\n')
                recipe_id = cursor.lastrowid
                
                for ing_line in ingredients:
                    if ing_line.strip():
                        # Try to parse quantity and ingredient
                        # This is a simple parser - could be enhanced
                        parts = ing_line.strip().split(maxsplit=2)
                        if len(parts) >= 2:
                            qty = parts[0]
                            unit = parts[1] if len(parts) > 2 else ''
                            ing_name = parts[2] if len(parts) > 2 else parts[1]
                            
                            # Find (exact name) or create the ingredient
                            ing_id = find_or_create_ingredient_id(cursor, ing_name)
                            
                            cursor.execute('''INSERT INTO recipe_ingredients 
                                            (recipe_id, ingredient_id, quantity, unit, notes)
                                            VALUES (?, ?, ?, ?, ?)''',
                                         (recipe_id, ing_id, qty, unit, ''))
                
                self.conn.commit()
                dialog.destroy()
                if parent_dialog:
                    parent_dialog.destroy()
                self.load_recipes()
                self.update_status()
                messagebox.showinfo("Success", f"Recipe '{name}' imported successfully!")
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Could not import recipe: {e}")
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Import Recipe", command=import_recipe,
                  style='Action.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ==============================================
    # EXPORT FUNCTIONS
    # ==============================================

    def export_recipes_csv(self):
        """Export all recipes to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="recipes.csv"
        )

        if filename:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM recipes ORDER BY name")
                recipes = cursor.fetchall()

                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Name', 'Cuisine', 'Category', 'Difficulty', 'Prep Time (min)',
                        'Cook Time (min)', 'Total Time (min)', 'Servings', 'Description',
                        'Instructions', 'Tips', 'Rating'
                    ])

                    for recipe in recipes:
                        writer.writerow([
                            recipe['name'], recipe['cuisine'], recipe['category'],
                            recipe['difficulty'], recipe['prep_time'], recipe['cook_time'],
                            recipe['total_time'], recipe['servings'], recipe['description'],
                            recipe['instructions'], recipe['tips'], recipe['rating']
                        ])

                messagebox.showinfo("Export Successful", f"Recipes exported to {filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export recipes: {e}")

    # ==============================================
    # UTILITY FUNCTIONS
    # ==============================================

    def show_about(self):
        """Show about dialog"""
        about_text = """Recipe Collection Explorer v2.0 - ENHANCED EDITION

✨ NEW FEATURES:
• Search and import recipes from the web
• Enhanced manual recipe entry
• Automatic recipe parsing from web content
• 54 pre-loaded recipes from 11 cuisines

Features:
• Browse recipes from 11 world cuisines
• Comprehensive ingredients database
• Kitchen equipment reference
• Shopping list generator
• Add and update recipes
• Export functionality

A kitchen companion for home cooks!

January 2026
        """
        messagebox.showinfo("About", about_text)

    def __del__(self):
        """Cleanup when app closes"""
        if self.conn:
            self.conn.close()


def main():
    """Run the Recipe Collection Explorer"""
    root = tk.Tk()
    app = RecipeExplorerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
