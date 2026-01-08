import random
import sys
import json
import os
import glob
import csv
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# Import running board functionality
from running_boards import (
    RunningBoard, Trip,
    create_running_board_interactive,
    view_running_boards,
    list_running_boards,
    load_running_board,
    save_running_board
)

@dataclass
class Stop:
    name: str
    minutes_from_prev: int  # Changed from distance_from_prev_km

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        # Support both old and new format for backwards compatibility
        if "minutes_from_prev" in data:
            return Stop(name=data["name"], minutes_from_prev=data["minutes_from_prev"])
        else:
            # Convert old km data to minutes (assuming avg speed of 30 km/h)
            minutes = int(data.get("distance_from_prev_km", 0) * 2)
            return Stop(name=data["name"], minutes_from_prev=minutes)

@dataclass
class Route:
    name: str
    stops: List[Stop]
    base_schedule_minutes: int
    current_schedule_minutes: int
    assigned_bus_id: Optional[int] = None

    def to_dict(self):
        return {
            "name": self.name,
            "stops": [stop.to_dict() for stop in self.stops],
            "base_schedule_minutes": self.base_schedule_minutes,
            "current_schedule_minutes": self.current_schedule_minutes,
            "assigned_bus_id": self.assigned_bus_id,
        }

    @staticmethod
    def from_dict(data):
        stops = [Stop.from_dict(s) for s in data["stops"]]
        return Route(
            name=data["name"],
            stops=stops,
            base_schedule_minutes=data["base_schedule_minutes"],
            current_schedule_minutes=data["current_schedule_minutes"],
            assigned_bus_id=data.get("assigned_bus_id"),
        )

@dataclass
class Bus:
    bus_id: int
    model: str
    capacity: int
    fuel_capacity: float
    fuel_level: float
    fuel_efficiency: float  # litres/km at 50 km/h
    assigned_route: Optional[str] = None
    health: int = 100
    purchase_price: float = 0.0
    fleet_number: Optional[str] = None
    dlc_source: Optional[str] = None  # Track which DLC this bus came from
    livery: str = "Standard"  # New: Bus livery/color scheme

    def consume_fuel(self, minutes, speed=30):
        # Convert minutes to distance assuming average speed
        distance = (minutes / 60) * speed
        speed_factor = speed / 50
        used = distance * self.fuel_efficiency * speed_factor
        self.fuel_level = max(self.fuel_level - used, 0)
        return used

    def to_dict(self):
        data = asdict(self)
        return data

    @staticmethod
    def from_dict(data):
        return Bus(
            bus_id=data["bus_id"],
            model=data["model"],
            capacity=data["capacity"],
            fuel_capacity=data["fuel_capacity"],
            fuel_level=data["fuel_level"],
            fuel_efficiency=data["fuel_efficiency"],
            assigned_route=data.get("assigned_route"),
            health=data.get("health", 100),
            purchase_price=data.get("purchase_price", 0.0),
            fleet_number=data.get("fleet_number"),
            dlc_source=data.get("dlc_source"),
            livery=data.get("livery", "Standard"),
        )

@dataclass
class ManagerState:
    company_name: str
    routes: List[Route] = field(default_factory=list)
    fleet: List[Bus] = field(default_factory=list)
    money: float = 2500000.0
    reputation: float = 50.0
    day: int = 1
    next_bus_id: int = 1
    use_running_boards: bool = False  # Toggle between static and dynamic assignment
    fuel_price: float = 1.60  # Dynamic fuel price per litre (min 1.25, max 2.00)

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "routes": [route.to_dict() for route in self.routes],
            "fleet": [bus.to_dict() for bus in self.fleet],
            "money": self.money,
            "reputation": self.reputation,
            "day": self.day,
            "next_bus_id": self.next_bus_id,
            "use_running_boards": self.use_running_boards,
            "fuel_price": self.fuel_price,
        }

    @staticmethod
    def from_dict(data):
        routes = [Route.from_dict(r) for r in data["routes"]]
        fleet = [Bus.from_dict(b) for b in data["fleet"]]
        return ManagerState(
            company_name=data["company_name"],
            routes=routes,
            fleet=fleet,
            money=data["money"],
            reputation=data["reputation"],
            day=data["day"],
            next_bus_id=data.get("next_bus_id", 1),
            use_running_boards=data.get("use_running_boards", False),
            fuel_price=data.get("fuel_price", 1.60),
        )


# Available liveries for buses
AVAILABLE_LIVERIES = [
    "Red & White",
    "Blue & Yellow",
    "Green & Cream",
    "Silver & Black",
    "Orange & White",
    "Purple & Gold",
    "All-over White",
    "All-over Red",
    "All-over Blue",
    "All-over Green",
    "Corporate Fleet",
    "Heritage Classic",
    "Modern Metro",
    "Express Service",
    "Night Service",
    "Airport Special",
    "City Centre",
    "Suburban Route",
    "Premium Service",
    "Eco-Friendly Green",
]


def load_dlc_vehicles():
    """Load all vehicle DLC files from the dlcs_and_mods/ directory"""
    dlc_vehicles = []

    # Get the script's directory (CBMText folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dlc_folder = os.path.join(script_dir, "dlcs_and_mods")

    if not os.path.exists(dlc_folder):
        print(f"Note: dlcs_and_mods folder not found at {dlc_folder}")
        return dlc_vehicles

    # Find all JSON files in the dlcs_and_mods folder
    dlc_files = glob.glob(os.path.join(dlc_folder, "*.json"))

    for dlc_file in dlc_files:
        try:
            with open(dlc_file, 'r') as f:
                data = json.load(f)

            # Validate DLC format
            if "dlc_name" not in data or "vehicles" not in data:
                print(f"Warning: {dlc_file} missing required fields (dlc_name, vehicles). Skipping.")
                continue

            dlc_name = data["dlc_name"]
            vehicles = data["vehicles"]

            # Validate each vehicle
            for vehicle in vehicles:
                required_fields = ["model", "capacity", "fuel_capacity", "fuel_efficiency", "price"]
                if all(field in vehicle for field in required_fields):
                    # Add DLC source to each vehicle
                    vehicle["dlc_source"] = dlc_name
                    dlc_vehicles.append(vehicle)
                else:
                    print(f"Warning: Vehicle in {dlc_file} missing required fields. Skipping.")

            print(f"Loaded DLC: {dlc_name} ({len(vehicles)} vehicles)")

        except json.JSONDecodeError:
            print(f"Warning: {dlc_file} is not valid JSON. Skipping.")
        except Exception as e:
            print(f"Warning: Error loading {dlc_file}: {e}. Skipping.")

    return dlc_vehicles


def save_game(state: ManagerState):
    # Create saves folder if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    saves_folder = os.path.join(script_dir, "saves")

    if not os.path.exists(saves_folder):
        os.makedirs(saves_folder)
        print(f"Created saves folder at {saves_folder}")

    filename = input("Enter filename to save to (e.g. my_company_save.json): ").strip()
    if not filename:
        print("Invalid filename. Save cancelled.")
        return

    # Add .json extension if not present
    if not filename.endswith('.json'):
        filename += '.json'

    filepath = os.path.join(saves_folder, filename)

    try:
        with open(filepath, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        print(f"Game saved successfully to 'saves/{filename}'.")
    except Exception as e:
        print(f"Error saving game: {e}")

def load_game() -> Optional[ManagerState]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    saves_folder = os.path.join(script_dir, "saves")

    if not os.path.exists(saves_folder):
        print("No saves folder found. No saved games available.")
        return None

    # List available save files
    save_files = [f for f in os.listdir(saves_folder) if f.endswith('.json')]

    if not save_files:
        print("No saved games found in saves folder.")
        return None

    print("\n--- Available Saved Games ---")
    for i, save_file in enumerate(sorted(save_files), 1):
        # Try to read company name from save
        try:
            filepath = os.path.join(saves_folder, save_file)
            with open(filepath, "r") as f:
                data = json.load(f)
            company = data.get("company_name", "Unknown")
            day = data.get("day", "?")
            money = data.get("money", 0)
            print(f"[{i}] {save_file} - {company} (Day {day}, £{money:,.2f})")
        except:
            print(f"[{i}] {save_file}")

    print("\nEnter save number to load, or type filename directly (or 0 to cancel):")
    choice = input("> ").strip()

    if choice == "0":
        print("Load cancelled.")
        return None

    # Check if it's a number (selecting from list)
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(save_files):
            filename = sorted(save_files)[choice_num - 1]
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        # It's a filename
        filename = choice
        if not filename.endswith('.json'):
            filename += '.json'
        if filename not in save_files:
            print(f"Save file '{filename}' not found.")
            return None

    filepath = os.path.join(saves_folder, filename)

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        state = ManagerState.from_dict(data)
        print(f"Game loaded successfully from 'saves/{filename}'.")
        return state
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error loading game: {e}")
    return None


def update_fuel_price(state: ManagerState):
    """Update fuel price dynamically with random fluctuations"""
    # Random fluctuation between -0.05 and +0.05
    fluctuation = random.uniform(-0.05, 0.05)
    new_price = state.fuel_price + fluctuation
    
    # Clamp price between min (1.25) and max (2.00)
    state.fuel_price = max(1.25, min(2.00, new_price))


def view_fuel_price(state: ManagerState):
    """Display current fuel price and price history"""
    print(f"\n--- Current Fuel Price ---")
    print(f"Price per litre: £{state.fuel_price:.2f}")
    
    # Show color indication
    if state.fuel_price <= 1.40:
        status = "🟢 LOW (Good buying opportunity!)"
    elif state.fuel_price <= 1.70:
        status = "🟡 MEDIUM (Average)"
    else:
        status = "🔴 HIGH (Consider waiting)"
    print(f"Status: {status}")


def print_main_menu(state: ManagerState):
    mode = "Running Boards" if state.use_running_boards else "Static Routes"
    print(f"\n===== City Bus Manager – {state.company_name} [Mode: {mode}] =====")
    print(f"Fuel Price: £{state.fuel_price:.2f}/L")
    print("1) View Routes")
    print("2) View Fleet")
    print("3) Assign Bus to Route")
    print("4) Change Route Schedule")
    print("5) Run Day Simulation")
    print("6) Buy New Bus")
    print("7) Add New Route (Costs £500 per stop)")
    print("8) Delete Route")
    print("9) View Company Status")
    print("10) View Fuel Price Details")
    print("11) Save Game")
    print("12) Load Game")
    print("13) Running Board Management")
    print("14) Toggle Assignment Mode")
    print("15) Quit")

def view_routes(state: ManagerState):
    if not state.routes:
        print("\nNo routes available yet.")
        return
    print("\n--- Routes ---")
    for i, route in enumerate(state.routes, 1):
        assigned_bus = next((b.model for b in state.fleet if b.bus_id == route.assigned_bus_id), "None")
        total_time = sum(stop.minutes_from_prev for stop in route.stops[1:])
        print(f"[{i}] {route.name} | Journey Time: {total_time} mins | Schedule: {route.current_schedule_minutes} mins | Bus: {assigned_bus}")

def view_fleet(state: ManagerState):
    if not state.fleet:
        print("\nNo buses in fleet yet.")
        return
    while True:
        print("\n--- Fleet ---")
        for bus in state.fleet:
            route_name = next((r.name for r in state.routes if r.assigned_bus_id == bus.bus_id), "None")
            fn = bus.fleet_number if bus.fleet_number else "N/A"
            dlc_tag = f" [{bus.dlc_source}]" if bus.dlc_source else ""

            # Check running board assignments
            rb_assignments = []
            if state.use_running_boards:
                for board_name in list_running_boards():
                    board = load_running_board(board_name)
                    if board and board.assigned_bus_id == bus.bus_id:
                        rb_assignments.append(board.name)

            assignment_info = f"Route: {route_name}"
            if rb_assignments:
                assignment_info = f"Running Boards: {', '.join(rb_assignments)}"

            print(f"[{bus.bus_id}] {bus.model}{dlc_tag} (Fleet No: {fn}) | Livery: {bus.livery} | Capacity: {bus.capacity} | Fuel: {bus.fuel_level:.1f}L | Health: {bus.health} | {assignment_info}")

        print("\nOptions: [E] Edit Fleet Number, [L] Change Livery, [Q] Return to Main Menu")
        choice = input("> ").strip().lower()
        if choice == 'e':
            edit_fleet_number(state)
        elif choice == 'l':
            change_bus_livery(state)
        elif choice == 'q':
            break
        else:
            print("Invalid option, try again.")

def edit_fleet_number(state: ManagerState):
    if not state.fleet:
        print("\nNo buses in fleet to edit.")
        return

    print("\n--- Edit Fleet Number ---")
    print("Current fleet:")
    for bus in state.fleet:
        fn = bus.fleet_number if bus.fleet_number else "N/A"
        print(f"[{bus.bus_id}] {bus.model} (Fleet No: {fn})")

    print("Enter bus ID to edit fleet number (or 0 to cancel):")
    try:
        bus_id = int(input("> "))
    except ValueError:
        print("Invalid input.")
        return

    if bus_id == 0:
        print("Edit cancelled.")
        return

    bus = next((b for b in state.fleet if b.bus_id == bus_id), None)
    if not bus:
        print("Bus ID not found.")
        return

    print(f"Current fleet number: {bus.fleet_number if bus.fleet_number else 'N/A'}")
    print("Enter new fleet number (or leave blank to cancel):")
    new_number = input("> ").strip()
    if new_number == "":
        print("Edit cancelled.")
        return

    if any(b.fleet_number == new_number and b.bus_id != bus.bus_id for b in state.fleet):
        print(f"Fleet number '{new_number}' already in use by another bus. Edit cancelled.")
        return

    bus.fleet_number = new_number
    print(f"Fleet number updated to '{new_number}' for bus ID {bus.bus_id}.")

def change_bus_livery(state: ManagerState):
    """Allow player to change the livery of a bus"""
    if not state.fleet:
        print("\nNo buses in fleet to edit.")
        return

    print("\n--- Change Bus Livery ---")
    print("Current fleet:")
    for bus in state.fleet:
        fn = bus.fleet_number if bus.fleet_number else "N/A"
        print(f"[{bus.bus_id}] {bus.model} (Fleet No: {fn}) - Current Livery: {bus.livery}")

    print("\nEnter bus ID to change livery (or 0 to cancel):")
    try:
        bus_id = int(input("> "))
    except ValueError:
        print("Invalid input.")
        return

    if bus_id == 0:
        print("Livery change cancelled.")
        return

    bus = next((b for b in state.fleet if b.bus_id == bus_id), None)
    if not bus:
        print("Bus ID not found.")
        return

    print(f"\n--- Available Liveries for {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'}) ---")
    print(f"Current livery: {bus.livery}")
    print("\nChoose a new livery:")
    
    for i, livery in enumerate(AVAILABLE_LIVERIES, 1):
        current_marker = " (CURRENT)" if livery == bus.livery else ""
        print(f"[{i}] {livery}{current_marker}")

    print("\nEnter livery number (or 0 to cancel):")
    try:
        livery_choice = int(input("> "))
    except ValueError:
        print("Invalid input.")
        return

    if livery_choice == 0:
        print("Livery change cancelled.")
        return

    if not (1 <= livery_choice <= len(AVAILABLE_LIVERIES)):
        print("Invalid livery number.")
        return

    new_livery = AVAILABLE_LIVERIES[livery_choice - 1]
    
    if new_livery == bus.livery:
        print(f"Bus already has the '{new_livery}' livery.")
        return

    # Cost to change livery
    livery_cost = 500.0
    print(f"\nChanging livery to '{new_livery}' will cost £{livery_cost:.2f}")
    print(f"Current balance: £{state.money:.2f}")
    
    confirm = input("Proceed with livery change? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Livery change cancelled.")
        return

    if state.money < livery_cost:
        print("You don't have enough money to change the livery!")
        return

    old_livery = bus.livery
    bus.livery = new_livery
    state.money -= livery_cost
    
    print(f"\n✓ Livery successfully changed!")
    print(f"  Bus: {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'})")
    print(f"  Old livery: {old_livery}")
    print(f"  New livery: {new_livery}")
    print(f"  Cost: £{livery_cost:.2f}")
    print(f"  Remaining balance: £{state.money:.2f}")

def assign_bus_to_route(state: ManagerState):
    if state.use_running_boards:
        print("\nYou are in Running Board mode. Use Running Board Management (option 12) to assign buses.")
        return

    if not state.fleet:
        print("\nNo buses available. Buy some first.")
        return
    if not state.routes:
        print("\nNo routes available. Add some first.")
        return

    print("\nSelect Bus to assign:")
    for bus in state.fleet:
        fn = bus.fleet_number if bus.fleet_number else "N/A"
        print(f"[{bus.bus_id}] {bus.model} (Fleet No: {fn}, Capacity: {bus.capacity})")

    try:
        bus_id = int(input("> "))
    except ValueError:
        print("Invalid input.")
        return

    bus = next((b for b in state.fleet if b.bus_id == bus_id), None)
    if not bus:
        print("Bus not found.")
        return

    print("\nSelect Route:")
    for i, route in enumerate(state.routes, 1):
        print(f"[{i}] {route.name}")

    try:
        route_idx = int(input("> ")) - 1
    except ValueError:
        print("Invalid input.")
        return

    if not (0 <= route_idx < len(state.routes)):
        print("Invalid route number.")
        return

    route = state.routes[route_idx]

    for r in state.routes:
        if r.assigned_bus_id == bus.bus_id:
            r.assigned_bus_id = None

    route.assigned_bus_id = bus.bus_id
    bus.assigned_route = route.name
    print(f"Assigned {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'}) to {route.name}")

def change_route_schedule(state: ManagerState):
    if not state.routes:
        print("\nNo routes available to edit.")
        return
    print("\nSelect Route to edit schedule:")
    for i, route in enumerate(state.routes, 1):
        print(f"[{i}] {route.name} | Current Schedule: {route.current_schedule_minutes} mins")

    try:
        route_idx = int(input("> ")) - 1
    except ValueError:
        print("Invalid input.")
        return

    if not (0 <= route_idx < len(state.routes)):
        print("Invalid route number.")
        return

    route = state.routes[route_idx]
    print(f"Enter new schedule time in minutes for {route.name} (base is {route.base_schedule_minutes}):")

    try:
        new_time = int(input("> "))
        if new_time < route.base_schedule_minutes // 2:
            print("Schedule too short! Aborting.")
            return
    except ValueError:
        print("Invalid input.")
        return

    route.current_schedule_minutes = new_time
    print(f"Schedule updated: {route.name} now runs in {new_time} minutes.")

def run_day_simulation_static(state: ManagerState):
    """Original static route simulation"""
    if not state.routes:
        print("\nNo routes available to run.")
        return
    if not state.fleet:
        print("\nNo buses available to run routes.")
        return

    print(f"\n--- Running Day Simulation (Static Mode): Day {state.day} ---")
    total_earnings = 0.0
    total_fuel_cost = 0.0
    reputation_change = 0.0

    for route in state.routes:
        bus = next((b for b in state.fleet if b.bus_id == route.assigned_bus_id), None)
        if not bus:
            print(f"Route '{route.name}' has no bus assigned! No service today.")
            reputation_change -= 5
            continue

        print(f"\nRoute: {route.name}")
        print(f"Bus: {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'}) [Livery: {bus.livery}] (Capacity: {bus.capacity})")
        print(f"Schedule time: {route.current_schedule_minutes} mins")

        total_time = sum(stop.minutes_from_prev for stop in route.stops[1:])
        ticket_price = 2.50

        # Base demand on route length (more stops/time = more passengers)
        avg_demand = int(total_time * 1.5)
        passengers = min(bus.capacity, random.randint(max(0, avg_demand - 5), avg_demand + 5))
        earnings = passengers * ticket_price

        fuel_used = bus.consume_fuel(total_time)
        fuel_cost = fuel_used * state.fuel_price

        if random.random() < 0.2:
            event = random.choice(["flat tyre", "engine trouble", "heavy traffic"])
            print(f"** Event: {event}! Delays the route and costs £200 to fix. **")
            reputation_change -= 3
            state.money -= 200
        else:
            reputation_change += 1

        if route.current_schedule_minutes < route.base_schedule_minutes:
            if random.random() < 0.3:
                print("Tight schedule caused delays and made passengers unhappy!")
                reputation_change -= 2
            else:
                reputation_change += 1
        else:
            reputation_change += 1

        total_earnings += earnings
        total_fuel_cost += fuel_cost

        print(f"Passengers carried: {passengers}")
        print(f"Fare income: £{earnings:.2f}")
        print(f"Fuel used: {fuel_used:.2f}L costing £{fuel_cost:.2f}")

    net_profit = total_earnings - total_fuel_cost
    state.money += net_profit
    state.reputation = max(0.0, min(100.0, state.reputation + reputation_change))
    
    # Update fuel price for next day
    update_fuel_price(state)
    
    state.day += 1

    print(f"\nDay {state.day-1} summary:")
    print(f"Total fare income: £{total_earnings:.2f}")
    print(f"Total fuel cost: £{total_fuel_cost:.2f}")
    print(f"Net profit: £{net_profit:.2f}")
    print(f"Reputation change: {reputation_change:+.1f}")
    print(f"New reputation: {state.reputation:.1f}/100")
    print(f"Fuel price for Day {state.day}: £{state.fuel_price:.2f}/L")
    print(f"Money available: £{state.money:.2f}")

def run_day_simulation_running_boards(state: ManagerState):
    """New dynamic simulation using running boards"""
    boards = []
    for board_name in list_running_boards():
        board = load_running_board(board_name)
        if board and board.assigned_bus_id:
            boards.append(board)

    if not boards:
        print("\nNo running boards with assigned buses available.")
        print("Use Running Board Management (option 12) to create and assign running boards.")
        return

    print(f"\n--- Running Day Simulation (Running Board Mode): Day {state.day} ---")
    print(f"Operating {len(boards)} running board(s)...\n")

    total_earnings = 0.0
    total_fuel_cost = 0.0
    reputation_change = 0.0

    for board in boards:
        bus = next((b for b in state.fleet if b.bus_id == board.assigned_bus_id), None)
        if not bus:
            print(f"Running board '{board.name}' has invalid bus assignment! Skipping.")
            continue

        print(f"\n--- Running Board: {board.name} ---")
        print(f"Bus: {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'}) [Livery: {bus.livery}]")
        print(f"Total trips: {len(board.trips)}")

        board_earnings = 0.0
        board_fuel = 0.0
        trips_completed = 0

        for trip in board.trips:
            route = next((r for r in state.routes if r.name == trip.route_name), None)
            if not route:
                print(f"  {trip.departure_time} - {trip.route_name}: Route not found! Skipping.")
                reputation_change -= 2
                continue

            total_time = sum(stop.minutes_from_prev for stop in route.stops[1:])

            # Check if bus has enough fuel
            fuel_needed = total_time / 60 * 30 * bus.fuel_efficiency  # Estimate based on time
            if bus.fuel_level < fuel_needed:
                print(f"  {trip.departure_time} - {trip.route_name}: ⚠ Insufficient fuel! Trip cancelled.")
                reputation_change -= 5
                continue

            ticket_price = 2.50
            avg_demand = int(total_time * 1.5)
            passengers = min(bus.capacity, random.randint(max(0, avg_demand - 5), avg_demand + 5))
            earnings = passengers * ticket_price

            fuel_used = bus.consume_fuel(total_time)
            fuel_cost = fuel_used * state.fuel_price

            # Random events
            if random.random() < 0.10:
                event = random.choice(["minor delay", "passenger incident", "route deviation"])
                reputation_change -= 1
            else:
                reputation_change += 0.5

            board_earnings += earnings
            board_fuel += fuel_cost
            trips_completed += 1

            print(f"  {trip.departure_time} - {trip.route_name} to {trip.destination}: {passengers} pax, £{earnings:.2f}")

        total_earnings += board_earnings
        total_fuel_cost += board_fuel

        print(f"  Board summary: {trips_completed}/{len(board.trips)} trips, £{board_earnings:.2f} income, £{board_fuel:.2f} fuel")

    net_profit = total_earnings - total_fuel_cost
    state.money += net_profit
    state.reputation = max(0.0, min(100.0, state.reputation + reputation_change))
    
    # Update fuel price for next day
    update_fuel_price(state)
    
    state.day += 1

    print(f"\n--- Day {state.day-1} Summary ---")
    print(f"Total fare income: £{total_earnings:.2f}")
    print(f"Total fuel cost: £{total_fuel_cost:.2f}")
    print(f"Net profit: £{net_profit:.2f}")
    print(f"Reputation change: {reputation_change:+.1f}")
    print(f"New reputation: {state.reputation:.1f}/100")
    print(f"Fuel price for Day {state.day}: £{state.fuel_price:.2f}/L")
    print(f"Money available: £{state.money:.2f}")

def run_day_simulation(state: ManagerState):
    """Route to appropriate simulation based on mode"""
    if state.use_running_boards:
        run_day_simulation_running_boards(state)
    else:
        run_day_simulation_static(state)

def buy_new_bus(state: ManagerState):
    # Base game vehicles
    shop = [
        ("ADL Enviro200 [Base Game]", 40, 160.0, 0.26, 90000, None),
        ("ADL Enviro200 MMC [Base Game]", 40, 160.0, 0.25, 95000, None),
        ("ADL Enviro400 [Base Game]", 80, 240.0, 0.38, 135000, None),
        ("ADL Enviro400 MMC [Base Game]", 80, 240.0, 0.38, 140000, None),
        ("ADL Enviro400 City [Base Game]", 80, 240.0, 0.37, 145000, None),
        ("Wright Streetlite DF [Base Game]", 40, 150.0, 0.25, 72000, None),
        ("Wright Streetlite WF [Base Game]", 40, 150.0, 0.24, 73000, None),
        ("Wright Streetdeck Ultroliner [Base Game]", 75, 220.0, 0.35, 130000, None),
        ("Wright Eclipse Urban [Base Game]", 40, 150.0, 0.26, 70000, None),
        ("Wright Eclipse Urban 2 [Base Game]", 40, 150.0, 0.25, 72000, None),
        ("Wright Eclipse Gemini [Base Game]", 80, 230.0, 0.37, 130000, None),
        ("Wright Eclipse Gemini 2 [Base Game]", 80, 230.0, 0.36, 132000, None),
        ("Wright Eclipse Gemini 3 [Base Game]", 80, 230.0, 0.35, 135000, None),
        ("Scania N94UD Omnidekka [Base Game]", 80, 240.0, 0.40, 138000, None),
        ("Scania N270UD Omnicity [Base Game]", 80, 230.0, 0.38, 140000, None),
        ("Scania N230UD Enviro400 [Base Game]", 80, 240.0, 0.37, 137000, None),
        ("Scania N250UD Enviro400 MMC [Base Game]", 80, 240.0, 0.36, 142000, None),
        ("Scania L94UB Wright Solar [Base Game]", 40, 150.0, 0.26, 72000, None),
        ("Optare Solo [Base Game]", 30, 120.0, 0.22, 60000, None),
        ("Optare Solo SR [Base Game]", 30, 120.0, 0.22, 62000, None),
        ("Dennis Trident Optare Olympus [Base Game]", 75, 230.0, 0.38, 125000, None),
        ("Volvo B7TL Plaxton President [Base Game]", 80, 230.0, 0.39, 130000, None),
        ("Dennis Dart MPD [Base Game]", 35, 140.0, 0.24, 65000, None),
    ]

    # Load DLC vehicles
    dlc_vehicles = load_dlc_vehicles()
    for dlc_vehicle in dlc_vehicles:
        shop.append((
            dlc_vehicle["model"],
            dlc_vehicle["capacity"],
            dlc_vehicle["fuel_capacity"],
            dlc_vehicle["fuel_efficiency"],
            dlc_vehicle["price"],
            dlc_vehicle["dlc_source"]
        ))

    print("\n--- Bus Shop ---")
    for i, item in enumerate(shop, 1):
        model, capacity, fuel_cap, efficiency, price, dlc_source = item
        dlc_tag = f" [{dlc_source}]" if dlc_source else ""
        print(f"[{i}] {model}{dlc_tag} | Capacity: {capacity} | Price: £{price:,}")

    print(f"Current money: £{state.money:.2f}")
    print("Select bus to buy or 0 to cancel:")

    try:
        choice = int(input("> "))
    except ValueError:
        print("Invalid input.")
        return

    if choice == 0:
        print("Cancelled purchase.")
        return

    if not (1 <= choice <= len(shop)):
        print("Invalid choice.")
        return

    model, capacity, fuel_cap, efficiency, price, dlc_source = shop[choice - 1]

    if state.money < price:
        print("You can't afford that bus yet!")
        return

    print("Enter fleet number (or leave blank for auto-assignment):")
    entered_number = input("> ").strip()

    existing_numbers = {bus.fleet_number for bus in state.fleet if bus.fleet_number}
    if entered_number == "":
        n = 1
        while str(n) in existing_numbers:
            n += 1
        fleet_number = str(n)
    else:
        fleet_number = entered_number
        if fleet_number in existing_numbers:
            print(f"Fleet number {fleet_number} already in use. Purchase cancelled.")
            return

    bus_id = state.next_bus_id
    state.next_bus_id += 1
    new_bus = Bus(bus_id, model, capacity, fuel_cap, fuel_cap, efficiency,
                   purchase_price=price, fleet_number=fleet_number, dlc_source=dlc_source)
    state.fleet.append(new_bus)
    state.money -= price
    dlc_msg = f" from {dlc_source}" if dlc_source else ""
    print(f"Congratulations! You bought a new {model}{dlc_msg} with fleet number {fleet_number} for £{price:,}.")
    print(f"Default livery: {new_bus.livery}")

def add_route(state: ManagerState):
    print("\n--- Add New Route ---")
    name = input("Enter route name: ").strip()
    if not name:
        print("Route name cannot be empty.")
        return

    print("Enter stops for the route. Type 'done' when finished.")
    stops = []
    while True:
        stop_name = input("Stop name (or 'done'): ").strip()
        if stop_name.lower() == "done":
            break
        if not stop_name:
            print("Stop name cannot be empty.")
            continue
        while True:
            try:
                minutes = int(input(f"Travel time from previous stop to {stop_name} in minutes: "))
                if minutes < 0:
                    print("Time cannot be negative.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")

        stops.append(Stop(stop_name, minutes))

    if len(stops) < 2:
        print("A route must have at least two stops.")
        return

    cost = 500 * len(stops)
    print(f"Creating this route will cost £{cost}. Confirm? (y/n)")
    confirm = input("> ").strip().lower()
    if confirm != 'y':
        print("Route creation cancelled.")
        return

    if state.money < cost:
        print("You don't have enough money to create this route.")
        return

    total_time = sum(stop.minutes_from_prev for stop in stops[1:])
    # Add buffer time for base schedule (20% extra for layover/turnaround)
    base_schedule = int(total_time * 1.2)

    new_route = Route(name, stops, base_schedule, base_schedule)
    state.routes.append(new_route)
    state.money -= cost
    print(f"Route '{name}' created with {len(stops)} stops, total journey time {total_time} mins, costing £{cost}.")

def delete_route(state: ManagerState):
    if not state.routes:
        print("\nNo routes to delete.")
        return
    print("\nSelect route to delete:")
    for i, route in enumerate(state.routes, 1):
        assigned = "(Assigned to bus)" if route.assigned_bus_id else ""
        print(f"[{i}] {route.name} {assigned}")

    try:
        idx = int(input("> ")) - 1
    except ValueError:
        print("Invalid input.")
        return

    if not (0 <= idx < len(state.routes)):
        print("Invalid route number.")
        return

    route = state.routes[idx]
    if route.assigned_bus_id is not None:
        print("Cannot delete a route that has a bus assigned. Unassign the bus first.")
        return

    confirm = input(f"Are you sure you want to delete route '{route.name}'? (y/n): ").strip().lower()
    if confirm == 'y':
        del state.routes[idx]
        print(f"Route '{route.name}' deleted.")
    else:
        print("Deletion cancelled.")

def view_company_status(state: ManagerState):
    print(f"\n--- {state.company_name} Status ---")
    print(f"Day: {state.day}")
    print(f"Money: £{state.money:.2f}")
    print(f"Reputation: {state.reputation:.1f}/100")
    print(f"Fleet size: {len(state.fleet)} buses")
    print(f"Routes managed: {len(state.routes)}")

    mode = "Running Boards (Dynamic)" if state.use_running_boards else "Static Routes"
    print(f"Assignment mode: {mode}")

    if state.use_running_boards:
        boards_count = len(list_running_boards())
        print(f"Running boards available: {boards_count}")

def running_board_menu(state: ManagerState):
    """Running board management submenu"""
    while True:
        print("\n--- Running Board Management ---")
        print("1) Create New Running Board")
        print("2) View Running Boards")
        print("3) Assign Bus to Running Board")
        print("4) View Running Board Details")
        print("5) Delete Running Board")
        print("6) Return to Main Menu")

        choice = input("> ").strip()

        if choice == "1":
            create_running_board_interactive(state)
        elif choice == "2":
            view_running_boards(state)
        elif choice == "3":
            from running_boards import assign_bus_to_running_board
            assign_bus_to_running_board(state)
        elif choice == "4":
            from running_boards import view_running_board_details
            view_running_board_details(state)
        elif choice == "5":
            from running_boards import delete_running_board_interactive
            delete_running_board_interactive(state)
        elif choice == "6":
            break
        else:
            print("Invalid option, try again.")

def toggle_assignment_mode(state: ManagerState):
    """Toggle between static route and running board mode"""
    current = "Running Boards" if state.use_running_boards else "Static Routes"
    new_mode = "Static Routes" if state.use_running_boards else "Running Boards"

    print(f"\n--- Toggle Assignment Mode ---")
    print(f"Current mode: {current}")
    print(f"Switch to: {new_mode}")
    print("\nNote: Switching modes will not affect existing assignments,")
    print("but you'll need to use the appropriate management system for each mode.")

    confirm = input(f"\nSwitch to {new_mode} mode? (y/n): ").strip().lower()
    if confirm == 'y':
        state.use_running_boards = not state.use_running_boards
        print(f"Switched to {new_mode} mode.")
    else:
        print("Mode change cancelled.")

def main():
    print("Welcome to City Bus Manager!")
    company_name = input("Please enter your company name (or leave blank to load a game): ").strip()
    if company_name:
        state = ManagerState(company_name=company_name)
        print(f"\nWelcome, {state.company_name}! You start with £{state.money:,.2f}.")
        print("Build your fleet and routes from scratch and become a transport legend!\n")
    else:
        loaded_state = load_game()
        if loaded_state:
            state = loaded_state
        else:
            print("Starting new company as no valid save loaded.")
            state = ManagerState(company_name="My Bus Company")

    while True:
        print_main_menu(state)
        choice = input("> ").strip()
        if choice == "1":
            view_routes(state)
        elif choice == "2":
            view_fleet(state)
        elif choice == "3":
            assign_bus_to_route(state)
        elif choice == "4":
            change_route_schedule(state)
        elif choice == "5":
            run_day_simulation(state)
        elif choice == "6":
            buy_new_bus(state)
        elif choice == "7":
            add_route(state)
        elif choice == "8":
            delete_route(state)
        elif choice == "9":
            view_company_status(state)
        elif choice == "10":
            view_fuel_price(state)
        elif choice == "11":
            save_game(state)
        elif choice == "12":
            loaded = load_game()
            if loaded:
                state = loaded
        elif choice == "13":
            running_board_menu(state)
        elif choice == "14":
            toggle_assignment_mode(state)
        elif choice == "15":
            print(f"Exiting City Bus Manager. Thanks for playing, {state.company_name}!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting City Bus Manager Text Edition")
        sys.exit(0)
