<script lang="ts">
  // The extras: the peeking trap, this run against 1,000 others, and 200 parallel worlds.
  import type { SimConfig } from '../engine/config';
  import type { PeekMoment } from '../engine/run';
  import type { FinalVerdict as Verdict } from '../engine/guardrail';
  import { boundPoints, fmt, points } from '../format';
  import { runWorlds, type WorldsResult } from '../worlds';

  let {
    cfg, lift, slug, peek, verdict, verdictAt, seed,
  }: {
    cfg: SimConfig;
    lift: number;
    slug: string;
    peek: PeekMoment | null;
    verdict: Verdict;
    verdictAt: number | null;
    seed: number;
  } = $props();

  // ---- your run vs 1,000 others (pre-computed by `npm run precompute`)
  type Pre = { configHash: number; runs: number; presets: Record<string, { verdict: Verdict; n: number }[]> };
  let pre = $state<Pre | null>(null);
  $effect(() => {
    fetch('runs.json').then((r) => (r.ok ? r.json() : null)).then((j) => (pre = j)).catch(() => (pre = null));
  });
  const others = $derived(pre?.presets[slug] ?? null);
  const max = $derived(cfg.plan.max_players);
  const BINS = 20;
  const hist = $derived.by(() => {
    if (!others) return null;
    const bins = Array.from({ length: BINS }, () => 0);
    let none = 0;
    for (const r of others) {
      if (r.verdict === 'inconclusive') none++;
      else bins[Math.min(BINS - 1, Math.floor((r.n / max) * BINS))]!++;
    }
    return { bins, none, top: Math.max(1, ...bins) }; // bars scaled to the runs that decided
  });
  const yourN = $derived(verdict === 'keep_collecting' ? null : verdict === 'inconclusive' ? max : verdictAt);
  const sooner = $derived(
    others && yourN !== null && verdict !== 'inconclusive'
      ? others.filter((r) => r.verdict !== 'inconclusive' && r.n < yourN).length / others.length
      : null,
  );
  const decided = $derived(others ? others.filter((r) => r.verdict !== 'inconclusive').length / others.length : 0);

  // ---- 200 parallel worlds (computed in the browser, on request)
  const WORLDS = 200;
  let worlds: WorldsResult | null = $state(null);
  let running = $state(false);
  async function startWorlds() {
    running = true;
    worlds = null;
    await runWorlds(cfg, lift, WORLDS, seed * 7 + 1, (r) => (worlds = r));
    running = false;
  }
  const pct = (k: number, n: number) => (n ? `${((k / n) * 100).toFixed(1)}%` : '–');

  let width = $state(540);
  const W = $derived(Math.max(280, Math.round(width)));
  const H = 120;
</script>

<div class="how">
  <section>
    <h3>The peeking trap</h3>
    {#if peek}
      <p>
        After <b class="num">{fmt(peek.n)}</b> players the usual interval ({boundPoints(peek.naiveLo)} to {boundPoints(peek.naiveHi)} points)
        already excluded zero, so someone watching it would have called it there.
        {#if peek.lo > 0 || peek.hi < 0}
          The always-valid range ({boundPoints(peek.lo)} to {boundPoints(peek.hi)}) agreed at that moment.
        {:else}
          At that same moment the always-valid range was still {boundPoints(peek.lo)} to {boundPoints(peek.hi)} points: too early to tell.
        {/if}
      </p>
    {:else}
      <p>So far the usual interval has not excluded zero either, so a peeker would not have been fooled yet.</p>
    {/if}
  </section>

  <section>
    <h3>Your run against 1,000 others</h3>
    <div bind:clientWidth={width}></div>
    {#if slug === 'custom'}
      <p class="sub">Available for the three preset scenarios.</p>
    {:else if hist && others}
      <p class="sub">The same scenario, 1,000 times with other seeds. Each bar counts runs by how many players they needed for a verdict; {pct(decided * others.length, others.length)} reached one.</p>
      <svg viewBox="0 0 {W} {H + 26}" role="img" aria-label="Histogram of players needed for a verdict across 1,000 runs">
        {#each hist.bins as c, i (i)}
          <rect class="bar" x={(i / BINS) * W} y={H - (c / hist.top) * H} width={W / BINS - 2} height={(c / hist.top) * H} />
        {/each}
        <line class="base" x1="0" x2={W} y1={H} y2={H} />
        <text class="tick" x="0" y={H + 16}>0 players</text>
        <text class="tick" x={W} y={H + 16} text-anchor="end">{fmt(max)}</text>
        {#if yourN !== null && verdict !== 'inconclusive'}
          {@const xv = Math.min(W - 1, (yourN / max) * W)}
          <line class="you" x1={xv} x2={xv} y1="0" y2={H} />
          <text class="you-label" x={xv > W - 70 ? xv - 5 : xv + 5} y="12" text-anchor={xv > W - 70 ? 'end' : 'start'}>your run</text>
        {/if}
      </svg>
      <p class="none-note num"><span class="chip"></span>{fmt(hist.none)} of {fmt(others.length)} runs reached {fmt(max)} players without a verdict{verdict === 'inconclusive' ? ', yours among them' : ''}.</p>
      <p class="num">
        {#if yourN === null}
          Your run is still going.
        {:else if sooner !== null}
          Your run decided after {fmt(yourN)} players; {pct(sooner * others.length, others.length)} of the other runs decided sooner.
        {:else}
          Your run reached the {fmt(max)}-player limit without a verdict, like {pct(others.length - decided * others.length, others.length)} of the others.
        {/if}
      </p>
    {:else}
      <p class="sub">Loading the other runs…</p>
    {/if}
  </section>

  <section>
    <h3>200 parallel worlds</h3>
    <p class="sub">Replay this exact scenario 200 times, each watched at every update up to {fmt(max)} players, and
      {lift === 0 ? 'The bonus does nothing here, so any verdict is wrong.' : `The true lift is ${points(lift)} points, so a verdict the other way is wrong.`}</p>
    <button class="go" type="button" disabled={running} onclick={startWorlds}>
      {running ? `Running… ${worlds?.done ?? 0} of ${WORLDS}` : worlds ? 'Run 200 more' : 'Run 200 parallel worlds'}
    </button>
    {#if worlds}
      {@const av = worlds.alwaysValid}
      {@const us = worlds.usual}
      {@const reported = (t: { shipped: number; shipLiftSum: number }) => (t.shipped ? points(t.shipLiftSum / t.shipped) : '–')}
      <div class="table-scroll">
        <table class="num">
          {#if worlds.lift === 0}
            <thead><tr><th></th><th>Wrong verdict</th><th>Zero always in range</th></tr></thead>
            <tbody>
              <tr><td>Always-valid</td><td>{pct(av.wrong, worlds.done)}</td><td>{pct(av.covered, worlds.done)}</td></tr>
              <tr><td>Usual interval, peeked at</td><td class:bad={us.wrong / worlds.done > 0.05}>{pct(us.wrong, worlds.done)}</td><td>{pct(us.covered, worlds.done)}</td></tr>
            </tbody>
          {:else}
            <thead><tr><th></th><th>Shipped</th><th>Lift reported when shipping</th><th>True lift always in range</th></tr></thead>
            <tbody>
              <tr><td>Always-valid</td><td>{pct(av.shipped, worlds.done)}</td><td>{reported(av)} pts</td><td>{pct(av.covered, worlds.done)}</td></tr>
              <tr><td>Usual interval, peeked at</td><td>{pct(us.shipped, worlds.done)}</td><td>{reported(us)} pts</td><td class:bad={us.covered / worlds.done < 0.95}>{pct(us.covered, worlds.done)}</td></tr>
            </tbody>
          {/if}
        </table>
      </div>
      <p class="sub">
        {worlds.done} of {worlds.total} worlds.
        {#if worlds.lift === 0}
          Allowed: at most 5% wrong. Any verdict is wrong here, because the bonus does nothing.
        {:else}
          The true lift is {points(worlds.lift)} points. Any rule that stops when the data looks good reports a little more than the truth (the winner's curse); stopping at the first lucky high with the usual interval overstates it most.
        {/if}
      </p>
    {/if}
  </section>
</div>

<style>
  .how { margin-top: 20px; display: flex; flex-direction: column; gap: 28px; }
  h3 { font: 600 14px/1.3 var(--font-body); margin: 0 0 6px; }
  p { font-size: 13.5px; margin: 0 0 8px; max-width: 62ch; }
  .sub { font-size: 13px; color: var(--muted); }
  svg { width: 100%; height: auto; display: block; margin: 6px 0 8px; overflow: visible; }
  .bar { fill: var(--gold); fill-opacity: 0.55; }
  .base { stroke: var(--line-strong); }
  .none-note { font-size: 12.5px; color: var(--muted); display: flex; align-items: center; gap: 8px; }
  .chip { width: 10px; height: 10px; border-radius: 2px; background: var(--control); opacity: 0.45; flex: none; }
  .tick { fill: var(--muted); font: 11px var(--font-body); }
  .you { stroke: var(--ink); stroke-width: 2; }
  .you-label { fill: var(--ink); font: 600 11px var(--font-body); }
  .go { border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 7px 14px; font-size: 13.5px; cursor: pointer; margin-bottom: 10px; }
  .go:disabled { cursor: progress; color: var(--muted); }
  .table-scroll { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; min-width: 420px; }
  th, td { text-align: right; padding: 7px 8px; border-bottom: 1px solid var(--line); }
  th:first-child, td:first-child { text-align: left; padding-left: 0; }
  th { font-weight: 500; color: var(--muted); }
  .bad { color: var(--stop); font-weight: 600; }
</style>
