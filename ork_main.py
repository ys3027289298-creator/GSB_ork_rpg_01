# Ork-RPG Main Entry Point
# Run this file to start the game.

import os
import random
import sys
from ork_core import (Player, Enemy, combat, save_game, load_game,
                      handle_death, SAVE_DIR, SAVE_PATH)
from ork_data import TEXTS, ENEMIES, QUESTS, LOCATIONS

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_input():
    input("\n[ENTER] to continue...\n")

def get_input(prompt):
    return input(prompt).strip()

def print_header(player):
    t = TEXTS[player.lang]
    print(f"=== {player.name} | {t['DAY']}: {player.day} ===")
    print(f"{t['LVL']}: {player.lvl} | {t['XP']}: {player.xp}/{player.lvl*20}")
    print(f"{t['HP']}: {player.hp}/{player.max_hp} | {t['GOLD']}: {player.gold}")
    print(f"{t['LOCATION']}: {t.get(player.location, player.location)}")
    if player.active_quest:
        q = player.active_quest
        desc = t[q['desc_key']]
        print(f"{t['QUEST_ACTIVE']} {desc} ({player.quest_progress}/{q['count']})")
    print("-" * 30)

def process_location(player):
    t = TEXTS[player.lang]
    print(f"\n{t['ACTION']}:")
    print(f"[1] {t['ACTION_FARM']} (Safe)")
    print(f"[2] {t['ACTION_HUNT']} (Risk)")
    print(f"[3] {t['LOC_SHOP']}")
    print(f"[4] {t['LOC_TRAIN']}")
    print(f"[5] {t['LOC_HOME']} (Save)")
    print(f"[6] {t['LOC_RIVER']}")
    print(f"[7] {t['LOC_DUNGEON']} (High Risk)")
    print(f"[Q] Quests")
    print(f"[E] Exit Game")

def action_farm(player):
    t = TEXTS[player.lang]
    clear_screen()
    print("Farming...")
    gold = random.randint(5, 15)
    player.gold += gold
    print(f"{t['GET_GOLD']}: {gold}")
    # Chance for item
    if random.random() < 0.3:
        player.pickup_item('Potion')
        print(f"{t['GET_ITEM']}: Potion")
    player.day += 1
    wait_input()

def action_hunt(player):
    t = TEXTS[player.lang]
    clear_screen()
    roll = random.random()
    if roll < 0.4:
        print(t['NO_ENEMY'])
        player.day += 1
        wait_input()
        return
    
    # Spawn enemy based on player level
    pool = [e for e in ENEMIES if e['name_key'] != 'E_BOSS']
    if player.lvl > 5 and random.random() < 0.1:
        pool = [e for e in ENEMIES if e['name_key'] == 'E_BOSS']
    
    enemy_data = random.choice(pool)
    enemy = Enemy(enemy_data, player.lang)
    
    result = combat(player, enemy)
    
    if result == 'LOSE':
        handle_death(player)
        print("You woke up beaten at the tent. Lost half gold.")
        wait_input()
    elif result == 'RUN':
        pass
    else:
        player.day += 1
        wait_input()

def action_shop(player):
    t = TEXTS[player.lang]
    clear_screen()
    print(t['SHOP_WELCOME'])
    print(f"[1] {t['SHOP_HEAL']} (You have: {player.potions})")
    print(f"[2] {t['SHOP_EXIT']}")
    
    choice = get_input("> ")
    if choice == '1':
        if player.gold >= 50:
            player.gold -= 50
            player.potions += 1
            print(t['SHOP_THANKS'])
        else:
            print(t['NO_GOLD'])
    wait_input()

def action_train(player):
    t = TEXTS[player.lang]
    clear_screen()
    print(t['TRAIN_WELCOME'])
    print(f"[1] {t['TRAIN_STR']}")
    print(f"[2] {t['TRAIN_VIT']}")
    print(f"[3] {t['TRAIN_EXIT']}")
    
    choice = get_input("> ")
    if choice == '1':
        if player.gold >= 100:
            player.gold -= 100
            player.dmg += 2
            print("+2 STR")
        else:
            print(t['NO_GOLD'])
    elif choice == '2':
        if player.gold >= 100:
            player.gold -= 100
            player.max_hp += 2
            player.hp += 2
            print("+2 VIT")
        else:
            print(t['NO_GOLD'])
    wait_input()

def action_river(player):
    t = TEXTS[player.lang]
    clear_screen()
    print("Fishing...")
    if random.random() < 0.5:
        gold = random.randint(10, 30)
        player.gold += gold
        print(f"Caught a big fish! {t['GET_GOLD']}: {gold}")
    else:
        print("Nothing...")
    player.day += 1
    wait_input()

def action_dungeon(player):
    t = TEXTS[player.lang]
    clear_screen()
    print("Entering dark place...")
    if random.random() < 0.2:
        # Boss spawn chance
        enemy_data = [e for e in ENEMIES if e['name_key'] == 'E_BOSS'][0]
        enemy = Enemy(enemy_data, player.lang)
    else:
        enemy_data = random.choice([e for e in ENEMIES if e['name_key'] not in ['E_KADIK', 'E_BOSS']])
        enemy = Enemy(enemy_data, player.lang)
    
    result = combat(player, enemy)
    if result == 'LOSE':
        handle_death(player)
        print("You woke up beaten at the tent. Lost half gold.")
    else:
        player.day += 1
    wait_input()

def action_sleep(player):
    t = TEXTS[player.lang]
    clear_screen()
    save_game(player)
    print("Game Saved. Goodnight.")
    sys.exit()

def action_quests(player):
    t = TEXTS[player.lang]
    clear_screen()
    print("=== QUESTS ===")
    if player.active_quest:
        desc = t[player.active_quest['desc_key']]
        print(f"{t['QUEST_ACTIVE']} {desc}")
        print(f"Progress: {player.quest_progress}/{player.active_quest['count']}")
    else:
        print("Available Quests:")
        for q in QUESTS:
            desc = t[q['desc_key']]
            status = "(Active)" if player.active_quest and player.active_quest['id'] == q['id'] else "(New)"
            print(f"[{q['id']}] {desc} {status}")
        
        choice = get_input("Pick ID to take quest (or Enter to cancel): ")
        if choice.isdigit():
            q_id = int(choice)
            selected = next((q for q in QUESTS if q['id'] == q_id), None)
            if selected:
                player.active_quest = selected
                player.quest_progress = 0
                print("Quest Accepted!")
    wait_input()

def main_menu():
    t = TEXTS['RU'] # Default to RU for menu first
    clear_screen()
    print(t['SELECT_LANG'])
    print(f"[1] {t['RU_LANG']}")
    print(f"[2] {t['EN_LANG']}")
    
    lang_choice = get_input("> ")
    lang = 'RU'
    if lang_choice == '2':
        lang = 'EN'
        t = TEXTS['EN']
    
    clear_screen()
    print(t['START_HEADER'])
    print(f"Language: {lang}")
    print(f"[1] {t['START_NEW']}")
    print(f"[2] {t['START_LOAD']}")
    print(f"[3] {t['START_EXIT']}")
    
    choice = get_input("> ")
    
    if choice == '1':
        p = Player()
        p.lang = lang
        return p
    elif choice == '2':
        p = Player()
        if load_game(p):
            return p
        else:
            # load_game already reports a corrupt save; only mention
            # "no saves" when the file is genuinely absent.
            if not os.path.exists(SAVE_PATH):
                print(t['NO_SAVES'])
            wait_input()
            return main_menu() # Retry
    else:
        sys.exit()

def main():
    # Ensure saves folder exists
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    player = main_menu()
    
    if not player:
        return

    while True:
        clear_screen()
        if not player.is_alive():
            # Dead players cannot keep moving: respawn at the tent.
            handle_death(player)
            print("You woke up beaten at the tent. Lost half gold.")
            wait_input()
        print_header(player)
        process_location(player)
        
        action = get_input("> ").upper()
        
        if action == '1':
            action_farm(player)
        elif action == '2':
            action_hunt(player)
        elif action == '3':
            action_shop(player)
        elif action == '4':
            action_train(player)
        elif action == '5':
            action_sleep(player)
        elif action == '6':
            action_river(player)
        elif action == '7':
            action_dungeon(player)
        elif action == 'Q':
            action_quests(player)
        elif action == 'E':
            if get_input("Save before exit? (y/n): ").lower() == 'y':
                save_game(player)
            sys.exit()
        else:
            print(TEXTS[player.lang]['ERROR_INPUT'])
            wait_input()

if __name__ == "__main__":
    main()
