// Shopping list: recipes chosen on recipe pages (kept in this browser), each at its own servings, shown either as
// combined totals (same ingredient and unit added up) or by recipe like the desktop Shopping List tab. Export writes
// the desktop app's text format. Works the same on the static site (computed in the browser by scaling_engine.js).
import { route, api, app, esc, list, download } from './core.js';
import { load, save, selection } from './shopping_store.js';

const line = i => `${i.quantity} ${i.unit} ${i.name}`.replace(/\s+/g, ' ').trim();
const key = i => `${i.name}|${i.unit}`.toLowerCase();

// The desktop app's export format (grouped by recipe), here with scaled quantities.
export function exportText(data) {
  let out = 'SHOPPING LIST\n' + '='.repeat(50) + '\n\n';
  for (const r of data.recipes) {
    out += `\n${r.name} (${r.servings} servings)\n` + '-'.repeat(50) + '\n';
    for (const i of r.ingredients) out += `☐ ${line(i)}\n`;
  }
  return out;
}

route('shopping', async (_args, query) => {
  const s = load();
  const view = query.view === 'recipes' ? 'recipes' : 'combined';
  if (!s.recipes.length) {
    app().innerHTML = `<p class="kicker">Plan</p><h1>Shopping list</h1>
      <p class="lead">Your list is empty. Open a recipe, set the servings and press "Add to shopping list".</p>
      <p class="mute small">The list is kept in this browser only; nothing is sent anywhere.</p>
      <p><a class="btn" href="#/recipes">Browse recipes</a></p>`;
    return;
  }
  const data = await api(`/shopping?r=${encodeURIComponent(selection(s))}&units=${s.units}`, { fresh: true });
  const item = (i, k) => `<label class="shop-item ${s.done[k] ? 'done' : ''}"><input type="checkbox" data-k="${esc(k)}" ${s.done[k] ? 'checked' : ''}>
    <span>${esc(line(i))}${i.recipes && i.recipes.length > 1 ? `<small class="from">${esc(i.recipes.join(' · '))}</small>` : ''}</span></label>`;
  app().innerHTML = `<p class="kicker">Plan</p><h1>Shopping list</h1>
    <p class="lead">${data.items.length} items for ${data.recipes.length} recipe${data.recipes.length === 1 ? '' : 's'}. Kept in this browser only.</p>
    <div class="panel noprint">
      <h3>Recipes</h3>
      ${list(data.recipes, r => `<div class="chosen"><a href="#/recipe/${r.recipe_id}?servings=${r.servings}&units=${s.units}">${esc(r.name)}</a>
        <label class="small" for="sv-${r.recipe_id}" style="margin:0">Servings</label>
        <input id="sv-${r.recipe_id}" type="number" min="1" max="1000" value="${r.servings}" data-id="${r.recipe_id}">
        <button type="button" class="alt" data-rm="${r.recipe_id}" aria-label="Remove ${esc(r.name)}">Remove</button></div>`)}
      <div class="row" style="margin-top:10px">
        <div><label for="sh-units">Units</label><select id="sh-units"><option value="us">As written (US)</option>
          <option value="metric" ${s.units === 'metric' ? 'selected' : ''}>Metric (g, ml)</option></select></div>
        <div><label for="sh-view">Show</label><select id="sh-view"><option value="combined">Combined totals</option>
          <option value="recipes" ${view === 'recipes' ? 'selected' : ''}>By recipe</option></select></div>
      </div>
      <button type="button" id="sh-export">Export .txt</button><button type="button" class="alt" id="sh-print">Print</button>
      <button type="button" class="alt" id="sh-clear">Clear all</button>
    </div>
    <div class="panel" id="sh-list">${view === 'combined' ? list(data.items, i => item(i, key(i)))
      : list(data.recipes, r => `<h3>${esc(r.name)} · ${r.servings} servings</h3>${list(r.ingredients, i => item(i, r.recipe_id + ':' + key(i)))}`)}</div>`;

  const rerender = () => { location.hash = `#/shopping?view=${document.getElementById('sh-view').value}&t=${Date.now()}`; };
  app().querySelectorAll('input[data-id]').forEach(inp => inp.addEventListener('change', () => {
    const n = Math.min(1000, Math.max(1, parseInt(inp.value, 10) || 1));
    s.recipes.find(r => r.id === +inp.dataset.id).servings = n; save(s); rerender();
  }));
  app().querySelectorAll('button[data-rm]').forEach(b => b.addEventListener('click', () => {
    s.recipes = s.recipes.filter(r => r.id !== +b.dataset.rm); save(s); rerender();
  }));
  app().querySelectorAll('input[data-k]').forEach(c => c.addEventListener('change', () => {
    if (c.checked) s.done[c.dataset.k] = 1; else delete s.done[c.dataset.k];
    save(s); c.closest('.shop-item').classList.toggle('done', c.checked);
  }));
  document.getElementById('sh-units').addEventListener('change', e => { s.units = e.target.value; save(s); rerender(); });
  document.getElementById('sh-view').addEventListener('change', rerender);
  document.getElementById('sh-export').addEventListener('click', () => download('shopping_list.txt', exportText(data)));
  document.getElementById('sh-print').addEventListener('click', () => print());
  document.getElementById('sh-clear').addEventListener('click', () => {
    if (confirm('Clear the shopping list?')) { save({ recipes: [], units: s.units, done: {} }); rerender(); }
  });
});
