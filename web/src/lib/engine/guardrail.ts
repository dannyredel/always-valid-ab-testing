// The guardrail (port of ablab/guardrail.py): projected net value per player and its traffic light.

import type { Plan } from './config';
import type { Verdict } from './sequential';

export type Light = 'green' | 'grey' | 'red';
export type FinalVerdict = Verdict | 'doesnt_pay';

export const extraCost = (plan: Plan) => plan.bonus_usd * (1 - plan.p_reach_level10);

export function value(activated: boolean, treated: boolean, plan: Plan): number {
  if (!activated) return 0;
  return plan.value_per_activation_usd - (treated ? extraCost(plan) : 0);
}

/** Value per player (Starter Bonus minus standard, $) as an exact, increasing function of the lift:
 * (V - c) * lift - c * pC. Maps the always-valid lift interval to a value interval, so 'pays' (green)
 * is exactly 'the lift is shown above break-even' (pC as a plug-in estimate). */
export function valueFromLift(lift: number, pC: number, plan: Plan): number {
  const c = extraCost(plan);
  return (plan.value_per_activation_usd - c) * lift - c * pC;
}

export function light(lo: number, hi: number): Light {
  if (hi < 0) return 'red';
  if (lo > 0) return 'green';
  return 'grey';
}

/** Ship when the lift is shown above zero and the guardrail is not red (DECISIONS.md, 2026-10-12). */
export function finalVerdict(lift: Verdict, pays: Light): FinalVerdict {
  return lift === 'ship' && pays === 'red' ? 'doesnt_pay' : lift;
}
