// Pre-computes 1,000 runs per preset with the same engine the page uses, for "your run vs all runs".
//   npm run precompute      (re-run whenever config/simulator.toml changes; a test checks the hash)

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { murmur3_32 } from '../src/lib/engine/assign';
import { parseConfig } from '../src/lib/engine/config';
import { Run } from '../src/lib/engine/run';
import { presets } from '../src/lib/scenario';

const RUNS = 1000;
const FIRST_SEED = 500_000;
const tomlText = readFileSync(resolve(import.meta.dirname, '../../config/simulator.toml'), 'utf8');
const cfg = parseConfig(tomlText);
const cupacText = readFileSync(resolve(import.meta.dirname, '../../config/cupac.json'), 'utf8');

const out: Record<string, { verdict: string; n: number; updates: number }[]> = {};
for (const p of presets(cfg)) {
  const t0 = Date.now();
  out[p.slug] = [];
  for (let i = 0; i < RUNS; i++) {
    const run = new Run(cfg, FIRST_SEED + i, p.lift);
    run.finish();
    out[p.slug]!.push({ verdict: run.verdict, n: run.verdictAt ?? run.n, updates: run.looks.length });
  }
  console.log(`${p.name}: ${RUNS} runs in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}

const file = resolve(import.meta.dirname, '../public/runs.json');
writeFileSync(file, JSON.stringify({ configHash: murmur3_32(new TextEncoder().encode(tomlText + cupacText)), runs: RUNS, firstSeed: FIRST_SEED, presets: out }));
console.log(`wrote ${file}`);
