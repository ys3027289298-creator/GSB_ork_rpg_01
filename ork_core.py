# Ork-RPG Core Module
# Character classes, Inventory, and Game Logic

import random
import json
import os
from ork_data import TEXTS, ENEMIES, QUESTS

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
        self.name = data.get('name', 'Ork')
        self.hp = data.get('hp', 50)
        self.max_hp = data.get('max_hp', 50)
        self.dmg = data.get('dmg', 5)
        self.lvl = data.get('lvl', 1)
        self.xp = data.get('xp', 0)
        self.gold = data.get('gold', 0)
        self.potions = data.get('potions', 1)
        self.location = data.get('location', 'LOC_FOREST')
        self.day = data.get('day', 1)
        self.lang = data.get('lang', 'RU')
        self.active_quest = data.get('active_quest')
        self.quest_progress = data.get('quest_progress', 0)
        self.kills = data.get('kills', {})
        self.items_collected = data.get('items_collected', {})

class Enemy(Character):
    def __init__(self, data, lang):
        name = TEXTS[lang][data['name_key']]
        super().__init__(name, data['hp'], data['dmg'])
        self.xp = data['xp']
        self.gold = data['gold']

def combat(player, enemy):
    t = TEXTS[player.lang]
    print(f"\n{t['ENEMY_SPOT']} {enemy.name} (HP: {enemy.hp})")
    
    while player.hp > 0 and enemy.hp > 0:
        print(f"\n{t['FIGHT']}: {player.get_text('HP')} {player.hp}/{player.max_hp} | {enemy.name}: {enemy.hp}")
        print(f"[1] {t['ATTACK']} | [2] {t['BLOCK']} | [3] {t['USE_ITEM']} | [4] {t['RUN']}")
        
        action = input("> ").strip()
        
        if action == '1': # Attack
            dmg = player.dmg + random.randint(0, 2)
            crit = random.random() < 0.2
            if crit: dmg = int(dmg * 1.5)
            enemy.hp -= dmg
            print(f"{t['HIT']}: {dmg} {'(CRIT!)' if crit else ''}")
            
        elif action == '2': # Block
            if random.random() < 0.4:
                print(f"{t['DODGE']}!")
                enemy.hp -= 1 # Counter attack
            else:
                print("Blocked but took scratch.")
                player.hp -= enemy.dmg // 2
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
            player.hp -= enemy.dmg
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
    except:
        return False