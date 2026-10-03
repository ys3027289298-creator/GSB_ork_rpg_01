# -*- coding: utf-8 -*-
"""
测试: 数据解析、状态迁移(存档)、异常输入。
运行: python3 -m unittest test_ork -v
"""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import ork_main
from ork_core import (
    Player, Enemy, combat, save_game, load_game,
    compute_attack_damage, handle_death, known_items,
    validate_enemy, validate_item,
    DataValidationError, SaveDataError, SAVE_VERSION, KNOWN_LOCATIONS,
)
from ork_data import TEXTS, ENEMIES, QUESTS, LOCATIONS


def run_combat(player, enemy, inputs, randint=0, randoms=None):
    """Run combat with scripted input/randomness, return (result, output)."""
    it = iter(inputs)
    randoms = iter(randoms if randoms is not None else [0.9] * 100)
    buf = io.StringIO()
    with mock.patch('builtins.input', lambda *a: next(it)), \
         mock.patch('random.randint', return_value=randint), \
         mock.patch('random.random', side_effect=lambda *a: next(randoms)):
        with redirect_stdout(buf):
            result = combat(player, enemy)
    return result, buf.getvalue()


def make_enemy(idx=0):
    return Enemy(ENEMIES[idx], 'EN')


class TestDataParsing(unittest.TestCase):
    """ork_data 是单一事实来源: 解析边界必须 fail-fast。"""

    def test_all_shipped_enemies_are_valid(self):
        for lang in TEXTS:
            for data in ENEMIES:
                validate_enemy(data, lang)  # 不抛异常
                e = Enemy(data, lang)
                self.assertGreater(e.hp, 0)
                self.assertGreaterEqual(e.dmg, 0)

    def test_missing_field_raises_naming_entity_and_fields(self):
        broken = {'name_key': 'E_GOPIK', 'hp': 20}  # 缺 dmg/xp/gold
        with self.assertRaises(DataValidationError) as ctx:
            Enemy(broken, 'EN')
        msg = str(ctx.exception)
        self.assertIn('E_GOPIK', msg)
        for field in ('dmg', 'xp', 'gold'):
            self.assertIn(field, msg)

    def test_missing_name_key_and_bad_type(self):
        with self.assertRaises(DataValidationError):
            Enemy({'hp': 10, 'dmg': 1, 'xp': 1, 'gold': 1}, 'EN')
        with self.assertRaises(DataValidationError):
            validate_enemy(['not', 'a', 'dict'])

    def test_out_of_range_stats_rejected(self):
        base = dict(ENEMIES[0])
        for field, bad in (('hp', 0), ('hp', -5), ('dmg', -1), ('xp', -1),
                           ('gold', -1), ('hp', 'ten')):
            data = dict(base, **{field: bad})
            with self.assertRaises(DataValidationError, msg=f'{field}={bad}'):
                validate_enemy(data)

    def test_unlocalized_name_key_rejected(self):
        data = dict(ENEMIES[0], name_key='E_NOPE')
        with self.assertRaises(DataValidationError):
            Enemy(data, 'EN')

    def test_item_validation_against_data(self):
        # 已知物品来自 ork_data 的 loot 表 + Potion
        self.assertIn('Potion', known_items())
        for loc in LOCATIONS.values():
            for item in loc['loot']:
                validate_item(item)  # 不抛异常
        with self.assertRaises(DataValidationError):
            validate_item('Excalibur')
        with self.assertRaises(DataValidationError):
            validate_item(123)

    def test_duplicate_pickup_rejected(self):
        p = Player()
        self.assertTrue(p.pickup_item('Key'))
        self.assertFalse(p.pickup_item('Key'))  # 重复拾取不重复计数
        self.assertEqual(p.items_collected, {'Key': 1})
        with self.assertRaises(DataValidationError):
            p.pickup_item('Excalibur')


class TestAttackBounds(unittest.TestCase):
    """攻击公式越界: 伤害必须 >= 0, 攻击绝不能给敌人回血。"""

    def test_negative_dmg_clamped_to_zero(self):
        p = Player()
        p.dmg = -5
        with mock.patch('random.randint', return_value=0), \
             mock.patch('random.random', return_value=0.9):
            dmg, crit = compute_attack_damage(p)
        self.assertEqual(dmg, 0)
        self.assertFalse(crit)

    def test_normal_and_crit_damage(self):
        p = Player()  # dmg = 5
        with mock.patch('random.randint', return_value=2), \
             mock.patch('random.random', return_value=0.9):
            self.assertEqual(compute_attack_damage(p), (7, False))
        with mock.patch('random.randint', return_value=2), \
             mock.patch('random.random', return_value=0.1):
            self.assertEqual(compute_attack_damage(p), (int(7 * 1.5), True))

    def test_combat_attack_never_heals_enemy(self):
        p = Player()
        p.dmg = -5
        e = make_enemy(0)  # hp 10
        # 攻击一次(不暴击)然后逃跑成功
        result, _ = run_combat(p, e, ['1', '4'], randint=0, randoms=[0.9, 0.1])
        self.assertEqual(result, 'RUN')
        self.assertEqual(e.hp, 10)  # 修复前: 10 -> 15


class TestDeathGuard(unittest.TestCase):
    """死亡后不能继续移动/行动。"""

    def test_is_alive(self):
        p = Player()
        self.assertTrue(p.is_alive)
        p.hp = 0
        self.assertFalse(p.is_alive)

    def test_handle_death_respawns_at_tent(self):
        p = Player()
        p.hp = 0
        p.gold = 101
        p.location = 'LOC_DUNGEON'
        handle_death(p)
        self.assertTrue(p.is_alive)
        self.assertEqual(p.location, 'LOC_HOME')
        self.assertEqual(p.gold, 50)

    def test_main_loop_blocks_dead_player(self):
        # 主循环遇到 hp<=0 必须先复活惩罚, 而不是让玩家继续行动
        p = Player()
        p.hp = 0
        p.gold = 100
        gold_before, day_before = p.gold, p.day
        with mock.patch('builtins.input', side_effect=['', 'E', 'n']), \
             mock.patch('os.system'), \
             mock.patch.object(ork_main, 'main_menu', lambda: p), \
             mock.patch.object(ork_main, 'clear_screen', lambda: None):
            with redirect_stdout(io.StringIO()):
                try:
                    ork_main.main()
                except SystemExit:
                    pass
        self.assertEqual(p.location, 'LOC_HOME')
        self.assertEqual(p.gold, gold_before // 2)
        self.assertEqual(p.day, day_before)  # 死亡当天没有推进


class TestSaveMigration(unittest.TestCase):
    """退出重进一致性: 存档必须完整合法, 否则报错而非静默默认化。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def roundtrip_player(self):
        p = Player()
        p.lang = 'EN'
        p.gold = 77
        p.potions = 3
        p.location = 'LOC_DUNGEON'
        p.day = 9
        p.pickup_item('Key')
        p.pickup_item('Wood')
        p.active_quest = QUESTS[1]
        p.quest_progress = 2
        return p

    def test_roundtrip_preserves_map_and_inventory(self):
        p = self.roundtrip_player()
        save_game(p)
        q = Player()
        self.assertTrue(load_game(q))
        self.assertEqual(q.to_dict(), p.to_dict())
        self.assertEqual(q.location, 'LOC_DUNGEON')
        self.assertEqual(q.items_collected, {'Key': 1, 'Wood': 1})
        self.assertEqual(q.potions, 3)

    def write_save(self, obj):
        os.makedirs('saves', exist_ok=True)
        with open('saves/save.json', 'w') as f:
            json.dump(obj, f)

    def assert_load_rejected(self, obj):
        self.write_save(obj)
        p = Player()
        p.gold = 5
        with redirect_stdout(io.StringIO()) as buf:
            ok = load_game(p)
        self.assertFalse(ok)
        self.assertIn(TEXTS[p.lang]['SAVE_CORRUPT'], buf.getvalue())
        self.assertEqual(p.gold, 5)  # 失败不污染当前状态

    def test_no_save_file(self):
        self.assertFalse(load_game(Player()))

    def test_broken_json(self):
        os.makedirs('saves', exist_ok=True)
        with open('saves/save.json', 'w') as f:
            f.write('{not json')
        with redirect_stdout(io.StringIO()):
            self.assertFalse(load_game(Player()))

    def test_incomplete_save_rejected(self):
        self.assert_load_rejected({'gold': 999})  # 旧版/残缺存档

    def test_version_mismatch_rejected(self):
        data = self.roundtrip_player().to_dict()
        data['save_version'] = SAVE_VERSION + 1
        self.assert_load_rejected(data)

    def test_unknown_location_rejected(self):
        data = self.roundtrip_player().to_dict()
        data['location'] = 'LOC_NOWHERE'
        self.assert_load_rejected(data)

    def test_unknown_item_rejected(self):
        data = self.roundtrip_player().to_dict()
        data['items_collected'] = {'Excalibur': 1}
        self.assert_load_rejected(data)

    def test_negative_stats_rejected(self):
        for field in ('dmg', 'gold', 'potions', 'lvl', 'xp', 'day'):
            data = self.roundtrip_player().to_dict()
            data[field] = -1
            self.assert_load_rejected(data)

    def test_hp_above_max_rejected(self):
        data = self.roundtrip_player().to_dict()
        data['hp'] = data['max_hp'] + 1
        self.assert_load_rejected(data)

    def test_unknown_quest_rejected(self):
        data = self.roundtrip_player().to_dict()
        data['active_quest'] = {'id': 999}
        self.assert_load_rejected(data)

    def test_from_dict_atomic_on_failure(self):
        p = Player()
        p.location = 'LOC_RIVER'
        with self.assertRaises(SaveDataError):
            p.from_dict({'save_version': SAVE_VERSION, 'hp': 10})
        self.assertEqual(p.location, 'LOC_RIVER')  # 校验失败不留下半迁移状态


class TestAbnormalInput(unittest.TestCase):
    """异常输入不应崩溃或产生非法状态。"""

    def test_combat_garbage_input_then_run(self):
        p = Player()
        e = make_enemy(0)
        # 乱按: 空串/字母/超范围数字, 最后逃跑(0.1 < 0.5 成功)
        result, out = run_combat(p, e, ['', 'x', '99', '4'], randoms=[0.1])
        self.assertEqual(result, 'RUN')
        self.assertIn(TEXTS['RU']['ERROR_INPUT'], out)

    def test_potion_without_potions_not_negative(self):
        p = Player()
        p.potions = 0
        e = make_enemy(0)
        result, out = run_combat(p, e, ['3', '3', '4'], randoms=[0.1])
        self.assertEqual(result, 'RUN')
        self.assertEqual(p.potions, 0)  # 不会变成 -1
        self.assertIn(TEXTS['RU']['NO_POTIONS'], out)

    def test_combat_win_grants_rewards(self):
        p = Player()
        e = make_enemy(0)  # hp 10, xp 5, gold 5
        result, _ = run_combat(p, e, ['1'] * 5, randint=2, randoms=[0.9] * 5)
        self.assertEqual(result, 'WIN')
        self.assertEqual(p.gold, 5)
        self.assertEqual(p.xp, 5)

    def test_quest_menu_garbage_input(self):
        p = Player()
        with mock.patch('builtins.input', side_effect=['abc', '999', '']), \
             mock.patch.object(ork_main, 'clear_screen', lambda: None):
            with redirect_stdout(io.StringIO()):
                ork_main.action_quests(p)
        self.assertIsNone(p.active_quest)  # 非法 ID 不接任务


if __name__ == '__main__':
    unittest.main()
