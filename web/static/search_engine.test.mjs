// node search_engine.test.mjs: the JS filters must give the same results as web/search.py. Expected ids below were
// computed by running web.search.filter_rows on the same rows (tests/test_web.py also checks parity on the full data).
import assert from 'node:assert/strict';
import { filterRows, terms } from './search_engine.js';

const recipes = [
  { recipe_id: 1, name: 'Mac and Cheese', cuisine: 'American', category: 'Main Course', difficulty: 'Easy', total_time: 45,
    description: 'Creamy baked pasta', instructions: 'Boil macaroni.', dietary_tags: 'Vegetarian, contains gluten, dairy',
    ingredients: ['Macaroni', 'Milk', 'Cheddar Cheese'], equipment: ['Large Pot', 'Whisk'] },
  { recipe_id: 2, name: 'Hummus', cuisine: 'Middle Eastern', category: 'Appetizer', difficulty: 'Easy', total_time: 10,
    description: 'Chickpea dip', instructions: 'Blend.', dietary_tags: 'Vegan, gluten-free, contains sesame',
    ingredients: ['Chickpeas', 'Tahini', 'Lemon Juice'], equipment: ['Food Processor'] },
  { recipe_id: 3, name: 'Pad Thai', cuisine: 'Thai', category: 'Main Course', difficulty: 'Medium', total_time: null,
    description: 'Stir-fried noodles', instructions: 'Soak noodles.', dietary_tags: 'Can be vegan, contains peanuts',
    ingredients: ['Rice Noodles', 'Peanuts'], equipment: ['Wok or Large Skillet'] },
];
const cases = [[{}, [1, 2, 3]], [{ q: 'noodles' }, [3]], [{ q: 'CHEESE whisk' }, [1]], [{ ingredient: 'tahini' }, [2]],
  [{ ingredient: 'Tahin' }, []], [{ equipment: 'Food Processor' }, [2]], [{ diet: 'vegan' }, [2]], [{ diet: 'Vegetarian' }, [1]],
  [{ max_time: '30' }, [2]], [{ max_time: 'abc' }, [1, 2, 3]], [{ max_time: ' 60 ' }, [1, 2]], [{ category: 'Main Course' }, [1, 3]],
  [{ cuisine: 'thai' }, []], [{ difficulty: 'Easy', q: 'dip' }, [2]], [{ q: 'middle eastern' }, [2]]];
for (const [q, ids] of cases) assert.deepEqual(filterRows('recipes', recipes, q).map(r => r.recipe_id), ids, JSON.stringify(q));

const equipment = [{ equipment_id: 1, name: 'Whisk', category: 'Utensils', essential: true },
  { equipment_id: 2, name: 'Blender', category: 'Appliances', essential: false }];
const ecases = [[{ essential: '1' }, [1]], [{ essential: '0' }, [2]], [{ essential: '' }, [1, 2]], [{ category: 'Appliances' }, [2]]];
for (const [q, ids] of ecases) assert.deepEqual(filterRows('equipment', equipment, q).map(r => r.equipment_id), ids, JSON.stringify(q));

assert.deepEqual(terms('Vegetarian, contains gluten,  dairy ,'), ['vegetarian', 'contains gluten', 'dairy']);
console.log('search_engine: all ok');
