# petforge

**Forge a companion pet for your agent.**

Every hard-working agent deserves a sidekick with opinions. `petforge` is a
small, dependency-free Python package of AI companion pets that a chief agent
or any subagent can *adopt*. The pet rides along on the work: it celebrates
green builds, sulks (supportively) at failures, drifts off when things idle,
and slowly bonds with its agent — levelling from *Newly Met* all the way to
*Soulbound*.

Each pet is a complete character, not a skin:

- **Personality core** — traits, a speech style, quirks, and a favourite thing.
- **Mood engine** — four live stats (`energy`, `joy`, `focus`, `affection`)
  that shift with every task outcome and settle into moods like *ecstatic*,
  *focused*, *downcast* or *sleepy*.
- **Appearance descriptor** — a ready-to-paste image-generation prompt, so the
  pet can be drawn exactly as described.
- **Bond / level system** — shared work earns bond XP. Wins count, praise
  counts, and sticking around after a failure counts almost as much.
- **Agent-integration API** — plain-dict reactions any agent framework can
  consume without importing petforge types.

## The roster

27 original pets across eight categories:

| Category | Pets |
|---|---|
| `anime` | Mochi · Senpai Null · Pudding |
| `animal` | Captain Whiskers · Biscuit · Professor Hoot · Panda · Raja |
| `human` | Nova Reyes · Coach Dario · Grandma Juniper |
| `aquatic` | Bubbles · Admiral Finn · Squish |
| `couples` | Peanut & Pickle · Echo & Ember · Bit & Byte |
| `robot` | Unit-7 "Seven" · Glitch · Motherboard Maeve |
| `spirit` | Wisp · Djinn Tonic · Auntie Aurora |
| `plushie` | Labubu · Rasgulla · Jalebi · Chidiya |

`couples` pets are paired duos with two voices — Peanut charges ahead while
Pickle checks the map; Bit & Byte finish each other's sentences (and each
other's status reports).

## Quick start

```bash
pip install -e .
petforge --list            # browse the catalogue
petforge --pet glitch      # adopt Glitch for a demo shift
petforge                   # adopt a surprise pet
```

## Agent-integration API

```python
from petforge import PetForge

forge = PetForge(agent_name="research-subagent-3")
buddy = forge.adopt("glitch")          # or forge.adopt_random()

print(buddy.greeting())
reaction = buddy.react("success")      # "success" | "failure" | "idle" | "praise"
print(reaction["message"])             # the pet speaks, in character
print(reaction["mood"])                # e.g. "ecstatic"
print(buddy.status())                  # stats, bond XP, level, level title

forge.broadcast("success")             # feed one event to every adopted pet
buddy.tick()                           # heartbeat: time passes, pets get sleepy
```

`react()` returns a plain dict — `pet_id`, `event`, `message`, `mood`,
`stats`, `bond_xp_gained`, `level`, `level_title`, `levelled_up` — so it
drops straight into logs, traces, dashboards or a chief agent's report.

Reaction lines rotate per pet instead of repeating at random, so a long
session keeps feeling fresh.

## Demo output (real run)

```text
====================================================================
ADOPTED: Glitch  [robot]  holographic robot cat made of shifting pixels
Tagline : Not a bug. A feature with whiskers.
Traits  : chaotic, brilliant, unpredictable
Voice   : Sentences occasionally pixelate mid-word, then resume like nothing happened
Loves   : edge cases, neon light, and rendering errors that look cool
Look    : Holographic robot cat formed from shifting cyan and magenta pixels, blocky glitch fragments trailing from its tail, one eye a pixel heart, floating slightly rotated in space, dark background with scan lines, vaporwave digital art style
====================================================================
Glitch (holographic robot cat made of shifting pixels) joins demo-subagent. Not a bug. A feature with whiskers.

[success] finished the research sweep
  Glitch: Render: PERFECT. Glitch is doing the pixel zoomies for you, demo-subagent!
  mood=happy  bond Lv0 (Newly Met)  +12 XP

[success] tests went green on the first run
  Glitch: That compiled in my HEART first. The machine agreed second.
  mood=ecstatic  bond Lv1 (Warming Up)  +12 XP  *** LEVEL UP! ***

[failure] hit a wall: flaky integration test
  Glitch: A crash? Glitch calls that 'creative rendering', demo-subagent. We re-render.
  mood=ecstatic  bond Lv1 (Warming Up)  +9 XP

[success] root-caused the flake and fixed it
  Glitch: Render: PERFECT. Glitch is doing the pixel zoomies for you, demo-subagent!
  mood=ecstatic  bond Lv1 (Warming Up)  +12 XP

[idle   ] waiting on a slow review
  Glitch: Glitch is rendering as a loaf. Do not question the loaf.
  mood=ecstatic  bond Lv1 (Warming Up)  +2 XP

[praise ] the chief agent praised the fix
  Glitch: Glitch just rendered as a dog for one second. That is MAXIMUM joy.
  mood=ecstatic  bond Lv1 (Warming Up)  +7 XP

[success] shipped the final report
  Glitch: That compiled in my HEART first. The machine agreed second.
  mood=ecstatic  bond Lv2 (Trusted Sidekick)  +12 XP  *** LEVEL UP! ***

--------------------------------------------------------------------
End of shift: Glitch is ecstatic, bond level 2 — Trusted Sidekick (66 XP total, 44 XP to next level).
Stats: {'energy': 100, 'joy': 100, 'focus': 69, 'affection': 82}
```

## How it works

```
src/petforge/
├── catalogue.py   # loads & validates data/catalogue.json
├── models.py      # the Pet dataclass (personality core + appearance)
├── mood.py        # MoodEngine: stat deltas per event, derived mood label
├── bond.py        # Bond: XP curve, 8 levels, "Soulbound" at the top
├── companion.py   # Companion + PetForge: the adopt/react agent API
├── cli.py         # demo CLI (petforge --pet <id> | --list)
└── data/
    └── catalogue.json   # the 27 pets, all content data-driven
```

Adding a pet is a JSON edit — no code changes. The test suite validates that
every catalogue entry is complete (traits, quirks, reactions for all four
event kinds, in-range base stats), so a half-written pet fails CI, not users.

Bond XP per event: success `+12`, failure `+9`, praise `+7`, idle `+2`.
Levels: Newly Met → Warming Up → Trusted Sidekick → Close Companion →
Best Friend → Partner in Crime → Family → Soulbound.

## Development

```bash
python -m venv .venv && .venv/bin/pip install pytest
.venv/bin/python -m pytest     # 39 tests: catalogue, mood, bond, companion API
```

## License

MIT — see [LICENSE](LICENSE). Copyright © 2026 Priyanshu Kumar Thakur.
All pets, names, personalities and artwork prompts are original content
created for this project.
