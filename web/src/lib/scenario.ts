// What a run simulates: one of the three presets, or custom values from the sliders. Kept in the URL.

import type { SimConfig } from './engine/config';
import { calibrateIntercept } from './engine/simulator';

export const SLUGS = ['none', 'small', 'large'] as const;

export interface Scenario {
  slug: (typeof SLUGS)[number] | 'custom';
  name: string;
  lift: number; // true average lift, probability points
  baseline: number; // control activation
  perHour: number; // sign-ups per hour
}

export const SLIDERS = {
  lift: { min: -0.02, max: 0.06, step: 0.005 },
  baseline: { min: 0.1, max: 0.4, step: 0.01 },
  perHour: { min: 100, max: 1000, step: 50 },
};

export function presets(cfg: SimConfig): Scenario[] {
  return cfg.presets.names.map((name, i) => ({
    slug: SLUGS[i]!,
    name,
    lift: cfg.presets.lifts[i]!,
    baseline: cfg.experiment.baseline_rate,
    perHour: cfg.arrivals.per_hour,
  }));
}

const clamp = (v: number, { min, max }: { min: number; max: number }) => Math.min(max, Math.max(min, v));

export function fromUrl(cfg: SimConfig, q: URLSearchParams): Scenario {
  const all = presets(cfg);
  const preset = all.find((p) => p.slug === q.get('preset'));
  if (preset) return preset;
  const num = (k: string) => (q.get(k) === null ? NaN : Number(q.get(k)));
  const [lift, base, traffic] = [num('lift'), num('base'), num('traffic')];
  if (q.get('preset') === 'custom' && [lift, base, traffic].every(Number.isFinite)) {
    return custom(lift / 100, base / 100, traffic);
  }
  return all.find((p) => p.name === cfg.presets.default)!;
}

export function custom(lift: number, baseline: number, perHour: number): Scenario {
  return {
    slug: 'custom',
    name: 'Custom',
    lift: clamp(lift, SLIDERS.lift),
    baseline: clamp(baseline, SLIDERS.baseline),
    perHour: clamp(perHour, SLIDERS.perHour),
  };
}

export function toUrl(url: URL, s: Scenario): void {
  url.searchParams.set('preset', s.slug);
  for (const k of ['lift', 'base', 'traffic']) url.searchParams.delete(k);
  if (s.slug === 'custom') {
    url.searchParams.set('lift', (s.lift * 100).toFixed(1));
    url.searchParams.set('base', (s.baseline * 100).toFixed(0));
    url.searchParams.set('traffic', String(s.perHour));
  }
}

/** The config a scenario runs with. A custom baseline recalibrates the intercept. */
export function configFor(cfg: SimConfig, s: Scenario): SimConfig {
  if (s.baseline === cfg.experiment.baseline_rate && s.perHour === cfg.arrivals.per_hour) return cfg;
  const out: SimConfig = {
    ...cfg,
    experiment: { ...cfg.experiment, baseline_rate: s.baseline },
    arrivals: { ...cfg.arrivals, per_hour: s.perHour },
  };
  if (s.baseline !== cfg.experiment.baseline_rate) {
    out.calibration = { ...cfg.calibration, intercept: calibrateIntercept(cfg, s.baseline) };
  }
  return out;
}
