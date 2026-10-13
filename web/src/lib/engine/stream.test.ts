// The browser's own simulation: generator, world, and whole runs as the page plays them.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { smdFromCounts, srmLogBayesFactor } from './checks';
import { parseConfig } from './config';
import { Rng } from './rng';
import { Run } from './run';
import { PlayerFactory } from './simulator';

const root = resolve(__dirname, '../../../..');
const cfg = parseConfig(readFileSync(resolve(root, 'config', 'simulator.toml'), 'utf8'));
const fixture = (name: string) => JSON.parse(readFileSync(resolve(root, 'fixtures', `${name}.json`), 'utf8'));

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
const variance = (xs: number[]) => {
  const m = mean(xs);
  return xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1);
};

describe('generator', () => {
  it('is reproducible from its seed', () => {
    const a = new Rng(42);
    const b = new Rng(42);
    for (let i = 0; i < 100; i++) expect(a.random()).toBe(b.random());
  });

  it.each([3, 25, 450, 1200])('Poisson(%d) has the right mean and variance', (lam) => {
    const r = new Rng(lam);
    const xs = Array.from({ length: 20_000 }, () => r.poisson(lam));
    const se = Math.sqrt(lam / xs.length);
    expect(Math.abs(mean(xs) - lam)).toBeLessThan(4 * se);
    expect(variance(xs) / lam).toBeGreaterThan(0.95);
    expect(variance(xs) / lam).toBeLessThan(1.05);
  });

  it('normal draws are standard', () => {
    const r = new Rng(7);
    const xs = Array.from({ length: 50_000 }, () => r.normal());
    expect(Math.abs(mean(xs))).toBeLessThan(0.02);
    expect(Math.abs(variance(xs) - 1)).toBeLessThan(0.03);
  });
});

describe('checks match Python', () => {
  const fx = fixture('checks');
  const close = (a: number, b: number) => Math.abs(a - b) <= 1e-9 * Math.max(Math.abs(a), Math.abs(b)) + 1e-12;
  it('always-valid split check', () => {
    for (const c of fx.srm) expect(close(srmLogBayesFactor(c.n_c, c.n_t), c.log_bf), JSON.stringify(c)).toBe(true);
  });
  it('standardised mean difference', () => {
    for (const c of fx.smd) expect(close(smdFromCounts(c.k_c, c.n_c, c.k_t, c.n_t), c.smd)).toBe(true);
  });
});

describe('simulated world', () => {
  const players = (() => {
    const r = new Rng(1);
    const f = new PlayerFactory(cfg, 0.02, 'T', r.fork(), r.fork(), r.fork());
    return Array.from({ length: 24 * 14 }, (_, h) => f.hour(h)).flat();
  })();

  it('has the calibrated baseline and the preset lift', () => {
    expect(Math.abs(mean(players.map((p) => p.p0)) - 0.22)).toBeLessThan(0.005);
    expect(Math.abs(mean(players.map((p) => p.p1 - p.p0)) - 0.02)).toBeLessThan(0.001);
  });

  it('splits players 50/50 and gives partner scores only to paid social', () => {
    expect(Math.abs(mean(players.map((p) => (p.treated ? 1 : 0))) - 0.5)).toBeLessThan(0.01);
    expect(players.every((p) => (p.channel === 1) === (p.partnerScore !== null))).toBe(true);
  });
});

describe('whole runs', () => {
  it('replays exactly from a seed', () => {
    const a = new Run(cfg, 123, 0.02);
    const b = new Run(cfg, 123, 0.02);
    a.finish();
    b.finish();
    expect(a.looks).toEqual(b.looks);
    expect(a.verdict).toBe(b.verdict);
  });

  it('waits for outcomes, then never shows a verdict before the minimum sample', () => {
    const run = new Run(cfg, 9, 0.05);
    run.finish();
    expect(run.looks[0]!.hour).toBeGreaterThan(cfg.page.start_hour);
    for (const l of run.looks.filter((x) => x.n < cfg.plan.min_players)) {
      expect(l.lo).toBe(-Infinity);
      expect(l.hi).toBe(Infinity);
    }
  });

  it('rarely gives a false verdict when the bonus does nothing (evidence 1, browser stream)', () => {
    const runs = 300;
    let wrong = 0;
    for (let s = 0; s < runs; s++) {
      const run = new Run(cfg, 10_000 + s, 0);
      run.finish();
      if (run.verdict !== 'inconclusive') wrong++; // any verdict is wrong when nothing works
    }
    // Expected about 1.3% (Python validity); 5% allowed. 300 runs: SE about 1.3 points at 5%.
    expect(wrong / runs).toBeLessThan(0.05);
  }, 120_000);

  it('the default preset reaches a verdict in about 60-90 seconds of watching', () => {
    const updates: number[] = [];
    for (let s = 0; s < 120; s++) {
      const run = new Run(cfg, 20_000 + s, 0.02);
      run.finish();
      updates.push(run.looks.length);
    }
    updates.sort((a, b) => a - b);
    const medianSeconds = updates[60]! * 2.5;
    console.log(`default preset: median ${medianSeconds} s`);
    expect(medianSeconds).toBeGreaterThanOrEqual(60);
    expect(medianSeconds).toBeLessThanOrEqual(90);
  }, 120_000);
});
