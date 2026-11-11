// Home (hero, live counts, entry cards), search across every list, and About.
import { route, api, app, esc, list, isStatic } from './core.js';
import { trim, recipeCard } from './ui.js';
import { load } from './shopping_store.js';

const DOORS = [
  ['#/recipes', 'Recipes', 'Search and filter by cuisine, category, difficulty, time, diet, ingredient or equipment.', 'recipes'],
  ['#/ingredients', 'Ingredients', 'Storage tips, substitutes, nutrition, allergens and season, with the recipes that use each one.', 'ingredients'],
  ['#/equipment', 'Kitchen equipment', 'Essential and optional tools with care tips, substitutes and price ranges.', 'equipment'],
  ['#/cuisines', 'World cuisines', 'Regions, characteristics, common ingredients and popular dishes.', 'cuisines'],
  ['#/shopping', 'Shopping list', 'Pick recipes and servings; get combined totals in US or metric units, then print or export.', null],
  ['#/add', 'Add a recipe', 'Write your own recipes into the collection (local app only).', null],
];

route('home', async () => {
  const s = await api('/stats');
  const picks = (await api('/recipes')).filter(r => r.rating >= 4.9).slice(0, 6);
  const nShop = load().recipes.length;
  app().innerHTML = `
  <section class="hero">
    <p class="kicker">Recipes · Ingredients · Equipment · Shopping</p>
    <h1 class="glow">Recipe Collection Explorer</h1>
    <p class="lead">Browse recipes from world cuisines, scale them to the number of people you are cooking for, switch
    to metric, and build a shopping list. Look up ingredients and kitchen equipment along the way.</p>
    <form id="hsearch" role="search" class="row"><div><label for="hs-q">Search everything</label>
      <input id="hs-q" type="search" placeholder="e.g. lentils, risotto, wok, vegan"></div>
      <div style="flex:0"><button type="submit">Search</button></div></form>
  </section>
  <div class="tiles">
    <a class="tile" href="#/recipes"><b>${s.recipes}</b><span>recipes</span></a>
    <a class="tile" href="#/cuisines"><b>${s.cuisines}</b><span>cuisines</span></a>
    <a class="tile" href="#/ingredients"><b>${s.ingredients}</b><span>ingredients</span></a>
    <a class="tile" href="#/equipment"><b>${s.equipment}</b><span>equipment items</span></a>
    <a class="tile" href="#/shopping"><b>${nShop}</b><span>on your shopping list</span></a>
  </div>
  <div class="grid wide">${list(DOORS, ([href, t, d, k]) => `<a class="card door" href="${href}"><b>${t}${k ? ` <em class="n">${s[k]}</em>` : ''}</b><span>${d}</span></a>`)}</div>
  ${picks.length ? `<h2>Top rated</h2><div class="grid">${list(picks, recipeCard)}</div>` : ''}`;
  document.getElementById('hsearch').addEventListener('submit', e => {
    e.preventDefault();
    location.hash = '#/search?q=' + encodeURIComponent(document.getElementById('hs-q').value.trim());
  });
});

const GROUPS = [
  ['recipes', 'Recipes', r => [`#/recipe/${r.recipe_id}`, r.name, `${r.cuisine} · ${r.category}`, r.description]],
  ['ingredients', 'Ingredients', i => [`#/ingredient/${i.ingredient_id}`, i.name, i.category, i.description]],
  ['equipment', 'Equipment', e => [`#/tool/${e.equipment_id}`, e.name, e.category, e.description]],
  ['cuisines', 'Cuisines', c => [`#/cuisine/${c.cuisine_id}`, c.name, c.region, c.description]],
];

route('search', async (_args, query) => {
  app().innerHTML = `<p class="kicker">Search</p><h1>Search everything</h1>
    <div class="panel"><label for="s-q">Search recipes, ingredients, equipment and cuisines</label>
    <input id="s-q" type="search" value="${esc(query.q || '')}" placeholder="e.g. coconut milk, gluten-free, Sichuan"></div>
    <div id="s-out" aria-live="polite"></div>`;
  const input = document.getElementById('s-q');
  let seq = 0;
  async function run() {
    const n = ++seq, q = input.value.trim();
    history.replaceState(null, '', '#/search' + (q ? '?q=' + encodeURIComponent(q) : ''));
    const res = await api('/search?q=' + encodeURIComponent(q));
    if (n !== seq) return;
    const total = GROUPS.reduce((a, [k]) => a + res[k].length, 0);
    document.getElementById('s-out').innerHTML = !q ? '<p class="mute">Type a word or two; every word must match.</p>'
      : `<p class="mute small">${total} results</p>` + list(GROUPS.filter(([k]) => res[k].length), ([k, title, fn]) =>
        `<h2>${title} <span class="mute small">${res[k].length}</span></h2><div class="grid">${list(res[k], r => {
          const [href, name, sub, text] = fn(r);
          return `<a class="card" href="${href}"><small>${esc(sub || '')}</small><b>${esc(name)}</b><span>${esc(trim(text, 100))}</span></a>`;
        })}</div>`);
  }
  input.addEventListener('input', run);
  input.focus();
  await run();
});

route('about', async () => {
  const s = await api('/stats');
  app().innerHTML = `<p class="kicker">About</p><h1>Recipe Collection Explorer</h1>
    <p class="lead">A Python application for managing recipes, ingredients and kitchen equipment. This web interface
    shows the same SQLite database as the desktop app: ${s.recipes} recipes from ${s.recipe_cuisines} cuisines,
    ${s.ingredients} ingredients, ${s.equipment} equipment items and ${s.cuisines} cuisine profiles.</p>
    ${isStatic() ? '<p class="callout">This is the static (GitHub Pages) version: browsing, search, scaling, unit conversion and the shopping list all work here; adding, editing and rating recipes need the local app.</p>' : ''}
    <h2>Run the desktop app</h2>
    <pre>python3 run_recipe_explorer.py</pre>
    <p>A Tkinter app (standard library only) with tabs for recipes, ingredients, equipment, cuisines and the shopping
    list, plus forms to add recipes, ingredients and equipment.</p>
    <h2>Run the web app</h2>
    <pre>pip install -r requirements-web.txt
python run_web.py        # http://127.0.0.1:8115</pre>
    <p>The local web app reads recipe_collection.db read-only for browsing; adding, editing and rating a recipe write to
    the same file the desktop app uses. <code>python scripts/build_static.py</code> exports this static site.</p>
    <h2>Scaling and units</h2>
    <p>Quantities are scaled by new servings ÷ recipe servings and shown as kitchen fractions (1/4, 1/3, 1/2 ...).
    Metric mode converts teaspoons, tablespoons and cups to ml and ounces and pounds to grams (ounces are taken as
    weight); other units (cloves, cans, "to taste") stay as written. The rules are in <code>recipe_scaling.py</code>.</p>
    <h2>Credits</h2>
    <p>Starter recipes compiled from traditional recipes and culinary sources; recipe data compiled from public domain
    traditional recipes and general culinary knowledge (from the project README).</p>
    <p>Built with Python, Tkinter and SQLite (desktop) and FastAPI with plain JavaScript (web), with AI assistance from
    <a href="https://claude.com/" target="_blank" rel="noopener">Claude (Anthropic)</a>. Released under the MIT licence.
    <a href="https://github.com/gddickinson/recipe_explorer" target="_blank" rel="noopener">Source on GitHub</a>.</p>`;
});
