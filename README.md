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

## Installation

1. Clone or download this repository
2. Ensure the following folder structure:
   ```
   CBMText/
   ├── game.py
   └── dlcs_and_mods/  (optional - for DLC vehicle packs)
   ```

## How to Run

Navigate to the `CBMText` folder and run:
```bash
python game.py
```

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
