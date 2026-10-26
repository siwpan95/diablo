"""Headless self-check for Diablo: Cataclysm Era.

Exercises the non-GUI layers only: data models, save-file round trip
(with backup fallback) and the navigation state machine. tkinter/gui.py is
never imported, so no window is created.

Usage: python selfcheck.py
"""

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class Checker:
    """Collects failures so every check runs before exiting."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passed: list[str] = []

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passed.append(label)
            print(f"  ok   {label}")
        else:
            message = f"{label}: {detail}" if detail else label
            self.failures.append(message)
            print(f"  FAIL {message}")

    def section(self, title: str) -> None:
        print(f"[{title}]")


class FakeGUI:
    """Stand-in for GameGUI: records screen renders, creates no widgets."""

    def __init__(self) -> None:
        self.player = None
        self.rendered: list[str] = []

    def _record(self, name: str) -> None:
        self.rendered.append(name)

    def create_main_menu(self) -> None:
        self._record("create_main_menu")

    def show_main_hub(self) -> None:
        self._record("show_main_hub")

    def show_explore(self) -> None:
        self._record("show_explore")

    def show_dungeon_view(self) -> None:
        self._record("show_dungeon_view")

    def show_combat(self) -> None:
        self._record("show_combat")

    def show_settings(self) -> None:
        self._record("show_settings")

    def show_status(self) -> None:
        self._record("show_status")

    def show_hell_workshop(self) -> None:
        self._record("show_hell_workshop")

    def show_custom_combat(self) -> None:
        self._record("show_custom_combat")

    def show_preload(self) -> None:
        self._record("show_preload")


def check_models(c: Checker) -> None:
    """Player/Enemy arithmetic must follow the documented rules."""
    c.section("models")
    from data import ARMORS, WEAPONS
    from models import Enemy, Player

    p = Player("Hero", 80, 100, 10, 30, 12, 4, 3, 120, 500, 9,
               WEAPONS["Iron Sword"], ARMORS["Leather Armor"])
    c.check(
        "total_atk / total_def add base + equipment",
        p.total_atk() == 17 and p.total_def() == 7,
        f"atk={p.total_atk()} def={p.total_def()}",
    )

    p.take_damage(999)
    c.check("take_damage floors HP at 0", p.hp == 0 and not p.is_alive(), f"hp={p.hp}")

    p.heal(999)
    c.check("heal caps at max HP", p.hp == 100, f"hp={p.hp}")

    p.level_up()
    c.check(
        "level_up grants +10 HP/+5 MP/+2 ATK/+2 DEF and refills",
        (p.level, p.max_hp, p.hp, p.max_mp, p.mp, p.base_atk, p.base_def)
        == (4, 110, 110, 35, 35, 14, 6),
        f"({p.level},{p.max_hp},{p.hp},{p.max_mp},{p.mp},{p.base_atk},{p.base_def})",
    )

    enemy = Enemy("Zombie", 30, 7, 1, 10, 5, 2)
    samples = [enemy.attack_damage() for _ in range(200)]
    c.check(
        "enemy attack_damage stays in atk+-2 and is never 0",
        all(1 <= d <= 9 for d in samples),
        f"min={min(samples)} max={max(samples)}",
    )
    c.check("enemy starts alive", enemy.is_alive() and enemy.hp == enemy.max_hp)


def check_storage(c: Checker) -> None:
    """Save/load round trip, backup fallback, and settings persistence."""
    c.section("storage")
    import storage
    from data import ARMORS, WEAPONS
    from models import Player

    tmpdir = tempfile.mkdtemp(prefix="diablo-selfcheck-")
    original_get_path = storage.get_path
    # Redirect all storage paths into a throw-away dir: the project's real
    # save.json / save.backup.json / settings.json are never touched.
    storage.get_path = lambda filename: os.path.join(tmpdir, filename)
    try:
        player = Player("Tester", 77, 90, 12, 20, 10, 3, 4, 33, 250, 7,
                        WEAPONS["Iron Sword"], ARMORS["Leather Armor"])
        player.contract_active = True

        c.check("save_game writes the save file", storage.save_game(player, "s.json") is True)
        c.check("save file exists on disk", os.path.exists(os.path.join(tmpdir, "s.json")))

        loaded = storage.load_game("s.json")
        c.check(
            "load_game rebuilds every scalar field",
            loaded is not None
            and (loaded.name, loaded.hp, loaded.max_hp, loaded.mp, loaded.max_mp)
            == ("Tester", 77, 90, 12, 20)
            and (loaded.level, loaded.exp, loaded.gold, loaded.soul, loaded.contract_active)
            == (4, 33, 250, 7, True),
            f"got {loaded!r}",
        )
        c.check(
            "equipment is resolved back from its name",
            loaded is not None
            and loaded.weapon is not None and loaded.weapon.name == "Iron Sword"
            and loaded.armor is not None and loaded.armor.name == "Leather Armor",
            "weapon/armor not restored",
        )
        c.check(
            "restored player totals match the original",
            loaded is not None and loaded.total_atk() == 15 and loaded.total_def() == 6,
            f"atk={getattr(loaded, 'total_atk', lambda: '?')()}",
        )

        # Second save keeps the first version as save.backup.json.
        player.level = 5
        player.hp = 60
        storage.save_game(player, "s.json")
        with open(os.path.join(tmpdir, "s.json"), "w", encoding="utf-8") as f:
            f.write("{ this is not json")
        recovered = storage.load_game("s.json")
        c.check(
            "a corrupt save falls back to the backup file",
            recovered is not None and recovered.level == 4 and recovered.name == "Tester",
            f"got level={getattr(recovered, 'level', None)}",
        )

        info = storage.save_info("s.json")
        c.check(
            "save_info reports path, existence and backup",
            info["exists"] and info["backup_exists"] and info["path"].startswith(tmpdir),
            f"got {info}",
        )

        settings = {"language": "en", "show_tips": False, "auto_save": False}
        storage.save_settings(settings, "set.json")
        c.check(
            "settings survive a save/load round trip",
            storage.load_settings("set.json") == settings,
            f"got {storage.load_settings('set.json')}",
        )
        c.check(
            "missing settings fall back to defaults",
            storage.load_settings("nope.json")
            == {"language": "zh", "show_tips": True, "auto_save": True},
            "defaults differ",
        )

        broken = {"name": "Broken", "hp": 1}
        c.check(
            "_build_player rejects an incomplete save",
            storage._build_player(broken) is None,
            "incomplete dict accepted",
        )
    finally:
        storage.get_path = original_get_path
        shutil.rmtree(tmpdir, ignore_errors=True)


def check_navigation(c: Checker) -> None:
    """The game state machine must allow valid routes and block invalid ones."""
    c.section("navigation fsm")
    from game_fsm import GameFSM

    gui = FakeGUI()
    fsm = GameFSM(gui)

    c.check(
        "starts in preload without rendering",
        fsm.current_state == "preload" and gui.rendered == [],
        f"state={fsm.current_state} rendered={gui.rendered}",
    )

    state, _ = fsm.goto("load_complete")
    c.check(
        "load_complete enters the main menu and renders it",
        state == "main_menu" and fsm.current_state == "main_menu"
        and gui.rendered[-1:] == ["create_main_menu"],
        f"state={state} rendered={gui.rendered[-1:]}",
    )

    c.check("main_menu advertises new_game", "new_game" in fsm.available_events)
    blocked, reason = fsm.goto("explore")
    c.check(
        "an illegal event is rejected with a reason",
        blocked is None and bool(reason) and not fsm.can_go("explore"),
        f"got {blocked!r} / {reason!r}",
    )

    fsm.goto("open_settings")
    guarded, guard_reason = fsm.goto("back_to_hub")
    c.check(
        "back_to_hub is guarded while no player exists",
        guarded is None and "has_player" in (guard_reason or ""),
        f"got {guarded!r} / {guard_reason!r}",
    )
    fsm.goto("back_to_menu")
    c.check("back_to_menu returns to the main menu", fsm.current_state == "main_menu")

    gui.player = object()  # simulate a created character
    fsm.goto("new_game")
    route_ok = fsm.current_state == "hub"
    for event, expected in [
        ("explore", "explore"),
        ("select_region", "dungeon"),
        ("enter_battle", "combat"),
        ("win", "victory"),
        ("return_hub", "hub"),
    ]:
        fsm.goto(event)
        route_ok = route_ok and fsm.current_state == expected
    c.check(
        "hub -> explore -> dungeon -> combat -> victory -> hub route works",
        route_ok,
        f"ended in {fsm.current_state}",
    )
    c.check(
        "each screen transition rendered its handler",
        "show_combat" in gui.rendered and "show_dungeon_view" in gui.rendered,
        f"rendered={gui.rendered}",
    )

    history = fsm.get_history(limit=5)
    c.check(
        "transition history is recorded with from/to/event",
        len(history) > 0
        and all({"from", "event", "to"} <= set(entry) for entry in history),
        f"history={history[:1]}",
    )


def main() -> int:
    c = Checker()
    try:
        check_models(c)
        check_storage(c)
        check_navigation(c)
    except Exception as exc:  # noqa: BLE001 - report any crash as a failure
        print(f"FAIL unexpected {type(exc).__name__}: {exc}")
        return 1

    if c.failures:
        print(f"FAIL {len(c.failures)} check(s) failed: {c.failures[0]}")
        return 1

    print(
        f"selfcheck ok: {len(c.passed)} checks - player/enemy model maths, "
        "save-load round trip with backup fallback + settings persistence, "
        "navigation FSM routes/guards/history"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
