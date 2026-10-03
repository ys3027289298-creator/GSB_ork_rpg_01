# Ork RPG

**Version:** 2.0 (Clean Code)
**Genre:** Text RPG / Simulator
**Languages:** English / Russian

## 📖 Description

Welcome to the deep. You play as an **Ork** (or Gopnik) trying to survive in a cruel world. No graphics, only pure text, stats, and basement 90s atmosphere.

*   **Vibe like SharpShooter3D:** Why 3D when the vibe is 100%? Grind, quests, bosses, and full immersion.
*   **Hardcore:** You can die. You can lose money. Stay alert.

## 🎮 Features

*   **Two Languages:** Full support for English and Russian (Selected at the start).
*   **Savings:** Save your progress anywhere (In the Tent).
*   **Quests:** Missions from the bros (Kill rivals, find loot).
*   **Combat:** Turn-based tactical fights.
*   **Upgrading:** Levels, permanent Strength/Endurance training, buying potions.

## 🚀 How to Run

### Requirements
*   Python 3.7 or higher.

### Steps
1. Open terminal/command prompt.
2. Navigate to the game folder:
    ```bash
    cd path/to/ork-rpg
    ```
3. Run the script:
    ```bash
    python ork_main.py
    ```
    *(On Linux/Mac use `python3` instead of `python`)*

## 📂 File Structure

*   `ork_main.py` - Entry point. Handles UI, input, and game loop.
*   `ork_core.py` - Brain. Player stats, combat logic, saves.
*   `ork_data.py` - Database. All text, enemies, and quest definitions.
*   `saves/` - Folder created automatically for save files.

## 🕹️ Controls

*   **Menu:** Numbers (1, 2, 3...) or Letters (Q, E).
*   **Combat:**
    *   `1` - Attack (Kick)
    *   `2` - Block (Dodge chance)
    *   `3` - Drink potion
    *   `4` - Run away (50% chance)

## 💡 Game Tips

1.  **Start easy:** Don't go to the Dungeon immediately. Farm firewood or fish first.
2.  **Grind:** As soon as you have money, go to the Gym to pump stats permanently.
3.  **Quests:** Check Quests (Q) often. They give huge cash.
4.  **Boss:** The Thief in Law is tough. Max out your stats before going for him.

## 🛡️ License

Open source. Feel free to fork, modify, or add more gopniks.

**Good luck, Bro.**

---

## 🛠️ Setup Instructions

### Windows
1. Download all files into one folder.
2. Double-click `run_game.bat`.

### Linux / macOS
1. Open terminal in the game folder.
2. Run: `chmod +x run_game.sh`
3. Run: `./run_game.sh`

## 📦 Project Structure

*   `ork_main.py` - Entry point.
*   `ork_core.py` - Core game logic.
*   `ork_data.py` - Localization and items.
*   `saves/` - Save folder (created automatically).

## 🤝 Contribution

If you find a bug or want to add content, fork the repo and send a Pull Request.