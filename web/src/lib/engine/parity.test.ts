// Validity evidence 4: the browser port returns the same numbers as the Python reference
// (fixtures written by `python -m scripts.make_fixtures`).

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { assignmentU } from './assign';
import { parseConfig } from './config';
import { AlwaysValidState, confidenceSequence, csMultiplier, pValueAtLook, rho2For, verdict } from './sequential';
import { diffInProportions, naiveInterval, naivePValue } from './stats';

const root = resolve(__dirname, '../../../..');
const fixture = (name: string) => JSON.parse(readFileSync(resolve(root, 'fixtures', `${name}.json`), 'utf8'));

const REL = 1e-9;
function expectClose(actual: number, expected: number, label = '') {
  const tol = REL * Math.max(Math.abs(actual), Math.abs(expected)) + 1e-15;
  expect(Math.abs(actual - expected), `${label}: ${actual} vs ${expected}`).toBeLessThanOrEqual(tol);
}

describe('assignment hash', () => {
  const fx = fixture('assign');
  it(`matches Python exactly on ${fx.cases.length} ids (incl. empty and non-ASCII)`, () => {
    for (const c of fx.cases) expect(assignmentU(c.player_id, fx.key)).toBe(c.u);
  });
});

describe('usual interval', () => {
  const fx = fixture('stats');
  it(`matches Python on ${fx.cases.length} cases`, () => {
    for (const c of fx.cases) {
      const { d, se, z } = diffInProportions(c);
      const [lo, hi] = naiveInterval(c);
      expectClose(d, c.d, 'd');
      expectClose(se, c.se, 'se');
      expectClose(z, c.z, 'z');
      expectClose(lo, c.lo, 'lo');
      expectClose(hi, c.hi, 'hi');
      expectClose(naivePValue(c), c.p, 'p');
    }
  });
});

describe('always-valid interval', () => {
  const fx = fixture('sequential');

  it('uses the same tuning', () => {
    expectClose(rho2For(fx.n_star, fx.alpha), fx.rho2, 'rho2');
    for (const m of fx.multiplier) expectClose(csMultiplier(m.n, fx.rho2, fx.alpha), m.c, `c(${m.n})`);
  });

  for (const path of fx.paths) {
    it(`matches Python look by look, true lift ${path.lift}`, () => {
      const state = new AlwaysValidState(fx.rho2, fx.alpha, fx.min_players);
      for (const look of path.looks) {
        const { d, se, z } = diffInProportions(look);
        const n = look.n_t + look.n_c;
        const [lo, hi] = confidenceSequence(d, se, n, fx.rho2, fx.alpha);
        expectClose(lo, look.lo, 'lo');
        expectClose(hi, look.hi, 'hi');
        expectClose(pValueAtLook(z, n, fx.rho2), look.p_at_look, 'p_at_look');

        const s = state.update(d, se, z, n);
        expectClose(s.p, look.p_always_valid, 'p_always_valid');
        if (look.lo_intersected === null) expect(s.lo).toBe(-Infinity);
        else expectClose(s.lo, look.lo_intersected, 'lo_intersected');
        if (look.hi_intersected === null) expect(s.hi).toBe(Infinity);
        else expectClose(s.hi, look.hi_intersected, 'hi_intersected');
        expect(verdict(s.lo, s.hi, n, fx.min_players, fx.max_players)).toBe(look.verdict);
      }
    });
  }

  it('covers all four verdicts', () => {
    const seen = new Set(fx.paths.flatMap((p: { looks: { verdict: string }[] }) => p.looks.map((l) => l.verdict)));
    expect([...seen].sort()).toEqual(['dont_ship', 'inconclusive', 'keep_collecting', 'ship']);
  });
});

describe('config', () => {
  it('reads the same TOML as Python', () => {
    const cfg = parseConfig(readFileSync(resolve(root, 'config', 'simulator.toml'), 'utf8'));
    expect(cfg.plan.n_star).toBe(30000);
    expect(cfg.plan.min_players).toBe(1000);
    expect(cfg.page.hours_per_update).toBe(1.75);
    expect(cfg.presets.default).toBe('Small real effect');
  });
});
