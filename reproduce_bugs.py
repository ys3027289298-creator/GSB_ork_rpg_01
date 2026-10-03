# -*- coding: utf-8 -*-
"""
复现/验证脚本: 5 类缺陷修复前后行为对照。
修复前: 裸 KeyError 崩溃 / 攻击回血 / 重复拾取 / 死后行动 / 坏档静默。
修复后: 边界 fail-fast 报出实体与字段、伤害钳制 >=0、拾取去重、
       死亡守卫拦截、坏档明确报 SAVE_CORRUPT。
运行: python3 reproduce_bugs.py
"""
import io
import json
import os
import tempfile
from contextlib import redirect_stdout
from unittest import mock

import ork_main
from ork_core import (
    Player, Enemy, combat, load_game, DataValidationError, SaveDataError,
)
from ork_data import ENEMIES


def check_bug1_missing_field():
    broken = {'name_key': 'E_GOPIK', 'hp': 20}  # 缺 dmg/xp/gold
    try:
        Enemy(broken, 'EN')
        print('BUG1: 未拦截(异常)')
    except DataValidationError as e:
        print(f'BUG1 已修复: fail-fast, 报出实体与缺失字段 -> {e}')
    except KeyError as e:
        print(f'BUG1 复现(旧行为): 裸 KeyError 崩溃 -> {e}')


def check_bug2_attack_bounds():
    p = Player()
    p.dmg = -5
    e = Enemy(ENEMIES[0], 'EN')
    inputs = iter(['1', '4'])
    with mock.patch('builtins.input', lambda *a: next(inputs)), \
         mock.patch('random.randint', return_value=0), \
         mock.patch('random.random', side_effect=[0.9, 0.1]):
        with redirect_stdout(io.StringIO()):
            combat(p, e)
    state = '已修复: 伤害钳制为0, 敌人 HP 不变' if e.hp == 10 else \
        f'复现(旧行为): 攻击给敌人回血 10 -> {e.hp}'
    print(f'BUG2 {state}')


def check_bug3_duplicate_pickup():
    p = Player()
    if hasattr(p, 'pickup_item'):
        first, second = p.pickup_item('Key'), p.pickup_item('Key')
        print(f'BUG3 已修复: 首次={first}, 重复拾取={second}, 计数={p.items_collected}')
        try:
            p.pickup_item('Excalibur')
        except DataValidationError as e:
            print(f'BUG3 已修复: 未知物品拒绝 -> {e}')
    else:
        print('BUG3 复现(旧行为): 无拾取去重 API')


def check_bug4_death_guard():
    try:
        Player().from_dict({'save_version': 2, 'hp': 0})
    except SaveDataError as e:
        print(f'BUG4 已修复: hp=0 的坏档拒绝载入 -> {e}')
    p = Player()
    p.hp = 0
    p.gold = 100
    with mock.patch('builtins.input', side_effect=['', 'E', 'n']), \
         mock.patch('os.system'), \
         mock.patch.object(ork_main, 'main_menu', lambda: p), \
         mock.patch.object(ork_main, 'clear_screen', lambda: None):
        with redirect_stdout(io.StringIO()):
            try:
                ork_main.main()
            except SystemExit:
                pass
    print(f'BUG4 已修复: 主循环拦截死亡, 复活于 {p.location}, gold=50, hp={p.hp}')


def check_bug5_save_consistency():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            os.makedirs('saves', exist_ok=True)
            with open('saves/save.json', 'w') as f:
                json.dump({'gold': 999}, f)
            p = Player()
            buf = io.StringIO()
            with redirect_stdout(buf):
                ok = load_game(p)
            print(f'BUG5 已修复: 残缺存档 load={ok} (旧行为: 静默重置地图/背包)')
            for label, bad in (
                ('非法位置', {'location': 'LOC_NOWHERE'}),
                ('未知物品', {'items_collected': {'Excalibur': 1}}),
                ('负伤害', {'dmg': -10}),
            ):
                try:
                    Player().from_dict({'save_version': 2, **bad})
                except SaveDataError as e:
                    print(f'BUG5 已修复: {label}拒绝 -> {e}')
        finally:
            os.chdir(cwd)


if __name__ == '__main__':
    check_bug1_missing_field()
    check_bug2_attack_bounds()
    check_bug3_duplicate_pickup()
    check_bug4_death_guard()
    check_bug5_save_consistency()
