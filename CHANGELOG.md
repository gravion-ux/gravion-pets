# Changelog

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
