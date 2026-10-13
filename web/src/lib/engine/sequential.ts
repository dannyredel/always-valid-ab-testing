// Always-valid inference, port of ablab/sequential.py (Waudby-Smith et al. 2023, as in gbstats).

export type Verdict = 'ship' | 'dont_ship' | 'keep_collecting' | 'inconclusive';

/** Mixing variance that makes the interval tightest at nStar players. */
export function rho2For(nStar: number, alpha = 0.05): number {
  const a = -2 * Math.log(alpha);
  return (a + Math.log(a + 1)) / nStar;
}

/** Replaces 1.96: half-width of the always-valid interval in standard errors. */
export function csMultiplier(n: number, rho2: number, alpha = 0.05): number {
  const t = n * rho2;
  return Math.sqrt(((2 * (t + 1)) / t) * Math.log(Math.sqrt(t + 1) / alpha));
}

/** log of the mixture martingale (the bet against "no effect"). */
export function logWealth(z: number, n: number, rho2: number): number {
  const t = n * rho2;
  return (t * z * z) / (2 * (t + 1)) - 0.5 * Math.log(t + 1);
}

export function pValueAtLook(z: number, n: number, rho2: number): number {
  return Math.min(1, Math.exp(-logWealth(z, n, rho2)));
}

export function confidenceSequence(d: number, se: number, n: number, rho2: number, alpha = 0.05): [number, number] {
  const half = se * csMultiplier(n, rho2, alpha);
  return [d - half, d + half];
}

export function verdict(lo: number, hi: number, n: number, minN: number, maxN: number): Verdict {
  if (n >= minN && lo > 0) return 'ship';
  if (n >= minN && hi < 0) return 'dont_ship';
  if (n >= maxN) return 'inconclusive';
  return 'keep_collecting';
}

/**
 * Running state the page keeps between updates: the intersected interval (from the minimum
 * sample on) and the running minimum of the p-value. Same results as ablab's array functions.
 */
export class AlwaysValidState {
  lo = -Infinity;
  hi = Infinity;
  p = 1;

  constructor(
    readonly rho2: number,
    readonly alpha: number,
    readonly minN: number,
  ) {}

  update(d: number, se: number, z: number, n: number): { lo: number; hi: number; p: number } {
    this.p = Math.min(this.p, pValueAtLook(z, n, this.rho2));
    if (n >= this.minN) {
      const [lo, hi] = confidenceSequence(d, se, n, this.rho2, this.alpha);
      this.lo = Math.max(this.lo, lo);
      this.hi = Math.min(this.hi, hi);
    }
    return { lo: this.lo, hi: this.hi, p: this.p };
  }
}
