// World cuisines (the desktop Cuisines tab): region, characteristics, common ingredients, popular dishes and the
// recipes in the collection.
import { route, api, app, esc, list, tags } from './core.js';
import { listPage, kv, sections, crumb, trim, words, recipeCard } from './ui.js';

route('cuisines', async (_args, query) => {
  const f = (await api('/facets')).cuisines;
  await listPage({
    routeName: 'cuisines', kind: 'cuisines', kicker: 'Kitchen', title: 'World cuisines', query,
    lead: 'Culinary traditions: where they come from, what characterises them, their staple ingredients and best-known dishes.',
    placeholder: 'e.g. Asia, olive oil, curry',
    filters: [{ id: 'region', label: 'Region', options: f.region }],
    card: c => `<a class="card" href="#/cuisine/${c.cuisine_id}"><small>${esc(c.region || '')}</small><b>${esc(c.name)}</b>
      <span>${esc(trim(c.description, 110))}</span><div class="meta"><span>${c.recipes} recipe${c.recipes === 1 ? '' : 's'}</span></div></a>`,
  });
});

route('cuisine', async ([id]) => {
  const c = await api('/cuisines/' + encodeURIComponent(id));
  app().innerHTML = `
    ${crumb('#/cuisines', 'World cuisines', c.region || '')}
    <h1>${esc(c.name)}</h1>
    <p class="lead">${esc(c.description || '')}</p>
    ${kv([['region', c.region], ['recipes', c.recipe_list.length]])}
    ${sections([['Characteristics', c.characteristics]])}
    ${c.common_ingredients ? `<h3>Common ingredients</h3><p>${tags(words(c.common_ingredients), 'a')}</p>` : ''}
    ${c.popular_dishes ? `<h3>Popular dishes</h3><p>${tags(words(c.popular_dishes), 'c')}</p>` : ''}
    ${c.recipe_list.length ? `<h2>${esc(c.name)} recipes</h2><div class="grid">${list(c.recipe_list, recipeCard)}</div>` : ''}`;
});
