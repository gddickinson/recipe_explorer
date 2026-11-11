// The shopping list lives in this browser only (localStorage): chosen recipes with servings, the unit system and
// ticked-off items. Nothing is sent to a server, so it works the same on the static site and the local app.
const KEY = 'recipe_explorer.shopping';
function read() {
  try { const v = JSON.parse(localStorage.getItem(KEY) || '{}'); return { recipes: Array.isArray(v.recipes) ? v.recipes : [], units: v.units === 'metric' ? 'metric' : 'us', done: v.done || {} }; }
  catch { return { recipes: [], units: 'us', done: {} }; }
}
function write(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* storage blocked: list lasts for this page only */ } }

export const load = read;
export const save = write;
export function addRecipe(id, servings) {
  const s = read();
  const hit = s.recipes.find(r => r.id === +id);
  if (hit) hit.servings = servings; else s.recipes.push({ id: +id, servings });
  write(s);
  return s;
}
export function hasRecipe(id) { return read().recipes.some(r => r.id === +id); }
// '?r=' value for /api/shopping.
export const selection = s => s.recipes.map(r => `${r.id}:${r.servings}`).join(',');
