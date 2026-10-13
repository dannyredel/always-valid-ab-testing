// Segment monitoring (port of ablab/segments.py): always-valid interval per segment level at alpha / K,
// tuned to the segment's expected share. Trustworthy when it fires; catches only large harms (notebook 05).

import type { SimConfig } from './config';
import { csMultiplier, rho2For } from './sequential';
import { diffInProportions, type Totals } from './stats';

export const SEGMENT_MIN_PLAYERS = 300;

export interface SegmentLevel {
  dimension: 'Country tier' | 'Device' | 'Channel';
  key: 'tier' | 'device' | 'channel';
  index: number;
  name: string;
  share: number;
}

export function segmentLevels(cfg: SimConfig): SegmentLevel[] {
  const c = cfg.covariates;
  const iphone = c.tier.p.reduce((s, p, i) => s + p * c.device.p_iphone_by_tier[i]!, 0);
  return [
    ...c.tier.levels.map((name, i) => ({ dimension: 'Country tier' as const, key: 'tier' as const, index: i, name, share: c.tier.p[i]! })),
    { dimension: 'Device', key: 'device', index: 0, name: c.device.levels[0]!, share: iphone },
    { dimension: 'Device', key: 'device', index: 1, name: c.device.levels[1]!, share: 1 - iphone },
    ...c.channel.levels.map((name, i) => ({ dimension: 'Channel' as const, key: 'channel' as const, index: i, name, share: c.channel.p[i]! })),
  ];
}

export function segmentInterval(t: Totals, share: number, k: number, alpha: number, nStar: number): [number, number] {
  const { d, se } = diffInProportions(t);
  const a = alpha / k;
  const half = se * csMultiplier(t.n_t + t.n_c, rho2For(nStar * share, a), a);
  return [d - half, d + half];
}
