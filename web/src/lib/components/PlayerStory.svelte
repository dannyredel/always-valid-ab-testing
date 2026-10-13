<script lang="ts">
  import type { SimConfig } from '../engine/config';
  import type { Player } from '../engine/simulator';
  import { journey } from '../engine/story';
  import { clockLabel } from '../format';

  let { player, cfg, onclose }: { player: Player | null; cfg: SimConfig; onclose: () => void } = $props();

  let dialog: HTMLDialogElement | undefined = $state();
  $effect(() => {
    if (player && dialog && !dialog.open) dialog.showModal();
    if (!player && dialog?.open) dialog.close();
  });

  const j = $derived(player ? journey(player, cfg) : null);
  const signedUpAt = $derived(player && j ? player.signupHour + j.signupMinute / 60 : 0);
  const after = (h: number) => (h < 1 ? `${Math.max(1, Math.round(h * 60))} min` : `${h < 10 ? h.toFixed(1) : Math.round(h)} h`);
  const levels = $derived(cfg.covariates);
</script>

<dialog bind:this={dialog} onclose={onclose} onclick={(e) => e.target === dialog && dialog?.close()}>
  {#if player && j}
    <div class="sheet">
      <div class="head">
        <div>
          <h2>Player {player.id.split('-').at(-1)?.replace(/^0+/, '')}</h2>
          <span class="arm"><span class="swatch" class:t={player.treated}></span>{player.treated ? 'Starter Bonus' : 'Standard rewards'}</span>
        </div>
        <button class="close" type="button" aria-label="Close" onclick={() => dialog?.close()}>×</button>
      </div>

      <dl class="profile">
        <dt>Country</dt><dd>{levels.tier.levels[player.tier]}</dd>
        <dt>Device</dt><dd>{levels.device.levels[player.device]}</dd>
        <dt>Came from</dt><dd>{levels.channel.levels[player.channel]}</dd>
        <dt>Games installed, last 30 days</dt><dd>{player.gamesInstalled}</dd>
        <dt>Ad click to install</dt><dd>{Math.round(player.clickToInstallS)} s</dd>
        {#if player.partnerScore !== null}
          <dt>Ad partner's engagement score</dt><dd>{player.partnerScore.toFixed(2)}</dd>
        {/if}
      </dl>

      <ol class="journey">
        <li class="done">Signed up<time>{clockLabel(signedUpAt)}</time></li>
        <li class="done">Assigned to {player.treated ? 'the Starter Bonus' : 'standard rewards'}
          <time>at sign-up, by a hash of the player ID</time></li>
        {#if j.startedAfterH !== null}
          <li class="done">Started Gem Harbor<time>{after(j.startedAfterH)} after sign-up</time></li>
        {:else}
          <li class="miss">Never started a game</li>
        {/if}
        {#if j.levelFiveAfterH !== null && j.inWindow}
          <li class="done">Reached level 5<time>{after(j.levelFiveAfterH)} after sign-up,
            {player.treated ? '40 coins paid straight away' : '40 coins on hold until level 10'}</time></li>
        {:else if j.levelFiveAfterH !== null}
          <li class="miss">Reached level 5 after {Math.round(j.levelFiveAfterH)} h<time>too late to count</time></li>
        {:else if j.startedAfterH !== null}
          <li class="miss">Did not reach level 5</li>
        {/if}
        <li class="done">Counted in the analysis<time>{clockLabel(player.signupHour + 1 + cfg.plan.outcome_delay_h)}, when the three days were up</time></li>
      </ol>

      <p class="foot">A simulated player. Journey times are for the story only: the verdict uses just one fact, whether level 5 was reached within three days.</p>
    </div>
  {/if}
</dialog>

<style>
  dialog { border: 0; padding: 0; background: var(--surface); color: var(--ink); border-radius: 14px;
    width: min(440px, calc(100vw - 32px)); box-shadow: 0 24px 60px var(--shadow); }
  dialog::backdrop { background: rgba(10, 12, 16, 0.4); }
  .sheet { padding: 22px 22px 18px; }
  .head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
  h2 { font: 700 22px/1.15 var(--font-display); margin: 0; }
  .close { border: 0; background: transparent; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 20px; color: var(--muted); }
  .arm { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 500; margin-top: 6px; }
  .swatch { width: 10px; height: 10px; border-radius: 50%; background: var(--control); }
  .swatch.t { background: var(--gold); }
  .profile { display: grid; grid-template-columns: auto 1fr; gap: 4px 16px; margin: 18px 0 0; font-size: 13.5px; }
  .profile dt { color: var(--muted); }
  .profile dd { margin: 0; font-variant-numeric: tabular-nums; }
  .journey { list-style: none; margin: 20px 0 0; padding: 0; position: relative; }
  .journey::before { content: ''; position: absolute; left: 5px; top: 8px; bottom: 8px; width: 1.5px; background: var(--line-strong); }
  .journey li { position: relative; padding: 0 0 14px 26px; font-size: 13.5px; }
  .journey li::before { content: ''; position: absolute; left: 0; top: 5px; width: 12px; height: 12px; border-radius: 50%;
    background: var(--surface); border: 2px solid var(--line-strong); }
  .journey li.done::before { background: var(--ink); border-color: var(--ink); }
  .journey li.miss { color: var(--muted); }
  time { display: block; color: var(--muted); font-size: 12px; }
  .foot { margin: 4px 0 0; padding: 12px 14px; background: var(--bg); border-radius: 8px; font-size: 12.5px; color: var(--muted); }
</style>
