# Ork-RPG Data Module
# This file contains all static data: Locations, Enemies, NPCs, Items, Quests.

# Localization Strings (RU/EN)
TEXTS = {
    'RU': {
        'START_HEADER': '=== ОРК РПГ: ГЛУБИНКА ===',
        'START_NEW': 'Новая игра',
        'START_LOAD': 'Загрузить',
        'START_EXIT': 'Выход',
        'SELECT_LANG': 'Выберите язык / Select Language:',
        'RU_LANG': 'Русский (RU)',
        'EN_LANG': 'English (EN)',
        'ERROR_INPUT': 'Неверный ввод. Попробуйте снова.',
        'SAVE_CORRUPT': 'Сейв битый или старый. Лучше начать заново, братан.',
        'GAME_SAVED': 'Сохранено успешно!',
        'NO_SAVES': 'Нет сохранений.',
        
        # Gameplay
        'DAY': 'День',
        'HP': 'ЗДОРОВЬЕ',
        'GOLD': 'БАБКИ',
        'LVL': 'УРОВЕНЬ',
        'XP': 'ОПЫТ',
        'LOCATION': 'ЛОКАЦИЯ',
        'ACTION': 'ДЕЙСТВИЕ',
        'ENEMY_SPOT': 'Вы встретили:',
        'FIGHT': 'БИТВА',
        'ATTACK': 'Пнуть',
        'BLOCK': 'Прикрыться',
        'USE_ITEM': 'Выпить зелье',
        'RUN': 'Смыться',
        'WIN': 'Врага пнул!',
        'LOSE': 'Вас порвали...',
        'HIT': 'Удар',
        'DODGE': 'Уклон',
        'DMG': 'Урон',
        'GET_XP': 'Получено опыта',
        'GET_GOLD': 'Поднято бабла',
        'GET_ITEM': 'Нашел предмет',
        'LEVEL_UP': 'LEVEL UP! Статы +',
        'NO_GOLD': 'Нет бабла!',
        'NO_POTIONS': 'Нет зелий!',
        'HEAL': 'Выпил зелье',
        'NO_ENEMY': 'Тут пусто.',
        
        # Locations & Actions
        'LOC_FOREST': 'Лес (Фармить дрова)',
        'LOC_RIVER': 'Река (Ловить рыбу)',
        'LOC_DUNGEON': 'Бандитская пристань (Риск)',
        'LOC_TRAIN': 'Спортзал (Тренировка)',
        'LOC_SHOP': 'Магазин (Турбопродажи)',
        'LOC_HOME': 'Палатка (Спать/Сохранить)',
        'ACTION_FARM': 'Работать',
        'ACTION_HUNT': 'Искать приключений',
        'ACTION_BUY': 'Купить',
        'ACTION_TRAIN': 'Качаться',
        'ACTION_SLEEP': 'Сохранить и выйти',
        
        # Shop
        'SHOP_WELCOME': 'Че приперся? Купишь что-нибудь?',
        'SHOP_HEAL': 'Зелье (50г)',
        'SHOP_EXIT': 'Уйти',
        'SHOP_BUY': 'Купил',
        'SHOP_THANKS': 'На здоровье!',
        
        # Train
        'TRAIN_WELCOME': 'Хочешь стать крепче? Плати.',
        'TRAIN_STR': 'Сила (+2) [100г]',
        'TRAIN_VIT': 'Выносливость (+2) [100г]',
        'TRAIN_EXIT': 'Уйти',
        
        # Quests (Gopnik Style)
        'QUEST_START': 'Задание:',
        'QUEST_ACTIVE': 'Текущее задание:',
        'QUEST_COMPLETE': 'Задание выполнено! +',
        'QUEST_DESC_1': 'Угости бомжей (Принести 3 зелья)',
        'QUEST_DESC_2': 'Найти "сокровище" в лесу (Убить 5 гопников)',
        'QUEST_DESC_3': 'Застучать конкурента (Убить Босса)',
        'QUEST_DONE': 'Задание уже сделано.',
        
        # Enemies (Gopniks)
        'E_GOPIK': 'Гопник',
        'E_KADIK': 'Кадик (Безобидный)',
        'E_BORODACH': 'Бородач (Опасный)',
        'E_SLOVAK': 'Словак (Чувак)',
        'E_BOSS': 'ОПГ Вор в законе',
    },
    'EN': {
        'START_HEADER': '=== ORK RPG: DEPTHS ===',
        'START_NEW': 'New Game',
        'START_LOAD': 'Load Game',
        'START_EXIT': 'Exit',
        'SELECT_LANG': 'Choose Language / Выберите язык:',
        'RU_LANG': 'Russian (RU)',
        'EN_LANG': 'English (EN)',
        'ERROR_INPUT': 'Invalid input. Try again.',
        'SAVE_CORRUPT': 'Save corrupted. Start fresh, bro.',
        'GAME_SAVED': 'Game saved!',
        'NO_SAVES': 'No saves found.',
        
        'DAY': 'Day',
        'HP': 'HEALTH',
        'GOLD': 'GOLD',
        'LVL': 'LEVEL',
        'XP': 'XP',
        'LOCATION': 'LOCATION',
        'ACTION': 'ACTION',
        'ENEMY_SPOT': 'You met:',
        'FIGHT': 'FIGHT',
        'ATTACK': 'Kick',
        'BLOCK': 'Block',
        'USE_ITEM': 'Drink Potion',
        'RUN': 'Run',
        'WIN': 'Enemy kicked!',
        'LOSE': 'You got wrecked...',
        'HIT': 'Hit',
        'DODGE': 'Dodge',
        'DMG': 'Dmg',
        'GET_XP': 'Got XP',
        'GET_GOLD': 'Got Gold',
        'GET_ITEM': 'Found Item',
        'LEVEL_UP': 'LEVEL UP! Stats +',
        'NO_GOLD': 'No gold!',
        'NO_POTIONS': 'No potions!',
        'HEAL': 'Drank potion',
        'NO_ENEMY': 'Empty here.',
        
        'LOC_FOREST': 'Forest (Farm wood)',
        'LOC_RIVER': 'River (Fish)',
        'LOC_DUNGEON': 'Bandit Den (Risk)',
        'LOC_TRAIN': 'Gym (Train)',
        'LOC_SHOP': 'Shop (Trade)',
        'LOC_HOME': 'Tent (Save/Rest)',
        'ACTION_FARM': 'Work',
        'ACTION_HUNT': 'Hunt',
        'ACTION_BUY': 'Buy',
        'ACTION_TRAIN': 'Train',
        'ACTION_SLEEP': 'Save & Exit',
        
        'SHOP_WELCOME': 'Yo whatchu want?',
        'SHOP_HEAL': 'Potion (50g)',
        'SHOP_EXIT': 'Leave',
        'SHOP_BUY': 'Bought',
        'SHOP_THANKS': 'Peace!',
        
        'TRAIN_WELCOME': 'Wanna get ripped? Pay up.',
        'TRAIN_STR': 'Strength (+2) [100g]',
        'TRAIN_VIT': 'Vitality (+2) [100g]',
        'TRAIN_EXIT': 'Leave',
        
        'QUEST_START': 'Quest:',
        'QUEST_ACTIVE': 'Active Quest:',
        'QUEST_COMPLETE': 'Quest Done! +',
        'QUEST_DESC_1': 'Feed hobos (Bring 3 potions)',
        'QUEST_DESC_2': 'Find "treasure" (Kill 5 Gopniks)',
        'QUEST_DESC_3': 'Snitch rival (Kill Boss)',
        'QUEST_DONE': 'Already done.',
        
        'E_GOPIK': 'Gopnik',
        'E_KADIK': 'Weakling',
        'E_BORODACH': 'Borodach (Tough)',
        'E_SLOVAK': 'Slovak (Dude)',
        'E_BOSS': 'Crime Boss',
    }
}

# Locations Data
LOCATIONS = {
    'LOC_FOREST': {'id': 'LOC_FOREST', 'risk': 0.3, 'loot': ['Wood', 'Berry']},
    'LOC_RIVER': {'id': 'LOC_RIVER', 'risk': 0.2, 'loot': ['Fish', 'Water']},
    'LOC_DUNGEON': {'id': 'LOC_DUNGEON', 'risk': 0.8, 'loot': ['Gold', 'Key']},
}

# Enemy Database (Scaled by difficulty)
ENEMIES = [
    {'name_key': 'E_KADIK', 'hp': 10, 'dmg': 2, 'xp': 5, 'gold': 5},
    {'name_key': 'E_GOPIK', 'hp': 20, 'dmg': 5, 'xp': 10, 'gold': 15},
    {'name_key': 'E_SLOVAK', 'hp': 30, 'dmg': 8, 'xp': 15, 'gold': 25},
    {'name_key': 'E_BORODACH', 'hp': 50, 'dmg': 12, 'xp': 25, 'gold': 50},
    {'name_key': 'E_BOSS', 'hp': 100, 'dmg': 20, 'xp': 100, 'gold': 200},
]

# Quests Database
QUESTS = [
    {'id': 1, 'desc_key': 'QUEST_DESC_1', 'target': 'Potion', 'count': 3, 'type': 'item', 'reward': 50},
    {'id': 2, 'desc_key': 'QUEST_DESC_2', 'target': 'E_GOPIK', 'count': 5, 'type': 'kill', 'reward': 100},
    {'id': 3, 'desc_key': 'QUEST_DESC_3', 'target': 'E_BOSS', 'count': 1, 'type': 'kill', 'reward': 500},
]