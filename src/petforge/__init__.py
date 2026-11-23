"""petforge — forge a companion pet for your agent.

Every pet ships with a personality core (traits, mood engine, speech
style), an appearance descriptor usable as an image-generation prompt,
a bond/level system, an action repertoire (shared + category-flavoured
actions plus one signature move, each with an animation prompt), and a
small agent-integration API: a subagent adopts a pet, and the pet reacts
as tasks succeed, fail, stall or get praised — and acts on command.
"""

from .catalogue import (
    by_category,
    categories,
    category_actions,
    get_action,
    get_pet,
    load_actions,
    load_catalogue,
    pet_action,
    random_pet,
)
from .companion import Companion, PetForge
from .models import CATEGORIES, Action, Pet

__version__ = "0.4.0"

__all__ = [
    "CATEGORIES",
    "Action",
    "Companion",
    "Pet",
    "PetForge",
    "by_category",
    "categories",
    "category_actions",
    "get_action",
    "get_pet",
    "load_actions",
    "load_catalogue",
    "pet_action",
    "random_pet",
    "__version__",
]
