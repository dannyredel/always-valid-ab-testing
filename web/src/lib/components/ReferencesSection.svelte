<script lang="ts">
  // References: the papers, books and software behind the methods, each with what it is used for here.
  import { REFERENCES } from '../references';

  const REPO = 'https://github.com/dannyredel/always-valid-ab-testing';
</script>

<section class="refs" aria-labelledby="refs-title">
  <h2 id="refs-title" class="title">References</h2>
  <p class="lead">
    The methods on this page come from the research below. Each entry says what it is used for here. The notebooks that
    build and check every method are in the <a href={REPO}>source code</a>.
  </p>

  {#each REFERENCES as group (group.title)}
    <h3>{group.title}</h3>
    <p class="intro">{group.intro}</p>
    <ol>
      {#each group.items as r (r.url)}
        <li>
          <p class="cite">
            {r.authors} ({r.year}). <a href={r.url}>{r.title}</a>. <span class="venue">{r.venue}</span>.
          </p>
          <p class="used">{r.usedFor}</p>
        </li>
      {/each}
    </ol>
  {/each}
</section>

<style>
  .refs { max-width: 760px; padding-block: 32px 48px; }
  .title { font: 700 clamp(30px, 5vw, 44px)/1.05 var(--font-display); letter-spacing: -0.02em; margin: 0 0 16px; }
  .lead { font-size: 16px; line-height: 1.55; max-width: 60ch; margin: 0; text-wrap: pretty; }
  h3 { font: 600 15px var(--font-body); margin: 34px 0 2px; }
  .intro { font-size: 13px; color: var(--muted); margin: 0 0 10px; }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }
  li { padding-left: 14px; border-left: 2px solid var(--line); }
  .cite { font-size: 14px; line-height: 1.5; margin: 0; text-wrap: pretty; }
  .cite a { color: var(--ink); text-decoration-color: var(--line-strong); text-underline-offset: 3px; }
  .cite a:hover { text-decoration-color: var(--ink); }
  .venue { font-style: italic; color: var(--muted); }
  .used { font-size: 13px; color: var(--muted); margin: 3px 0 0; }
  .lead a { color: var(--ink); text-underline-offset: 3px; }
</style>
