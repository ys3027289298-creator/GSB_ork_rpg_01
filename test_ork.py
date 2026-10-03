# Tests for ork_rpg: data parsing, state migration, abnormal input.
# Run: python3 -m unittest test_ork -v

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

import ork_core
from ork_core import (Enemy, Player, OrkDataError, combat, handle_death,
                      load_game, roll_attack, save_game, validate_data)
from ork_data import ENEMIES, QUESTS


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


class DataParsingTests(unittest.TestCase):
    """The data file is the single source of truth: bad entries must
    fail loudly with named fields, never crash as a bare KeyError or
    silently default into a wrong game state."""

    def test_shipped_data_is_valid(self):
        validate_data()  # must not raise

    def test_enemy_missing_fields_raise_named_error(self):
        bad = {'name_key': 'E_GOPIK', 'hp': 20, 'dmg': 5}
        with self.assertRaises(OrkDataError) as ctx:
            Enemy(bad, 'EN')
        msg = str(ctx.exception)
        self.assertIn('E_GOPIK', msg)
        self.assertIn('xp', msg)
        self.assertIn('gold', msg)

    def test_enemy_unknown_name_key_raises(self):
        bad = {'name_key': 'E_GHOST', 'hp': 1, 'dmg': 1, 'xp': 1, 'gold': 1}
        with self.assertRaises(OrkDataError) as ctx:
            Enemy(bad, 'EN')
        self.assertIn('E_GHOST', str(ctx.exception))

    def test_validate_data_reports_every_missing_field(self):
        bad_enemies = [{'name_key': 'E_X', 'hp': 10}]
        with self.assertRaises(OrkDataError) as ctx:
            validate_data(enemies=bad_enemies)
        msg = str(ctx.exception)
        for field in ('dmg', 'xp', 'gold'):
            self.assertIn(field, msg)
        self.assertIn('E_X', msg)

    def test_validate_data_rejects_unknown_kill_target(self):
        bad_quests = [dict(QUESTS[1], target='E_GHOST')]
        with self.assertRaises(OrkDataError) as ctx:
            validate_data(quests=bad_quests)
        self.assertIn('E_GHOST', str(ctx.exception))

    def test_validate_data_rejects_non_positive_hp(self):
        bad = [dict(ENEMIES[0], hp=0)]
        with self.assertRaises(OrkDataError):
            validate_data(enemies=bad)


class AttackFormulaTests(unittest.TestCase):
    """Damage rolls must stay inside their valid domain."""

    def test_negative_dmg_stat_is_clamped(self):
        rng = mock.Mock()
        rng.randint.return_value = 0
        rng.random.return_value = 0.5  # no crit
        dmg, crit = roll_attack(-10, rng)
        self.assertEqual(dmg, 1)
        self.assertFalse(crit)

    def test_normal_roll_within_bounds(self):
        rng = mock.Mock()
        rng.randint.return_value = 2
        rng.random.return_value = 0.5
        dmg, _ = roll_attack(5, rng)
        self.assertEqual(dmg, 7)

    def test_combat_with_broken_stats_still_terminates(self):
        player = Player()
        player.lang = 'EN'
        player.dmg = -10  # migrated/corrupt stat: must not heal the enemy
        enemy = Enemy(ENEMIES[0], 'EN')  # 10 hp
        inputs = iter(['1'] * 10)
        with mock.patch('builtins.input', lambda *a: next(inputs)), \
             mock.patch('random.randint', return_value=0), \
             mock.patch('random.random', return_value=0.5), \
             quiet():
            result = combat(player, enemy)
        self.assertEqual(result, 'WIN')
        self.assertGreater(player.hp, 0)


class PickupTests(unittest.TestCase):
    def test_unique_item_cannot_be_picked_up_twice(self):
        player = Player()
        self.assertTrue(player.pickup_item('Key', unique=True))
        self.assertFalse(player.pickup_item('Key', unique=True))
        self.assertEqual(player.items_collected['Key'], 1)

    def test_potion_pickup_is_recorded(self):
        player = Player()
        player.pickup_item('Potion')
        self.assertEqual(player.potions, 2)
        self.assertEqual(player.items_collected['Potion'], 1)

    def test_item_quest_completes_via_pickups(self):
        player = Player()
        player.active_quest = dict(QUESTS[0])  # bring 3 Potions
        player.quest_progress = 0
        for _ in range(3):
            player.pickup_item('Potion')
        self.assertIsNone(player.active_quest)
        self.assertEqual(player.gold, QUESTS[0]['reward'])

    def test_kill_quest_matches_name_key(self):
        player = Player()
        player.lang = 'EN'
        player.active_quest = dict(QUESTS[1])  # kill 5 E_GOPIK
        player.quest_progress = 4
        enemy = Enemy(ENEMIES[1], 'EN')  # E_GOPIK, 20 hp
        inputs = iter(['1'] * 4)
        with mock.patch('builtins.input', lambda *a: next(inputs)), \
             mock.patch('random.randint', return_value=0), \
             mock.patch('random.random', return_value=0.5), \
             quiet():
            combat(player, enemy)
        self.assertIsNone(player.active_quest)
        self.assertEqual(player.gold, enemy.gold + QUESTS[1]['reward'])


class DeathTests(unittest.TestCase):
    def test_is_alive(self):
        player = Player()
        self.assertTrue(player.is_alive())
        player.hp = 0
        self.assertFalse(player.is_alive())

    def test_handle_death_respawns_at_tent(self):
        player = Player()
        player.hp = 0
        player.gold = 101
        player.location = 'LOC_DUNGEON'
        handle_death(player)
        self.assertEqual(player.hp, 10)
        self.assertEqual(player.gold, 50)
        self.assertEqual(player.location, 'LOC_HOME')
        self.assertTrue(player.is_alive())


class StateMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_dir, self.old_path = ork_core.SAVE_DIR, ork_core.SAVE_PATH
        ork_core.SAVE_DIR = self.tmp.name
        ork_core.SAVE_PATH = os.path.join(self.tmp.name, 'save.json')

    def tearDown(self):
        ork_core.SAVE_DIR, ork_core.SAVE_PATH = self.old_dir, self.old_path
        self.tmp.cleanup()

    def test_roundtrip_preserves_map_and_inventory(self):
        player = Player()
        player.location = 'LOC_DUNGEON'
        player.potions = 7
        player.gold = 123
        player.items_collected = {'Potion': 7, 'Key': 1}
        player.active_quest = dict(QUESTS[1])
        player.quest_progress = 2
        with quiet():
            save_game(player)
        loaded = Player()
        self.assertTrue(load_game(loaded))
        self.assertEqual(loaded.location, 'LOC_DUNGEON')
        self.assertEqual(loaded.potions, 7)
        self.assertEqual(loaded.gold, 123)
        self.assertEqual(loaded.items_collected, {'Potion': 7, 'Key': 1})
        self.assertEqual(loaded.active_quest['id'], QUESTS[1]['id'])
        self.assertEqual(loaded.quest_progress, 2)

    def test_missing_save_returns_false(self):
        player = Player()
        self.assertFalse(load_game(player))
        self.assertEqual(player.location, 'LOC_FOREST')

    def test_corrupt_save_reports_and_leaves_state_untouched(self):
        with open(ork_core.SAVE_PATH, 'w') as f:
            f.write('{"hp": ')  # truncated JSON
        player = Player()
        player.gold = 999
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ok = load_game(player)
        self.assertFalse(ok)
        from ork_data import TEXTS
        self.assertIn(TEXTS['RU']['SAVE_CORRUPT'], out.getvalue())
        self.assertEqual(player.gold, 999)  # not silently half-loaded

    def test_out_of_range_save_is_migrated_to_valid_state(self):
        data = {'hp': 99999, 'max_hp': 50, 'potions': -3, 'dmg': -10,
                'location': 'NOWHERE', 'lang': 'XX', 'gold': -5,
                'active_quest': {'id': 999}, 'quest_progress': 42,
                'kills': 'oops', 'items_collected': [1, 2]}
        with open(ork_core.SAVE_PATH, 'w') as f:
            json.dump(data, f)
        player = Player()
        with quiet():
            self.assertTrue(load_game(player))
        self.assertEqual(player.hp, 50)       # clamped to max_hp
        self.assertEqual(player.potions, 0)   # no negative inventory
        self.assertEqual(player.dmg, 1)       # attack stat back in domain
        self.assertEqual(player.location, 'LOC_FOREST')  # known map node
        self.assertEqual(player.lang, 'RU')
        self.assertEqual(player.gold, 0)
        self.assertIsNone(player.active_quest)  # unknown quest dropped
        self.assertEqual(player.quest_progress, 0)
        self.assertEqual(player.kills, {})
        self.assertEqual(player.items_collected, {})

    def test_save_is_atomic_no_tmp_file_left(self):
        with quiet():
            save_game(Player())
        self.assertTrue(os.path.exists(ork_core.SAVE_PATH))
        self.assertFalse(os.path.exists(ork_core.SAVE_PATH + '.tmp'))


class SavePathTests(unittest.TestCase):
    def test_save_path_anchored_to_module_not_cwd(self):
        module_dir = os.path.dirname(os.path.abspath(ork_core.__file__))
        self.assertEqual(ork_core.SAVE_DIR, os.path.join(module_dir, 'saves'))
        self.assertTrue(os.path.isabs(ork_core.SAVE_PATH))

    def test_save_works_from_any_cwd(self):
        module_dir = os.path.dirname(os.path.abspath(ork_core.__file__))
        save_path = os.path.join(module_dir, 'saves', 'save.json')
        old_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as other:
                os.chdir(other)
                player = Player()
                player.location = 'LOC_RIVER'
                with quiet():
                    save_game(player)
                self.assertTrue(os.path.exists(save_path))
                loaded = Player()
                self.assertTrue(load_game(loaded))
                self.assertEqual(loaded.location, 'LOC_RIVER')
        finally:
            os.chdir(old_cwd)
            if os.path.exists(save_path):
                os.remove(save_path)


class AbnormalInputTests(unittest.TestCase):
    def test_combat_garbage_input_then_run(self):
        player = Player()
        player.lang = 'EN'
        enemy = Enemy(ENEMIES[0], 'EN')
        inputs = iter(['xyz', '', '99', '4'])
        with mock.patch('builtins.input', lambda *a: next(inputs)), \
             mock.patch('random.random', return_value=0.0), \
             quiet():
            result = combat(player, enemy)
        self.assertEqual(result, 'RUN')
        self.assertEqual(player.hp, player.max_hp)  # garbage cost no hp

    def test_from_dict_with_wrong_types_yields_valid_state(self):
        player = Player()
        player.from_dict({'hp': 'abc', 'potions': None, 'gold': [1],
                          'location': 42, 'active_quest': 'not-a-quest',
                          'kills': {'E_GOPIK': '3'}})
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.potions, 1)
        self.assertEqual(player.gold, 0)
        self.assertEqual(player.location, 'LOC_FOREST')
        self.assertIsNone(player.active_quest)
        self.assertEqual(player.kills, {'E_GOPIK': 3})


if __name__ == '__main__':
    unittest.main()
