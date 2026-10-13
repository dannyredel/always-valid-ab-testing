<script lang="ts">
  // LaTeX rendered with KaTeX at runtime (no network: fonts and CSS are bundled).
  import katex from 'katex';
  import 'katex/dist/katex.min.css';

  let { tex, block = false }: { tex: string; block?: boolean } = $props();
  const html = $derived(katex.renderToString(tex, { displayMode: block, throwOnError: false, output: 'html' }));
</script>

{#if block}
  <div class="tex-block">{@html html}</div>
{:else}
  <span>{@html html}</span>
{/if}

<style>
  .tex-block { overflow-x: auto; overflow-y: hidden; padding: 4px 0; }
  .tex-block :global(.katex) { font-size: 1.08em; }
</style>
