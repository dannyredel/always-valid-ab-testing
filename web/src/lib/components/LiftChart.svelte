<script lang="ts">
  import type { Look, PeekMoment } from '../engine/run';
  import { fmt, points } from '../format';

  let {
    looks, minPlayers, maxPlayers, truth = null, peek = null,
  }: { looks: Look[]; minPlayers: number; maxPlayers: number; truth?: number | null; peek?: PeekMoment | null } = $props();

  // Drawn at the container's real width, so text stays at its set size on a phone.
  let width = $state(560);
  const W = $derived(Math.max(300, Math.round(width)));
  const H = $derived(Math.round(Math.min(280, Math.max(220, W * 0.46))));
  const R_TRUTH = 58; // extra right margin for the true-lift label, outside the plot
  const M = $derived({ l: 46, r: truth !== null ? 16 + R_TRUTH : 16, t: 14, b: 34 });
  const EARLIEST = 500; // the estimate is too noisy to draw before this

  const shown = $derived(looks.filter((l) => l.n >= EARLIEST));
  const banded = $derived(looks.filter((l) => Number.isFinite(l.lo)));
  const last = $derived(shown.at(-1));

  // y range: fitted to the band from twice the minimum sample on and to the estimate from the minimum
  // on, always including zero. The first, widest stretch of the band is clipped at the plot edges.
  const yDomain = $derived.by(() => {
    let lo = -0.02;
    let hi = 0.04;
    // until twice the minimum is reached, fit the latest band so it is never clipped out of view
    const from = Math.min(2 * minPlayers, banded.at(-1)?.n ?? Infinity);
    for (const l of banded) if (l.n >= from) { lo = Math.min(lo, l.lo); hi = Math.max(hi, l.hi); }
    for (const l of shown) if (l.n >= minPlayers) { lo = Math.min(lo, l.d); hi = Math.max(hi, l.d); }
    if (truth !== null) { lo = Math.min(lo, truth); hi = Math.max(hi, truth); }
    lo = Math.max(lo, -0.15);
    hi = Math.min(hi, 0.2);
    const step = tickStep(hi - lo);
    return { lo: Math.floor(lo / step) * step, hi: Math.ceil(hi / step) * step, step };
  });

  function tickStep(span: number): number {
    for (const s of [0.01, 0.02, 0.05]) if (span / s <= 7) return s;
    return 0.1;
  }

  const x = (n: number) => M.l + (n / maxPlayers) * (W - M.l - M.r);
  const y = (v: number) => {
    const { lo, hi } = yDomain;
    const c = Math.max(lo, Math.min(hi, v));
    return M.t + ((hi - c) / (hi - lo)) * (H - M.t - M.b);
  };

  const yTicks = $derived.by(() => {
    const t: number[] = [];
    for (let v = yDomain.lo; v <= yDomain.hi + 1e-9; v += yDomain.step) t.push(Math.round(v * 1e6) / 1e6);
    return t;
  });
  const xTicks = $derived(W < 420 ? [0, maxPlayers / 2, maxPlayers] : [0, maxPlayers / 3, (2 * maxPlayers) / 3, maxPlayers]);

  const bandPath = $derived.by(() => {
    if (banded.length === 0) return '';
    if (banded.length === 1) { // first update with a range: a thin bar, so the range is visible at once
      const l = banded[0]!;
      return `M${x(l.n) - 1.5},${y(l.hi)}H${x(l.n) + 1.5}V${y(l.lo)}H${x(l.n) - 1.5}Z`;
    }
    return 'M' + banded.map((l) => `${x(l.n)},${y(l.hi)}`).join('L') + 'L' +
      [...banded].reverse().map((l) => `${x(l.n)},${y(l.lo)}`).join('L') + 'Z';
  });
  const linePath = $derived(shown.length > 1 ? 'M' + shown.map((l) => `${x(l.n)},${y(l.d)}`).join('L') : '');
</script>

<figure class="chart" bind:clientWidth={width}>
  <svg viewBox="0 0 {W} {H}" role="img"
    aria-label="Estimated lift of the Starter Bonus over time, with the range it is likely in">
    {#each yTicks as t (t)}
      {#if t !== 0}
        <line class="grid" x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} />
      {/if}
      <text class="tick" x={M.l - 8} y={y(t) + 4} text-anchor="end">{t === 0 ? '0' : points(t, 0)}</text>
    {/each}
    {#each xTicks as t, i (t)}
      <text class="tick" x={x(t)} y={H - 10} text-anchor={i === 0 ? 'start' : i === xTicks.length - 1 ? 'end' : 'middle'}>
        {i === 0 ? '0 players' : fmt(t)}
      </text>
    {/each}

    <line class="min" x1={x(minPlayers)} x2={x(minPlayers)} y1={M.t} y2={H - M.b} />
    <clipPath id="plot"><rect x={M.l} y={M.t} width={W - M.l - M.r} height={H - M.t - M.b} /></clipPath>
    <line class="zero" x1={M.l} x2={W - M.r} y1={y(0)} y2={y(0)} />

    {#if bandPath}<path class="band" d={bandPath} clip-path="url(#plot)" />{/if}
    {#if linePath}<path class="line" d={linePath} clip-path="url(#plot)" />{/if}
    {#if truth !== null}
      <line class="truth" x1={M.l} x2={W - M.r} y1={y(truth)} y2={y(truth)} />
      <text class="truth-label" x={W - M.r + 6} y={y(truth) + 4}>true {points(truth)}</text>
    {/if}
    {#if peek}
      <circle class="peek" cx={x(peek.n)} cy={y(peek.d)} r="6" />
    {/if}
    {#if last}
      <circle class="dot" cx={x(last.n)} cy={y(last.d)} r="4.5" />
      <text class="end" x={Math.min(x(last.n) + 8, W - M.r - 44)} y={y(last.d) - 9}>{points(last.d)} pts</text>
    {/if}
  </svg>
  <figcaption class="legend">
    <span><i class="lg-line"></i>Estimated lift</span>
    <span><i class="lg-band"></i>Range the true lift is in (95%, safe to check any time)</span>
    <span><i class="lg-zero"></i>No difference</span>
    {#if peek}<span><i class="lg-peek"></i>Where someone peeking at the usual interval would have stopped</span>{/if}
    {#if truth !== null}<span><i class="lg-truth"></i>True lift (known only to the simulator)</span>{/if}
  </figcaption>
</figure>

<style>
  .chart { margin: 0; }
  svg { width: 100%; height: auto; display: block; overflow: visible; }
  .tick { fill: var(--muted); font: 11px var(--font-body); font-variant-numeric: tabular-nums; }
  .grid { stroke: var(--line); }
  .zero { stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 4 4; }
  .min { stroke: var(--line-strong); stroke-dasharray: 2 4; }
  .band { fill: var(--gold); fill-opacity: 0.2; }
  .line { fill: none; stroke: var(--gold-line); stroke-width: 2.2; stroke-linejoin: round; }
  .dot { fill: var(--gold-line); stroke: var(--bg); stroke-width: 2; }
  .end { fill: var(--ink); font: 600 11px var(--font-body); font-variant-numeric: tabular-nums; }
  .truth { stroke: var(--ink); stroke-width: 1.4; }
  .truth-label { fill: var(--ink); font: 600 11px var(--font-body); }
  .peek { fill: none; stroke: var(--stop); stroke-width: 2; }
  .lg-peek { height: 10px; width: 10px !important; border: 2px solid var(--stop); border-radius: 50%; }
  .lg-truth { height: 0; border-top: 1.5px solid var(--ink); }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 12.5px; color: var(--muted); margin-top: 10px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .legend i { display: inline-block; width: 18px; }
  .lg-band { height: 10px; background: var(--gold); opacity: 0.25; border-radius: 2px; }
  .lg-line { height: 2px; background: var(--gold); }
  .lg-zero { border-top: 1.5px dashed var(--muted); }
</style>
