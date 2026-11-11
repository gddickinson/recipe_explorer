// Recipes: filterable list (the desktop Recipes tab's filters plus ingredient, equipment and diet) and a detail page
// with servings scaling, US/metric units, add-to-shopping-list and (local app only) rating and editing.
import { route, api, app, esc, list, tags, isStatic, needsServer } from './core.js';
import { listPage, kv, crumb, recipeCard, stars, mins, words } from './ui.js';
import { addRecipe, hasRecipe } from './shopping_store.js';

// Same choices as the desktop app's "Max time" filter.
const TIMES = [['30', '30 min or less'], ['60', '1 hour or less'], ['90', '1.5 hours or less'], ['120', '2 hours or less']];
const DIET = { vegetarian: 'Vegetarian', vegan: 'Vegan', 'gluten-free': 'Gluten-free', 'dairy-free': 'Dairy-free' };

route('recipes', async (_args, query) => {
  const f = (await api('/facets')).recipes;
  await listPage({
    routeName: 'recipes', kind: 'recipes', kicker: 'Recipes', title: 'Recipes', query,
    lead: 'Recipes from world cuisines. Search names, descriptions, instructions, ingredients and equipment; every word must match.',
    placeholder: 'e.g. chicken curry, risotto, whisk',
    filters: [
      { id: 'cuisine', label: 'Cuisine', options: f.cuisine },
      { id: 'category', label: 'Category', options: f.category },
      { id: 'difficulty', label: 'Difficulty', options: f.difficulty },
      { id: 'max_time', label: 'Total time', options: TIMES },
      { id: 'diet', label: 'Diet', options: f.diet, names: DIET },
      { id: 'ingredient', label: 'Uses ingredient', options: f.ingredient, datalist: true, placeholder: 'e.g. Garlic' },
      { id: 'equipment', label: 'Uses equipment', options: f.equipment },
    ],
    card: recipeCard,
  });
});

const steps = text => String(text || '').split('\n').map(s => s.trim()).filter(Boolean).map(s => s.replace(/^\d+[.)]\s*/, ''));

function ingredientList(r) {
  return `<ul class="ings">${list(r.ingredients, i => `<li><span class="q">${esc(i.quantity)} ${esc(i.unit)}</span>
    <span><a href="#/ingredient/${i.ingredient_id}">${esc(i.name)}</a>${i.notes ? ` <span class="note">(${esc(i.notes)})</span>` : ''}</span></li>`)}</ul>`;
}

route('recipe', async ([id], query) => {
  const units = query.units === 'metric' ? 'metric' : 'us';
  const qs = new URLSearchParams({ ...(query.servings ? { servings: query.servings } : {}), units }).toString();
  const r = await api(`/recipes/${encodeURIComponent(id)}?${qs}`, { fresh: !isStatic() }); // local data can change (edits)
  const inList = hasRecipe(r.recipe_id);
  app().innerHTML = `
    ${crumb('#/recipes', 'Recipes', `${r.cuisine} · ${r.category}`)}
    <h1>${esc(r.name)}</h1>
    <p class="lead">${esc(r.description || '')}</p>
    ${kv([['difficulty', r.difficulty], ['prep', mins(r.prep_time), true], ['cook', mins(r.cook_time), true],
      ['total', mins(r.total_time), true], ['serves', r.servings],
      ['rating', r.rating ? `<span class="stars">${stars(r.rating)}</span> ${r.rating}` : '—', true]])}
    <div class="recipe-side">
      <div>
        <div class="panel noprint">
          <div class="scale">
            <div><label for="r-serv">Servings</label><div class="stepper">
              <button type="button" class="alt" id="r-minus" aria-label="Fewer servings">−</button>
              <input id="r-serv" type="number" min="1" max="1000" value="${r.servings_shown}" inputmode="numeric">
              <button type="button" class="alt" id="r-plus" aria-label="More servings">+</button></div></div>
            <div><label for="r-units">Units</label><select id="r-units">
              <option value="us" ${units === 'us' ? 'selected' : ''}>As written (US)</option>
              <option value="metric" ${units === 'metric' ? 'selected' : ''}>Metric (g, ml)</option></select></div>
          </div>
          <p class="small mute">${r.servings_shown !== r.servings ? `Scaled from ${r.servings} to ${r.servings_shown} servings. ` : ''}${units === 'metric' ? 'Cups and spoons in ml, oz and lb in grams.' : ''}</p>
          <button type="button" id="r-shop">${inList ? 'Update on shopping list' : 'Add to shopping list'}</button>
          <span id="r-msg" class="small toast" aria-live="polite"></span>
        </div>
        <h2>Ingredients</h2>${ingredientList(r)}
        ${r.equipment.length ? `<h2>Equipment</h2><p>${list(r.equipment, e => `<a class="tag c" href="#/tool/${e.equipment_id}">${esc(e.name)}</a>`)}</p>` : ''}
      </div>
      <div>
        <h2>Instructions</h2><ol class="steps">${list(steps(r.instructions), s => `<li>${esc(s)}</li>`)}</ol>
        ${r.tips ? `<h3>Chef's tips</h3><p>${esc(r.tips)}</p>` : ''}
        ${r.nutrition ? `<h3>Nutrition (per serving)</h3>${kv(Object.entries(r.nutrition).map(([k, v]) => [k, v]))}` : ''}
        ${r.dietary_tags ? `<h3>Dietary information</h3><p>${tags(words(r.dietary_tags), 'b')}</p>` : ''}
        ${r.source ? `<h3>Source</h3><p>${esc(r.source)}</p>` : ''}
      </div>
    </div>
    <div class="noprint" id="r-local"></div>
    <p class="noprint"><a class="btn alt" href="#/recipes?cuisine=${encodeURIComponent(r.cuisine)}">More ${esc(r.cuisine)} recipes</a>
    <a class="btn alt" href="#/shopping">Shopping list</a></p>`;

  const serv = document.getElementById('r-serv'), unitSel = document.getElementById('r-units');
  const go = () => {
    const n = Math.min(1000, Math.max(1, parseInt(serv.value, 10) || r.servings));
    location.hash = `#/recipe/${r.recipe_id}?servings=${n}&units=${unitSel.value}&keep=1`;
  };
  serv.addEventListener('change', go);
  unitSel.addEventListener('change', go);
  document.getElementById('r-minus').addEventListener('click', () => { serv.value = Math.max(1, (+serv.value || 1) - 1); go(); });
  document.getElementById('r-plus').addEventListener('click', () => { serv.value = Math.min(1000, (+serv.value || 0) + 1); go(); });
  document.getElementById('r-shop').addEventListener('click', () => {
    const s = addRecipe(r.recipe_id, r.servings_shown);
    document.getElementById('r-msg').textContent = `On your list for ${r.servings_shown} servings (${s.recipes.length} recipe${s.recipes.length === 1 ? '' : 's'}).`;
    document.getElementById('r-shop').textContent = 'Update on shopping list';
  });

  const local = document.getElementById('r-local');
  if (isStatic()) { local.innerHTML = needsServer('Rating and editing recipes'); return; }
  local.innerHTML = `<div class="panel"><h3>Your rating</h3>
    <div class="row"><div><label for="r-rate">Rating</label><select id="r-rate">${[5, 4, 3, 2, 1].map(n =>
      `<option value="${n}" ${Math.round(r.rating || 3) === n ? 'selected' : ''}>${stars(n)} (${n})</option>`).join('')}</select></div>
    <div style="flex:0"><button type="button" id="r-save-rate">Save rating</button></div></div>
    <p id="r-rate-msg" class="small" aria-live="polite"></p>
    <a class="btn alt" href="#/edit/${r.recipe_id}">Edit this recipe</a></div>`;
  document.getElementById('r-save-rate').addEventListener('click', async () => {
    const msg = document.getElementById('r-rate-msg');
    try {
      await api(`/recipes/${r.recipe_id}/rating`, { body: { rating: +document.getElementById('r-rate').value } });
      location.hash = `#/recipe/${r.recipe_id}?servings=${r.servings_shown}&units=${units}&rated=${Date.now()}&keep=1`;
    } catch (e) { msg.className = 'small err'; msg.textContent = e.message; }
  });
});
