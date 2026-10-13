// Milestone 9 parity: CUPAC scoring, adjusted/value intervals, segments and the guardrail match Python.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { parseConfig } from './config';
import { adjusted, CUPAC, score } from './cupac';
import { extraCost, finalVerdict, light } from './guardrail';
import { segmentInterval, segmentLevels } from './segments';
import { confidenceSequence, rho2For } from './sequential';
import { diffInMeans } from './stats';

const root = resolve(__dirname, '../../../..');
const fx = JSON.parse(readFileSync(resolve(root, 'fixtures', 'm9.json'), 'utf8'));
const cfg = parseConfig(readFileSync(resolve(root, 'config', 'simulator.toml'), 'utf8'));
const close = (a: number, b: number, rel = 1e-9) => Math.abs(a - b) <= rel * Math.max(Math.abs(a), Math.abs(b)) + 1e-12;

describe('CUPAC', () => {
  it('uses the stored model', () => {
    expect(CUPAC.weights).toEqual(fx.cupac.weights);
    expect(CUPAC.theta).toBe(fx.cupac.theta);
  });
  it(`scores ${fx.score_cases.length} players like Python`, () => {
    for (const c of fx.score_cases) {
      const p = { evening: c.evening, gamesInstalled: c.games_30d, clickToInstallS: c.click_to_install_s,
        partnerScore: c.partner_score, tier: c.tier, device: c.device, channel: c.channel };
      const x = score(p);
      expect(close(x, c.x), `x ${x} vs ${c.x}`).toBe(true);
      expect(close(adjusted(c.activated ? 1 : 0, x), c.y_adj)).toBe(true);
    }
  });
});

describe('intervals on means (CUPAC outcome, value per player)', () => {
  it(`match Python on ${fx.means.length} cases, with the guardrail light`, () => {
    const rho2 = rho2For(cfg.plan.n_star, cfg.plan.alpha);
    for (const c of fx.means) {
      const { d, se } = diffInMeans(c);
      expect(close(d, c.d)).toBe(true);
      expect(close(se, c.se)).toBe(true);
      const [lo, hi] = confidenceSequence(d, se, c.n_t + c.n_c, rho2, cfg.plan.alpha);
      expect(close(lo, c.lo) && close(hi, c.hi)).toBe(true);
      expect(light(lo, hi)).toBe(c.light);
    }
  });
});

describe('segments', () => {
  it('have the same levels and shares', () => {
    const lv = segmentLevels(cfg);
    expect(lv.map((l) => [l.dimension, l.name])).toEqual(fx.segments.levels.map((l: [string, string, number]) => [l[0], l[1]]));
    lv.forEach((l, i) => expect(close(l.share, fx.segments.levels[i][2])).toBe(true));
  });
  it(`give the same widened intervals on ${fx.segments.cases.length} cases`, () => {
    for (const c of fx.segments.cases) {
      const [lo, hi] = segmentInterval(c, c.share, fx.segments.k, cfg.plan.alpha, cfg.plan.n_star);
      expect(close(lo, c.lo) && close(hi, c.hi)).toBe(true);
    }
  });
});

describe('guardrail', () => {
  it('has the same expected early-payout cost', () => expect(close(extraCost(cfg.plan), fx.extra_cost)).toBe(true));
  it('blocks a ship only when red', () => {
    expect(finalVerdict('ship', 'red')).toBe('doesnt_pay');
    expect(finalVerdict('ship', 'grey')).toBe('ship');
    expect(finalVerdict('keep_collecting', 'red')).toBe('keep_collecting');
  });
});

describe('value per player comes from the lift, so everything agrees', () => {
  it('net value = value of extra players − cost of paying early, at every look', async () => {
    const { Run } = await import('./run');
    const { valueFromLift } = await import('./guardrail');
    const run = new Run(cfg, 31, 0.02);
    run.finish();
    const c = extraCost(cfg.plan);
    const pC = run.control.activated / run.control.n;
    const last = run.looks.at(-1)!;
    const V = cfg.plan.value_per_activation_usd;
    expect(close(last.valD, V * last.d - c * (pC + last.d), 1e-9)).toBe(true);
    // 'pays' is exactly 'the lift is shown above break-even'
    const breakEven = (c * pC) / (V - c);
    expect(last.pays === 'green').toBe(last.lo > breakEven);
    expect(last.pays === 'red').toBe(last.hi < breakEven);
    expect(close(valueFromLift(breakEven, pC, cfg.plan), 0, 1e-9) || Math.abs(valueFromLift(breakEven, pC, cfg.plan)) < 1e-12).toBe(true);
  });
});
