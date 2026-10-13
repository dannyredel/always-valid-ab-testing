import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

import { parseConfig } from './config';
import { Run } from './run';
import { journey } from './story';

const cfg = parseConfig(readFileSync(resolve(__dirname, '../../../../config/simulator.toml'), 'utf8'));
const run = new Run(cfg, 77, 0.02);
run.finish();
const players = [...run.dots.control, ...run.dots.treatment];

describe('player stories', () => {
  it('are the same every time a player is opened', () => {
    for (const p of players.slice(0, 20)) expect(journey(p, cfg)).toEqual(journey(p, cfg));
  });

  it('agree with the outcome the analysis counted', () => {
    const window = cfg.plan.outcome_delay_h;
    for (const p of players) {
      const j = journey(p, cfg);
      expect(j.inWindow).toBe(p.activated);
      if (p.activated) {
        expect(j.startedAfterH).not.toBeNull();
        expect(j.levelFiveAfterH!).toBeLessThan(window);
        expect(j.levelFiveAfterH!).toBeGreaterThan(j.startedAfterH!);
      } else if (j.levelFiveAfterH !== null) {
        expect(j.levelFiveAfterH).toBeGreaterThanOrEqual(window); // late finisher: does not count
      }
    }
  });

  it('lanes hold a 1-in-25 sample, capped', () => {
    expect(run.dots.control.length).toBeLessThanOrEqual(Run.MAX_DOTS);
    expect(run.dots.treatment.length).toBeLessThanOrEqual(Run.MAX_DOTS);
    expect(players.every((p) => p.treated === run.dots.treatment.includes(p))).toBe(true);
  });
});
