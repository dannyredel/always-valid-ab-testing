<script lang="ts">
  import { SLIDERS, custom, type Scenario } from '../scenario';
  import { points } from '../format';

  let { current, onapply }: { current: Scenario; onapply: (s: Scenario) => void } = $props();

  // svelte-ignore state_referenced_locally (the sliders start from the scenario that is running)
  let lift = $state(current.lift);
  // svelte-ignore state_referenced_locally
  let baseline = $state(current.baseline);
  // svelte-ignore state_referenced_locally
  let perHour = $state(current.perHour);
</script>

<form class="adjust" onsubmit={(e) => { e.preventDefault(); onapply(custom(lift, baseline, perHour)); }}>
  <label>
    <span>True lift <b class="num">{points(lift)} pts</b></span>
    <input id="adj-lift" type="range" min={SLIDERS.lift.min} max={SLIDERS.lift.max} step={SLIDERS.lift.step} bind:value={lift} />
    <small>What the Starter Bonus really does. Only the simulator knows this.</small>
  </label>
  <label>
    <span>Baseline <b class="num">{(baseline * 100).toFixed(0)}%</b></span>
    <input id="adj-base" type="range" min={SLIDERS.baseline.min} max={SLIDERS.baseline.max} step={SLIDERS.baseline.step} bind:value={baseline} />
    <small>Share of new players who reach level 5 with standard rewards.</small>
  </label>
  <label>
    <span>Traffic <b class="num">{perHour} sign-ups / hour</b></span>
    <input id="adj-traffic" type="range" min={SLIDERS.perHour.min} max={SLIDERS.perHour.max} step={SLIDERS.perHour.step} bind:value={perHour} />
    <small>More traffic, quicker answers. The plan stays 30,000 players.</small>
  </label>
  <button type="submit">Start a run with these</button>
</form>

<style>
  .adjust { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)) auto; gap: 16px 28px; align-items: end;
    padding: 18px 0 20px; border-bottom: 1px solid var(--line); }
  @media (max-width: 860px) { .adjust { grid-template-columns: minmax(0, 1fr); } }
  label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; min-width: 0; }
  label span { display: flex; justify-content: space-between; gap: 8px; }
  b { font-weight: 600; }
  small { color: var(--muted); font-size: 12px; }
  input[type='range'] { width: 100%; accent-color: var(--gold); }
  button { border: 0; background: var(--ink); color: var(--bg); border-radius: 999px; padding: 8px 16px; font-size: 13.5px; cursor: pointer; white-space: nowrap; }
</style>
