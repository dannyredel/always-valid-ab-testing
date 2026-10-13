// CUPAC (port of ablab/cupac.py): logistic weights from config/cupac.json, trained on an earlier cohort.
// Each player's predicted activation becomes the covariate of a CUPED adjustment, theta and mu fixed.

import model from '../../../../config/cupac.json';

export interface CupacModel {
  columns: string[];
  intercept: number;
  weights: number[];
  theta: number;
  mu: number;
}

export interface CupacFeatures {
  evening: boolean;
  gamesInstalled: number;
  clickToInstallS: number;
  partnerScore: number | null;
  tier: number;
  device: number;
  channel: number;
}

export const CUPAC: CupacModel = model;

/** Same columns, same order as ablab.cupac.COLUMNS. */
export function design(p: CupacFeatures): number[] {
  return [
    p.evening ? 1 : 0,
    Math.log1p(p.gamesInstalled),
    Math.log(p.clickToInstallS),
    p.partnerScore ?? 0,
    p.partnerScore === null ? 0 : 1,
    p.tier === 1 ? 1 : 0,
    p.tier === 2 ? 1 : 0,
    p.device === 1 ? 1 : 0,
    p.channel === 1 ? 1 : 0,
    p.channel === 2 ? 1 : 0,
  ];
}

export function score(p: CupacFeatures, m: CupacModel = CUPAC): number {
  const x = design(p);
  let eta = m.intercept;
  for (let i = 0; i < x.length; i++) eta += m.weights[i]! * x[i]!;
  return 1 / (1 + Math.exp(-eta));
}

export function adjusted(y: number, x: number, m: CupacModel = CUPAC): number {
  return y - m.theta * (x - m.mu);
}
