// node scaling_engine.test.mjs: the JS port must give the same results as recipe_scaling.py. The expected values are in
// tests/fixtures/scaling_fixture.json (written by scripts/make_scaling_fixture.py from the Python code). Display
// text must match exactly; numbers within a relative 1e-9.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { scaleItem, combine, parseQuantity, formatAmount } from './scaling_engine.js';

const fx = JSON.parse(readFileSync(new URL('../../tests/fixtures/scaling_fixture.json', import.meta.url), 'utf8'));
const close = (a, b, what) => {
  if (a === null || b === null) return assert.equal(a, b, what);
  assert.ok(Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b)), `${what}: ${a} vs ${b}`);
};
function same(got, want, what) {
  assert.equal(got.quantity, want.quantity, what + ' quantity');
  assert.equal(got.unit, want.unit, what + ' unit');
  close(got.low, want.low, what + ' low');
  close(got.high, want.high, what + ' high');
}
for (const { in: [q, u, f, m], out } of fx.scale) same(scaleItem(q, u, f, m), out, JSON.stringify([q, u, f, m]));
for (const { items, metric, out } of fx.combine) {
  const got = combine(items, metric);
  assert.equal(got.length, out.length);
  got.forEach((g, i) => { assert.equal(g.name, out[i].name); assert.deepEqual(g.recipes, out[i].recipes); same(g, out[i], g.name); });
}
// A few hand-checked values.
assert.deepEqual(parseQuantity('8-10'), [8, 10]);
assert.equal(parseQuantity('to taste'), null);
assert.equal(formatAmount(1.5), '1 1/2');
assert.equal(formatAmount(0.33), '1/3');
assert.equal(formatAmount(2.999), '3');
assert.deepEqual(scaleItem('1', 'cup', 2), { quantity: '2', unit: 'cups', low: 2, high: 2 });
assert.deepEqual(scaleItem('1', 'lb', 1, true), { quantity: '455', unit: 'g', low: 453.592, high: 453.592 });
console.log(`scaling_engine: ${fx.scale.length} scaling cases and ${fx.combine.length} shopping lists match Python; all ok`);
