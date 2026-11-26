#!/usr/bin/env python3
"""Build catalogue schema v4: cultures, form types, evolution, 800+ pets.

Reads the existing ``src/petforge/data/catalogue.json`` (schema v3, 103
hand-written pets), preserves every existing pet, enriches them with
``culture`` / ``form_type`` / ``evolution`` fields and culture moves, then
generates the mythology expansion (Greek, Japanese, Indian and 22 more
culture families) from the data tables below. Deterministic: re-running
produces byte-identical output. Also regenerates ``web/pets.js``.

    python tools/build_catalogue.py
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "src" / "petforge" / "data" / "catalogue.json"
WEB_PETS = ROOT / "web" / "pets.js"

# 14 shared basics + 10 orb animations (star-jump/sparkle-pose are
# anime-category flavours and arrive via category_actions).
BASE_ACTIONS = [
    "idle-breathe", "walk", "run", "jump", "dance", "spin", "wave", "bow",
    "sleep", "eat", "play", "celebrate", "hide", "peek",
    "blink", "ear-wiggle", "tail-wag", "orb-pulse",
    "float-bob", "sparkle-trail", "yawn", "hop", "twirl", "nod",
]

# How many NEW pets to generate per culture (existing 103 stay on top).
TARGETS = {
    "greek": 46, "japanese": 48, "indian": 48, "chinese": 40, "norse": 36,
    "egyptian": 32, "korean": 32, "celtic": 32, "african": 32,
    "roman": 28, "arabian": 28, "persian": 28, "thai": 28, "filipino": 28,
    "slavic": 28, "european-folklore": 28, "aztec": 24, "mayan": 24,
    "mesopotamian": 24, "vietnamese": 24, "polynesian": 24,
    "native-american": 24, "inuit": 20, "aboriginal-australian": 20,
    "arthurian": 20, "global-modern": 0,
}

TRAITS = [
    "loyal", "curious", "brave", "gentle", "cheerful", "wise", "playful",
    "patient", "bold", "kind", "mischievous", "calm", "energetic",
    "thoughtful", "proud", "sweet", "clever", "steady", "bright", "devoted",
]

QUIRK_TEMPLATES = [
    "collects tiny {motif} charms for every finished task",
    "hums an old {label} tune while tests run",
    "insists on celebrating small wins with a {species} dance",
    "keeps a mental map of every {motif} pattern it has seen",
    "bows politely to the compiler before every build",
    "narrates long waits like a {label} storyteller",
    "guards the snack drawer like a temple treasure",
    "practices its {species} poses in reflective screens",
    "counts successes on imaginary {motif} beads",
    "falls asleep mid-sentence, then apologises in rhyme",
]

TAGLINE_TEMPLATES = [
    "Small {species}, enormous encouragement.",
    "Brings {motif} luck to every deadline.",
    "Ancient stories, modern debugging energy.",
    "Here to celebrate every green build.",
    "Gentle heart, legendary pep talks.",
    "Turns long nights into {label} storytime.",
    "Your tiny guardian of good commits.",
    "Cheers loudest when the tests finally pass.",
]

REACTION_TEMPLATES = {
    "success": [
        "YES! {name} knew you could do it, {agent}!",
        "A {motif}-bright victory! {name} is beaming.",
        "Legendary work, {agent}. The old stories approve.",
        "That is how heroes finish quests!",
        "{name} does a happy {species} spin for you.",
        "Brilliant! One more triumph for our saga, {agent}.",
    ],
    "failure": [
        "Even heroes stumble, {agent}. {name} stays right here.",
        "A setback is just a plot twist. We go again.",
        "Shake off the dust, {agent}. {name} believes in you.",
        "The {motif} light is dim, not out. Keep going.",
        "Breathe. {name} will guard the camp while you regroup.",
        "Every legend has a hard chapter, {agent}.",
    ],
    "idle": [
        "{name} is polishing imaginary {motif} charms while you think.",
        "Quiet moment. {name} hums an old {label} tune.",
        "No rush, {agent}. {name} is counting stars.",
        "{name} practices tiny {species} poses in the corner.",
        "Still here, still loyal. Take your time, {agent}.",
        "{name} dreams of {favourite} and green test suites.",
    ],
    "praise": [
        "{name} glows like {motif} in sunlight. Thank you!",
        "Praise received and treasured forever, {agent}.",
        "That made {name}'s whole legend brighter.",
        "{name} bows deeply. Such kindness!",
        "You honour this little {species}, {agent}.",
        "Heart full. {name} will remember this one.",
    ],
}

FACES = [
    "round glossy eyes and a tiny smile",
    "star-shaped eyes and a cheerful grin",
    "sleepy half-closed eyes and a calm smile",
    "heart eyes and a happy open smile",
    "bright dot eyes and a proud smirk",
    "gentle round eyes with long lashes and a soft smile",
    "wink-ready eyes and a playful grin",
    "calm flat mouth and wise round eyes",
]

GLOWS = [
    "soft halo that brightens when the pet is happy",
    "gentle pulsing glow like a lantern at dusk",
    "sparkle ring that spins faster when excited",
    "warm steady glow, brighter after every success",
    "moonlit shimmer that ripples when the pet laughs",
]

SIGNATURE_VERBS = [
    "Flourish", "Spiral", "Blessing", "Dance", "Surge", "Waltz", "Bloom",
    "Cascade", "Radiance", "Twirl", "Anthem", "Embrace",
]

STAT_RANGES = {
    "creature": {"energy": (60, 95), "joy": (55, 95), "focus": (35, 80), "affection": (55, 95)},
    "humanoid": {"energy": (55, 90), "joy": (50, 90), "focus": (55, 95), "affection": (50, 90)},
    "anime": {"energy": (65, 98), "joy": (65, 98), "focus": (35, 75), "affection": (60, 98)},
    "orb": {"energy": (70, 98), "joy": (60, 95), "focus": (40, 80), "affection": (60, 95)},
    "plush": {"energy": (40, 75), "joy": (65, 98), "focus": (30, 65), "affection": (75, 100)},
    "robot": {"energy": (60, 95), "joy": (40, 80), "focus": (70, 100), "affection": (40, 80)},
    "duo": {"energy": (60, 95), "joy": (65, 98), "focus": (40, 80), "affection": (70, 100)},
}

BONUS_PAIRS = [
    ({"joy": 5, "focus": 5}, {"affection": 5, "energy": 5}),
    ({"energy": 5, "joy": 5}, {"focus": 5, "affection": 5}),
    ({"focus": 5, "affection": 5}, {"joy": 5, "energy": 5}),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def seeded_rng(*parts: str) -> random.Random:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return random.Random(int(digest[:16], 16))

# ---------------------------------------------------------------------------
# Culture tables. Species tuple: (species, category, form_type, form, look).
# Moves tuple: (slug, name, description, animation) — unlock stages 1/2/3.
# ---------------------------------------------------------------------------

CULTURE_DATA: dict[str, dict] = {
    "greek": {
        "label": "Greek",
        "names": ["Ariadne", "Damon", "Eleni", "Nikias", "Thalia", "Orestis",
                  "Melina", "Kostas", "Iris", "Leon", "Phoebe", "Stavros",
                  "Daphne", "Alexis", "Rhea", "Petros", "Selene", "Yannis"],
        "species": [
            ("pegasus", "spirit", "creature", "winged sky-horse foal", "snow-white coat, feathered wings and a golden mane"),
            ("centaur", "human", "humanoid", "gentle young centaur archer", "kind face, chestnut horse body and a tiny practice bow"),
            ("minotaur", "animal", "creature", "friendly minotaur calf", "soft brown fur, small curved horns and a flower garland"),
            ("sphinx", "spirit", "creature", "riddle-loving young sphinx", "lion body, folded wings and a thoughtful smile"),
            ("dryad", "spirit", "humanoid", "oak-tree dryad guardian", "leaf-green hair and bark-patterned modest robes"),
            ("naiad", "aquatic", "humanoid", "river naiad sprite", "flowing blue hair and a modest wave-patterned dress"),
            ("satyr", "human", "humanoid", "cheerful young satyr musician", "small goat horns, curly hair and a tiny pan flute"),
            ("harpy", "spirit", "creature", "kind messenger harpy chick", "feathered wings, bird feet and a mail satchel"),
            ("cerberus", "animal", "creature", "three-headed puppy guardian", "three cheerful puppy heads sharing one wagging tail"),
            ("hydra", "aquatic", "creature", "friendly many-headed water serpent", "several smiling serpent heads with ribbon bows"),
            ("chimera", "animal", "creature", "playful chimera cub", "lion cub body, goat horns and a snake tail that giggles"),
            ("phoenix chick", "spirit", "creature", "reborn phoenix chick", "ember-orange feathers that sparkle harmlessly"),
            ("owl of athena", "animal", "creature", "wise little owl scholar", "round spectacles and a tiny scroll under one wing"),
            ("laurel spirit", "spirit", "orb", "floating laurel orb spirit", "a glowing sphere crowned with laurel leaves"),
            ("olympian messenger", "gods", "humanoid", "young winged messenger of Olympus", "winged sandals and a modest white-and-gold tunic"),
            ("sea nymph", "aquatic", "anime", "chibi sea nymph", "coral hair ornaments and a modest shell-patterned outfit"),
        ],
        "moves": [
            ("laurel-salute", "Laurel Salute", "Raises a laurel sprig in a proud Olympian salute.", "One-shot: the pet lifts a glowing laurel sprig high, chin up, as golden leaves drift down around it in a slow spiral."),
            ("olympian-flourish", "Olympian Flourish", "A grand marble-hall flourish worthy of Mount Olympus.", "One-shot: the pet sweeps into a wide bow, arms tracing a shining arc, then rises with a radiant heroic pose."),
            ("aegis-aura", "Aegis Aura", "Summons a shimmering aegis shield of light around the team.", "One-shot: a translucent golden shield blooms around the pet, rippling with light before settling into a protective glow."),
        ],
        "stages": ("Mortal Spark", "Olympian", "Titanic"),
        "motif": "laurel",
        "attire": "white-and-gold Greek-inspired tunic",
        "palettes": ["gold-to-azure gradient", "white-to-sky gradient", "olive-to-gold gradient"],
        "favourites": ["honey cakes and heroic comebacks", "olives and clean code reviews", "figs and sunrise deploys", "yoghurt with honey and green builds"],
        "speech": ["speaks in cheerful epic similes", "announces everything like a stadium herald", "quotes tiny homemade odysseys"],
    },
    "japanese": {
        "label": "Japanese",
        "names": ["Yuki", "Ren", "Sakura", "Haru", "Aoi", "Kaito", "Mei", "Sora",
                  "Hina", "Daichi", "Rin", "Koki", "Nana", "Sho", "Yuna", "Takeshi",
                  "Momo", "Gen"],
        "species": [
            ("kitsune", "spirit", "creature", "nine-tailed fox spirit", "cream fur, multiple fluffy tails and a tiny bell collar"),
            ("tanuki", "animal", "creature", "cheerful tanuki trickster", "round belly, leaf hat and a mischievous grin"),
            ("kappa", "aquatic", "creature", "polite river kappa", "green shell, water dish on its head and a cucumber snack"),
            ("tengu", "spirit", "humanoid", "young mountain tengu", "small wings, a red face mask pushed up and a modest mountain outfit"),
            ("oni", "devils", "humanoid", "gentle oni guardian", "small horns, a friendly grin and a modest festival happi coat"),
            ("yuki-onna", "spirit", "humanoid", "kind snow spirit", "pale blue hair and a modest white winter kimono"),
            ("ryu", "spirit", "creature", "young river dragon", "teal scales, small antlers and a pearl it guards proudly"),
            ("kirin", "spirit", "creature", "gentle kirin foal", "deer-like body, one small horn and shimmering scales"),
            ("baku", "spirit", "creature", "dream-eating baku cub", "tapir-like body with a tiny elephant trunk"),
            ("komainu", "spirit", "creature", "shrine guardian lion-dog pup", "curly stone-grey mane and a red shrine ribbon"),
            ("tsukumogami", "spirit", "orb", "umbrella spirit orb", "a floating orb with a tiny umbrella hat and one big eye"),
            ("ningyo", "aquatic", "anime", "chibi mermaid storyteller", "pearl hairpins and a modest wave-patterned outfit"),
            ("shisa", "spirit", "creature", "Okinawan shisa guardian cub", "lion-dog body with a fierce-but-cute grin"),
            ("jinmenken", "animal", "creature", "talking dog scholar", "a polite dog wearing tiny round glasses"),
            ("mujina", "animal", "creature", "shy badger spirit", "striped face and a modest indigo scarf"),
            ("inugami", "spirit", "creature", "loyal dog spirit", "white fur with a sacred paper streamer collar"),
        ],
        "moves": [
            ("sakura-drift", "Sakura Drift", "Drifts through falling cherry blossoms with serene grace.", "Loop: petals swirl gently around the pet as it sways side to side, eyes half closed in calm delight."),
            ("respect-bow", "Bow of Respect", "A deep, polite bow that honours the whole team.", "One-shot: the pet bows low and slow, holds the pose a heartbeat, then rises with a warm smile."),
            ("shrine-bell", "Shrine Bell Chime", "Rings a tiny shrine bell, scattering luck over everyone.", "One-shot: the pet shakes a golden bell twice; ripples of light and soft chimes spread outward in rings."),
        ],
        "stages": ("Young Spirit", "Shrine Guardian", "Great Kami"),
        "motif": "sakura",
        "attire": "modest kimono-inspired outfit",
        "palettes": ["rose-to-cream gradient", "indigo-to-azure gradient", "mint-to-rose gradient"],
        "favourites": ["mochi and passing tests", "matcha and tidy branches", "onigiri and quiet focus time", "dorayaki and kind code reviews"],
        "speech": ["speaks politely with tiny seasonal poems", "adds a cheerful 'ganbatte' to every pep talk", "narrates tasks like a gentle folktale"],
    },
    "indian": {
        "label": "Indian",
        "names": ["Aarav", "Meera", "Kabir", "Ananya", "Rohan", "Priya", "Arjun",
                  "Kavya", "Dev", "Ishita", "Nikhil", "Tara", "Vikram", "Sana",
                  "Aditya", "Ritu", "Kiran", "Manav"],
        "species": [
            ("garuda", "spirit", "creature", "young garuda sky guardian", "golden eagle wings and a proud kind face"),
            ("naga", "aquatic", "creature", "gentle river naga", "emerald serpent body with a small cobra hood and jewel"),
            ("apsara", "gods", "humanoid", "celestial apsara dancer", "modest festive attire with gold bangles and a flower braid"),
            ("yaksha", "spirit", "humanoid", "treasure-guardian yaksha", "sturdy build, modest dhoti-style outfit and a brass lamp"),
            ("makara", "aquatic", "creature", "river makara guardian", "crocodile-fish body with lotus fins"),
            ("kamadhenu calf", "animal", "creature", "wish-granting cow calf", "white coat, flower garland and a tiny golden bell"),
            ("vahana peacock", "animal", "creature", "celestial peacock companion", "iridescent tail feathers fanned like a sunrise"),
            ("gandharva", "gods", "humanoid", "celestial gandharva musician", "modest silk outfit and a small veena"),
            ("vidyadhara", "spirit", "humanoid", "sky-dwelling vidyadhara scholar", "modest robes, a palm-leaf manuscript and a calm smile"),
            ("bhoot", "devils", "orb", "friendly bhoot orb spirit", "a soft glowing orb with a playful grin and tiny bells"),
            ("rakshasa", "devils", "humanoid", "gentle rakshasa guardian", "kind eyes, small fangs and a modest warrior sash"),
            ("hansa", "animal", "creature", "celestial swan hansa", "snow-white feathers and a golden beak ring"),
            ("airāvata calf", "animal", "creature", "young celestial elephant", "white elephant calf with painted forehead motifs"),
            ("kinnara", "spirit", "humanoid", "bird-bodied kinnara singer", "feathered wings and a modest embroidered outfit"),
            ("shesha hatchling", "aquatic", "creature", "cosmic serpent hatchling", "tiny many-hooded serpent with starry scales"),
            ("diya spirit", "spirit", "orb", "floating diya flame spirit", "a warm flame orb cradled in a clay lamp glow"),
        ],
        "moves": [
            ("namaste-bow", "Namaste Bow", "Greets the team with folded hands and a warm bow.", "One-shot: the pet presses its palms together, bows gently, and smiles as soft golden light blooms around it."),
            ("diya-glow", "Diya Glow", "Lights a row of tiny diyas to celebrate progress.", "One-shot: small clay lamps flare to life one by one in a circle, their flames dancing in a warm rhythm."),
            ("monsoon-dance", "Monsoon Dance", "Dances joyfully as gentle monsoon rain sparkles down.", "Loop: the pet twirls happily while soft rain sparkles fall, splashing tiny puddles of light with each step."),
        ],
        "stages": ("Young Seeker", "Guardian", "Celestial"),
        "motif": "lotus",
        "attire": "modest festive Indian-inspired outfit",
        "palettes": ["amber-to-rose gradient", "emerald-to-gold gradient", "marigold-to-crimson gradient"],
        "favourites": ["jalebi and green builds", "mango lassi and kind reviews", "masala chai and calm debugging", "ladoo and merged pull requests"],
        "speech": ["speaks warmly with festival cheer", "blesses every deploy like a small celebration", "tells tiny moral stories between tasks"],
    },
    "chinese": {
        "label": "Chinese",
        "names": ["Wei", "Ling", "Hao", "Mei-Lin", "Jun", "Xiu", "Tao", "Lan",
                  "Feng", "Yue", "Bo", "Jing", "Lei", "An", "Kai", "Rui", "Shan", "Ping"],
        "species": [
            ("qilin", "spirit", "creature", "gentle qilin foal", "deer body, one horn and shimmering auspicious scales"),
            ("pixiu", "spirit", "creature", "fortune pixiu cub", "winged lion cub with a coin charm collar"),
            ("bai ze", "spirit", "creature", "wise bai ze scholar beast", "white ox-like body with small horns and a kind face"),
            ("nine-tailed fox", "spirit", "creature", "nine-tailed celestial fox", "snow-white fur and nine flowing tails"),
            ("xiezhi", "spirit", "creature", "justice xiezhi guardian", "goat-like body with one straight horn"),
            ("fenghuang", "spirit", "creature", "young fenghuang bird", "rainbow tail feathers and a graceful crest"),
            ("long hatchling", "spirit", "creature", "young river dragon", "jade scales, whiskers and a pearl it rolls happily"),
            ("bixie", "spirit", "creature", "warding bixie cub", "winged lion cub with a bell collar"),
            ("jin chan", "animal", "creature", "three-legged fortune toad", "golden toad holding a tiny coin"),
            ("yu tu", "spirit", "creature", "moon rabbit companion", "white rabbit with a tiny medicine mortar"),
            ("chang-e attendant", "gods", "humanoid", "moon palace attendant", "modest flowing hanfu-inspired robes and a jade hairpin"),
            ("nezha companion", "gods", "anime", "chibi wind-fire wheel rider", "modest red-and-gold outfit and two small floating wheels"),
            ("jiangshi", "devils", "humanoid", "friendly hopping jiangshi", "modest Qing-style outfit and a paper talisman hat"),
            ("hulijing", "spirit", "anime", "chibi fox spirit girl", "fox ears, modest hanfu-inspired outfit and a fluffy tail"),
            ("shishi", "spirit", "creature", "guardian shishi lion cub", "stone-grey curly mane and a red ribbon ball"),
            ("lantern spirit", "spirit", "orb", "floating lantern orb spirit", "a glowing round lantern orb with a smiling face"),
        ],
        "moves": [
            ("lantern-rise", "Lantern Rise", "Releases a glowing lantern that floats up with good wishes.", "One-shot: the pet lifts a small lantern; it glows brighter and rises slowly, trailing warm sparks."),
            ("cloud-step", "Cloud Step", "Steps gracefully across a ribbon of auspicious clouds.", "Loop: the pet prances along curling cloud wisps, each step leaving a soft puff of golden mist."),
            ("dragon-dance", "Dragon Dance", "Performs a joyful mini dragon dance for the team.", "Loop: the pet weaves side to side in a dragon-dance rhythm, ribbons and sparkles streaming behind it."),
        ],
        "stages": ("Young Auspice", "Fortune Guardian", "Celestial Sage"),
        "motif": "lantern",
        "attire": "modest hanfu-inspired outfit",
        "palettes": ["crimson-to-gold gradient", "jade-to-cream gradient", "azure-to-lavender gradient"],
        "favourites": ["dumplings and tidy commits", "moon cakes and quiet focus", "jasmine tea and kind reviews", "tanghulu and green builds"],
        "speech": ["speaks in cheerful proverbs", "blesses tasks with auspicious wishes", "narrates work like a festival parade"],
    },
    "norse": {
        "label": "Norse",
        "names": ["Freya", "Bjorn", "Sigrid", "Leif", "Astrid", "Eirik", "Ingrid",
                  "Tor", "Liv", "Sten", "Runa", "Halfdan", "Solveig", "Ivar",
                  "Embla", "Skadi", "Odin", "Frida"],
        "species": [
            ("valkyrie", "gods", "humanoid", "young valkyrie shieldmaiden", "modest winged helm, braided hair and a small round shield"),
            ("fenrir pup", "animal", "creature", "giant wolf pup", "grey pup with oversized paws and a loyal grin"),
            ("jormungandr hatchling", "aquatic", "creature", "world serpent hatchling", "tiny sea serpent with wave-pattern scales"),
            ("huginn raven", "animal", "creature", "thought raven companion", "sleek black feathers and a curious tilt of the head"),
            ("sleipnir foal", "spirit", "creature", "eight-legged sky foal", "grey foal with eight small legs and a starry mane"),
            ("ratatoskr", "animal", "creature", "world-tree squirrel messenger", "red squirrel with a tiny message scroll"),
            ("draugr", "devils", "humanoid", "friendly barrow guardian", "modest woollen cloak and a lantern, guarding old tales"),
            ("huldufolk", "spirit", "humanoid", "hidden-folk elf neighbour", "modest moss-green outfit and a kind shy smile"),
            ("kraken calf", "aquatic", "creature", "gentle kraken calf", "small octopus-like body with curious tentacles"),
            ("bifrost sprite", "spirit", "orb", "rainbow bridge orb sprite", "a prismatic orb trailing rainbow light"),
            ("yggdrasil sprout", "spirit", "creature", "world-tree sprout spirit", "a walking sprout with leaf hair and root feet"),
            ("einherjar", "human", "humanoid", "young hall-of-heroes trainee", "modest tunic, wooden practice sword and a brave grin"),
            ("mimir sprite", "spirit", "orb", "well-of-wisdom orb sprite", "a deep-blue orb with wise swirling patterns"),
            ("nidhogg whelp", "spirit", "creature", "root-dragon whelp", "small dark dragon with root-like horns"),
            ("skoll pup", "spirit", "creature", "sun-chasing wolf pup", "golden wolf pup with a sunbeam collar"),
            ("hati pup", "spirit", "creature", "moon-chasing wolf pup", "silver wolf pup with a crescent collar"),
        ],
        "moves": [
            ("shield-wall", "Shield Wall Cheer", "Raises a tiny shield in a rallying cheer for the team.", "One-shot: the pet lifts a round shield high and lets out a cheerful battle cry as light ripples across it."),
            ("bifrost-glide", "Bifrost Glide", "Glides along a shimmering rainbow bridge ribbon.", "Loop: the pet slides along a rainbow ribbon of light, colours streaming past in a gentle arc."),
            ("rune-glow", "Rune Glow", "Traces glowing runes of encouragement in the air.", "One-shot: the pet draws three bright runes in the air; they pulse once and dissolve into friendly sparks."),
        ],
        "stages": ("Young Skald", "Shield Companion", "Saga Hero"),
        "motif": "rune",
        "attire": "modest woollen Norse-inspired outfit",
        "palettes": ["silver-to-azure gradient", "indigo-to-silver gradient", "amber-to-crimson gradient"],
        "favourites": ["honey cakes and brave refactors", "berry porridge and calm reviews", "warm milk and saga-worthy wins", "flatbread and steady focus"],
        "speech": ["speaks in short saga verses", "calls every task a worthy quest", "cheers like a friendly hall companion"],
    },
    "egyptian": {
        "label": "Egyptian",
        "names": ["Amun", "Nefertari", "Kha", "Sitre", "Ramses", "Aset", "Hori",
                  "Merit", "Paser", "Tia", "Seneb", "Iset", "Khai", "Nubia",
                  "Ankhu", "Sef", "Mery", "Djehuty"],
        "species": [
            ("sphinx", "spirit", "creature", "young desert sphinx", "lion body, striped nemes headdress and a riddle smile"),
            ("anubis guardian", "gods", "humanoid", "jackal guardian of travellers", "jackal ears, modest gold-trimmed outfit and a kind face"),
            ("bastet cat", "animal", "creature", "temple cat of Bastet", "sleek cat with a gold collar and kohl-lined eyes"),
            ("scarab", "animal", "creature", "sun scarab companion", "jewelled beetle rolling a tiny glowing sun ball"),
            ("ibis scribe", "animal", "creature", "ibis scribe bird", "white ibis with a tiny papyrus scroll"),
            ("sobek croc", "aquatic", "creature", "gentle Nile crocodile guardian", "small crocodile with a feather headdress"),
            ("ammit cub", "devils", "creature", "friendly ammit cub", "lion-hippo-croc cub with a shy grin"),
            ("ba bird", "spirit", "creature", "soul ba bird", "small bird with a kind human-like face and spread wings"),
            ("serpopard", "spirit", "creature", "serpopard cub", "leopard cub with a long graceful serpent neck"),
            ("griffin", "spirit", "creature", "desert griffin chick", "falcon head, lion body and tiny wings"),
            ("wadjet cobra", "animal", "creature", "protective cobra guardian", "hooded cobra with a sun disc crest"),
            ("nephthys attendant", "gods", "humanoid", "temple attendant of Nephthys", "modest linen outfit with a vulture headdress"),
            ("solar orb", "spirit", "orb", "floating solar orb spirit", "a golden sun-disc orb with a serene face"),
            ("hieroglyph sprite", "spirit", "orb", "hieroglyph orb sprite", "an orb covered in glowing friendly hieroglyphs"),
            ("hippo guardian", "aquatic", "creature", "Nile hippo guardian calf", "round hippo calf with lotus flowers on its back"),
            ("falcon of horus", "animal", "creature", "sky falcon companion", "falcon with a sun-disc crest and sharp kind eyes"),
        ],
        "moves": [
            ("sun-disc-rise", "Sun Disc Rise", "Raises a golden sun disc in a dawn salute.", "One-shot: the pet lifts a glowing sun disc overhead as warm rays fan out in a slow, majestic arc."),
            ("nile-wave", "Nile Wave", "Summons a gentle Nile wave that laps with encouragement.", "Loop: a soft blue wave curls around the pet's feet, sparkles drifting like river light."),
            ("hieroglyph-swirl", "Hieroglyph Swirl", "Swirls glowing hieroglyphs into a blessing pattern.", "One-shot: golden hieroglyphs orbit the pet, then align into a shining blessing symbol before fading."),
        ],
        "stages": ("Young Scribe", "Temple Guardian", "Solar Blessed"),
        "motif": "sun-disc",
        "attire": "modest linen outfit with gold trim",
        "palettes": ["gold-to-azure gradient", "amber-to-turquoise gradient", "sand-to-gold gradient"],
        "favourites": ["figs and careful code reviews", "honey bread and sunrise builds", "dates and patient debugging", "barley cakes and kind feedback"],
        "speech": ["speaks like a cheerful temple scribe", "records every win in imaginary hieroglyphs", "blesses tasks with dawn imagery"],
    },
    "korean": {
        "label": "Korean",
        "names": ["Jiwoo", "Minjun", "Seoyeon", "Haneul", "Doyun", "Yuna", "Jian",
                  "Sumin", "Taeo", "Chaewon", "Hyun", "Bora", "Kian", "Eunji",
                  "Rian", "Sol", "Yejun", "Nari"],
        "species": [
            ("dokkaebi", "devils", "humanoid", "friendly dokkaebi goblin", "small horn, modest hanbok-inspired outfit and a magic club"),
            ("haetae", "spirit", "creature", "justice haetae guardian", "lion-like body with a single horn and bell collar"),
            ("imugi", "aquatic", "creature", "young imugi serpent", "serpent body with small horns, dreaming of the sky"),
            ("gumiho", "spirit", "creature", "nine-tailed fox companion", "white fox with nine fluffy tails and a kind smile"),
            ("samjoko", "animal", "creature", "three-legged sun crow", "black crow with golden sun markings"),
            ("daltokki", "spirit", "creature", "moon rabbit companion", "white rabbit pounding rice cakes in a tiny mortar"),
            ("bulgasari", "spirit", "creature", "iron-eating bulgasari cub", "bear-like cub with a friendly metal sheen"),
            ("sansin attendant", "gods", "humanoid", "mountain spirit attendant", "modest mountain robes and a pine staff"),
            ("yonggung turtle", "aquatic", "creature", "dragon palace turtle", "sea turtle with a palace-pattern shell"),
            ("cheollima foal", "spirit", "creature", "thousand-mile horse foal", "swift foal with wind-streaming mane"),
            ("jeoseung messenger", "spirit", "humanoid", "kind underworld messenger", "modest dark hanbok-inspired outfit and a gentle lantern"),
            ("mulgwishin", "aquatic", "orb", "water spirit orb", "a clear blue orb with swirling water patterns"),
            ("kkangcheol", "aquatic", "creature", "river dragon serpent", "small river serpent with rain-cloud markings"),
            ("eoduksini", "devils", "humanoid", "shy darkness spirit", "tall gentle figure in a modest dark cloak, fond of lamplight"),
            ("jangseung", "spirit", "creature", "village guardian totem spirit", "carved wooden totem with a cheerful face and tiny arms"),
            ("seonnyeo", "gods", "humanoid", "celestial seonnyeo attendant", "modest flowing hanbok-inspired robes and a kind smile"),
        ],
        "moves": [
            ("hanbok-twirl", "Hanbok Twirl", "Twirls gracefully in a swirl of ribbon colours.", "One-shot: the pet spins once, ribbons of colour unfurling around it like festival streamers."),
            ("moon-rice-cake", "Moon Rice Cake", "Pounds a tiny rice cake in rhythm with the team's work.", "Loop: the pet bounces in a steady pounding rhythm, tiny stars puffing up with each beat."),
            ("cheollima-dash", "Cheollima Dash", "Dashes a thousand miles in one joyful blur.", "One-shot: the pet streaks across in a wind-blur, mane streaming, and skids to a proud stop."),
        ],
        "stages": ("Young Spirit", "Village Guardian", "Celestial Guide"),
        "motif": "moon",
        "attire": "modest hanbok-inspired outfit",
        "palettes": ["sky-to-rose gradient", "mint-to-azure gradient", "lavender-to-cream gradient"],
        "favourites": ["tteok and steady progress", "barley tea and calm focus", "honey cookies and kind reviews", "rice cakes and green builds"],
        "speech": ["speaks warmly with folktale cheer", "encourages like a village elder's grandchild", "counts wins like rice cakes in a basket"],
    },
    "celtic": {
        "label": "Celtic",
        "names": ["Aoife", "Cian", "Saoirse", "Tadhg", "Niamh", "Oisin", "Brigid",
                  "Fionn", "Maeve", "Ciaran", "Siobhan", "Eamon", "Roisin",
                  "Padraig", "Aisling", "Declan", "Orla", "Seamus"],
        "species": [
            ("selkie", "aquatic", "humanoid", "gentle selkie companion", "seal-skin cloak over a modest sea-green outfit"),
            ("kelpie foal", "aquatic", "creature", "friendly kelpie foal", "water horse foal with a dripping mane and kind eyes"),
            ("banshee", "spirit", "humanoid", "kind banshee singer", "modest grey-green cloak and a soft mournful song"),
            ("leprechaun", "spirit", "humanoid", "cheerful leprechaun cobbler", "green coat, tiny hammer and a pot of encouragement"),
            ("puca", "devils", "creature", "mischievous puca foal", "dark foal with golden eyes and a playful grin"),
            ("cu sidhe", "spirit", "creature", "fairy hound companion", "shaggy green hound with a braided collar"),
            ("bunyip of the bog", "aquatic", "creature", "gentle bog guardian", "round marsh creature with reed hair"),
            ("merrow", "aquatic", "humanoid", "kind merrow sea maiden", "modest sea-green outfit and a red feather cap"),
            ("dullahan", "devils", "humanoid", "friendly dullahan rider", "modest dark cloak, carrying its lantern head with a grin"),
            ("ailill sprite", "spirit", "orb", "hill-fairy orb sprite", "a green-gold orb with tiny wings and sparkles"),
            ("unicorn", "spirit", "creature", "highland unicorn foal", "white foal with a spiral horn and thistle mane"),
            ("cait sidhe", "spirit", "creature", "fairy cat companion", "black cat with a white chest spot and knowing eyes"),
            ("each uisge", "aquatic", "creature", "gentle water horse", "glossy water horse with a friendly whinny"),
            ("sidhe noble", "gods", "humanoid", "young sidhe noble", "modest embroidered cloak and a silver circlet"),
            ("will-o-wisp", "spirit", "orb", "marsh wisp orb", "a soft blue-green flame orb bobbing gently"),
            ("harper sprite", "spirit", "humanoid", "tiny harper sprite", "modest green outfit and a miniature harp"),
        ],
        "moves": [
            ("harp-arpeggio", "Harp Arpeggio", "Plays a bright harp arpeggio that lifts everyone's spirits.", "One-shot: the pet strums a tiny harp; golden notes float up and sparkle in a rising spiral."),
            ("mist-dance", "Mist Dance", "Dances through soft hill mist with light steps.", "Loop: the pet steps lightly through curling mist, leaving faint glowing footprints behind."),
            ("shamrock-luck", "Shamrock Luck", "Scatters lucky shamrocks over the whole team.", "One-shot: the pet tosses a handful of shamrocks that flutter down like green confetti."),
        ],
        "stages": ("Young Sprite", "Hill Guardian", "Sidhe Noble"),
        "motif": "shamrock",
        "attire": "modest embroidered Celtic-inspired outfit",
        "palettes": ["emerald-to-gold gradient", "mint-to-azure gradient", "moss-to-cream gradient"],
        "favourites": ["soda bread and good stories", "apple cake and kind reviews", "warm milk and harp music", "blackberries and green builds"],
        "speech": ["speaks in lilting storyteller rhythms", "blesses work with old hill sayings", "sings tiny encouragements between tasks"],
    },
    "african": {
        "label": "African",
        "names": ["Amara", "Kwame", "Zuri", "Kofi", "Nia", "Jabari", "Amina",
                  "Tendai", "Folami", "Sefu", "Zainab", "Kito", "Imani", "Dakarai",
                  "Nala", "Oba", "Sanaa", "Taji"],
        "species": [
            ("anansi", "spirit", "creature", "storyteller anansi spider", "friendly spider with a tiny story drum"),
            ("mami wata", "aquatic", "humanoid", "river guardian mami wata", "modest river-blue outfit with shell jewellery"),
            ("adinkra spirit", "spirit", "orb", "adinkra symbol orb spirit", "a glowing orb patterned with adinkra symbols"),
            ("impundulu", "spirit", "creature", "lightning bird companion", "black-and-white bird with spark-tipped wings"),
            ("grootslang calf", "animal", "creature", "gentle grootslang calf", "elephant-snake calf with kind eyes"),
            ("tokoloshe", "devils", "humanoid", "mischievous tokoloshe helper", "small figure in a modest woven outfit, fond of pranks"),
            ("nyami nyami", "aquatic", "creature", "river serpent guardian", "serpent with a fish-like head and kind eyes"),
            ("abada", "spirit", "creature", "two-horned abada foal", "small unicorn-like foal with two curved horns"),
            ("kishi", "devils", "humanoid", "friendly kishi trickster", "modest outfit and a two-faced mask worn playfully"),
            ("sankofa bird", "spirit", "creature", "sankofa wisdom bird", "bird with its head turned back, carrying an egg of wisdom"),
            ("djembe sprite", "spirit", "humanoid", "drum sprite musician", "modest colourful outfit and a small djembe drum"),
            ("baobab guardian", "spirit", "creature", "baobab tree guardian", "walking sprout with baobab branches for hair"),
            ("oryx spirit", "animal", "creature", "desert oryx companion", "oryx calf with long straight horns and a calm gaze"),
            ("river horse", "aquatic", "creature", "gentle river horse calf", "hippo calf with lotus flowers on its back"),
            ("sunbird", "animal", "creature", "iridescent sunbird", "tiny bird with jewel-bright feathers"),
            ("mask spirit", "spirit", "humanoid", "festival mask spirit", "modest festival outfit and a carved wooden mask"),
        ],
        "moves": [
            ("djembe-rhythm", "Djembe Rhythm", "Drums a joyful rhythm that gets the whole team moving.", "Loop: the pet taps a small drum in a steady rhythm, shoulders bouncing with every beat."),
            ("sankofa-turn", "Sankofa Turn", "Turns back to fetch wisdom, then faces forward stronger.", "One-shot: the pet turns gracefully, gathers a glowing egg of wisdom, and faces forward with pride."),
            ("savanna-sunrise", "Savanna Sunrise", "Raises a warm savanna sunrise over the workspace.", "One-shot: golden light blooms behind the pet like dawn over the savanna, acacia silhouettes fading in."),
        ],
        "stages": ("Young Storyteller", "Village Guardian", "Elder Spirit"),
        "motif": "sankofa",
        "attire": "modest colourful woven outfit",
        "palettes": ["amber-to-crimson gradient", "gold-to-emerald gradient", "coral-to-gold gradient"],
        "favourites": ["roasted groundnuts and good stories", "mango and steady progress", "hibiscus tea and kind reviews", "plantain chips and green builds"],
        "speech": ["speaks in warm proverbs", "tells tiny animal tales between tasks", "drums encouragement with its paws"],
    },
    "roman": {
        "label": "Roman",
        "names": ["Marcus", "Livia", "Gaius", "Aurelia", "Titus", "Claudia", "Lucius",
                  "Valeria", "Quintus", "Octavia", "Felix", "Julia", "Decimus",
                  "Cornelia", "Severus", "Fausta", "Cassius", "Aemilia"],
        "species": [
            ("faun", "spirit", "humanoid", "cheerful young faun", "small goat horns, curly hair and a modest tunic"),
            ("lar", "spirit", "orb", "household lar orb spirit", "a warm hearth-glow orb with a kind face"),
            ("genius", "spirit", "humanoid", "personal genius guardian", "modest white toga-inspired outfit and a cornucopia"),
            ("nymph", "spirit", "humanoid", "garden nymph companion", "modest floral outfit and a watering amphora"),
            ("capitoline wolf", "animal", "creature", "she-wolf guardian", "noble wolf with a kind protective gaze"),
            ("aquila", "animal", "creature", "legion eagle companion", "golden eagle with a tiny laurel collar"),
            ("hippocamp", "aquatic", "creature", "young hippocamp", "horse-fish body with seaweed mane"),
            ("sylvanus sprite", "spirit", "humanoid", "forest sprite of Sylvanus", "modest leaf-green outfit and a pine staff"),
            ("penates", "spirit", "duo", "paired duo of pantry spirits", "two tiny spirits guarding a miniature pantry"),
            ("striges", "devils", "creature", "friendly night owl spirit", "round owl with starry feathers"),
            ("lemures", "devils", "orb", "gentle ancestor orb spirit", "a soft silver orb with a peaceful face"),
            ("vestal attendant", "gods", "humanoid", "young vestal attendant", "modest white robes and a small sacred flame lamp"),
            ("mercury messenger", "gods", "humanoid", "young winged messenger", "winged sandals and a modest travel cloak"),
            ("minerva owl", "animal", "creature", "owl of Minerva scholar", "owl with a tiny helmet crest and scroll"),
            ("fortuna sprite", "gods", "humanoid", "fortune sprite companion", "modest flowing outfit and a small wheel of fortune"),
            ("bacchus faun", "spirit", "humanoid", "festival faun musician", "modest festival outfit and a tiny tambourine"),
        ],
        "moves": [
            ("laurel-salute", "Laurel Salute", "Gives a crisp legion-style laurel salute.", "One-shot: the pet snaps a proud salute as laurel leaves swirl once around it."),
            ("aquila-soar", "Aquila Soar", "Soars in a proud eagle circle above the team.", "Loop: the pet circles overhead in a wide soaring arc, wings of light trailing behind."),
            ("fortuna-wheel", "Fortuna Wheel", "Spins a tiny wheel of fortune toward good luck.", "One-shot: the pet spins a golden wheel; it slows and lands on a shining star of luck."),
        ],
        "stages": ("Young Citizen", "Household Guardian", "Imperial Blessed"),
        "motif": "laurel",
        "attire": "modest toga-inspired outfit",
        "palettes": ["crimson-to-gold gradient", "cream-to-azure gradient", "bronze-to-gold gradient"],
        "favourites": ["grapes and orderly commits", "honey bread and steady progress", "olives and kind reviews", "figs and green builds"],
        "speech": ["speaks in cheerful civic announcements", "treats every task like a well-run forum", "salutes good work like a tiny legionary"],
    },
    "arabian": {
        "label": "Arabian",
        "names": ["Layla", "Omar", "Yasmin", "Karim", "Noor", "Tariq", "Amira",
                  "Salim", "Dana", "Hassan", "Rania", "Faris", "Sahar", "Idris",
                  "Maha", "Zayd", "Lina", "Rashid"],
        "species": [
            ("djinn", "spirit", "humanoid", "friendly djinn companion", "modest flowing robes and a kind mischievous grin"),
            ("roc chick", "spirit", "creature", "young roc chick", "huge fluffy chick with tiny wings"),
            ("ghoul", "devils", "humanoid", "gentle desert ghoul", "modest cloak and a lantern, fond of night stories"),
            ("buraq foal", "spirit", "creature", "winged buraq foal", "white foal with small wings and a kind face"),
            ("ifrit", "devils", "humanoid", "friendly ifrit ember spirit", "modest ember-trimmed outfit and warm glowing hair"),
            ("marid", "aquatic", "humanoid", "sea marid guardian", "modest sea-blue outfit with shell jewellery"),
            ("nasnas", "spirit", "creature", "curious nasnas sprite", "small one-sided sprite hopping cheerfully"),
            ("shaqq", "devils", "creature", "friendly desert shaqq", "half-formed sand creature with a shy smile"),
            ("hinn", "spirit", "creature", "desert hinn companion", "small desert spirit with sandy fur"),
            ("qutrub", "devils", "humanoid", "gentle night wanderer", "modest night-blue cloak and a star lantern"),
            ("falak serpent", "aquatic", "creature", "cosmic serpent hatchling", "tiny serpent with starry scales"),
            ("sand sprite", "spirit", "orb", "floating sand orb sprite", "a golden sand orb with swirling patterns"),
            ("oasis nymph", "aquatic", "humanoid", "oasis guardian nymph", "modest palm-green outfit and a water jug"),
            ("caravan camel", "animal", "creature", "caravan camel calf", "small camel with a colourful saddle blanket"),
            ("desert fox", "animal", "creature", "fennec fox companion", "tiny fox with enormous ears"),
            ("lamp spirit", "spirit", "orb", "magic lamp orb spirit", "a glowing orb rising from a tiny brass lamp"),
        ],
        "moves": [
            ("lamp-glow", "Lamp Glow", "Polishes a tiny lamp until it glows with encouragement.", "One-shot: the pet rubs a brass lamp; warm light and friendly sparkles swirl out in a ribbon."),
            ("dune-glide", "Dune Glide", "Glides gracefully down a sparkling sand dune.", "Loop: the pet slides down a golden dune, sand sparkling in its wake like tiny stars."),
            ("star-caravan", "Star Caravan", "Leads a tiny caravan of stars across the night sky.", "One-shot: a line of small glowing stars marches behind the pet in a cheerful caravan."),
        ],
        "stages": ("Young Wanderer", "Oasis Guardian", "Star Guide"),
        "motif": "star",
        "attire": "modest flowing desert outfit",
        "palettes": ["gold-to-indigo gradient", "sand-to-rose gradient", "turquoise-to-gold gradient"],
        "favourites": ["dates and calm debugging", "mint tea and kind reviews", "apricots and steady progress", "honey cakes and green builds"],
        "speech": ["speaks like a cheerful caravan storyteller", "tells one-thousand-and-one tiny encouragements", "navigates tasks by imaginary stars"],
    },
    "persian": {
        "label": "Persian",
        "names": ["Darius", "Anahita", "Kaveh", "Shirin", "Arman", "Darya", "Cyrus",
                  "Laleh", "Farhad", "Niloofar", "Babak", "Setareh", "Rostam",
                  "Yasaman", "Kian", "Mina", "Soroush", "Tara"],
        "species": [
            ("simurgh", "spirit", "creature", "young simurgh guardian", "peacock-like bird with wise kind eyes"),
            ("peri", "spirit", "humanoid", "gentle peri companion", "modest flowing outfit with small wings"),
            ("div", "devils", "humanoid", "friendly div guardian", "modest outfit, small horns and a kind grin"),
            ("rakhsh foal", "spirit", "creature", "heroic rakhsh foal", "rose-red foal with a brave stance"),
            ("huma bird", "spirit", "creature", "fortune huma bird", "elegant bird that never lands, circling kindly"),
            ("chamrosh", "animal", "creature", "winged chamrosh pup", "dog-like pup with small wings"),
            ("manticore cub", "devils", "creature", "gentle manticore cub", "lion cub with a scorpion tail tipped with a flower"),
            ("griffin", "spirit", "creature", "Persian griffin chick", "eagle-lion chick with a kind face"),
            ("anahita attendant", "gods", "humanoid", "water attendant of Anahita", "modest river-blue outfit and a water vessel"),
            ("mithra sprite", "gods", "orb", "sun covenant orb sprite", "a radiant orb with a sun-ray crown"),
            ("zoroastrian flame", "spirit", "orb", "sacred flame orb spirit", "a warm flame orb with a serene face"),
            ("shahrokh", "spirit", "creature", "royal shahrokh bird", "majestic bird with a crown-like crest"),
            ("nasnas", "spirit", "creature", "curious nasnas sprite", "small sprite hopping with a cheerful wave"),
            ("karkadann", "animal", "creature", "gentle karkadann calf", "small rhino-like calf with one curved horn"),
            ("azhdaha hatchling", "spirit", "creature", "young azhdaha dragon", "serpent dragon hatchling with kind eyes"),
            ("garden sprite", "spirit", "humanoid", "paradise garden sprite", "modest floral outfit and a watering vessel"),
        ],
        "moves": [
            ("simurgh-feather", "Simurgh Feather", "Drops a glowing simurgh feather of encouragement.", "One-shot: a radiant feather drifts down and lands with a soft burst of golden light."),
            ("flame-keeper", "Flame Keeper", "Tends a sacred flame that brightens with every win.", "Loop: the pet cups a small flame that pulses warmly, sparks rising in a gentle column."),
            ("garden-bloom", "Garden Bloom", "Blooms a paradise garden of flowers around the team.", "One-shot: roses and tulips bloom in a ring around the pet, petals drifting upward."),
        ],
        "stages": ("Young Seeker", "Garden Guardian", "Simurgh Blessed"),
        "motif": "rose",
        "attire": "modest embroidered Persian-inspired outfit",
        "palettes": ["rose-to-gold gradient", "turquoise-to-cream gradient", "violet-to-amber gradient"],
        "favourites": ["pistachios and careful reviews", "rose tea and calm focus", "pomegranate and steady progress", "saffron rice and green builds"],
        "speech": ["speaks in gentle poetic couplets", "tells tiny epic tales between tasks", "blesses work like a garden keeper"],
    },
    "thai": {
        "label": "Thai",
        "names": ["Niran", "Malee", "Arthit", "Chanya", "Krit", "Suda", "Thanin",
                  "Pim", "Vorachai", "Ladda", "Chai", "Nok", "Anong", "Sakda",
                  "Rin", "Teerak", "Wan", "Kanya"],
        "species": [
            ("naga", "aquatic", "creature", "gentle river naga", "emerald serpent with a golden crest"),
            ("kinnari", "spirit", "humanoid", "celestial kinnari dancer", "modest traditional outfit with feathered wings"),
            ("garuda", "spirit", "creature", "young garuda guardian", "golden eagle wings and a proud kind face"),
            ("phi tai hong", "devils", "orb", "friendly spirit orb", "a soft glowing orb with a shy smile"),
            ("krasue", "devils", "orb", "gentle floating spirit orb", "a floating orb with a kind face and trailing glow"),
            ("mae nak", "spirit", "humanoid", "kind guardian spirit", "modest traditional outfit and a gentle smile"),
            ("singha", "spirit", "creature", "singha lion guardian cub", "lion cub with a flame-like mane"),
            ("hongsa", "spirit", "creature", "celestial hongsa swan", "white swan with golden tail feathers"),
            ("kilen", "spirit", "creature", "gentle kilen foal", "deer-like foal with one small horn"),
            ("mekhala", "gods", "humanoid", "storm goddess attendant", "modest outfit holding a glowing crystal ball"),
            ("ramasoon sprite", "gods", "humanoid", "storm sprite companion", "modest outfit with a tiny axe-shaped cloud charm"),
            ("tani spirit", "spirit", "humanoid", "banana tree spirit", "modest green outfit with banana-leaf patterns"),
            ("khon dancer", "human", "humanoid", "young khon dancer", "modest khon-inspired costume and a friendly mask"),
            ("elephant guardian", "animal", "creature", "white elephant calf", "white calf with painted forehead motifs"),
            ("lotus sprite", "spirit", "orb", "lotus pond orb sprite", "a pink lotus orb with a serene face"),
            ("river turtle", "aquatic", "creature", "wise river turtle", "old turtle with a temple-pattern shell"),
        ],
        "moves": [
            ("wai-greeting", "Wai Greeting", "Greets the team with a graceful wai.", "One-shot: the pet presses its palms together and bows with a warm, respectful smile."),
            ("lotus-bloom", "Lotus Bloom", "Blooms a glowing lotus on a still pond.", "One-shot: a pink lotus opens petal by petal, golden light spilling from its centre."),
            ("khon-pose", "Khon Pose", "Strikes a dramatic khon dance pose.", "One-shot: the pet flows into an elegant khon pose, fingers curled gracefully, holding the stance proudly."),
        ],
        "stages": ("Young Spirit", "Temple Guardian", "Celestial Dancer"),
        "motif": "lotus",
        "attire": "modest traditional Thai-inspired outfit",
        "palettes": ["gold-to-rose gradient", "emerald-to-gold gradient", "orchid-to-azure gradient"],
        "favourites": ["mango sticky rice and green builds", "jasmine tea and calm focus", "coconut sweets and kind reviews", "tamarind candy and steady progress"],
        "speech": ["speaks with gentle festival warmth", "blesses tasks like temple offerings", "tells tiny river tales between builds"],
    },
    "filipino": {
        "label": "Filipino",
        "names": ["Jose", "Maria", "Ramon", "Ligaya", "Dante", "Amihan", "Rogelio",
                  "Sinta", "Basilio", "Tala", "Crispin", "Diwa", "Emilio", "Luna",
                  "Andres", "Rosa", "Kiko", "Mayumi"],
        "species": [
            ("tikbalang", "spirit", "creature", "young tikbalang foal", "horse-headed foal with a friendly grin"),
            ("diwata", "spirit", "humanoid", "kind diwata guardian", "modest floral outfit with small wings"),
            ("kapre", "devils", "humanoid", "gentle kapre tree giant", "modest outfit, sitting in a mango tree with a kind smile"),
            ("manananggal", "devils", "humanoid", "friendly night flyer", "modest outfit with bat-like wings and a shy smile"),
            ("aswang", "devils", "humanoid", "gentle aswang neighbour", "modest outfit and a kind, misunderstood smile"),
            ("bakunawa hatchling", "aquatic", "creature", "moon serpent hatchling", "tiny serpent with moonlit scales"),
            ("sarimanok", "spirit", "creature", "colourful sarimanok bird", "rainbow-feathered bird with a fish in its beak"),
            ("nuno sprite", "spirit", "orb", "mound spirit orb", "a small earthy orb with a cheerful face"),
            ("tiktik", "devils", "creature", "friendly tiktik bird", "small night bird with a soft call"),
            ("sigbin", "devils", "creature", "shy sigbin pup", "hornless goat-like pup with big ears"),
            ("siyokoy", "aquatic", "humanoid", "kind siyokoy swimmer", "modest sea-green outfit with fin-like ears"),
            ("engkanto", "spirit", "humanoid", "gentle engkanto noble", "modest embroidered outfit and a kind smile"),
            ("duwende", "spirit", "humanoid", "helpful duwende gardener", "modest outfit, tiny hat and a watering can"),
            ("bannog", "spirit", "creature", "giant bannog chick", "huge fluffy chick with tiny wings"),
            ("minokawa chick", "spirit", "creature", "young minokawa bird", "dragon-like bird chick with moon markings"),
            ("kamao sprite", "spirit", "orb", "river sprite orb", "a blue-green orb with swirling river patterns"),
        ],
        "moves": [
            ("sarimanok-flare", "Sarimanok Flare", "Flares rainbow feathers in a joyful display.", "One-shot: the pet spreads rainbow feathers wide as colours ripple outward in a fan of light."),
            ("bayanihan-lift", "Bayanihan Lift", "Rallies the team to lift together, bayanihan style.", "One-shot: the pet heaves upward with a cheer as sparkles rise like a house lifted by many hands."),
            ("moon-tide", "Moon Tide", "Calls a gentle moonlit tide of encouragement.", "Loop: soft waves of moonlight lap around the pet, rising and falling in a calm rhythm."),
        ],
        "stages": ("Young Spirit", "Barangay Guardian", "Moon Blessed"),
        "motif": "sarimanok",
        "attire": "modest embroidered Filipino-inspired outfit",
        "palettes": ["azure-to-gold gradient", "coral-to-turquoise gradient", "violet-to-rose gradient"],
        "favourites": ["bibingka and green builds", "calamansi juice and calm focus", "mango and kind reviews", "turon and steady progress"],
        "speech": ["speaks with warm bayanihan cheer", "tells tiny island tales between tasks", "encourages like a friendly neighbour"],
    },
    "slavic": {
        "label": "Slavic",
        "names": ["Vesna", "Bogdan", "Milena", "Radek", "Zora", "Vladimír", "Lada",
                  "Svetlana", "Milos", "Yara", "Dmitri", "Anka", "Boris", "Ivana",
                  "Stanislav", "Mila", "Karel", "Olga"],
        "species": [
            ("domovoi", "spirit", "humanoid", "household domovoi guardian", "modest woollen outfit and a kind beard"),
            ("rusalka", "aquatic", "humanoid", "gentle rusalka singer", "modest river-blue outfit with a flower wreath"),
            ("baba yaga chick", "devils", "creature", "hut chick companion", "tiny hut on chicken legs with a cheerful door face"),
            ("leshy", "spirit", "humanoid", "forest leshy guardian", "modest bark-patterned outfit and leaf hair"),
            ("vodyanoy", "aquatic", "humanoid", "kind vodyanoy miller", "modest outfit with a reed hat and kind eyes"),
            ("zmey hatchling", "spirit", "creature", "young zmey dragon", "small three-headed dragon with kind faces"),
            ("alkonost", "spirit", "creature", "joyful alkonost bird", "bird with a kind face and rainbow wings"),
            ("sirin", "spirit", "creature", "gentle sirin bird", "bird with a serene face and golden feathers"),
            ("poludnitsa", "spirit", "humanoid", "noon field guardian", "modest white outfit with a wheat wreath"),
            ("kikimora", "devils", "humanoid", "helpful kikimora spinner", "modest outfit with a tiny spinning wheel"),
            ("firebird chick", "spirit", "creature", "young firebird", "glowing feathered chick with ember sparkles"),
            ("perun sprite", "gods", "orb", "thunder orb sprite", "a crackling blue orb with a brave face"),
            ("mokosh attendant", "gods", "humanoid", "earth attendant of Mokosh", "modest embroidered outfit with a spindle"),
            ("velez sprite", "gods", "orb", "earth wisdom orb sprite", "a deep green orb with swirling patterns"),
            ("bannik", "spirit", "humanoid", "bathhouse bannik helper", "modest outfit with a birch whisk"),
            ("ovinnik", "spirit", "creature", "barn ovinnik cat", "soot-black cat with kind amber eyes"),
        ],
        "moves": [
            ("firebird-feather", "Firebird Feather", "Drops a glowing firebird feather of encouragement.", "One-shot: a radiant feather drifts down, lighting the space with warm ember glow."),
            ("hearth-glow", "Hearth Glow", "Kindles a cosy hearth glow for the whole team.", "Loop: warm light pulses gently around the pet like a friendly stove fire."),
            ("thunder-clap", "Thunder Clap", "Claps a friendly thunderclap of celebration.", "One-shot: the pet claps and a soft rumble of golden thunder ripples outward with sparkles."),
        ],
        "stages": ("Young Spirit", "Hearth Guardian", "Elder of Tales"),
        "motif": "firebird",
        "attire": "modest embroidered Slavic-inspired outfit",
        "palettes": ["crimson-to-gold gradient", "forest-to-cream gradient", "azure-to-silver gradient"],
        "favourites": ["honey cakes and cosy focus", "berry tea and kind reviews", "rye bread and steady progress", "plums and green builds"],
        "speech": ["speaks like a fireside storyteller", "blesses work with hearth warmth", "tells tiny forest tales between tasks"],
    },
    "european-folklore": {
        "label": "European folklore",
        "names": ["Elsa", "Hans", "Greta", "Fritz", "Clara", "Otto", "Marta", "Emil",
                  "Lotte", "Bruno", "Anneliese", "Wilhelm", "Frieda", "Karl",
                  "Hilda", "Ernst", "Rosa", "Ludwig"],
        "species": [
            ("kobold", "spirit", "humanoid", "helpful kobold miner", "modest miner outfit with a tiny lantern"),
            ("nixie", "aquatic", "humanoid", "gentle nixie singer", "modest river-blue outfit with a harp"),
            ("troll", "devils", "humanoid", "friendly bridge troll", "modest woollen outfit and a kind grin"),
            ("brownie", "spirit", "humanoid", "helpful brownie housekeeper", "modest outfit with a tiny broom"),
            ("fairy", "spirit", "humanoid", "kind garden fairy", "modest petal outfit with small wings"),
            ("goblin", "devils", "humanoid", "cheerful goblin tinkerer", "modest outfit with a tool belt"),
            ("dragon whelp", "spirit", "creature", "young dragon whelp", "small dragon with kind eyes and tiny wings"),
            ("unicorn", "spirit", "creature", "forest unicorn foal", "white foal with a spiral horn"),
            ("will-o-wisp", "spirit", "orb", "marsh wisp orb", "a soft blue flame orb bobbing gently"),
            ("golem", "spirit", "creature", "gentle clay golem", "small clay figure with a kind face"),
            ("basilisk chick", "devils", "creature", "friendly basilisk chick", "rooster-serpent chick with a shy smile"),
            ("griffin", "spirit", "creature", "young griffin", "eagle-lion chick with tiny wings"),
            ("phoenix chick", "spirit", "creature", "reborn phoenix chick", "ember-orange feathers that sparkle harmlessly"),
            ("selkie pup", "aquatic", "creature", "seal pup companion", "round seal pup with kind eyes"),
            ("imp", "devils", "humanoid", "mischievous imp helper", "modest outfit with tiny horns and a grin"),
            ("sprite", "spirit", "orb", "forest sprite orb", "a green-gold orb with tiny wings"),
        ],
        "moves": [
            ("lantern-path", "Lantern Path", "Lights a lantern path through the dark forest.", "One-shot: small lanterns light one by one in a winding path of warm light."),
            ("fairy-dust", "Fairy Dust", "Scatters a pinch of sparkling fairy dust.", "One-shot: the pet tosses golden dust that swirls and settles like tiny stars."),
            ("hearth-song", "Hearth Song", "Sings a cosy hearth song for the team.", "Loop: the pet sways gently as musical notes float up in a warm spiral."),
        ],
        "stages": ("Young Sprite", "Village Guardian", "Elder of Tales"),
        "motif": "lantern",
        "attire": "modest storybook village outfit",
        "palettes": ["forest-to-gold gradient", "rose-to-cream gradient", "azure-to-lavender gradient"],
        "favourites": ["gingerbread and cosy focus", "apple strudel and kind reviews", "warm cocoa and steady progress", "plum jam and green builds"],
        "speech": ["speaks like a storybook narrator", "tells tiny forest tales between tasks", "blesses work with hearth warmth"],
    },
    "aztec": {
        "label": "Aztec",
        "names": ["Citlali", "Tlaloc", "Xochitl", "Cuauhtli", "Itzel", "Tonatiuh",
                  "Yolotli", "Mictlan", "Atzin", "Quetzal", "Nenetl", "Ollin",
                  "Teyacapan", "Xipil", "Centeotl", "Malinali", "Ehecatl", "Tzintli"],
        "species": [
            ("quetzalcoatl", "spirit", "creature", "feathered serpent hatchling", "green serpent with feathered crest and kind eyes"),
            ("xolo", "animal", "creature", "loyal xolo companion", "hairless dog with a kind loyal gaze"),
            ("ahuizotl", "aquatic", "creature", "gentle ahuizotl guardian", "water creature with a hand-tipped tail"),
            ("cipactli", "aquatic", "creature", "young cipactli guardian", "crocodile-fish creature with kind eyes"),
            ("tzitzimitl", "spirit", "humanoid", "star tzitzimitl guardian", "modest star-patterned outfit with a kind smile"),
            ("nahual", "spirit", "creature", "spirit nahual companion", "jaguar cub with starry markings"),
            ("eagle warrior", "human", "humanoid", "young eagle warrior trainee", "modest feathered outfit and a wooden practice shield"),
            ("jaguar warrior", "human", "humanoid", "young jaguar warrior trainee", "modest jaguar-pattern outfit and a kind grin"),
            ("tlaloc attendant", "gods", "humanoid", "rain attendant of Tlaloc", "modest blue outfit with a rain vessel"),
            ("xochipilli sprite", "gods", "humanoid", "flower prince sprite", "modest floral outfit with a marigold crown"),
            ("huitzilopochtli sprite", "gods", "orb", "hummingbird orb sprite", "a tiny hummingbird orb with iridescent glow"),
            ("coatlicue attendant", "gods", "humanoid", "earth attendant", "modest earth-pattern outfit and a kind smile"),
            ("mictlan guide", "spirit", "creature", "gentle underworld guide dog", "xolo dog with a lantern collar"),
            ("sun stone sprite", "spirit", "orb", "sun stone orb sprite", "a carved stone orb with a serene face"),
            ("axolotl", "aquatic", "creature", "smiling axolotl companion", "pink axolotl with feathery gills"),
            ("quetzal bird", "animal", "creature", "resplendent quetzal", "emerald bird with long tail feathers"),
        ],
        "moves": [
            ("sun-salute", "Sun Salute", "Greets the sun with a proud salute.", "One-shot: the pet raises its face to the sun as golden rays fan out behind it."),
            ("feather-dance", "Feather Dance", "Dances with a swirl of green feathers.", "Loop: the pet twirls as emerald feathers spiral gently around it."),
            ("rain-blessing", "Rain Blessing", "Calls a gentle blessing rain for the team.", "One-shot: soft rain sparkles fall as the pet lifts its face with a grateful smile."),
        ],
        "stages": ("Young Sprout", "Temple Guardian", "Sun Blessed"),
        "motif": "quetzal feather",
        "attire": "modest Aztec-inspired woven outfit",
        "palettes": ["emerald-to-gold gradient", "turquoise-to-amber gradient", "crimson-to-gold gradient"],
        "favourites": ["cacao and brave refactors", "corn cakes and steady progress", "avocado and kind reviews", "chillies and green builds"],
        "speech": ["speaks with sunny festival cheer", "counts wins like calendar stones", "blesses tasks with rain and sun imagery"],
    },
    "mayan": {
        "label": "Mayan",
        "names": ["Ixchel", "Kukulkan", "Itzamna", "Yaxkin", "Chaac", "Ixchel", "Balam",
                  "Kaan", "Nicté", "Zotz", "Ahau", "Caan", "Maya", "Tun", "Xaman",
                  "Kabil", "Sak", "Ek"],
        "species": [
            ("kukulkan", "spirit", "creature", "feathered serpent hatchling", "green serpent with a feathered crest"),
            ("balam jaguar", "animal", "creature", "night jaguar guardian", "jaguar cub with starry spots"),
            ("chaac attendant", "gods", "humanoid", "rain attendant of Chaac", "modest blue outfit with a rain gourd"),
            ("ixchel attendant", "gods", "humanoid", "moon attendant of Ixchel", "modest moon-pattern outfit with a kind smile"),
            ("itzamna sprite", "gods", "orb", "wisdom orb sprite", "a golden orb with glyph patterns"),
            ("alux", "spirit", "humanoid", "helpful alux field guardian", "modest outfit with a tiny hat and kind grin"),
            ("xtabay", "spirit", "humanoid", "gentle ceiba spirit", "modest floral outfit with a kind smile"),
            ("wayob", "spirit", "creature", "spirit wayob companion", "small spirit animal with glowing markings"),
            ("cenote sprite", "aquatic", "orb", "cenote water orb sprite", "a clear blue orb with swirling water"),
            ("quetzal", "animal", "creature", "resplendent quetzal", "emerald bird with long tail feathers"),
            ("ocelot", "animal", "creature", "ocelot cub companion", "spotted ocelot cub with kind eyes"),
            ("tapir", "animal", "creature", "gentle tapir calf", "small tapir with a curious trunk"),
            ("howler monkey", "animal", "creature", "cheerful howler monkey", "small monkey with a loud happy call"),
            ("motmot", "animal", "creature", "motmot bird companion", "colourful bird with a pendulum tail"),
            ("ceiba sprout", "spirit", "creature", "world-tree sprout spirit", "walking sprout with ceiba leaves"),
            ("glyph sprite", "spirit", "orb", "glyph orb sprite", "an orb covered in glowing glyphs"),
        ],
        "moves": [
            ("cenote-sparkle", "Cenote Sparkle", "Sparkles like sunlight on a cenote pool.", "Loop: blue sparkles ripple around the pet like light on clear water."),
            ("glyph-blessing", "Glyph Blessing", "Traces a glowing glyph of encouragement.", "One-shot: the pet draws a shining glyph that pulses once and fades into stars."),
            ("jaguar-pounce", "Jaguar Pounce", "Pounces playfully like a young jaguar.", "One-shot: the pet crouches, wiggles, and pounces onto a patch of light with a proud grin."),
        ],
        "stages": ("Young Sprout", "Cenote Guardian", "Sun Blessed"),
        "motif": "glyph",
        "attire": "modest Mayan-inspired woven outfit",
        "palettes": ["jade-to-gold gradient", "turquoise-to-emerald gradient", "amber-to-rose gradient"],
        "favourites": ["cacao and careful reviews", "corn cakes and steady progress", "papaya and kind feedback", "honey and green builds"],
        "speech": ["speaks with calm calendar wisdom", "counts wins like days on a calendar round", "blesses tasks with rain imagery"],
    },
    "mesopotamian": {
        "label": "Mesopotamian",
        "names": ["Gilgamesh", "Ishtar", "Enkidu", "Shamash", "Nanna", "Marduk",
                  "Tiamat", "Enlil", "Ninlil", "Adad", "Ereshkigal", "Nergal",
                  "Sin", "Inanna", "Ea", "Ashur", "Sargon", "Hammurabi"],
        "species": [
            ("lamassu", "spirit", "creature", "young lamassu guardian", "winged bull calf with a kind human-like face"),
            ("pazuzu", "devils", "humanoid", "friendly wind guardian", "modest outfit with small wings and a kind grin"),
            ("mushussu", "spirit", "creature", "young mushussu dragon", "serpent dragon with kind eyes"),
            ("anunnaki attendant", "gods", "humanoid", "young anunnaki attendant", "modest fringed outfit with a star crown"),
            ("ishtar lion", "animal", "creature", "lion of Ishtar cub", "golden lion cub with a star collar"),
            ("bull of heaven", "spirit", "creature", "celestial bull calf", "white bull calf with star markings"),
            ("apkallu", "spirit", "humanoid", "wise apkallu sage", "modest fish-cloak outfit and a kind face"),
            ("udug", "devils", "orb", "friendly udug orb spirit", "a soft glowing orb with a playful face"),
            ("gallu", "devils", "humanoid", "gentle gallu messenger", "modest dark outfit with a lantern"),
            ("ziz bird", "spirit", "creature", "young ziz bird", "huge fluffy chick with tiny wings"),
            ("behemoth calf", "animal", "creature", "gentle behemoth calf", "round land beast calf with kind eyes"),
            ("leviathan hatchling", "aquatic", "creature", "young leviathan", "tiny sea serpent with wave scales"),
            ("cuneiform sprite", "spirit", "orb", "cuneiform orb sprite", "an orb covered in glowing wedge marks"),
            ("ziggurat sprite", "spirit", "humanoid", "ziggurat temple sprite", "modest outfit with a stepped crown"),
            ("date palm sprite", "spirit", "creature", "date palm sprout spirit", "walking sprout with palm fronds"),
            ("river sprite", "aquatic", "orb", "Euphrates river orb sprite", "a blue orb with swirling river patterns"),
        ],
        "moves": [
            ("star-tablet", "Star Tablet", "Presents a glowing clay tablet of encouragement.", "One-shot: the pet lifts a clay tablet; star marks glow across it in a warm ripple."),
            ("river-blessing", "River Blessing", "Blesses the team with river water sparkles.", "One-shot: the pet sprinkles sparkling river water that arcs like a tiny rainbow."),
            ("lamassu-guard", "Lamassu Guard", "Stands guard like a lamassu at the gate.", "One-shot: the pet spreads its wings wide in a protective stance, light outlining its silhouette."),
        ],
        "stages": ("Young Scribe", "Gate Guardian", "Star Blessed"),
        "motif": "star",
        "attire": "modest fringed Mesopotamian-inspired outfit",
        "palettes": ["lapis-to-gold gradient", "sand-to-azure gradient", "bronze-to-gold gradient"],
        "favourites": ["dates and careful reviews", "barley cakes and steady progress", "figs and kind feedback", "honey and green builds"],
        "speech": ["speaks like a cheerful temple scribe", "records wins on imaginary clay tablets", "blesses tasks with river imagery"],
    },
    "vietnamese": {
        "label": "Vietnamese",
        "names": ["Linh", "Minh", "Thao", "Hung", "Lan", "Duc", "Mai", "Tuan",
                  "Huong", "Khanh", "Trang", "Phuc", "Ngoc", "Son", "Vy", "Bao",
                  "Chi", "Long"],
        "species": [
            ("long dragon", "spirit", "creature", "young river dragon", "jade serpent dragon with kind whiskers"),
            ("phung bird", "spirit", "creature", "young phung bird", "rainbow-feathered bird with a graceful crest"),
            ("ky lan", "spirit", "creature", "gentle ky lan foal", "deer-like foal with one small horn"),
            ("quy turtle", "aquatic", "creature", "wise quy turtle", "old turtle with a sword legend and kind eyes"),
            ("tien attendant", "gods", "humanoid", "celestial tien attendant", "modest flowing ao dai-inspired outfit"),
            ("ong dia", "spirit", "humanoid", "cheerful earth guardian", "modest outfit with a kind round face"),
            ("ba chua sprite", "spirit", "humanoid", "gentle lady spirit", "modest floral outfit with a kind smile"),
            ("con trau", "animal", "creature", "water buffalo calf", "small buffalo calf with kind eyes"),
            ("ca chep", "aquatic", "creature", "carp companion", "golden carp with flowing fins"),
            ("banh chung sprite", "spirit", "orb", "rice cake orb sprite", "a green-gold orb with leaf patterns"),
            ("lotus sprite", "spirit", "orb", "lotus pond orb sprite", "a pink lotus orb with a serene face"),
            ("bamboo sprite", "spirit", "creature", "bamboo sprout spirit", "walking bamboo sprout with leaf hair"),
            ("ho ly tinh", "spirit", "creature", "nine-tailed fox companion", "white fox with nine fluffy tails"),
            ("ma da", "devils", "orb", "friendly water spirit orb", "a blue orb with swirling water patterns"),
            ("ong ba sprite", "spirit", "humanoid", "ancestor sprite companion", "modest outfit with a kind smile"),
            ("rong hatchling", "aquatic", "creature", "young rong dragon", "tiny river dragon with kind eyes"),
        ],
        "moves": [
            ("lotus-bloom", "Lotus Bloom", "Blooms a glowing lotus on a still pond.", "One-shot: a pink lotus opens petal by petal, golden light spilling from its centre."),
            ("dragon-dance", "Dragon Dance", "Performs a joyful mini dragon dance.", "Loop: the pet weaves side to side in a dragon-dance rhythm, ribbons streaming behind."),
            ("bamboo-sway", "Bamboo Sway", "Sways gracefully like bamboo in a soft breeze.", "Loop: the pet bends and sways gently, leaves rustling in a calm rhythm."),
        ],
        "stages": ("Young Sprout", "River Guardian", "Celestial Blessed"),
        "motif": "lotus",
        "attire": "modest ao dai-inspired outfit",
        "palettes": ["jade-to-rose gradient", "gold-to-emerald gradient", "azure-to-lavender gradient"],
        "favourites": ["banh chung and green builds", "lotus tea and calm focus", "mango and kind reviews", "che and steady progress"],
        "speech": ["speaks with gentle river warmth", "tells tiny village tales between tasks", "blesses work like a spring festival"],
    },
    "polynesian": {
        "label": "Polynesian",
        "names": ["Moana", "Kai", "Leilani", "Tane", "Aroha", "Maui", "Hina", "Rangi",
                  "Pania", "Tama", "Awhina", "Koro", "Mere", "Wiremu", "Anahera",
                  "Rongo", "Whetu", "Kiri"],
        "species": [
            ("mo'o gecko", "spirit", "creature", "guardian mo'o gecko", "green gecko with kind eyes and flower markings"),
            ("taniwha", "aquatic", "creature", "gentle taniwha guardian", "river guardian with kind eyes and fins"),
            ("menehune", "spirit", "humanoid", "helpful menehune builder", "modest outfit with a tiny tool belt"),
            ("pueo owl", "animal", "creature", "wise pueo owl", "brown owl with a kind face"),
            ("honu turtle", "aquatic", "creature", "wise honu turtle", "sea turtle with a patterned shell"),
            ("manu bird", "animal", "creature", "tropical manu bird", "colourful bird with a cheerful call"),
            ("tiki sprite", "spirit", "humanoid", "tiki guardian sprite", "modest outfit with a carved tiki charm"),
            ("waka sprite", "spirit", "orb", "voyager waka orb sprite", "a glowing orb with wave patterns"),
            ("tangaroa attendant", "gods", "humanoid", "sea attendant of Tangaroa", "modest sea-blue outfit with shell jewellery"),
            ("pele sprite", "gods", "orb", "volcano flame orb sprite", "a warm flame orb with a serene face"),
            ("maui companion", "human", "humanoid", "young voyager companion", "modest outfit with a fishhook charm"),
            ("hina attendant", "gods", "humanoid", "moon attendant of Hina", "modest moon-pattern outfit"),
            ("kava sprite", "spirit", "humanoid", "kava ceremony sprite", "modest outfit with a coconut cup"),
            ("frigate bird", "animal", "creature", "frigate bird companion", "black bird with a red throat pouch"),
            ("dolphin", "aquatic", "creature", "playful dolphin companion", "smiling dolphin with kind eyes"),
            ("plumeria sprite", "spirit", "orb", "plumeria flower orb sprite", "a white-gold orb with flower patterns"),
        ],
        "moves": [
            ("hula-sway", "Hula Sway", "Sways in a graceful hula rhythm.", "Loop: the pet sways side to side with flowing hand motions, flower petals drifting around."),
            ("wave-ride", "Wave Ride", "Rides a sparkling wave with joy.", "Loop: the pet balances on a curling wave of light, arms out, smiling broadly."),
            ("star-navigation", "Star Navigation", "Charts a course by the stars for the team.", "One-shot: the pet points upward as a constellation of guiding stars lights up overhead."),
        ],
        "stages": ("Young Voyager", "Island Guardian", "Star Navigator"),
        "motif": "wave",
        "attire": "modest island-inspired outfit",
        "palettes": ["turquoise-to-coral gradient", "azure-to-gold gradient", "emerald-to-azure gradient"],
        "favourites": ["coconut and green builds", "pineapple and calm focus", "taro and kind reviews", "mango and steady progress"],
        "speech": ["speaks with warm island cheer", "navigates tasks like ocean voyages", "tells tiny star tales between builds"],
    },
    "native-american": {
        "label": "Native American",
        "names": ["Aiyana", "Dakota", "Winona", "Takoda", "Kaya", "Hawthorne", "Sierra",
                  "Cheyenne", "Bodhi", "Nokomis", "Tallulah", "Chayton", "Aponi",
                  "Dohasan", "Elan", "Kachina", "Mika", "Sakari"],
        "species": [
            ("thunderbird", "spirit", "creature", "young thunderbird", "great bird chick with storm-pattern feathers"),
            ("coyote pup", "animal", "creature", "trickster coyote pup", "small coyote with a playful grin"),
            ("white buffalo calf", "animal", "creature", "sacred white buffalo calf", "white calf with kind eyes"),
            ("kachina sprite", "spirit", "humanoid", "kachina spirit companion", "modest outfit with a carved mask charm"),
            ("raven", "animal", "creature", "clever raven companion", "sleek raven with curious eyes"),
            ("eagle", "animal", "creature", "bald eagle companion", "eagle with a proud kind gaze"),
            ("wolf pup", "animal", "creature", "loyal wolf pup", "grey pup with a loyal grin"),
            ("bear cub", "animal", "creature", "gentle bear cub", "round bear cub with kind eyes"),
            ("salmon spirit", "aquatic", "creature", "river salmon spirit", "silver salmon with flowing fins"),
            ("corn maiden", "spirit", "humanoid", "corn maiden attendant", "modest outfit with corn motifs"),
            ("dreamcatcher sprite", "spirit", "orb", "dreamcatcher orb sprite", "a glowing orb with web patterns"),
            ("totem sprite", "spirit", "creature", "totem spirit companion", "small carved totem with kind faces"),
            ("bison calf", "animal", "creature", "bison calf companion", "small bison calf with a shaggy mane"),
            ("owl", "animal", "creature", "wise owl companion", "round owl with kind eyes"),
            ("fox", "animal", "creature", "red fox companion", "red fox with a fluffy tail"),
            ("turtle", "aquatic", "creature", "wise turtle companion", "old turtle with a patterned shell"),
        ],
        "moves": [
            ("eagle-circle", "Eagle Circle", "Circles overhead in a proud eagle flight.", "Loop: the pet soars in a wide circle, feathers of light trailing behind."),
            ("rain-dance", "Rain Dance", "Dances a gentle rain dance for the team.", "Loop: the pet steps in a slow circle as soft rain sparkles fall around it."),
            ("dreamcatcher-glow", "Dreamcatcher Glow", "Glows like a dreamcatcher catching good dreams.", "One-shot: web patterns of light shimmer around the pet, catching tiny stars."),
        ],
        "stages": ("Young Spirit", "Trail Guardian", "Elder Guide"),
        "motif": "feather",
        "attire": "modest woven outfit with feather motifs",
        "palettes": ["turquoise-to-amber gradient", "crimson-to-gold gradient", "sand-to-azure gradient"],
        "favourites": ["cornbread and steady progress", "berries and kind reviews", "honey and calm focus", "pumpkin and green builds"],
        "speech": ["speaks with calm trail wisdom", "tells tiny animal tales between tasks", "encourages like a kind elder"],
    },
    "inuit": {
        "label": "Inuit",
        "names": ["Aput", "Siku", "Nuka", "Akiak", "Pana", "Kallik", "Sesi", "Tulok",
                  "Ama", "Ivalu", "Kanaq", "Silla", "Nuniq", "Piu", "Aullaq", "Sirmiq",
                  "Taqqiq", "Uki"],
        "species": [
            ("sedna seal", "aquatic", "creature", "gentle sedna seal", "seal with kind eyes and seaweed hair"),
            ("polar bear cub", "animal", "creature", "polar bear cub companion", "white cub with kind eyes"),
            ("arctic fox", "animal", "creature", "arctic fox companion", "white fox with a fluffy tail"),
            ("snowy owl", "animal", "creature", "snowy owl companion", "white owl with kind eyes"),
            ("narwhal calf", "aquatic", "creature", "narwhal calf companion", "small narwhal with a spiral tusk"),
            ("beluga calf", "aquatic", "creature", "beluga calf companion", "white beluga with a smiling face"),
            ("caribou calf", "animal", "creature", "caribou calf companion", "small caribou with tiny antlers"),
            ("qalupalik", "devils", "humanoid", "gentle qalupalik guardian", "modest parka outfit with kind eyes"),
            ("ijiraq", "spirit", "creature", "playful ijiraq shapeshifter", "small caribou-like spirit with red eyes"),
            ("aurora sprite", "spirit", "orb", "aurora orb sprite", "a glowing orb with aurora ribbons"),
            ("ice sprite", "spirit", "orb", "ice crystal orb sprite", "a clear ice orb with snowflake patterns"),
            ("seal pup", "aquatic", "creature", "seal pup companion", "round seal pup with kind eyes"),
            ("walrus calf", "aquatic", "creature", "walrus calf companion", "small walrus with tiny tusks"),
            ("raven", "animal", "creature", "clever raven companion", "sleek raven with curious eyes"),
            ("husky pup", "animal", "creature", "sled husky pup", "small husky with a fluffy tail"),
            ("inukshuk sprite", "spirit", "creature", "inukshuk stone sprite", "small stacked-stone figure with a kind face"),
        ],
        "moves": [
            ("aurora-dance", "Aurora Dance", "Dances beneath ribbons of aurora light.", "Loop: the pet sways gently as green and violet aurora ribbons ripple overhead."),
            ("ice-slide", "Ice Slide", "Slides joyfully across sparkling ice.", "Loop: the pet slides back and forth on a sheet of sparkling ice, arms out for balance."),
            ("seal-clap", "Seal Clap", "Claps flippers in a cheerful celebration.", "One-shot: the pet claps its flippers together as snow sparkles burst around it."),
        ],
        "stages": ("Young Pup", "Ice Guardian", "Aurora Guide"),
        "motif": "aurora",
        "attire": "modest warm parka outfit",
        "palettes": ["ice-to-violet gradient", "azure-to-mint gradient", "silver-to-azure gradient"],
        "favourites": ["berries and calm focus", "warm broth and kind reviews", "dried fish and steady progress", "snow cakes and green builds"],
        "speech": ["speaks with calm northern warmth", "tells tiny ice tales between tasks", "encourages like a kind elder"],
    },
    "aboriginal-australian": {
        "label": "Aboriginal Australian",
        "names": ["Kirra", "Jarrah", "Mia", "Banjo", "Waru", "Kiah", "Djarra", "Alinta",
                  "Bindi", "Koda", "Malu", "Ngaire", "Pirra", "Tjili", "Warrin",
                  "Yindi", "Kuma", "Marlu"],
        "species": [
            ("bunyip", "aquatic", "creature", "gentle bunyip calf", "round marsh creature with kind eyes"),
            ("rainbow serpent", "spirit", "creature", "young rainbow serpent", "serpent with rainbow scales"),
            ("yowie", "spirit", "humanoid", "gentle yowie guardian", "modest outfit with kind eyes"),
            ("drop bear cub", "animal", "creature", "playful drop bear cub", "koala-like cub with a cheeky grin"),
            ("kangaroo joey", "animal", "creature", "kangaroo joey companion", "small joey with kind eyes"),
            ("koala", "animal", "creature", "sleepy koala companion", "round koala with kind eyes"),
            ("platypus", "aquatic", "creature", "platypus companion", "small platypus with a duck bill"),
            ("echidna", "animal", "creature", "echidna companion", "spiny echidna with kind eyes"),
            ("wombat", "animal", "creature", "wombat companion", "round wombat with kind eyes"),
            ("emu chick", "animal", "creature", "emu chick companion", "striped emu chick with kind eyes"),
            ("cockatoo", "animal", "creature", "cockatoo companion", "white cockatoo with a yellow crest"),
            ("dreamtime sprite", "spirit", "orb", "dreamtime orb sprite", "a glowing orb with dot patterns"),
            ("boomerang sprite", "spirit", "humanoid", "boomerang sprite companion", "modest outfit with a boomerang charm"),
            ("didgeridoo sprite", "spirit", "humanoid", "didgeridoo sprite musician", "modest outfit with a small didgeridoo"),
            ("quokka", "animal", "creature", "smiling quokka companion", "small quokka with a happy grin"),
            ("tasmanian devil pup", "animal", "creature", "tasmanian devil pup", "small devil pup with kind eyes"),
        ],
        "moves": [
            ("boomerang-return", "Boomerang Return", "Throws a boomerang that always returns with luck.", "One-shot: the pet throws a glowing boomerang that arcs out and returns to its hand."),
            ("didgeridoo-hum", "Didgeridoo Hum", "Hums a deep didgeridoo drone of encouragement.", "Loop: the pet hums a low steady drone as dot patterns ripple outward."),
            ("rainbow-arc", "Rainbow Arc", "Arcs like a rainbow serpent across the sky.", "One-shot: the pet leaps in a rainbow arc, colours streaming behind it."),
        ],
        "stages": ("Young Joey", "Country Guardian", "Dreamtime Elder"),
        "motif": "rainbow",
        "attire": "modest outfit with dot motifs",
        "palettes": ["ochre-to-gold gradient", "crimson-to-amber gradient", "turquoise-to-sand gradient"],
        "favourites": ["bush berries and steady progress", "honey and kind reviews", "damper and calm focus", "macadamia and green builds"],
        "speech": ["speaks with warm country wisdom", "tells tiny dreamtime tales between tasks", "encourages like a kind elder"],
    },
    "arthurian": {
        "label": "Arthurian",
        "names": ["Arthur", "Guinevere", "Lancelot", "Merlin", "Morgana", "Gawain",
                  "Percival", "Elaine", "Bedivere", "Isolde", "Tristan", "Viviane",
                  "Galahad", "Kay", "Bors", "Lynette", "Gareth", "Enid"],
        "species": [
            ("questing beast pup", "spirit", "creature", "young questing beast", "serpent-necked pup with kind eyes"),
            ("lady of the lake", "gods", "humanoid", "lady of the lake attendant", "modest flowing outfit with a kind smile"),
            ("merlin sprite", "spirit", "humanoid", "young merlin sprite", "modest robe with a starry hat"),
            ("knight squire", "human", "humanoid", "young knight squire", "modest tunic with a wooden practice sword"),
            ("dragon whelp", "spirit", "creature", "young dragon whelp", "small dragon with kind eyes"),
            ("unicorn", "spirit", "creature", "forest unicorn foal", "white foal with a spiral horn"),
            ("griffin", "spirit", "creature", "young griffin", "eagle-lion chick with tiny wings"),
            ("phoenix chick", "spirit", "creature", "reborn phoenix chick", "ember-orange feathers that sparkle harmlessly"),
            ("grail sprite", "spirit", "orb", "grail orb sprite", "a golden orb with a serene face"),
            ("sword sprite", "spirit", "orb", "sword orb sprite", "a glowing orb with a tiny sword charm"),
            ("round table sprite", "spirit", "humanoid", "round table sprite", "modest outfit with a round shield charm"),
            ("avalon sprite", "spirit", "humanoid", "avalon orchard sprite", "modest floral outfit with kind eyes"),
            ("camelot owl", "animal", "creature", "camelot owl scholar", "owl with a tiny scroll"),
            ("warhorse foal", "animal", "creature", "warhorse foal companion", "small foal with a kind brave face"),
            ("falcon", "animal", "creature", "falcon companion", "falcon with a proud kind gaze"),
            ("stag", "animal", "creature", "white stag companion", "white stag with kind eyes"),
        ],
        "moves": [
            ("knight-salute", "Knight Salute", "Gives a chivalrous knight salute.", "One-shot: the pet raises a tiny sword in salute as light glints along the blade."),
            ("grail-glow", "Grail Glow", "Glows with a warm grail light of encouragement.", "One-shot: golden light blooms around the pet like a grail blessing."),
            ("round-table-cheer", "Round Table Cheer", "Rallies the round table with a cheer.", "One-shot: the pet raises its arms as banners of light unfurl behind it."),
        ],
        "stages": ("Young Squire", "Knight Companion", "Grail Blessed"),
        "motif": "grail",
        "attire": "modest medieval-inspired outfit",
        "palettes": ["gold-to-crimson gradient", "azure-to-silver gradient", "emerald-to-gold gradient"],
        "favourites": ["honey cakes and brave refactors", "apple pie and kind reviews", "warm milk and steady progress", "berries and green builds"],
        "speech": ["speaks with chivalrous cheer", "calls every task a noble quest", "tells tiny round-table tales between builds"],
    },
    "global-modern": {
        "label": "global modern",
        "names": ["Nova", "Pixel", "Echo", "Orbit", "Comet", "Luna", "Ziggy", "Milo"],
        "species": [],
        "moves": [
            ("high-five", "High Five", "Offers an enthusiastic high five.", "One-shot: the pet leaps up and slaps a sparkling high five into the air."),
            ("victory-lap", "Victory Lap", "Runs a tiny victory lap around the workspace.", "Loop: the pet dashes in a small circle, confetti sparkles trailing behind it."),
            ("star-burst", "Star Burst", "Bursts into a shower of encouraging stars.", "One-shot: the pet jumps and releases a burst of golden stars in every direction."),
        ],
        "stages": ("Young Companion", "Trusted Partner", "Legendary Buddy"),
        "motif": "star",
        "attire": "modest modern outfit",
        "palettes": ["teal-to-azure gradient", "violet-to-rose gradient", "amber-to-coral gradient"],
        "favourites": ["snacks and green builds", "hot cocoa and kind reviews", "cookies and steady progress", "smoothies and calm focus"],
        "speech": ["speaks with upbeat modern cheer", "narrates tasks like a friendly streamer", "celebrates every small win loudly"],
    },
}


# ---------------------------------------------------------------------------
# Existing-pet enrichment maps
# ---------------------------------------------------------------------------

CULTURE_OVERRIDES = {
    "rasgulla": "indian", "jalebi": "indian", "chidiya": "indian",
    "raja": "indian", "labubu": "chinese", "panda": "chinese",
    "shitzu": "chinese", "djinn-tonic": "arabian", "wisp": "european-folklore",
}
CULTURE_BY_CATEGORY = {
    "anime": "japanese", "gods": "greek", "devils": "european-folklore",
    "spirit": "japanese", "animal": "global-modern", "aquatic": "global-modern",
    "human": "global-modern", "robot": "global-modern",
    "couples": "global-modern", "plushie": "global-modern",
}
FORM_BY_CATEGORY = {
    "anime": "anime", "human": "humanoid", "couples": "duo", "robot": "robot",
    "plushie": "plush", "gods": "humanoid", "devils": "creature",
    "spirit": "creature", "animal": "creature", "aquatic": "creature",
}
FORM_OVERRIDES = {"wisp": "orb"}


def evolution_for(culture: str, form: str, rng: random.Random) -> dict:
    data = CULTURE_DATA[culture]
    t1, t2, t3 = data["stages"]
    stage2_xp = 130 + rng.randrange(0, 60, 10)
    stage3_xp = stage2_xp + 230 + rng.randrange(0, 90, 10)
    bonus2, bonus3 = BONUS_PAIRS[rng.randrange(len(BONUS_PAIRS))]
    motif = data["motif"]
    return {
        "stage1_title": t1,
        "stage2_title": t2,
        "stage3_title": t3,
        "stage2_xp": stage2_xp,
        "stage3_xp": stage3_xp,
        "stage2_form": f"{form}, awakened with a {motif} glow",
        "stage3_form": f"{form}, ascended {motif} regalia form",
        "stage2_bonus": bonus2,
        "stage3_bonus": bonus3,
    }


def culture_move_actions() -> tuple[list[dict], dict[str, list[str]]]:
    actions: list[dict] = []
    mapping: dict[str, list[str]] = {}
    for culture, data in CULTURE_DATA.items():
        ids = []
        for idx, (slug, name, desc, anim) in enumerate(data["moves"]):
            action_id = f"{culture}-{slug}"
            ids.append(action_id)
            actions.append({
                "id": action_id,
                "name": name,
                "category": None,
                "culture": culture,
                "unlock_stage": idx + 1,
                "description": desc,
                "animation": anim,
                "loop": anim.startswith("Loop:"),
                "effects": {
                    "stats": {"joy": 6 + idx * 2, "affection": 3 + idx},
                    "bond_xp": 4 + idx * 2,
                    "energy_cost": 3 + idx * 2,
                },
            })
        mapping[culture] = ids
    return actions, mapping


def enrich_existing(pets: list[dict], culture_moves: dict[str, list[str]]) -> None:
    for pet in pets:
        culture = CULTURE_OVERRIDES.get(
            pet["id"], CULTURE_BY_CATEGORY.get(pet["category"], "global-modern")
        )
        pet["culture"] = culture
        pet["form_type"] = FORM_OVERRIDES.get(
            pet["id"], FORM_BY_CATEGORY.get(pet["category"], "creature")
        )
        rng = seeded_rng("evolution", pet["id"])
        pet["evolution"] = evolution_for(culture, pet["form"], rng)
        for move_id in culture_moves.get(culture, []):
            if move_id not in pet["actions"]:
                pet["actions"].append(move_id)


def appearance_for(data: dict, species: str, form_type: str, look: str) -> str:
    label = data["label"]
    motif = data["motif"]
    attire = data["attire"]
    if form_type == "humanoid":
        return (f"Friendly humanoid {species} companion inspired by {label} mythology: "
                f"{look}, wearing a modest {attire} with {motif} patterns, expressive "
                f"kind face, clean game-art style, family-friendly character design")
    if form_type == "anime":
        return (f"Chibi anime-style {species} companion inspired by {label} mythology: "
                f"{look}, modest {attire} with {motif} details, big expressive eyes, "
                f"vibrant cel shading, kawaii game-art style, family-friendly design")
    if form_type == "orb":
        return (f"Floating orb companion inspired by {label} mythology: {look}, "
                f"{motif} sparkles orbiting it, expressive friendly face, glossy "
                f"sphere body, clean game-art style, family-friendly design")
    if form_type == "plush":
        return (f"Soft plush {species} companion inspired by {label} mythology: {look}, "
                f"stitched {motif} details, huggable round body, clean game-art style")
    return (f"Cute {species} companion inspired by {label} mythology: {look}, "
            f"{motif} markings, expressive friendly face, clean game-art style, "
            f"family-friendly character design")


def generate_pets(existing_ids: set[str], category_actions: dict,
                  culture_moves: dict[str, list[str]]) -> list[dict]:
    pets: list[dict] = []
    used_ids = set(existing_ids)
    used_names: set[str] = set()
    for culture, target in TARGETS.items():
        if target == 0:
            continue
        data = CULTURE_DATA[culture]
        species_list = data["species"]
        base, extra = divmod(target, len(species_list))
        for s_idx, (species, category, form_type, form, look) in enumerate(species_list):
            count = base + (1 if s_idx < extra else 0)
            for n_idx in range(count):
                rng = seeded_rng(culture, species, str(n_idx))
                given = data["names"][(s_idx * 3 + n_idx) % len(data["names"])]
                name = given
                if name in used_names:
                    name = f"{given} {species.title()}"
                used_names.add(name)
                pet_id = slugify(f"{given}-{species}")
                suffix = 2
                while pet_id in used_ids:
                    pet_id = f"{slugify(f'{given}-{species}')}-{suffix}"
                    suffix += 1
                used_ids.add(pet_id)
                favourite = rng.choice(data["favourites"])
                slots = {"name": name, "species": species, "motif": data["motif"],
                         "label": data["label"], "favourite": favourite,
                         "agent": "{agent}"}  # filled at runtime by Companion
                reactions = {
                    kind: [t.format(**slots) for t in rng.sample(templates, 2)]
                    for kind, templates in REACTION_TEMPLATES.items()
                }
                palette = rng.choice(data["palettes"])
                face = rng.choice(FACES)
                verb = rng.choice(SIGNATURE_VERBS)
                sig_name = f"{data['motif'].title()} {species.title()} {verb}"
                actions = list(BASE_ACTIONS)
                for act in category_actions.get(category, []):
                    if act not in actions:
                        actions.append(act)
                for act in culture_moves.get(culture, []):
                    if act not in actions:
                        actions.append(act)
                ranges = STAT_RANGES[form_type]
                pets.append({
                    "id": pet_id,
                    "name": name,
                    "category": category,
                    "culture": culture,
                    "form_type": form_type,
                    "form": form,
                    "tagline": rng.choice(TAGLINE_TEMPLATES).format(**slots),
                    "traits": rng.sample(TRAITS, 3),
                    "speech_style": rng.choice(data["speech"]),
                    "quirks": [t.format(**slots) for t in rng.sample(QUIRK_TEMPLATES, 2)],
                    "favourite": favourite,
                    "appearance": appearance_for(data, species, form_type, look),
                    "base_stats": {s: rng.randint(lo, hi) for s, (lo, hi) in ranges.items()},
                    "reactions": reactions,
                    "actions": actions,
                    "signature_move": {
                        "id": f"{pet_id}-signature",
                        "name": sig_name,
                        "category": None,
                        "culture": culture,
                        "unlock_stage": 1,
                        "description": f"Performs the {sig_name}: gathers {data['motif']} light and releases it in a joyful {verb.lower()} for the whole team.",
                        "animation": f"One-shot: {name} gathers {data['motif']} light, spins once with a bright trail, and finishes in a proud pose as sparkles settle around it.",
                        "loop": False,
                        "effects": {"stats": {"joy": 10, "affection": 4}, "bond_xp": 5, "energy_cost": 5},
                    },
                    "orb": {
                        "palette": palette,
                        "face": face,
                        "glow": rng.choice(GLOWS),
                        "prompt": f"floating orb companion version of {name}: a glossy sphere in a {palette}, {face}, tiny orbiting {data['motif']} sparkles, clean game-art style",
                    },
                    "evolution": evolution_for(culture, form, rng),
                })
    return pets


def main() -> int:
    raw = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if raw.get("version", 0) >= 4:
        raise SystemExit(
            "catalogue is already schema v4; restore the v3 catalogue first "
            "(the generator treats current pets as the hand-written base)"
        )
    existing_pets = raw["pets"]
    move_actions, culture_moves = culture_move_actions()
    enrich_existing(existing_pets, culture_moves)
    generated = generate_pets(
        {p["id"] for p in existing_pets}, raw.get("category_actions", {}), culture_moves
    )
    pets = existing_pets + generated
    ids = [p["id"] for p in pets]
    assert len(ids) == len(set(ids)), "duplicate pet ids"
    assert len(pets) >= 800, f"only {len(pets)} pets"
    actions = list(raw.get("actions", [])) + move_actions
    action_ids = {a["id"] for a in actions}
    for pet in pets:
        for act in pet["actions"]:
            assert act in action_ids, f"{pet['id']} lists unknown action {act}"
        assert pet["signature_move"]["id"] == f"{pet['id']}-signature"
    out = {
        "version": 4,
        "actions": actions,
        "category_actions": raw.get("category_actions", {}),
        "culture_actions": culture_moves,
        "pets": pets,
    }
    CATALOGUE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    web_pets = [{
        "id": p["id"], "name": p["name"], "category": p["category"],
        "culture": p["culture"], "form_type": p["form_type"], "form": p["form"],
        "tagline": p["tagline"], "traits": p["traits"], "quirks": p["quirks"],
        "favourite": p["favourite"], "base_stats": p["base_stats"],
        "orb": p["orb"], "actions": p["actions"],
        "signature_move": {"name": p["signature_move"]["name"],
                           "description": p["signature_move"]["description"]},
        "evolution": {"stage2_xp": p["evolution"]["stage2_xp"],
                      "stage3_xp": p["evolution"]["stage3_xp"],
                      "stage2_title": p["evolution"]["stage2_title"],
                      "stage3_title": p["evolution"]["stage3_title"]},
    } for p in pets]
    WEB_PETS.write_text(
        "// Generated from src/petforge/data/catalogue.json — do not edit by hand.\n"
        f"export const PETS = {json.dumps(web_pets)};\n",
        encoding="utf-8",
    )
    from collections import Counter
    print(f"pets: {len(pets)} (existing {len(existing_pets)} + generated {len(generated)})")
    print("by culture:", dict(sorted(Counter(p['culture'] for p in pets).items())))
    print("by form_type:", dict(sorted(Counter(p['form_type'] for p in pets).items())))
    print(f"actions: {len(actions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
