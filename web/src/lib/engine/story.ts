// One player's journey, for the story shown on tap. Same model as ablab/simulator.py (journey section).
// Generated on demand from the player's ID, so tapping the same player always tells the same story.
// The verdict never uses these times: only whether level 5 was reached within the window.

import { murmur3_32 } from './assign';
import type { SimConfig } from './config';
import { Rng } from './rng';
import type { Player } from './simulator';

export interface Journey {
  signupMinute: number; // minute within the sign-up hour
  startedAfterH: number | null; // hours from sign-up to first game, null if never started
  levelFiveAfterH: number | null; // hours from sign-up to level 5, null if never
  inWindow: boolean; // reached level 5 within the outcome window (= activated)
}

export function journey(p: Player, cfg: SimConfig): Journey {
  const j = cfg.journey;
  const window = cfg.plan.outcome_delay_h;
  const r = new Rng(murmur3_32(new TextEncoder().encode(`${p.id}:story`)));
  const lognormal = (median: number, sigma: number) => Math.exp(Math.log(median) + sigma * r.normal());

  const signupMinute = Math.floor(r.random() * 60);
  const started = p.activated || r.random() < j.p_start_if_not_activated;
  let startH = lognormal(j.start_median_min, j.start_sigma) / 60;
  // an activated player must start inside the window (a later start is about 1 in 50 million)
  for (let i = 0; i < 1000 && p.activated && startH >= window - 1; i++) startH = lognormal(j.start_median_min, j.start_sigma) / 60;
  if (!started) return { signupMinute, startedAfterH: null, levelFiveAfterH: null, inWindow: false };

  if (p.activated) {
    const median = j.milestone_median_h * (p.treated ? j.treatment_speedup : 1);
    let t = lognormal(median, j.milestone_sigma);
    for (let i = 0; i < 1000 && startH + t >= window; i++) t = lognormal(median, j.milestone_sigma);
    return { signupMinute, startedAfterH: startH, levelFiveAfterH: Math.min(startH + t, window - 0.01), inWindow: true };
  }
  const late = r.random() < j.p_late_finisher;
  const levelFiveAfterH = late ? window - 24 * Math.log(1 - r.random()) : null; // exponential, mean 24 h
  return { signupMinute, startedAfterH: startH, levelFiveAfterH, inWindow: false };
}
