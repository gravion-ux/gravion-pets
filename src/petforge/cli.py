"""CLI demo: adopt a pet and watch it react to a simulated work session.

    python -m petforge.cli                 # random pet
    python -m petforge.cli --pet glitch    # a specific pet
    python -m petforge.cli --list          # show the whole catalogue
    python -m petforge.cli --pet vaelion --act bless --act vaelion-signature
"""

from __future__ import annotations

import argparse

from .catalogue import categories, cultures, load_catalogue
from .companion import PetForge

# A tiny simulated shift for a subagent: wins, a stumble, a pause, praise.
DEMO_EVENTS = [
    ("success", "finished the research sweep"),
    ("success", "tests went green on the first run"),
    ("failure", "hit a wall: flaky integration test"),
    ("success", "root-caused the flake and fixed it"),
    ("idle", "waiting on a slow review"),
    ("praise", "the chief agent praised the fix"),
    ("success", "shipped the final report"),
]


def list_catalogue() -> None:
    for pet in load_catalogue():
        print(f"{pet.id:<28} [{pet.category:<8}] {pet.name} — {pet.tagline}")
    print("\nBy category:", categories())
    print("By culture:", cultures())


def _show_performance(buddy, action_id: str) -> None:
    performance = buddy.act(action_id)
    star = "  *** SIGNATURE MOVE ***" if performance["signature"] else ""
    print(f"[act    ] {performance['name']}{star}")
    print(f"  {performance['description']}")
    print(f"  Motion : {performance['animation']}")
    print(
        f"  mood={performance['mood']}  bond Lv{performance['level']} "
        f"({performance['level_title']})  +{performance['bond_xp_gained']} XP  "
        f"energy cost {performance['energy_cost']}"
    )
    print()


def run_demo(pet_id: str | None, acts: list[str] | None = None) -> None:
    forge = PetForge(agent_name="demo-subagent")
    buddy = forge.adopt(pet_id) if pet_id else forge.adopt_random(rng_seed=7)
    pet = buddy.pet
    print("=" * 68)
    print(f"ADOPTED: {pet.name}  [{pet.category}]  {pet.form}")
    print(f"Tagline : {pet.tagline}")
    print(f"Traits  : {', '.join(pet.traits)}")
    print(f"Voice   : {pet.speech_style}")
    print(f"Loves   : {pet.favourite}")
    print(f"Look    : {pet.image_prompt()}")
    repertoire = ", ".join(action.id for action in buddy.available_actions())
    print(f"Moves   : {repertoire}")
    print("=" * 68)
    print(buddy.greeting())
    print()
    for event, note in DEMO_EVENTS:
        reaction = buddy.react(event)
        level_note = "  *** LEVEL UP! ***" if reaction["levelled_up"] else ""
        print(f"[{event:<7}] {note}")
        print(f"  {pet.name}: {reaction['message']}")
        print(
            f"  mood={reaction['mood']}  bond Lv{reaction['level']} "
            f"({reaction['level_title']})  +{reaction['bond_xp_gained']} XP"
            f"{level_note}"
        )
        print()
    for action_id in acts or []:
        _show_performance(buddy, action_id)
    if pet.signature_move is not None:
        _show_performance(buddy, pet.signature_move.id)
    status = buddy.status()
    print("-" * 68)
    print(
        f"End of shift: {pet.name} is {status['mood']}, "
        f"bond level {status['level']} — {status['level_title']} "
        f"({status['bond_xp']} XP total, {status['xp_to_next']} XP to next level)."
    )
    print(
        f"Evolution: stage {status['evolution_stage']} — {status['stage_title']} "
        f"({status['stage_form']}); {status['xp_to_evolution']} XP to next stage."
    )
    print(f"Stats: {status['stats']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="petforge", description=__doc__)
    parser.add_argument("--pet", help="catalogue id of the pet to adopt")
    parser.add_argument("--list", action="store_true", help="list all pets")
    parser.add_argument(
        "--act",
        action="append",
        default=[],
        metavar="ACTION",
        help="perform an action from the pet's repertoire (repeatable); "
        "the demo always ends with the pet's signature move",
    )
    args = parser.parse_args(argv)
    if args.list:
        list_catalogue()
    else:
        run_demo(args.pet, args.act)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
