# Changelog

## 0.6.0 — 2026-11-26

- Catalogue expanded from 103 to **849 pets** across **26 culture
  families** (Greek 58, Japanese 67, Indian 52, Chinese 43, Norse 36,
  Egyptian/Korean/Celtic/African 32 each, and 17 more), generated
  deterministically by `tools/build_catalogue.py` from culture tables.
  Body plans (`form_type`): 473 creatures, 250 humanoids, 79 orb-primary
  spirits, 19 anime, 10 plush, 9 robots, 9 duos — all family-friendly.
- **Evolution system:** bond XP now evolves every pet through three
  stages with culture-flavoured titles (e.g. *Young Spirit → Shrine
  Guardian → Great Kami*). Evolving grants a stat bonus and an evolved
  form; `react()`/`act()` report `evolved`, `evolution_stage`,
  `stage_title` and `xp_to_evolution`, and `status()` exposes the full
  evolution state.
- **Culture signature moves:** 78 new library actions (3 per culture,
  127 total), unlocked at evolution stages 1/2/3 — Greek *Aegis Aura*,
  Japanese *Shrine Bell Chime*, Indian *Monsoon Dance*, and 75 more.
  `available_actions()` returns stage-unlocked moves;
  `locked_actions()` lists the rest.
- **API:** `by_culture()` / `cultures()` / `culture_actions()` added;
  `Pet.evolution_stage()`, `stage_title()`, `stage_form()`,
  `stage_bonus()` and `xp_to_evolution()` helpers. Catalogue data
  schema bumped to v4. Web gallery regenerated (849 pets, culture
  search). 69 Python tests + 7 web tests, all passing.

## 0.5.0 — 2026-11-25

- Catalogue expanded from 46 to **103 pets** across the ten categories.
- Every pet now has an **orb face form**: palette, face, glow and a ready
  image-generation prompt (`pet.orb_prompt()`).
- Ten new shared orb/face animations (blink, ear-wiggle, tail-wag,
  orb-pulse, float-bob, sparkle-trail, yawn, hop, twirl, nod) added to the
  action library and to every pet's repertoire — 49 library actions total.
- Catalogue data schema bumped to v3.


## 0.4.0 — Gods, devils & the actions update

- **Two new categories:** `gods` and `devils` (8 → 10 categories),
  with six original pets each (34 → 46 pets): Vaelion the storm
  sovereign, Solenne the sun goddess, Lunessa the moon guardian,
  Thalassor the sea emperor, Noctua the owl-bearer, Sylvarra the
  harvest mother; Pimwick the imp lord, Seraphel the fallen seraph,
  Grimfang the hellhound alpha, Vex the shadow broker, Emberlyn the
  ember enchantress, and Doctor Fester the plague alchemist.
- **Actions & movements system:** a shared action library (39 actions:
  14 shared basics like walk/dance/sleep/celebrate plus
  category-flavoured moves — aquatic swim/dive/splash, robot
  hover/charge, spirit float/vanish, gods levitate/bless/
  thunder-gesture, devils cackle/smoke-vanish/tail-flick, and more).
  Every pet has an explicit repertoire, and every pet — new and old —
  has one unique signature move. Each action carries a description, an
  image-to-video animation prompt (loop or one-shot), and gameplay
  effects (stat deltas, bond XP, energy cost).
- **API:** `Companion.act(action_id)` validates the repertoire, applies
  effects, and returns a performance dict; `Companion.available_actions()`
  lists a pet's repertoire; `load_actions()` / `get_action()` /
  `category_actions()` expose the library. CLI gains `--act` and every
  demo now ends with the pet's signature move.
- Catalogue data schema v2 (`actions`, `category_actions`, per-pet
  `actions` + `signature_move`). 50 tests, all passing.

## 0.3.0

- Seven new pets (34 total): Shitzu, Pitbull, Snake, Eagle, Falcon
  (animal), Dragon and Phoenix (spirit).

## 0.2.0

- New `plushie` category with Labubu, Rasgulla, Jalebi and Chidiya,
  plus Panda and Raja (animal) — 27 pets total.

## 0.1.0

- First release: 21 pets across 7 categories, personality cores, mood
  engine, bond/level system, adopt/react agent API, and the CLI demo.
