// Static-site data layer: answers api(path) calls from the JSON files exported by scripts/build_static.py.
// Plain paths map to files (api/recipes/3.json). List endpoints with a query string and /search are filtered here from
// the exported full lists with the same rules as web/search.py (search_engine.js); /recipes/<id>?servings=&units= and
// /shopping are computed with scaling_engine.js (the port of recipe_scaling.py). Writes need the local server.
import { KINDS, filterRows } from './search_engine.js';
import { scaleRecipeIngredients, combine } from './scaling_engine.js';

const files = new Map();
async function file(rel) {
  if (!files.has(rel)) {
    files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  }
  return files.get(rel);
}

const servingsParam = (v, dflt) => { const n = /^\d+$/.test(String(v ?? '').trim()) ? parseInt(v, 10) : NaN; return n >= 1 && n <= 1000 ? n : dflt; };
const originals = r => r.ingredients.map(i => ({ ...i, quantity: i.original.quantity, unit: i.original.unit }));

async function recipe(id, q) {
  const r = await file('recipes/' + id);
  const base = r.servings || 1, shown = servingsParam(q.servings, base), metric = q.units === 'metric';
  return { ...r, ingredients: scaleRecipeIngredients(originals(r), base, shown, metric), servings_shown: shown, units: metric ? 'metric' : 'us' };
}

async function shopping(q) {
  const metric = q.units === 'metric', chosen = [], items = [];
  for (const part of String(q.r || '').split(',')) {
    const [rid, srv] = part.trim().split(':');
    if (!/^\d+$/.test(rid || '')) continue;
    let rec;
    try { rec = await file('recipes/' + parseInt(rid, 10)); } catch { continue; }
    const base = rec.servings || 1, s = /^\d+$/.test((srv || '').trim()) && +srv > 0 ? +srv : null, shown = s || base;
    const raw = originals(rec);
    chosen.push({ recipe_id: rec.recipe_id, name: rec.name, servings: shown, base_servings: base,
      ingredients: scaleRecipeIngredients(raw, base, shown, metric) });
    for (const i of raw) items.push({ name: i.name, quantity: i.quantity, unit: i.unit, factor: shown / base, recipe: rec.name });
  }
  return { recipes: chosen, items: combine(items, metric), units: metric ? 'metric' : 'us' };
}

export async function staticApi(path, body) {
  const [p, qs] = path.split('?');
  const q = Object.fromEntries(new URLSearchParams(qs || ''));
  const clean = p.replace(/^\/+|\/+$/g, '');
  if (body) throw new Error('Adding, editing and rating recipes needs the full app (Python server).');
  if (clean === 'search') {
    const words = (q.q || '').trim();
    const lists = await Promise.all(KINDS.map(k => words ? file(k) : []));
    return Object.fromEntries(KINDS.map((k, i) => [k, words ? filterRows(k, lists[i], { q: words }) : []]));
  }
  if (clean === 'shopping') return shopping(q);
  const m = /^recipes\/(\d+)$/.exec(clean);
  if (m) return recipe(m[1], q);
  if (KINDS.includes(clean)) return filterRows(clean, await file(clean), q);
  return file(clean);
}
