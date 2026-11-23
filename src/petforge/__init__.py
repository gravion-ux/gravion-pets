"""petforge — forge a companion pet for your agent.

Every pet ships with a personality core (traits, mood engine, speech
style), an appearance descriptor usable as an image-generation prompt, a
bond/level system, and a small agent-integration API: a subagent adopts a
pet, and the pet reacts as tasks succeed, fail, stall or get praised.
"""

from .catalogue import by_category, categories, get_pet, load_catalogue, random_pet
from .companion import Companion, PetForge
from .models import CATEGORIES, Pet

__version__ = "0.1.0"

__all__ = [
    "CATEGORIES",
    "Companion",
    "Pet",
    "PetForge",
    "by_category",
    "categories",
    "get_pet",
    "load_catalogue",
    "random_pet",
    "__version__",
]
