"""
Diablo: Cataclysm Era - 图形界面版
基于 pygame_ce/tkinter 的暗黑破坏神风格 RPG 游戏
"""
import random
import json
import os
from typing import Optional, List, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ---------------------------- Path Resolution ----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(filename: str) -> str:
    """获取脚本目录下的文件绝对路径"""
    return os.path.join(SCRIPT_DIR, filename)


# ---------------------------- Data Definitions ----------------------------
class Equipment:
    def __init__(self, name: str, atk: int, def_: int, value: int, quality: str = "Common"):
        self.name = name
        self.atk = atk
        self.def_ = def_
        self.value = value
        self.quality = quality

class Player:
    def __init__(self, name: str, hp: int, max_hp: int, mp: int, max_mp: int,
                 base_atk: int, base_def: int, level: int, exp: int, 
                 gold: int, soul: int, weapon: Equipment, armor: Equipment):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.mp = mp
        self.max_mp = max_mp
        self.base_atk = base_atk
        self.base_def = base_def
        self.level = level
        self.exp = exp
        self.gold = gold
        self.soul = soul
        self.weapon = weapon
        self.armor = armor
        self.contract_active = False

    def total_atk(self) -> int:
        return self.base_atk + (self.weapon.atk if self.weapon else 0)

    def total_def(self) -> int:
        return self.base_def + (self.armor.def_ if self.armor else 0)

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self) -> bool:
        return self.hp > 0

    def level_up(self):
        self.level += 1
        self.max_hp += 10
        self.hp = self.max_hp
        self.max_mp += 5
        self.mp = self.max_mp
        self.base_atk += 2
        self.base_def += 2

# 敌人ASCII艺术（定义在Enemy类之前，供Enemy.__init__使用）
ENEMY_ASCII = {
    "Fallen": [
        "    /\\    ",
        "   /  \\   ",
        "  / !! \\  ",
        " /  /\\  \\ ",
        "/___/  \\___\\",
        "    |__|    ",
    ],
    "Goatman": [
        "  \\|//    ",
        "  @****@  ",
        "  (====)  ",
        "  /|  |\\  ",
        " / |  | \\ ",
        "   |  |   ",
    ],
    "Corrupt Mage": [
        "    *     ",
        "   ***    ",
        "  *@*@*   ",
        "   |||    ",
        "  /|||\\  ",
        " / ||| \\ ",
    ],
    "Skeleton King": [
        "   ___    ",
        "  /   \\   ",
        " | X X |  ",
        "  \\ = /  ",
        " __\\|/__ ",
        "/|     |\\",
    ],
}

class Enemy:
    def __init__(self, name: str, hp: int, atk: int, def_: int, exp_reward: int,
                 gold_reward: int, soul_reward: int, quality: str = "Common",
                 ascii_art: Optional[List[str]] = None):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.def_ = def_
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.soul_reward = soul_reward
        self.quality = quality
        self.ascii_art = ascii_art if ascii_art is not None else ENEMY_ASCII.get(name, ["?    ?"])

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp < 0:
            self.hp = 0

    def attack_damage(self) -> int:
        return max(1, self.atk + random.randint(-2, 2))

# ---------------------------- Preset Data ----------------------------
WEAPONS = {
    "Iron Sword": Equipment("Iron Sword", 5, 0, 20, "Common"),
    "Flame Staff": Equipment("Flame Staff", 6, 0, 50, "Rare"),
    "Butcher's Cleaver": Equipment("Butcher's Cleaver", 9, 0, 120, "Epic"),
}
ARMORS = {
    "Leather Armor": Equipment("Leather Armor", 0, 3, 20, "Common"),
    "Chainmail": Equipment("Chainmail", 0, 5, 50, "Rare"),
    "Shadow Cloak": Equipment("Shadow Cloak", 0, 8, 120, "Epic"),
}
ENEMIES = {
    "Fallen": Enemy("Fallen", 20, 6, 2, 30, 15, 1),
    "Goatman": Enemy("Goatman", 35, 9, 4, 60, 30, 2, "Rare"),
    "Corrupt Mage": Enemy("Corrupt Mage", 28, 12, 3, 70, 25, 3, "Rare"),
    "Skeleton King": Enemy("Skeleton King", 70, 14, 8, 150, 80, 10, "Epic"),
}
REGIONS = {
    "Forest": ["Fallen", "Fallen", "Goatman"],
    "Graveyard": ["Skeleton King", "Corrupt Mage", "Fallen"],
    "Dungeon": ["Goatman", "Corrupt Mage", "Corrupt Mage"],
}

# 装备/敌人/词缀名称翻译映射
NAME_TRANSLATIONS = {
    # 武器
    "Iron Sword": {"en": "Iron Sword", "zh": "铁剑"},
    "Flame Staff": {"en": "Flame Staff", "zh": "烈焰法杖"},
    "Butcher's Cleaver": {"en": "Butcher's Cleaver", "zh": "屠夫切肉刀"},
    # 护甲
    "Leather Armor": {"en": "Leather Armor", "zh": "皮甲"},
    "Chainmail": {"en": "Chainmail", "zh": "锁链甲"},
    "Shadow Cloak": {"en": "Shadow Cloak", "zh": "暗影斗篷"},
    # 敌人
    "Fallen": {"en": "Fallen", "zh": "堕落者"},
    "Goatman": {"en": "Goatman", "zh": "羊头魔"},
    "Corrupt Mage": {"en": "Corrupt Mage", "zh": "腐化法师"},
    "Skeleton King": {"en": "Skeleton King", "zh": "骷髅王"},
    # 词缀
    "Flesh Resilience": {"en": "Flesh Resilience", "zh": "血肉韧性"},
    "Hellish Blade": {"en": "Hellish Blade", "zh": "地狱之刃"},
    "Resource Exhaustion": {"en": "Resource Exhaustion", "zh": "资源枯竭"},
    # 区域
    "Forest": {"en": "Forest", "zh": "森林"},
    "Graveyard": {"en": "Graveyard", "zh": "墓地"},
    "Dungeon": {"en": "Dungeon", "zh": "地下城"},
    # 品质
    "Common": {"en": "Common", "zh": "普通"},
    "Rare": {"en": "Rare", "zh": "稀有"},
    "Epic": {"en": "Epic", "zh": "史诗"},
}

def get_translated_name(name: str, lang: str = "en") -> str:
    """获取翻译后的名称"""
    trans = NAME_TRANSLATIONS.get(name, {})
    return trans.get(lang, name)

# ---------------------------- Helper Functions ----------------------------
def save_game(player: Player, filename="save.json"):
    filepath = get_path(filename)
    data = {
        "name": player.name, "hp": player.hp, "max_hp": player.max_hp,
        "mp": player.mp, "max_mp": player.max_mp, "base_atk": player.base_atk,
        "base_def": player.base_def, "level": player.level, "exp": player.exp,
        "gold": player.gold, "soul": player.soul, "contract_active": player.contract_active,
        "weapon": player.weapon.name if player.weapon else None,
        "armor": player.armor.name if player.armor else None,
    }
    try:
        with open(filepath, "w") as f:
            json.dump(data, f)
        return True
    except (PermissionError, IOError) as e:
        print(f"存档失败: {e}")
        return False

def load_game(filename="save.json") -> Optional[Player]:
    filepath = get_path(filename)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        # 校验存档数据完整性
        required_keys = ["name", "hp", "max_hp", "mp", "max_mp", "base_atk",
                        "base_def", "level", "exp", "gold", "soul"]
        for key in required_keys:
            if key not in data:
                print(f"存档损坏：缺少字段 {key}")
                return None
        weapon = WEAPONS.get(data.get("weapon")) if data.get("weapon") else None
        armor = ARMORS.get(data.get("armor")) if data.get("armor") else None
        p = Player(data["name"], data["hp"], data["max_hp"], data["mp"], data["max_mp"],
                   data["base_atk"], data["base_def"], data["level"], data["exp"],
                   data["gold"], data["soul"], weapon, armor)
        p.contract_active = data.get("contract_active", False)
        return p
    except (PermissionError, IOError, json.JSONDecodeError, KeyError) as e:
        print(f"读取存档失败: {e}")
        return None

def random_equipment(quality_bonus: float = 1.0) -> Optional[Equipment]:
    roll = random.random()
    common_max = min(0.95, 0.7 * quality_bonus)
    rare_max = min(0.98, 0.95 * quality_bonus)
    if roll < common_max:
        return random.choice(list(WEAPONS.values()) + list(ARMORS.values()))
    elif roll < rare_max:
        return random.choice([w for w in WEAPONS.values() if w.quality == "Rare"] +
                             [a for a in ARMORS.values() if a.quality == "Rare"])
    else:
        return random.choice([w for w in WEAPONS.values() if w.quality == "Epic"] +
                             [a for a in ARMORS.values() if a.quality == "Epic"])

def save_settings(settings: dict, filename="settings.json"):
    filepath = get_path(filename)
    try:
        with open(filepath, "w") as f:
            json.dump(settings, f)
    except (PermissionError, IOError) as e:
        print(f"设置保存失败: {e}")

def load_settings(filename="settings.json") -> dict:
    filepath = get_path(filename)
    if not os.path.exists(filepath):
        return {"language": "zh", "show_tips": True, "auto_save": True}
    try:
        with open(filepath, "r") as f:
            settings = json.load(f)
        # 确保必要键存在
        settings.setdefault("language", "zh")
        settings.setdefault("show_tips", True)
        settings.setdefault("auto_save", True)
        return settings
    except (PermissionError, IOError, json.JSONDecodeError) as e:
        print(f"读取设置失败: {e}")
        return {"language": "zh", "show_tips": True, "auto_save": True}

# ---------------------------- Language Dictionary ----------------------------
LANG = {
    "en": {
        # Main Menu
        "game_title": "DIABLO",
        "game_subtitle": "CATACLYSM ERA",
        "game_tagline": "Dark Fantasy Action RPG",
        "btn_new_game": "New Game",
        "btn_continue": "Continue",
        "btn_settings": "Settings",
        "btn_exit": "Exit",
        
        # Character Creation
        "create_char_title": "Create Character",
        "create_char_prompt": "Enter character name:",
        "name_required": "Name Required",
        "name_required_msg": "Please enter a character name!",
        "char_created": "Success",
        "char_created_msg": "Character {name} created!",
        
        # Load Game
        "load_success": "Load Success",
        "load_welcome": "Welcome back, {name}!",
        "no_save": "No Save",
        "no_save_msg": "No save file found. Please start a new game.",
        
        # Main Hub
        "main_menu": "Main Menu",
        "btn_explore": "Explore World",
        "btn_workshop": "Hell Workshop",
        "btn_status": "Character Status",
        "btn_contract": "Pain Contract",
        "btn_save": "Save Game",
        "btn_return_menu": "Return to Menu",
        
        # Contract
        "contract_title": "Pain Contract",
        "contract_active": "ACTIVATED",
        "contract_deactivated": "DEACTIVATED",
        "contract_active_msg": "Pain Contract ACTIVATED!\nEnemies +50% stronger, but rewards DOUBLED!",
        "contract_deactivated_msg": "Pain Contract DEACTIVATED!\nEnemies and rewards return to normal.",
        "contract_active_tag": "[PAIN CONTRACT ACTIVE]",
        
        # Save
        "save_title": "Save",
        "save_success": "Game saved successfully!",
        
        # Explore
        "explore_title": "Explore World",
        "select_region": "Select Region:",
        "btn_return_main": "Return to Main",
        "btn_return_explore": "Return to Explore",
        
        # 3D Dungeon
        "dungeon_3d_title": "Dungeon View",
        "dungeon_controls": "Controls:",
        "dungeon_btn_left": "← Left",
        "dungeon_btn_right": "Right →",
        "dungeon_btn_forward": "↑ Forward",
        "dungeon_btn_backward": "↓ Back",
        "btn_enter_battle": "⚔ Enter Battle",
        "btn_exit_dungeon": "← Return to Explore",
        "auto_enter_tip": "Auto-entering battle in 2.5s...",
        
        # Status & Stats
        "level": "Level",
        "exp_tag": "(EXP:",
        "name_tag": "Name:",
        
        # Combat
        "battle": "Battle",
        "enemy": "Enemy",
        "player": "Player",
        "atk": "ATK",
        "def": "DEF",
        "hp": "HP",
        "mp": "MP",
        "combat_log": "Combat Log:",
        "btn_attack": "Attack",
        "btn_heavy": "Heavy Strike (5MP)",
        "btn_defend": "Defend",
        "btn_flee_pct": "Flee (50%)",
        "btn_flee": "Flee",
        "btn_return_main_hub": "Return to Main",
        "btn_return_workshop": "Return to Workshop",
        "def_stance": "[Defense Stance - Next damage halved]",
        "you_dealt": "You dealt {dmg} damage. Enemy HP: {hp}",
        "heavy_dealt": "Heavy strike dealt {dmg} damage! Enemy HP: {hp}",
        "not_enough_mp": "Not enough MP!",
        "def_entered": "You enter defense stance. Next damage halved.",
        "flee_success": "Flee successful!",
        "flee_failed": "Flee failed!",
        "def_reduced": "Defense reduced damage! Enemy dealt {dmg} damage.",
        "enemy_attacked": "Enemy counterattacked for {dmg} damage.",
        "victory": "VICTORY! Gained {exp} EXP, {gold} Gold, {soul} Souls.",
        "pain_contract_bonus": "[PAIN CONTRACT] Rewards DOUBLED!",
        "level_up": "LEVEL UP! Now Level {level}!",
        "level_up_stats": "HP+10 MP+5 ATK+2 DEF+2",
        "equip_obtained": "Equipment obtained: {name} (Quality: {quality})",
        
        # Equipment Dialog
        "new_equip_title": "New Equipment",
        "new_equip_header": "New Equipment!",
        "quality": "Quality",
        "btn_equip_weapon": "Equip as Weapon",
        "btn_equip_armor": "Equip as Armor",
        "btn_discard": "Discard",
        "equipped_weapon": "Weapon equipped: {name}",
        "equipped_armor": "Armor equipped: {name}",
        "discarded": "Discarded equipment.",
        
        # Defeat
        "defeat_title": "Defeat",
        "defeat_msg": "You have fallen! Game Over.",
        
        # Status
        "status_title": "Character Status",
        "basic_info": "=== Basic Info ===",
        "attributes": "=== Attributes ===",
        "equipment": "=== Equipment ===",
        "resources": "=== Resources ===",
        "weapon": "Weapon",
        "armor": "Armor",
        "gold": "Gold",
        "souls": "Souls",
        "pain_contract": "Pain Contract",
        "contract_active_st": "Active",
        "contract_inactive": "Inactive",
        "none": "None",
        "base": "Base",
        "weapon_bonus": "Weapon",
        "armor_bonus": "Armor",
        "soul": "Soul",
        
        # Hell Workshop
        "workshop_title": "Hell Workshop",
        "current_souls": "Current Souls: {souls}",
        "not_enough_souls": "Not enough Souls! Need at least 10 souls.",
        "earn_more": "Defeat monsters or complete challenges to earn more.",
        "btn_back": "Back",
        "create_challenge": "=== Create Custom Challenge ===",
        "map_name_label": "Map Name:",
        "map_default": "Unnamed Trial",
        "difficulty_label": "Difficulty (1-5):",
        "select_affixes": "Select Affixes (Multiple allowed):",
        "cost_label": "Estimated Cost: {cost} souls",
        "btn_start_challenge": "Start Challenge",
        "not_enough_souls_warn": "Not Enough Souls",
        "need_souls_msg": "Need {need} souls, you have {have}.",
        "entering": "Entering: {name}",
        "difficulty_affixes": "Difficulty: {diff} | Affixes: {affixes}",
        "affix_exhaustion": "[Affix] Resource Exhaustion: No MP recovery in combat",
        "challenge_complete": "Challenge Complete! Gained {souls} souls!",
        "bonus_reward": "Bonus reward: {name} (Quality: {quality})",
        "challenge_success": "Challenge Success",
        "challenge_success_msg": "Congratulations! Gained {souls} souls!",
        "challenge_reward_title": "Bonus Reward",
        "challenge_reward_header": "Challenge Reward!",
        "challenge_failed": "Challenge Failed",
        "challenge_failed_msg": "Challenge failed, souls not refunded.\nTry again!",
        "recovered_mp": "Recovered {mp} MP.",
        "exhaustion_active": "[Resource Exhaustion - No MP recovery]",
        "boss": "BOSS",
        "challenger": "Challenger",
        
        # Settings
        "settings_title": "Settings",
        "game_settings": "=== Game Settings ===",
        "show_tips": "Show Tips & Hints",
        "auto_save": "Auto-Save on Exit",
        "language": "Language",
        "english": "English",
        "chinese": "Chinese",
        "about": "=== About ===",
        "about_title": "Diablo: Cataclysm Era",
        "version": "Version 1.0",
        "about_desc": "A Dark Fantasy Action RPG",
        
        # Exit
        "exit_title": "Exit",
        "exit_msg": "Are you sure you want to exit the game?",
        
        # Loading
        "loading_title": "Loading",
        "loading_tip": "Loading game assets...",
        
        # Tips
        "tip_explore": "Explore different regions to find better equipment!",
        "tip_contract": "Pain Contract doubles rewards but makes enemies stronger.",
        "tip_workshop": "Hell Workshop offers challenging custom battles.",
        
        # 区域描述
        "region_forest": "Enemies: Fallen, Goatman",
        "region_graveyard": "Enemies: Skeleton King, Corrupt Mage, Fallen",
        "region_dungeon": "Enemies: Goatman, Corrupt Mage",
        "region_enemies": "Enemies:",
        
        # 词缀
        "affix_flesh": "Enemy HP +50%",
        "affix_hellish": "Enemy ATK +30%",
        "affix_exhaustion_desc": "No MP recovery",
        "affixes_label": "Affixes:",
        
        # 地下城
        "dungeon_pos": "Pos",
        "dungeon_facing": "Facing",
    },
    "zh": {
        # Main Menu
        "game_title": "暗黑破坏神",
        "game_subtitle": "灾厄纪元",
        "game_tagline": "暗黑奇幻动作RPG",
        "btn_new_game": "新游戏",
        "btn_continue": "继续游戏",
        "btn_settings": "设置",
        "btn_exit": "退出",
        
        # Character Creation
        "create_char_title": "创建角色",
        "create_char_prompt": "请输入角色名称：",
        "name_required": "需要名称",
        "name_required_msg": "请输入角色名称！",
        "char_created": "创建成功",
        "char_created_msg": "角色 {name} 创建成功！",
        
        # Load Game
        "load_success": "读取成功",
        "load_welcome": "欢迎回来，{name}！",
        "no_save": "没有存档",
        "no_save_msg": "未找到存档文件，请开始新游戏。",
        
        # Main Hub
        "main_menu": "主菜单",
        "btn_explore": "探索世界",
        "btn_workshop": "地狱工坊",
        "btn_status": "角色状态",
        "btn_contract": "痛苦契约",
        "btn_save": "保存游戏",
        "btn_return_menu": "返回主菜单",
        
        # Contract
        "contract_title": "痛苦契约",
        "contract_active": "已激活",
        "contract_deactivated": "已关闭",
        "contract_active_msg": "痛苦契约已激活！\n敌人强度+50%，但奖励翻倍！",
        "contract_deactivated_msg": "痛苦契约已关闭！\n敌人强度和奖励恢复正常。",
        "contract_active_tag": "【痛苦契约已激活】",
        
        # Save
        "save_title": "保存",
        "save_success": "游戏保存成功！",
        
        # Explore
        "explore_title": "探索世界",
        "select_region": "选择区域：",
        "btn_return_main": "返回主菜单",
        "btn_return_explore": "返回探索",
        
        # 3D Dungeon
        "dungeon_3d_title": "地下城视图",
        "dungeon_controls": "控制：",
        "dungeon_btn_left": "← 左转",
        "dungeon_btn_right": "右转 →",
        "dungeon_btn_forward": "↑ 前进",
        "dungeon_btn_backward": "↓ 后退",
        "btn_enter_battle": "⚔ 进入战斗",
        "btn_exit_dungeon": "← 返回探索",
        "auto_enter_tip": "2.5秒后自动进入战斗...",
        
        # Status & Stats
        "level": "等级",
        "exp_tag": "(经验：",
        "name_tag": "名称：",
        
        # Combat
        "battle": "战斗",
        "enemy": "敌人",
        "player": "玩家",
        "atk": "攻击",
        "def": "防御",
        "hp": "生命",
        "mp": "魔法",
        "combat_log": "战斗日志：",
        "btn_attack": "攻击",
        "btn_heavy": "重击 (5MP)",
        "btn_defend": "防御",
        "btn_flee_pct": "逃跑 (50%)",
        "btn_flee": "逃跑",
        "btn_return_main_hub": "返回主界面",
        "btn_return_workshop": "返回工坊",
        "def_stance": "【防御姿态 - 下次伤害减半】",
        "you_dealt": "你造成了 {dmg} 点伤害。敌人HP：{hp}",
        "heavy_dealt": "重击造成 {dmg} 点伤害！敌人HP：{hp}",
        "not_enough_mp": "魔法值不足！",
        "def_entered": "你进入防御姿态，下次伤害减半。",
        "flee_success": "逃跑成功！",
        "flee_failed": "逃跑失败！",
        "def_reduced": "防御减少伤害！敌人造成 {dmg} 点伤害。",
        "enemy_attacked": "敌人反击，造成 {dmg} 点伤害。",
        "victory": "胜利！获得 {exp} 经验、{gold} 金币、{soul} 魂。",
        "pain_contract_bonus": "【痛苦契约】奖励翻倍！",
        "level_up": "升级！当前等级 {level}！",
        "level_up_stats": "生命+10 魔法+5 攻击+2 防御+2",
        "equip_obtained": "获得装备：{name}（品质：{quality}）",
        
        # Equipment Dialog
        "new_equip_title": "新装备",
        "new_equip_header": "获得新装备！",
        "quality": "品质",
        "btn_equip_weapon": "装备为武器",
        "btn_equip_armor": "装备为护甲",
        "btn_discard": "丢弃",
        "equipped_weapon": "已装备武器：{name}",
        "equipped_armor": "已装备护甲：{name}",
        "discarded": "已丢弃装备。",
        
        # Defeat
        "defeat_title": "战败",
        "defeat_msg": "你倒下了！游戏结束。",
        
        # Status
        "status_title": "角色状态",
        "basic_info": "=== 基本信息 ===",
        "attributes": "=== 属性 ===",
        "equipment": "=== 装备 ===",
        "resources": "=== 资源 ===",
        "weapon": "武器",
        "armor": "护甲",
        "gold": "金币",
        "souls": "魂",
        "pain_contract": "痛苦契约",
        "contract_active_st": "已激活",
        "contract_inactive": "未激活",
        "none": "无",
        "base": "基础",
        "weapon_bonus": "武器",
        "armor_bonus": "护甲",
        "soul": "魂",
        
        # Hell Workshop
        "workshop_title": "地狱工坊",
        "current_souls": "当前魂数：{souls}",
        "not_enough_souls": "魂不足！至少需要10点魂。",
        "earn_more": "击败怪物或完成任务来获取更多魂。",
        "btn_back": "返回",
        "create_challenge": "=== 创建自定义挑战 ===",
        "map_name_label": "地图名称：",
        "map_default": "无名试炼",
        "difficulty_label": "难度 (1-5)：",
        "select_affixes": "选择词缀（可多选）：",
        "cost_label": "预计消耗：{cost} 魂",
        "btn_start_challenge": "开始挑战",
        "not_enough_souls_warn": "魂不足",
        "need_souls_msg": "需要 {need} 魂，你只有 {have} 魂。",
        "entering": "进入：{name}",
        "difficulty_affixes": "难度：{diff} | 词缀：{affixes}",
        "affix_exhaustion": "【词缀】资源枯竭：战斗中无法恢复魔法",
        "challenge_complete": "挑战完成！获得 {souls} 魂！",
        "bonus_reward": "额外奖励：{name}（品质：{quality}）",
        "challenge_success": "挑战成功",
        "challenge_success_msg": "恭喜！获得 {souls} 魂！",
        "challenge_reward_title": "额外奖励",
        "challenge_reward_header": "挑战奖励！",
        "challenge_failed": "挑战失败",
        "challenge_failed_msg": "挑战失败，魂不予退还。\n请再试一次！",
        "recovered_mp": "恢复了 {mp} 点魔法。",
        "exhaustion_active": "【资源枯竭 - 无法恢复魔法】",
        "boss": "首领",
        "challenger": "挑战者",
        
        # Settings
        "settings_title": "设置",
        "game_settings": "=== 游戏设置 ===",
        "show_tips": "显示提示与技巧",
        "auto_save": "退出时自动保存",
        "language": "语言",
        "english": "英语",
        "chinese": "中文",
        "about": "=== 关于 ===",
        "about_title": "暗黑破坏神：灾厄纪元",
        "version": "版本 1.0",
        "about_desc": "一款暗黑奇幻动作RPG游戏",
        
        # Exit
        "exit_title": "退出",
        "exit_msg": "确定要退出游戏吗？",
        
        # Loading
        "loading_title": "加载中",
        "loading_tip": "正在加载游戏资源...",
        
        # Tips
        "tip_explore": "探索不同区域可以找到更好的装备！",
        "tip_contract": "痛苦契约可获得双倍奖励，但敌人也会更强。",
        "tip_workshop": "地狱工坊提供具有挑战性的自定义战斗。",
        
        # 区域描述
        "region_forest": "敌人：堕落者、羊头魔",
        "region_graveyard": "敌人：骷髅王、腐化法师、堕落者",
        "region_dungeon": "敌人：羊头魔、腐化法师",
        "region_enemies": "敌人：",
        
        # 词缀
        "affix_flesh": "敌人生命+50%",
        "affix_hellish": "敌人攻击+30%",
        "affix_exhaustion_desc": "无法恢复魔法",
        "affixes_label": "词缀：",
        
        # 地下城
        "dungeon_pos": "位置",
        "dungeon_facing": "朝向",
    }
}

# ---------------------------- Game GUI Application ----------------------------
class GameGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("暗黑破坏神：灾厄纪元")
        self.root.geometry("900x700")
        self.root.configure(bg="#1a1a1a")
        self.root.resizable(True, True)
        
        # Colors
        self.bg_dark = "#1a1a1a"
        self.bg_medium = "#2d2d2d"
        self.bg_light = "#3d3d3d"
        self.text_gold = "#FFD700"
        self.text_red = "#FF4444"
        self.text_green = "#44FF44"
        self.text_blue = "#4488FF"
        self.text_white = "#FFFFFF"
        self.text_gray = "#888888"
        self.border_color = "#555555"
        
        self.player: Optional[Player] = None
        self.current_enemy: Optional[Enemy] = None
        self.combat_log: List[str] = []
        self.defense_stance = False
        self.is_in_combat = False
        
        # Settings & Language
        self.settings = load_settings()
        self.lang = self.settings.get("language", "zh")
        self._ = lambda key: LANG.get(self.lang, LANG["en"]).get(key, key)
        
        # Preload screen
        self.show_preload()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def show_preload(self):
        """显示预加载界面"""
        self.clear_window()
        
        # Center content
        center_frame = tk.Frame(self.root, bg=self.bg_dark)
        center_frame.pack(expand=True)
        
        # Title
        tk.Label(center_frame, text=self._("game_title"), font=("Arial", 48, "bold"),
                fg=self.text_red, bg=self.bg_dark).pack(pady=(50, 0))
        tk.Label(center_frame, text=self._("game_subtitle"), font=("Arial", 28, "bold"),
                fg=self.text_gold, bg=self.bg_dark).pack()
        
        # Loading bar frame
        load_frame = tk.Frame(center_frame, bg=self.bg_medium, padx=20, pady=20)
        load_frame.pack(pady=50)
        
        tk.Label(load_frame, text=self._("loading_title"), font=("Arial", 14),
                fg=self.text_white, bg=self.bg_medium).pack()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(load_frame, length=300, mode='determinate')
        self.progress_bar.pack(pady=20)
        
        # Progress text
        self.progress_label = tk.Label(load_frame, text="0%", font=("Arial", 12),
                fg=self.text_gold, bg=self.bg_medium)
        self.progress_label.pack()
        
        # Tip text
        tip_key = f"tip_{random.choice(['explore', 'contract', 'workshop'])}"
        tk.Label(load_frame, text=self._(tip_key), font=("Arial", 10),
                fg=self.text_gray, bg=self.bg_medium).pack(pady=10)
        
        # Start loading animation
        self.load_progress = 0
        self.root.after(50, self.update_loading)
    
    def update_loading(self):
        """更新预加载进度"""
        self.load_progress += random.randint(3, 8)
        if self.load_progress > 100:
            self.load_progress = 100
        
        self.progress_bar['value'] = self.load_progress
        self.progress_label.config(text=f"{self.load_progress}%")
        
        if self.load_progress < 100:
            self.root.after(30, self.update_loading)
        else:
            # Loading complete - show main menu after a short delay
            self.root.after(300, self.create_main_menu)
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_title_bar(self, title: str):
        title_frame = tk.Frame(self.root, bg=self.bg_dark, pady=10)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text=title, font=("Arial", 24, "bold"),
                fg=self.text_gold, bg=self.bg_dark).pack()
    
    def create_frame(self, parent, width=None, height=None):
        frame = tk.Frame(parent, bg=self.bg_medium, 
                        highlightbackground=self.border_color,
                        highlightthickness=2, padx=10, pady=10)
        if width:
            frame.config(width=width)
        if height:
            frame.config(height=height)
        return frame
    
    def create_button(self, parent, text, command, color=None, width=20):
        btn_color = color if color else self.bg_light
        btn = tk.Button(parent, text=text, command=command,
                       bg=btn_color, fg=self.text_white,
                       font=("Arial", 12, "bold"), width=width,
                       relief=tk.RAISED, borderwidth=3)
        return btn
    
    def create_label(self, parent, text, color=None, size=12, bold=False):
        font_weight = "bold" if bold else "normal"
        fg_color = color if color else self.text_white
        return tk.Label(parent, text=text, font=("Arial", size, font_weight),
                       fg=fg_color, bg=self.bg_medium)
    
    def on_closing(self):
        if messagebox.askokcancel(self._("exit_title"), self._("exit_msg")):
            save_settings(self.settings)
            if self.player:
                save_game(self.player)
            self.root.destroy()
    
    # ==================== Main Menu ====================
    def create_main_menu(self):
        self.clear_window()
        
        # Title
        title_frame = tk.Frame(self.root, bg=self.bg_dark)
        title_frame.pack(fill=tk.X, pady=50)
        
        tk.Label(title_frame, text=self._("game_title"), font=("Arial", 48, "bold"),
                fg=self.text_red, bg=self.bg_dark).pack()
        tk.Label(title_frame, text=self._("game_subtitle"), font=("Arial", 28, "bold"),
                fg=self.text_gold, bg=self.bg_dark).pack()
        tk.Label(title_frame, text=self._("game_tagline"), font=("Arial", 14),
                fg=self.text_gray, bg=self.bg_dark).pack(pady=10)
        
        # Menu buttons
        btn_frame = tk.Frame(self.root, bg=self.bg_dark)
        btn_frame.pack(pady=30)
        
        self.create_button(btn_frame, self._("btn_new_game"), self.start_game, 
                          self.text_green, 20).pack(pady=10)
        self.create_button(btn_frame, self._("btn_continue"), self.continue_game,
                          self.text_blue, 20).pack(pady=10)
        self.create_button(btn_frame, self._("btn_settings"), self.show_settings,
                          self.text_gold, 20).pack(pady=10)
        self.create_button(btn_frame, self._("btn_exit"), self.root.destroy,
                          self.text_red, 20).pack(pady=10)
    
    def start_game(self):
        name = simpledialog.askstring(self._("create_char_title"), self._("create_char_prompt"), 
                                     parent=self.root)
        if not name or not name.strip():
            messagebox.showwarning(self._("name_required"), self._("name_required_msg"))
            return
        name = name.strip()
        
        self.player = Player(name, 100, 100, 50, 50, 10, 5, 1, 0, 50, 5,
                            WEAPONS["Iron Sword"], ARMORS["Leather Armor"])
        messagebox.showinfo(self._("char_created"), self._("char_created_msg").format(name=name))
        self.show_main_hub()
    
    def continue_game(self):
        loaded = load_game()
        if loaded:
            self.player = loaded
            messagebox.showinfo(self._("load_success"), self._("load_welcome").format(name=self.player.name))
            self.show_main_hub()
        else:
            messagebox.showinfo(self._("no_save"), self._("no_save_msg"))
    
    # ==================== Main Hub ====================
    def show_main_hub(self):
        self.clear_window()
        self.is_in_combat = False
        
        self.create_title_bar(self._("main_menu"))
        
        # Player info bar
        info_frame = self.create_frame(self.root)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = f"{self.player.name} | Level {self.player.level} | "
        info_text += f"{self._('hp')} {self.player.hp}/{self.player.max_hp} | "
        info_text += f"{self._('mp')} {self.player.mp}/{self.player.max_mp} | "
        info_text += f"{self._('gold')} {self.player.gold} | {self._('souls')} {self.player.soul}"
        tk.Label(info_frame, text=info_text, font=("Arial", 11),
                fg=self.text_green, bg=self.bg_medium).pack()
        
        # Main menu buttons
        btn_frame = tk.Frame(self.root, bg=self.bg_dark)
        btn_frame.pack(pady=40)
        
        btns = [
            (self._("btn_explore"), self.show_explore, self.text_green),
            (self._("btn_workshop"), self.show_hell_workshop, self.text_red),
            (self._("btn_status"), self.show_status, self.text_blue),
            (self._("btn_contract"), self.toggle_contract, "#9966FF" if not self.player.contract_active else "#FF66FF"),
            (self._("btn_save"), self.save_current_game, self.text_gold),
            (self._("btn_settings"), self.show_settings, self.text_gray),
            (self._("btn_return_menu"), self.create_main_menu, self.text_gray),
        ]
        
        for text, cmd, color in btns:
            self.create_button(btn_frame, text, cmd, color, 25).pack(pady=8)
    
    def save_current_game(self):
        if save_game(self.player):
            messagebox.showinfo(self._("save_title"), self._("save_success"))
        else:
            messagebox.showerror(self._("save_title"), "存档失败！请检查磁盘空间或文件权限。")
    
    def toggle_contract(self):
        self.player.contract_active = not self.player.contract_active
        status = self._("contract_active") if self.player.contract_active else self._("contract_deactivated")
        if self.player.contract_active:
            msg = self._("contract_active_msg")
        else:
            msg = self._("contract_deactivated_msg")
        messagebox.showinfo(self._("contract_title"), msg)
        self.show_main_hub()
    
    # ==================== Explore ====================
    def show_explore(self):
        self.clear_window()
        self.create_title_bar(self._("explore_title"))
        
        info_frame = self.create_frame(self.root)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        contract_text = self._("contract_active_tag") if self.player.contract_active else ""
        tk.Label(info_frame, 
                text=f"{self.player.name} | {self._('level')} {self.player.level} | {contract_text}",
                font=("Arial", 11), fg=self.text_gold, bg=self.bg_medium).pack()
        
        # Region selection
        region_frame = self.create_frame(self.root)
        region_frame.pack(pady=30, padx=50, fill=tk.BOTH, expand=True)
        
        tk.Label(region_frame, text=self._("select_region"), font=("Arial", 16, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(pady=15)
        
        region_colors = {
            "Forest": "#228B22",
            "Graveyard": "#4A4A4A",
            "Dungeon": "#8B0000"
        }
        
        region_desc_keys = {
            "Forest": "region_forest",
            "Graveyard": "region_graveyard",
            "Dungeon": "region_dungeon"
        }
        
        for region_name in REGIONS.keys():
            color = region_colors.get(region_name, self.text_white)
            desc_key = region_desc_keys.get(region_name)
            desc = self._(desc_key) if desc_key else ""
            region_translated = get_translated_name(region_name, self.lang)
            btn_text = f"{region_translated} - {desc}"
            
            btn = tk.Button(region_frame, text=btn_text, 
                           command=lambda r=region_name: self.start_explore(r),
                           bg=color, fg=self.text_white,
                           font=("Arial", 12), width=40, height=2,
                           relief=tk.RAISED, borderwidth=3)
            btn.pack(pady=8)
        
        self.create_button(region_frame, self._("btn_return_main"), self.show_main_hub, 
                          self.text_gray, 20).pack(pady=20)
    
    def start_explore(self, region: str):
        enemy_name = random.choice(REGIONS[region])
        template = ENEMIES[enemy_name]
        self.current_enemy = Enemy(template.name, template.max_hp, template.atk, template.def_,
                     template.exp_reward, template.gold_reward, template.soul_reward,
                     template.quality,
                     ENEMY_ASCII.get(template.name))
        
        if self.player.contract_active:
            self.current_enemy.max_hp = int(self.current_enemy.max_hp * 1.5)
            self.current_enemy.hp = int(self.current_enemy.hp * 1.5)
            self.current_enemy.atk = int(self.current_enemy.atk * 1.3)
            self.current_enemy.def_ = int(self.current_enemy.def_ * 1.2)
        
        self.is_in_combat = True
        self.defense_stance = False
        self.combat_log = []
        self.show_dungeon_view()
    
    # ==================== 3D Dungeon View (过渡场景) ====================
    def show_dungeon_view(self):
        """3D地下城过渡场景 - 显示3D背景，自动进入战斗"""
        self.clear_window()

        import math
        self.dungeon_pos = [0.0, 0.0]
        self.dungeon_dir = 0.0

        # 墙壁布局
        self.wall_segments = [
            {'p1': (-6, -6), 'p2': (6, -6), 'color_base': (130, 30, 20), 'name': 'outer'},
            {'p1': (6, -6),  'p2': (6, 6),   'color_base': (115, 25, 18), 'name': 'outer'},
            {'p1': (6, 6),   'p2': (-6, 6),  'color_base': (105, 22, 15), 'name': 'outer'},
            {'p1': (-6, 6),  'p2': (-6, -6), 'color_base': (125, 28, 19), 'name': 'outer'},
            {'p1': (-3, -3), 'p2': (-3, -1.5), 'color_base': (170, 90, 45), 'name': 'pillar'},
            {'p1': (-3, -3), 'p2': (-1.5, -3), 'color_base': (165, 85, 40), 'name': 'pillar'},
            {'p1': (3, 3),   'p2': (3, 1.5),   'color_base': (160, 82, 42), 'name': 'pillar'},
            {'p1': (3, 3),   'p2': (1.5, 3),    'color_base': (168, 88, 44), 'name': 'pillar'},
            {'p1': (-3, 2),  'p2': (-1.5, 2),   'color_base': (162, 84, 41), 'name': 'pillar'},
            {'p1': (2, -3),  'p2': (3, -3),     'color_base': (158, 80, 39), 'name': 'pillar'},
        ]

        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True)

        canvas_w, canvas_h = 860, 460
        self.canvas_width = canvas_w
        self.canvas_height = canvas_h
        self.dungeon_canvas = tk.Canvas(main_frame, width=canvas_w, height=canvas_h,
                                        bg="#050202", highlightthickness=0)
        self.dungeon_canvas.pack(pady=(10, 4))

        # 敌人名字标签
        enemy_name_label = tk.Label(main_frame,
                text=f"{self._('enemy')}: {get_translated_name(self.current_enemy.name, self.lang)}",
                font=("Arial", 14, "bold"), fg=self.text_red, bg=self.bg_medium)
        enemy_name_label.pack(pady=(2, 4))

        self.raycast_render()

        # 底部提示（唯一按钮）
        bot_frame = self.create_frame(main_frame)
        bot_frame.pack(pady=6, fill=tk.X)

        self.dungeon_pos_label = tk.Label(bot_frame, text="", font=("Arial", 9),
                fg=self.text_gray, bg=self.bg_medium)
        self.dungeon_pos_label.pack(pady=2)

        tk.Label(bot_frame, text=self._("auto_enter_tip"), font=("Arial", 10),
                fg=self.text_gray, bg=self.bg_medium).pack(pady=3)

        tk.Button(bot_frame, text=self._("btn_enter_battle"), command=self.show_combat,
                 bg="#8B0000", fg="#FFD700", font=("Arial", 12, "bold"),
                 width=20, height=2, relief=tk.RAISED, borderwidth=3, cursor="hand2").pack(pady=4)

        # 自动切换计时器：2.5秒后自动进入战斗
        self.dungeon_timer = self.root.after(2500, self.show_combat)

    def raycast_render(self):
        """射线投射渲染"""
        import math
        canvas = self.dungeon_canvas
        W = self.canvas_width
        H = self.canvas_height
        canvas.delete("all")

        px, py = self.dungeon_pos
        angle = self.dungeon_dir
        FOV = math.pi / 3
        num_rays = 172
        strip_w = W / num_rays

        dir_x = math.cos(angle)
        dir_y = math.sin(angle)

        # 天花板渐变
        horizon = H // 2
        for y in range(horizon):
            t = y / horizon
            r, g, b = int(18 + t * 35), int(4 + t * 12), int(4 + t * 10)
            canvas.create_line(0, y, W, y, fill=f"#{r:02x}{g:02x}{b:02x}")

        # 地板渐变
        for y in range(horizon, H):
            t = (y - horizon) / horizon
            r = int(28 * (1 - t * 0.7))
            g = int(14 * (1 - t * 0.7))
            b = int(4 * (1 - t * 0.6))
            canvas.create_line(0, y, W, y, fill=f"#{max(r,3):02x}{max(g,1):02x}{max(b,1):02x}")

        # 射线投射
        half_fov = FOV / 2
        for i in range(num_rays):
            ray_angle = angle - half_fov + (i / num_rays) * FOV
            rd_x = math.cos(ray_angle)
            rd_y = math.sin(ray_angle)

            best_t = float('inf')
            best_wall = None

            for wall in self.wall_segments:
                x1, y1 = wall['p1']
                x2, y2 = wall['p2']
                wx, wy = x2 - x1, y2 - y1
                denom = rd_x * wy - rd_y * wx
                if abs(denom) < 1e-10:
                    continue
                t = ((x1 - px) * wy - (y1 - py) * wx) / denom
                u = ((x1 - px) * rd_y - (y1 - py) * rd_x) / denom
                if t > 0.05 and 0 <= u <= 1 and t < best_t:
                    best_t = t
                    best_wall = wall

            if best_wall is not None and best_t < float('inf'):
                # 鱼眼校正：垂直于相机方向的距离
                cos_a = rd_x * dir_x + rd_y * dir_y
                perp_dist = max(best_t * cos_a, 0.05)

                wall_h = min(H * 1.6, H / perp_dist)
                top = horizon - wall_h / 2
                bottom = horizon + wall_h / 2

                shade = max(0.12, min(1.0, 4.5 / perp_dist))
                cr, cg, cb = best_wall['color_base']
                r = min(255, int(cr * shade))
                g = min(255, int(cg * shade))
                b = min(255, int(cb * shade))

                sx = int(i * strip_w)
                sw = max(int(strip_w) + 1, 1)
                canvas.create_rectangle(sx, int(top), sx + sw, int(bottom),
                                       fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
                # 顶部高光
                er = min(255, int((cr + 70) * shade))
                eg = min(255, int((cg + 50) * shade))
                eb = min(255, int((cb + 25) * shade))
                canvas.create_line(sx, int(top), sx + sw, int(top),
                                   fill=f"#{er:02x}{eg:02x}{eb:02x}", width=1)
                # 柱子纹理线
                if best_wall['name'] == 'pillar' and i % 7 == 0:
                    ty = int(top + wall_h * 0.4)
                    tr, tg, tb = max(2, int(r*0.5)), max(1, int(g*0.5)), max(1, int(b*0.5))
                    canvas.create_line(sx, ty, sx + sw, ty,
                                       fill=f"#{tr:02x}{tg:02x}{tb:02x}", width=1)

        # 准星（十字）
        cx, cy = W // 2, H // 2
        canvas.create_oval(cx-3, cy-3, cx+3, cy+3, outline="#FFD700", width=2)
        canvas.create_line(cx-9, cy, cx-14, cy, fill="#FFD700", width=2)
        canvas.create_line(cx+9, cy, cx+14, cy, fill="#FFD700", width=2)

        # 小地图
        msz = 88
        mmx, mmy = W - msz - 8, 8
        sc = msz / 14.0   # 映射 [-7,7] 到 [0,msz]
        canvas.create_rectangle(mmx, mmy, mmx + msz, mmy + msz,
                               fill="#111", outline="#555")
        for ws in self.wall_segments:
            wx1 = mmx + (ws['p1'][0] + 7) * sc
            wy1 = mmy + (ws['p1'][1] + 7) * sc
            wx2 = mmx + (ws['p2'][0] + 7) * sc
            wy2 = mmy + (ws['p2'][1] + 7) * sc
            c = "#c33" if ws['name'] == 'outer' else "#a74"
            canvas.create_line(wx1, wy1, wx2, wy2, fill=c, width=2)
        ppx = mmx + (px + 7) * sc
        ppy = mmy + (py + 7) * sc
        canvas.create_oval(ppx-4, ppy-4, ppx+4, ppy+4, fill="#FF0", outline="")
        canvas.create_line(ppx, ppy, ppx + dir_x * 14, ppy + dir_y * 14,
                           fill="#FF0", width=2)

    def _on_dungeon_key(self, event):
        """键盘控制"""
        k = event.keysym.lower()
        import math
        if k in ('w', 'up'):
            self.dungeon_move(0.35)
        elif k in ('s', 'down'):
            self.dungeon_move(-0.35)
        elif k in ('a', 'left'):
            self.dungeon_rotate(-math.pi / 16)
        elif k in ('d', 'right'):
            self.dungeon_rotate(math.pi / 16)
        elif k == 'escape':
            self.show_explore()

    def dungeon_rotate(self, delta: float):
        """旋转视角"""
        import math
        self.dungeon_dir = (self.dungeon_dir + delta) % (2 * math.pi)
        self.raycast_render()
        self._refresh_pos_label()

    def dungeon_move(self, dist: float):
        """移动"""
        import math
        dx = math.cos(self.dungeon_dir) * dist
        dy = math.sin(self.dungeon_dir) * dist
        nx = self.dungeon_pos[0] + dx
        ny = self.dungeon_pos[1] + dy
        if -5.5 < nx < 5.5:
            self.dungeon_pos[0] = nx
        if -5.5 < ny < 5.5:
            self.dungeon_pos[1] = ny
        self.raycast_render()
        self._refresh_pos_label()

    def _refresh_pos_label(self):
        import math
        if not hasattr(self, 'dungeon_pos_label') or self.dungeon_pos_label is None:
            return
        deg = int(self.dungeon_dir * 180 / math.pi) % 360
        txt = f"{self._('dungeon_pos')} ({self.dungeon_pos[0]:+.1f}, {self.dungeon_pos[1]:+.1f}) | {self._('dungeon_facing')} {deg}°"
        self.dungeon_pos_label.config(text=txt)
    
    # ==================== Combat ====================
    def show_combat(self):
        self.clear_window()
        self.create_title_bar(self._("battle"))
        
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Enemy frame (左侧ASCII + 右侧数据)
        enemy_frame = self.create_frame(main_frame)
        enemy_frame.pack(fill=tk.X, pady=5)

        quality_color = {"Common": self.text_white, "Rare": self.text_blue, "Epic": self.text_red}
        qcolor = quality_color.get(self.current_enemy.quality, self.text_white)

        # 左侧：ASCII艺术
        ascii_frame = tk.Frame(enemy_frame, bg=self.bg_dark)
        ascii_frame.pack(side=tk.LEFT, padx=10)
        for line in self.current_enemy.ascii_art:
            tk.Label(ascii_frame, text=line, font=("Courier New", 10),
                    fg=qcolor, bg=self.bg_dark).pack(anchor=tk.W)

        # 右侧：敌人数据
        data_frame = tk.Frame(enemy_frame, bg=self.bg_medium)
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(data_frame, text=f"{self._('enemy')}: {get_translated_name(self.current_enemy.name, self.lang)}",
                font=("Arial", 16, "bold"), fg=qcolor, bg=self.bg_medium).pack()
        
        # Enemy HP bar
        hp_frame = tk.Frame(enemy_frame, bg=self.bg_medium)
        hp_frame.pack(fill=tk.X, pady=5)
        tk.Label(hp_frame, text=f"{self._('hp')}: {self.current_enemy.hp}/{self.current_enemy.max_hp}",
                font=("Arial", 12), fg=self.text_red, bg=self.bg_medium).pack(side=tk.LEFT)
        
        enemy_hp_percent = self.current_enemy.hp / self.current_enemy.max_hp
        enemy_hp_bar = tk.Canvas(hp_frame, width=300, height=20, bg=self.bg_dark, highlightthickness=0)
        enemy_hp_bar.create_rectangle(0, 0, 300 * enemy_hp_percent, 20, fill="#FF4444")
        enemy_hp_bar.create_rectangle(300 * enemy_hp_percent, 0, 300, 20, fill="#333333")
        enemy_hp_bar.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(enemy_frame, text=f"{self._('atk')}: {self.current_enemy.atk}  {self._('def')}: {self.current_enemy.def_}",
                font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack()
        
        # Player frame
        player_frame = self.create_frame(main_frame)
        player_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(player_frame, text=f"{self._('player')}: {self.player.name}",
                font=("Arial", 14, "bold"), fg=self.text_gold, bg=self.bg_medium).pack()
        
        # Player HP and MP bars
        stats_frame = tk.Frame(player_frame, bg=self.bg_medium)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # HP bar
        hp_bar_frame = tk.Frame(stats_frame, bg=self.bg_medium)
        hp_bar_frame.pack(fill=tk.X, pady=2)
        tk.Label(hp_bar_frame, text=f"{self._('hp')}: {self.player.hp}/{self.player.max_hp}",
                font=("Arial", 11), fg=self.text_green, bg=self.bg_medium).pack(side=tk.LEFT)
        player_hp_canvas = tk.Canvas(hp_bar_frame, width=250, height=15, bg=self.bg_dark, highlightthickness=0)
        player_hp_canvas.create_rectangle(0, 0, 250 * (self.player.hp / self.player.max_hp), 15, fill="#44FF44")
        player_hp_canvas.create_rectangle(250 * (self.player.hp / self.player.max_hp), 0, 250, 15, fill="#333333")
        player_hp_canvas.pack(side=tk.RIGHT, padx=10)
        
        # MP bar
        mp_bar_frame = tk.Frame(stats_frame, bg=self.bg_medium)
        mp_bar_frame.pack(fill=tk.X, pady=2)
        tk.Label(mp_bar_frame, text=f"{self._('mp')}: {self.player.mp}/{self.player.max_mp}",
                font=("Arial", 11), fg=self.text_blue, bg=self.bg_medium).pack(side=tk.LEFT)
        player_mp_canvas = tk.Canvas(mp_bar_frame, width=250, height=15, bg=self.bg_dark, highlightthickness=0)
        player_mp_canvas.create_rectangle(0, 0, 250 * (self.player.mp / self.player.max_mp), 15, fill="#4488FF")
        player_mp_canvas.create_rectangle(250 * (self.player.mp / self.player.max_mp), 0, 250, 15, fill="#333333")
        player_mp_canvas.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(player_frame, text=f"{self._('atk')}: {self.player.total_atk()}  {self._('def')}: {self.player.total_def()}",
                font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack()
        
        if self.defense_stance:
            tk.Label(player_frame, text=self._("def_stance"),
                    font=("Arial", 11, "bold"), fg="#FFAA00", bg=self.bg_medium).pack()
        
        # Combat log
        log_frame = self.create_frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(log_frame, text=self._("combat_log"), font=("Arial", 12, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(anchor=tk.W)
        
        log_text = tk.Text(log_frame, height=10, width=70, bg=self.bg_dark,
                          fg=self.text_white, font=("Consolas", 10), state=tk.DISABLED)
        log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        for msg in self.combat_log[-15:]:
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, msg + "\n")
            log_text.config(state=tk.DISABLED)
        log_text.see(tk.END)
        
        # Action buttons
        action_frame = tk.Frame(main_frame, bg=self.bg_dark)
        action_frame.pack(pady=10)
        
        if self.player.is_alive() and self.current_enemy.is_alive():
            self.create_button(action_frame, self._("btn_attack"), lambda: self.combat_action("attack"),
                             self.text_green, 15).pack(side=tk.LEFT, padx=5)
            
            mp_color = self.text_blue if self.player.mp >= 5 else self.text_gray
            self.create_button(action_frame, self._("btn_heavy"), 
                             lambda: self.combat_action("heavy"), mp_color, 15).pack(side=tk.LEFT, padx=5)
            
            stance_color = "#FFAA00" if not self.defense_stance else self.text_gray
            self.create_button(action_frame, self._("btn_defend"),
                             lambda: self.combat_action("defend"), stance_color, 15).pack(side=tk.LEFT, padx=5)
            
            self.create_button(action_frame, self._("btn_flee_pct"),
                             lambda: self.combat_action("flee"), self.text_gray, 15).pack(side=tk.LEFT, padx=5)
        else:
            self.create_button(action_frame, self._("btn_return_main_hub"), self.show_main_hub,
                             self.text_blue, 20).pack(pady=10)
        
        self.create_button(action_frame, self._("btn_return_main_hub"), self.show_main_hub,
                          self.text_gray, 15).pack(side=tk.LEFT, padx=5)
    
    def add_log(self, msg: str):
        self.combat_log.append(msg)
    
    def combat_action(self, action: str):
        if action == "attack":
            dmg = max(1, self.player.total_atk() - self.current_enemy.def_ + random.randint(-2, 2))
            self.current_enemy.take_damage(dmg)
            self.add_log(self._("you_dealt").format(dmg=dmg, hp=self.current_enemy.hp))
            
        elif action == "heavy":
            if self.player.mp >= 5:
                dmg = max(1, self.player.total_atk() * 2 - self.current_enemy.def_ + random.randint(-2, 2))
                self.current_enemy.take_damage(dmg)
                self.player.mp -= 5
                self.add_log(self._("heavy_dealt").format(dmg=dmg, hp=self.current_enemy.hp))
            else:
                self.add_log(self._("not_enough_mp"))
                self.show_combat()
                return
                
        elif action == "defend":
            self.defense_stance = True
            self.add_log(self._("def_entered"))
            
        elif action == "flee":
            if random.random() < 0.5:
                self.add_log(self._("flee_success"))
                self.show_main_hub()
                return
            else:
                self.add_log(self._("flee_failed"))
        
        # Enemy counterattack
        if self.current_enemy.is_alive():
            enemy_dmg = self.current_enemy.attack_damage()
            if self.defense_stance:
                enemy_dmg = max(1, enemy_dmg // 2)
                self.add_log(self._("def_reduced").format(dmg=enemy_dmg))
                self.defense_stance = False
            else:
                self.add_log(self._("enemy_attacked").format(dmg=enemy_dmg))
            self.player.take_damage(enemy_dmg)
        
        self.show_combat()
        
        # Check for battle end
        if not self.current_enemy.is_alive():
            self.root.after(500, self.combat_victory)
        elif not self.player.is_alive():
            self.root.after(500, self.combat_defeat)
    
    def combat_victory(self):
        self.show_combat()  # 先显示战斗界面和日志
        
        gain_exp = self.current_enemy.exp_reward
        gain_gold = self.current_enemy.gold_reward
        gain_soul = self.current_enemy.soul_reward
        
        if self.player.contract_active:
            gain_exp = int(gain_exp * 1.5)
            gain_gold = int(gain_gold * 2)
            gain_soul = int(gain_soul * 2)
            self.add_log(self._("pain_contract_bonus"))
        
        self.player.exp += gain_exp
        self.player.gold += gain_gold
        self.player.soul += gain_soul
        
        self.add_log(self._("victory").format(exp=gain_exp, gold=gain_gold, soul=gain_soul))
        
        # Level up check
        if self.player.exp >= self.player.level * 100:
            self.player.level_up()
            self.add_log(self._("level_up").format(level=self.player.level))
            self.add_log(self._("level_up_stats"))
        
        # Refresh display with new logs
        self.show_combat()
        
        # Equipment drop
        drop = random_equipment(1.5 if self.player.contract_active else 1.0)
        if drop:
            drop_name = get_translated_name(drop.name, self.lang)
            drop_quality = get_translated_name(drop.quality, self.lang)
            self.root.after(100, lambda: self.add_log(self._("equip_obtained").format(name=drop_name, quality=drop_quality)))
            self.root.after(200, lambda: self.handle_equipment_drop(drop))
    
    def handle_equipment_drop(self, equipment: Equipment):
        dialog = tk.Toplevel(self.root)
        dialog.title(self._("new_equip_title"))
        dialog.geometry("400x250")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)
        dialog.grab_set()
        
        quality_color = {"Common": self.text_white, "Rare": self.text_blue, "Epic": self.text_red}
        qcolor = quality_color.get(equipment.quality, self.text_white)
        
        tk.Label(dialog, text=self._("new_equip_header"), font=("Arial", 16, "bold"),
                fg=self.text_gold, bg=self.bg_dark).pack(pady=15)
        
        equip_name = get_translated_name(equipment.name, self.lang)
        equip_quality = get_translated_name(equipment.quality, self.lang)
        info = f"{equip_name}\nATK: +{equipment.atk}  DEF: +{equipment.def_}\n{self._('quality')}: {equip_quality}"
        tk.Label(dialog, text=info, font=("Arial", 12), fg=qcolor,
                bg=self.bg_dark).pack(pady=10)
        
        btn_frame = tk.Frame(dialog, bg=self.bg_dark)
        btn_frame.pack(pady=20)
        
        def equip_weapon():
            dialog.destroy()
            self.player.weapon = equipment
            self.add_log(f"{self._('equipped_weapon').format(name=get_translated_name(equipment.name, self.lang))}")
            self.show_combat()
        
        def equip_armor():
            dialog.destroy()
            self.player.armor = equipment
            self.add_log(f"{self._('equipped_armor').format(name=get_translated_name(equipment.name, self.lang))}")
            self.show_combat()
        
        def discard():
            dialog.destroy()
            self.add_log(self._("discarded"))
            self.show_combat()
        
        if equipment.atk > 0:
            tk.Button(btn_frame, text=self._("btn_equip_weapon"), command=equip_weapon,
                     bg=self.text_green, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        if equipment.def_ > 0:
            tk.Button(btn_frame, text=self._("btn_equip_armor"), command=equip_armor,
                     bg=self.text_blue, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=self._("btn_discard"), command=discard,
                 bg=self.text_gray, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
    
    def combat_defeat(self):
        messagebox.showinfo(self._("defeat_title"), self._("defeat_msg"))
        self.create_main_menu()
    
    # ==================== Status ====================
    def show_status(self):
        self.clear_window()
        self.create_title_bar(self._("status_title"))
        
        # 返回按钮固定在底部（先pack，显示在最下方）
        btn_frame = tk.Frame(self.root, bg=self.bg_dark)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=15)
        self.create_button(btn_frame, self._("btn_return_main_hub"), self.show_main_hub,
                          self.text_green, 20).pack(pady=5)
        
        # 可滚动内容区域
        canvas = tk.Canvas(self.root, bg=self.bg_dark, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_dark)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 鼠标滚轮绑定
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=20)
        
        # Basic info
        basic_frame = self.create_frame(scrollable_frame)
        basic_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(basic_frame, text=self._("basic_info"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack()
        tk.Label(basic_frame, text=f"{self._('name_tag')} {self.player.name}",
                font=("Arial", 12), fg=self.text_white, bg=self.bg_medium).pack()
        tk.Label(basic_frame, text=f"{self._('level')}: {self.player.level}  {self._('exp_tag')} {self.player.exp}/{self.player.level*100})",
                font=("Arial", 12), fg=self.text_white, bg=self.bg_medium).pack()
        
        # Stats
        stats_frame = self.create_frame(scrollable_frame)
        stats_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(stats_frame, text=self._("attributes"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack()
        
        # HP
        tk.Label(stats_frame, text=f"{self._('hp')}: {self.player.hp}/{self.player.max_hp}",
                font=("Arial", 12), fg=self.text_green, bg=self.bg_medium).pack(anchor=tk.W)
        hp_canvas = tk.Canvas(stats_frame, width=400, height=20, bg=self.bg_dark, highlightthickness=0)
        hp_canvas.create_rectangle(0, 0, 400 * (self.player.hp / self.player.max_hp), 20, fill="#44FF44")
        hp_canvas.create_rectangle(400 * (self.player.hp / self.player.max_hp), 0, 400, 20, fill="#333333")
        hp_canvas.pack()
        
        # MP
        tk.Label(stats_frame, text=f"{self._('mp')}: {self.player.mp}/{self.player.max_mp}",
                font=("Arial", 12), fg=self.text_blue, bg=self.bg_medium).pack(anchor=tk.W)
        mp_canvas = tk.Canvas(stats_frame, width=400, height=20, bg=self.bg_dark, highlightthickness=0)
        mp_canvas.create_rectangle(0, 0, 400 * (self.player.mp / self.player.max_mp), 20, fill="#4488FF")
        mp_canvas.create_rectangle(400 * (self.player.mp / self.player.max_mp), 0, 400, 20, fill="#333333")
        mp_canvas.pack()
        
        tk.Label(stats_frame, text=f"{self._('atk')}: {self.player.total_atk()} ({self._('base')} {self.player.base_atk} + {self._('weapon_bonus')} {self.player.weapon.atk if self.player.weapon else 0})",
                font=("Arial", 12), fg=self.text_red, bg=self.bg_medium).pack(anchor=tk.W)
        tk.Label(stats_frame, text=f"{self._('def')}: {self.player.total_def()} ({self._('base')} {self.player.base_def} + {self._('armor_bonus')} {self.player.armor.def_ if self.player.armor else 0})",
                font=("Arial", 12), fg=self.text_gray, bg=self.bg_medium).pack(anchor=tk.W)
        
        # Currency & Equipment
        equip_frame = self.create_frame(scrollable_frame)
        equip_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(equip_frame, text=self._("equipment"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack()
        
        if self.player.weapon:
            wq_color = {"Common": self.text_white, "Rare": self.text_blue, "Epic": self.text_red}.get(self.player.weapon.quality, self.text_white)
            weapon_name = get_translated_name(self.player.weapon.name, self.lang)
            tk.Label(equip_frame, text=f"{self._('weapon')}: {weapon_name} (ATK+{self.player.weapon.atk})",
                    font=("Arial", 11), fg=wq_color, bg=self.bg_medium).pack(anchor=tk.W)
        else:
            tk.Label(equip_frame, text=f"{self._('weapon')}: {self._('none')}",
                    font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack(anchor=tk.W)
        
        if self.player.armor:
            aq_color = {"Common": self.text_white, "Rare": self.text_blue, "Epic": self.text_red}.get(self.player.armor.quality, self.text_white)
            armor_name = get_translated_name(self.player.armor.name, self.lang)
            tk.Label(equip_frame, text=f"{self._('armor')}: {armor_name} (DEF+{self.player.armor.def_})",
                    font=("Arial", 11), fg=aq_color, bg=self.bg_medium).pack(anchor=tk.W)
        else:
            tk.Label(equip_frame, text=f"{self._('armor')}: {self._('none')}",
                    font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack(anchor=tk.W)
        
        tk.Label(equip_frame, text=self._("resources"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(pady=(10,0))
        tk.Label(equip_frame, text=f"{self._('gold')}: {self.player.gold}",
                font=("Arial", 12), fg=self.text_gold, bg=self.bg_medium).pack(anchor=tk.W)
        tk.Label(equip_frame, text=f"{self._('souls')}: {self.player.soul}",
                font=("Arial", 12), fg="#9933FF", bg=self.bg_medium).pack(anchor=tk.W)
        
        contract_color = "#FF66FF" if self.player.contract_active else self.text_gray
        contract_text = self._("contract_active_st") if self.player.contract_active else self._("contract_inactive")
        tk.Label(equip_frame, text=f"{self._('pain_contract')}: {contract_text}",
                font=("Arial", 12, "bold"), fg=contract_color, bg=self.bg_medium).pack(anchor=tk.W)
    
    # ==================== Hell Workshop ====================
    def show_hell_workshop(self):
        self.clear_window()
        self.create_title_bar(self._("workshop_title"))
        
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info_frame = self.create_frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text=self._("current_souls").format(souls=self.player.soul),
                font=("Arial", 14, "bold"), fg="#9933FF", bg=self.bg_medium).pack()
        
        if self.player.soul < 10:
            tk.Label(info_frame, text=self._("not_enough_souls"),
                    font=("Arial", 12), fg=self.text_red, bg=self.bg_medium).pack()
            tk.Label(info_frame, text=self._("earn_more"),
                    font=("Arial", 10), fg=self.text_gray, bg=self.bg_medium).pack()
            self.create_button(main_frame, self._("btn_back"), self.show_main_hub,
                             self.text_gray, 15).pack(pady=20)
            return
        
        # Map creation
        create_frame = self.create_frame(main_frame)
        create_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(create_frame, text=self._("create_challenge"),
                font=("Arial", 14, "bold"), fg=self.text_red, bg=self.bg_medium).pack(pady=10)
        
        # Map name
        name_frame = tk.Frame(create_frame, bg=self.bg_medium)
        name_frame.pack(fill=tk.X, pady=5)
        tk.Label(name_frame, text=self._("map_name_label"), font=("Arial", 12),
                fg=self.text_white, bg=self.bg_medium).pack(side=tk.LEFT)
        map_name_entry = tk.Entry(name_frame, font=("Arial", 12), width=30)
        map_name_entry.insert(0, self._("map_default"))
        map_name_entry.pack(side=tk.RIGHT, padx=10)
        
        # Difficulty
        diff_frame = tk.Frame(create_frame, bg=self.bg_medium)
        diff_frame.pack(fill=tk.X, pady=5)
        tk.Label(diff_frame, text=self._("difficulty_label"), font=("Arial", 12),
                fg=self.text_white, bg=self.bg_medium).pack(side=tk.LEFT)
        diff_var = tk.IntVar(value=1)
        diff_spin = tk.Spinbox(diff_frame, from_=1, to=5, textvariable=diff_var,
                              font=("Arial", 12), width=10)
        diff_spin.pack(side=tk.RIGHT, padx=10)
        
        # Affixes
        tk.Label(create_frame, text=self._("select_affixes"),
                font=("Arial", 12), fg=self.text_gold, bg=self.bg_medium).pack(pady=(15,5))
        
        affixes_vars = {}
        affixes_list = [
            ("Flesh Resilience", "affix_flesh", "#FF6666"),
            ("Hellish Blade", "affix_hellish", "#FFAA00"),
            ("Resource Exhaustion", "affix_exhaustion_desc", "#6666FF"),
        ]
        
        for name, desc_key, color in affixes_list:
            desc = self._(desc_key)
            var = tk.BooleanVar(value=False)
            affixes_vars[name] = var
            display_name = get_translated_name(name, self.lang)
            cb = tk.Checkbutton(create_frame, text=f"{display_name}: {desc}",
                              variable=var, font=("Arial", 10), fg=color,
                              bg=self.bg_medium, selectcolor=self.bg_dark)
            cb.pack(anchor=tk.W, padx=20)
        
        # Cost preview
        def update_cost(*args):
            difficulty = diff_var.get()
            affix_count = sum(1 for v in affixes_vars.values() if v.get())
            cost = 10 + difficulty * 5 + affix_count * 3
            cost_label.config(text=self._("cost_label").format(cost=cost))
        
        diff_var.trace_add("write", update_cost)
        for v in affixes_vars.values():
            v.trace_add("write", update_cost)
        
        cost_label = tk.Label(create_frame, text=self._("cost_label").format(cost=15),
                            font=("Arial", 12, "bold"), fg=self.text_green, bg=self.bg_medium)
        cost_label.pack(pady=10)
        
        # Start button
        def start_challenge():
            difficulty = diff_var.get()
            affixes = [name for name, var in affixes_vars.items() if var.get()]
            cost = 10 + difficulty * 5 + len(affixes) * 3
            
            if self.player.soul < cost:
                messagebox.showwarning(self._("not_enough_souls_warn"), 
                    self._("need_souls_msg").format(need=cost, have=self.player.soul))
                return
            
            map_name = map_name_entry.get().strip() or self._("map_default")
            self.player.soul -= cost
            
            self.start_custom_battle(map_name, difficulty, affixes)
        
        btn_frame = tk.Frame(create_frame, bg=self.bg_medium)
        btn_frame.pack(pady=15)
        self.create_button(btn_frame, self._("btn_start_challenge"), start_challenge,
                          self.text_red, 15).pack(side=tk.LEFT, padx=10)
        self.create_button(btn_frame, self._("btn_return_main"), self.show_main_hub,
                          self.text_gray, 15).pack(side=tk.LEFT, padx=10)
    
    def start_custom_battle(self, map_name: str, difficulty: int, affixes: List[str]):
        base_enemy = ENEMIES["Skeleton King"]
        self.current_enemy = Enemy(base_enemy.name, base_enemy.max_hp, base_enemy.atk, base_enemy.def_,
                     base_enemy.exp_reward, base_enemy.gold_reward, base_enemy.soul_reward,
                     base_enemy.quality,
                     ENEMY_ASCII.get(base_enemy.name))
        
        # Apply difficulty
        self.current_enemy.max_hp = int(self.current_enemy.max_hp * (1 + 0.2 * difficulty))
        self.current_enemy.hp = self.current_enemy.max_hp
        self.current_enemy.atk = int(self.current_enemy.atk * (1 + 0.15 * difficulty))
        self.current_enemy.def_ = int(self.current_enemy.def_ * (1 + 0.1 * difficulty))
        
        # Apply affixes
        if "Flesh Resilience" in affixes:
            self.current_enemy.max_hp = int(self.current_enemy.max_hp * 1.5)
            self.current_enemy.hp = self.current_enemy.max_hp
        if "Hellish Blade" in affixes:
            self.current_enemy.atk = int(self.current_enemy.atk * 1.3)
        
        has_exhaustion = "Resource Exhaustion" in affixes
        
        self.is_in_combat = True
        self.defense_stance = False
        affixes_translated = [get_translated_name(a, self.lang) for a in affixes]
        self.combat_log = [
            self._("entering").format(name=map_name), 
            self._("difficulty_affixes").format(diff=difficulty, affixes=', '.join(affixes_translated) if affixes_translated else self._('none'))
        ]
        if has_exhaustion:
            self.combat_log.append(self._("affix_exhaustion"))
        
        self.custom_battle_data = {
            "difficulty": difficulty,
            "affixes": affixes,
            "has_exhaustion": has_exhaustion
        }
        
        self.show_custom_combat()
    
    def show_custom_combat(self):
        self.clear_window()
        self.create_title_bar(f"{self._('workshop_title')} - {self._('battle')}")
        
        data = getattr(self, 'custom_battle_data', {})
        affixes_translated = [get_translated_name(a, self.lang) for a in data.get('affixes', [])]
        map_info = f"{self._('difficulty_label').replace(':', '')} {data.get('difficulty', 1)} | {self._('affixes_label')} {', '.join(affixes_translated) if affixes_translated else self._('none')}"
        
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(main_frame, text=map_info, font=("Arial", 11),
                fg=self.text_red, bg=self.bg_dark).pack()
        
        # Enemy frame (左侧ASCII + 右侧数据)
        enemy_frame = self.create_frame(main_frame)
        enemy_frame.pack(fill=tk.X, pady=5)

        # ASCII艺术
        ascii_frame = tk.Frame(enemy_frame, bg=self.bg_dark)
        ascii_frame.pack(side=tk.LEFT, padx=10)
        for line in self.current_enemy.ascii_art:
            tk.Label(ascii_frame, text=line, font=("Courier New", 10),
                    fg=self.text_red, bg=self.bg_dark).pack(anchor=tk.W)

        data_frame = tk.Frame(enemy_frame, bg=self.bg_medium)
        data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(data_frame, text=f"{self._('boss')}: {get_translated_name(self.current_enemy.name, self.lang)}",
                font=("Arial", 18, "bold"), fg=self.text_red, bg=self.bg_medium).pack()
        
        hp_frame = tk.Frame(enemy_frame, bg=self.bg_medium)
        hp_frame.pack(fill=tk.X, pady=5)
        tk.Label(hp_frame, text=f"{self._('hp')}: {self.current_enemy.hp}/{self.current_enemy.max_hp}",
                font=("Arial", 12), fg=self.text_red, bg=self.bg_medium).pack(side=tk.LEFT)
        
        enemy_hp_percent = self.current_enemy.hp / self.current_enemy.max_hp
        enemy_hp_bar = tk.Canvas(hp_frame, width=300, height=20, bg=self.bg_dark, highlightthickness=0)
        enemy_hp_bar.create_rectangle(0, 0, 300 * enemy_hp_percent, 20, fill="#FF4444")
        enemy_hp_bar.create_rectangle(300 * enemy_hp_percent, 0, 300, 20, fill="#333333")
        enemy_hp_bar.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(enemy_frame, text=f"{self._('atk')}: {self.current_enemy.atk}  {self._('def')}: {self.current_enemy.def_}",
                font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack()
        
        # Player frame
        player_frame = self.create_frame(main_frame)
        player_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(player_frame, text=f"{self._('challenger')}: {self.player.name}",
                font=("Arial", 14, "bold"), fg=self.text_gold, bg=self.bg_medium).pack()
        
        stats_frame = tk.Frame(player_frame, bg=self.bg_medium)
        stats_frame.pack(fill=tk.X, pady=5)
        
        hp_bar_frame = tk.Frame(stats_frame, bg=self.bg_medium)
        hp_bar_frame.pack(fill=tk.X, pady=2)
        tk.Label(hp_bar_frame, text=f"{self._('hp')}: {self.player.hp}/{self.player.max_hp}",
                font=("Arial", 11), fg=self.text_green, bg=self.bg_medium).pack(side=tk.LEFT)
        player_hp_canvas = tk.Canvas(hp_bar_frame, width=250, height=15, bg=self.bg_dark, highlightthickness=0)
        player_hp_canvas.create_rectangle(0, 0, 250 * (self.player.hp / self.player.max_hp), 15, fill="#44FF44")
        player_hp_canvas.create_rectangle(250 * (self.player.hp / self.player.max_hp), 0, 250, 15, fill="#333333")
        player_hp_canvas.pack(side=tk.RIGHT, padx=10)
        
        mp_bar_frame = tk.Frame(stats_frame, bg=self.bg_medium)
        mp_bar_frame.pack(fill=tk.X, pady=2)
        tk.Label(mp_bar_frame, text=f"{self._('mp')}: {self.player.mp}/{self.player.max_mp}",
                font=("Arial", 11), fg=self.text_blue, bg=self.bg_medium).pack(side=tk.LEFT)
        player_mp_canvas = tk.Canvas(mp_bar_frame, width=250, height=15, bg=self.bg_dark, highlightthickness=0)
        player_mp_canvas.create_rectangle(0, 0, 250 * (self.player.mp / self.player.max_mp), 15, fill="#4488FF")
        player_mp_canvas.create_rectangle(250 * (self.player.mp / self.player.max_mp), 0, 250, 15, fill="#333333")
        player_mp_canvas.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(player_frame, text=f"{self._('atk')}: {self.player.total_atk()}  {self._('def')}: {self.player.total_def()}",
                font=("Arial", 11), fg=self.text_gray, bg=self.bg_medium).pack()
        
        if self.defense_stance:
            tk.Label(player_frame, text=self._("def_stance"),
                    font=("Arial", 11, "bold"), fg="#FFAA00", bg=self.bg_medium).pack()
        
        if data.get('has_exhaustion'):
            tk.Label(player_frame, text=self._("exhaustion_active"),
                    font=("Arial", 11, "bold"), fg="#6666FF", bg=self.bg_medium).pack()
        
        # Combat log
        log_frame = self.create_frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(log_frame, text=self._("combat_log"), font=("Arial", 12, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(anchor=tk.W)
        
        log_text = tk.Text(log_frame, height=10, width=70, bg=self.bg_dark,
                          fg=self.text_white, font=("Consolas", 10), state=tk.DISABLED)
        log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        for msg in self.combat_log[-15:]:
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, msg + "\n")
            log_text.config(state=tk.DISABLED)
        log_text.see(tk.END)
        
        # Action buttons
        action_frame = tk.Frame(main_frame, bg=self.bg_dark)
        action_frame.pack(pady=10)
        
        if self.player.is_alive() and self.current_enemy.is_alive():
            self.create_button(action_frame, self._("btn_attack"), lambda: self.custom_combat_action("attack"),
                             self.text_green, 15).pack(side=tk.LEFT, padx=5)
            
            mp_color = self.text_blue if self.player.mp >= 5 else self.text_gray
            self.create_button(action_frame, self._("btn_heavy"), 
                             lambda: self.custom_combat_action("heavy"), mp_color, 15).pack(side=tk.LEFT, padx=5)
            
            stance_color = "#FFAA00" if not self.defense_stance else self.text_gray
            self.create_button(action_frame, self._("btn_defend"),
                             lambda: self.custom_combat_action("defend"), stance_color, 15).pack(side=tk.LEFT, padx=5)
            
            self.create_button(action_frame, self._("btn_flee"),
                             lambda: self.custom_combat_action("flee"), self.text_gray, 15).pack(side=tk.LEFT, padx=5)
        else:
            self.create_button(action_frame, self._("btn_return_workshop"), self.show_hell_workshop,
                             self.text_blue, 20).pack(pady=10)
        
        self.create_button(action_frame, self._("btn_return_main_hub"), self.show_main_hub,
                          self.text_gray, 15).pack(side=tk.LEFT, padx=5)
    
    def custom_combat_action(self, action: str):
        data = getattr(self, 'custom_battle_data', {})
        has_exhaustion = data.get('has_exhaustion', False)
        
        if action == "attack":
            dmg = max(1, self.player.total_atk() - self.current_enemy.def_ + random.randint(-2, 2))
            self.current_enemy.take_damage(dmg)
            self.add_log(self._("you_dealt").format(dmg=dmg, hp=self.current_enemy.hp))
            
        elif action == "heavy":
            if self.player.mp >= 5:
                dmg = max(1, self.player.total_atk() * 2 - self.current_enemy.def_ + random.randint(-2, 2))
                self.current_enemy.take_damage(dmg)
                self.player.mp -= 5
                self.add_log(self._("heavy_dealt").format(dmg=dmg, hp=self.current_enemy.hp))
            else:
                self.add_log(self._("not_enough_mp"))
                self.show_custom_combat()
                return
                
        elif action == "defend":
            self.defense_stance = True
            self.add_log(self._("def_entered"))
            
        elif action == "flee":
            if random.random() < 0.5:
                self.add_log(self._("flee_success"))
                self.show_hell_workshop()
                return
            else:
                self.add_log(self._("flee_failed"))
        
        # Enemy counterattack
        if self.current_enemy.is_alive():
            enemy_dmg = self.current_enemy.attack_damage()
            if self.defense_stance:
                enemy_dmg = max(1, enemy_dmg // 2)
                self.add_log(self._("def_reduced").format(dmg=enemy_dmg))
                self.defense_stance = False
            else:
                self.add_log(self._("enemy_attacked").format(dmg=enemy_dmg))
            self.player.take_damage(enemy_dmg)
            
            # MP recovery (unless exhausted)
            if not has_exhaustion and self.player.is_alive():
                old_mp = self.player.mp
                self.player.mp = min(self.player.max_mp, self.player.mp + 5)
                if self.player.mp > old_mp:
                    self.add_log(self._("recovered_mp").format(mp=self.player.mp - old_mp))
        
        self.show_custom_combat()
        
        # Check for battle end
        if not self.current_enemy.is_alive():
            self.root.after(500, self.custom_victory)
        elif not self.player.is_alive():
            self.root.after(500, self.custom_defeat)
    
    def custom_victory(self):
        self.show_custom_combat()  # 先显示战斗界面
        
        data = getattr(self, 'custom_battle_data', {})
        difficulty = data.get('difficulty', 1)
        affixes = data.get('affixes', [])
        
        bonus = difficulty * 10 + len(affixes) * 5
        self.player.soul += bonus
        
        self.add_log(self._("challenge_complete").format(souls=bonus))
        
        self.show_custom_combat()  # 刷新显示
        
        # Extra equipment drop
        extra_drop = random_equipment(1 + difficulty * 0.2)
        if extra_drop:
            drop_name = get_translated_name(extra_drop.name, self.lang)
            drop_quality = get_translated_name(extra_drop.quality, self.lang)
            self.root.after(100, lambda: self.add_log(self._("bonus_reward").format(name=drop_name, quality=drop_quality)))
            self.root.after(200, lambda: self.handle_custom_equipment_drop(extra_drop))
        else:
            self.root.after(300, lambda: messagebox.showinfo(
                self._("challenge_success"), 
                self._("challenge_success_msg").format(souls=bonus)
            ))
            self.root.after(400, self.show_hell_workshop)
    
    def handle_custom_equipment_drop(self, equipment: Equipment):
        dialog = tk.Toplevel(self.root)
        dialog.title(self._("challenge_reward_title"))
        dialog.geometry("400x250")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)
        dialog.grab_set()
        
        quality_color = {"Common": self.text_white, "Rare": self.text_blue, "Epic": self.text_red}
        qcolor = quality_color.get(equipment.quality, self.text_white)
        
        tk.Label(dialog, text=self._("challenge_reward_header"), font=("Arial", 16, "bold"),
                fg=self.text_gold, bg=self.bg_dark).pack(pady=15)
        
        equip_name = get_translated_name(equipment.name, self.lang)
        equip_quality = get_translated_name(equipment.quality, self.lang)
        info = f"{equip_name}\nATK: +{equipment.atk}  DEF: +{equipment.def_}\n{self._('quality')}: {equip_quality}"
        tk.Label(dialog, text=info, font=("Arial", 12), fg=qcolor,
                bg=self.bg_dark).pack(pady=10)
        
        btn_frame = tk.Frame(dialog, bg=self.bg_dark)
        btn_frame.pack(pady=20)
        
        def equip_weapon():
            dialog.destroy()
            self.player.weapon = equipment
            messagebox.showinfo(self._("new_equip_title"), self._("equipped_weapon").format(name=get_translated_name(equipment.name, self.lang)))
            self.show_hell_workshop()
        
        def equip_armor():
            dialog.destroy()
            self.player.armor = equipment
            messagebox.showinfo(self._("new_equip_title"), self._("equipped_armor").format(name=get_translated_name(equipment.name, self.lang)))
            self.show_hell_workshop()
        
        def discard():
            dialog.destroy()
            self.show_hell_workshop()
        
        if equipment.atk > 0:
            tk.Button(btn_frame, text=self._("btn_equip_weapon"), command=equip_weapon,
                     bg=self.text_green, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        if equipment.def_ > 0:
            tk.Button(btn_frame, text=self._("btn_equip_armor"), command=equip_armor,
                     bg=self.text_blue, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=self._("btn_discard"), command=discard,
                 bg=self.text_gray, fg=self.text_white, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
    
    def custom_defeat(self):
        messagebox.showinfo(self._("challenge_failed"), self._("challenge_failed_msg"))
        self.show_hell_workshop()
    
    # ==================== Settings ====================
    def show_settings(self):
        self.clear_window()
        self.create_title_bar(self._("settings_title"))
        
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Settings frame
        settings_frame = self.create_frame(main_frame)
        settings_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(settings_frame, text=self._("game_settings"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(pady=10)
        
        # Language selection
        lang_frame = tk.Frame(settings_frame, bg=self.bg_medium)
        lang_frame.pack(fill=tk.X, pady=10, padx=20)
        
        tk.Label(lang_frame, text=self._("language") + ":", font=("Arial", 12),
                fg=self.text_white, bg=self.bg_medium).pack(side=tk.LEFT, padx=10)
        
        lang_var = tk.StringVar(value=self.lang)
        
        def on_lang_change():
            new_lang = lang_var.get()
            if new_lang in ["en", "zh"]:
                self.lang = new_lang
                self.settings["language"] = new_lang
                self._ = lambda key: LANG.get(self.lang, LANG["en"]).get(key, key)
                save_settings(self.settings)
                self.show_settings()  # Refresh UI with new language
        
        tk.Radiobutton(lang_frame, text=self._("english"), variable=lang_var, value="en",
                      font=("Arial", 11), fg=self.text_white, bg=self.bg_medium,
                      selectcolor=self.bg_dark, command=on_lang_change).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(lang_frame, text=self._("chinese"), variable=lang_var, value="zh",
                      font=("Arial", 11), fg=self.text_white, bg=self.bg_medium,
                      selectcolor=self.bg_dark, command=on_lang_change).pack(side=tk.LEFT, padx=10)
        
        # Tips toggle
        tips_var = tk.BooleanVar(value=bool(self.settings.get("show_tips", True)))
        tk.Checkbutton(settings_frame, text=self._("show_tips"),
                      variable=tips_var, font=("Arial", 12), fg=self.text_white,
                      bg=self.bg_medium, selectcolor=self.bg_dark,
                      command=lambda: self.update_setting("show_tips", bool(tips_var.get()))).pack(anchor=tk.W, padx=20, pady=5)
        
        # Auto-save toggle
        auto_save_var = tk.BooleanVar(value=bool(self.settings.get("auto_save", True)))
        tk.Checkbutton(settings_frame, text=self._("auto_save"),
                      variable=auto_save_var, font=("Arial", 12), fg=self.text_white,
                      bg=self.bg_medium, selectcolor=self.bg_dark,
                      command=lambda: self.update_setting("auto_save", bool(auto_save_var.get()))).pack(anchor=tk.W, padx=20, pady=5)
        
        # About frame
        about_frame = self.create_frame(main_frame)
        about_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(about_frame, text=self._("about"), font=("Arial", 14, "bold"),
                fg=self.text_gold, bg=self.bg_medium).pack(pady=10)
        
        tk.Label(about_frame, text=self._("about_title"), font=("Arial", 12, "bold"),
                fg=self.text_red, bg=self.bg_medium).pack()
        tk.Label(about_frame, text=self._("version"), font=("Arial", 10),
                fg=self.text_gray, bg=self.bg_medium).pack()
        tk.Label(about_frame, text=self._("about_desc"), font=("Arial", 10),
                fg=self.text_gray, bg=self.bg_medium).pack(pady=5)
        
        # Back button - 根据是否有玩家决定返回位置
        btn_frame = tk.Frame(main_frame, bg=self.bg_dark)
        btn_frame.pack(pady=20)
        if self.player:
            self.create_button(btn_frame, self._("btn_return_main_hub"), self.show_main_hub,
                              self.text_green, 20).pack(pady=5)
        self.create_button(btn_frame, self._("btn_return_menu"), self.create_main_menu,
                          self.text_blue, 20).pack(pady=5)
    
    def update_setting(self, key: str, value: Any):
        self.settings[key] = value
        save_settings(self.settings)

# ---------------------------- Main Entry Point ----------------------------
if __name__ == "__main__":
    app = GameGUI()
