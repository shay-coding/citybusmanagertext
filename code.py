import random
import sys
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class Stop:
    name: str
    distance_from_prev_km: float

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Stop(name=data["name"], distance_from_prev_km=data["distance_from_prev_km"])

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
    fleet_number: Optional[str] = None  # New field for fleet number

    def consume_fuel(self, distance, speed=50):
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
        )

@dataclass
class ManagerState:
    company_name: str
    routes: List[Route] = field(default_factory=list)
    fleet: List[Bus] = field(default_factory=list)
    money: float = 2500000.0  # Starting cash for new company
    reputation: float = 50.0
    day: int = 1
    next_bus_id: int = 1  # start IDs from 1 since empty fleet

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "routes": [route.to_dict() for route in self.routes],
            "fleet": [bus.to_dict() for bus in self.fleet],
            "money": self.money,
            "reputation": self.reputation,
            "day": self.day,
            "next_bus_id": self.next_bus_id,
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
        )


def save_game(state: ManagerState):
    filename = input("Enter filename to save to (e.g. my_company_save.json): ").strip()
    if not filename:
        print("Invalid filename. Save cancelled.")
        return
    try:
        with open(filename, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
        print(f"Game saved successfully to '{filename}'.")
    except Exception as e:
        print(f"Error saving game: {e}")

def load_game() -> Optional[ManagerState]:
    filename = input("Enter filename to load from (e.g. my_company_save.json): ").strip()
    if not filename:
        print("Invalid filename. Load cancelled.")
        return None
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        state = ManagerState.from_dict(data)
        print(f"Game loaded successfully from '{filename}'.")
        return state
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error loading game: {e}")
    return None


def print_main_menu(state: ManagerState):
    print(f"\n===== City Bus Manager — {state.company_name} =====")
    print("1) View Routes")
    print("2) View Fleet")
    print("3) Assign Bus to Route")
    print("4) Change Route Schedule")
    print("5) Run Day Simulation")
    print("6) Buy New Bus")
    print("7) Add New Route (Costs £500 per stop)")
    print("8) Delete Route")
    print("9) View Company Status")
    print("10) Save Game")
    print("11) Load Game")
    print("12) Quit")

def view_routes(state: ManagerState):
    if not state.routes:
        print("\nNo routes available yet.")
        return
    print("\n--- Routes ---")
    for i, route in enumerate(state.routes, 1):
        assigned_bus = next((b.model for b in state.fleet if b.bus_id == route.assigned_bus_id), "None")
        print(f"[{i}] {route.name} | Schedule: {route.current_schedule_minutes} mins | Bus: {assigned_bus}")

def view_fleet(state: ManagerState):
    if not state.fleet:
        print("\nNo buses in fleet yet.")
        return
    while True:
        print("\n--- Fleet ---")
        for bus in state.fleet:
            route_name = next((r.name for r in state.routes if r.assigned_bus_id == bus.bus_id), "None")
            fn = bus.fleet_number if bus.fleet_number else "N/A"
            print(f"[{bus.bus_id}] {bus.model} (Fleet No: {fn}) | Capacity: {bus.capacity} | Fuel: {bus.fuel_level:.1f}L | Health: {bus.health} | Assigned Route: {route_name}")

        print("\nOptions: [E] Edit Fleet Number, [Q] Return to Main Menu")
        choice = input("> ").strip().lower()
        if choice == 'e':
            edit_fleet_number(state)
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

    # Check duplicates
    if any(b.fleet_number == new_number and b.bus_id != bus.bus_id for b in state.fleet):
        print(f"Fleet number '{new_number}' already in use by another bus. Edit cancelled.")
        return

    bus.fleet_number = new_number
    print(f"Fleet number updated to '{new_number}' for bus ID {bus.bus_id}.")

def assign_bus_to_route(state: ManagerState):
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

    # Unassign bus from any other route
    for r in state.routes:
        if r.assigned_bus_id == bus.bus_id:
            r.assigned_bus_id = None

    # Assign bus
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

def run_day_simulation(state: ManagerState):
    if not state.routes:
        print("\nNo routes available to run.")
        return
    if not state.fleet:
        print("\nNo buses available to run routes.")
        return

    print(f"\n--- Running Day Simulation: Day {state.day} ---")
    total_earnings = 0.0
    total_fuel_cost = 0.0
    reputation_change = 0.0

    # For each route, simulate trip
    for route in state.routes:
        bus = next((b for b in state.fleet if b.bus_id == route.assigned_bus_id), None)
        if not bus:
            print(f"Route '{route.name}' has no bus assigned! No service today.")
            reputation_change -= 5
            continue

        print(f"\nRoute: {route.name}")
        print(f"Bus: {bus.model} (Fleet No: {bus.fleet_number if bus.fleet_number else 'N/A'}) (Capacity: {bus.capacity})")
        print(f"Schedule time: {route.current_schedule_minutes} mins")

        # Calculate distance
        total_distance = sum(stop.distance_from_prev_km for stop in route.stops[1:])
        # Assume ticket price £2.50 for simplicity
        ticket_price = 2.50

        # Passengers demand approx proportional to stops and route length
        avg_demand = int(total_distance * 10)
        passengers = min(bus.capacity, random.randint(max(0, avg_demand - 5), avg_demand + 5))
        earnings = passengers * ticket_price

        # Fuel consumption
        fuel_used = bus.consume_fuel(total_distance)
        fuel_cost = fuel_used * 1.60  # £1.60 per litre

        # Random event chance
        if random.random() < 0.15:
            event = random.choice(["flat tyre", "engine trouble", "heavy traffic"])
            print(f"** Event: {event}! Delays the route and costs £20 to fix. **")
            reputation_change -= 3
            state.money -= 20
        else:
            reputation_change += 1

        # Time impact on reputation
        if route.current_schedule_minutes < route.base_schedule_minutes:
            # Risky tight schedule
            if random.random() < 0.3:
                print("Tight schedule caused delays and unhappy passengers!")
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
    state.day += 1

    print(f"\nDay {state.day-1} summary:")
    print(f"Total fare income: £{total_earnings:.2f}")
    print(f"Total fuel cost: £{total_fuel_cost:.2f}")
    print(f"Net profit: £{net_profit:.2f}")
    print(f"Reputation change: {reputation_change:+.1f}")
    print(f"New reputation: {state.reputation:.1f}/100")
    print(f"Money available: £{state.money:.2f}")

def buy_new_bus(state: ManagerState):
    shop = [
        ("ADL Enviro200", 40, 160.0, 0.26, 90000),
        ("ADL Enviro200 MMC", 40, 160.0, 0.25, 95000),
        ("ADL Enviro400", 80, 240.0, 0.38, 135000),
        ("ADL Enviro400 MMC", 80, 240.0, 0.38, 140000),
        ("ADL Enviro400 City", 80, 240.0, 0.37, 145000),
        ("Wright Streetlite DF", 40, 150.0, 0.25, 72000),
        ("Wright Streetlite WF", 40, 150.0, 0.24, 73000),
        ("Wright Streetdeck", 75, 220.0, 0.36, 125000),
        ("Wright Streetdeck Ultroliner", 75, 220.0, 0.35, 130000),
        ("Wright Eclipse Urban", 40, 150.0, 0.26, 70000),
        ("Wright Eclipse Urban 2", 40, 150.0, 0.25, 72000),
        ("Wright Eclipse Gemini", 80, 230.0, 0.37, 130000),
        ("Wright Eclipse Gemini 2", 80, 230.0, 0.36, 132000),
        ("Wright Eclipse Gemini 3", 80, 230.0, 0.35, 135000),
        ("Scania N94UD Omnidekka", 80, 240.0, 0.40, 138000),
        ("Scania N270UD Omnicity", 80, 230.0, 0.38, 140000),
        ("Scania N230UD Enviro400", 80, 240.0, 0.37, 137000),
        ("Scania N250UD Enviro400 MMC", 80, 240.0, 0.36, 142000),
        ("Scania L94UB Wright Solar", 40, 150.0, 0.26, 72000),
        ("Optare Solo", 30, 120.0, 0.22, 60000),
        ("Optare Solo SR", 30, 120.0, 0.22, 62000),
        ("Dennis Trident Optare Olympus", 75, 230.0, 0.38, 125000),
        ("Volvo B7TL Plaxton President", 80, 230.0, 0.39, 130000),
        ("Dennis Dart MPD", 35, 140.0, 0.24, 65000),
    ]

    print("\n--- Bus Shop ---")
    for i, (model, capacity, fuel_cap, efficiency, price) in enumerate(shop, 1):
        print(f"[{i}] {model} | Capacity: {capacity} | Price: £{price:,}")

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

    model, capacity, fuel_cap, efficiency, price = shop[choice - 1]

    if state.money < price:
        print("You can't afford that bus yet!")
        return

    # Fleet number assignment
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
    new_bus = Bus(bus_id, model, capacity, fuel_cap, fuel_cap, efficiency, purchase_price=price, fleet_number=fleet_number)
    state.fleet.append(new_bus)
    state.money -= price
    print(f"Congratulations! You bought a new {model} with fleet number {fleet_number} for £{price:,}.")

def add_route(state: ManagerState):
    print("\n--- Add New Route ---")
    name = input("Enter route name: ").strip()
    if not name:
        print("Route name cannot be empty.")
        return

    print("Enter stops for the route. Type 'done' when finished.")
    stops = []
    prev_distance = 0.0
    while True:
        stop_name = input("Stop name (or 'done'): ").strip()
        if stop_name.lower() == "done":
            break
        if not stop_name:
            print("Stop name cannot be empty.")
            continue
        while True:
            try:
                dist = float(input(f"Distance from previous stop to {stop_name} in km: "))
                if dist < 0:
                    print("Distance cannot be negative.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")

        stops.append(Stop(stop_name, dist))

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

    # Base schedule: sum distances / avg speed (30 km/h) * 60 to minutes
    total_distance = sum(stop.distance_from_prev_km for stop in stops[1:])
    base_schedule = max(int(total_distance / 30 * 60), 10)

    new_route = Route(name, stops, base_schedule, base_schedule)
    state.routes.append(new_route)
    state.money -= cost
    print(f"Route '{name}' created with {len(stops)} stops, costing £{cost}.")

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
            save_game(state)
        elif choice == "11":
            loaded = load_game()
            if loaded:
                state = loaded
        elif choice == "12":
            print(f"Exiting City Bus Manager. Thanks for playing, {state.company_name}!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting City Bus Manager. Ta-ra!")
        sys.exit(0)
