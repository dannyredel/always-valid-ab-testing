<script lang="ts">
  // Ship it to whom? Precomputed by notebook 08 (scripts/targeting_page.py -> web/public/targeting.json).
  // A fixed article about simulated experiments, not the visitor's run: nothing is fitted in the browser.
  import { fmt } from '../format';
  import Tex from './Tex.svelte';

  type RuleKey = 'everyone' | 'subgroups' | 'forest' | 'baseline_rule';
  interface RuleStat { mean: number; q10: number; q90: number }
  interface Size {
    players: number; experiments: number; rules: Record<RuleKey, RuleStat>;
    baseline_rule_share: number; forest_share: number;
    forest_beats_subgroups: number; forest_beats_baseline_rule: number;
    heterogeneity_found_test: number; heterogeneity_found_forest: number; forest_calibration_slope: number;
  }
  interface Cell { tier: string; channel: string; share: number; lift: number; baseline: number; value_cents: number }
  interface Targeting {
    preset_lift: number; planned_players: number;
    economics: { value_per_activation_usd: number; extra_cost_usd: number };
    truth: {
      cells: Cell[]; everyone_cents: number; best_by_cell_cents: number; best_possible_cents: number;
      baseline_cutoff: number; baseline_rule_share: number;
    };
    sizes: Size[];
  }

  let data = $state<Targeting | null>(null);
  let failed = $state(false);
  let chosen = $state<number | null>(null);
  let showMethod = $state(false);
  $effect(() => {
    fetch('targeting.json').then((r) => (r.ok ? r.json() : Promise.reject())).then((j: Targeting) => {
      data = j;
      chosen = j.planned_players;
    }).catch(() => (failed = true));
  });

  const size = $derived(data?.sizes.find((s) => s.players === chosen));
  // money per 1,000 new players, like the readout's table
  const per1000 = (cents: number, sign = true) => `${cents < 0 ? '−' : sign ? '+' : ''}$${Math.abs(cents * 10).toFixed(0)}`;
  const pct = (x: number) => `${Math.round(x * 100)}%`;
  const sizeLabel = (s: Size, planned: number) =>
    s.players >= 100_000 ? 'All 14 days' : s.players === planned ? `${fmt(s.players)} (planned)` : fmt(s.players);
  const ROWS: { key: RuleKey; label: string }[] = [
    { key: 'everyone', label: 'Everyone' },
    { key: 'subgroups', label: 'Best country tier × channel groups, estimated' },
    { key: 'forest', label: 'Causal forest' },
    { key: 'baseline_rule', label: 'Players unlikely to reach level 5 anyway' },
  ];

  let width = $state(560);
  const W = $derived(Math.max(300, Math.round(width)));
  const ROW = 46;
  const M = { l: 4, r: 64, t: 22, b: 26 };
  const H = ROWS.length * ROW + M.t + M.b;
  const xMax = $derived(data ? data.truth.best_possible_cents * 1.08 : 1);
  const x = (c: number) => M.l + (Math.max(0, c) / xMax) * (W - M.l - M.r);
  const ticks = $derived(Array.from({ length: Math.floor(xMax / 0.5) + 1 }, (_, i) => i * 0.5)); // every $5 per 1,000

  const tiers = $derived(data ? [...new Set(data.truth.cells.map((c) => c.tier))] : []);
  const channels = $derived(data ? [...new Set(data.truth.cells.map((c) => c.channel))] : []);
  const cell = (t: string, ch: string) => data!.truth.cells.find((c) => c.tier === t && c.channel === ch)!;
  const maxAbs = $derived(data ? Math.max(...data.truth.cells.map((c) => Math.abs(c.value_cents))) : 1);
  const tint = (v: number) => `color-mix(in srgb, ${v > 0 ? 'var(--ship)' : 'var(--stop)'} ${Math.round(8 + 30 * Math.abs(v) / maxAbs)}%, transparent)`;
</script>

<section class="targeting" aria-labelledby="targeting-title">
  <h3 id="targeting-title">Next question: ship it to whom?</h3>
  {#if failed}
    <p class="sub">The targeting results could not be loaded.</p>
  {:else if data && size}
    {@const r = size.rules}
    <p class="lead">
      Give the bonus only to players who are unlikely to reach level 5 on their own. Across {size.experiments} simulated
      experiments of {size.players >= 100_000 ? 'two weeks' : `${fmt(size.players)} players`}, that earned
      <b>{per1000(r.baseline_rule.mean, false)}</b> per 1,000 new players, against {per1000(r.everyone.mean, false)} for giving it to everyone.
    </p>

    <div class="sizes" role="group" aria-label="Experiment size">
      {#each data.sizes as s (s.players)}
        <button type="button" aria-pressed={s.players === chosen} onclick={() => (chosen = s.players)}>{sizeLabel(s, data.planned_players)}</button>
      {/each}
    </div>

    <figure class="chart" bind:clientWidth={width}>
      <svg viewBox="0 0 {W} {H}" role="img" aria-label="Value of each way of choosing who gets the bonus, per 1,000 new players">
        {#each [{ v: data.truth.best_by_cell_cents, l: 'best groups, if known' }, { v: data.truth.best_possible_cents, l: 'best possible' }] as ref (ref.l)}
          <line class="ref" x1={x(ref.v)} x2={x(ref.v)} y1={M.t - 4} y2={H - M.b} />
          <text class="ref-label" x={x(ref.v)} y={M.t - 9} text-anchor="middle">{ref.l}</text>
        {/each}
        <line class="zero" x1={x(0)} x2={W - M.r} y1={H - M.b} y2={H - M.b} />
        {#each ticks as v (v)}
          <text class="tick" x={x(v)} y={H - 8} text-anchor={v === 0 ? 'start' : 'middle'}>{v === 0 ? '$0' : per1000(v, false)}</text>
        {/each}
        {#each ROWS as row, i (row.key)}
          {@const s = r[row.key]}
          {@const y0 = M.t + i * ROW}
          <g class:best={row.key === 'baseline_rule'}>
            <text class="label" x={M.l} y={y0 + 14}>{row.label}</text>
            {#if s.q90 - s.q10 > 0.005}
              <line class="range" x1={x(s.q10)} x2={x(s.q90)} y1={y0 + 29} y2={y0 + 29} />
            {/if}
            <circle class="dot" cx={x(s.mean)} cy={y0 + 29} r="5" />
            <text class="value num" x={x(Math.max(s.mean, s.q90)) + 10} y={y0 + 33}>{per1000(s.mean)}</text>
          </g>
        {/each}
      </svg>
      <figcaption>Value of the bonus per 1,000 new players, after its cost. Dot: average over {size.experiments} experiments; line: 8 in 10 of them.</figcaption>
    </figure>

    <p class="body">
      The bonus costs money for every player who reaches level 5 with it, including those who would have anyway. So it pays
      most where that chance is low. Predicted from signals known at sign-up, the cut-off is {pct(data.truth.baseline_cutoff)}:
      about {pct(data.truth.baseline_rule_share)} of new players fall below it. This assumes the lift is no smaller for them,
      which the experiment can check. In this simulated game it holds: the countries with the lowest baseline also get the largest lift.
    </p>

    <h4>Where the bonus pays, in the simulator's truth</h4>
    <div class="grid-wrap">
      <table class="grid num">
        <thead><tr><th></th>{#each channels as ch (ch)}<th scope="col">{ch}</th>{/each}</tr></thead>
        <tbody>
          {#each tiers as t (t)}
            <tr>
              <th scope="row">{t}</th>
              {#each channels as ch (ch)}
                {@const c = cell(t, ch)}
                <td style:background={tint(c.value_cents)} title="lift {(c.lift * 100).toFixed(1)} points, baseline {pct(c.baseline)}">{per1000(c.value_cents)}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="sub">Per 1,000 players in each group. Giving the bonus to the best groups would earn {per1000(data.truth.best_by_cell_cents)}, but an experiment has to estimate them first.</p>

    <h4>Why not a causal forest?</h4>
    <p class="body">
      A causal forest, the usual tool for this question, searches for players with a larger lift. With {fmt(size.players)} players
      its own check found real differences in {pct(size.heterogeneity_found_forest)} of experiments, and a plain test of the groups
      fixed in advance in {pct(size.heterogeneity_found_test)}. Its picks earned {per1000(r.forest.mean)} per 1,000 players and
      {size.forest_beats_baseline_rule === 0 ? 'never beat' : `beat in only ${pct(size.forest_beats_baseline_rule)} of experiments`}
      the simpler rule above. The lift does differ between groups, but one experiment of this size cannot show it reliably.
    </p>

    <button class="toggle" type="button" aria-expanded={showMethod} onclick={() => (showMethod = !showMethod)}>
      {showMethod ? 'Hide the method' : 'Show the method'}
    </button>
    {#if showMethod}
      <div class="method">
        <p>Giving a player with sign-up attributes <Tex tex="x" /> the bonus changes value by the same economics as the "Pays for itself" check:</p>
        <Tex block tex={String.raw`G(x) = (V - c)\,\tau(x) - c\,p_0(x)`} />
        <p>with <Tex tex={String.raw`\tau(x)`} /> the lift, <Tex tex={String.raw`p_0(x)`} /> the chance of reaching level 5 anyway,
          <Tex tex="V" /> = ${data.economics.value_per_activation_usd.toFixed(2)} and <Tex tex="c" /> = ${data.economics.extra_cost_usd.toFixed(2)}.
          The simple rule keeps the average lift <Tex tex={String.raw`\bar\tau`} /> for everyone and gives the bonus when</p>
        <Tex block tex={String.raw`\hat p_0(x) < \frac{(V - c)\,\bar\tau}{c} = ${(data.truth.baseline_cutoff * 100).toFixed(1)}\%`} />
        <p>Each experiment is split in half at random: one half chooses the players (the forest, the group estimates, the average
          lift), the other half judges them. Every rule is then scored against the simulator's true lift and baseline for a fresh
          set of players. The groups and attributes were fixed in advance, and no group is shown unless an overall test finds
          that the lift differs at all.</p>
        <p>Computed offline in Python (econml, doubleml, statsmodels; notebook 08) at the Small preset
          ({(data.preset_lift * 100).toFixed(0)} points). Not your run.</p>
      </div>
    {/if}
  {:else}
    <p class="sub">Loading the targeting results…</p>
  {/if}
</section>

<style>
  .targeting { margin-top: 40px; padding-top: 28px; border-top: 1px solid var(--line); }
  h3 { font: 600 15px var(--font-body); margin: 0 0 10px; }
  h4 { font: 600 14px var(--font-body); margin: 28px 0 10px; }
  .lead { font-size: 18px; line-height: 1.5; max-width: 52ch; margin: 0; text-wrap: pretty; }
  .lead b { font-weight: 600; }
  .body { font-size: 14px; line-height: 1.55; max-width: 62ch; margin: 16px 0 0; text-wrap: pretty; }
  .sub { font-size: 13px; color: var(--muted); max-width: 62ch; margin: 8px 0 0; }
  .sizes { display: flex; flex-wrap: wrap; gap: 6px; margin: 18px 0 0; }
  .sizes button { border: 1px solid var(--border); background: var(--surface); color: var(--ink); border-radius: 999px; padding: 5px 12px; font-size: 13px; cursor: pointer; }
  .sizes button[aria-pressed='true'] { background: var(--ink); color: var(--bg); border-color: var(--ink); }
  .chart { margin: 14px 0 0; }
  svg { width: 100%; height: auto; display: block; overflow: visible; }
  .label { fill: var(--muted); font: 12.5px var(--font-body); }
  .best .label { fill: var(--ink); font-weight: 600; }
  .range { stroke: var(--line-strong); stroke-width: 6; stroke-linecap: round; }
  .best .range { stroke: color-mix(in srgb, var(--gold) 45%, transparent); }
  .dot { fill: var(--control); stroke: var(--bg); stroke-width: 1.5; }
  .best .dot { fill: var(--gold-line); }
  .value { fill: var(--ink); font: 600 12.5px var(--font-body); font-variant-numeric: tabular-nums; }
  .ref { stroke: var(--muted); stroke-dasharray: 3 3; }
  .ref-label, .tick { fill: var(--muted); font: 10.5px var(--font-body); }
  .value { paint-order: stroke; stroke: var(--bg); stroke-width: 4px; stroke-linejoin: round; }
  .zero { stroke: var(--line-strong); }
  figcaption { font-size: 12.5px; color: var(--muted); margin-top: 6px; }
  .grid-wrap { overflow-x: auto; }
  .grid { border-collapse: separate; border-spacing: 4px; font-size: 13.5px; }
  .grid th { font-weight: 500; color: var(--muted); padding: 4px 8px; text-align: left; white-space: nowrap; }
  .grid thead th { text-align: center; }
  .grid td { padding: 10px 14px; text-align: center; border-radius: 6px; font-weight: 600; min-width: 64px; }
  .toggle { margin-top: 22px; border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 7px 14px; font-size: 13.5px; cursor: pointer; }
  .method { margin-top: 14px; max-width: 64ch; }
  .method p { font-size: 13.5px; margin: 0 0 6px; }
</style>
