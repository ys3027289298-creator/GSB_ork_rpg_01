# Ork-RPG Core Module
# Character classes, Inventory, and Game Logic

import random
import json
import os
from ork_data import TEXTS, ENEMIES, QUESTS, LOCATIONS

# Save files live next to the code, not next to the caller's CWD,
# so exit/re-launch from any directory sees the same map & inventory.
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saves')
SAVE_PATH = os.path.join(SAVE_DIR, 'save.json')

REQUIRED_ENEMY_FIELDS = ('name_key', 'hp', 'dmg', 'xp', 'gold')
REQUIRED_QUEST_FIELDS = ('id', 'desc_key', 'target', 'count', 'type', 'reward')
REQUIRED_LOCATION_FIELDS = ('id', 'risk', 'loot')
QUEST_TYPES = ('item', 'kill')
HOME_LOCATION = 'LOC_HOME'
START_LOCATION = 'LOC_FOREST'


class OrkDataError(ValueError):
    """Static data (ork_data.py) or a save file is invalid.

    Missing fields must fail loudly at the parsing boundary, naming the
    entity and the exact fields, instead of surfacing as a raw KeyError
    mid-game or being silently replaced by defaults.
    """


def _require_fields(kind, entry, required):
    missing = [f for f in required if f not in entry]
    if missing:
        ident = entry.get('name_key') or entry.get('id') or entry
        raise OrkDataError(
            "ork_data.py: %s %r is missing required field(s): %s"
            % (kind, ident, ', '.join(missing)))


def validate_data(enemies=None, quests=None, locations=None, texts=None):
    """Validate the static database. Raises OrkDataError listing every
    problem found, so a broken data file fails at startup, not mid-game."""
    enemies = ENEMIES if enemies is None else enemies
    quests = QUESTS if quests is None else quests
    locations = LOCATIONS if locations is None else locations
    texts = TEXTS if texts is None else texts

    errors = []
    enemy_keys = set()
    for entry in enemies:
        try:
            _require_fields('enemy', entry, REQUIRED_ENEMY_FIELDS)
        except OrkDataError as exc:
            errors.append(str(exc))
            continue
        key = entry['name_key']
        enemy_keys.add(key)
        for field in ('hp', 'dmg', 'xp', 'gold'):
            if not isinstance(entry[field], (int, float)):
                errors.append("enemy %r: %s must be a number, got %r"
                              % (key, field, entry[field]))
        if isinstance(entry.get('hp'), (int, float)) and entry['hp'] <= 0:
            errors.append("enemy %r: hp must be positive" % key)
        for lang, strings in texts.items():
            if key not in strings:
                errors.append("enemy %r has no name in TEXTS[%r]" % (key, lang))

    for quest in quests:
        try:
            _require_fields('quest', quest, REQUIRED_QUEST_FIELDS)
        except OrkDataError as exc:
            errors.append(str(exc))
            continue
        if quest['type'] not in QUEST_TYPES:
            errors.append("quest %r: unknown type %r" % (quest['id'], quest['type']))
        if quest['type'] == 'kill' and quest['target'] not in enemy_keys:
            errors.append("quest %r: kill target %r is not a known enemy"
                          % (quest['id'], quest['target']))
        for lang, strings in texts.items():
            if quest['desc_key'] not in strings:
                errors.append("quest %r has no desc in TEXTS[%r]"
                              % (quest['id'], lang))

    for loc_id, loc in locations.items():
        try:
            _require_fields('location', loc, REQUIRED_LOCATION_FIELDS)
        except OrkDataError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(loc['loot'], list) or not loc['loot']:
            errors.append("location %r: loot must be a non-empty list" % loc_id)

    if errors:
        raise OrkDataError("invalid static data:\n - " + "\n - ".join(errors))


# ork_data.py is the single source of truth: refuse to boot on bad data.
validate_data()


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _to_int_map(value):
    if not isinstance(value, dict):
        return {}
    return {str(k): max(0, _to_int(v, 0)) for k, v in value.items()}


def _is_known_quest(quest):
    if not isinstance(quest, dict):
        return False
    if any(f not in quest for f in REQUIRED_QUEST_FIELDS):
        return False
    return any(q['id'] == quest['id'] for q in QUESTS)


def roll_attack(dmg_stat, rng=random):
    """Player attack roll. Damage is clamped to >= 1 so an out-of-range
    dmg stat can never heal the enemy or soft-lock a fight."""
    dmg = max(1, dmg_stat + rng.randint(0, 2))
    crit = rng.random() < 0.2
    if crit:
        dmg = int(dmg * 1.5)
    return dmg, crit


class Character:
    def __init__(self, name, hp, dmg):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.dmg = dmg

class Player(Character):
    def __init__(self):
        super().__init__("Ork", 50, 5)
        self.lvl = 1
        self.xp = 0
        self.gold = 0
        self.potions = 1
        self.location = START_LOCATION
        self.day = 1
        self.lang = 'RU'
        self.active_quest = None
        self.quest_progress = 0
        self.kills = {}
        self.items_collected = {}

    def get_text(self, key):
        return TEXTS[self.lang].get(key, key)

    def is_alive(self):
        return self.hp > 0

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def add_xp(self, amount):
        self.xp += amount
        req = self.lvl * 20
        if self.xp >= req:
            self.lvl += 1
            self.xp -= req
            self.max_hp += 10
            self.dmg += 2
            self.hp = self.max_hp
            return True
        return False

    def pickup_item(self, item, unique=False):
        """Pick up an item. A unique item already owned is refused
        (returns False) instead of silently stacking a duplicate."""
        if unique and self.items_collected.get(item, 0) > 0:
            return False
        self.items_collected[item] = self.items_collected.get(item, 0) + 1
        if item == 'Potion':
            self.potions += 1
        self.check_quest('item', item)
        return True

    def check_quest(self, action, target):
        if not self.active_quest:
            return False

        q = self.active_quest
        if q['type'] != action:
            return False

        if q['type'] == 'kill' and target == q['target']:
            self.quest_progress += 1
        elif q['type'] == 'item' and target == q['target']:
            self.quest_progress += 1

        if self.quest_progress >= q['count']:
            self.gold += q['reward']
            self.active_quest = None
            self.quest_progress = 0
            return True
        return False

    def to_dict(self):
        return {
            'name': self.name,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'dmg': self.dmg,
            'lvl': self.lvl,
            'xp': self.xp,
            'gold': self.gold,
            'potions': self.potions,
            'location': self.location,
            'day': self.day,
            'lang': self.lang,
            'active_quest': self.active_quest,
            'quest_progress': self.quest_progress,
            'kills': self.kills,
            'items_collected': self.items_collected
        }

    def from_dict(self, data):
        # State migration: a save is user data, not static data, so
        # out-of-range or wrong-typed values are clamped back into a
        # valid game state instead of silently producing a broken hero.
        self.name = str(data.get('name') or 'Ork')
        self.max_hp = max(1, _to_int(data.get('max_hp'), 50))
        self.hp = _clamp(_to_int(data.get('hp'), self.max_hp), 0, self.max_hp)
        self.dmg = max(1, _to_int(data.get('dmg'), 5))
        self.lvl = max(1, _to_int(data.get('lvl'), 1))
        self.xp = max(0, _to_int(data.get('xp'), 0))
        self.gold = max(0, _to_int(data.get('gold'), 0))
        self.potions = max(0, _to_int(data.get('potions'), 1))
        self.day = max(1, _to_int(data.get('day'), 1))
        location = data.get('location')
        if location not in LOCATIONS and location != HOME_LOCATION:
            location = START_LOCATION
        self.location = location
        lang = data.get('lang')
        self.lang = lang if lang in TEXTS else 'RU'
        quest = data.get('active_quest')
        self.active_quest = quest if _is_known_quest(quest) else None
        max_progress = self.active_quest['count'] if self.active_quest else 0
        self.quest_progress = _clamp(_to_int(data.get('quest_progress'), 0),
                                     0, max_progress)
        self.kills = _to_int_map(data.get('kills'))
        self.items_collected = _to_int_map(data.get('items_collected'))

class Enemy(Character):
    def __init__(self, data, lang):
        _require_fields('enemy', data, REQUIRED_ENEMY_FIELDS)
        name_key = data['name_key']
        if lang not in TEXTS or name_key not in TEXTS[lang]:
            raise OrkDataError(
                "ork_data.py: enemy %r has no name in TEXTS[%r]"
                % (name_key, lang))
        self.name_key = name_key
        super().__init__(TEXTS[lang][name_key], data['hp'], data['dmg'])
        self.xp = data['xp']
        self.gold = data['gold']

def handle_death(player):
    """Respawn a dead player at the tent. Called whenever hp <= 0 so a
    corpse can never keep walking around the map."""
    player.hp = min(10, player.max_hp)
    player.gold = max(0, player.gold // 2)
    player.location = HOME_LOCATION

def combat(player, enemy):
    t = TEXTS[player.lang]
    print(f"\n{t['ENEMY_SPOT']} {enemy.name} (HP: {enemy.hp})")

    while player.hp > 0 and enemy.hp > 0:
        print(f"\n{t['FIGHT']}: {player.get_text('HP')} {player.hp}/{player.max_hp} | {enemy.name}: {enemy.hp}")
        print(f"[1] {t['ATTACK']} | [2] {t['BLOCK']} | [3] {t['USE_ITEM']} | [4] {t['RUN']}")

        action = input("> ").strip()

        if action == '1': # Attack
            dmg, crit = roll_attack(player.dmg)
            enemy.hp -= dmg
            print(f"{t['HIT']}: {dmg} {'(CRIT!)' if crit else ''}")

        elif action == '2': # Block
            if random.random() < 0.4:
                print(f"{t['DODGE']}!")
                enemy.hp -= 1 # Counter attack
            else:
                print("Blocked but took scratch.")
                player.hp = max(0, player.hp - max(0, enemy.dmg) // 2)
                continue

        elif action == '3': # Potion
            if player.potions > 0:
                player.potions -= 1
                player.heal(20)
                print(f"{t['HEAL']} (+20 HP)")
            else:
                print(t['NO_POTIONS'])
                continue

        elif action == '4': # Run
            if random.random() < 0.5:
                print("Escaped!")
                return 'RUN'
            else:
                print("Failed to run!")
        else:
            print(t['ERROR_INPUT'])
            continue

        # Enemy Turn
        if enemy.hp > 0:
            enemy_dmg = max(0, enemy.dmg)
            player.hp = max(0, player.hp - enemy_dmg)
            print(f"{enemy.name} hits for {enemy_dmg}")

    if player.hp <= 0:
        print(f"\n{t['LOSE']}")
        return 'LOSE'

    if enemy.hp <= 0:
        print(f"\n{t['WIN']}")
        player.add_xp(enemy.xp)
        player.gold += enemy.gold
        print(f"{t['GET_XP']}: {enemy.xp} | {t['GET_GOLD']}: {enemy.gold}")

        # Quest tracking (quests reference name_key, not localized text)
        player.check_quest('kill', enemy.name_key)

        # Boss Logic
        if enemy.name_key == 'E_BOSS':
            print("\n!!! THE BOSS IS DOWN !!!")
            print("You rule the region now.")
            return 'WIN'

        return 'WIN'

def save_game(player):
    os.makedirs(SAVE_DIR, exist_ok=True)
    # Atomic write: a crash mid-save can never leave a truncated JSON
    # that the next load would silently "migrate" into a wrong state.
    tmp_path = SAVE_PATH + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(player.to_dict(), f)
    os.replace(tmp_path, SAVE_PATH)
    print(player.get_text('GAME_SAVED'))

def load_game(player):
    if not os.path.exists(SAVE_PATH):
        return False
    try:
        with open(SAVE_PATH, 'r') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        # Corrupt save: say so, and leave the fresh player untouched
        # instead of silently half-loading a broken state.
        print(player.get_text('SAVE_CORRUPT'))
        return False
    player.from_dict(data)
    return True
