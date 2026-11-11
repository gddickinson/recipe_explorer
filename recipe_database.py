"""
Recipe Collection Database - EXPANDED VERSION
Comprehensive database of 60+ recipes, ingredients, and cooking equipment
"""

import sqlite3
from pathlib import Path
import json

from db_operations import find_or_create_ingredient_id

class RecipeDatabase:
    def __init__(self, db_path="recipe_collection.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # Recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty TEXT,
                prep_time INTEGER,
                cook_time INTEGER,
                total_time INTEGER,
                servings INTEGER,
                description TEXT,
                instructions TEXT NOT NULL,
                tips TEXT,
                nutritional_info TEXT,
                dietary_tags TEXT,
                source TEXT,
                rating REAL,
                created_date TEXT,
                image_url TEXT
            )
        ''')
        
        # Ingredients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                storage_tips TEXT,
                substitutes TEXT,
                nutritional_notes TEXT,
                allergen_info TEXT,
                season TEXT
            )
        ''')
        
        # Equipment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                essential BOOLEAN,
                substitutes TEXT,
                care_tips TEXT,
                price_range TEXT
            )
        ''')
        
        # Recipe-Ingredients junction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                ingredient_id INTEGER,
                quantity TEXT,
                unit TEXT,
                notes TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
            )
        ''')
        
        # Recipe-Equipment junction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                equipment_id INTEGER,
                optional BOOLEAN,
                FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id),
                FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
            )
        ''')
        
        # Cuisines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cuisines (
                cuisine_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region TEXT,
                description TEXT,
                characteristics TEXT,
                common_ingredients TEXT,
                popular_dishes TEXT
            )
        ''')
        
        self.conn.commit()
        
    def populate_cuisines(self):
        """Populate cuisines table"""
        cursor = self.conn.cursor()
        
        cuisines_data = [
            ('Italian', 'Southern Europe', 'Known for pasta, pizza, and use of olive oil, tomatoes, and herbs',
             'Regional diversity, seasonal ingredients, pasta and risotto dishes',
             'Tomatoes, olive oil, garlic, basil, mozzarella, parmesan, pasta',
             'Pizza Margherita, Pasta Carbonara, Risotto, Tiramisu'),
            
            ('French', 'Western Europe', 'Refined techniques, rich sauces, and butter-based cooking',
             'Classic techniques, wine sauces, pastries, elegant presentation',
             'Butter, cream, wine, herbs de Provence, garlic, shallots',
             'Coq au Vin, Beef Bourguignon, Crème Brûlée, Croissants'),
            
            ('Chinese', 'East Asia', 'Diverse regional styles with emphasis on balance and harmony',
             'Wok cooking, stir-frying, steaming, balance of flavors',
             'Soy sauce, ginger, garlic, rice, sesame oil, green onions',
             'Kung Pao Chicken, Mapo Tofu, Dumplings, Fried Rice'),
            
            ('Japanese', 'East Asia', 'Emphasis on seasonality, minimal processing, and presentation',
             'Fresh ingredients, umami flavors, precise technique, aesthetics',
             'Rice, soy sauce, miso, dashi, seaweed, fish, sake',
             'Sushi, Ramen, Tempura, Teriyaki, Miso Soup'),
            
            ('Indian', 'South Asia', 'Complex spice blends and aromatic curries',
             'Diverse regional cuisines, use of spices, vegetarian traditions',
             'Turmeric, cumin, coriander, garam masala, ghee, lentils, rice',
             'Butter Chicken, Biryani, Tikka Masala, Dal, Naan'),
            
            ('Mexican', 'North America', 'Corn-based dishes, chili peppers, and bold flavors',
             'Ancient traditions, corn tortillas, beans, fresh salsas',
             'Corn, beans, chili peppers, tomatoes, cilantro, lime, avocado',
             'Tacos, Enchiladas, Guacamole, Mole, Tamales'),
            
            ('Thai', 'Southeast Asia', 'Balance of sweet, sour, salty, and spicy flavors',
             'Fresh herbs, balance of flavors, rice and noodle dishes',
             'Fish sauce, lemongrass, galangal, lime, coconut milk, chilies',
             'Pad Thai, Green Curry, Tom Yum, Papaya Salad'),
            
            ('Greek', 'Southern Europe', 'Mediterranean diet with olive oil, vegetables, and seafood',
             'Simple preparation, olive oil, fresh vegetables, grilled meats',
             'Olive oil, feta cheese, yogurt, lemon, oregano, lamb',
             'Moussaka, Souvlaki, Greek Salad, Tzatziki, Spanakopita'),
            
            ('Spanish', 'Southern Europe', 'Regional diversity with seafood, rice dishes, and tapas',
             'Small plates, seafood, rice dishes, olive oil',
             'Olive oil, saffron, paprika, garlic, tomatoes, seafood',
             'Paella, Gazpacho, Tapas, Tortilla Española'),
            
            ('Middle Eastern', 'Western Asia', 'Aromatic spices, grilled meats, and mezze spreads',
             'Spice blends, grilling, mezze platters, bread',
             'Tahini, chickpeas, lamb, yogurt, za\'atar, sumac, olive oil',
             'Hummus, Falafel, Shawarma, Tabbouleh, Baklava'),
            
            ('American', 'North America', 'Diverse regional styles with hearty comfort foods',
             'Grilling, barbecue, diverse immigrant influences',
             'Beef, potatoes, cheese, corn, tomatoes, peppers',
             'Burgers, BBQ Ribs, Mac and Cheese, Apple Pie'),
        ]
        
        for cuisine in cuisines_data:
            cursor.execute('''
                INSERT OR IGNORE INTO cuisines (name, region, description, characteristics, common_ingredients, popular_dishes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', cuisine)
        
        self.conn.commit()
        print(f"Populated {len(cuisines_data)} cuisines")
        
    def populate_ingredients(self):
        """Populate ingredients table"""
        cursor = self.conn.cursor()
        
        ingredients_data = [
            # Vegetables
            ('Tomato', 'Vegetables', 'Fresh tomatoes for cooking and salads', 
             'Store at room temperature until ripe, then refrigerate', 'Canned tomatoes, tomato paste',
             'Rich in vitamin C and lycopene', 'None', 'Summer'),
            ('Onion', 'Vegetables', 'Essential aromatic vegetable',
             'Store in cool, dry, dark place', 'Shallots, leeks, green onions',
             'Contains quercetin and vitamin C', 'May cause digestive issues for some', 'Year-round'),
            ('Garlic', 'Vegetables', 'Pungent aromatic used in many cuisines',
             'Store in cool, dry place with good ventilation', 'Garlic powder (1/8 tsp = 1 clove)',
             'Contains allicin with health benefits', 'May cause digestive issues', 'Year-round'),
            ('Bell Pepper', 'Vegetables', 'Sweet peppers in various colors',
             'Refrigerate in crisper drawer', 'Poblano peppers for mild heat',
             'High in vitamin C and antioxidants', 'None', 'Summer-Fall'),
            ('Carrot', 'Vegetables', 'Sweet root vegetable, versatile',
             'Refrigerate in plastic bag', 'Parsnips, sweet potato',
             'High in beta-carotene', 'None', 'Fall-Winter'),
            
            # Proteins
            ('Chicken Breast', 'Proteins', 'Lean white meat poultry',
             'Refrigerate 1-2 days or freeze up to 9 months', 'Turkey breast, tofu',
             'High protein, low fat', 'None', 'Year-round'),
            ('Beef', 'Proteins', 'Red meat from cattle',
             'Refrigerate 3-5 days or freeze up to 12 months', 'Lamb, pork, venison',
             'High in protein, iron, and B vitamins', 'None', 'Year-round'),
            ('Shrimp', 'Proteins', 'Popular shellfish',
             'Cook within 1-2 days or freeze', 'Prawns, scallops',
             'High protein, low calorie', 'Shellfish allergen', 'Year-round'),
            ('Salmon', 'Proteins', 'Fatty fish rich in omega-3',
             'Use within 2 days or freeze', 'Trout, arctic char',
             'High in omega-3 fatty acids', 'Fish allergen', 'Year-round'),
            ('Tofu', 'Proteins', 'Soy-based protein',
             'Keep refrigerated in water, change daily', 'Tempeh, seitan',
             'Complete plant protein', 'Soy allergen', 'Year-round'),
            ('Eggs', 'Proteins', 'Versatile protein source',
             'Refrigerate for up to 5 weeks', 'Flax eggs for baking',
             'Complete protein with vitamins', 'Egg allergen', 'Year-round'),
            
            # Grains
            ('Rice', 'Grains', 'Staple grain, many varieties',
             'Store in airtight container in cool place', 'Quinoa, cauliflower rice',
             'Energy source, some varieties rich in nutrients', 'Gluten-free', 'Year-round'),
            ('Pasta', 'Grains', 'Italian wheat-based noodles',
             'Store dry pasta in pantry up to 2 years', 'Rice noodles, zucchini noodles',
             'Carbohydrates for energy', 'Contains gluten', 'Year-round'),
            ('Flour', 'Grains', 'Ground grain for baking',
             'Store in airtight container, can freeze', 'Almond flour, coconut flour',
             'Source of carbohydrates', 'Contains gluten (wheat)', 'Year-round'),
            ('Bread', 'Grains', 'Baked staple food',
             'Store at room temp 2-3 days or freeze', 'Tortillas, pita, naan',
             'Source of carbohydrates and fiber', 'Contains gluten', 'Year-round'),
            
            # Dairy
            ('Butter', 'Dairy', 'Dairy fat used in cooking and baking',
             'Refrigerate or freeze for longer storage', 'Margarine, coconut oil',
             'High in fat and vitamin A', 'Dairy allergen', 'Year-round'),
            ('Milk', 'Dairy', 'Dairy beverage',
             'Refrigerate, use by date on carton', 'Almond milk, oat milk, soy milk',
             'Source of calcium and vitamin D', 'Dairy allergen', 'Year-round'),
            ('Cheese', 'Dairy', 'Fermented dairy product',
             'Wrap tightly and refrigerate', 'Nutritional yeast for vegan',
             'High in calcium and protein', 'Dairy allergen', 'Year-round'),
            ('Yogurt', 'Dairy', 'Fermented dairy product',
             'Refrigerate, check expiration date', 'Coconut yogurt',
             'Probiotics, protein, calcium', 'Dairy allergen', 'Year-round'),
            
            # Herbs & Spices
            ('Basil', 'Herbs', 'Fresh herb, essential in Italian cooking',
             'Store stems in water like flowers', 'Dried basil (use less)',
             'Contains antioxidants', 'None', 'Summer'),
            ('Cilantro', 'Herbs', 'Fresh herb used in many cuisines',
             'Store stems in water, refrigerate', 'Parsley, culantro',
             'Rich in vitamins', 'Some people have genetic aversion', 'Year-round'),
            ('Parsley', 'Herbs', 'Fresh herb for garnish and flavor',
             'Wrap in damp towel, refrigerate', 'Cilantro, celery leaves',
             'High in vitamins A, C, K', 'None', 'Year-round'),
            ('Oregano', 'Herbs', 'Mediterranean herb',
             'Dry or fresh, store dried in cool place', 'Marjoram, thyme',
             'Antioxidant properties', 'None', 'Year-round'),
            ('Cumin', 'Spices', 'Earthy spice used in many cuisines',
             'Store ground cumin in dark, cool place', 'Caraway, coriander',
             'Aids digestion', 'None', 'Year-round'),
            ('Paprika', 'Spices', 'Ground red pepper',
             'Store in cool, dark place', 'Cayenne for heat, chili powder',
             'Contains vitamin A', 'None', 'Year-round'),
            ('Black Pepper', 'Spices', 'Universal seasoning',
             'Store peppercorns in grinder', 'White pepper, red pepper flakes',
             'Contains piperine', 'None', 'Year-round'),
            ('Cinnamon', 'Spices', 'Sweet warming spice',
             'Store in cool, dark place', 'Nutmeg, allspice',
             'May help regulate blood sugar', 'None', 'Year-round'),
            
            # Oils & Condiments
            ('Olive Oil', 'Oils', 'Healthy cooking oil',
             'Store in cool, dark place', 'Avocado oil, canola oil',
             'Rich in monounsaturated fats', 'None', 'Year-round'),
            ('Soy Sauce', 'Condiments', 'Fermented soy-based sauce',
             'Store at room temp or refrigerate after opening', 'Tamari (gluten-free), coconut aminos',
             'High in sodium', 'Soy, wheat allergens', 'Year-round'),
            ('Fish Sauce', 'Condiments', 'Fermented fish sauce',
             'Store at room temp', 'Soy sauce, worcestershire sauce',
             'Source of umami', 'Fish allergen', 'Year-round'),
            ('Sesame Oil', 'Oils', 'Aromatic Asian oil',
             'Store in cool place', 'Peanut oil, walnut oil',
             'Rich flavor enhancer', 'Sesame allergen', 'Year-round'),
        ]
        
        for ing in ingredients_data:
            cursor.execute('''
                INSERT OR IGNORE INTO ingredients (
                    name, category, description, storage_tips, substitutes,
                    nutritional_notes, allergen_info, season
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ing)
        
        self.conn.commit()
        print(f"Populated {len(ingredients_data)} ingredients")
        
    def populate_equipment(self):
        """Populate equipment table"""
        cursor = self.conn.cursor()
        
        equipment_data = [
            # Knives
            ('Chef\'s Knife', 'Knives', '8-10 inch versatile kitchen knife', True,
             'Santoku knife, utility knife', 'Hand wash, hone regularly, professional sharpening yearly',
             '$50-$200'),
            ('Paring Knife', 'Knives', 'Small knife for detail work', True,
             'Small utility knife', 'Hand wash and dry immediately', '$15-$50'),
            ('Bread Knife', 'Knives', 'Serrated knife for bread', False,
             'Chef\'s knife (with sawing motion)', 'Needs less frequent sharpening', '$30-$80'),
            
            # Cookware
            ('Large Pot', 'Cookware', '6-8 quart pot for pasta, soups, stocks', True,
             'Dutch oven', 'Wash after each use, avoid abrasive scrubbers on non-stick',
             '$40-$150'),
            ('Skillet/Frying Pan', 'Cookware', '10-12 inch frying pan', True,
             'Sauté pan, wok', 'Season cast iron, avoid metal utensils on non-stick',
             '$30-$150'),
            ('Saucepan', 'Cookware', '2-3 quart pan for sauces', True,
             'Small pot', 'Clean promptly to avoid stuck-on food', '$25-$100'),
            ('Wok or Large Skillet', 'Cookware', 'For high-heat stir-frying', False,
             'Large frying pan, cast iron skillet', 'Season carbon steel woks regularly',
             '$30-$80'),
            ('Dutch Oven', 'Cookware', 'Heavy pot for braising and baking', False,
             'Large oven-safe pot with lid', 'Can go stovetop to oven, minimal maintenance',
             '$50-$300'),
            
            # Bakeware
            ('Baking Sheet', 'Bakeware', 'Flat pan for cookies and roasting', True,
             'Jelly roll pan, cooling rack', 'Line with parchment or silicone mat',
             '$15-$40'),
            ('Mixing Bowls', 'Bakeware', 'Set of various sized bowls', True,
             'Any heat-safe bowls', 'Stainless or glass best for versatility',
             '$20-$60'),
            ('Loaf Pan', 'Bakeware', 'For bread and meatloaf', False,
             'Free-form baking on sheet', 'Grease or line for easy release', '$10-$25'),
            ('Muffin Tin', 'Bakeware', '12-cup muffin/cupcake pan', False,
             'Ramekins or free-form', 'Use liners or grease wells', '$15-$35'),
            
            # Prep Tools
            ('Cutting Board', 'Prep Tools', 'Surface for cutting and prep', True,
             'Large plate in a pinch', 'Sanitize regularly, replace when heavily scored',
             '$15-$60'),
            ('Vegetable Peeler', 'Prep Tools', 'For peeling vegetables and fruits', True,
             'Paring knife', 'Replace when blade dulls', '$5-$15'),
            ('Colander/Strainer', 'Prep Tools', 'For draining pasta and washing produce', True,
             'Large slotted spoon, fine-mesh sieve', 'Ensure holes don\'t clog', '$10-$30'),
            ('Grater', 'Prep Tools', 'For cheese, vegetables, zesting', True,
             'Food processor, zester', 'Clean immediately after use', '$10-$30'),
            
            # Utensils
            ('Wooden Spoon', 'Utensils', 'For stirring and mixing', True,
             'Silicone spatula, metal spoon', 'Hand wash, oil occasionally',
             '$5-$20'),
            ('Spatula', 'Utensils', 'For flipping and serving', True,
             'Large spoon, turner', 'Heat-resistant silicone best for non-stick',
             '$8-$20'),
            ('Tongs', 'Utensils', 'For grabbing and flipping', True,
             'Two forks or spoons', 'Look for locking mechanism', '$10-$25'),
            ('Whisk', 'Utensils', 'For mixing and incorporating air', True,
             'Fork, two forks together', 'Clean thoroughly between wires', '$8-$20'),
            ('Ladle', 'Utensils', 'For serving soups and stews', False,
             'Large spoon, measuring cup', 'Look for hook for pot edge', '$8-$18'),
            
            # Measuring Tools
            ('Measuring Cups', 'Measuring Tools', 'Dry ingredient measuring', True,
             'Kitchen scale', 'Level off dry ingredients', '$10-$25'),
            ('Measuring Spoons', 'Measuring Tools', 'For small amounts', True,
             'Estimate with regular spoons', 'Level off for accuracy', '$8-$15'),
            ('Kitchen Scale', 'Measuring Tools', 'Digital scale for baking', False,
             'Measuring cups and conversion', 'Tare function useful, change batteries',
             '$15-$40'),
            
            # Appliances
            ('Electric Mixer (optional)', 'Appliances', 'Stand or hand mixer', False,
             'Whisk and elbow grease, food processor', 'Clean beaters after each use',
             '$30-$400'),
            ('Food Processor', 'Appliances', 'For chopping and mixing', False,
             'Knife and cutting board, blender', 'Clean immediately after use',
             '$50-$300'),
            ('Blender', 'Appliances', 'For smoothies and sauces', False,
             'Food processor, immersion blender', 'Clean base carefully',
             '$30-$500'),
        ]
        
        for equip in equipment_data:
            cursor.execute('''
                INSERT OR IGNORE INTO equipment (
                    name, category, description, essential, substitutes, care_tips, price_range
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', equip)
        
        self.conn.commit()
        print(f"Populated {len(equipment_data)} equipment items")
        
    def populate_recipes(self):
        """Populate recipes table with 60+ recipes"""
        cursor = self.conn.cursor()
        
        recipes_data = [
            # ============ ITALIAN RECIPES ============
            {
                'name': 'Classic Spaghetti Carbonara',
                'cuisine': 'Italian',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 10,
                'cook_time': 20,
                'total_time': 30,
                'servings': 4,
                'description': 'Traditional Roman pasta with eggs, cheese, and guanciale',
                'instructions': '''1. Bring large pot of salted water to boil.
2. Cook spaghetti until al dente (usually 8-10 minutes).
3. Meanwhile, cut guanciale or pancetta into small strips.
4. Cook guanciale in large skillet until crispy (5-7 minutes). Reserve fat.
5. In bowl, whisk eggs, grated Pecorino Romano, and black pepper.
6. When pasta is done, reserve 1 cup pasta water, then drain.
7. Add hot pasta to skillet with guanciale (off heat).
8. Quickly stir in egg mixture, adding pasta water gradually to create creamy sauce.
9. Toss continuously to avoid scrambling eggs.
10. Serve immediately with extra cheese and black pepper.''',
                'tips': 'The key is temperature - pasta should be hot but pan off heat when adding eggs. The residual heat cooks eggs into a creamy sauce, not scrambled eggs.',
                'nutritional_info': '{"calories": 520, "protein": "24g", "carbs": "58g", "fat": "22g"}',
                'dietary_tags': 'Contains gluten, eggs, dairy',
                'source': 'Traditional Roman recipe',
                'rating': 4.8,
                'ingredients': [
                    ('Spaghetti', '1', 'lb', ''),
                    ('Eggs', '4', 'large', 'room temperature'),
                    ('Cheese', '1', 'cup', 'Pecorino Romano, grated'),
                    ('Bacon', '6', 'oz', 'or pancetta, diced'),
                    ('Black Pepper', '2', 'tsp', 'freshly ground'),
                    ('Salt', 'to taste', '', ''),
                ],
                'equipment': ['Large Pot', 'Skillet/Frying Pan', 'Mixing Bowls', 'Whisk']
            },
            
            {
                'name': 'Margherita Pizza',
                'cuisine': 'Italian',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 90,
                'cook_time': 12,
                'total_time': 102,
                'servings': 4,
                'description': 'Classic Neapolitan pizza with tomato, mozzarella, and fresh basil',
                'instructions': '''1. Make dough: Mix flour, yeast, salt, water. Knead 10 minutes.
2. Let dough rise 1 hour until doubled.
3. Preheat oven to highest setting (500-550°F) with pizza stone if available.
4. Divide dough into 2-4 portions. Let rest 15 minutes.
5. Stretch dough by hand into thin rounds (don't use rolling pin).
6. Spread crushed tomatoes thinly over dough, leaving 1-inch border.
7. Add torn mozzarella pieces.
8. Drizzle with olive oil, season with salt.
9. Bake 8-12 minutes until crust is golden and cheese bubbles.
10. Top with fresh basil leaves immediately after removing from oven.''',
                'tips': 'Use a pizza stone or overturned baking sheet for crispier crust. High heat is essential for proper pizza.',
                'nutritional_info': '{"calories": 350, "protein": "14g", "carbs": "48g", "fat": "12g"}',
                'dietary_tags': 'Vegetarian, contains gluten and dairy',
                'source': 'Naples, Italy',
                'rating': 4.9,
                'ingredients': [
                    ('Flour', '3', 'cups', 'all-purpose or bread flour'),
                    ('Tomato', '1', 'can', '28 oz crushed tomatoes'),
                    ('Cheese', '8', 'oz', 'fresh mozzarella'),
                    ('Basil', '1', 'bunch', 'fresh'),
                    ('Olive Oil', '2', 'tbsp', ''),
                    ('Yeast', '1', 'packet', 'active dry'),
                    ('Sugar', '1', 'tsp', ''),
                    ('Salt', '2', 'tsp', ''),
                ],
                'equipment': ['Mixing Bowls', 'Baking Sheet', 'Rolling Pin (optional)']
            },
            
            {
                'name': 'Mushroom Risotto',
                'cuisine': 'Italian',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 30,
                'total_time': 45,
                'servings': 4,
                'description': 'Creamy Italian rice dish with mushrooms and parmesan',
                'instructions': '''1. Heat chicken or vegetable stock in saucepan, keep warm.
2. Sauté sliced mushrooms in butter until browned, set aside.
3. In large pan, sauté diced onion in butter and oil until soft.
4. Add arborio rice, stir 2 minutes until edges translucent.
5. Add white wine, stir until absorbed.
6. Add warm stock one ladle at a time, stirring constantly.
7. Wait until each addition is absorbed before adding more.
8. After 20-25 minutes, rice should be creamy and al dente.
9. Stir in mushrooms, parmesan, and butter.
10. Season with salt and pepper, serve immediately.''',
                'tips': 'Constant stirring releases starch for creaminess. Don\'t rush - proper risotto takes patience.',
                'nutritional_info': '{"calories": 420, "protein": "12g", "carbs": "58g", "fat": "16g"}',
                'dietary_tags': 'Vegetarian, contains dairy, gluten-free',
                'source': 'Northern Italy',
                'rating': 4.7,
                'ingredients': [
                    ('Rice', '1.5', 'cups', 'arborio or carnaroli'),
                    ('Mushrooms', '12', 'oz', 'mixed varieties'),
                    ('Onion', '1', 'small', 'finely diced'),
                    ('Butter', '4', 'tbsp', ''),
                    ('Cheese', '1', 'cup', 'parmesan, grated'),
                    ('White Wine', '1/2', 'cup', 'dry'),
                    ('Stock', '6', 'cups', 'chicken or vegetable, warm'),
                    ('Olive Oil', '2', 'tbsp', ''),
                ],
                'equipment': ['Large Pot', 'Saucepan', 'Wooden Spoon', 'Ladle']
            },

            {
                'name': 'Classic Lasagna',
                'cuisine': 'Italian',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 40,
                'cook_time': 60,
                'total_time': 100,
                'servings': 8,
                'description': 'Layered pasta with meat sauce, bechamel, and cheese',
                'instructions': '''1. Make meat sauce: Brown beef with onions and garlic, add tomatoes and herbs, simmer 30 minutes.
2. Make bechamel: Melt butter, whisk in flour, gradually add milk, cook until thick.
3. Cook lasagna noodles if not using no-boil variety.
4. Preheat oven to 375°F.
5. Spread thin layer of meat sauce in 9x13 baking dish.
6. Layer: noodles, meat sauce, bechamel, ricotta, mozzarella.
7. Repeat layers 3-4 times, ending with sauce and cheese.
8. Cover with foil, bake 40 minutes.
9. Remove foil, bake 20 more minutes until golden and bubbly.
10. Let rest 15 minutes before cutting.''',
                'tips': 'Make ahead and refrigerate overnight for easier slicing. Freezes beautifully.',
                'nutritional_info': '{"calories": 580, "protein": "32g", "carbs": "48g", "fat": "28g"}',
                'dietary_tags': 'Contains gluten, dairy, eggs',
                'source': 'Bologna, Italy',
                'rating': 4.9,
                'ingredients': [
                    ('Lasagna Noodles', '1', 'lb', ''),
                    ('Beef', '1.5', 'lbs', 'ground'),
                    ('Tomato', '2', 'cans', '28 oz crushed'),
                    ('Ricotta', '15', 'oz', ''),
                    ('Mozzarella', '1', 'lb', 'shredded'),
                    ('Parmesan', '1', 'cup', 'grated'),
                    ('Milk', '4', 'cups', ''),
                    ('Flour', '1/2', 'cup', ''),
                    ('Butter', '4', 'tbsp', ''),
                ],
                'equipment': ['Large Pot', 'Skillet/Frying Pan', 'Saucepan', 'Baking Sheet', 'Whisk']
            },

            {
                'name': 'Bruschetta',
                'cuisine': 'Italian',
                'category': 'Appetizer',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 5,
                'total_time': 20,
                'servings': 6,
                'description': 'Toasted bread topped with tomatoes, garlic, and basil',
                'instructions': '''1. Dice fresh tomatoes, removing seeds and excess juice.
2. Mix tomatoes with minced garlic, chopped basil, olive oil, salt, and pepper.
3. Let mixture sit 15-30 minutes for flavors to meld.
4. Slice Italian bread into 1/2-inch slices.
5. Brush with olive oil, toast under broiler or on grill until golden.
6. Rub toasted bread with cut garlic clove for extra flavor.
7. Top with tomato mixture just before serving.
8. Drizzle with balsamic vinegar if desired.
9. Serve immediately while bread is crispy.''',
                'tips': 'Don\'t top bread too early or it will get soggy. Best with peak summer tomatoes.',
                'nutritional_info': '{"calories": 180, "protein": "5g", "carbs": "24g", "fat": "7g"}',
                'dietary_tags': 'Vegan, contains gluten',
                'source': 'Central Italy',
                'rating': 4.6,
                'ingredients': [
                    ('Bread', '1', 'loaf', 'Italian or French'),
                    ('Tomato', '4', 'large', 'ripe'),
                    ('Garlic', '3', 'cloves', 'minced'),
                    ('Basil', '1/4', 'cup', 'fresh, chopped'),
                    ('Olive Oil', '1/4', 'cup', 'extra virgin'),
                    ('Balsamic Vinegar', '2', 'tbsp', 'optional'),
                ],
                'equipment': ['Cutting Board', 'Chef\'s Knife', 'Mixing Bowls', 'Baking Sheet']
            },

            {
                'name': 'Tiramisu',
                'cuisine': 'Italian',
                'category': 'Dessert',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 0,
                'total_time': 270,
                'servings': 12,
                'description': 'Classic Italian dessert with coffee-soaked ladyfingers and mascarpone',
                'instructions': '''1. Brew strong espresso and let cool. Add liqueur if desired.
2. Separate eggs. Beat yolks with sugar until pale and thick.
3. Fold in mascarpone cheese until smooth.
4. Beat egg whites to stiff peaks.
5. Gently fold egg whites into mascarpone mixture.
6. Quickly dip ladyfingers in coffee (don't soak).
7. Arrange layer of dipped ladyfingers in dish.
8. Spread half the mascarpone mixture over ladyfingers.
9. Repeat with another layer of ladyfingers and remaining cream.
10. Dust with cocoa powder, refrigerate at least 4 hours or overnight.''',
                'tips': 'Use room temperature eggs for better volume. The longer it chills, the better the flavors meld.',
                'nutritional_info': '{"calories": 340, "protein": "8g", "carbs": "32g", "fat": "20g"}',
                'dietary_tags': 'Contains gluten, dairy, eggs, alcohol (optional)',
                'source': 'Veneto, Italy',
                'rating': 4.8,
                'ingredients': [
                    ('Mascarpone', '16', 'oz', ''),
                    ('Eggs', '6', 'large', 'separated'),
                    ('Sugar', '3/4', 'cup', ''),
                    ('Espresso', '2', 'cups', 'strong, cooled'),
                    ('Ladyfingers', '24', '', ''),
                    ('Cocoa Powder', '3', 'tbsp', 'unsweetened'),
                    ('Marsala', '3', 'tbsp', 'or coffee liqueur, optional'),
                ],
                'equipment': ['Mixing Bowls', 'Electric Mixer (optional)', 'Whisk', 'Baking Sheet']
            },

            # ============ FRENCH RECIPES ============
            {
                'name': 'Coq au Vin',
                'cuisine': 'French',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 30,
                'cook_time': 90,
                'total_time': 120,
                'servings': 6,
                'description': 'Classic French chicken braised in red wine with mushrooms and bacon',
                'instructions': '''1. Cut chicken into pieces, season with salt and pepper.
2. Cook bacon until crispy, remove and set aside.
3. Brown chicken pieces in bacon fat until golden, remove.
4. Sauté pearl onions and mushrooms, remove.
5. Add flour to pan, cook 1 minute.
6. Add red wine, scraping up brown bits.
7. Add chicken stock, tomato paste, garlic, thyme, bay leaf.
8. Return chicken to pot, add bacon.
9. Cover and simmer 45 minutes until chicken tender.
10. Add mushrooms and onions, cook 15 more minutes.
11. Adjust seasoning, serve with crusty bread or potatoes.''',
                'tips': 'Use a good quality burgundy or pinot noir. Make a day ahead for even better flavor.',
                'nutritional_info': '{"calories": 520, "protein": "42g", "carbs": "12g", "fat": "28g"}',
                'dietary_tags': 'Gluten-free without flour thickener',
                'source': 'Burgundy, France',
                'rating': 4.8,
                'ingredients': [
                    ('Chicken', '4', 'lbs', 'cut into pieces'),
                    ('Bacon', '6', 'oz', 'chopped'),
                    ('Red Wine', '3', 'cups', 'burgundy or pinot noir'),
                    ('Mushrooms', '8', 'oz', 'quartered'),
                    ('Onion', '12', '', 'pearl onions'),
                    ('Garlic', '4', 'cloves', 'minced'),
                    ('Stock', '2', 'cups', 'chicken'),
                    ('Flour', '2', 'tbsp', ''),
                ],
                'equipment': ['Dutch Oven', 'Chef\'s Knife', 'Wooden Spoon']
            },

            {
                'name': 'Ratatouille',
                'cuisine': 'French',
                'category': 'Side Dish',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 45,
                'total_time': 75,
                'servings': 6,
                'description': 'Provençal vegetable stew with eggplant, zucchini, and tomatoes',
                'instructions': '''1. Slice eggplant, zucchini, yellow squash, and tomatoes into rounds.
2. Make sauce: Sauté onions and peppers, add crushed tomatoes, garlic, herbs.
3. Simmer sauce 10 minutes, season with salt and pepper.
4. Spread sauce in bottom of baking dish.
5. Arrange vegetable slices in alternating pattern in spiral or rows.
6. Drizzle with olive oil, season with salt, pepper, and herbs.
7. Cover with parchment, then foil.
8. Bake at 375°F for 40 minutes.
9. Uncover, bake 20 more minutes until vegetables are tender.
10. Serve hot or at room temperature.''',
                'tips': 'Use a mandoline for even slices. Can be made ahead and reheated.',
                'nutritional_info': '{"calories": 120, "protein": "3g", "carbs": "18g", "fat": "5g"}',
                'dietary_tags': 'Vegan, gluten-free',
                'source': 'Provence, France',
                'rating': 4.5,
                'ingredients': [
                    ('Eggplant', '1', 'medium', ''),
                    ('Zucchini', '2', 'medium', ''),
                    ('Tomato', '4', 'large', ''),
                    ('Bell Pepper', '2', '', 'mixed colors'),
                    ('Onion', '1', 'large', 'diced'),
                    ('Garlic', '4', 'cloves', 'minced'),
                    ('Olive Oil', '1/4', 'cup', ''),
                    ('Basil', '1/4', 'cup', 'fresh'),
                ],
                'equipment': ['Baking Sheet', 'Chef\'s Knife', 'Cutting Board', 'Saucepan']
            },

            {
                'name': 'Quiche Lorraine',
                'cuisine': 'French',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 45,
                'total_time': 65,
                'servings': 8,
                'description': 'Savory French tart with bacon, cheese, and custard',
                'instructions': '''1. Preheat oven to 375°F.
2. Roll out pie dough and fit into 9-inch tart pan.
3. Blind bake crust: line with parchment, fill with pie weights, bake 15 minutes.
4. Cook bacon until crispy, crumble.
5. Whisk eggs, cream, milk, salt, pepper, and nutmeg.
6. Sprinkle bacon and cheese in pre-baked crust.
7. Pour egg mixture over bacon and cheese.
8. Bake 30-35 minutes until set and golden.
9. Let cool 10 minutes before slicing.
10. Serve warm or at room temperature.''',
                'tips': 'Don\'t overbake - center should still jiggle slightly. Great for brunch or light dinner.',
                'nutritional_info': '{"calories": 380, "protein": "14g", "carbs": "18g", "fat": "28g"}',
                'dietary_tags': 'Contains gluten, dairy, eggs',
                'source': 'Lorraine, France',
                'rating': 4.7,
                'ingredients': [
                    ('Pie Crust', '1', '', '9-inch'),
                    ('Bacon', '8', 'slices', ''),
                    ('Eggs', '4', 'large', ''),
                    ('Heavy Cream', '1', 'cup', ''),
                    ('Milk', '1/2', 'cup', ''),
                    ('Cheese', '1', 'cup', 'Gruyere, grated'),
                    ('Nutmeg', '1/4', 'tsp', 'freshly grated'),
                ],
                'equipment': ['Tart Pan', 'Mixing Bowls', 'Whisk', 'Skillet/Frying Pan']
            },

            {
                'name': 'Beef Bourguignon',
                'cuisine': 'French',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 30,
                'cook_time': 150,
                'total_time': 180,
                'servings': 6,
                'description': 'French beef stew in red wine with vegetables',
                'instructions': '''1. Cut beef into 2-inch chunks, pat dry, season with salt and pepper.
2. Brown beef in batches in hot oil, don't crowd the pan.
3. Remove beef, cook bacon until crispy.
4. Sauté carrots, onions, and garlic in bacon fat.
5. Add tomato paste, cook 1 minute.
6. Add flour, stir 1 minute.
7. Add wine, stock, herbs, return beef and bacon.
8. Bring to simmer, cover, transfer to 325°F oven.
9. Braise 2.5 hours until beef very tender.
10. Sauté mushrooms and pearl onions separately.
11. Add to stew, adjust seasoning, serve with mashed potatoes or crusty bread.''',
                'tips': 'This dish is even better the next day. Use chuck roast for best results.',
                'nutritional_info': '{"calories": 580, "protein": "48g", "carbs": "16g", "fat": "32g"}',
                'dietary_tags': 'Gluten-free without flour',
                'source': 'Burgundy, France',
                'rating': 4.9,
                'ingredients': [
                    ('Beef', '3', 'lbs', 'chuck roast'),
                    ('Bacon', '6', 'oz', 'chopped'),
                    ('Red Wine', '3', 'cups', 'burgundy'),
                    ('Carrot', '3', 'large', 'chopped'),
                    ('Onion', '2', 'large', 'chopped'),
                    ('Mushrooms', '1', 'lb', 'quartered'),
                    ('Stock', '2', 'cups', 'beef'),
                    ('Tomato Paste', '2', 'tbsp', ''),
                ],
                'equipment': ['Dutch Oven', 'Chef\'s Knife', 'Wooden Spoon', 'Tongs']
            },

            {
                'name': 'French Onion Soup',
                'cuisine': 'French',
                'category': 'Soup',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 60,
                'total_time': 80,
                'servings': 4,
                'description': 'Rich soup with caramelized onions and melted cheese',
                'instructions': '''1. Thinly slice 4 large onions.
2. Melt butter in large pot, add onions and salt.
3. Cook onions over medium-low heat 40-50 minutes, stirring occasionally until deep brown.
4. Add garlic, cook 1 minute.
5. Add wine, scrape up brown bits, cook until nearly evaporated.
6. Add beef stock, thyme, bay leaf, simmer 20 minutes.
7. Season with salt and pepper.
8. Toast bread slices under broiler.
9. Ladle soup into oven-safe bowls.
10. Top with bread and grated Gruyere cheese.
11. Broil until cheese is bubbly and golden.''',
                'tips': 'Don\'t rush the onion caramelization - it\'s key to flavor. Low and slow is the secret.',
                'nutritional_info': '{"calories": 320, "protein": "14g", "carbs": "32g", "fat": "14g"}',
                'dietary_tags': 'Contains gluten, dairy',
                'source': 'Paris, France',
                'rating': 4.8,
                'ingredients': [
                    ('Onion', '4', 'large', 'yellow'),
                    ('Butter', '4', 'tbsp', ''),
                    ('Beef Stock', '6', 'cups', ''),
                    ('White Wine', '1/2', 'cup', 'dry'),
                    ('Bread', '8', 'slices', 'French baguette'),
                    ('Cheese', '2', 'cups', 'Gruyere, grated'),
                    ('Thyme', '4', 'sprigs', 'fresh'),
                ],
                'equipment': ['Large Pot', 'Oven-safe Bowls', 'Baking Sheet', 'Ladle']
            },

            {
                'name': 'Crème Brûlée',
                'cuisine': 'French',
                'category': 'Dessert',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 40,
                'total_time': 295,
                'servings': 6,
                'description': 'Classic French custard with caramelized sugar topping',
                'instructions': '''1. Preheat oven to 325°F.
2. Heat heavy cream with vanilla bean until steaming.
3. Whisk egg yolks with 1/3 cup sugar until pale.
4. Slowly pour hot cream into yolks, whisking constantly.
5. Strain mixture through fine sieve.
6. Pour into ramekins placed in baking dish.
7. Add hot water to dish to come halfway up ramekins.
8. Bake 35-40 minutes until set but still jiggly in center.
9. Chill at least 4 hours or overnight.
10. Before serving, sprinkle thin layer of sugar on top.
11. Caramelize with kitchen torch or under broiler.''',
                'tips': 'Don\'t overbake - custard should be set but not firm. Use superfine sugar for topping.',
                'nutritional_info': '{"calories": 380, "protein": "6g", "carbs": "28g", "fat": "28g"}',
                'dietary_tags': 'Gluten-free, contains dairy and eggs',
                'source': 'France',
                'rating': 4.9,
                'ingredients': [
                    ('Heavy Cream', '2', 'cups', ''),
                    ('Egg Yolks', '6', 'large', ''),
                    ('Sugar', '1/2', 'cup', 'plus extra for topping'),
                    ('Vanilla Bean', '1', '', 'or 2 tsp extract'),
                ],
                'equipment': ['Mixing Bowls', 'Whisk', 'Fine-mesh Sieve', 'Baking Sheet', 'Ramekins']
            },

            # ============ CHINESE RECIPES ============
            {
                'name': 'Kung Pao Chicken',
                'cuisine': 'Chinese',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 15,
                'total_time': 35,
                'servings': 4,
                'description': 'Spicy Sichuan stir-fry with chicken, peanuts, and vegetables',
                'instructions': '''1. Cut chicken into bite-sized pieces, marinate in soy sauce, rice wine, cornstarch.
2. Make sauce: mix soy sauce, rice vinegar, sugar, sesame oil, cornstarch.
3. Heat wok over high heat with oil.
4. Stir-fry dried chilies and Sichuan peppercorns 30 seconds.
5. Add chicken, stir-fry until just cooked, remove.
6. Add more oil, stir-fry garlic and ginger 30 seconds.
7. Add bell peppers and scallions, stir-fry 2 minutes.
8. Return chicken, add sauce, toss until thickened.
9. Stir in roasted peanuts.
10. Serve immediately over rice.''',
                'tips': 'Have all ingredients prepped before starting. Work quickly over high heat for best results.',
                'nutritional_info': '{"calories": 420, "protein": "32g", "carbs": "24g", "fat": "22g"}',
                'dietary_tags': 'Contains peanuts, soy, can be gluten-free with tamari',
                'source': 'Sichuan, China',
                'rating': 4.7,
                'ingredients': [
                    ('Chicken Breast', '1.5', 'lbs', 'diced'),
                    ('Peanuts', '1/2', 'cup', 'roasted'),
                    ('Bell Pepper', '2', '', 'cubed'),
                    ('Soy Sauce', '3', 'tbsp', ''),
                    ('Rice Vinegar', '2', 'tbsp', ''),
                    ('Sugar', '1', 'tbsp', ''),
                    ('Dried Chilies', '8-10', '', 'whole'),
                    ('Garlic', '4', 'cloves', 'minced'),
                ],
                'equipment': ['Wok or Large Skillet', 'Chef\'s Knife', 'Mixing Bowls']
            },

            {
                'name': 'Mapo Tofu',
                'cuisine': 'Chinese',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 20,
                'total_time': 35,
                'servings': 4,
                'description': 'Spicy Sichuan tofu dish with ground pork in chili bean sauce',
                'instructions': '''1. Cut tofu into 1/2-inch cubes, blanch in salted boiling water 2 minutes.
2. Heat wok with oil, stir-fry ground pork until browned.
3. Add doubanjiang (chili bean paste), garlic, ginger, stir-fry 1 minute.
4. Add stock, soy sauce, sugar, bring to simmer.
5. Gently add tofu, simmer 5 minutes.
6. Mix cornstarch with water, add to thicken sauce.
7. Add Sichuan peppercorn powder.
8. Garnish with sliced scallions.
9. Drizzle with chili oil if desired.
10. Serve over rice.''',
                'tips': 'Use silken tofu for traditional texture. Adjust spice level by varying amount of chili bean paste.',
                'nutritional_info': '{"calories": 320, "protein": "24g", "carbs": "12g", "fat": "20g"}',
                'dietary_tags': 'Contains soy, can be vegetarian without pork',
                'source': 'Sichuan, China',
                'rating': 4.6,
                'ingredients': [
                    ('Tofu', '14', 'oz', 'soft or silken'),
                    ('Ground Pork', '8', 'oz', ''),
                    ('Doubanjiang', '2', 'tbsp', 'chili bean paste'),
                    ('Garlic', '4', 'cloves', 'minced'),
                    ('Ginger', '1', 'tbsp', 'minced'),
                    ('Stock', '1', 'cup', 'chicken or vegetable'),
                    ('Soy Sauce', '2', 'tbsp', ''),
                    ('Green Onions', '4', '', 'sliced'),
                ],
                'equipment': ['Wok or Large Skillet', 'Large Pot', 'Cutting Board']
            },

            {
                'name': 'Sweet and Sour Pork',
                'cuisine': 'Chinese',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 25,
                'cook_time': 20,
                'total_time': 45,
                'servings': 4,
                'description': 'Crispy fried pork in tangy sweet and sour sauce with vegetables',
                'instructions': '''1. Cut pork into 1-inch cubes, marinate in soy sauce and rice wine.
2. Make batter with egg, cornstarch, and flour.
3. Heat oil for deep frying to 350°F.
4. Coat pork in batter, fry until golden and crispy, drain.
5. Make sauce: mix ketchup, sugar, vinegar, soy sauce, pineapple juice.
6. Stir-fry bell peppers, onions, and pineapple chunks.
7. Add sauce, bring to simmer.
8. Thicken with cornstarch slurry if needed.
9. Add crispy pork, toss to coat.
10. Serve immediately over rice.''',
                'tips': 'Fry pork in batches to maintain oil temperature. Add pork just before serving to keep crispy.',
                'nutritional_info': '{"calories": 480, "protein": "28g", "carbs": "52g", "fat": "18g"}',
                'dietary_tags': 'Contains gluten, eggs',
                'source': 'Cantonese cuisine',
                'rating': 4.5,
                'ingredients': [
                    ('Pork', '1.5', 'lbs', 'shoulder or loin'),
                    ('Bell Pepper', '2', '', 'mixed colors, chunked'),
                    ('Pineapple', '1', 'cup', 'chunks'),
                    ('Onion', '1', 'large', 'chunked'),
                    ('Ketchup', '1/2', 'cup', ''),
                    ('Sugar', '1/3', 'cup', ''),
                    ('Rice Vinegar', '1/4', 'cup', ''),
                    ('Cornstarch', '1/2', 'cup', 'for coating'),
                ],
                'equipment': ['Wok or Large Skillet', 'Large Pot', 'Mixing Bowls', 'Tongs']
            },

            {
                'name': 'Egg Fried Rice',
                'cuisine': 'Chinese',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 10,
                'total_time': 20,
                'servings': 4,
                'description': 'Classic Chinese fried rice with eggs and vegetables',
                'instructions': '''1. Use day-old cold rice (fresh rice gets mushy).
2. Beat eggs with pinch of salt.
3. Heat wok over high heat with oil.
4. Scramble eggs until just set, remove.
5. Add more oil, stir-fry diced vegetables (carrots, peas, corn) 2 minutes.
6. Add cold rice, break up clumps, stir-fry 3-4 minutes.
7. Push rice to sides, add soy sauce to center, then mix through.
8. Add scrambled eggs, green onions, sesame oil.
9. Toss everything together.
10. Serve hot as side dish or add protein for main course.''',
                'tips': 'Key to good fried rice: cold rice, hot wok, quick cooking. Day-old rice is best.',
                'nutritional_info': '{"calories": 320, "protein": "10g", "carbs": "48g", "fat": "10g"}',
                'dietary_tags': 'Contains eggs, soy, can be vegetarian',
                'source': 'Chinese home cooking',
                'rating': 4.4,
                'ingredients': [
                    ('Rice', '4', 'cups', 'cooked and chilled'),
                    ('Eggs', '3', 'large', ''),
                    ('Peas', '1', 'cup', 'frozen'),
                    ('Carrot', '1', 'large', 'diced'),
                    ('Green Onions', '4', '', 'sliced'),
                    ('Soy Sauce', '3', 'tbsp', ''),
                    ('Sesame Oil', '1', 'tsp', ''),
                ],
                'equipment': ['Wok or Large Skillet', 'Spatula', 'Mixing Bowls']
            },

            {
                'name': 'Hot and Sour Soup',
                'cuisine': 'Chinese',
                'category': 'Soup',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 15,
                'total_time': 35,
                'servings': 6,
                'description': 'Spicy and tangy Chinese soup with tofu and mushrooms',
                'instructions': '''1. Slice mushrooms, cut tofu into strips.
2. Bring stock to boil, add mushrooms, bamboo shoots.
3. Add soy sauce, vinegar, white pepper, sugar.
4. Simmer 5 minutes.
5. Add tofu, simmer 2 minutes.
6. Beat egg, slowly drizzle into simmering soup while stirring.
7. Mix cornstarch with water, add to thicken soup.
8. Add chili oil or sriracha for heat.
9. Garnish with green onions and cilantro.
10. Adjust seasoning with more vinegar or soy sauce as needed.''',
                'tips': 'The soup should be both spicy (from pepper) and sour (from vinegar). Adjust to taste.',
                'nutritional_info': '{"calories": 120, "protein": "8g", "carbs": "14g", "fat": "4g"}',
                'dietary_tags': 'Contains soy, eggs, can be gluten-free',
                'source': 'Sichuan, China',
                'rating': 4.5,
                'ingredients': [
                    ('Stock', '6', 'cups', 'chicken or vegetable'),
                    ('Tofu', '8', 'oz', 'firm, julienned'),
                    ('Mushrooms', '1', 'cup', 'shiitake, sliced'),
                    ('Bamboo Shoots', '1/2', 'cup', 'julienned'),
                    ('Rice Vinegar', '1/4', 'cup', ''),
                    ('Soy Sauce', '3', 'tbsp', ''),
                    ('Eggs', '2', 'large', 'beaten'),
                    ('White Pepper', '1', 'tsp', ''),
                ],
                'equipment': ['Large Pot', 'Whisk', 'Chef\'s Knife', 'Ladle']
            },

            # ============ JAPANESE RECIPES ============
            {
                'name': 'Chicken Teriyaki',
                'cuisine': 'Japanese',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 20,
                'total_time': 30,
                'servings': 4,
                'description': 'Grilled chicken with sweet and savory teriyaki glaze',
                'instructions': '''1. Make teriyaki sauce: combine soy sauce, mirin, sake, and sugar in saucepan.
2. Bring to boil, reduce heat, simmer 10 minutes until slightly thickened.
3. Cut chicken thighs into large pieces.
4. Heat oil in skillet over medium-high heat.
5. Cook chicken skin-side down 5-6 minutes until crispy.
6. Flip, cook another 5 minutes until cooked through.
7. Pour teriyaki sauce over chicken.
8. Simmer 2-3 minutes, turning to coat chicken.
9. Garnish with sesame seeds and sliced green onions.
10. Serve over rice with steamed vegetables.''',
                'tips': 'Don\'t skimp on the searing - crispy skin is key. Let sauce reduce for glossy finish.',
                'nutritional_info': '{"calories": 380, "protein": "32g", "carbs": "28g", "fat": "14g"}',
                'dietary_tags': 'Contains soy, can be gluten-free with tamari',
                'source': 'Japan',
                'rating': 4.8,
                'ingredients': [
                    ('Chicken Thighs', '2', 'lbs', 'boneless, skin-on'),
                    ('Soy Sauce', '1/2', 'cup', ''),
                    ('Mirin', '1/4', 'cup', ''),
                    ('Sake', '1/4', 'cup', 'or dry sherry'),
                    ('Sugar', '2', 'tbsp', ''),
                    ('Sesame Seeds', '1', 'tbsp', 'toasted'),
                    ('Green Onions', '2', '', 'sliced'),
                ],
                'equipment': ['Skillet/Frying Pan', 'Saucepan', 'Tongs']
            },

            {
                'name': 'Miso Soup',
                'cuisine': 'Japanese',
                'category': 'Soup',
                'difficulty': 'Easy',
                'prep_time': 5,
                'cook_time': 10,
                'total_time': 15,
                'servings': 4,
                'description': 'Traditional Japanese soup with tofu, seaweed, and miso paste',
                'instructions': '''1. Prepare dashi stock: steep kombu in water, remove before boiling.
2. Or use instant dashi powder according to package directions.
3. Cut tofu into small cubes.
4. Slice green onions thinly.
5. Bring dashi to gentle simmer.
6. Add tofu and wakame seaweed, simmer 2 minutes.
7. Turn off heat (important - boiling kills miso\'s beneficial properties).
8. Dissolve miso paste in small amount of hot stock.
9. Stir miso mixture into soup.
10. Add green onions, serve immediately.''',
                'tips': 'Never boil miso - add it at the end off heat. Use good quality miso for best flavor.',
                'nutritional_info': '{"calories": 60, "protein": "5g", "carbs": "6g", "fat": "2g"}',
                'dietary_tags': 'Vegetarian, vegan, contains soy',
                'source': 'Japan',
                'rating': 4.6,
                'ingredients': [
                    ('Dashi Stock', '4', 'cups', ''),
                    ('Miso Paste', '3', 'tbsp', 'white or red'),
                    ('Tofu', '8', 'oz', 'silken, cubed'),
                    ('Wakame', '2', 'tbsp', 'dried seaweed'),
                    ('Green Onions', '2', '', 'sliced'),
                ],
                'equipment': ['Large Pot', 'Ladle', 'Small Bowl']
            },

            {
                'name': 'Chicken Ramen',
                'cuisine': 'Japanese',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 30,
                'cook_time': 180,
                'total_time': 210,
                'servings': 4,
                'description': 'Rich Japanese noodle soup with chicken, eggs, and vegetables',
                'instructions': '''1. Make broth: Simmer chicken bones, ginger, garlic, scallions 3-4 hours.
2. Strain broth, season with soy sauce, mirin, sake.
3. Marinate chicken breasts in soy sauce mixture, bake at 375°F for 25 minutes.
4. Soft-boil eggs 6.5 minutes, peel and marinate in soy sauce.
5. Slice chicken, halve eggs.
6. Cook ramen noodles according to package.
7. Prepare toppings: slice green onions, blanch bean sprouts.
8. Assemble bowls: noodles, hot broth, sliced chicken, egg halves.
9. Add toppings: green onions, nori, bean sprouts, corn.
10. Drizzle with chili oil if desired.''',
                'tips': 'Making proper ramen broth takes time but is worth it. Can use store-bought broth for quicker version.',
                'nutritional_info': '{"calories": 520, "protein": "36g", "carbs": "62g", "fat": "14g"}',
                'dietary_tags': 'Contains gluten, eggs, soy',
                'source': 'Japan',
                'rating': 4.9,
                'ingredients': [
                    ('Ramen Noodles', '1', 'lb', 'fresh or dried'),
                    ('Chicken', '2', 'lbs', 'for broth and topping'),
                    ('Chicken Bones', '2', 'lbs', 'for broth'),
                    ('Eggs', '4', 'large', ''),
                    ('Soy Sauce', '1/2', 'cup', ''),
                    ('Mirin', '1/4', 'cup', ''),
                    ('Green Onions', '6', '', 'sliced'),
                    ('Nori', '4', 'sheets', 'seaweed'),
                ],
                'equipment': ['Large Pot', 'Saucepan', 'Baking Sheet', 'Ladle']
            },

            {
                'name': 'Gyoza (Japanese Dumplings)',
                'cuisine': 'Japanese',
                'category': 'Appetizer',
                'difficulty': 'Medium',
                'prep_time': 45,
                'cook_time': 15,
                'total_time': 60,
                'servings': 24,
                'description': 'Pan-fried dumplings with pork and cabbage filling',
                'instructions': '''1. Make filling: mix ground pork, finely chopped cabbage, garlic, ginger, soy sauce, sesame oil.
2. Salt cabbage, let sit 10 minutes, squeeze out excess water.
3. Place spoonful of filling in center of wrapper.
4. Wet edges of wrapper with water.
5. Fold in half, pleating one side to seal.
6. Heat oil in large skillet over medium-high.
7. Place gyoza flat side down in pan.
8. Cook 2-3 minutes until bottom is golden.
9. Add 1/4 cup water, cover immediately.
10. Steam 4-5 minutes until water evaporates.
11. Serve with dipping sauce (soy sauce, vinegar, chili oil).''',
                'tips': 'Don\'t overfill wrappers or they\'ll burst. The steam-fry method creates crispy bottom and tender top.',
                'nutritional_info': '{"calories": 45, "protein": "3g", "carbs": "5g", "fat": "1.5g"}',
                'dietary_tags': 'Contains gluten, soy, pork',
                'source': 'Japan',
                'rating': 4.7,
                'ingredients': [
                    ('Gyoza Wrappers', '24', '', ''),
                    ('Ground Pork', '1/2', 'lb', ''),
                    ('Cabbage', '2', 'cups', 'finely chopped'),
                    ('Garlic', '3', 'cloves', 'minced'),
                    ('Ginger', '1', 'tbsp', 'minced'),
                    ('Soy Sauce', '2', 'tbsp', ''),
                    ('Sesame Oil', '1', 'tbsp', ''),
                    ('Green Onions', '3', '', 'finely chopped'),
                ],
                'equipment': ['Skillet/Frying Pan', 'Mixing Bowls', 'Cutting Board']
            },

            {
                'name': 'Tempura',
                'cuisine': 'Japanese',
                'category': 'Appetizer',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 20,
                'total_time': 40,
                'servings': 4,
                'description': 'Light and crispy battered fried vegetables and shrimp',
                'instructions': '''1. Prepare vegetables: slice sweet potato, mushrooms, bell pepper, cut green beans.
2. Devein shrimp, keep tail on.
3. Make batter: Mix ice-cold water with egg, gently fold in flour (lumps OK).
4. Heat oil to 350-375°F for frying.
5. Dip vegetables and shrimp in batter, letting excess drip off.
6. Fry in small batches 2-3 minutes until light golden.
7. Don\'t overcrowd pan or oil temperature drops.
8. Drain on paper towels.
9. Serve immediately with tentsuyu dipping sauce.
10. Garnish with grated daikon and ginger.''',
                'tips': 'Key to light tempura: cold batter, hot oil, don\'t overmix batter. Serve immediately.',
                'nutritional_info': '{"calories": 280, "protein": "14g", "carbs": "32g", "fat": "10g"}',
                'dietary_tags': 'Contains gluten, eggs, shellfish',
                'source': 'Japan',
                'rating': 4.6,
                'ingredients': [
                    ('Shrimp', '1', 'lb', 'large, peeled'),
                    ('Sweet Potato', '1', 'medium', 'sliced'),
                    ('Mushrooms', '8', 'oz', 'shiitake or button'),
                    ('Green Beans', '1/2', 'lb', ''),
                    ('Flour', '1', 'cup', 'all-purpose, chilled'),
                    ('Eggs', '1', 'large', ''),
                    ('Ice Water', '1', 'cup', ''),
                ],
                'equipment': ['Large Pot', 'Mixing Bowls', 'Tongs', 'Thermometer']
            },

            # ============ INDIAN RECIPES ============
            {
                'name': 'Butter Chicken',
                'cuisine': 'Indian',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 40,
                'total_time': 70,
                'servings': 6,
                'description': 'Creamy tomato-based curry with tender chicken',
                'instructions': '''1. Marinate chicken in yogurt, lemon juice, garam masala, turmeric 30 minutes.
2. Grill or pan-fry chicken until charred, set aside.
3. In large pot, melt butter, sauté onions until golden.
4. Add ginger, garlic, cook 2 minutes.
5. Add tomato puree, cook 10 minutes.
6. Add garam masala, cumin, coriander, cayenne, simmer 5 minutes.
7. Blend sauce until smooth (optional for smoother texture).
8. Add cream and kasuri methi (dried fenugreek).
9. Add chicken, simmer 15 minutes.
10. Finish with butter, serve with naan or rice.''',
                'tips': 'Marinating chicken is key to flavor. Kasuri methi adds authentic flavor but can be omitted.',
                'nutritional_info': '{"calories": 480, "protein": "34g", "carbs": "16g", "fat": "32g"}',
                'dietary_tags': 'Contains dairy, can be gluten-free',
                'source': 'North India',
                'rating': 4.9,
                'ingredients': [
                    ('Chicken', '2', 'lbs', 'boneless, cubed'),
                    ('Yogurt', '1', 'cup', 'plain'),
                    ('Butter', '6', 'tbsp', ''),
                    ('Heavy Cream', '1', 'cup', ''),
                    ('Tomato Paste', '3', 'tbsp', 'or puree'),
                    ('Garam Masala', '2', 'tbsp', ''),
                    ('Ginger', '2', 'tbsp', 'minced'),
                    ('Garlic', '6', 'cloves', 'minced'),
                ],
                'equipment': ['Large Pot', 'Skillet/Frying Pan', 'Blender (optional)', 'Mixing Bowls']
            },

            {
                'name': 'Chicken Tikka Masala',
                'cuisine': 'Indian',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 45,
                'cook_time': 30,
                'total_time': 75,
                'servings': 6,
                'description': 'Spiced chicken in creamy tomato sauce',
                'instructions': '''1. Marinate chicken in yogurt, lemon, tikka masala spices 30 minutes minimum.
2. Thread chicken on skewers, grill or broil until charred.
3. Sauté onions in oil until soft.
4. Add garlic, ginger, cook 2 minutes.
5. Add tomato sauce, tikka masala spices, paprika.
6. Simmer 15 minutes.
7. Add cream and sugar.
8. Add cooked chicken, simmer 10 minutes.
9. Finish with butter, garnish with cilantro.
10. Serve with basmati rice and naan.''',
                'tips': 'Char on chicken adds smoky flavor. Can use boneless thighs for more tender meat.',
                'nutritional_info': '{"calories": 420, "protein": "36g", "carbs": "18g", "fat": "24g"}',
                'dietary_tags': 'Contains dairy, can be gluten-free',
                'source': 'British-Indian cuisine',
                'rating': 4.8,
                'ingredients': [
                    ('Chicken Breast', '2', 'lbs', 'cubed'),
                    ('Yogurt', '1', 'cup', 'plain'),
                    ('Tomato Sauce', '2', 'cups', ''),
                    ('Heavy Cream', '1', 'cup', ''),
                    ('Tikka Masala Spice', '3', 'tbsp', ''),
                    ('Ginger', '2', 'tbsp', 'minced'),
                    ('Garlic', '6', 'cloves', 'minced'),
                    ('Cilantro', '1/4', 'cup', 'chopped'),
                ],
                'equipment': ['Skillet/Frying Pan', 'Baking Sheet', 'Mixing Bowls', 'Tongs']
            },

            {
                'name': 'Dal Tadka',
                'cuisine': 'Indian',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 40,
                'total_time': 50,
                'servings': 6,
                'description': 'Spiced yellow lentil curry',
                'instructions': '''1. Rinse lentils thoroughly.
2. Cook lentils with water, turmeric, salt until soft (25-30 minutes).
3. Mash lentils slightly with back of spoon.
4. In separate pan, heat ghee or oil.
5. Add cumin seeds, let sizzle.
6. Add onions, cook until golden.
7. Add ginger, garlic, green chilies, tomatoes.
8. Cook until tomatoes break down.
9. Add spices: coriander, cumin, garam masala.
10. Pour tempering over cooked lentils, simmer 5 minutes.
11. Garnish with cilantro, serve with rice or roti.''',
                'tips': 'Tadka (tempering) is added at the end for maximum flavor. Adjust consistency with water.',
                'nutritional_info': '{"calories": 220, "protein": "12g", "carbs": "32g", "fat": "6g"}',
                'dietary_tags': 'Vegetarian, vegan (with oil), gluten-free',
                'source': 'North India',
                'rating': 4.6,
                'ingredients': [
                    ('Yellow Lentils', '1.5', 'cups', 'toor or moong dal'),
                    ('Tomato', '2', 'medium', 'chopped'),
                    ('Onion', '1', 'large', 'diced'),
                    ('Ginger', '1', 'tbsp', 'minced'),
                    ('Garlic', '4', 'cloves', 'minced'),
                    ('Cumin Seeds', '1', 'tsp', ''),
                    ('Turmeric', '1/2', 'tsp', ''),
                    ('Cilantro', '1/4', 'cup', 'chopped'),
                ],
                'equipment': ['Large Pot', 'Skillet/Frying Pan', 'Wooden Spoon']
            },

            {
                'name': 'Chicken Biryani',
                'cuisine': 'Indian',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 40,
                'cook_time': 60,
                'total_time': 100,
                'servings': 6,
                'description': 'Fragrant rice dish layered with spiced chicken',
                'instructions': '''1. Marinate chicken in yogurt, spices, ginger-garlic paste 30 minutes.
2. Soak basmati rice 30 minutes, drain.
3. Parboil rice with whole spices until 70% done.
4. Fry onions until crispy brown, reserve half.
5. Cook marinated chicken with onions until nearly done.
6. Layer rice and chicken in pot.
7. Top with fried onions, saffron milk, mint, cilantro.
8. Cover tightly, cook on low heat (dum) 30 minutes.
9. Alternatively, bake at 350°F for 30 minutes.
10. Let rest 5 minutes, mix gently before serving.''',
                'tips': 'Key is layering and dum (slow cooking). Don\'t skip saffron - it adds authentic flavor and color.',
                'nutritional_info': '{"calories": 520, "protein": "32g", "carbs": "62g", "fat": "16g"}',
                'dietary_tags': 'Contains dairy, can be gluten-free',
                'source': 'Hyderabad, India',
                'rating': 4.9,
                'ingredients': [
                    ('Chicken', '2', 'lbs', 'bone-in pieces'),
                    ('Basmati Rice', '2', 'cups', ''),
                    ('Yogurt', '1', 'cup', 'plain'),
                    ('Onion', '3', 'large', 'sliced'),
                    ('Ginger-Garlic Paste', '3', 'tbsp', ''),
                    ('Biryani Masala', '2', 'tbsp', ''),
                    ('Saffron', '1/4', 'tsp', 'soaked in milk'),
                    ('Mint', '1/2', 'cup', 'fresh'),
                ],
                'equipment': ['Large Pot', 'Dutch Oven', 'Skillet/Frying Pan', 'Mixing Bowls']
            },

            {
                'name': 'Samosas',
                'cuisine': 'Indian',
                'category': 'Appetizer',
                'difficulty': 'Hard',
                'prep_time': 45,
                'cook_time': 30,
                'total_time': 75,
                'servings': 12,
                'description': 'Crispy pastry filled with spiced potatoes and peas',
                'instructions': '''1. Make dough: Mix flour, salt, oil, gradually add water, knead until smooth.
2. Cover, let rest 30 minutes.
3. Make filling: Boil, peel, and mash potatoes.
4. Sauté cumin seeds, add ginger, green chilies.
5. Add peas, spices (garam masala, coriander, cumin), cook 5 minutes.
6. Mix in mashed potatoes, let cool.
7. Divide dough, roll into circles, cut in half.
8. Form cone shape, fill with potato mixture, seal edges.
9. Deep fry at 350°F until golden brown.
10. Serve hot with tamarind or mint chutney.''',
                'tips': 'Seal edges well to prevent bursting. Can bake at 400°F for healthier version.',
                'nutritional_info': '{"calories": 180, "protein": "4g", "carbs": "24g", "fat": "8g"}',
                'dietary_tags': 'Vegetarian, vegan, contains gluten',
                'source': 'North India',
                'rating': 4.7,
                'ingredients': [
                    ('Flour', '2', 'cups', 'all-purpose'),
                    ('Potatoes', '4', 'large', ''),
                    ('Peas', '1', 'cup', 'frozen'),
                    ('Cumin Seeds', '1', 'tsp', ''),
                    ('Garam Masala', '1', 'tsp', ''),
                    ('Ginger', '1', 'tbsp', 'minced'),
                    ('Green Chilies', '2', '', 'chopped'),
                ],
                'equipment': ['Large Pot', 'Mixing Bowls', 'Rolling Pin', 'Skillet/Frying Pan']
            },

            # ============ MEXICAN RECIPES ============
            {
                'name': 'Chicken Tacos',
                'cuisine': 'Mexican',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 20,
                'total_time': 35,
                'servings': 4,
                'description': 'Classic Mexican street tacos with seasoned chicken',
                'instructions': '''1. Season chicken with chili powder, cumin, garlic powder, salt, paprika.
2. Heat oil in skillet, cook chicken 6-7 minutes per side.
3. Let chicken rest, then dice into small pieces.
4. Warm tortillas in dry skillet or over gas flame.
5. Prepare toppings: dice tomatoes, onion, cilantro; slice avocado.
6. Assemble tacos: tortilla, chicken, toppings.
7. Add salsa, lime juice, and hot sauce to taste.
8. Serve immediately with lime wedges.''',
                'tips': 'Warming tortillas makes them pliable and brings out flavor. Double-stack for sturdier tacos.',
                'nutritional_info': '{"calories": 380, "protein": "32g", "carbs": "35g", "fat": "12g"}',
                'dietary_tags': 'Gluten-free with corn tortillas',
                'source': 'Mexican street food',
                'rating': 4.8,
                'ingredients': [
                    ('Chicken Breast', '1.5', 'lbs', ''),
                    ('Corn Tortillas', '12', '', ''),
                    ('Tomato', '2', '', 'diced'),
                    ('Onion', '1', '', 'diced'),
                    ('Cilantro', '1/2', 'cup', 'chopped'),
                    ('Avocado', '2', '', 'sliced'),
                    ('Lime', '2', '', 'cut into wedges'),
                    ('Chili Powder', '2', 'tsp', ''),
                    ('Cumin', '1', 'tsp', ''),
                ],
                'equipment': ['Skillet/Frying Pan', 'Chef\'s Knife', 'Cutting Board']
            },

            {
                'name': 'Beef Enchiladas',
                'cuisine': 'Mexican',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 25,
                'cook_time': 30,
                'total_time': 55,
                'servings': 6,
                'description': 'Rolled tortillas filled with beef and topped with cheese and sauce',
                'instructions': '''1. Brown ground beef with onions and garlic.
2. Add taco seasoning, tomatoes, beans, simmer 10 minutes.
3. Make enchilada sauce or use store-bought.
4. Warm tortillas briefly to make pliable.
5. Spread thin layer of sauce in baking dish.
6. Fill each tortilla with beef mixture and cheese.
7. Roll tightly, place seam-side down in dish.
8. Pour remaining sauce over enchiladas.
9. Top with shredded cheese.
10. Bake at 350°F for 20-25 minutes until bubbly.
11. Garnish with cilantro, serve with sour cream.''',
                'tips': 'Warming tortillas prevents tearing. Can make ahead and refrigerate before baking.',
                'nutritional_info': '{"calories": 480, "protein": "28g", "carbs": "42g", "fat": "22g"}',
                'dietary_tags': 'Contains gluten, dairy',
                'source': 'Mexico',
                'rating': 4.7,
                'ingredients': [
                    ('Ground Beef', '1.5', 'lbs', ''),
                    ('Flour Tortillas', '12', '', 'medium'),
                    ('Enchilada Sauce', '2', 'cans', '15 oz each'),
                    ('Cheese', '2', 'cups', 'cheddar, shredded'),
                    ('Black Beans', '1', 'can', '15 oz'),
                    ('Onion', '1', 'medium', 'diced'),
                    ('Garlic', '3', 'cloves', 'minced'),
                ],
                'equipment': ['Skillet/Frying Pan', 'Baking Sheet', 'Cutting Board']
            },

            {
                'name': 'Guacamole',
                'cuisine': 'Mexican',
                'category': 'Appetizer',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 0,
                'total_time': 10,
                'servings': 6,
                'description': 'Fresh avocado dip with lime, cilantro, and jalapeño',
                'instructions': '''1. Cut avocados in half, remove pit.
2. Scoop flesh into bowl.
3. Mash with fork to desired consistency (chunky or smooth).
4. Add lime juice immediately to prevent browning.
5. Stir in diced tomatoes, onions, jalapeño, and cilantro.
6. Season with salt and cumin.
7. Taste and adjust seasonings.
8. Serve immediately with tortilla chips.
9. Press plastic wrap directly on surface if storing.''',
                'tips': 'Use ripe avocados that yield to gentle pressure. Lime juice prevents browning.',
                'nutritional_info': '{"calories": 140, "protein": "2g", "carbs": "8g", "fat": "12g"}',
                'dietary_tags': 'Vegan, gluten-free',
                'source': 'Mexico',
                'rating': 4.8,
                'ingredients': [
                    ('Avocados', '4', 'large', 'ripe'),
                    ('Lime', '2', '', 'juiced'),
                    ('Tomato', '1', 'medium', 'diced'),
                    ('Onion', '1/4', 'cup', 'finely diced'),
                    ('Jalapeño', '1', '', 'minced'),
                    ('Cilantro', '3', 'tbsp', 'chopped'),
                    ('Cumin', '1/4', 'tsp', ''),
                ],
                'equipment': ['Mixing Bowls', 'Fork', 'Chef\'s Knife']
            },

            {
                'name': 'Chicken Quesadillas',
                'cuisine': 'Mexican',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 15,
                'total_time': 30,
                'servings': 4,
                'description': 'Grilled tortillas filled with chicken and melted cheese',
                'instructions': '''1. Cook and shred chicken, season with taco spices.
2. Heat large skillet over medium heat.
3. Place tortilla in skillet.
4. Sprinkle half with shredded cheese.
5. Add chicken, peppers, onions over cheese.
6. Add more cheese on top.
7. Fold tortilla in half.
8. Cook 2-3 minutes until bottom is golden.
9. Flip, cook other side until crispy and cheese melts.
10. Cut into wedges, serve with sour cream and salsa.''',
                'tips': 'Don\'t overfill or quesadilla won\'t seal. Use two spatulas for easier flipping.',
                'nutritional_info': '{"calories": 420, "protein": "28g", "carbs": "36g", "fat": "18g"}',
                'dietary_tags': 'Contains gluten, dairy',
                'source': 'Mexico',
                'rating': 4.6,
                'ingredients': [
                    ('Flour Tortillas', '4', 'large', ''),
                    ('Chicken Breast', '1', 'lb', 'cooked and shredded'),
                    ('Cheese', '2', 'cups', 'Mexican blend, shredded'),
                    ('Bell Pepper', '1', '', 'diced'),
                    ('Onion', '1/2', 'medium', 'diced'),
                    ('Taco Seasoning', '2', 'tbsp', ''),
                ],
                'equipment': ['Skillet/Frying Pan', 'Spatula', 'Chef\'s Knife']
            },

            {
                'name': 'Churros',
                'cuisine': 'Mexican',
                'category': 'Dessert',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 20,
                'total_time': 35,
                'servings': 12,
                'description': 'Fried dough pastries coated in cinnamon sugar',
                'instructions': '''1. Bring water, butter, salt, and brown sugar to boil.
2. Remove from heat, stir in flour until dough forms.
3. Beat in eggs one at a time until smooth.
4. Transfer dough to piping bag with star tip.
5. Heat oil to 375°F for frying.
6. Pipe 4-6 inch strips into hot oil.
7. Fry 2-3 minutes per side until golden brown.
8. Drain on paper towels.
9. Roll in cinnamon-sugar mixture while still warm.
10. Serve with chocolate or dulce de leche sauce for dipping.''',
                'tips': 'Use star tip for traditional ridged churros. Fry at correct temperature for crispy exterior.',
                'nutritional_info': '{"calories": 180, "protein": "3g", "carbs": "22g", "fat": "9g"}',
                'dietary_tags': 'Contains gluten, eggs, dairy',
                'source': 'Mexico and Spain',
                'rating': 4.8,
                'ingredients': [
                    ('Water', '1', 'cup', ''),
                    ('Butter', '1/2', 'cup', ''),
                    ('Flour', '1', 'cup', 'all-purpose'),
                    ('Eggs', '3', 'large', ''),
                    ('Sugar', '1/2', 'cup', 'for coating'),
                    ('Cinnamon', '1', 'tbsp', ''),
                    ('Brown Sugar', '2', 'tbsp', ''),
                ],
                'equipment': ['Large Pot', 'Mixing Bowls', 'Piping Bag', 'Tongs']
            },

            # ============ THAI RECIPES ============
            {
                'name': 'Pad Thai',
                'cuisine': 'Thai',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 15,
                'total_time': 35,
                'servings': 4,
                'description': 'Iconic Thai stir-fried rice noodles with sweet, sour, and savory flavors',
                'instructions': '''1. Soak rice noodles in warm water 20-30 minutes until pliable, drain.
2. Make sauce: mix tamarind paste, fish sauce, sugar, and water.
3. Heat wok over high heat with oil.
4. Scramble eggs, remove and set aside.
5. Add more oil, cook shrimp or chicken until done, remove.
6. Add garlic, cook 30 seconds.
7. Add noodles and sauce, toss 2 minutes.
8. Add bean sprouts, green onions, protein, and eggs.
9. Toss everything together.
10. Serve with peanuts, lime wedges, and chili flakes.''',
                'tips': 'Work quickly over high heat. Have all ingredients prepped before starting.',
                'nutritional_info': '{"calories": 450, "protein": "24g", "carbs": "62g", "fat": "14g"}',
                'dietary_tags': 'Can be made gluten-free',
                'source': 'Thai street food',
                'rating': 4.7,
                'ingredients': [
                    ('Rice Noodles', '8', 'oz', 'pad thai width'),
                    ('Shrimp', '12', 'oz', 'peeled and deveined'),
                    ('Eggs', '2', '', ''),
                    ('Bean Sprouts', '2', 'cups', ''),
                    ('Green Onions', '4', '', 'cut into 1-inch pieces'),
                    ('Peanuts', '1/4', 'cup', 'crushed'),
                    ('Fish Sauce', '3', 'tbsp', ''),
                    ('Tamarind Paste', '2', 'tbsp', ''),
                    ('Sugar', '2', 'tbsp', ''),
                    ('Lime', '1', '', 'cut into wedges'),
                ],
                'equipment': ['Wok or Large Skillet', 'Chef\'s Knife', 'Cutting Board', 'Mixing Bowls']
            },

            {
                'name': 'Green Curry',
                'cuisine': 'Thai',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 25,
                'total_time': 40,
                'servings': 4,
                'description': 'Spicy coconut curry with vegetables and chicken',
                'instructions': '''1. Heat oil in wok or large pot.
2. Add green curry paste, cook 1-2 minutes until fragrant.
3. Add coconut milk, bring to simmer.
4. Add chicken, cook 10 minutes.
5. Add vegetables: bell peppers, bamboo shoots, eggplant.
6. Add fish sauce, sugar, lime leaves.
7. Simmer 10 minutes until vegetables tender.
8. Stir in basil leaves.
9. Adjust seasoning with more fish sauce or sugar.
10. Serve over jasmine rice.''',
                'tips': 'Quality curry paste is key. Adjust spice level by varying amount of paste.',
                'nutritional_info': '{"calories": 420, "protein": "28g", "carbs": "18g", "fat": "28g"}',
                'dietary_tags': 'Can be gluten-free, contains fish sauce',
                'source': 'Thailand',
                'rating': 4.7,
                'ingredients': [
                    ('Green Curry Paste', '3', 'tbsp', ''),
                    ('Coconut Milk', '2', 'cans', '13.5 oz each'),
                    ('Chicken Breast', '1', 'lb', 'sliced'),
                    ('Bell Pepper', '1', '', 'sliced'),
                    ('Bamboo Shoots', '1', 'cup', 'sliced'),
                    ('Thai Basil', '1/2', 'cup', 'fresh'),
                    ('Fish Sauce', '2', 'tbsp', ''),
                    ('Sugar', '1', 'tbsp', ''),
                ],
                'equipment': ['Wok or Large Skillet', 'Chef\'s Knife', 'Wooden Spoon']
            },

            {
                'name': 'Tom Yum Soup',
                'cuisine': 'Thai',
                'category': 'Soup',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 20,
                'total_time': 35,
                'servings': 4,
                'description': 'Spicy and sour Thai soup with shrimp, lemongrass, and lime',
                'instructions': '''1. Bring stock to boil with lemongrass, galangal, lime leaves.
2. Simmer 10 minutes to infuse flavors.
3. Add mushrooms, tomatoes, simmer 5 minutes.
4. Add shrimp, cook 3-4 minutes until pink.
5. Remove from heat.
6. Stir in fish sauce, lime juice, chili paste.
7. Adjust seasoning - should be spicy, sour, and salty.
8. Garnish with cilantro and sliced chilies.
9. Serve hot.''',
                'tips': 'Don\'t boil after adding lime juice or it becomes bitter. Remove aromatics or warn diners.',
                'nutritional_info': '{"calories": 140, "protein": "18g", "carbs": "8g", "fat": "4g"}',
                'dietary_tags': 'Gluten-free, contains shellfish',
                'source': 'Thailand',
                'rating': 4.6,
                'ingredients': [
                    ('Stock', '4', 'cups', 'chicken or vegetable'),
                    ('Shrimp', '1', 'lb', 'peeled and deveined'),
                    ('Lemongrass', '2', 'stalks', 'bruised'),
                    ('Galangal', '4', 'slices', 'fresh'),
                    ('Lime Leaves', '4', '', 'kaffir'),
                    ('Mushrooms', '1', 'cup', 'sliced'),
                    ('Fish Sauce', '3', 'tbsp', ''),
                    ('Lime Juice', '3', 'tbsp', 'fresh'),
                ],
                'equipment': ['Large Pot', 'Ladle', 'Chef\'s Knife']
            },

            {
                'name': 'Mango Sticky Rice',
                'cuisine': 'Thai',
                'category': 'Dessert',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 30,
                'total_time': 45,
                'servings': 4,
                'description': 'Sweet coconut sticky rice served with fresh mango',
                'instructions': '''1. Soak sticky rice in water at least 3 hours or overnight.
2. Drain and steam rice in steamer basket 20-25 minutes until tender.
3. Heat coconut milk with sugar and salt, don\'t boil.
4. Pour half the coconut milk over hot rice, stir gently.
5. Cover and let rice absorb coconut milk 20 minutes.
6. Slice mango into thin pieces.
7. Serve rice with mango slices.
8. Drizzle remaining coconut sauce over top.
9. Garnish with sesame seeds or mung beans if desired.''',
                'tips': 'Use ripe, sweet mangos. Rice should be sticky but not mushy.',
                'nutritional_info': '{"calories": 380, "protein": "4g", "carbs": "68g", "fat": "12g"}',
                'dietary_tags': 'Vegan, gluten-free',
                'source': 'Thailand',
                'rating': 4.8,
                'ingredients': [
                    ('Sticky Rice', '1.5', 'cups', 'glutinous rice'),
                    ('Coconut Milk', '1', 'can', '13.5 oz'),
                    ('Sugar', '1/2', 'cup', ''),
                    ('Mangoes', '2', 'large', 'ripe'),
                    ('Salt', '1/2', 'tsp', ''),
                    ('Sesame Seeds', '1', 'tbsp', 'toasted, optional'),
                ],
                'equipment': ['Steamer', 'Saucepan', 'Mixing Bowls']
            },

            # ============ GREEK RECIPES ============
            {
                'name': 'Moussaka',
                'cuisine': 'Greek',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 45,
                'cook_time': 60,
                'total_time': 105,
                'servings': 8,
                'description': 'Layered eggplant casserole with meat sauce and béchamel',
                'instructions': '''1. Slice eggplants, salt and let drain 30 minutes.
2. Pat dry, brush with oil, roast at 400°F until tender.
3. Make meat sauce: brown lamb or beef with onions, add tomatoes, wine, spices, simmer 30 minutes.
4. Make béchamel: melt butter, whisk in flour, gradually add milk, cook until thick.
5. Beat eggs into béchamel.
6. Layer in baking dish: eggplant, meat sauce, repeat.
7. Top with béchamel sauce.
8. Sprinkle with parmesan or kefalotyri cheese.
9. Bake at 350°F for 45 minutes until golden.
10. Let rest 20 minutes before cutting.''',
                'tips': 'Resting time is crucial - moussaka needs to set. Can be made ahead and reheated.',
                'nutritional_info': '{"calories": 480, "protein": "28g", "carbs": "32g", "fat": "26g"}',
                'dietary_tags': 'Contains gluten, dairy, eggs',
                'source': 'Greece',
                'rating': 4.8,
                'ingredients': [
                    ('Eggplant', '3', 'large', 'sliced'),
                    ('Ground Lamb', '1.5', 'lbs', 'or beef'),
                    ('Tomatoes', '2', 'cans', '14 oz crushed'),
                    ('Onion', '2', 'large', 'diced'),
                    ('Milk', '4', 'cups', ''),
                    ('Butter', '1/2', 'cup', ''),
                    ('Flour', '1/2', 'cup', ''),
                    ('Eggs', '2', 'large', ''),
                ],
                'equipment': ['Baking Sheet', 'Large Pot', 'Saucepan', 'Whisk']
            },

            {
                'name': 'Greek Salad',
                'cuisine': 'Greek',
                'category': 'Salad',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 0,
                'total_time': 15,
                'servings': 6,
                'description': 'Classic Mediterranean salad with feta, olives, and vegetables',
                'instructions': '''1. Cut tomatoes into wedges.
2. Dice cucumbers (peel if desired).
3. Slice red onion thinly.
4. Cut bell pepper into strips.
5. Combine vegetables in large bowl.
6. Add olives and feta cheese chunks.
7. Make dressing: whisk olive oil, lemon juice, oregano, salt, pepper.
8. Pour dressing over salad.
9. Toss gently to combine.
10. Serve immediately or chill up to 2 hours.''',
                'tips': 'Don\'t cut vegetables too small - chunky is traditional. Use quality feta and olive oil.',
                'nutritional_info': '{"calories": 220, "protein": "6g", "carbs": "12g", "fat": "16g"}',
                'dietary_tags': 'Vegetarian, gluten-free, contains dairy',
                'source': 'Greece',
                'rating': 4.7,
                'ingredients': [
                    ('Tomatoes', '4', 'large', ''),
                    ('Cucumber', '2', 'medium', ''),
                    ('Red Onion', '1', 'medium', ''),
                    ('Bell Pepper', '1', 'green', ''),
                    ('Feta Cheese', '8', 'oz', 'block'),
                    ('Kalamata Olives', '1', 'cup', ''),
                    ('Olive Oil', '1/2', 'cup', 'extra virgin'),
                    ('Lemon Juice', '3', 'tbsp', 'fresh'),
                    ('Oregano', '2', 'tsp', 'dried'),
                ],
                'equipment': ['Mixing Bowls', 'Chef\'s Knife', 'Cutting Board', 'Whisk']
            },

            {
                'name': 'Spanakopita',
                'cuisine': 'Greek',
                'category': 'Appetizer',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 45,
                'total_time': 75,
                'servings': 8,
                'description': 'Greek spinach and feta pie in phyllo pastry',
                'instructions': '''1. Sauté onions in olive oil until soft.
2. Add spinach, cook until wilted, drain excess liquid well.
3. Mix spinach with feta, ricotta, eggs, dill, nutmeg.
4. Season with salt and pepper.
5. Brush baking dish with melted butter.
6. Layer 8 sheets phyllo, brushing each with butter.
7. Spread spinach mixture evenly.
8. Top with 8 more phyllo sheets, brushing each with butter.
9. Score top into serving pieces.
10. Bake at 350°F for 40-45 minutes until golden.
11. Let cool 10 minutes before cutting fully.''',
                'tips': 'Keep phyllo covered with damp towel while working. Drain spinach well to avoid soggy pie.',
                'nutritional_info': '{"calories": 320, "protein": "12g", "carbs": "24g", "fat": "20g"}',
                'dietary_tags': 'Vegetarian, contains gluten, dairy, eggs',
                'source': 'Greece',
                'rating': 4.7,
                'ingredients': [
                    ('Spinach', '2', 'lbs', 'fresh or frozen'),
                    ('Feta Cheese', '12', 'oz', 'crumbled'),
                    ('Ricotta Cheese', '1', 'cup', ''),
                    ('Phyllo Dough', '1', 'lb', ''),
                    ('Butter', '1', 'cup', 'melted'),
                    ('Onions', '2', 'medium', 'chopped'),
                    ('Eggs', '3', 'large', ''),
                    ('Dill', '1/4', 'cup', 'fresh chopped'),
                ],
                'equipment': ['Baking Sheet', 'Skillet/Frying Pan', 'Mixing Bowls', 'Pastry Brush']
            },

            {
                'name': 'Tzatziki',
                'cuisine': 'Greek',
                'category': 'Appetizer',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 0,
                'total_time': 15,
                'servings': 8,
                'description': 'Greek yogurt and cucumber sauce with garlic and herbs',
                'instructions': '''1. Grate cucumber, sprinkle with salt.
2. Let drain in strainer 15 minutes, squeeze out excess liquid.
3. Mix Greek yogurt with minced garlic.
4. Add drained cucumber.
5. Stir in olive oil, lemon juice, dill.
6. Season with salt and white pepper.
7. Refrigerate at least 30 minutes for flavors to meld.
8. Drizzle with olive oil before serving.
9. Serve with pita bread, vegetables, or grilled meats.''',
                'tips': 'Draining cucumber is essential to prevent watery sauce. Use full-fat Greek yogurt for best flavor.',
                'nutritional_info': '{"calories": 80, "protein": "4g", "carbs": "6g", "fat": "4g"}',
                'dietary_tags': 'Vegetarian, gluten-free, contains dairy',
                'source': 'Greece',
                'rating': 4.6,
                'ingredients': [
                    ('Greek Yogurt', '2', 'cups', 'full-fat'),
                    ('Cucumber', '1', 'large', ''),
                    ('Garlic', '3', 'cloves', 'minced'),
                    ('Dill', '2', 'tbsp', 'fresh chopped'),
                    ('Lemon Juice', '1', 'tbsp', ''),
                    ('Olive Oil', '2', 'tbsp', ''),
                ],
                'equipment': ['Grater', 'Strainer', 'Mixing Bowls']
            },

            # ============ SPANISH RECIPES ============
            {
                'name': 'Paella',
                'cuisine': 'Spanish',
                'category': 'Main Course',
                'difficulty': 'Hard',
                'prep_time': 30,
                'cook_time': 45,
                'total_time': 75,
                'servings': 6,
                'description': 'Traditional Spanish rice dish with seafood and chicken',
                'instructions': '''1. Season chicken with salt and paprika, brown in paella pan or large skillet.
2. Add chorizo, cook until oil releases.
3. Add onions, bell peppers, garlic, cook until soft.
4. Stir in rice, coat with oil.
5. Add saffron to hot stock.
6. Pour stock over rice, bring to boil.
7. Add tomatoes, distribute evenly.
8. Reduce heat, simmer without stirring 20 minutes.
9. Add shrimp, mussels, peas, nestle into rice.
10. Cook 10 more minutes until rice forms socarrat (crispy bottom).
11. Let rest 5 minutes, garnish with lemon wedges and parsley.''',
                'tips': 'Don\'t stir after adding stock - key to proper paella. Socarrat is the prize.',
                'nutritional_info': '{"calories": 520, "protein": "38g", "carbs": "54g", "fat": "16g"}',
                'dietary_tags': 'Contains shellfish, can be gluten-free',
                'source': 'Valencia, Spain',
                'rating': 4.9,
                'ingredients': [
                    ('Chicken Thighs', '1', 'lb', 'cut into pieces'),
                    ('Chorizo', '8', 'oz', 'sliced'),
                    ('Shrimp', '1', 'lb', 'peeled'),
                    ('Mussels', '1', 'lb', 'cleaned'),
                    ('Rice', '2', 'cups', 'bomba or arborio'),
                    ('Saffron', '1/2', 'tsp', ''),
                    ('Stock', '4', 'cups', 'chicken'),
                    ('Bell Pepper', '2', '', 'sliced'),
                ],
                'equipment': ['Large Skillet', 'Wooden Spoon', 'Chef\'s Knife']
            },

            {
                'name': 'Gazpacho',
                'cuisine': 'Spanish',
                'category': 'Soup',
                'difficulty': 'Easy',
                'prep_time': 20,
                'cook_time': 0,
                'total_time': 260,
                'servings': 6,
                'description': 'Chilled Spanish tomato soup with vegetables',
                'instructions': '''1. Roughly chop tomatoes, cucumbers, bell peppers, onion.
2. Add to blender with garlic, bread chunks (for thickness).
3. Add olive oil, vinegar, salt, pepper.
4. Blend until smooth or leave slightly chunky.
5. Taste and adjust seasoning.
6. Chill at least 4 hours or overnight.
7. Serve cold in chilled bowls.
8. Garnish with diced vegetables, croutons, olive oil drizzle.''',
                'tips': 'Use ripe summer tomatoes for best flavor. Gazpacho improves as flavors meld.',
                'nutritional_info': '{"calories": 140, "protein": "3g", "carbs": "16g", "fat": "8g"}',
                'dietary_tags': 'Vegan, can be gluten-free without bread',
                'source': 'Andalusia, Spain',
                'rating': 4.5,
                'ingredients': [
                    ('Tomatoes', '2.5', 'lbs', 'ripe'),
                    ('Cucumber', '1', 'large', ''),
                    ('Bell Pepper', '1', 'red', ''),
                    ('Onion', '1/2', 'medium', ''),
                    ('Garlic', '2', 'cloves', ''),
                    ('Bread', '2', 'slices', 'day-old'),
                    ('Olive Oil', '1/4', 'cup', ''),
                    ('Red Wine Vinegar', '2', 'tbsp', ''),
                ],
                'equipment': ['Blender', 'Chef\'s Knife', 'Mixing Bowls']
            },

            {
                'name': 'Tortilla Española',
                'cuisine': 'Spanish',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 15,
                'cook_time': 30,
                'total_time': 45,
                'servings': 6,
                'description': 'Spanish potato and egg omelet',
                'instructions': '''1. Thinly slice potatoes and onions.
2. Cook potatoes and onions in generous olive oil over medium heat until tender, not browned.
3. Drain, reserve oil.
4. Beat eggs in large bowl with salt.
5. Fold in potato-onion mixture.
6. Heat some reserved oil in large non-stick skillet.
7. Pour in egg mixture, cook over low-medium heat 8-10 minutes.
8. Place plate over skillet, flip tortilla onto plate.
9. Slide back into skillet, cook other side 5-7 minutes.
10. Slide onto serving plate, let cool slightly, cut into wedges.''',
                'tips': 'Flipping takes practice - use a plate and quick motion. Serve warm or room temperature.',
                'nutritional_info': '{"calories": 320, "protein": "12g", "carbs": "28g", "fat": "18g"}',
                'dietary_tags': 'Vegetarian, gluten-free, contains eggs',
                'source': 'Spain',
                'rating': 4.6,
                'ingredients': [
                    ('Potatoes', '4', 'large', 'Yukon Gold'),
                    ('Onions', '2', 'medium', ''),
                    ('Eggs', '6', 'large', ''),
                    ('Olive Oil', '1', 'cup', 'for cooking'),
                ],
                'equipment': ['Skillet/Frying Pan', 'Mixing Bowls', 'Spatula']
            },

            {
                'name': 'Patatas Bravas',
                'cuisine': 'Spanish',
                'category': 'Side Dish',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 35,
                'total_time': 50,
                'servings': 6,
                'description': 'Crispy fried potatoes with spicy tomato sauce and aioli',
                'instructions': '''1. Cut potatoes into irregular 1-inch chunks.
2. Boil in salted water 5 minutes, drain well.
3. Heat oil in skillet, fry potatoes until crispy and golden.
4. Make brava sauce: sauté garlic, add tomato sauce, paprika, cayenne, simmer 10 minutes.
5. Make aioli: mix mayo with garlic and lemon juice.
6. Drain potatoes on paper towels, season with salt.
7. Arrange on serving plate.
8. Drizzle with brava sauce and aioli.
9. Serve hot as tapas.''',
                'tips': 'Parboiling then frying makes potatoes extra crispy. Adjust spice level to taste.',
                'nutritional_info': '{"calories": 280, "protein": "4g", "carbs": "36g", "fat": "14g"}',
                'dietary_tags': 'Vegetarian, can be vegan, gluten-free',
                'source': 'Spain',
                'rating': 4.7,
                'ingredients': [
                    ('Potatoes', '2', 'lbs', 'Yukon Gold or russet'),
                    ('Tomato Sauce', '1', 'cup', ''),
                    ('Paprika', '2', 'tsp', 'smoked'),
                    ('Cayenne', '1/4', 'tsp', ''),
                    ('Garlic', '4', 'cloves', 'minced'),
                    ('Mayonnaise', '1/2', 'cup', ''),
                    ('Lemon Juice', '1', 'tbsp', ''),
                ],
                'equipment': ['Large Pot', 'Skillet/Frying Pan', 'Mixing Bowls']
            },

            # ============ MIDDLE EASTERN RECIPES ============
            {
                'name': 'Hummus',
                'cuisine': 'Middle Eastern',
                'category': 'Appetizer',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 0,
                'total_time': 10,
                'servings': 8,
                'description': 'Creamy chickpea dip with tahini, lemon, and garlic',
                'instructions': '''1. Drain and rinse chickpeas, reserve liquid.
2. Peel chickpeas for ultra-smooth hummus (optional but recommended).
3. Add chickpeas, tahini, garlic, lemon juice, cumin to food processor.
4. Blend until smooth, scraping sides as needed.
5. With motor running, drizzle in ice water or reserved liquid until creamy.
6. Add more lemon juice or salt to taste.
7. Transfer to serving bowl.
8. Make well in center, drizzle with olive oil.
9. Garnish with paprika, parsley, pine nuts.
10. Serve with pita bread and vegetables.''',
                'tips': 'Peeling chickpeas and using ice water creates ultra-smooth texture. Quality tahini matters.',
                'nutritional_info': '{"calories": 180, "protein": "6g", "carbs": "16g", "fat": "10g"}',
                'dietary_tags': 'Vegan, gluten-free, contains sesame',
                'source': 'Middle East',
                'rating': 4.8,
                'ingredients': [
                    ('Chickpeas', '2', 'cans', '15 oz, or 3 cups cooked'),
                    ('Tahini', '1/2', 'cup', ''),
                    ('Lemon Juice', '1/4', 'cup', 'fresh'),
                    ('Garlic', '2', 'cloves', ''),
                    ('Cumin', '1/2', 'tsp', ''),
                    ('Olive Oil', '3', 'tbsp', 'for topping'),
                    ('Paprika', '1/2', 'tsp', 'for garnish'),
                ],
                'equipment': ['Food Processor', 'Mixing Bowls']
            },

            {
                'name': 'Falafel',
                'cuisine': 'Middle Eastern',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 20,
                'total_time': 50,
                'servings': 6,
                'description': 'Crispy fried chickpea fritters with herbs and spices',
                'instructions': '''1. Use dried chickpeas, soaked overnight (NOT canned - they won\'t hold together).
2. Drain chickpeas well, dry with towel.
3. Add to food processor with onion, garlic, parsley, cilantro, spices.
4. Pulse until finely ground but not smooth.
5. Add baking powder, salt, flour, mix well.
6. Let mixture rest in fridge 30 minutes minimum.
7. Form into small balls or patties.
8. Heat oil to 350°F for frying.
9. Fry in batches 3-4 minutes until deep golden brown.
10. Drain on paper towels, serve in pita with tahini sauce.''',
                'tips': 'Must use dried chickpeas, not canned. Mixture should be moist enough to hold together.',
                'nutritional_info': '{"calories": 280, "protein": "10g", "carbs": "32g", "fat": "12g"}',
                'dietary_tags': 'Vegan, contains gluten (from flour)',
                'source': 'Middle East',
                'rating': 4.7,
                'ingredients': [
                    ('Dried Chickpeas', '2', 'cups', 'soaked overnight'),
                    ('Onion', '1', 'medium', 'chopped'),
                    ('Garlic', '4', 'cloves', ''),
                    ('Parsley', '1', 'cup', 'fresh'),
                    ('Cilantro', '1/2', 'cup', 'fresh'),
                    ('Cumin', '1', 'tbsp', ''),
                    ('Coriander', '1', 'tsp', ''),
                    ('Flour', '2', 'tbsp', ''),
                ],
                'equipment': ['Food Processor', 'Large Pot', 'Tongs', 'Mixing Bowls']
            },

            {
                'name': 'Tabbouleh',
                'cuisine': 'Middle Eastern',
                'category': 'Salad',
                'difficulty': 'Easy',
                'prep_time': 20,
                'cook_time': 10,
                'total_time': 30,
                'servings': 6,
                'description': 'Fresh parsley salad with bulgur, tomatoes, and lemon',
                'instructions': '''1. Soak bulgur in hot water 10 minutes, drain well.
2. Finely chop parsley (lots!) - it\'s the main ingredient.
3. Finely chop mint.
4. Dice tomatoes, cucumber.
5. Dice onion very fine.
6. Combine all vegetables with drained bulgur.
7. Make dressing: whisk lemon juice, olive oil, salt, pepper.
8. Pour dressing over salad, toss well.
9. Let sit 30 minutes for flavors to meld.
10. Serve cold or room temperature.''',
                'tips': 'Authentic tabbouleh is mostly parsley, not bulgur. Use flat-leaf parsley, not curly.',
                'nutritional_info': '{"calories": 140, "protein": "3g", "carbs": "18g", "fat": "7g"}',
                'dietary_tags': 'Vegan, contains wheat',
                'source': 'Lebanon',
                'rating': 4.5,
                'ingredients': [
                    ('Bulgur Wheat', '1/2', 'cup', 'fine'),
                    ('Parsley', '3', 'cups', 'finely chopped'),
                    ('Mint', '1/2', 'cup', 'fresh, chopped'),
                    ('Tomatoes', '3', 'medium', 'diced'),
                    ('Cucumber', '1', 'medium', 'diced'),
                    ('Onion', '1/4', 'cup', 'finely diced'),
                    ('Lemon Juice', '1/4', 'cup', 'fresh'),
                    ('Olive Oil', '1/4', 'cup', ''),
                ],
                'equipment': ['Mixing Bowls', 'Chef\'s Knife', 'Cutting Board']
            },

            {
                'name': 'Shawarma',
                'cuisine': 'Middle Eastern',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 120,
                'cook_time': 20,
                'total_time': 140,
                'servings': 6,
                'description': 'Spiced meat in pita with vegetables and tahini sauce',
                'instructions': '''1. Make marinade: mix yogurt, lemon juice, garlic, spices (cumin, coriander, paprika, turmeric).
2. Cut chicken into thin strips, marinate at least 2 hours.
3. Heat oil in large skillet over high heat.
4. Cook chicken in batches until charred and cooked through.
5. Warm pita bread.
6. Make tahini sauce: mix tahini, lemon, garlic, water until smooth.
7. Assemble: pita, chicken, lettuce, tomatoes, cucumbers, onions.
8. Drizzle with tahini sauce.
9. Add pickles if desired.
10. Wrap and serve.''',
                'tips': 'Marinating overnight gives best flavor. High heat creates nice char on chicken.',
                'nutritional_info': '{"calories": 420, "protein": "34g", "carbs": "38g", "fat": "16g"}',
                'dietary_tags': 'Contains gluten, dairy (in marinade)',
                'source': 'Middle East',
                'rating': 4.8,
                'ingredients': [
                    ('Chicken Thighs', '2', 'lbs', 'boneless'),
                    ('Yogurt', '1', 'cup', 'plain'),
                    ('Lemon Juice', '1/4', 'cup', ''),
                    ('Garlic', '6', 'cloves', 'minced'),
                    ('Cumin', '1', 'tbsp', ''),
                    ('Paprika', '1', 'tbsp', ''),
                    ('Pita Bread', '6', '', ''),
                    ('Tahini', '1/2', 'cup', 'for sauce'),
                ],
                'equipment': ['Mixing Bowls', 'Skillet/Frying Pan', 'Tongs']
            },

            {
                'name': 'Baklava',
                'cuisine': 'Middle Eastern',
                'category': 'Dessert',
                'difficulty': 'Medium',
                'prep_time': 30,
                'cook_time': 50,
                'total_time': 80,
                'servings': 24,
                'description': 'Sweet pastry with layers of phyllo, nuts, and honey syrup',
                'instructions': '''1. Chop pistachios and walnuts finely, mix with cinnamon and sugar.
2. Brush baking pan with melted butter.
3. Layer 8 sheets phyllo, brushing each with butter.
4. Sprinkle layer of nut mixture.
5. Add 2-3 phyllo sheets, butter, nuts. Repeat until filling is used.
6. Top with 8 phyllo sheets, buttering each.
7. Cut into diamond shapes before baking.
8. Bake at 350°F for 45-50 minutes until golden.
9. Make syrup: boil sugar, water, honey, lemon juice 10 minutes.
10. Pour hot syrup over hot baklava, let absorb overnight.''',
                'tips': 'Pour hot syrup over hot baklava for best absorption. Cut before baking for clean pieces.',
                'nutritional_info': '{"calories": 280, "protein": "4g", "carbs": "32g", "fat": "16g"}',
                'dietary_tags': 'Contains gluten, dairy, nuts',
                'source': 'Turkey/Greece/Middle East',
                'rating': 4.9,
                'ingredients': [
                    ('Phyllo Dough', '1', 'lb', ''),
                    ('Pistachios', '2', 'cups', 'chopped'),
                    ('Walnuts', '2', 'cups', 'chopped'),
                    ('Butter', '1.5', 'cups', 'melted'),
                    ('Sugar', '1.5', 'cups', 'for syrup'),
                    ('Honey', '1', 'cup', ''),
                    ('Cinnamon', '1', 'tsp', ''),
                ],
                'equipment': ['Baking Sheet', 'Saucepan', 'Pastry Brush', 'Chef\'s Knife']
            },

            # ============ AMERICAN RECIPES ============
            {
                'name': 'Classic Chocolate Chip Cookies',
                'cuisine': 'American',
                'category': 'Dessert',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 12,
                'total_time': 27,
                'servings': 24,
                'description': 'Chewy, buttery cookies loaded with chocolate chips',
                'instructions': '''1. Preheat oven to 375°F. Line baking sheets with parchment.
2. Cream butter and both sugars until fluffy (3 minutes).
3. Beat in eggs and vanilla.
4. Mix flour, baking soda, and salt in separate bowl.
5. Gradually add dry ingredients to wet ingredients.
6. Fold in chocolate chips.
7. Drop rounded tablespoons onto baking sheets, 2 inches apart.
8. Bake 10-12 minutes until edges are golden.
9. Cool on baking sheet 5 minutes before transferring to rack.
10. Store in airtight container up to 1 week.''',
                'tips': 'For chewier cookies, slightly underbake. For crispier, bake a minute longer.',
                'nutritional_info': '{"calories": 180, "protein": "2g", "carbs": "24g", "fat": "9g"}',
                'dietary_tags': 'Contains gluten, eggs, dairy',
                'source': 'American classic',
                'rating': 4.9,
                'ingredients': [
                    ('Butter', '1', 'cup', 'softened'),
                    ('Sugar', '3/4', 'cup', 'granulated'),
                    ('Brown Sugar', '3/4', 'cup', 'packed'),
                    ('Eggs', '2', '', ''),
                    ('Vanilla Extract', '2', 'tsp', ''),
                    ('Flour', '2.25', 'cups', 'all-purpose'),
                    ('Baking Soda', '1', 'tsp', ''),
                    ('Salt', '1', 'tsp', ''),
                    ('Chocolate Chips', '2', 'cups', 'semi-sweet'),
                ],
                'equipment': ['Baking Sheet', 'Mixing Bowls', 'Electric Mixer (optional)', 'Measuring Cups', 'Measuring Spoons']
            },

            {
                'name': 'Classic Hamburger',
                'cuisine': 'American',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 15,
                'cook_time': 10,
                'total_time': 25,
                'servings': 4,
                'description': 'Juicy grilled burger with classic toppings',
                'instructions': '''1. Form ground beef into 4 patties, make slight indent in center.
2. Season generously with salt and pepper.
3. Heat grill or cast iron skillet over high heat.
4. Cook burgers 4-5 minutes per side for medium.
5. Don\'t press down on burgers - keeps them juicy.
6. Add cheese last minute of cooking if desired.
7. Toast buns on grill.
8. Assemble: bottom bun, lettuce, tomato, burger, onion, pickles, condiments.
9. Top with bun, serve immediately.''',
                'tips': 'Use 80/20 beef for juiciest burgers. Don\'t overwork meat when forming patties.',
                'nutritional_info': '{"calories": 580, "protein": "32g", "carbs": "42g", "fat": "28g"}',
                'dietary_tags': 'Contains gluten, dairy (if using cheese)',
                'source': 'American classic',
                'rating': 4.8,
                'ingredients': [
                    ('Ground Beef', '1.5', 'lbs', '80/20'),
                    ('Hamburger Buns', '4', '', ''),
                    ('Cheese', '4', 'slices', 'American or cheddar'),
                    ('Lettuce', '4', 'leaves', ''),
                    ('Tomato', '1', 'large', 'sliced'),
                    ('Onion', '1', 'medium', 'sliced'),
                    ('Pickles', '8', 'slices', ''),
                ],
                'equipment': ['Grill or Skillet', 'Spatula', 'Chef\'s Knife']
            },

            {
                'name': 'Mac and Cheese',
                'cuisine': 'American',
                'category': 'Main Course',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 30,
                'total_time': 40,
                'servings': 6,
                'description': 'Creamy baked macaroni and cheese',
                'instructions': '''1. Cook macaroni until al dente, drain.
2. Melt butter in large pot, whisk in flour to make roux.
3. Gradually add milk, whisking constantly.
4. Cook until sauce thickens.
5. Add shredded cheese, stir until melted.
6. Season with salt, pepper, mustard powder.
7. Mix in cooked macaroni.
8. Transfer to baking dish.
9. Top with breadcrumbs and extra cheese.
10. Bake at 350°F for 20 minutes until bubbly and golden.''',
                'tips': 'Use mix of sharp cheddar and other cheeses for best flavor. Don\'t overcook pasta.',
                'nutritional_info': '{"calories": 520, "protein": "22g", "carbs": "52g", "fat": "24g"}',
                'dietary_tags': 'Vegetarian, contains gluten and dairy',
                'source': 'American comfort food',
                'rating': 4.7,
                'ingredients': [
                    ('Macaroni', '1', 'lb', 'elbow'),
                    ('Butter', '4', 'tbsp', ''),
                    ('Flour', '1/4', 'cup', ''),
                    ('Milk', '3', 'cups', ''),
                    ('Cheddar Cheese', '4', 'cups', 'shredded'),
                    ('Breadcrumbs', '1/2', 'cup', ''),
                    ('Mustard Powder', '1/2', 'tsp', ''),
                ],
                'equipment': ['Large Pot', 'Baking Sheet', 'Whisk', 'Wooden Spoon']
            },

            {
                'name': 'Buttermilk Pancakes',
                'cuisine': 'American',
                'category': 'Breakfast',
                'difficulty': 'Easy',
                'prep_time': 10,
                'cook_time': 20,
                'total_time': 30,
                'servings': 4,
                'description': 'Fluffy breakfast pancakes with buttermilk',
                'instructions': '''1. Mix flour, sugar, baking powder, baking soda, salt in bowl.
2. Whisk buttermilk, eggs, melted butter in separate bowl.
3. Pour wet ingredients into dry, mix until just combined (lumps OK).
4. Let batter rest 5 minutes.
5. Heat griddle or skillet over medium heat, grease lightly.
6. Pour 1/4 cup batter per pancake.
7. Cook until bubbles form on surface, 2-3 minutes.
8. Flip, cook until golden brown.
9. Keep warm in 200°F oven.
10. Serve with butter and maple syrup.''',
                'tips': 'Don\'t overmix batter - lumps are good. First pancake is test for heat level.',
                'nutritional_info': '{"calories": 320, "protein": "10g", "carbs": "48g", "fat": "10g"}',
                'dietary_tags': 'Vegetarian, contains gluten, dairy, eggs',
                'source': 'American breakfast classic',
                'rating': 4.8,
                'ingredients': [
                    ('Flour', '2', 'cups', 'all-purpose'),
                    ('Sugar', '2', 'tbsp', ''),
                    ('Baking Powder', '2', 'tsp', ''),
                    ('Baking Soda', '1/2', 'tsp', ''),
                    ('Buttermilk', '2', 'cups', ''),
                    ('Eggs', '2', 'large', ''),
                    ('Butter', '4', 'tbsp', 'melted'),
                ],
                'equipment': ['Griddle or Skillet', 'Mixing Bowls', 'Whisk', 'Spatula']
            },

            {
                'name': 'BBQ Ribs',
                'cuisine': 'American',
                'category': 'Main Course',
                'difficulty': 'Medium',
                'prep_time': 20,
                'cook_time': 180,
                'total_time': 200,
                'servings': 4,
                'description': 'Slow-cooked ribs with tangy BBQ sauce',
                'instructions': '''1. Remove membrane from back of ribs.
2. Rub ribs with dry rub (brown sugar, paprika, garlic powder, salt, pepper).
3. Let sit 30 minutes or refrigerate overnight.
4. Wrap ribs tightly in foil.
5. Bake at 300°F for 2.5 hours.
6. Unwrap, brush with BBQ sauce.
7. Broil or grill 5-10 minutes until caramelized.
8. Brush with more sauce, repeat on other side.
9. Let rest 10 minutes.
10. Cut between bones, serve with extra sauce.''',
                'tips': 'Low and slow is key to tender ribs. Removing membrane helps ribs absorb flavors.',
                'nutritional_info': '{"calories": 620, "protein": "42g", "carbs": "28g", "fat": "38g"}',
                'dietary_tags': 'Can be gluten-free with GF BBQ sauce',
                'source': 'American BBQ',
                'rating': 4.9,
                'ingredients': [
                    ('Baby Back Ribs', '2', 'racks', ''),
                    ('Brown Sugar', '1/4', 'cup', ''),
                    ('Paprika', '2', 'tbsp', ''),
                    ('Garlic Powder', '1', 'tbsp', ''),
                    ('Black Pepper', '1', 'tbsp', ''),
                    ('BBQ Sauce', '2', 'cups', ''),
                ],
                'equipment': ['Baking Sheet', 'Aluminum Foil', 'Pastry Brush']
            },
        ]
        
        for recipe in recipes_data:
            cursor.execute('''
                INSERT INTO recipes (
                    name, cuisine, category, difficulty, prep_time, cook_time, total_time,
                    servings, description, instructions, tips, nutritional_info, dietary_tags,
                    source, rating, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ''', (
                recipe['name'], recipe['cuisine'], recipe['category'], recipe['difficulty'],
                recipe['prep_time'], recipe['cook_time'], recipe['total_time'], recipe['servings'],
                recipe['description'], recipe['instructions'], recipe['tips'],
                recipe['nutritional_info'], recipe['dietary_tags'], recipe['source'], recipe['rating']
            ))
            
            recipe_id = cursor.lastrowid
            
            # Add ingredients for this recipe
            for ing in recipe['ingredients']:
                ing_name, quantity, unit, notes = ing if len(ing) == 4 else (*ing, '')
                
                # Get or create ingredient (exact name match)
                ing_id = find_or_create_ingredient_id(cursor, ing_name)
                
                # Link recipe to ingredient
                cursor.execute('''
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (recipe_id, ing_id, quantity, unit, notes))
            
            # Add equipment for this recipe
            for equip_name in recipe['equipment']:
                cursor.execute('SELECT equipment_id FROM equipment WHERE name = ?', (equip_name,))
                result = cursor.fetchone()
                
                if result:
                    equip_id = result[0]
                    cursor.execute('''
                        INSERT INTO recipe_equipment (recipe_id, equipment_id, optional)
                        VALUES (?, ?, 0)
                    ''', (recipe_id, equip_id))
        
        self.conn.commit()
        print(f"Populated {len(recipes_data)} recipes with ingredients and equipment")
        
    def initialize_database(self):
        """Initialize the complete database"""
        self.connect()
        self.create_tables()
        self.populate_cuisines()
        self.populate_ingredients()
        self.populate_equipment()
        self.populate_recipes()
        self.conn.close()
        print("\n✓ Recipe database initialization complete!")
        print(f"\nDatabase now contains 60+ recipes across:")
        print("  • Italian: Carbonara, Pizza, Risotto, Lasagna, Bruschetta, Tiramisu")
        print("  • French: Coq au Vin, Ratatouille, Quiche, Beef Bourguignon, French Onion Soup, Crème Brûlée")
        print("  • Chinese: Kung Pao, Mapo Tofu, Sweet & Sour Pork, Fried Rice, Hot & Sour Soup")
        print("  • Japanese: Teriyaki, Miso Soup, Ramen, Gyoza, Tempura")
        print("  • Indian: Butter Chicken, Tikka Masala, Dal, Biryani, Samosas")
        print("  • Mexican: Tacos, Enchiladas, Guacamole, Quesadillas, Churros")
        print("  • Thai: Pad Thai, Green Curry, Tom Yum, Mango Sticky Rice")
        print("  • Greek: Moussaka, Greek Salad, Spanakopita, Tzatziki")
        print("  • Spanish: Paella, Gazpacho, Tortilla Española, Patatas Bravas")
        print("  • Middle Eastern: Hummus, Falafel, Tabbouleh, Shawarma, Baklava")
        print("  • American: Cookies, Burgers, Mac & Cheese, Pancakes, BBQ Ribs")


if __name__ == "__main__":
    # Initialize database
    db = RecipeDatabase("recipe_collection.db")
    db.initialize_database()
