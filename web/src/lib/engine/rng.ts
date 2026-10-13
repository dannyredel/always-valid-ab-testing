// Seeded randomness for the live stream. Never Math.random(): a run is reproducible from its seed.
// Generator: xoroshiro128+ from pure-rand. Samplers follow numpy's algorithms where they matter.

import prand from 'pure-rand';
import gammaln from '@stdlib/math-base-special-gammaln';

export class Rng {
  private gen: prand.RandomGenerator;
  private spare: number | null = null;

  constructor(seed: number) {
    this.gen = prand.xoroshiro128plus(seed | 0);
  }

  /** Uniform on [0, 1) with 53 random bits. */
  random(): number {
    const a = this.gen.unsafeNext() >>> 5;
    const b = this.gen.unsafeNext() >>> 6;
    return (a * 67108864 + b) / 9007199254740992;
  }

  /** Independent child stream (for a separate part of the model). */
  fork(): Rng {
    return new Rng(this.gen.unsafeNext());
  }

  normal(): number {
    if (this.spare !== null) {
      const s = this.spare;
      this.spare = null;
      return s;
    }
    let u = 0;
    let v = 0;
    let s = 0;
    do { // Marsaglia polar method
      u = 2 * this.random() - 1;
      v = 2 * this.random() - 1;
      s = u * u + v * v;
    } while (s >= 1 || s === 0);
    const m = Math.sqrt((-2 * Math.log(s)) / s);
    this.spare = v * m;
    return u * m;
  }

  /** Index drawn with the given probabilities. */
  choice(p: readonly number[]): number {
    const u = this.random();
    let c = 0;
    for (let i = 0; i < p.length; i++) {
      c += p[i]!;
      if (u < c) return i;
    }
    return p.length - 1;
  }

  /** Poisson: multiplication method for small means, PTRS (Hörmann 1993, as in numpy) otherwise. */
  poisson(lam: number): number {
    if (lam <= 0) return 0;
    if (lam < 10) {
      const limit = Math.exp(-lam);
      let k = 0;
      let prod = this.random();
      while (prod > limit) {
        k++;
        prod *= this.random();
      }
      return k;
    }
    const slam = Math.sqrt(lam);
    const loglam = Math.log(lam);
    const b = 0.931 + 2.53 * slam;
    const a = -0.059 + 0.02483 * b;
    const invalpha = 1.1239 + 1.1328 / (b - 3.4);
    const vr = 0.9277 - 3.6224 / (b - 2);
    for (;;) {
      const U = this.random() - 0.5;
      const V = this.random();
      const us = 0.5 - Math.abs(U);
      const k = Math.floor(((2 * a) / us + b) * U + lam + 0.43);
      if (us >= 0.07 && V <= vr) return k;
      if (k < 0 || (us < 0.013 && V > us)) continue;
      if (Math.log(V) + Math.log(invalpha) - Math.log(a / (us * us) + b) <= -lam + k * loglam - gammaln(k + 1)) {
        return k;
      }
    }
  }
}

/** A fresh seed for a new visit, from the browser's crypto source (not Math.random). */
export function freshSeed(): number {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0]! % 1_000_000_000;
}
