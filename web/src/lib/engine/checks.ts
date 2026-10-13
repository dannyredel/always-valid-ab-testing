// Health checks from running counts, port of ablab/checks.py.

import gammaln from '@stdlib/math-base-special-gammaln';

/** Log Bayes factor against the planned split (Lindon & Malek 2022, as in savvi). */
export function srmLogBayesFactor(nC: number, nT: number, shareT = 0.5, k = 100): number {
  const theta = [1 - shareT, shareT];
  const x = [nC, nT];
  const a0 = theta.map((t) => k * t);
  const logBeta = (a: number[]) => a.reduce((s, v) => s + gammaln(v), 0) - gammaln(a.reduce((s, v) => s + v, 0));
  const post = a0.map((v, i) => v + x[i]!);
  return logBeta(post) - logBeta(a0) - x.reduce((s, xi, i) => s + xi * Math.log(theta[i]!), 0);
}

/** Standardised mean difference of a 0/1 indicator from counts (sample variances, as causalml). */
export function smdFromCounts(kC: number, nC: number, kT: number, nT: number): number {
  const pC = kC / nC;
  const pT = kT / nT;
  const vC = (pC * (1 - pC) * nC) / (nC - 1);
  const vT = (pT * (1 - pT) * nT) / (nT - 1);
  const denom = Math.sqrt(0.5 * (vC + vT));
  return denom === 0 ? 0 : (pT - pC) / denom;
}
