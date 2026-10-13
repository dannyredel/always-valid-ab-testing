// "Run 200 parallel worlds": the same scenario, many seeds, each watched at every update to the
// maximum sample. Counts how often each method gives a wrong verdict and keeps the truth in its range.

import type { SimConfig } from './engine/config';
import { Run } from './engine/run';

export interface MethodTally {
  wrong: number; // verdicts pointing the wrong way (any verdict when there is no effect)
  shipped: number;
  covered: number; // range contained the true lift at every look
  shipLiftSum: number; // sum of the lift reported at the moment of shipping (winner's curse)
}

export interface WorldsResult {
  done: number;
  total: number;
  lift: number;
  alwaysValid: MethodTally;
  usual: MethodTally;
}

const empty = (): MethodTally => ({ wrong: 0, shipped: 0, covered: 0, shipLiftSum: 0 });

export async function runWorlds(
  cfg: SimConfig,
  lift: number,
  total: number,
  firstSeed: number,
  onProgress: (r: WorldsResult) => void,
  signal?: AbortSignal,
): Promise<WorldsResult> {
  const res: WorldsResult = { done: 0, total, lift, alwaysValid: empty(), usual: empty() };
  for (let i = 0; i < total; i++) {
    if (signal?.aborted) break;
    const run = new Run(cfg, firstSeed + i, lift, { stopAtVerdict: false });
    run.finish();
    const v = run.verdict;
    if (v === 'ship') {
      res.alwaysValid.shipped++;
      res.alwaysValid.shipLiftSum += run.verdictD!;
    }
    const claimsWorks = v === 'ship' || v === 'doesnt_pay'; // both say the lift is above zero
    if (lift === 0 ? claimsWorks || v === 'dont_ship' : lift > 0 ? v === 'dont_ship' : claimsWorks) res.alwaysValid.wrong++;
    if (run.covered.alwaysValid) res.alwaysValid.covered++;
    if (run.usualCalls.ship) {
      res.usual.shipped++;
      res.usual.shipLiftSum += run.usualShipD!;
    }
    if (lift === 0 ? run.usualCalls.ship || run.usualCalls.dontShip : lift > 0 ? run.usualCalls.dontShip : run.usualCalls.ship)
      res.usual.wrong++;
    if (run.covered.usual) res.usual.covered++;
    res.done = i + 1;
    if (i % 4 === 3 || i === total - 1) {
      onProgress({ ...res, alwaysValid: { ...res.alwaysValid }, usual: { ...res.usual } });
      await new Promise((r) => setTimeout(r, 0)); // let the page breathe
    }
  }
  return res;
}
