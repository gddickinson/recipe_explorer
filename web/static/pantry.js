// Ingredients and kitchen equipment: filterable lists (like the desktop Ingredients and Equipment tabs) and detail
// pages that list the recipes using each item.
import { route, api, app, esc, list } from './core.js';
import { listPage, kv, sections, crumb, trim, or, recipeCard } from './ui.js';

route('ingredients', async (_args, query) => {
  const f = (await api('/facets')).ingredients;
  await listPage({
    routeName: 'ingredients', kind: 'ingredients', kicker: 'Kitchen', title: 'Ingredients', query,
    lead: 'Every ingredient the recipes use. The common ones have storage tips, substitutes, nutrition, allergens and season.',
    placeholder: 'e.g. garlic, dairy, summer',
    filters: [{ id: 'category', label: 'Category', options: f.category }],
    card: i => `<a class="card" href="#/ingredient/${i.ingredient_id}"><small>${esc(or(i.category, ''))}</small><b>${esc(i.name)}</b>
      ${i.description ? `<span>${esc(trim(i.description, 100))}</span>` : ''}
      <div class="meta"><span>${i.recipes} recipe${i.recipes === 1 ? '' : 's'}</span><span>${esc(i.season || '')}</span></div></a>`,
  });
});

route('ingredient', async ([id]) => {
  const i = await api('/ingredients/' + encodeURIComponent(id));
  const recipes = [...new Map(i.used_in.map(r => [r.recipe_id, r])).values()];
  app().innerHTML = `
    ${crumb('#/ingredients', 'Ingredients', i.category || '')}
    <h1>${esc(i.name)}</h1>
    <p class="lead">${esc(i.description || 'No description in the database yet.')}</p>
    ${kv([['category', i.category], ['best season', i.season], ['used in', `${recipes.length} recipe${recipes.length === 1 ? '' : 's'}`]])}
    ${sections([['Storage tips', i.storage_tips], ['Substitutes', i.substitutes], ['Nutritional notes', i.nutritional_notes],
      ['Allergen information', i.allergen_info]])}
    ${recipes.length ? `<h2>Recipes using ${esc(i.name)}</h2>
      <p><a href="#/recipes?ingredient=${encodeURIComponent(i.name)}">Filter the recipe list by this ingredient</a></p>
      <div class="grid">${list(recipes, recipeCard)}</div>` : ''}`;
});

const ESSENTIAL = [['1', 'Essential only'], ['0', 'Optional only']];

route('equipment', async (_args, query) => {
  const f = (await api('/facets')).equipment;
  await listPage({
    routeName: 'equipment', kind: 'equipment', kicker: 'Kitchen', title: 'Kitchen equipment', query,
    lead: 'Knives, cookware, bakeware, tools and appliances, with care tips, substitutes and price ranges. ★ marks the essentials.',
    placeholder: 'e.g. knife, pan, hand wash',
    filters: [{ id: 'category', label: 'Category', options: f.category }, { id: 'essential', label: 'Essential', options: ESSENTIAL }],
    card: e => `<a class="card" href="#/tool/${e.equipment_id}"><small>${esc(or(e.category, ''))}</small>
      <b>${e.essential ? '<span class="rate" aria-label="essential">★</span> ' : ''}${esc(e.name)}</b><span>${esc(trim(e.description, 100))}</span>
      <div class="meta"><span>${e.recipes} recipe${e.recipes === 1 ? '' : 's'}</span><span>${esc(e.price_range || '')}</span></div></a>`,
  });
});

route('tool', async ([id]) => {
  const e = await api('/equipment/' + encodeURIComponent(id));
  app().innerHTML = `
    ${crumb('#/equipment', 'Equipment', e.category || '')}
    <h1>${e.essential ? '★ ' : ''}${esc(e.name)}</h1>
    <p class="lead">${esc(e.description || '')}</p>
    ${kv([['category', e.category], ['essential', e.essential ? 'Yes' : 'Optional'], ['price range', e.price_range],
      ['used in', `${e.used_in.length} recipe${e.used_in.length === 1 ? '' : 's'}`]])}
    ${sections([['Substitutes', e.substitutes], ['Care and maintenance', e.care_tips]])}
    ${e.used_in.length ? `<h2>Recipes that need it</h2><div class="grid">${list(e.used_in, recipeCard)}</div>` : ''}`;
});
