<script lang="ts">
  import { smdFromCounts } from '../engine/checks';
  import type { ArmCounts, Look, SegmentRow } from '../engine/run';
  import { boundPoints, PAYS_LABEL } from '../format';

  let {
    look, control, treatment, srmP, minPlayers, levels, segments,
  }: {
    look: Look | undefined;
    control: ArmCounts;
    treatment: ArmCounts;
    srmP: number;
    minPlayers: number;
    levels: { tier: string[]; device: string[]; channel: string[] };
    segments: SegmentRow[];
  } = $props();

  const SRM_ALPHA = 0.001; // usual threshold for a split warning; the test stays valid at every update

  const range = (lo: number, hi: number) => `${boundPoints(lo)} to ${boundPoints(hi)}`;
  const finite = (v: number) => Number.isFinite(v);

  // one shared axis for the three lift rows
  const dom = $derived.by(() => {
    if (!look) return [-0.05, 0.05];
    const vals = [0, look.naiveLo, look.naiveHi, look.lo, look.hi, look.rawLo, look.rawHi].filter(finite);
    return [Math.min(...vals) - 0.01, Math.max(...vals) + 0.01];
  });
  const segDom = $derived.by(() => {
    const vals = [0, ...segments.flatMap((s) => [s.lo, s.hi]).filter(finite)];
    return [Math.max(-0.2, Math.min(...vals) - 0.01), Math.min(0.25, Math.max(...vals) + 0.01)];
  });

  const n = $derived(control.n + treatment.n);
  const balance = $derived(
    (['tier', 'device', 'channel'] as const).flatMap((k) =>
      levels[k].map((name, i) => ({
        name,
        c: control.n ? control[k][i]! / control.n : 0,
        t: treatment.n ? treatment[k][i]! / treatment.n : 0,
        smd: control.n > 1 && treatment.n > 1 ? smdFromCounts(control[k][i]!, control.n, treatment[k][i]!, treatment.n) : 0,
      })),
    ),
  );
  const anyHarmed = $derived(segments.some((s) => s.harmed));
</script>

{#snippet bar(lo: number, hi: number, mark: number, d: number[], kind: 'gold' | 'grey' | 'red')}
  {@const bx = (v: number) => ((Math.max(d[0]!, Math.min(d[1]!, v)) - d[0]!) / (d[1]! - d[0]!)) * 300}
  <svg viewBox="0 0 300 18" preserveAspectRatio="none" aria-hidden="true">
    <line class="z" x1={bx(0)} x2={bx(0)} y1="0" y2="18" />
    <rect class="band {kind}" x={bx(lo)} y="6" width={Math.max(2, bx(hi) - bx(lo))} height="6" rx="3" />
    <rect class="mark {kind}" x={bx(mark) - 1.5} y="2" width="3" height="14" rx="1.5" />
  </svg>
{/snippet}

<div class="details">
  <section>
    <h3>Why we wait</h3>
    <p class="sub">The usual interval assumes you look once; looking every few seconds makes it cry wolf. The always-valid range stays honest however often you check, and CUPAC (signals known before sign-up) narrows it without breaking that promise.</p>
    {#if look}
      <div class="rows">
        {#each [
          { name: 'Always-valid, with CUPAC', note: 'used for the decision', lo: look.lo, hi: look.hi, d: look.d, kind: 'gold' as const },
          { name: 'Always-valid, plain', note: 'same promise, wider', lo: look.rawLo, hi: look.rawHi, d: look.rawD, kind: 'grey' as const },
          { name: 'Usual interval', note: 'only valid if you look once', lo: look.naiveLo, hi: look.naiveHi, d: look.rawD, kind: 'grey' as const },
        ] as row (row.name)}
          <div class="row">
            <span>{row.name}<br /><small>{row.note}</small></span>
            {#if finite(row.lo)}
              {@render bar(row.lo, row.hi, row.d, dom, row.kind)}
              <span class="val num">{range(row.lo, row.hi)}</span>
            {:else}
              <span class="wait">from {minPlayers.toLocaleString('en-US')} players</span><span></span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </section>

  {#if look}
    <section>
      <h3>Does it pay?</h3>
      <p class="sub">Value per player: an activated player is worth about $2.50 over their life, and the Starter Bonus costs about $0.18 for each activated player it pays early. "Ship" needs the lift above zero; a red light here blocks it.</p>
      <p class="check num" data-light={look.pays}>
        <b>{PAYS_LABEL[look.pays]}.</b>
        {#if finite(look.valLo)}
          The Starter Bonus changes value per player by {boundPoints(look.valLo)} to {boundPoints(look.valHi)} cents.
          {#if look.pays === 'grey'}Telling a few cents apart takes far more players than telling whether it works.{/if}
        {:else}
          Available from {minPlayers.toLocaleString('en-US')} players.
        {/if}
      </p>
    </section>
  {/if}

  <section>
    <h3>Is any group being harmed?</h3>
    <p class="sub">Lift within groups chosen before the test, each range widened because eight are watched at once. A red row is trustworthy. No red row does not prove no harm: this check only catches large harms.</p>
    <div class="rows">
      {#each segments as s (s.name)}
        <div class="row">
          <span>{s.name}<br /><small>{s.dimension}</small></span>
          {#if finite(s.lo)}
            {@render bar(s.lo, s.hi, s.d, segDom, s.harmed ? 'red' : 'gold')}
            <span class="val num" class:bad={s.harmed}>{s.harmed ? 'harmed: ' : ''}{range(s.lo, s.hi)}</span>
          {:else}
            <span class="wait">not enough players yet</span><span></span>
          {/if}
        </div>
      {/each}
    </div>
    <p class="sub after-rows">{anyHarmed ? 'At least one group is being harmed.' : 'No group shows clear harm yet.'}</p>
  </section>

  <section>
    <h3>Is the split fair?</h3>
    {#if n > 0}
      <p class="check num">
        <b class:bad={srmP < SRM_ALPHA}>{srmP < SRM_ALPHA ? 'Check the split.' : 'Looks fine.'}</b>
        {(control.n / n * 100).toFixed(1)}% standard, {(treatment.n / n * 100).toFixed(1)}% Starter Bonus, against a planned 50 / 50. Checked at every update with a test that stays valid when watched.
      </p>
    {/if}
  </section>

  <section>
    <h3>Are the groups alike?</h3>
    <p class="sub">Share of each group at sign-up. Assignment ignores these, so big gaps would mean the split went wrong. A standardised difference under 0.1 counts as balanced.</p>
    <div class="table-scroll">
      <table class="num">
        <thead><tr><th></th><th>Standard</th><th>Starter Bonus</th><th>Std. difference</th></tr></thead>
        <tbody>
          {#each balance as b (b.name)}
            <tr><td>{b.name}</td><td>{(b.c * 100).toFixed(1)}%</td><td>{(b.t * 100).toFixed(1)}%</td>
              <td class:bad={Math.abs(b.smd) >= 0.1}>{b.smd.toFixed(3)}</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>
</div>

<style>
  .details { margin-top: 20px; display: flex; flex-direction: column; gap: 28px; }
  h3 { font: 600 14px/1.3 var(--font-body); margin: 0 0 4px; }
  .sub { font-size: 13px; color: var(--muted); margin: 0 0 12px; max-width: 62ch; }
  .after-rows { margin: 10px 0 0; }
  .rows { border-top: 1px solid var(--line); }
  .row { display: grid; grid-template-columns: minmax(120px, 1.15fr) minmax(0, 2fr) 128px; gap: 12px; align-items: center;
    padding: 9px 0; border-bottom: 1px solid var(--line); font-size: 13.5px; }
  .row small { color: var(--muted); }
  .row svg { width: 100%; height: 18px; display: block; }
  .val { text-align: right; color: var(--muted); font-size: 12.5px; }
  .wait { color: var(--faint); font-size: 12.5px; }
  .z { stroke: var(--muted); stroke-dasharray: 3 3; }
  .band { fill-opacity: 0.35; }
  .band.gold, .mark.gold { fill: var(--gold); }
  .band.grey, .mark.grey { fill: var(--control); }
  .band.red, .mark.red { fill: var(--stop); }
  .mark.gold { fill: var(--gold-line); }
  .check { font-size: 13.5px; margin: 0; max-width: 62ch; }
  .check b { color: var(--ship); font-weight: 600; margin-right: 4px; }
  .check[data-light='grey'] b { color: var(--muted); }
  .check[data-light='red'] b { color: var(--stop); }
  .bad { color: var(--stop) !important; }
  .table-scroll { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; min-width: 380px; }
  th, td { text-align: right; padding: 7px 8px; border-bottom: 1px solid var(--line); }
  th:first-child, td:first-child { text-align: left; padding-left: 0; }
  th { font-weight: 500; color: var(--muted); }
  @media (max-width: 480px) {
    .row { grid-template-columns: 1fr 120px; }
    .row svg { grid-column: 1 / -1; grid-row: 2; }
  }
</style>
