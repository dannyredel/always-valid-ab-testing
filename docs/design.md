# Design direction

The page has one job: let someone with no statistics background watch an experiment and know, at a glance, whether it's safe to act yet. Everything below serves that.

Live mockup: [design/mockups/live-lab.html](../design/mockups/live-lab.html). Open it in a browser. Its numbers come from a throwaway simulation inside the page, not from the engine.

## Principles

1. **The verdict is the headline.** It's the largest thing on screen, and it's a sentence a person would say ("Keep collecting"), not a statistic.
2. **Show behaviour first, statistics second.** Players and what they see sit on one side; the analyst's conclusion sits on the other. The chart summarises the dots; it doesn't replace them.
3. **Four things by default.** The two experiences, the arriving players, the verdict and the chart. Everything else waits behind "Show details" or a tap on a dot.
4. **One accent that means something.** Coin gold is the Starter Bonus: the treatment arm, its dots, its chart band and the coins in the app. Control is neutral ink. So colour alone tells you which arm you're looking at.
5. **Captions are live and plain.** "After 6,200 players the Starter Bonus is ahead by 1.8 points, but that could still be noise." No jargon above the details toggle. Below it, terms are explained in one line each ("only valid if you look once").
6. **Motion only where something happens.** Dots drop in each tick; the band narrows; the "keep collecting" dot breathes. Nothing else moves. Everything respects `prefers-reduced-motion`.

## Not Vega, not Lyra

| Vega / Lyra did | We do |
|---|---|
| Sidebar with 5+ sections, a wizard, a registry | Two tabs: *Live experiment*, *After the experiment* |
| Many stacked cards per screen, chips and badges | No cards on the main screen. Rows and whitespace. |
| Three typefaces (serif, mono, sans) | Two: a display face for the verdict, one text face for everything else |
| Navy and blue accents, pastel status chips | Cool neutrals plus one gold accent. Green and red only for *Ship* / *Don't ship*. |
| Tooltips on everything | Captions that are written to be understood without them |

## Tokens

| Token | Light | Dark | Role |
|---|---|---|---|
| `--bg` | `#f5f6f8` | `#0f1114` | Page |
| `--surface` | `#ffffff` | `#171a1f` | Phone UI, dialogs |
| `--ink` | `#15181e` | `#eceef2` | Text, primary buttons |
| `--muted` | `#5b6270` | `#a2a8b3` | Secondary text, axes |
| `--line` | `#e2e5ea` | `#262a31` | Hairlines, grid |
| `--control` | `#4a5260` | `#b9bfca` | Control arm |
| `--gold` | `#d99a0b` | `#f0b52c` | Starter Bonus, coins, lift band (fills only) |
| `--gold-line` | `#b07c00` | `#f0b52c` | Gold strokes: estimate line, dot outlines (≥ 3:1) |
| `--faint` | `#6b717c` | `#868d97` | Small notes (≥ 4.5:1) |
| `--border` | `#828994` | `#646b76` | Control outlines (≥ 3:1) |
| `--gold-ink` | `#8a5f00` | `#f3c25a` | Gold as text (passes contrast) |
| `--ship` | `#1f8a4c` | `#4cc27f` | Ship verdict only |
| `--stop` | `#c2362f` | `#ff6b61` | Don't-ship verdict, harmed segment |

**Type.** *Bricolage Grotesque* for the verdict and dialog titles: a little playful, which suits a games product, but still serious at large sizes. *Geist* for everything else, with tabular figures wherever numbers update.

## Screen anatomy

Laptop (≥ 920 px): two columns.

```
Live A/B Lab                      [⏸] [1× | 5× | Skip to end] [Simulator | Personas]
Live experiment   After the experiment
──────────────────────────────────────────────────────────────────────────────
Questline is a fictional app ... Does it get more players to finish?

What players see                    What the analyst concludes
┌──────────┐ ┌──────────┐           ◉ Keep collecting                ← largest
│ standard │ │ starter  │           After 6,200 players the Starter Bonus is
│  phone   │ │  bonus   │           ahead by 1.8 points, but that could ...
└──────────┘ └──────────┘
The only difference: 40 coins paid  [ lift over time, gold band narrowing,
right away instead of at level 10.    dashed zero line ]

Players arriving                    [ Show details ⌄ ]
● Standard  ○○●○○○●○○○○ ...
● Starter   ●○○●○○●○○●○ ...
```

Phone (< 920 px): one column, analyst first. Verdict, sentence, chart, then the two phones side by side at a smaller scale, then the lanes.

### Details (on request)

Rows in the style of Spotify Confidence: label on the left, an interval bar on a shared axis with a zero line, the range on the right.

1. *Why we wait*: always-valid range vs the usual interval.
2. *Is the split fair?*: SRM in one sentence.
3. *Are the groups alike?*: balance table.
4. *Is any group being harmed?*: segment rows, red only when a range sits wholly below zero.

### Player story (tap a dot)

A modal sheet. Name and arm, a short profile, then the journey as a real timeline: signed up, assigned, started a game, reached level 5, counted in the analysis. For persona runs, the persona's own reason closes it.

**Dots.** One dot is a sampled player, one in every 40, so each dot is a real person with a yes/no outcome you can tap. This avoids "dots as groups", which can't be filled or empty honestly.

## The two experiences

Questline's game screen in both arms is identical except for the first milestone row:

- **Standard:** "Reach level 5, 40 coins" with a lock: *paid when you reach level 10*.
- **Starter Bonus:** the same row in gold: *Starter Bonus: paid right away*, and the balance already shows 40.

A one-line note under the phones names the difference, so nobody has to spot it.

The example game is *Gem Harbor*, a fictional match-3 puzzle with a hand-drawn icon. No real game or studio brands.

## Open design questions

- Does the story paragraph at the top earn its space on phone, or should it collapse after the first visit?
- Should the chart show the naive interval by default as a faint second band (more teaching) or only in details (calmer)? The mockup keeps it in details.
- Max sample and tick length are placeholders until M1 tuning.
