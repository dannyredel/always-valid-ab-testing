// Plain-language text for the page. Every number comes from the engine.

import type { FinalVerdict as Verdict, Light } from './engine/guardrail';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export const fmt = (n: number) => Math.round(n).toLocaleString('en-US');

/** Probability difference as signed percentage points, e.g. "+1.8". Rounds before choosing the sign,
 * so a value that rounds to zero reads "0.0", never "−0.0". */
export function points(x: number, digits = 1): string {
  const v = Number((x * 100).toFixed(digits));
  if (v === 0) return (0).toFixed(digits);
  return `${v > 0 ? '+' : '−'}${Math.abs(v).toFixed(digits)}`;
}

/** Like points(), but with two decimals near zero, so a bound that excludes zero never reads "0.0". */
export function boundPoints(x: number): string {
  return Math.abs(x * 100) < 0.05 && x !== 0 ? points(x, 2) : points(x);
}

/** Experiment clock (hours since launch on a Monday) as "Thu, day 4, 14:00". */
export function clockLabel(hour: number): string {
  const day = Math.floor(hour / 24);
  const h = Math.floor(hour % 24);
  const m = Math.round((hour % 1) * 60);
  return `${WEEKDAYS[day % 7]}, day ${day + 1}, ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

export const VERDICT_LABEL: Record<Verdict, string> = {
  keep_collecting: 'Keep collecting',
  ship: 'Ship',
  dont_ship: "Don't ship",
  inconclusive: 'Inconclusive',
  doesnt_pay: "Don't ship",
};

export const PAYS_LABEL: Record<Light, string> = {
  green: 'Yes',
  grey: 'Not clear yet',
  red: 'No',
};

/** The verdict in one plain sentence. Anything said about paying comes from the guardrail light alone,
 * so the page never gives two answers to "does it pay?". */
export function verdictSentence(args: {
  verdict: Verdict;
  n: number;
  d: number;
  minPlayers: number;
  maxPlayers: number;
  pays?: Light;
}): string {
  const { verdict, n, d, minPlayers, maxPlayers, pays = 'grey' } = args;
  const lead = `${Math.abs(d * 100).toFixed(1)} points`;
  const ahead = d >= 0 ? 'ahead' : 'behind';
  if (n === 0) return 'The first outcomes are about to come in.';
  if (verdict === 'ship')
    return pays === 'green'
      ? `After ${fmt(n)} players the Starter Bonus is ahead by ${lead}, the whole range is above zero, and it pays for itself. Ship it.`
      : `After ${fmt(n)} players the Starter Bonus is ahead by ${lead} and the whole range is above zero: it works, so ship it. Whether it pays for itself isn't clear yet.`;
  if (verdict === 'doesnt_pay')
    return `After ${fmt(n)} players the Starter Bonus is ahead by ${lead}: it works, but it costs more than it brings in. Don't ship it.`;
  if (verdict === 'dont_ship')
    return `After ${fmt(n)} players the Starter Bonus is behind by ${lead}, and the whole range is below zero. Don't ship it.`;
  if (verdict === 'inconclusive') {
    const limit = `We reached the ${fmt(maxPlayers)}-player limit without a clear answer.`;
    if (pays === 'red') return `${limit} One thing is clear: the bonus costs more than it brings in, so it isn't worth it.`;
    if (pays === 'green') return `${limit} Value per player does look higher with the bonus.`;
    return `${limit} Any effect is too small to tell apart from zero, and so is its effect on value per player.`;
  }
  if (n < minPlayers)
    return `First results are coming in: ${fmt(n)} players so far. A verdict is possible from ${fmt(minPlayers)} players.`;
  return `After ${fmt(n)} players the Starter Bonus is ${ahead} by ${lead}, but that could still be noise.`;
}
