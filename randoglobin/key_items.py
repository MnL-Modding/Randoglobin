"""
Key item / ability randomization with logic.

How it works in the game
------------------------
* Abilities (Hammer, Spin Jump, Flame, ...) are flags the game engine checks directly,
  e.g. 0x2002 = Spin Jump. Every room that is entered copies a new "owned" flag into the
  ability flag (`install_ability_sync`), so the abilities you have are always exactly the
  ones you have collected.
* Each ability's original cutscene still turns its own ability on, so the tutorial that
  makes you perform the move can't softlock. That temporary grant is undone as soon as you
  change rooms, and the cutscene additionally grants whatever item was placed there and
  shows a "You got ...!" textbox.
* Door items (the Peach's Castle keys and the Stingler) are granted by setting the flags
  their doors check, so the doors only open once you actually have the item.

How it works in the randomizer
------------------------------
`place_key_items` performs an assumed fill: items are placed one at a time into
locations that are reachable with every item that hasn't been placed yet, so every seed
can always be finished. The rules live in `LOCATIONS` and are meant to be edited as more
of the game is opened up.
"""

import random
from dataclasses import dataclass, field

import mnllib
from mnllib.bis import BIS_ENCODING, FEVENT_PADDING_TEXT_TABLE_ID, LANGUAGE_TABLE_ALIGNMENT

from randoglobin.script_reloc import ScriptRelocator

# -------------------------------------------------------------------------------------------
# flags

# 0xEC00-0xED58 is not used by any vanilla script (it sits between used story flags, so it
# is saved with the rest of them).
OWNED_FLAG_BASE = 0xEC00   # one "owned" flag per ability
LOCATION_FLAG_BASE = 0xEC40  # replacement "location already done" flags
DUMMY_FLAG = 0xEC7F         # vanilla rewards we disable get redirected here

FIELD_INIT_SKIP_ROOMS = {0x0000, 0x0001, 0x0002}  # debug scripts

# testing hooks (never set by the GUI):
# {location key: item key} applied on top of the fill
FORCED_PLACEMENT = {}
# copy the abilities of a save made on an unrandomized ROM into the owned flags, once
MIGRATE_VANILLA_SAVES = False
MIGRATED_FLAG = 0xEC7E

# where "Skip Story" puts the flags it sets when a new game starts (see patch.skip_stuff)
NEW_GAME_SCRIPTS = [(0x01FD, 1), (0x0215, 0)]


@dataclass
class KeyItem:
    key: str              # internal name
    name: str             # display name (spoiler log / textbox)
    ui: str               # TreasureTab checkbox attribute
    ability_flag: int | None = None  # engine-checked ability flag
    inverted: bool = False           # flag value 1 means *not* having the ability (Flame)
    grant_flags: list = field(default_factory=list)  # door items: flags to set when obtained
    progression: bool = True         # False: never needed to reach anything
    index: int = 0

    @property
    def owned_flag(self):
        return OWNED_FLAG_BASE + self.index

    def grant_commands(self):
        if self.ability_flag is not None:
            return [mnllib.CodeCommand(0x0008, [0x1], mnllib.Variable(self.owned_flag))]
        return [mnllib.CodeCommand(0x0008, [value], mnllib.Variable(flag)) for flag, value in self.grant_flags]

    def sync_command(self):
        """Ability flag := owned flag (room init)."""
        if self.inverted:
            # 0x000A = subtraction: flag = 1 - owned
            return mnllib.CodeCommand(0x000A, [0x1, mnllib.Variable(self.owned_flag)], mnllib.Variable(self.ability_flag))
        return mnllib.CodeCommand(0x0008, [mnllib.Variable(self.owned_flag)], mnllib.Variable(self.ability_flag))


ITEM_LIST = [
    KeyItem("hammer",     "Hammers",           "rando_hammer",   ability_flag=0x2001),
    KeyItem("mini_mario", "Mini Mario",        "rando_mini",     ability_flag=0x2000),
    KeyItem("spin_jump",  "Spin Jump",         "rando_spin",     ability_flag=0x2002),
    KeyItem("drill",      "Drill Bros.",       "rando_drill",    ability_flag=0x2003),
    KeyItem("flame",      "Fire Breath",       "rando_flame",    ability_flag=0x2004, inverted=True),
    KeyItem("slide",      "Sliding Haymaker",  "rando_slide",    ability_flag=0x2005),
    KeyItem("body_slam",  "Body Slam",         "rando_slam",     ability_flag=0x2006),
    KeyItem("spike_ball", "Spike Ball",        "rando_spike",    ability_flag=0x2007),
    KeyItem("vacuum",     "Vacuum Block",      "rando_vacuum",   ability_flag=0x200E),
    KeyItem("badges",     "Badges",            "rando_badge",    ability_flag=0x200C, progression=False),
    KeyItem("blue_shell", "Blue Shell Blocks", "rando_shell",    ability_flag=0x2025),
    KeyItem("air_vents",  "Air Vents",         "rando_vent",     ability_flag=0x202D),
    KeyItem("stingler",   "Stingler",          "rando_stingler", grant_flags=[(0xEB8D, 1), (0xE843, 1)]),
    KeyItem("key_r",      "Red Key",           "rando_key_r",    grant_flags=[(0xE873, 1), (0xE84C, 1)]),
    KeyItem("key_g",      "Green Key",         "rando_key_g",    grant_flags=[(0xE874, 1), (0xE84D, 1)]),
    KeyItem("key_b",      "Blue Key",          "rando_key_b",    grant_flags=[(0xE875, 1), (0xE84E, 1)]),
]
for _i, _item in enumerate(ITEM_LIST):
    _item.index = _i
ITEMS = {item.key: item for item in ITEM_LIST}
ABILITIES = [item for item in ITEM_LIST if item.ability_flag is not None]

# Items whose story role is a plot token rather than a gate (the game's own story flags move
# the plot forward, not these items), so shuffling them would change nothing. They stay vanilla.
UNSUPPORTED_UI = ["rando_bill", "rando_cure_r", "rando_cure_y", "rando_cure_g"]


# -------------------------------------------------------------------------------------------
# locations

@dataclass
class Location:
    key: str
    name: str
    vanilla: str | None          # vanilla item key (None for sidequest rewards)
    requires: frozenset          # item keys needed to reach and finish this check
    room: int | None = None
    # (variable, value) writes that mark the vanilla reward; the new reward is inserted after them
    anchors: list = field(default_factory=list)
    # vanilla reward writes that must be disabled (door items); the ability flag write is kept
    # for tutorials instead
    disable: list = field(default_factory=list)
    # (old_flag, new_flag) reads/writes to retarget so the location tracks its own completion
    relocate_done: list = field(default_factory=list)


def _req(*keys):
    return frozenset(keys)


# Vanilla story order, confirmed against a full playthrough's saves:
#   Hammer -> Vacuum -> Mini Mario -> Stingler -> Flame -> Sliding Haymaker -> Spin Jump/Badges
#   -> Blue Shell -> Drill -> Body Slam -> Air Vents -> Spike Ball -> Keys
#
# The story is linear and each chapter uses the move it just taught, so the requirement of
# every location is "everything obtained before it in the story". These rules are the part
# to loosen as the open world gets extended to later chapters.
_STORY = ["hammer", "vacuum", "mini_mario", "stingler", "flame", "slide", "spin_jump",
          "badges", "blue_shell", "drill", "body_slam", "air_vents", "spike_ball"]


def _before(item_key):
    i = _STORY.index(item_key)
    return frozenset(k for k in _STORY[:i] if ITEMS[k].progression)


LOCATIONS = [
    Location("trash_pit_hammers", "Trash Pit - Hammers", "hammer", _before("hammer"),
             room=0x021B, anchors=[(0x2001, 1)]),
    Location("plack_beach_vacuum", "Plack Beach - Vacuum Block", "vacuum", _before("vacuum"),
             room=0x003D, anchors=[(0x200E, 1)]),
    Location("pump_works_mini", "Pump Works - Mini Mario", "mini_mario", _before("mini_mario"),
             room=0x000D, anchors=[(0x2000, 1)]),
    Location("pump_works_stingler", "Pump Works - Stingler", "stingler", _before("stingler"),
             room=0x000C, anchors=[(0xEB8D, 1)], disable=[(0xEB8D, 1), (0xE843, 1)],
             relocate_done=[(0xEB8D, LOCATION_FLAG_BASE + 0)]),
    Location("flame_pipe_flame", "Flame Pipe - Fire Breath", "flame", _before("flame"),
             room=0x001A, anchors=[(0x2004, 0)]),
    Location("dimble_wood_slide", "Dimble Wood - Sliding Haymaker", "slide", _before("slide"),
             room=0x0032, anchors=[(0x2005, 1)]),
    Location("flab_zone_spin", "Flab Zone - Spin Jump", "spin_jump", _before("spin_jump"),
             room=0x0068, anchors=[(0x2002, 1)]),
    Location("flab_zone_badges", "Flab Zone - Badges", "badges", _before("badges"),
             room=0x00B8, anchors=[(0x200C, 1)]),
    Location("toad_town_blue_shell", "Blue Shell Blocks", "blue_shell", _before("blue_shell"),
             room=0x00CF, anchors=[(0x2025, 1)]),
    Location("energy_hold_drill", "Energy Hold - Drill Bros.", "drill", _before("drill"),
             room=0x00E5, anchors=[(0x2003, 1)]),
    Location("tower_of_yikk_slam", "Tower of Yikk - Body Slam", "body_slam", _before("body_slam"),
             room=0x0144, anchors=[(0x2006, 1)]),
    Location("air_vents", "Air Vents", "air_vents", _before("air_vents"),
             room=0x012A, anchors=[(0x202D, 1)]),
    Location("peach_castle_spike", "Peach's Castle - Spike Ball", "spike_ball", _before("spike_ball"),
             room=0x019E, anchors=[(0x2007, 1)]),
    Location("fawfulcopter_red", "Peach's Castle - Fawfulcopter (Red Key)", "key_r", _before("spike_ball") | {"spike_ball"},
             room=0x01C5, anchors=[(0xE873, 1)], disable=[(0xE873, 1), (0xE84C, 1)]),
    Location("fawfulcopter_green", "Peach's Castle - Fawfulcopter (Green Key)", "key_g", _before("spike_ball") | {"spike_ball"},
             room=0x01CF, anchors=[(0xE874, 1)], disable=[(0xE874, 1), (0xE84D, 1)]),
    Location("fawfulcopter_blue", "Peach's Castle - Fawfulcopter (Blue Key)", "key_b", _before("spike_ball") | {"spike_ball"},
             room=0x01D5, anchors=[(0xE875, 1)], disable=[(0xE875, 1), (0xE84E, 1)]),
]
LOCATIONS_BY_KEY = {loc.key: loc for loc in LOCATIONS}

# Finishing the game needs every progression item.
GOAL_REQUIRES = frozenset(item.key for item in ITEM_LIST if item.progression)


def sidequest_locations(sidequest_slots):
    """Sidequest reward slots (Blitties, Kuzzle, ...) that may receive key items.

    `sidequest_slots` is a list of (key, name, requires) tuples. Sidequests are spread over
    the whole game, so unless a better rule is known they require every progression item
    obtained before the end of the vanilla story.
    """
    return [Location(key, name, None, frozenset(requires)) for key, name, requires in sidequest_slots]


# -------------------------------------------------------------------------------------------
# logic / fill

class FillError(Exception):
    pass


def reachable(locations, placement, have):
    """Sweep: collect items from reachable locations until nothing new can be reached."""
    have = set(have)
    checked = set()
    changed = True
    while changed:
        changed = False
        for loc in locations:
            if loc.key in checked or not loc.requires <= have:
                continue
            checked.add(loc.key)
            item = placement.get(loc.key)
            if item is not None and item not in have:
                have.add(item)
                changed = True
    return have, checked


def is_beatable(locations, placement, start_items=()):
    have, _ = reachable(locations, placement, start_items)
    return GOAL_REQUIRES <= have


def place_key_items(rng, item_keys, locations, max_steps=200000, allow_empty_vanilla=False):
    """Place `item_keys` into `locations` so the game stays beatable.

    Locations whose vanilla item isn't being shuffled keep it. Every vanilla spot of a
    shuffled item gets one of the shuffled items; sidequest slots (vanilla None) may also
    receive one. This is a randomized backtracking search: locations are filled in a random
    order, each with a random remaining item, and a branch is abandoned as soon as the goal
    stops being reachable when all still-unplaced items are assumed collected (the same test
    an assumed fill uses). The search space here is small, so this always finds a placement
    when one exists, and every placement is equally likely to be explored first.
    """
    shuffled = list(item_keys)
    fixed = {loc.key: loc.vanilla for loc in locations if loc.vanilla is not None and loc.vanilla not in shuffled}
    slots = [loc for loc in locations if loc.key not in fixed]
    # with allow_empty_vanilla, a vanilla spot may end up with no key item (it would then give
    # the filler reward displaced from a sidequest slot; not wired into the ROM patcher yet)
    must_fill = [] if allow_empty_vanilla else [loc for loc in slots if loc.vanilla is not None]
    if len(must_fill) > len(shuffled):
        raise FillError("more locations than items")

    steps = 0

    def search(placement, remaining_items):
        """Forward search: only fill spots reachable with the items placed so far."""
        nonlocal steps
        steps += 1
        if steps > max_steps:
            raise FillError("key item placement search gave up")
        if not remaining_items:
            return placement if all(loc.key in placement for loc in must_fill) else None
        _have, checked = reachable(locations, placement, ())
        empty = [loc for loc in slots if loc.key not in placement]
        pending_must = [loc for loc in must_fill if loc.key not in placement]
        if len(pending_must) > len(remaining_items):
            return None
        candidates = [loc for loc in empty if loc.key in checked]
        if len(pending_must) == len(remaining_items):
            candidates = [loc for loc in candidates if loc in pending_must]
        if not candidates:
            return None  # dead end: nothing left to open up the rest of the game
        loc = rng.choice(candidates)
        order = list(remaining_items)
        rng.shuffle(order)
        for item in order:
            placement[loc.key] = item
            result = search(placement, [i for i in remaining_items if i != item])
            if result is not None:
                return result
            del placement[loc.key]
        return None

    result = search(dict(fixed), shuffled)
    if result is None or not is_beatable(locations, result):
        raise FillError("could not place key items in logic")
    return result


# -------------------------------------------------------------------------------------------
# ROM patching

def _find_writes(script, var, value):
    """[(subroutine, index)] of every `Variables[var] = value` in a room script."""
    found = []
    for sub in [script.header.post_table_subroutine, *script.subroutines]:
        for i, cmd in enumerate(sub.commands):
            if (isinstance(cmd, mnllib.CodeCommand) and cmd.command_id == 0x0008
                    and cmd.result_variable == mnllib.Variable(var) and cmd.arguments == [value]):
                found.append((sub, i))
    return found


def _replace_reads(script, old, new):
    for sub in [script.header.post_table_subroutine, *script.subroutines]:
        for cmd in sub.commands:
            if not isinstance(cmd, mnllib.CodeCommand):
                continue
            cmd.arguments = [mnllib.Variable(new) if a == mnllib.Variable(old) else a for a in cmd.arguments]
            if cmd.result_variable == mnllib.Variable(old):
                cmd.result_variable = mnllib.Variable(new)


def _add_text_entry(fevent_manager, room, text_by_lang):
    """Append a textbox entry to every language of a room. Returns its id (or None)."""
    lang_table = fevent_manager.fevent_chunks[room][2]
    if lang_table is None:
        return None
    entry_id = None
    for j in range(6):
        table = lang_table.text_tables[0x43 + j]
        if not table:
            continue
        text = text_by_lang[j]
        table.entries.append(text[0])
        table.textbox_sizes.append(text[1])
        if entry_id is None:
            entry_id = len(table.entries) - 1
        elif entry_id != len(table.entries) - 1:
            return None  # languages out of sync; skip the textbox rather than show the wrong text
    lang_table.text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b""
    size = len(lang_table.to_bytes())
    lang_table.text_tables[FEVENT_PADDING_TEXT_TABLE_ID] = b"\x00" * ((-(size + 1) % LANGUAGE_TABLE_ALIGNMENT) + 1)
    return entry_id


def _textbox_commands(text_id):
    return [
        mnllib.CodeCommand(0x01CD, [0x020000A1, 0x0080, 0x0060, 0x0000, 0x0000, 0x0001, 0x00]),  # key item jingle
        mnllib.CodeCommand(0x01BB, [-0x8000, 0x0010, 0x00, 0x00, 0x03, 0x00, -0x01, -0x01, -0x0001, 0x01, 0x00,
                                    0x00000000, text_id, 0x00, 0x08, 0x00, 0x0000, -0x01], mnllib.Variable(0x1000)),
        mnllib.CodeCommand(0x01BD, [0x00]),  # wait for textbox
    ]


def got_item_text(item_name, template_by_lang, item_template_name_by_lang, size_fn):
    """Build "You got <item>!" from the game's own "You got 5 Super Nuts!" string.
    `item_template_name_by_lang` holds the plural "Super Nuts" in each language."""
    out = []
    for j in range(6):
        template = template_by_lang[j]
        if template is None:
            out.append(None)
            continue
        old_name = item_template_name_by_lang[j]
        string = template
        if old_name is not None:
            for count in (b"5 ", b"5"):
                for name in (old_name, old_name.lower()):
                    candidate = count + name.encode(BIS_ENCODING)
                    if candidate in string:
                        string = string.replace(candidate, item_name.encode(BIS_ENCODING), 1)
                        break
                else:
                    continue
                break
        string = b"\xff\x35" + string
        out.append((string, size_fn(string)))
    return out


def install_ability_sync(fevent_manager, abilities, size_limit):
    """Prepend `ability := owned` for every shuffled ability to each room's init subroutine."""
    patched = skipped = 0
    for room, triple in enumerate(fevent_manager.fevent_chunks):
        script = triple[0]
        if room in FIELD_INIT_SKIP_ROOMS or not isinstance(script, mnllib.bis.FEventScript):
            continue
        if script.header.init_subroutine is None:
            continue
        commands = [item.sync_command() for item in abilities]
        if MIGRATE_VANILLA_SAVES:
            migrate = [mnllib.CodeCommand(0x0008, [mnllib.Variable(item.ability_flag)], mnllib.Variable(item.owned_flag))
                       for item in abilities if not item.inverted]
            migrate += [mnllib.CodeCommand(0x000A, [0x1, mnllib.Variable(item.ability_flag)], mnllib.Variable(item.owned_flag))
                        for item in abilities if item.inverted]
            migrate.append(mnllib.CodeCommand(0x0008, [0x1], mnllib.Variable(MIGRATED_FLAG)))
            skip = sum(c.serialized_len(fevent_manager, 0) for c in migrate)
            # branch_if(Variables[MIGRATED_FLAG], '==', 1, <past the migration>)
            commands = [mnllib.CodeCommand(0x0002, [0x00, mnllib.Variable(MIGRATED_FLAG), 0x1, 0x1, skip])] + migrate + commands
        before = len(script.to_bytes(fevent_manager))
        reloc = ScriptRelocator(fevent_manager, script)
        init = script.subroutines[script.header.init_subroutine]
        init.commands[0:0] = commands
        reloc.apply()
        if len(script.to_bytes(fevent_manager)) > size_limit:
            # undo: never make a room bigger than the biggest vanilla room
            reloc = ScriptRelocator(fevent_manager, script)
            del init.commands[0:len(commands)]
            reloc.apply()
            assert len(script.to_bytes(fevent_manager)) == before
            skipped += 1
            continue
        patched += 1
    return patched, skipped


def patch_location(fevent_manager, location, item, text_id_for):
    """Make `location` grant `item` instead of its vanilla reward."""
    script = fevent_manager.fevent_chunks[location.room][0]
    sites = _find_writes(script, *location.anchors[0])
    if not sites:
        raise ValueError(f"{location.name}: vanilla reward not found in room {location.room:#06x}")

    reloc = ScriptRelocator(fevent_manager, script)

    # disable vanilla door-item rewards (abilities keep theirs for the tutorial; room sync reverts it)
    for flag, value in location.disable:
        for sub, i in _find_writes(script, flag, value):
            # mutate in place: branches may target this exact command object
            sub.commands[i].result_variable = mnllib.Variable(DUMMY_FLAG)

    # the vanilla cutscene already announces its own item
    text_id = text_id_for(location.room, item) if item.key != location.vanilla else None
    for sub, i in reversed(sites):
        new = [cmd for cmd in item.grant_commands()]
        if location.relocate_done:
            new += [mnllib.CodeCommand(0x0008, [0x1], mnllib.Variable(new_flag)) for _old, new_flag in location.relocate_done]
        if text_id is not None:
            new += _textbox_commands(text_id)
        sub.commands[i + 1:i + 1] = new
    reloc.apply()

    # the location used the vanilla item's flag to remember it was done; give it its own flag
    for old, new in location.relocate_done:
        for sub in [script.header.post_table_subroutine, *script.subroutines]:
            for cmd in sub.commands:
                if (isinstance(cmd, mnllib.CodeCommand) and cmd.command_id == 0x0002
                        and mnllib.Variable(old) in cmd.arguments):
                    cmd.arguments = [mnllib.Variable(new) if a == mnllib.Variable(old) else a for a in cmd.arguments]


def owned_start_commands(item_keys):
    """Commands that give the player items from the start (used by "Start With All Abilities")."""
    commands = []
    for key in item_keys:
        commands += ITEMS[key].grant_commands()
    return commands


def randomize_key_items(seed, settings, fevent_manager, got_item_template, size_fn, spoiler_file, open_world=False, start_with_all=False, log=print):
    """Entry point used by the randomizer. Returns the updated spoiler text."""
    rng = random.Random(f"{seed}-key-items")
    item_keys = [item.key for item in ITEM_LIST if getattr(settings, item.ui).isChecked()]
    if not item_keys:
        return spoiler_file

    placement = place_key_items(rng, item_keys, LOCATIONS)
    if FORCED_PLACEMENT:  # testing hook
        placement.update(FORCED_PLACEMENT)

    size_limit = max(len(t[0].to_bytes(fevent_manager)) for t in fevent_manager.fevent_chunks
                     if isinstance(t[0], mnllib.bis.FEventScript))
    shuffled_abilities = [ITEMS[k] for k in item_keys if ITEMS[k].ability_flag is not None]
    patched, skipped = install_ability_sync(fevent_manager, shuffled_abilities, size_limit)
    log(f"ability sync installed in {patched} rooms ({skipped} too large)")

    texts = {}

    def text_id_for(room, item):
        if (room, item.key) not in texts:
            texts[(room, item.key)] = _add_text_entry(
                fevent_manager, room, got_item_text(item.name, *got_item_template, size_fn))
        return texts[(room, item.key)]

    for loc in LOCATIONS:
        if loc.key not in placement or loc.vanilla not in item_keys:
            continue
        item = ITEMS[placement[loc.key]]
        if item.key == loc.vanilla and item.ability_flag is None:
            continue  # a door item in its own spot: the vanilla cutscene already does everything
        patch_location(fevent_manager, loc, item, text_id_for)

    if open_world:
        # "Skip Story" marks the Trash Pit hammer cutscene as seen, which would make that check
        # impossible to collect. Let it play so it can hand out its item.
        for room, sub_index in NEW_GAME_SCRIPTS:
            for cmd in fevent_manager.fevent_chunks[room][0].subroutines[sub_index].commands:
                if (isinstance(cmd, mnllib.CodeCommand) and cmd.command_id == 0x0008
                        and cmd.result_variable == mnllib.Variable(0xE8A7)):
                    cmd.result_variable = mnllib.Variable(DUMMY_FLAG)

    if start_with_all:
        # the debug option sets the ability flags directly; with sync on, the owned flags are what count
        for room, sub_index in NEW_GAME_SCRIPTS:
            script = fevent_manager.fevent_chunks[room][0]
            reloc = ScriptRelocator(fevent_manager, script)
            script.subroutines[sub_index].commands[0:0] = owned_start_commands(item_keys)
            reloc.apply()

    spoiler_file += "\n\n----Key Items----"
    for loc in LOCATIONS:
        if loc.key in placement and loc.vanilla in item_keys:
            spoiler_file += f"\n{loc.name}: {ITEMS[placement[loc.key]].name}"
    return spoiler_file
