// The known-truth simulator, port of ablab/simulator.py: same model, same config, generated hour by
// hour so the page can stream it. (Random draws differ from Python; the statistics are what must match.)

import { assignmentU, isTreated } from './assign';
import { Rng as RngCtor, type Rng } from './rng';
import type { World } from './config';

export interface Player {
  id: string;
  signupHour: number;
  tier: number; // 0..2
  device: number; // 0 iPhone, 1 Android
  channel: number; // 0 Organic, 1 Paid social, 2 Referral
  evening: boolean;
  gamesInstalled: number;
  clickToInstallS: number;
  partnerScore: number | null;
  treated: boolean;
  p0: number;
  p1: number;
  activated: boolean;
}

const expit = (x: number) => 1 / (1 + Math.exp(-x));

export function hourShape(w: World): number[] {
  const hs = w.arrivals.hour_shape;
  const s = Array.from({ length: 24 }, (_, h) => {
    let v = hs.night_weight * (hs.night_level + hs.night_amp * Math.cos((2 * Math.PI * (h - hs.night_peak_hour)) / 24));
    for (const [height, centre, width] of hs.bumps) v += height * Math.exp(-(((h - centre) / width) ** 2));
    return v;
  });
  const mean = s.reduce((a, b) => a + b, 0) / 24;
  return s.map((v) => v / mean);
}

export function dayShape(w: World): number[] {
  const d = w.arrivals.weekday_shape;
  const mean = d.reduce((a, b) => a + b, 0) / d.length;
  return d.map((v) => v / mean);
}

/** Generates the players who sign up in each experiment hour. */
export class PlayerFactory {
  private readonly hours: number[];
  private readonly days: number[];
  private readonly paidSocial: number;
  private count = 0;

  constructor(
    private readonly w: World,
    private readonly lift: number,
    private readonly idPrefix: string,
    private readonly arrivals: Rng,
    private readonly covariates: Rng,
    private readonly outcomes: Rng,
  ) {
    this.hours = hourShape(w);
    this.days = dayShape(w);
    this.paidSocial = w.covariates.channel.levels.indexOf(w.signals.partner_score.channel);
  }

  expectedArrivals(hour: number): number {
    return this.w.arrivals.per_hour * this.hours[hour % 24]! * this.days[Math.floor(hour / 24) % 7]!;
  }

  hour(hour: number): Player[] {
    const n = this.arrivals.poisson(this.expectedArrivals(hour));
    const out: Player[] = [];
    for (let i = 0; i < n; i++) out.push(this.player(hour));
    return out;
  }

  private player(signupHour: number): Player {
    const { w, covariates: r } = this;
    const c = w.covariates;
    const b = w.baseline_logit;
    const sg = w.signals;
    const tier = r.choice(c.tier.p);
    const device = r.random() < c.device.p_iphone_by_tier[tier]! ? 0 : 1;
    const channel = r.choice(c.channel.p);
    const hod = signupHour % 24;
    const evening = hod >= c.evening_hours[0] && hod < c.evening_hours[1];
    const u = r.normal(); // latent engagement
    const gamesInstalled = r.poisson(Math.exp(sg.games_30d.log_mean + sg.games_30d.loading * u));
    const k = sg.click_to_install_s;
    const clickToInstallS = Math.exp(k.log_median - k.loading * u + k.noise_sd * r.normal());
    const ps = sg.partner_score;
    const partnerScore = channel === this.paidSocial ? expit(ps.loading * u + ps.noise_sd * r.normal()) : null;

    const eta = b.tier[tier]! + b.device[device]! + b.channel[channel]! + (evening ? b.evening : 0) + b.engagement * u;
    const p0 = expit(w.calibration.intercept + eta);
    const m = w.lift_multiplier;
    const tau = (this.lift * m.tier[tier]! * m.channel[channel]!) / w.calibration.multiplier_mean;
    const p1 = Math.min(1, Math.max(0, p0 + tau));

    const id = `${this.idPrefix}-${(this.count++).toString().padStart(6, '0')}`;
    const treated = isTreated(assignmentU(id, w.experiment.key));
    const activated = this.outcomes.random() < (treated ? p1 : p0);
    return { id, signupHour, tier, device, channel, evening, gamesInstalled, clickToInstallS, partnerScore,
      treated, p0, p1, activated };
  }
}

/**
 * Intercept that makes the average control activation equal `baseline` (port of ablab calibrate()),
 * on a reference sample of players. Used when a visitor changes the baseline slider.
 */
export function calibrateIntercept(w: World, baseline: number, n = 20_000, seed = 1): number {
  const r = new RngCtor(seed);
  const hours = hourShape(w);
  const days = dayShape(w);
  const weights = days.flatMap((d) => hours.map((h) => (d * h) / (24 * 7)));
  const c = w.covariates;
  const b = w.baseline_logit;
  const eta: number[] = [];
  for (let i = 0; i < n; i++) {
    const how = r.choice(weights);
    const hod = how % 24;
    const tier = r.choice(c.tier.p);
    const device = r.random() < c.device.p_iphone_by_tier[tier]! ? 0 : 1;
    const channel = r.choice(c.channel.p);
    const evening = hod >= c.evening_hours[0] && hod < c.evening_hours[1];
    eta.push(b.tier[tier]! + b.device[device]! + b.channel[channel]! + (evening ? b.evening : 0) + b.engagement * r.normal());
  }
  const mean = (b0: number) => eta.reduce((s, e) => s + expit(b0 + e), 0) / n;
  let lo = -8;
  let hi = 8;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (mean(mid) < baseline) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}
