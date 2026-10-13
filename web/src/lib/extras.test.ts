// Milestone 5: scenarios, the peeking counter, parallel worlds, and the pre-computed runs.

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { murmur3_32 } from './engine/assign';
import { parseConfig } from './engine/config';
import { Rng } from './engine/rng';
import { Run } from './engine/run';
import { PlayerFactory } from './engine/simulator';
import { configFor, custom, fromUrl, presets, toUrl } from './scenario';
import { runWorlds } from './worlds';

const tomlText = readFileSync(resolve(__dirname, '../../../config/simulator.toml'), 'utf8');
const cupacText = readFileSync(resolve(__dirname, '../../../config/cupac.json'), 'utf8');
const cfg = parseConfig(tomlText);
const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;

describe('scenarios', () => {
  it('round-trip through the URL', () => {
    for (const s of [...presets(cfg), custom(0.035, 0.3, 600)]) {
      const url = new URL('http://x/?seed=1');
      toUrl(url, s);
      const back = fromUrl(cfg, url.searchParams);
      expect(back.slug).toBe(s.slug);
      expect(back.lift).toBeCloseTo(s.lift, 6);
      expect(back.baseline).toBeCloseTo(s.baseline, 6);
      expect(back.perHour).toBe(s.perHour);
    }
  });

  it('falls back to the default preset on a broken link', () => {
    expect(fromUrl(cfg, new URLSearchParams('preset=custom&lift=abc')).name).toBe(cfg.presets.default);
  });

  it.each([0.12, 0.3])('a custom baseline of %f is what players actually get', (baseline) => {
    const c = configFor(cfg, custom(0.02, baseline, 300));
    const r = new Rng(3);
    const f = new PlayerFactory(c, 0.02, 'B', r.fork(), r.fork(), r.fork());
    const players = Array.from({ length: 24 * 7 }, (_, h) => f.hour(h)).flat();
    expect(Math.abs(mean(players.map((p) => p.p0)) - baseline)).toBeLessThan(0.006);
  });
});

describe('peeking counter and coverage', () => {
  it('marks the first look, from the minimum sample, where the usual interval excluded zero', () => {
    for (let s = 0; s < 30; s++) {
      const run = new Run(cfg, 900 + s, 0, { stopAtVerdict: false });
      run.finish();
      const first = run.looks.find((l) => l.n >= cfg.plan.min_players && (l.naiveLo > 0 || l.naiveHi < 0));
      expect(run.peek?.n ?? null).toBe(first?.n ?? null);
    }
  });

  it('keeps going to the maximum when asked, and a verdict, once reached, stands', () => {
    const run = new Run(cfg, 5, 0.05, { stopAtVerdict: false });
    run.finish();
    expect(run.n).toBe(cfg.plan.max_players);
    expect(run.verdict).toBe('ship');
    expect(run.verdictAt!).toBeLessThan(cfg.plan.max_players);
  });
});

describe('parallel worlds', () => {
  it('the usual interval, peeked at, is wrong far more often than the always-valid one', async () => {
    const r = await runWorlds(cfg, 0, 120, 1, () => {});
    expect(r.done).toBe(120);
    expect(r.alwaysValid.wrong / r.done).toBeLessThan(0.06);
    expect(r.usual.wrong / r.done).toBeGreaterThan(0.15);
    expect(r.alwaysValid.covered / r.done).toBeGreaterThan(0.93);
  }, 120_000);
});

describe('pre-computed runs', () => {
  it('were built from the current config (else: npm run precompute)', () => {
    const pre = JSON.parse(readFileSync(resolve(__dirname, '../../public/runs.json'), 'utf8'));
    expect(pre.configHash).toBe(murmur3_32(new TextEncoder().encode(tomlText + cupacText)));
    expect(Object.keys(pre.presets).sort()).toEqual(['large', 'none', 'small']);
    expect(pre.presets.small).toHaveLength(1000);
  });
});
