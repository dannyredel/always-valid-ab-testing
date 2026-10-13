// Reads config/simulator.toml, the same file the Python engine uses.

import { parse } from 'smol-toml';

export interface Plan {
  alpha: number;
  power: number;
  bonus_usd: number;
  p_reach_level10: number;
  value_per_activation_usd: number;
  cupac_r2: number;
  outcome_delay_h: number;
  min_players: number;
  max_players: number;
  n_star: number;
}

export interface Page {
  start_hour: number;
  hours_per_update: number;
  seconds_per_update: [number, number];
}

interface Levels {
  levels: string[];
}

export interface World {
  experiment: { key: string; days: number; baseline_rate: number };
  arrivals: {
    per_hour: number;
    weekday_shape: number[];
    hour_shape: {
      night_weight: number;
      night_level: number;
      night_amp: number;
      night_peak_hour: number;
      bumps: [number, number, number][];
    };
  };
  covariates: {
    evening_hours: [number, number];
    tier: Levels & { p: number[] };
    device: Levels & { p_iphone_by_tier: number[] };
    channel: Levels & { p: number[] };
  };
  baseline_logit: { tier: number[]; device: number[]; channel: number[]; evening: number; engagement: number };
  signals: {
    games_30d: { log_mean: number; loading: number };
    click_to_install_s: { log_median: number; loading: number; noise_sd: number };
    partner_score: { loading: number; noise_sd: number; channel: string };
  };
  lift_multiplier: { tier: number[]; channel: number[] };
  journey: {
    p_start_if_not_activated: number;
    start_median_min: number;
    start_sigma: number;
    milestone_median_h: number;
    milestone_sigma: number;
    treatment_speedup: number;
    p_late_finisher: number;
  };
  calibration: { intercept: number; multiplier_mean: number };
}

export interface SimConfig extends World {
  presets: { names: string[]; lifts: number[]; default: string };
  plan: Plan;
  page: Page;
}

export function parseConfig(toml: string): SimConfig {
  return parse(toml) as unknown as SimConfig;
}

/** Lift at which the Starter Bonus pays for itself (port of ablab.power.break_even_lift). */
export function breakEvenLift(cfg: SimConfig): number {
  const p = cfg.plan;
  const extra = (1 - p.p_reach_level10) * p.bonus_usd;
  return (cfg.experiment.baseline_rate * extra) / (p.value_per_activation_usd - extra);
}
