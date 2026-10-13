// The usual fixed-horizon analysis from running totals, port of ablab/stats.py.

import erfc from '@stdlib/math-base-special-erfc';

export const Z95 = 1.959963984540054;

export interface Totals {
  s_t: number; // activated, Starter Bonus
  n_t: number; // players, Starter Bonus
  s_c: number; // activated, standard rewards
  n_c: number; // players, standard rewards
}

export interface Diff {
  d: number;  // estimated lift
  se: number; // unpooled standard error
  z: number;
}

export function diffInProportions({ s_t, n_t, s_c, n_c }: Totals): Diff {
  const pT = s_t / n_t;
  const pC = s_c / n_c;
  const d = pT - pC;
  const se = Math.sqrt((pT * (1 - pT)) / n_t + (pC * (1 - pC)) / n_c);
  return { d, se, z: se > 0 ? d / se : 0 };
}

export function naiveInterval(t: Totals, zCrit = Z95): [number, number] {
  const { d, se } = diffInProportions(t);
  return [d - zCrit * se, d + zCrit * se];
}

/** Two-sided p-value 2 * P(Z > |z|) = erfc(|z| / sqrt 2). */
export function naivePValue(t: Totals): number {
  return erfc(Math.abs(diffInProportions(t).z) / Math.SQRT2);
}

export interface MeanSums {
  n_t: number;
  s_t: number; // sum
  ss_t: number; // sum of squares
  n_c: number;
  s_c: number;
  ss_c: number;
}

/** Difference in means and Welch standard error from running sums (port of ablab.stats.diff_in_means). */
export function diffInMeans({ n_t, s_t, ss_t, n_c, s_c, ss_c }: MeanSums): Diff {
  const mT = s_t / n_t;
  const mC = s_c / n_c;
  const vT = (ss_t - n_t * mT * mT) / (n_t - 1);
  const vC = (ss_c - n_c * mC * mC) / (n_c - 1);
  const d = mT - mC;
  const se = Math.sqrt(vT / n_t + vC / n_c);
  return { d, se, z: se > 0 ? d / se : 0 };
}
