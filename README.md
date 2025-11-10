# City Bus Manager Text Version

City Bus Manager text version is a text-based bus company management simulation game written in Python.  
Manage your bus fleet, create routes, assign buses, and run daily operations to grow your company.

> **Disclaimer:**  
> This is an unofficial, fan-made text version of *City Bus Manager*.  
> It is not affiliated with, endorsed by, or associated with PeDePe GmbH or the official City Bus Manager game.


## Features

- **Fleet Management**: Manage buses with different models, capacities, and fuel efficiency
- **Custom Fleet Numbers**: Assign and edit fleet numbers for better organization
- **Route Creation**: Create routes with multiple stops and custom schedules
- **Bus Assignment**: Assign buses to routes and optimize your operations
- **Day Simulation**: Run daily operations with passengers, fuel consumption, and random events
- **Company Growth**: Buy new buses and expand your route network
- **Save/Load System**: Save your progress and continue anytime
- **DLC & Mod Support**: Extend the game with custom vehicle packs via JSON files

## Requirements

- Python 3.7 or higher

  ---

# 🛠️ Installation & Running the Game

Follow these steps to install and run **City Bus Manager Text** on your computer.

## 1️⃣ Download the Game

You can either:

**Option A: Clone with Git**
```bash
git clone https://github.com/yourusername/CBMText.git
```
*(Replace `yourusername` with your actual GitHub username)*

**Option B: Download ZIP**
- Download the ZIP file directly from the GitHub page
- Extract it to your preferred location

## 2️⃣ Folder Structure

After downloading or cloning, your files should look like this:
```
CBMText/
├── game.py
├── saves/                # Required for save files
└── dlcs_and_mods/        # This is optional for DLC/mod vehicle packs only. The game runs normally without it.
```

## 3️⃣ Install Python

**Requirements:** Python 3.7 or higher

**Check your Python version:**
```bash
python --version
```
or
```bash
python3 --version
```

**Don't have Python?**  
👉 Download it from: [python.org/downloads](https://www.python.org/downloads/)

## 4️⃣ Run the Game

Open your terminal/command prompt, navigate to the game folder, and run:

**🪟 Windows**
```bash
cd path\to\CBMText
python game.py
```

**🍎 macOS**
```bash
cd /path/to/CBMText
python3 game.py
```

**🐧 Linux**
```bash
cd /path/to/CBMText
python3 game.py
```

💬 **Troubleshooting:** If you get a "python not found" error, try using `py` instead of `python`.

## 5️⃣ (Optional) Add DLC Packs

To install DLCs or mods:

1. Download the DLC or Mod from from: [the offical gooogle drive folder](https://drive.google.com/drive/folders/1gSySG89u-Sa8WN7JUTkuF0Upp9qig66G?usp=drive_link)
2. Download the `.json` file (e.g., `electric_buses_pack.json`)
3. Place it in the `dlcs_and_mods/` folder:
```
   CBMText/dlcs_and_mods/
```
3. Restart the game — all DLCs load automatically! ✨

---

## Gameplay

1. **Start a New Company**: Enter your company name or load a saved game
2. **Build Your Fleet**: Purchase buses from the shop (starting budget: £2,500,000)
3. **Create Routes**: Add routes with custom stops and distances
4. **Assign Buses**: Match buses to routes based on capacity needs
5. **Run Operations**: Simulate days to earn money and build reputation
6. **Manage Fleet Numbers**: Organize your fleet with custom numbering
7. **Save Progress**: Save your game anytime to continue later

## Creating DLC Vehicle Packs

Expand your game with custom vehicle packs! Create JSON files in the `dlcs_and_mods/` folder:

### Example DLC Structure
```json
{
  "dlc_name": "Vintage Pack",
  "vehicles": [
    {
      "model": "Routemaster RM",
      "capacity": 64,
      "fuel_capacity": 140.0,
      "fuel_efficiency": 0.45,
      "price": 85000
    },
    {
      "model": "AEC Regent III RT",
      "capacity": 56,
      "fuel_capacity": 130.0,
      "fuel_efficiency": 0.50,
      "price": 75000
    }
  ]
}
```

### DLC Field Reference
- **dlc_name**: Name of your DLC pack (appears in-game)
- **model**: Bus model name
- **capacity**: Passenger capacity
- **fuel_capacity**: Fuel tank size in litres
- **fuel_efficiency**: Litres per km at 50 km/h (lower is better)
- **price**: Purchase price in pounds

Place your JSON files in `CBMText/dlcs_and_mods/` and they'll automatically load when you start the game!

## 📦 Official & Community DLCs

You can download additional DLC packs here:
https://drive.google.com/drive/folders/1gSySG89u-Sa8WN7JUTkuF0Upp9qig66G?usp=drive_link

Place any downloaded .json files into your CBMText/dlcs_and_mods/ folder — they’ll load automatically on startup.

## Game Menu Options

1. View Routes
2. View Fleet
3. Assign Bus to Route
4. Change Route Schedule
5. Run Day Simulation
6. Buy New Bus
7. Add New Route (Costs £500 per stop)
8. Delete Route
9. View Company Status
10. Save Game
11. Load Game
12. Quit

## Tips

- Tighter schedules can increase reputation but risk delays
- Monitor fuel levels and efficiency when choosing buses
- Balance capacity with route demand for optimal profits
- Use fleet numbers to organize your buses by depot or route type
- Random events can occur during daily operations affecting finances and reputation

## Version History

**v1.1** - DLC Support & Fleet Numbers
- Added DLC/mod support for custom vehicle packs
- Implemented fleet number management system
- Improved fleet organization and visualization

**v1.0** - Initial Release
- Core bus management gameplay
- Route creation and management
- Basic economic simulation

## License

MIT License — see the LICENSE file for details.

## Contributing

Contributions are welcome! Feel free to:
- Submit bug reports
- Suggest new features
- Create and share DLC packs
- Improve documentation

## Contact

Created by **shay-coding**. Feel free to open issues or contribute!

---

Happy bus managing! 🚌
