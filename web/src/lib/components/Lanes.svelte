<script lang="ts">
  import type { ArmCounts } from '../engine/run';
  import type { Player } from '../engine/simulator';
  import { fmt } from '../format';

  let {
    control, treatment, dots, fresh, every, onpick,
  }: {
    control: ArmCounts;
    treatment: ArmCounts;
    dots: { control: Player[]; treatment: Player[] };
    fresh: Set<string>;
    every: number;
    onpick: (p: Player) => void;
  } = $props();

  const rate = (a: ArmCounts) => (a.n ? `${((a.activated / a.n) * 100).toFixed(1)}%` : '–');
  const newest = $derived(dots.treatment.at(-1) ?? dots.control.at(-1));
</script>

<div class="lanes">
  {#each [{ name: 'Standard rewards', key: 'control' as const, arm: control }, { name: 'Starter Bonus', key: 'treatment' as const, arm: treatment }] as lane (lane.key)}
    <div class="lane" class:t={lane.key === 'treatment'}>
      <div class="lane-head">
        <span><span class="swatch"></span>{lane.name}</span>
        <span class="num">{fmt(lane.arm.n)} players, {rate(lane.arm)} reached level 5</span>
      </div>
      <div class="dots">
        {#each [...dots[lane.key]].reverse() as p (p.id)}
          <button type="button" tabindex="-1" class="dot" class:on={p.activated} class:new={fresh.has(p.id)}
            aria-label="Player {p.id}, {p.activated ? 'reached' : 'did not reach'} level 5"
            onclick={() => onpick(p)}></button>
        {/each}
      </div>
    </div>
  {/each}
  <div class="key">
    <span><i class="on"></i>Reached level 5 within three days</span>
    <span><i></i>Did not</span>
    <span>One dot for every {every} players.</span>
    {#if newest}
      <button type="button" class="follow" onclick={() => onpick(newest)}>Follow a player</button>
    {/if}
  </div>
</div>

<style>
  .lanes { display: flex; flex-direction: column; gap: 18px; }
  .lane-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px 12px; font-size: 13px; margin-bottom: 8px; }
  .lane-head > span:first-child { display: inline-flex; gap: 8px; align-items: center; font-weight: 500; }
  .lane-head > span:last-child { color: var(--muted); }
  .swatch { width: 10px; height: 10px; border-radius: 50%; background: var(--control); }
  .t .swatch { background: var(--gold); }
  .dots { display: flex; flex-wrap: wrap; gap: 5px; min-height: 58px; align-content: flex-start; }
  .dot { width: 10px; height: 10px; border-radius: 50%; border: 1.5px solid var(--control); padding: 0; background: transparent; cursor: pointer; }
  .dot.on { background: var(--control); }
  .t .dot { border-color: var(--gold-line); }
  .t .dot.on { background: var(--gold); }
  .dot:hover { transform: scale(1.4); }
  .dot.new { animation: drop 0.5s ease-out; }
  @keyframes drop { from { transform: translateY(-6px) scale(0.4); opacity: 0; } }
  .key { font-size: 12.5px; color: var(--faint); display: flex; gap: 8px 16px; flex-wrap: wrap; align-items: center; }
  .key i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid var(--faint); vertical-align: -1px; margin-right: 5px; }
  .key i.on { background: var(--faint); }
  .follow { border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 3px 10px;
    font-size: 12.5px; color: var(--ink); cursor: pointer; }
</style>
