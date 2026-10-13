<script lang="ts">
  import tomlText from '../../config/simulator.toml?raw';
  import AdjustPanel from './lib/components/AdjustPanel.svelte';
  import AfterSection from './lib/components/AfterSection.svelte';
  import BeforeSection from './lib/components/BeforeSection.svelte';
  import Details from './lib/components/Details.svelte';
  import HowSure from './lib/components/HowSure.svelte';
  import Experiences from './lib/components/Experiences.svelte';
  import Lanes from './lib/components/Lanes.svelte';
  import PlayerStory from './lib/components/PlayerStory.svelte';
  import type { Player } from './lib/engine/simulator';
  import LiftChart from './lib/components/LiftChart.svelte';
  import { parseConfig } from './lib/engine/config';
  import { freshSeed } from './lib/engine/rng';
  import { Run } from './lib/engine/run';
  import { PAYS_LABEL, VERDICT_LABEL, boundPoints, clockLabel, fmt, verdictSentence } from './lib/format';
  import { configFor, fromUrl, presets, toUrl, type Scenario } from './lib/scenario';

  const cfg = parseConfig(tomlText);
  const PRESETS = presets(cfg);
  const SHOW_SOURCE = false; // personas deferred (DECISIONS.md, 2026-10-12)

  // A run is fully described by its seed and scenario, both kept in the URL so it can be shared.
  const q = new URLSearchParams(location.search);
  const initial = fromUrl(cfg, q);
  let scenario: Scenario = $state(initial);
  let seed = $state(Number(q.get('seed')) || freshSeed());
  let runCfg = $state.raw(configFor(cfg, initial));

  let run = $state.raw(start());
  let tick = $state(0); // bumped after every update; the run object itself is not reactive
  let playing = $state(true);
  let speed = $state(1);
  let showDetails = $state(q.get('details') === '1');
  let storyOf: Player | null = $state(null);

  // Sections: Before / Live / After, as a bare #anchor so a link can open any of them.
  type Section = 'before' | 'live' | 'after';
  const readSection = (): Section => {
    const h = location.hash.slice(1);
    return h === 'before' || h === 'after' ? h : 'live';
  };
  let section = $state<Section>(readSection());
  $effect(() => {
    const on = () => (section = readSection());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  });
  let showHowSure = $state(false);
  let showAdjust = $state(false);
  let revealTruth = $state(false);

  function start(): Run {
    runCfg = configFor(cfg, scenario);
    const r = new Run(runCfg, seed, scenario.lift);
    r.step(); // open on the first update, so the page is never empty
    const url = new URL(location.href);
    url.searchParams.set('seed', String(seed));
    toUrl(url, scenario);
    history.replaceState(null, '', url);
    return r;
  }

  function newRun(s: Scenario = scenario, sd = freshSeed()) {
    scenario = s;
    seed = sd;
    showAdjust = false;
    run = start();
    tick++;
    playing = true;
  }

  // Theme: system by default; a choice is remembered on this device only (a convenience, not state).
  type Theme = 'system' | 'light' | 'dark';
  function readTheme(): Theme {
    try {
      const t = localStorage.getItem('ablab-theme');
      return t === 'light' || t === 'dark' ? t : 'system';
    } catch {
      return 'system';
    }
  }
  let theme = $state<Theme>(readTheme());
  $effect(() => {
    const el = document.documentElement;
    if (theme === 'system') delete el.dataset.theme;
    else el.dataset.theme = theme;
    try {
      localStorage.setItem('ablab-theme', theme);
    } catch {
      /* storage blocked: the choice just isn't remembered */
    }
  });

  function onScenarioSelect(value: string) {
    if (value === 'custom') showAdjust = true;
    else newRun(PRESETS.find((p) => p.slug === value)!);
  }

  function skipToEnd() {
    run.finish();
    tick++;
    playing = false;
  }

  $effect(() => {
    void tick;
    if (!playing || run.done) return;
    const id = setTimeout(() => {
      run.step();
      tick++;
    }, (run.nextDelaySeconds() * 1000) / speed);
    return () => clearTimeout(id);
  });

  const view = $derived.by(() => {
    void tick;
    const look = run.looks.at(-1);
    return {
      look,
      looks: [...run.looks],
      verdict: run.verdict,
      n: run.n,
      clock: run.clock,
      srmP: run.srmP,
      control: { ...run.control },
      treatment: { ...run.treatment },
      dots: { control: [...run.dots.control], treatment: [...run.dots.treatment] },
      fresh: run.newDots,
      peek: run.peek,
      segments: run.segments,
      verdictAt: run.verdictAt,
      done: run.done,
    };
  });

  const sentence = $derived(
    verdictSentence({
      verdict: view.verdict,
      n: view.n,
      d: view.look?.d ?? 0,
      minPlayers: cfg.plan.min_players,
      maxPlayers: cfg.plan.max_players,
      pays: view.look?.pays,
    }),
  );
  const mood = $derived(view.verdict === 'keep_collecting' ? 'collect' : view.verdict === 'doesnt_pay' ? 'dont_ship' : view.verdict);
</script>

<div class="wrap">
  <header class="top">
    <div class="brand">
      <svg class="mark" viewBox="0 0 28 28" aria-hidden="true">
        <circle cx="14" cy="14" r="13" fill="var(--ink)" />
        <path d="M8 17.5 L12 11 L15.5 15 L20 9" stroke="var(--gold)" stroke-width="2.4" fill="none"
          stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <div>
        <h1>Live A/B Lab</h1>
        <p>Questline Starter Bonus test</p>
      </div>
    </div>

    <div class="controls">
      {@render playButton()}
      {@render speed_()}
      <div class="seg" role="group" aria-label="Scenario">
        {#each PRESETS as p (p.slug)}
          <button type="button" aria-pressed={scenario.slug === p.slug} onclick={() => newRun(p)}>{p.name}</button>
        {/each}
        <button type="button" aria-pressed={scenario.slug === 'custom'} aria-expanded={showAdjust}
          onclick={() => (showAdjust = !showAdjust)}>{scenario.slug === 'custom' ? 'Custom' : 'Adjust'}</button>
      </div>
      {@render source()}
    </div>
  </header>

  <nav class="tabs" aria-label="Sections">
    {#each [['before', 'Before the experiment'], ['live', 'Live experiment'], ['after', 'After the experiment']] as [id, label] (id)}
      <a href="#{id}" aria-current={section === id ? 'page' : undefined}>{label}</a>
    {/each}
  </nav>

  {#if section === 'before'}
    <BeforeSection />
  {:else if section === 'after'}
    <AfterSection {cfg} look={view.look} verdict={view.verdict} done={view.done} clock={view.clock} n={view.n}
      srmP={view.srmP} control={view.control} treatment={view.treatment} segments={view.segments} onfinish={skipToEnd} />
  {:else}

  {#if showAdjust}
    <AdjustPanel current={scenario} onapply={(s) => newRun(s)} />
  {/if}

  <p class="story">
    <strong>Questline</strong> is a fictional app that pays people to play mobile games. Reach a level in a partner
    game and you earn coins you can cash out (100 coins = $1). Every new player's first goal is the same: reach
    level 5 in their first game for 40 coins. Today those coins are only paid once the player also reaches level 10.
    The test: for half of new players, a <strong>Starter Bonus</strong> pays the 40 coins the moment they reach
    level 5. Same reward, paid sooner. Does it get more new players to reach level 5 within three days?
  </p>

  <main class="main">
  <section class="players" aria-label="What players see">
    <h2 class="half-title">What players see</h2>
    <Experiences />
    <h2 class="half-title lanes-title">Results coming in</h2>
    <Lanes control={view.control} treatment={view.treatment} dots={view.dots} fresh={view.fresh}
      every={Run.DOT_EVERY} onpick={(p) => (storyOf = p)} />
  </section>

  <section class="analyst" aria-label="What the analyst concludes">
    <h2 class="half-title">What the analyst concludes</h2>
    <p class="verdict" data-state={mood} aria-live="polite">
      {#if mood === 'collect'}
        <svg class="icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="2.4" /><circle class="pulse" cx="10" cy="10" r="3.6" fill="currentColor" /></svg>
      {:else if mood === 'ship'}
        <svg class="icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="9" fill="currentColor" /><path d="M5.8 10.4l2.8 2.8 5.6-6" stroke="var(--bg)" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round" /></svg>
      {:else if mood === 'dont_ship'}
        <svg class="icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="9" fill="currentColor" /><path d="M6.8 6.8l6.4 6.4M13.2 6.8l-6.4 6.4" stroke="var(--bg)" stroke-width="2.2" stroke-linecap="round" /></svg>
      {:else}
        <svg class="icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" fill="none" stroke="currentColor" stroke-width="2.4" /><path d="M6 10h8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" /></svg>
      {/if}
      {VERDICT_LABEL[view.verdict]}
    </p>
    <p class="sentence">{sentence}</p>
    {#if view.look && view.n >= cfg.plan.min_players}
      <p class="pays" data-light={view.look.pays}>
        <span class="light" aria-hidden="true"></span>
        Pays for itself: <b>{PAYS_LABEL[view.look.pays]}</b>
        <span class="pays-note">(value per player {boundPoints(view.look.valLo)} to {boundPoints(view.look.valHi)} cents)</span>
      </p>
    {/if}
    <p class="meta num">
      {clockLabel(view.clock)}. {fmt(view.n)} of {fmt(cfg.plan.max_players)} planned players analysed.
      {#if view.look && Number.isFinite(view.look.lo)}
        The true lift is likely between {boundPoints(view.look.lo)} and {boundPoints(view.look.hi)} points.
      {/if}
    </p>

    <div class="chart-wrap">
      <LiftChart looks={view.looks} minPlayers={cfg.plan.min_players} maxPlayers={cfg.plan.max_players}
        truth={revealTruth ? scenario.lift : null} peek={view.peek} />
      <label class="reveal"><input id="reveal" type="checkbox" bind:checked={revealTruth} /> Reveal the true lift</label>
    </div>

    <div class="after">
      <button class="details-btn" type="button" aria-expanded={showDetails} onclick={() => (showDetails = !showDetails)}>
        {showDetails ? 'Hide details' : 'Show details'}
        <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.6" fill="none" /></svg>
      </button>
      <button class="details-btn" type="button" aria-expanded={showHowSure} onclick={() => (showHowSure = !showHowSure)}>
        How sure can we be?
        <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.6" fill="none" /></svg>
      </button>
      {#if view.done}
        <button class="again" type="button" onclick={() => newRun()}>Run it again</button>
      {/if}
    </div>

    {#if showDetails}
      <Details look={view.look} control={view.control} treatment={view.treatment} srmP={view.srmP} segments={view.segments}
        minPlayers={cfg.plan.min_players}
        levels={{ tier: cfg.covariates.tier.levels, device: cfg.covariates.device.levels, channel: cfg.covariates.channel.levels }} />
    {/if}
    {#if showHowSure}
      <HowSure cfg={runCfg} lift={scenario.lift} slug={scenario.slug} peek={view.peek} verdict={view.verdict}
        verdictAt={view.verdictAt} {seed} />
    {/if}
  </section>
  </main>

  <PlayerStory player={storyOf} {cfg} onclose={() => (storyOf = null)} />
  {/if}

  <footer class="foot">
    <p>Questline is fictional and every player is simulated. Run {seed}: share this page's link to replay it exactly.</p>
    <div class="foot-controls">
      <span class="phone-only">{@render source()}</span>
      <div class="seg small" role="group" aria-label="Theme">
        {#each ['light', 'dark', 'system'] as const as t (t)}
          <button type="button" aria-pressed={theme === t} onclick={() => (theme = t)}>{t[0]!.toUpperCase() + t.slice(1)}</button>
        {/each}
      </div>
    </div>
  </footer>
</div>

<nav class="dock" aria-label="Playback and scenario">
  {@render playButton()}
  {@render speed_(true)}
  <label class="visually-hidden" for="scenario-select">Scenario</label>
  <select id="scenario-select" value={scenario.slug} onchange={(e) => onScenarioSelect(e.currentTarget.value)}>
    {#each PRESETS as p (p.slug)}<option value={p.slug}>{p.name}</option>{/each}
    <option value="custom">{scenario.slug === 'custom' ? 'Custom' : 'Adjust…'}</option>
  </select>
</nav>

{#snippet playButton()}
  <button class="play" type="button" aria-label={playing ? 'Pause' : 'Play'} disabled={view.done}
    onclick={() => (playing = !playing)}>
    {#if playing && !view.done}
      <svg viewBox="0 0 14 14"><rect x="2" y="1" width="3.5" height="12" rx="1" /><rect x="8.5" y="1" width="3.5" height="12" rx="1" /></svg>
    {:else}
      <svg viewBox="0 0 14 14"><path d="M3 1.5v11l9.5-5.5z" /></svg>
    {/if}
  </button>
{/snippet}

{#snippet speed_(compact = false)}
  <div class="seg" role="group" aria-label="Speed">
    <button type="button" aria-pressed={speed === 1} onclick={() => (speed = 1)}>1×</button>
    <button type="button" aria-pressed={speed === 5} onclick={() => (speed = 5)}>5×</button>
    <button type="button" disabled={view.done} onclick={skipToEnd} aria-label="Skip to end">{compact ? 'End' : 'Skip to end'}</button>
  </div>
{/snippet}

{#snippet source()}
  <!-- Data-source switch (Simulator / Synthetic personas): shown again when persona runs exist (M7-M8, deferred). -->
  {#if SHOW_SOURCE}
    <div class="seg" role="group" aria-label="Data source">
      <button type="button" aria-pressed="true">Simulator</button>
      <button type="button" disabled>Synthetic personas</button>
    </div>
  {/if}
{/snippet}

<style>
  .wrap { max-width: 1180px; margin: 0 auto; padding-inline: 24px; }
  @media (max-width: 640px) { .wrap { padding-inline: 16px; } }

  .top { display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: center; justify-content: space-between; padding-block: 20px 8px; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .mark { width: 28px; height: 28px; }
  h1 { font: 600 16px/1.2 var(--font-body); margin: 0; }
  .brand p { margin: 0; font-size: 13px; color: var(--muted); }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .seg { display: inline-flex; flex-wrap: wrap; background: var(--surface); border: 1px solid var(--line); border-radius: 999px; padding: 3px; }
  .seg button { border: 0; background: transparent; padding: 5px 12px; border-radius: 999px; font-size: 13px; color: var(--muted); cursor: pointer; }
  .seg button[aria-pressed='true'] { background: var(--ink); color: var(--bg); }
  .seg button:disabled { cursor: not-allowed; opacity: 0.5; }
  .play { width: 38px; height: 38px; border-radius: 50%; border: 0; background: var(--ink); color: var(--bg); display: grid; place-items: center; cursor: pointer; }
  .play:disabled { opacity: 0.35; cursor: default; }
  .play svg { width: 14px; height: 14px; fill: currentColor; }

  .tabs { display: flex; gap: 24px; border-bottom: 1px solid var(--line); margin-top: 8px; overflow-x: auto; }
  .tabs a { padding: 10px 0; font-size: 14px; color: var(--muted); text-decoration: none; border-bottom: 2px solid transparent;
    margin-bottom: -1px; white-space: nowrap; }
  .tabs a[aria-current='page'] { color: var(--ink); border-color: var(--ink); font-weight: 500; }
  .story { margin: 20px 0 0; max-width: 68ch; color: var(--muted); font-size: 14.5px; }
  .story strong { color: var(--ink); font-weight: 600; }

  .main { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.12fr); gap: 48px; padding-block: 32px 48px; align-items: start; }
  @media (max-width: 920px) {
    .main { grid-template-columns: minmax(0, 1fr); gap: 40px; }
    .analyst { order: -1; }
  }
  .analyst, .players { min-width: 0; }
  .half-title { font: 500 13px/1.3 var(--font-body); color: var(--muted); margin: 0 0 14px; }
  .lanes-title { margin-top: 36px; }
  .verdict { display: flex; align-items: center; gap: 16px; margin: 0; font: 700 clamp(40px, 7vw, 68px)/1 var(--font-display); letter-spacing: -0.03em; }
  .verdict[data-state='ship'] { color: var(--ship); }
  .verdict[data-state='dont_ship'] { color: var(--stop); }
  .verdict[data-state='inconclusive'] { color: var(--muted); }
  .icon { width: 0.62em; height: 0.62em; flex: none; }
  .pulse { animation: pulse 2.4s ease-in-out infinite; }
  @keyframes pulse { 50% { opacity: 0.35; } }
  .sentence { font-size: 18px; line-height: 1.45; margin: 16px 0 0; max-width: 46ch; text-wrap: pretty; }
  .pays { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; margin: 14px 0 0; padding: 5px 12px;
    border: 1px solid var(--line); border-radius: 999px; background: var(--surface); font-size: 13.5px; }
  .pays b { font-weight: 600; }
  .pays .light { width: 10px; height: 10px; border-radius: 50%; background: var(--faint); }
  .pays[data-light='green'] .light { background: var(--ship); }
  .pays[data-light='red'] .light { background: var(--stop); }
  .pays-note { color: var(--muted); font-size: 12.5px; }
  .meta { margin: 10px 0 0; font-size: 13px; color: var(--muted); max-width: 70ch; }
  .chart-wrap { margin-top: 32px; }

  .after { display: flex; gap: 10px; margin-top: 28px; flex-wrap: wrap; }
  .details-btn, .again { display: inline-flex; gap: 8px; align-items: center; border: 1px solid var(--border);
    background: var(--surface); border-radius: 999px; padding: 7px 14px; font-size: 13.5px; cursor: pointer; }
  .again { background: var(--ink); color: var(--bg); border-color: var(--ink); }
  .details-btn svg { width: 12px; height: 12px; transition: transform 0.2s; }
  .details-btn[aria-expanded='true'] svg { transform: rotate(180deg); }

  .reveal { display: inline-flex; gap: 8px; align-items: center; margin-top: 12px; font-size: 13px; color: var(--muted); cursor: pointer; }
  .reveal input { accent-color: var(--ink); }
  .dock { display: none; }
  .phone-only { display: none; }
  @media (max-width: 640px) {
    .controls { display: none; }
    .phone-only { display: inline-flex; }
    .wrap { padding-bottom: 76px; }
    .dock { display: flex; gap: 8px; align-items: center; position: fixed; left: 0; right: 0; bottom: 0; z-index: 10;
      padding: 10px 16px calc(10px + env(safe-area-inset-bottom, 0px)); background: var(--surface);
      border-top: 1px solid var(--line); box-shadow: 0 -8px 24px var(--shadow); }
    .dock select { flex: 1; min-width: 0; border: 1px solid var(--border); background: var(--bg); border-radius: 999px;
      padding: 7px 12px; font-size: 13.5px; }
  }
  .foot-controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .seg.small button { padding: 3px 10px; font-size: 12px; }
  .foot { border-top: 1px solid var(--line); padding-block: 16px 32px; font-size: 12.5px; color: var(--faint);
    display: flex; flex-wrap: wrap; gap: 12px 24px; justify-content: space-between; align-items: center; }
  .foot p { margin: 0; max-width: 60ch; }
</style>
