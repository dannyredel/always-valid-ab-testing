import { describe, expect, it } from 'vitest';
import { boundPoints, points, verdictSentence } from './format';

describe('points', () => {
  it('never shows a negative zero', () => {
    expect(points(-0.00004)).toBe('0.0');
    expect(points(0)).toBe('0.0');
    expect(points(0.0183)).toBe('+1.8');
    expect(points(-0.021)).toBe('−2.1');
  });
});

describe('what the sentence says about paying follows the guardrail light', () => {
  const base = { n: 30000, d: 0.014, minPlayers: 1000, maxPlayers: 30000 };
  it('inconclusive + red: not worth it', () => {
    expect(verdictSentence({ ...base, verdict: 'inconclusive', pays: 'red' })).toContain("isn't worth it");
  });
  it('inconclusive + grey: no claim about paying', () => {
    const t = verdictSentence({ ...base, verdict: 'inconclusive', pays: 'grey' });
    expect(t).not.toContain('worth');
    expect(t).not.toContain('pays for itself');
  });
  it('ship + grey: works, paying not clear', () => {
    expect(verdictSentence({ ...base, verdict: 'ship', pays: 'grey' })).toContain("isn't clear yet");
  });
  it('ship + green: pays', () => {
    expect(verdictSentence({ ...base, verdict: 'ship', pays: 'green' })).toContain('pays for itself. Ship it');
  });
  it('doesnt_pay: works but costs more', () => {
    expect(verdictSentence({ ...base, verdict: 'doesnt_pay', pays: 'red' })).toContain('costs more than it brings in');
  });
});

describe('bounds near zero', () => {
  it('keep their sign visible', () => {
    expect(boundPoints(0.0004)).toBe('+0.04');
    expect(boundPoints(-0.0003)).toBe('−0.03');
    expect(boundPoints(0.012)).toBe('+1.2');
  });
});
