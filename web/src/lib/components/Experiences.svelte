<script lang="ts">
  // The two experiences, side by side. They differ in one row: when the 40 coins for level 5 are paid.
</script>

{#snippet coin()}
  <svg class="coin" viewBox="0 0 12 12" aria-hidden="true">
    <circle cx="6" cy="6" r="5.5" fill="var(--gold)" />
    <circle cx="6" cy="6" r="3.4" fill="none" stroke="var(--gold-ink)" stroke-width="1" opacity=".55" />
  </svg>
{/snippet}

{#snippet lock()}
  <svg width="9" height="9" viewBox="0 0 10 10" aria-hidden="true">
    <rect x="1.5" y="4.5" width="7" height="5" rx="1" fill="currentColor" />
    <path d="M3 4.5V3a2 2 0 0 1 4 0v1.5" stroke="currentColor" fill="none" stroke-width="1.2" />
  </svg>
{/snippet}

{#snippet gemHarbor()}
  <svg class="icon" viewBox="0 0 42 42" aria-hidden="true">
    <rect width="42" height="42" fill="#1c7c86" />
    <circle cx="34" cy="8" r="14" fill="#2aa3a8" />
    <path d="M21 9l9 8-9 16-9-16z" fill="#bff3ee" />
    <path d="M12 17h18l-9 16z" fill="#7fdcd6" />
    <path d="M21 9l-3 8h6z" fill="#fff" opacity=".7" />
  </svg>
{/snippet}

{#snippet phone(bonus: boolean)}
  <div class="phone">
    <div class="screen">
      <div class="app-bar"><b>Questline</b><span class="balance">{@render coin()}0</span></div>
      <div class="game">
        {@render gemHarbor()}
        <div><b>Gem Harbor</b><span>Match-3 puzzle, about 5 min to level 5</span></div>
      </div>
      <div class="ms-title">Your first milestones</div>
      <ul class="ms">
        {#if bonus}
          <li class="bonus"><span>Reach level 5</span><span class="reward">{@render coin()}40</span>
            <small>Starter Bonus: paid the moment you get there</small></li>
        {:else}
          <li class="locked"><span>Reach level 5</span><span class="reward">{@render coin()}40</span>
            <small>{@render lock()} Paid when you reach level 10</small></li>
        {/if}
        <li><span>Reach level 10</span><span class="reward">{@render coin()}120</span></li>
        <li><span>Reach level 25</span><span class="reward">{@render coin()}300</span></li>
      </ul>
      <div class="cta">Play and earn</div>
    </div>
  </div>
{/snippet}

<div class="experiences">
  <figure>
    <figcaption><span class="swatch"></span>Standard rewards</figcaption>
    {@render phone(false)}
  </figure>
  <figure>
    <figcaption><span class="swatch t"></span>Starter Bonus</figcaption>
    {@render phone(true)}
  </figure>
  <p class="note">
    The only difference: with the Starter Bonus, the <mark>40 coins for level 5 are paid straight away</mark>
    instead of being held until level 10.
  </p>
</div>

<style>
  .experiences { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  figure { margin: 0; min-width: 0; }
  figcaption { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; margin-bottom: 10px; }
  .swatch { width: 10px; height: 10px; border-radius: 50%; background: var(--control); flex: none; }
  .swatch.t { background: var(--gold); }
  .phone { background: var(--phone-bezel); border-radius: 30px; padding: 7px; max-width: 232px; }
  .screen { background: var(--phone-screen); border-radius: 24px; min-height: 300px; overflow: hidden; padding: 14px 12px 12px;
    display: flex; flex-direction: column; gap: 10px; font-size: 11px; line-height: 1.35; }
  .app-bar { display: flex; justify-content: space-between; align-items: center; }
  .app-bar b { font: 700 13px var(--font-display); }
  .balance { display: inline-flex; align-items: center; gap: 4px; font-weight: 600; background: var(--surface);
    border: 1px solid var(--line); padding: 2px 7px 2px 4px; border-radius: 999px; }
  :global(.coin) { width: 12px; height: 12px; flex: none; }
  .game { display: flex; gap: 9px; align-items: center; }
  :global(.experiences .icon) { width: 42px; height: 42px; border-radius: 11px; flex: none; }
  .game b { display: block; font-size: 12.5px; }
  .game span { color: var(--muted); font-size: 10.5px; }
  .ms-title { font-weight: 600; font-size: 11px; color: var(--muted); margin-top: 2px; }
  .ms { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .ms li { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; align-items: center; background: var(--surface);
    border: 1px solid var(--line); border-radius: 10px; padding: 7px 8px; }
  .ms li small { grid-column: 1 / -1; color: var(--muted); font-size: 9.5px; display: inline-flex; gap: 4px; align-items: center; }
  .reward { display: inline-flex; align-items: center; gap: 3px; font-weight: 600; }
  .ms li.bonus { background: var(--gold-wash); border-color: var(--gold-line); }
  .ms li.bonus small { color: var(--gold-ink); font-weight: 600; }
  .cta { margin-top: auto; padding-top: 8px; text-align: center; background: var(--ink); color: var(--bg); border-radius: 10px; padding: 8px;
    font-weight: 600; font-size: 11.5px; }
  .note { grid-column: 1 / -1; font-size: 13px; color: var(--muted); margin: 4px 0 0; max-width: 60ch; }
  mark { background: var(--gold-wash); color: var(--gold-ink); padding: 0 4px; border-radius: 4px; }
</style>
