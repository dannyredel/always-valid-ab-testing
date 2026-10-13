<script lang="ts">
  // Before the experiment: the plan (notebook 04), from web/public/plan.json (scripts/plan_page.py).
  import { fmt, points } from '../format';
  import Tex from './Tex.svelte';

  interface Plan {
    baseline: number; alpha: number; power_target: number; break_even: number; cupac_r2: number;
    max_players: number; signups_per_hour: number; outcome_delay_h: number;
    fixed_horizon_n: { unadjusted: number; cupac: number };
    power_at_break_even: number;
    economics: { bonus_usd: number; p_reach_level10: number; value_per_activation_usd: number };
    curve: { lift: number; power: number; median_players: number | null }[];
  }

  let plan = $state<Plan | null>(null);
  let failed = $state(false);
  let showMaths = $state(false);
  $effect(() => {
    fetch('plan.json').then((r) => (r.ok ? r.json() : Promise.reject())).then((j) => (plan = j)).catch(() => (failed = true));
  });

  let width = $state(560);
  const W = $derived(Math.max(300, Math.round(width)));
  const H = 240;
  const M = { l: 46, r: 16, t: 16, b: 38 };
  const xMax = 0.05;
  const x = (v: number) => M.l + (v / xMax) * (W - M.l - M.r);
  const y = (p: number) => M.t + (1 - p) * (H - M.t - M.b);

  const days = $derived(plan ? plan.max_players / plan.signups_per_hour / 24 : 0);
  const atBreakEven = $derived(plan?.curve.find((c) => c.lift === plan!.break_even));
  const labelled = $derived(plan ? plan.curve.filter((c) => [plan!.break_even, 0.02, 0.03, 0.05].includes(c.lift)) : []);
</script>

<section class="before" aria-labelledby="before-title">
  <h2 id="before-title" class="title">Before the experiment</h2>
  {#if failed}
    <p class="sub">The plan could not be loaded.</p>
  {:else if plan && atBreakEven}
    <p class="lead">
      The Starter Bonus pays for itself above a lift of <b>{points(plan.break_even)} points</b>. To catch a lift that size,
      the test may run to <b>{fmt(plan.max_players)} players</b>: {days.toFixed(1)} days of sign-ups plus
      {plan.outcome_delay_h / 24} days for the last outcomes. It then reaches "ship" in
      {(atBreakEven.power * 100).toFixed(0)}% of runs, typically after {fmt(atBreakEven.median_players ?? 0)} players.
      Bigger effects are caught much sooner.
    </p>

    <figure class="chart" bind:clientWidth={width}>
      <svg viewBox="0 0 {W} {H}" role="img" aria-label="Chance of a ship verdict within the planned maximum, by true lift">
        {#each [0, 0.25, 0.5, 0.75, 1] as p (p)}
          <line class="grid" x1={M.l} x2={W - M.r} y1={y(p)} y2={y(p)} />
          <text class="tick" x={M.l - 8} y={y(p) + 4} text-anchor="end">{p * 100}%</text>
        {/each}
        {#each [0, 0.01, 0.02, 0.03, 0.04, 0.05] as v (v)}
          <text class="tick" x={x(v)} y={H - 18} text-anchor="middle">{v === 0 ? '0' : points(v, 0)}</text>
        {/each}
        <text class="tick" x={(M.l + W - M.r) / 2} y={H - 2} text-anchor="middle">true lift (percentage points)</text>
        <line class="be" x1={x(plan.break_even)} x2={x(plan.break_even)} y1={M.t} y2={H - M.b} />
        <text class="be-label" x={x(plan.break_even) + 6} y={H - M.b - 8}>break-even</text>
        <line class="target" x1={M.l} x2={W - M.r} y1={y(plan.power_target)} y2={y(plan.power_target)} />
        <path class="curve" d={'M' + plan.curve.map((c) => `${x(c.lift)},${y(c.power)}`).join('L')} />
        {#each plan.curve as c (c.lift)}
          <circle class="pt" cx={x(c.lift)} cy={y(c.power)} r="3.5" />
        {/each}
        {#each labelled as c (c.lift)}
          {#if c.median_players}
            <text class="pt-label" x={x(c.lift) + 6} y={y(c.power) - 8}>~{fmt(c.median_players / 1000)}k</text>
          {/if}
        {/each}
      </svg>
      <figcaption>Chance of reaching "ship" within {fmt(plan.max_players)} players. Labels: typical players needed. Dashed: the 80% target.</figcaption>
    </figure>

    <p class="assume num">
      Assumes {(plan.baseline * 100).toFixed(0)}% of new players reach level 5 with standard rewards, a 5% false-alarm
      rate however often the result is checked, and CUPAC removing {(plan.cupac_r2 * 100).toFixed(0)}% of the noise.
      Economics (fictional): 40 coins = ${plan.economics.bonus_usd.toFixed(2)}, {(plan.economics.p_reach_level10 * 100).toFixed(0)}%
      of activated players reach level 10 anyway, an activated player is worth ${plan.economics.value_per_activation_usd.toFixed(2)}.
    </p>

    <button class="toggle" type="button" aria-expanded={showMaths} onclick={() => (showMaths = !showMaths)}>
      {showMaths ? 'Hide the maths' : 'Show the maths'}
    </button>
    {#if showMaths}
      <div class="maths">
        <h3>Break-even: the smallest lift worth having</h3>
        <p>The bonus pays when the extra activations are worth more than paying 40 coins early to activated players who would
          never have reached level 10. With control activation <Tex tex="p_C" />, a share <Tex tex="q" /> of activated players
          reaching level 10 anyway, bonus <Tex tex="b" /> and lifetime value <Tex tex="V" /> of an activated player:</p>
        <Tex block tex={String.raw`\Delta^\star V = (p_C + \Delta^\star)(1-q)\,b \quad\Longrightarrow\quad \Delta^\star = \frac{p_C\,(1-q)\,b}{V - (1-q)\,b} = ${(plan.break_even * 100).toFixed(2)}\ \text{points}`} />

        <h3>A one-look test needs fewer players, but only one look</h3>
        <p>Looked at once, at 5% false alarms and 80% power, with CUPAC removing a share <Tex tex="R^2" /> of the noise:</p>
        <Tex block tex={String.raw`n = \frac{2\,\big(z_{0.975} + z_{0.80}\big)^2\,\big[p_C(1-p_C) + p_T(1-p_T)\big]}{\Delta^{\star 2}}\,\big(1 - R^2\big) \approx ${fmt(plan.fixed_horizon_n.cupac).replace(',', '{,}')}`} />

        <h3>The always-valid interval, checked at every update</h3>
        <p>After <Tex tex="n" /> players, the estimate <Tex tex={String.raw`\hat\Delta_n`} /> and its standard error give a range that holds at every
          look at once (Ville's inequality), tuned to be tightest at the planned size <Tex tex="N^\star" />:</p>
        <Tex block tex={String.raw`\hat\Delta_n \pm \widehat{\mathrm{SE}}_n\, c_n, \qquad c_n = \sqrt{\frac{2\,(n\rho^2 + 1)}{n\rho^2}\,\log\frac{\sqrt{n\rho^2+1}}{\alpha}}`} />
        <Tex block tex={String.raw`\rho^2 = \frac{-2\log\alpha + \log(-2\log\alpha + 1)}{N^\star}`} />
        <p>The multiplier <Tex tex="c_n" /> replaces the usual 1.96; at the planned size it is about 3, the price of being allowed to look
          at any time. So the maximum is larger ({fmt(plan.max_players)}, about {(plan.max_players / plan.fixed_horizon_n.cupac).toFixed(1)}× the one-look size),
          but real effects usually stop well before it.</p>

        <h3>Why the curve comes from simulation</h3>
        <p>When a test may stop at any update, its power depends on the whole path of the estimate, so there is no closed formula.
          The curve above comes from 2,000 simulated experiments per lift, each checked every 250 players with the interval above.</p>
      </div>
    {/if}
  {:else}
    <p class="sub">Loading the plan…</p>
  {/if}
</section>

<style>
  .before { max-width: 760px; padding-block: 32px 48px; }
  .title { font: 700 clamp(30px, 5vw, 44px)/1.05 var(--font-display); letter-spacing: -0.02em; margin: 0 0 16px; }
  .lead { font-size: 18px; line-height: 1.5; max-width: 52ch; margin: 0; text-wrap: pretty; }
  .lead b { font-weight: 600; }
  .chart { margin: 28px 0 0; }
  svg { width: 100%; height: auto; display: block; overflow: visible; }
  .grid { stroke: var(--line); }
  .tick { fill: var(--muted); font: 11px var(--font-body); font-variant-numeric: tabular-nums; }
  .be { stroke: var(--ink); stroke-dasharray: 3 3; }
  .be-label { fill: var(--ink); font: 600 11px var(--font-body); }
  .target { stroke: var(--muted); stroke-dasharray: 5 4; }
  .curve { fill: none; stroke: var(--gold-line); stroke-width: 2.4; }
  .pt { fill: var(--gold-line); stroke: var(--bg); stroke-width: 1.5; }
  .pt-label { fill: var(--muted); font: 10.5px var(--font-body); }
  figcaption { font-size: 12.5px; color: var(--muted); margin-top: 8px; }
  .assume { font-size: 13px; color: var(--muted); max-width: 64ch; margin: 20px 0 0; }
  .toggle { margin-top: 20px; border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 7px 14px; font-size: 13.5px; cursor: pointer; }
  .maths { margin-top: 16px; max-width: 64ch; }
  .maths h3 { font: 600 14px var(--font-body); margin: 18px 0 4px; }
  .maths p { font-size: 13.5px; margin: 0 0 4px; }
  .sub { color: var(--muted); }
</style>
