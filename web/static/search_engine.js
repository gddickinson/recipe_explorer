// Search and filter rules for list pages: an exact mirror of web/search.py, used by static_api.js to answer
// /api/<kind>?... and /api/search?q=... on the static site from the exported full lists.
export const SPECS = {
  recipes: { text: ['name', 'description', 'instructions', 'cuisine', 'category', 'dietary_tags', 'ingredients', 'equipment'],
    exact: { cuisine: 'cuisine', category: 'category', difficulty: 'difficulty' }, max: { max_time: 'total_time' },
    member: { ingredient: 'ingredients', equipment: 'equipment' }, terms: { diet: 'dietary_tags' }, flag: {}, id: 'recipe_id' },
  ingredients: { text: ['name', 'category', 'description', 'substitutes', 'nutritional_notes', 'allergen_info', 'season'],
    exact: { category: 'category' }, max: {}, member: {}, terms: {}, flag: {}, id: 'ingredient_id' },
  equipment: { text: ['name', 'category', 'description', 'substitutes', 'care_tips'],
    exact: { category: 'category' }, max: {}, member: {}, terms: {}, flag: { essential: 'essential' }, id: 'equipment_id' },
  cuisines: { text: ['name', 'region', 'description', 'characteristics', 'common_ingredients', 'popular_dishes'],
    exact: { region: 'region' }, max: {}, member: {}, terms: {}, flag: {}, id: 'cuisine_id' },
};
export const KINDS = Object.keys(SPECS);

// Python's str(): None -> 'None', True -> 'True', numbers as written. Only used for exact comparisons.
const pyStr = v => v === null || v === undefined ? 'None' : v === true ? 'True' : v === false ? 'False' : String(v);
const has = v => v !== undefined && v !== null && v !== '';
// Python float(): numbers and numeric strings (surrounding spaces allowed); anything else -> null.
const num = v => {
  if (typeof v === 'number') return v;
  if (typeof v !== 'string' || !/^\s*[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?\s*$/.test(v)) return null;
  return parseFloat(v);
};
export const terms = text => String(text ?? '').split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
const text = (r, fields) => fields.map(f => Array.isArray(r[f]) ? r[f].map(String).join(' ') : String(r[f] ?? '')).join(' ').toLowerCase();

function keep(spec, r, params, words) {
  for (const [p, col] of Object.entries(spec.exact)) if (has(params[p]) && pyStr(r[col]) !== String(params[p])) return false;
  for (const [p, col] of Object.entries(spec.max)) {
    const limit = num(params[p]);
    if (limit !== null && (num(r[col]) === null || num(r[col]) > limit)) return false;
  }
  for (const [p, col] of Object.entries(spec.member))
    if (params[p] && !(r[col] || []).map(x => String(x).toLowerCase()).includes(String(params[p]).toLowerCase())) return false;
  for (const [p, col] of Object.entries(spec.terms)) if (params[p] && !terms(r[col]).includes(String(params[p]).toLowerCase())) return false;
  for (const [p, col] of Object.entries(spec.flag)) {
    const v = String(params[p] || '');
    if ((v === '1' && !r[col]) || (v === '0' && r[col])) return false;
  }
  if (words.length) { const t = text(r, spec.text); return words.every(w => t.includes(w)); }
  return true;
}

export function filterRows(kind, rows, params = {}) {
  const spec = SPECS[kind];
  const words = String(params.q || '').toLowerCase().split(/\s+/).filter(Boolean);
  return rows.filter(r => keep(spec, r, params, words));
}
