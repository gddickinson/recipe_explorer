// Recipe scaling, US-to-metric conversion and shopping-list totals: an exact port of recipe_scaling.py (the desktop
// repo's pure Python module). scaling_engine.test.mjs checks it against tests/fixtures/scaling_fixture.json, which
// scripts/make_scaling_fixture.py writes from the Python code. Rounding is floor(x + 0.5) on both sides.
export const UNIT_ALIASES = {
  cups: 'cup', lbs: 'lb', pound: 'lb', pounds: 'lb', ounce: 'oz', ounces: 'oz',
  tablespoon: 'tbsp', tablespoons: 'tbsp', teaspoon: 'tsp', teaspoons: 'tsp', cans: 'can', sheets: 'sheet',
};
export const PLURALS = { cup: 'cups', lb: 'lbs', can: 'cans', sheet: 'sheets' };
export const METRIC = { tsp: ['ml', 4.92892], tbsp: ['ml', 14.7868], cup: ['ml', 236.588], oz: ['g', 28.3495], lb: ['g', 453.592] };
const BIG = { ml: 'L', g: 'kg' };
const FRACTIONS = [[0, ''], [1 / 8, '1/8'], [1 / 4, '1/4'], [1 / 3, '1/3'], [3 / 8, '3/8'], [1 / 2, '1/2'], [5 / 8, '5/8'],
  [2 / 3, '2/3'], [3 / 4, '3/4'], [7 / 8, '7/8'], [1, '']];
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);

export const roundTo = (x, d) => { const k = 10 ** d; return Math.floor(x * k + 0.5) / k; };
const trim = s => (s.includes('.') ? s.replace(/0+$/, '').replace(/\.$/, '') : s);
export const fmtDecimal = (x, d) => trim(roundTo(x, d).toFixed(d));

export function parseAmount(text) {
  const t = text.trim();
  let m = /^(\d+(?:\.\d+)?)$/.exec(t);
  if (m) return parseFloat(m[1]);
  m = /^(\d+)\/(\d+)$/.exec(t);
  if (m) return +m[2] ? +m[1] / +m[2] : null;
  m = /^(\d+)\s+(\d+)\/(\d+)$/.exec(t);
  if (m) return +m[3] ? +m[1] + +m[2] / +m[3] : null;
  return null;
}

export function parseQuantity(text) {
  const t = String(text ?? '').trim();
  if (!t) return null;
  const parts = t.split(/\s*(?:-|–|\bto\b)\s*/);
  if (parts.length === 2) {
    const lo = parseAmount(parts[0]), hi = parseAmount(parts[1]);
    return lo !== null && hi !== null ? [lo, hi] : null;
  }
  const v = parseAmount(t);
  return v !== null ? [v, v] : null;
}

export function formatAmount(x) {
  if (x <= 0) return '0';
  let whole = Math.floor(x + 1e-9);
  const frac = x - whole;
  let [best, label] = FRACTIONS[0];
  for (const [v, lab] of FRACTIONS.slice(1)) if (Math.abs(frac - v) < Math.abs(frac - best)) { best = v; label = lab; }
  if (Math.abs(frac - best) > 0.02) return fmtDecimal(x, 2);
  if (best === 1) whole += 1;
  if (!label) return String(whole);
  return whole ? `${whole} ${label}` : label;
}

export function normUnit(unit) {
  const u = String(unit ?? '').trim().toLowerCase();
  return has(UNIT_ALIASES, u) ? UNIT_ALIASES[u] : u;
}

export function usUnit(unit, amount) {
  const nu = normUnit(unit), raw = String(unit ?? '').trim().toLowerCase();
  if (has(PLURALS, nu) && (raw === nu || raw === PLURALS[nu])) return amount > 1 + 1e-9 ? PLURALS[nu] : nu;
  return String(unit ?? '');
}

export function metricValue(x) {
  if (x >= 100) return String(Math.floor(x / 5 + 0.5) * 5);
  if (x >= 10) return String(Math.floor(x + 0.5));
  return fmtDecimal(x, 1);
}

function metric(lo, hi, base) {
  if (hi >= 1000) {
    lo /= 1000; hi /= 1000;
    return [lo === hi ? fmtDecimal(lo, 2) : `${fmtDecimal(lo, 2)}-${fmtDecimal(hi, 2)}`, BIG[base], lo, hi];
  }
  return [lo === hi ? metricValue(lo) : `${metricValue(lo)}-${metricValue(hi)}`, base, lo, hi];
}

const us = (lo, hi, unit) => [lo === hi ? formatAmount(lo) : `${formatAmount(lo)}-${formatAmount(hi)}`, usUnit(unit, hi), lo, hi];

export function scaleItem(quantity, unit, factor = 1, toMetric = false) {
  const q = parseQuantity(quantity);
  if (q === null) return { quantity: String(quantity ?? ''), unit: String(unit ?? ''), low: null, high: null };
  const nu = normUnit(unit);
  let lo = q[0] * factor, hi = q[1] * factor, text, u;
  if (toMetric && has(METRIC, nu)) {
    const [base, f] = METRIC[nu];
    [text, u, lo, hi] = metric(lo * f, hi * f, base);
  } else {
    [text, u, lo, hi] = us(lo, hi, unit);
  }
  return { quantity: text, unit: u, low: lo, high: hi };
}

export function scaleRecipeIngredients(ingredients, from, to, toMetric = false) {
  const factor = from && to ? to / from : 1;
  return ingredients.map(ing => ({ ...ing, ...scaleItem(ing.quantity, ing.unit, factor, toMetric),
    original: { quantity: ing.quantity, unit: ing.unit } }));
}

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

export function combine(items, toMetric = false) {
  const groups = new Map();
  for (const it of items) {
    const name = String(it.name ?? ''), factor = it.factor || 1;
    const q = parseQuantity(it.quantity), nu = normUnit(it.unit);
    const key = q === null ? `${name.toLowerCase()}\u0000${nu}\u0000text:${String(it.quantity ?? '').trim().toLowerCase()}`
      : toMetric && has(METRIC, nu) ? `${name.toLowerCase()}\u0000${METRIC[nu][0]}\u0000num` : `${name.toLowerCase()}\u0000${nu}\u0000num`;
    let g = groups.get(key);
    if (!g) {
      g = { name, unit: it.unit || '', quantity: it.quantity || '', low: 0, high: 0, numeric: q !== null, recipes: [],
        base: toMetric && q !== null && has(METRIC, nu) ? METRIC[nu][0] : null };
      groups.set(key, g);
    }
    if (q !== null) {
      const f = toMetric && has(METRIC, nu) ? METRIC[nu][1] : 1;
      g.low += q[0] * factor * f;
      g.high += q[1] * factor * f;
    }
    if (it.recipe && !g.recipes.includes(it.recipe)) g.recipes.push(it.recipe);
  }
  const out = [];
  for (const g of groups.values()) {
    let text, unit, lo, hi;
    if (!g.numeric) [text, unit, lo, hi] = [String(g.quantity), String(g.unit), null, null];
    else if (g.base) [text, unit, lo, hi] = metric(g.low, g.high, g.base);
    else [text, unit, lo, hi] = us(g.low, g.high, g.unit);
    out.push({ name: g.name, quantity: text, unit, low: lo, high: hi, recipes: g.recipes });
  }
  return out.sort((a, b) => cmp(a.name.toLowerCase(), b.name.toLowerCase()) || cmp(a.unit.toLowerCase(), b.unit.toLowerCase()));
}
