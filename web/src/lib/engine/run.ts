// One live experiment: players sign up hour by hour, enter the analysis when their 72-hour window
// closes, and every update recomputes the verdict from running totals.
// The verdict uses the CUPAC-adjusted always-valid interval (notebook 06) and the guardrail light.

import { srmLogBayesFactor } from './checks';
import type { SimConfig } from './config';
import { adjusted, score } from './cupac';
import { finalVerdict, light, valueFromLift, type FinalVerdict, type Light } from './guardrail';
import { Rng } from './rng';
import { segmentLevels, SEGMENT_MIN_PLAYERS, type SegmentLevel } from './segments';
import { AlwaysValidState, rho2For, verdict } from './sequential';
import { PlayerFactory, type Player } from './simulator';
import { diffInMeans, diffInProportions, naiveInterval } from './stats';

export interface Look {
  hour: number; // experiment clock at this update
  n: number; // players analysed
  d: number; // CUPAC-adjusted estimate (used for the verdict)
  lo: number; // always-valid, CUPAC-adjusted, intersected (-inf before the minimum sample)
  hi: number;
  p: number; // always-valid p-value (adjusted)
  rawD: number; // unadjusted estimate
  rawLo: number; // always-valid, unadjusted
  rawHi: number;
  naiveLo: number; // the usual interval (unadjusted, valid for one look)
  naiveHi: number;
  valD: number; // value per player, Starter Bonus minus standard ($), from the adjusted lift
  valLo: number;
  valHi: number;
  pays: Light;
}

export interface SegmentRow extends SegmentLevel {
  n: number;
  d: number;
  lo: number;
  hi: number;
  harmed: boolean;
}

/** The first look (from the minimum sample) at which the usual interval excluded zero. */
export interface PeekMoment {
  n: number;
  d: number;
  naiveLo: number;
  naiveHi: number;
  lo: number; // always-valid range at that same moment
  hi: number;
}

export interface RunOptions {
  /** Stop at the verdict (the page) or keep going to the maximum (parallel worlds, validity). */
  stopAtVerdict?: boolean;
}

export interface ArmCounts {
  n: number;
  activated: number;
  tier: number[];
  device: number[];
  channel: number[];
  tierAct: number[];
  deviceAct: number[];
  channelAct: number[];
  adjSum: number; // CUPAC-adjusted outcome: sum and sum of squares
  adjSq: number;
}

const emptyArm = (): ArmCounts => ({
  n: 0, activated: 0, tier: [0, 0, 0], device: [0, 0], channel: [0, 0, 0],
  tierAct: [0, 0, 0], deviceAct: [0, 0], channelAct: [0, 0, 0], adjSum: 0, adjSq: 0,
});

export class Run {
  readonly rho2: number;
  clock: number; // experiment hours since launch
  readonly looks: Look[] = [];
  readonly control = emptyArm();
  readonly treatment = emptyArm();
  verdict: FinalVerdict = 'keep_collecting';
  /** Segment rows ('is any group being harmed?'), current. */
  segments: SegmentRow[] = [];
  /** Players analysed, and the estimated lift, when the verdict was first reached (null while collecting). */
  verdictAt: number | null = null;
  verdictD: number | null = null;
  srmP = 1;
  /** Peeking counter: when the usual interval would first have declared a winner. */
  peek: PeekMoment | null = null;
  /** Did each interval contain the true lift at every look so far (from the minimum sample)? */
  readonly covered = { alwaysValid: true, usual: true };
  /** Would someone peeking at the usual interval ever have seen 'ship' / 'don't ship'? */
  readonly usualCalls = { ship: false, dontShip: false };
  /** The lift a peeker at the usual interval would have reported when first calling 'ship'. */
  usualShipD: number | null = null;
  /** Players who signed up during the latest update. */
  latestSignups: Player[] = [];
  /** A 1-in-DOT_EVERY sample of analysed players, newest last, per arm (the lanes on the page). */
  readonly dots: { control: Player[]; treatment: Player[] } = { control: [], treatment: [] };
  /** Players sampled into the lanes in the latest update. */
  newDots: Set<string> = new Set();
  static readonly DOT_EVERY = 25;
  static readonly MAX_DOTS = 120;

  private readonly factory: PlayerFactory;
  private readonly queue: Player[] = []; // signed up, outcome not yet observed
  private generatedUntil = 0; // hours [0, generatedUntil) have been simulated
  private readonly state: AlwaysValidState; // adjusted lift (the verdict)
  private readonly rawState: AlwaysValidState;
  private readonly segLevels: SegmentLevel[];
  private readonly segStates: AlwaysValidState[];
  private readonly timing: Rng;

  constructor(
    readonly cfg: SimConfig,
    readonly seed: number,
    readonly lift: number,
    readonly options: RunOptions = {},
  ) {
    const root = new Rng(seed);
    const [arrivals, covariates, outcomes] = [root.fork(), root.fork(), root.fork()];
    this.timing = root.fork();
    this.factory = new PlayerFactory(cfg, lift, `Q${seed.toString(36)}`, arrivals, covariates, outcomes);
    this.rho2 = rho2For(cfg.plan.n_star, cfg.plan.alpha);
    const { alpha, min_players: minN, n_star: nStar } = cfg.plan;
    this.state = new AlwaysValidState(this.rho2, alpha, minN);
    this.rawState = new AlwaysValidState(this.rho2, alpha, minN);
    this.segLevels = segmentLevels(cfg);
    const k = this.segLevels.length;
    this.segStates = this.segLevels.map(
      (l) => new AlwaysValidState(rho2For(nStar * l.share, alpha / k), alpha / k, SEGMENT_MIN_PLAYERS),
    );
    this.clock = cfg.page.start_hour;
    this.signUpUntil(this.clock); // the visitor joins after the first days of sign-ups
    this.latestSignups = [];
  }

  get done(): boolean {
    if (this.options.stopAtVerdict === false) return this.n >= this.cfg.plan.max_players;
    return this.verdict !== 'keep_collecting';
  }

  get n(): number {
    return this.control.n + this.treatment.n;
  }

  get signedUp(): number {
    return this.n + this.queue.length;
  }

  /** Real seconds until the next update, with jitter. */
  nextDelaySeconds(): number {
    const [lo, hi] = this.cfg.page.seconds_per_update;
    return lo + (hi - lo) * this.timing.random();
  }

  /** Advance the experiment by one update. */
  step(): Look | null {
    if (this.done) return null;
    this.clock += this.cfg.page.hours_per_update;
    this.latestSignups = this.signUpUntil(this.clock);
    this.analyseMatured();
    return this.evaluate();
  }

  private signUpUntil(clock: number): Player[] {
    const fresh: Player[] = [];
    while (this.generatedUntil < Math.floor(clock)) {
      const players = this.factory.hour(this.generatedUntil++);
      this.queue.push(...players);
      fresh.push(...players);
    }
    return fresh;
  }

  /** A player signed up during hour h is observed once the 72-hour window closes, at h + 1 + 72. */
  private analyseMatured(): void {
    const delay = this.cfg.plan.outcome_delay_h;
    const max = this.cfg.plan.max_players;
    let taken = 0;
    this.newDots = new Set();
    while (taken < this.queue.length && this.queue[taken]!.signupHour + 1 + delay <= this.clock && this.n < max) {
      const p = this.queue[taken++]!;
      const arm = p.treated ? this.treatment : this.control;
      const y = p.activated ? 1 : 0;
      arm.n++;
      arm.activated += y;
      arm.tier[p.tier]!++;
      arm.device[p.device]!++;
      arm.channel[p.channel]!++;
      arm.tierAct[p.tier]! += y;
      arm.deviceAct[p.device]! += y;
      arm.channelAct[p.channel]! += y;
      const ya = adjusted(y, score(p));
      arm.adjSum += ya;
      arm.adjSq += ya * ya;

      if ((this.n - 1) % Run.DOT_EVERY === 0) {
        const lane = p.treated ? this.dots.treatment : this.dots.control;
        lane.push(p);
        if (lane.length > Run.MAX_DOTS) lane.shift();
        this.newDots.add(p.id);
      }
    }
    this.queue.splice(0, taken);
  }

  private evaluate(): Look | null {
    const { control: c, treatment: t } = this;
    if (c.n < 2 || t.n < 2) return null;
    const plan = this.cfg.plan;
    const n = this.n;
    const totals = { s_t: t.activated, n_t: t.n, s_c: c.activated, n_c: c.n };
    const raw = diffInProportions(totals);
    const adj = diffInMeans({ n_t: t.n, s_t: t.adjSum, ss_t: t.adjSq, n_c: c.n, s_c: c.adjSum, ss_c: c.adjSq });
    const { lo, hi, p } = this.state.update(adj.d, adj.se, adj.z, n);
    const r = this.rawState.update(raw.d, raw.se, raw.z, n);
    const pC = c.activated / c.n;
    const g = { d: valueFromLift(adj.d, pC, plan), lo: valueFromLift(lo, pC, plan), hi: valueFromLift(hi, pC, plan) };
    const pays = light(g.lo, g.hi);
    const [naiveLo, naiveHi] = naiveInterval(totals);
    this.srmP = Math.min(this.srmP, Math.exp(-srmLogBayesFactor(c.n, t.n)));
    this.updateSegments();

    if (this.verdictAt === null) { // a verdict, once reached, stands
      this.verdict = finalVerdict(verdict(lo, hi, n, plan.min_players, plan.max_players), pays);
      if (this.verdict !== 'keep_collecting') {
        this.verdictAt = n;
        this.verdictD = adj.d;
      }
    }
    if (n >= plan.min_players) {
      if (!this.peek && (naiveLo > 0 || naiveHi < 0)) this.peek = { n, d: raw.d, naiveLo, naiveHi, lo, hi };
      if (naiveLo > 0 && !this.usualCalls.ship) this.usualShipD = raw.d;
      if (naiveLo > 0) this.usualCalls.ship = true;
      if (naiveHi < 0) this.usualCalls.dontShip = true;
      if (!(lo <= this.lift && this.lift <= hi)) this.covered.alwaysValid = false;
      if (!(naiveLo <= this.lift && this.lift <= naiveHi)) this.covered.usual = false;
    }
    const look: Look = {
      hour: this.clock, n, d: adj.d, lo, hi, p, rawD: raw.d, rawLo: r.lo, rawHi: r.hi, naiveLo, naiveHi,
      valD: g.d, valLo: g.lo, valHi: g.hi, pays,
    };
    this.looks.push(look);
    return look;
  }

  private updateSegments(): void {
    const { control: c, treatment: t } = this;
    const act = { tier: 'tierAct', device: 'deviceAct', channel: 'channelAct' } as const;
    this.segments = this.segLevels.map((l, j) => {
      const tot = {
        n_t: t[l.key][l.index]!, s_t: t[act[l.key]][l.index]!, n_c: c[l.key][l.index]!, s_c: c[act[l.key]][l.index]!,
      };
      const n = tot.n_t + tot.n_c;
      if (tot.n_t < 2 || tot.n_c < 2) return { ...l, n, d: 0, lo: -Infinity, hi: Infinity, harmed: false };
      const { d, se, z } = diffInProportions(tot);
      const st = this.segStates[j]!.update(d, se, z, n);
      return { ...l, n, d, lo: st.lo, hi: st.hi, harmed: st.hi < 0 };
    });
  }

  /** Run to the end (used by "Skip to end"). */
  finish(maxUpdates = 10_000): void {
    for (let i = 0; i < maxUpdates && !this.done; i++) this.step();
  }
}
