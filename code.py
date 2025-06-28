"""
City Bus Manager - Text Edition

Manage your fleet, assign buses to routes, set schedules, and run your bus company!

Run: python3 city_bus_manager.py
"""

import random
import sys
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Stop:
    name: str
    distance_from_prev_km: float

@dataclass
class Route:
    name: str
    stops: List[Stop]
    base_schedule_minutes: int
    current_schedule_minutes: int
    assigned_bus_id: Optional[int] = None

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

    def consume_fuel(self, distance, speed=50):
        speed_factor = speed / 50
        used = distance * self.fuel_efficiency * speed_factor
        self.fuel_level = max(self.fuel_level - used, 0)
        return used

@dataclass
class ManagerState:
    routes: List[Route] = field(default_factory=list)
    fleet: List[Bus] = field(default_factory=list)
    money: float = 1000.0
    reputation: float = 50.0
    day: int = 1

def create_sample_routes():
    return [
        Route(
            name="Route 12: Newport - Ryde - Bembridge",
            stops=[
                Stop("Newport Bus Station", 0.0),
                Stop("Carisbrooke", 3.0),
                Stop("Shide", 2.5),
                Stop("Ryde Bus Station", 4.0),
                Stop("Binstead", 3.0),
                Stop("Bembridge", 5.0),
            ],
            base_schedule_minutes=70,
            current_schedule_minutes=70,
        ),
        Route(
            name="Route 22: Cowes Circular",
            stops=[
                Stop("Cowes Bus Station", 0.0),
                Stop("East Cowes", 3.0),
                Stop("Gurnard", 2.0),
                Stop("Northwood", 2.5),
                Stop("Cowes Bus Station", 2.5),
            ],
            base_schedule_minutes=50,
            current_schedule_minutes=50,
        ),
        Route(
            name="Route 100: Coastliner",
            stops=[
                Stop("Hewton", 0.0),
                Stop("Hethersett Castle", 8.0),
                Stop("Countryside Village", 6.0),
                Stop("Eastford Green", 5.0),
                Stop("Chesterleigh", 7.0),
            ],
            base_schedule_minutes=120,
            current_schedule_minutes=120,
        ),
    ]

def create_sample_fleet():
    return [
        Bus(1, "Optare Solo SR", 30, 120.0, 120.0, 0.22),
        Bus(2, "ADL Enviro200", 45, 180.0, 180.0, 0.28),
        Bus(3, "Wright Gemini 3", 70, 220.0, 220.0, 0.36),
        Bus(4, "Wright StreetLite", 40, 150.0, 150.0, 0.25),
        Bus(5, "Volvo B7TL Double-Decker", 80, 230.0, 230.0, 0.40),
    ]

def print_main_menu():
    print("\n===== City Bus Manager =====")
    print("1) View Routes")
    print("2) View Fleet")
    print("3) Assign Bus to Route")
    print("4) Change Route Schedule")
    print("5) Run Day Simulation")
    print("6) View Company Status")
    print("7) Quit")

def view_routes(state: ManagerState):
    print("\n--- Routes ---")
    for i, route in enumerate(state.routes, 1):
        assigned_bus = next((b.model for b in state.fleet if b.bus_id == route.assigned_bus_id), "None")
        print(f"[{i}] {route.name} | Schedule: {route.current_schedule_minutes} mins | Bus: {assigned_bus}")

def view_fleet(state: ManagerState):
    print("\n--- Fleet ---")
    for bus in state.fleet:
        route_name = next((r.name for r in state.routes if r.assigned_bus_id == bus.bus_id), "None")
        print(f"[{bus.bus_id}] {bus.model} | Capacity: {bus.capacity} | Fuel: {bus.fuel_level:.1f}L | Health: {bus.health} | Assigned Route: {route_name}")

def assign_bus_to_route(state: ManagerState):
    print("\nSelect Bus to assign:")
    for bus in state.fleet:
        print(f"[{bus.bus_id}] {bus.model} (Capacity: {bus.capacity})")

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
    print(f"Assigned {bus.model} to {route.name}")

def change_route_schedule(state: ManagerState):
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
        print(f"Bus: {bus.model} (Capacity: {bus.capacity})")
        print(f"Schedule time: {route.current_schedule_minutes} mins")

        # Calculate distance
        total_distance = sum(stop.distance_from_prev_km for stop in route.stops[1:])
        # Assume ticket price £2.50 for simplicity
        ticket_price = 2.50

        # Passengers demand approx proportional to stops and route length
        avg_demand = int(total_distance * 10)
        passengers = min(bus.capacity, random.randint(avg_demand - 5, avg_demand + 5))
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
        print(f"Fuel used: {fuel_used:.2f} L costing £{fuel_cost:.2f}")

    state.money += total_earnings - total_fuel_cost
    state.reputation = max(0, min(100, state.reputation + reputation_change))
    state.day += 1

    print("\n--- Day Summary ---")
    print(f"Total fare income: £{total_earnings:.2f}")
    print(f"Total fuel costs: £{total_fuel_cost:.2f}")
    print(f"Company money: £{state.money:.2f}")
    print(f"Company reputation: {state.reputation:.1f}/100")

def view_company_status(state: ManagerState):
    print(f"\n--- Company Status ---")
    print(f"Day: {state.day}")
    print(f"Money: £{state.money:.2f}")
    print(f"Reputation: {state.reputation:.1f}/100")
    print(f"Fleet size: {len(state.fleet)} buses")
    print(f"Routes managed: {len(state.routes)}")

def main():
    state = ManagerState()
    state.routes = create_sample_routes()
    state.fleet = create_sample_fleet()

    while True:
        print_main_menu()
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
            view_company_status(state)
        elif choice == "7":
            print("Exiting City Bus Manager. Thanks for playing!")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting City Bus Manager. Ta-ra!")
        sys.exit(0)
