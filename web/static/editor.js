// Add or edit a recipe: local app only (writes recipe_collection.db through the server's RecipeDAO, the same database
// the desktop app uses). On the static site this explains that writing needs the local app.
import { route, api, app, esc, list, isStatic, needsServer } from './core.js';
import { crumb } from './ui.js';

const CATEGORIES = ['Main Course', 'Appetizer', 'Dessert', 'Soup', 'Salad', 'Side Dish', 'Breakfast'];  // desktop form's list

const ingredientLines = r => r.ingredients.map(i =>
  [i.original.quantity, i.original.unit, i.name, i.notes].map(v => String(v ?? '').trim()).join(' | ').replace(/( \| )+$/, '')).join('\n');

function form(r, f) {
  const v = k => esc(r ? r[k] ?? '' : '');
  const cuisines = Object.keys(f.cuisine), cats = [...new Set([...CATEGORIES, ...Object.keys(f.category)])];
  return `<form class="panel" id="rform">
    <div class="formgrid">
      <div><label for="e-name">Recipe name *</label><input id="e-name" required value="${v('name')}"></div>
      <div><label for="e-cuisine">Cuisine *</label><input id="e-cuisine" list="e-cl" required value="${v('cuisine')}">
        <datalist id="e-cl">${list(cuisines, c => `<option value="${esc(c)}">`)}</datalist></div>
      <div><label for="e-category">Category *</label><input id="e-category" list="e-catl" required value="${v('category')}">
        <datalist id="e-catl">${list(cats, c => `<option value="${esc(c)}">`)}</datalist></div>
      <div><label for="e-difficulty">Difficulty</label><select id="e-difficulty">${['Easy', 'Medium', 'Hard'].map(d =>
        `<option ${(r ? r.difficulty : 'Medium') === d ? 'selected' : ''}>${d}</option>`).join('')}</select></div>
      <div><label for="e-prep">Prep time (min)</label><input id="e-prep" type="number" min="0" value="${r ? v('prep_time') : 0}"></div>
      <div><label for="e-cook">Cook time (min)</label><input id="e-cook" type="number" min="0" value="${r ? v('cook_time') : 0}"></div>
      <div><label for="e-servings">Servings</label><input id="e-servings" type="number" min="1" value="${r ? v('servings') : 4}"></div>
    </div>
    <label for="e-description">Description</label><textarea id="e-description" style="min-height:60px">${v('description')}</textarea>
    <label for="e-ingredients">Ingredients: one per line, "quantity | unit | name | notes" (or "2 cups flour")</label>
    <textarea id="e-ingredients" style="min-height:160px">${r ? esc(ingredientLines(r)) : ''}</textarea>
    <label for="e-instructions">Instructions *</label><textarea id="e-instructions" required style="min-height:180px">${v('instructions')}</textarea>
    <label for="e-tips">Tips</label><textarea id="e-tips" style="min-height:60px">${v('tips')}</textarea>
    <button type="submit">${r ? 'Save changes' : 'Save recipe'}</button>
    ${r ? `<a class="btn alt" href="#/recipe/${r.recipe_id}">Cancel</a>` : ''}
    <p id="e-msg" class="small" aria-live="polite"></p>
  </form>`;
}

const FIELDS = ['name', 'cuisine', 'category', 'difficulty', 'prep', 'cook', 'servings', 'description', 'ingredients', 'instructions', 'tips'];
const NAMES = { prep: 'prep_time', cook: 'cook_time' };

async function page(r) {
  const title = r ? `Edit ${r.name}` : 'Add a recipe';
  const head = r ? crumb(`#/recipe/${r.recipe_id}`, r.name, 'edit') : '<p class="kicker">Write</p>';
  if (isStatic()) {
    app().innerHTML = `${head}<h1>${esc(title)}</h1>${needsServer('Adding and editing recipes')}
      <p class="mute">Recipes are saved in recipe_collection.db on your own computer, through the desktop app or the
      local web app. This published site is read-only.</p>`;
    return;
  }
  const f = (await api('/facets', { fresh: true })).recipes;
  app().innerHTML = `${head}<h1>${esc(title)}</h1>
    <p class="lead">${r ? 'Changes are saved' : 'The recipe is saved'} to recipe_collection.db (shared with the desktop app). Fields marked * are required.</p>
    ${form(r, f)}`;
  document.getElementById('rform').addEventListener('submit', async e => {
    e.preventDefault();
    const msg = document.getElementById('e-msg');
    const body = Object.fromEntries(FIELDS.map(k => [NAMES[k] || k, document.getElementById('e-' + k).value]));
    try {
      const res = await api(r ? `/recipes/${r.recipe_id}` : '/recipes', { body });
      location.hash = `#/recipe/${res.recipe_id}`;
    } catch (err) { msg.className = 'small err'; const m = /"detail":"([^"]*)"/.exec(err.message); msg.textContent = m ? m[1] : err.message; }
  });
}

route('add', () => page(null));
route('edit', async ([id]) => page(await api('/recipes/' + encodeURIComponent(id), { fresh: true })));
