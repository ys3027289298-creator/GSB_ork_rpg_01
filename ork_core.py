# Ork-RPG Core Module
# Character classes, Inventory, and Game Logic

import random
import json
import os
from ork_data import TEXTS, ENEMIES, QUESTS, LOCATIONS

# Save format version. Bump when Player.to_dict changes; old saves must be
# rejected (or migrated) instead of being silently filled with defaults.
SAVE_VERSION = 2

# ork_data is the single source of truth: these schemas describe the shape
# every record in ork_data must have, and are checked at the data boundary.
ENEMY_REQUIRED_FIELDS = ('name_key', 'hp', 'dmg', 'xp', 'gold')
ENEMY_NON_NEGATIVE_FIELDS = ('dmg', 'xp', 'gold')

SAVE_REQUIRED_FIELDS = (
    'save_version', 'name', 'hp', 'max_hp', 'dmg', 'lvl', 'xp', 'gold',
    'potions', 'location', 'day', 'lang', 'active_quest', 'quest_progress',
    'kills', 'items_collected',
)


class DataValidationError(ValueError):
    """A static data record (enemy/item/quest) violates its schema.

    Raised at the parsing boundary so a broken data file fails fast with a
    message naming the entity and the bad field, instead of producing a
    corrupt game state (or crashing later with a bare KeyError).
    """


class SaveDataError(DataValidationError):
    """A save file is incomplete, outdated, or contains invalid state."""


def known_items():
    """All valid item ids, derived from ork_data (loot tables + Potion)."""
    items = {'Potion'}
    for loc in LOCATIONS.values():
        for item in loc.get('loot', ()):
            items.add(item)
    return items


# LOC_HOME is a runtime location (tent) not listed in LOCATIONS data.
KNOWN_LOCATIONS = set(LOCATIONS) | {'LOC_HOME'}
KNOWN_QUEST_IDS = {q['id'] for q in QUESTS}


def _require_int(value, where, *, minimum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise DataValidationError(f'{where} must be an int, got {value!r}')
    if minimum is not None and value < minimum:
        raise DataValidationError(f'{where} must be >= {minimum}, got {value}')


def validate_enemy(data, lang='RU'):
    """Validate one enemy record from ork_data.ENEMIES."""
    if not isinstance(data, dict):
        raise DataValidationError(
            f'enemy record must be a dict, got {type(data).__name__}')
    ident = data.get('name_key', '<? enemy ?>')
    missing = [f for f in ENEMY_REQUIRED_FIELDS if f not in data]
    if missing:
        raise DataValidationError(
            f"enemy {ident!r} is missing required field(s): {', '.join(missing)}")
    for field in ('hp',) + ENEMY_NON_NEGATIVE_FIELDS:
        _require_int(data[field], f"enemy {ident!r} field {field!r}",
                     minimum=1 if field == 'hp' else 0)
    if not isinstance(data['name_key'], str):
        raise DataValidationError(f"enemy field 'name_key' must be a string")
    if data['name_key'] not in TEXTS.get(lang, {}):
        raise DataValidationError(
            f"enemy name_key {data['name_key']!r} has no {lang!r} localization")


def validate_item(item):
    """Validate an item id against the ork_data loot tables."""
    if not isinstance(item, str) or item not in known_items():
        raise DataValidationError(
            f'unknown item {item!r}; known items: {sorted(known_items())}')


def compute_attack_damage(player):
    """Attack formula with bounded output: damage is always >= 0.

    A negative/zero dmg stat must never let an "attack" heal the enemy.
    """
    base = max(0, player.dmg) + random.randint(0, 2)
    crit = random.random() < 0.2
    return (int(base * 1.5) if crit else base), crit


def handle_death(player):
    """Respawn a defeated player at the tent with the gold penalty."""
    player.hp = 10
    player.gold = max(0, player.gold // 2)
    player.location = 'LOC_HOME'

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
        self.location = 'LOC_FOREST'
        self.day = 1
        self.lang = 'RU'
        self.active_quest = None
        self.quest_progress = 0
        self.kills = {}
        self.items_collected = {}

    def get_text(self, key):
        return TEXTS[self.lang].get(key, key)

    @property
    def is_alive(self):
        return self.hp > 0

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def pickup_item(self, item):
        """Collect a unique item. Returns True if picked up, False if already
        present (duplicate pickups are rejected, never counted twice)."""
        validate_item(item)
        if item in self.items_collected:
            return False
        self.items_collected[item] = 1
        return True

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
            'save_version': SAVE_VERSION,
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
        # Strict migration: a save must be complete and self-consistent.
        # Silently defaulting missing/illegal fields is what makes the map and
        # inventory disagree after exiting and re-entering.
        if not isinstance(data, dict):
            raise SaveDataError(f'save must be a JSON object, got {type(data).__name__}')
        if data.get('save_version') != SAVE_VERSION:
            raise SaveDataError(
                f"unsupported save version {data.get('save_version')!r}; "
                f'expected {SAVE_VERSION}')
        missing = [f for f in SAVE_REQUIRED_FIELDS if f not in data]
        if missing:
            raise SaveDataError(
                f'save is missing field(s): {", ".join(missing)}')

        if not isinstance(data['name'], str) or not data['name']:
            raise SaveDataError("save field 'name' must be a non-empty string")
        _require_int(data['max_hp'], "save field 'max_hp'", minimum=1)
        _require_int(data['hp'], "save field 'hp'", minimum=0)
        if data['hp'] > data['max_hp']:
            raise SaveDataError(
                f"save field 'hp' ({data['hp']}) > max_hp ({data['max_hp']})")
        _require_int(data['dmg'], "save field 'dmg'", minimum=0)
        _require_int(data['lvl'], "save field 'lvl'", minimum=1)
        _require_int(data['xp'], "save field 'xp'", minimum=0)
        _require_int(data['gold'], "save field 'gold'", minimum=0)
        _require_int(data['potions'], "save field 'potions'", minimum=0)
        _require_int(data['day'], "save field 'day'", minimum=1)
        _require_int(data['quest_progress'], "save field 'quest_progress'", minimum=0)
        if data['lang'] not in TEXTS:
            raise SaveDataError(f"unknown save language {data['lang']!r}")
        if data['location'] not in KNOWN_LOCATIONS:
            raise SaveDataError(
                f"unknown save location {data['location']!r}; "
                f'known: {sorted(KNOWN_LOCATIONS)}')
        if not isinstance(data['items_collected'], dict):
            raise SaveDataError("save field 'items_collected' must be an object")
        for item, count in data['items_collected'].items():
            validate_item(item)
            _require_int(count, f"items_collected[{item!r}]", minimum=1)
        if not isinstance(data['kills'], dict):
            raise SaveDataError("save field 'kills' must be an object")
        for enemy, count in data['kills'].items():
            if not isinstance(enemy, str):
                raise SaveDataError('kills keys must be strings')
            _require_int(count, f'kills[{enemy!r}]', minimum=0)

        quest = data['active_quest']
        if quest is not None:
            if not isinstance(quest, dict) or quest.get('id') not in KNOWN_QUEST_IDS:
                raise SaveDataError(
                    f"save field 'active_quest' is not a known quest: {quest!r}")

        self.name = data['name']
        self.hp = data['hp']
        self.max_hp = data['max_hp']
        self.dmg = data['dmg']
        self.lvl = data['lvl']
        self.xp = data['xp']
        self.gold = data['gold']
        self.potions = data['potions']
        self.location = data['location']
        self.day = data['day']
        self.lang = data['lang']
        self.active_quest = quest
        self.quest_progress = data['quest_progress']
        self.kills = data['kills']
        self.items_collected = data['items_collected']

class Enemy(Character):
    def __init__(self, data, lang):
        validate_enemy(data, lang)
        name = TEXTS[lang][data['name_key']]
        super().__init__(name, data['hp'], data['dmg'])
        self.xp = data['xp']
        self.gold = data['gold']
        self.name_key = data['name_key']

def combat(player, enemy):
    t = TEXTS[player.lang]
    print(f"\n{t['ENEMY_SPOT']} {enemy.name} (HP: {enemy.hp})")
    
    while player.hp > 0 and enemy.hp > 0:
        print(f"\n{t['FIGHT']}: {player.get_text('HP')} {player.hp}/{player.max_hp} | {enemy.name}: {enemy.hp}")
        print(f"[1] {t['ATTACK']} | [2] {t['BLOCK']} | [3] {t['USE_ITEM']} | [4] {t['RUN']}")
        
        action = input("> ").strip()
        
        if action == '1': # Attack
            dmg, crit = compute_attack_damage(player)
            enemy.hp -= dmg
            print(f"{t['HIT']}: {dmg} {'(CRIT!)' if crit else ''}")
            
        elif action == '2': # Block
            if random.random() < 0.4:
                print(f"{t['DODGE']}!")
                enemy.hp -= 1 # Counter attack
            else:
                print("Blocked but took scratch.")
                player.hp -= max(0, enemy.dmg) // 2
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
            player.hp -= max(0, enemy.dmg)
            print(f"{enemy.name} hits for {enemy.dmg}")
            
    if player.hp <= 0:
        print(f"\n{t['LOSE']}")
        return 'LOSE'
    
    if enemy.hp <= 0:
        print(f"\n{t['WIN']}")
        player.add_xp(enemy.xp)
        player.gold += enemy.gold
        print(f"{t['GET_XP']}: {enemy.xp} | {t['GET_GOLD']}: {enemy.gold}")
        
        # Quest tracking
        player.check_quest('kill', enemy.name)
        
        # Boss Logic
        if enemy.name == TEXTS[player.lang]['E_BOSS']:
            print("\n!!! THE BOSS IS DOWN !!!")
            print("You rule the region now.")
            return 'WIN'
            
        return 'WIN'

def save_game(player):
    os.makedirs('saves', exist_ok=True)
    with open('saves/save.json', 'w') as f:
        json.dump(player.to_dict(), f)
    print(player.get_text('GAME_SAVED'))

def load_game(player):
    try:
        with open('saves/save.json', 'r') as f:
            data = json.load(f)
        player.from_dict(data)
        return True
    except FileNotFoundError:
        return False
    except (json.JSONDecodeError, DataValidationError) as e:
        # Report corruption instead of silently starting from a bad state.
        print(f"{player.get_text('SAVE_CORRUPT')} ({e})")
        return False
