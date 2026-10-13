<script lang="ts">
  // After the experiment: a readout of the visitor's own run, computed from the run itself.
  import type { SimConfig } from '../engine/config';
  import { extraCost, type FinalVerdict } from '../engine/guardrail';
  import type { ArmCounts, Look, SegmentRow } from '../engine/run';
  import { smdFromCounts } from '../engine/checks';
  import TargetingSection from './TargetingSection.svelte';
  import { PAYS_LABEL, VERDICT_LABEL, boundPoints, clockLabel, fmt, verdictSentence } from '../format';

  let {
    cfg, look, verdict, done, clock, n, srmP, control, treatment, segments, onfinish,
  }: {
    cfg: SimConfig;
    look: Look | undefined;
    verdict: FinalVerdict;
    done: boolean;
    clock: number;
    n: number;
    srmP: number;
    control: ArmCounts;
    treatment: ArmCounts;
    segments: SegmentRow[];
    onfinish: () => void;
  } = $props();

  const plan = $derived(cfg.plan);
  const V = $derived(plan.value_per_activation_usd);
  const c = $derived(extraCost(plan));
  const pC = $derived(control.n ? control.activated / control.n : 0);
  const usd = (x: number) => `${x < 0 ? '−' : ''}$${Math.abs(x).toFixed(2)}`;
  const per1000 = (x: number) => Math.round(x * 1000);

  const maxSmd = $derived(
    Math.max(...(['tier', 'device', 'channel'] as const).flatMap((k) =>
      control[k].map((_, i) => (control.n > 1 && treatment.n > 1 ? Math.abs(smdFromCounts(control[k][i]!, control.n, treatment[k][i]!, treatment.n)) : 0)))),
  );
  const harmed = $derived(segments.filter((s) => s.harmed));
  // Everything below comes from the CUPAC lift, so the rows add up and agree with the 'pays' light.
  const cost = (lift: number) => c * (pC + lift); // paying early to activated bonus players
  const roi = (lift: number) => (V * lift) / cost(lift); // value of extra activations per $1 of bonus
</script>

<section class="after" aria-labelledby="after-title">
  <h2 id="after-title" class="title">After the experiment</h2>
  {#if !done || !look}
    <p class="lead">Your run is still going. Its readout appears here once it reaches a verdict.</p>
    <button class="go" type="button" onclick={onfinish}>Skip to the end of this run</button>
  {:else}
    <p class="verdict" data-state={verdict}>{VERDICT_LABEL[verdict]}</p>
    <p class="lead">{verdictSentence({ verdict, n, d: look.d, minPlayers: plan.min_players, maxPlayers: plan.max_players, pays: look.pays })}</p>

    <h3>The run</h3>
    <dl class="facts num">
      <dt>Players analysed</dt><dd>{fmt(n)} of {fmt(plan.max_players)} planned</dd>
      <dt>Ended</dt><dd>{clockLabel(clock)} after launch</dd>
      <dt>Lift (with CUPAC)</dt><dd>{boundPoints(look.d)} points, likely between {boundPoints(look.lo)} and {boundPoints(look.hi)}</dd>
      <dt>Pays for itself</dt><dd>{PAYS_LABEL[look.pays]}</dd>
      <dt>Split</dt><dd>{srmP < 0.001 ? 'Check it: the split drifted from 50 / 50' : 'Fair, checked at every update'}</dd>
      <dt>Groups alike</dt><dd>{maxSmd < 0.1 ? 'Yes' : 'No'}: largest standardised difference {maxSmd.toFixed(3)}</dd>
      <dt>Harmed groups</dt><dd>{harmed.length ? harmed.map((s) => s.name).join(', ') : 'None shows clear harm'}</dd>
    </dl>

    <h3>What it means in money, per 1,000 new players</h3>
    <p class="sub">Projected with the fictional economics of the plan: an activated player is worth {usd(V)}; paying the bonus early costs about {usd(c)} per activated player who gets it.</p>
    <table class="num">
      <tbody>
        <tr><td>Extra players reaching level 5</td><td>{per1000(look.d)}</td><td class="range">{per1000(look.lo)} to {per1000(look.hi)}</td></tr>
        <tr><td>Value of those extra players</td><td>{usd(V * look.d * 1000)}</td><td class="range">{usd(V * look.lo * 1000)} to {usd(V * look.hi * 1000)}</td></tr>
        <tr><td>Cost of paying the bonus early</td><td>−{usd(cost(look.d) * 1000)}</td><td class="range">{usd(cost(look.lo) * 1000)} to {usd(cost(look.hi) * 1000)}</td></tr>
        <tr class="total"><td>Net value</td><td>{usd(look.valD * 1000)}</td><td class="range">{usd(look.valLo * 1000)} to {usd(look.valHi * 1000)}</td></tr>
        <tr><td>Return per $1 spent on the bonus</td><td>{usd(roi(look.d))}</td><td class="range">{usd(roi(look.lo))} to {usd(roi(look.hi))}</td></tr>
      </tbody>
    </table>
    <p class="sub">Ranges are the always-valid 95% ranges. Above $1.00 per $1 the bonus pays for itself (break-even).</p>

  {/if}
  <TargetingSection />
</section>

<style>
  .after { max-width: 760px; padding-block: 32px 48px; }
  .title { font: 700 clamp(30px, 5vw, 44px)/1.05 var(--font-display); letter-spacing: -0.02em; margin: 0 0 16px; }
  .verdict { font: 700 28px/1.1 var(--font-display); margin: 0 0 8px; }
  .verdict[data-state='ship'] { color: var(--ship); }
  .verdict[data-state='dont_ship'], .verdict[data-state='doesnt_pay'] { color: var(--stop); }
  .verdict[data-state='inconclusive'] { color: var(--muted); }
  .lead { font-size: 18px; line-height: 1.5; max-width: 52ch; margin: 0; text-wrap: pretty; }
  h3 { font: 600 15px var(--font-body); margin: 32px 0 10px; }
  .facts { display: grid; grid-template-columns: max-content 1fr; gap: 6px 20px; margin: 0; font-size: 14px; }
  .facts dt { color: var(--muted); }
  .facts dd { margin: 0; }
  .sub { font-size: 13px; color: var(--muted); max-width: 62ch; margin: 0 0 12px; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; margin-bottom: 10px; }
  td { padding: 8px 0; border-bottom: 1px solid var(--line); }
  td:nth-child(2) { text-align: right; padding-right: 18px; font-weight: 600; }
  td.range { text-align: right; color: var(--muted); font-size: 12.5px; }
  tr.total td { border-top: 2px solid var(--line-strong); }
  .go { margin-top: 16px; border: 0; background: var(--ink); color: var(--bg); border-radius: 999px; padding: 8px 16px; cursor: pointer; }
  @media (max-width: 520px) { .facts { grid-template-columns: 1fr; } .facts dt { margin-top: 6px; } }
</style>
