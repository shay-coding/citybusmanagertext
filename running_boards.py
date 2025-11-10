import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, time

@dataclass
class Trip:
    route_name: str
    destination: str
    departure_time: str  # Format: "HH:MM"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Trip(
            route_name=data["route_name"],
            destination=data["destination"],
            departure_time=data["departure_time"]
        )

    def get_time_minutes(self) -> int:
        """Convert time string to minutes since midnight for comparison"""
        hours, minutes = map(int, self.departure_time.split(':'))
        return hours * 60 + minutes


@dataclass
class RunningBoard:
    name: str
    trips: List[Trip] = field(default_factory=list)
    assigned_bus_id: Optional[int] = None

    def to_dict(self):
        return {
            "name": self.name,
            "trips": [trip.to_dict() for trip in self.trips],
            "assigned_bus_id": self.assigned_bus_id
        }

    @staticmethod
    def from_dict(data):
        trips = [Trip.from_dict(t) for t in data["trips"]]
        return RunningBoard(
            name=data["name"],
            trips=trips,
            assigned_bus_id=data.get("assigned_bus_id")
        )

    def get_total_distance(self, routes) -> float:
        """Calculate total distance for all trips in this running board"""
        total = 0.0
        for trip in self.trips:
            route = next((r for r in routes if r.name == trip.route_name), None)
            if route:
                total += sum(stop.distance_from_prev_km for stop in route.stops[1:])
        return total

    def validate_against_routes(self, routes) -> tuple[bool, str]:
        """Validate that all routes in trips exist"""
        route_names = {r.name for r in routes}
        for trip in self.trips:
            if trip.route_name not in route_names:
                return False, f"Route '{trip.route_name}' not found"
        return True, ""


def save_running_board(board: RunningBoard):
    """Save a running board to the running_boards folder"""
    # Create running_boards folder if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    boards_folder = os.path.join(script_dir, "running_boards")

    if not os.path.exists(boards_folder):
        os.makedirs(boards_folder)
        print(f"Created running_boards folder at {boards_folder}")

    # Save with sanitized filename
    safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in board.name)
    filename = os.path.join(boards_folder, f"{safe_name}.json")

    try:
        with open(filename, "w") as f:
            json.dump(board.to_dict(), f, indent=2)
        print(f"Running board '{board.name}' saved successfully.")
        return True
    except Exception as e:
        print(f"Error saving running board: {e}")
        return False


def load_running_board(name: str) -> Optional[RunningBoard]:
    """Load a running board by name"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    boards_folder = os.path.join(script_dir, "running_boards")

    if not os.path.exists(boards_folder):
        return None

    safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name)
    filename = os.path.join(boards_folder, f"{safe_name}.json")

    try:
        with open(filename, "r") as f:
            data = json.load(f)
        return RunningBoard.from_dict(data)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading running board: {e}")
        return None


def list_running_boards() -> List[str]:
    """List all available running boards"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    boards_folder = os.path.join(script_dir, "running_boards")

    if not os.path.exists(boards_folder):
        return []

    boards = []
    for filename in os.listdir(boards_folder):
        if filename.endswith(".json"):
            try:
                filepath = os.path.join(boards_folder, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                boards.append(data["name"])
            except:
                pass

    return sorted(boards)


def delete_running_board(name: str) -> bool:
    """Delete a running board file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    boards_folder = os.path.join(script_dir, "running_boards")

    safe_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in name)
    filename = os.path.join(boards_folder, f"{safe_name}.json")

    try:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Running board '{name}' deleted.")
            return True
        else:
            print(f"Running board '{name}' not found.")
            return False
    except Exception as e:
        print(f"Error deleting running board: {e}")
        return False


def create_running_board_interactive(state):
    """Interactive creation of a running board"""
    print("\n--- Create Running Board ---")
    name = input("Enter running board name: ").strip()
    if not name:
        print("Running board name cannot be empty.")
        return None

    # Check if board already exists
    existing = load_running_board(name)
    if existing:
        overwrite = input(f"Running board '{name}' already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Creation cancelled.")
            return None

    print("\nEnter trips for this running board.")
    print("Format: Route - Destination - Time (HH:MM)")
    print("Type 'done' when finished.\n")

    if state.routes:
        print("Available routes:")
        for route in state.routes:
            print(f"  - {route.name}")
        print()

    trips = []
    while True:
        print(f"Trip {len(trips) + 1} (or 'done' to finish):")

        route_name = input("  Route name: ").strip()
        if route_name.lower() == "done":
            break

        if not route_name:
            print("  Route name cannot be empty.")
            continue

        # Validate route exists
        route = next((r for r in state.routes if r.name == route_name), None)
        if not route:
            print(f"  Warning: Route '{route_name}' not found in your routes.")
            confirm = input("  Add anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue

        destination = input("  Destination: ").strip()
        if not destination:
            print("  Destination cannot be empty.")
            continue

        while True:
            time_str = input("  Time (HH:MM): ").strip()
            try:
                # Validate time format
                hours, minutes = map(int, time_str.split(':'))
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    print("  Invalid time. Hours must be 0-23, minutes 0-59.")
                    continue
                time_str = f"{hours:02d}:{minutes:02d}"
                break
            except ValueError:
                print("  Invalid time format. Use HH:MM (e.g., 09:38)")

        trips.append(Trip(route_name, destination, time_str))
        print(f"  ✓ Added: {route_name} to {destination} at {time_str}\n")

    if len(trips) == 0:
        print("No trips added. Running board not created.")
        return None

    board = RunningBoard(name, trips)

    # Summary
    print(f"\n--- Running Board Summary ---")
    print(f"Name: {board.name}")
    print(f"Total trips: {len(board.trips)}")
    for i, trip in enumerate(board.trips, 1):
        print(f"  {i}. {trip.route_name} to {trip.destination} at {trip.departure_time}")

    confirm = input("\nSave this running board? (y/n): ").strip().lower()
    if confirm == 'y':
        if save_running_board(board):
            return board
    else:
        print("Running board not saved.")

    return None


def view_running_boards(state):
    """View all running boards and manage assignments"""
    boards_list = list_running_boards()

    if not boards_list:
        print("\nNo running boards created yet.")
        return

    print("\n--- Running Boards ---")
    for i, board_name in enumerate(boards_list, 1):
        board = load_running_board(board_name)
        if board:
            bus_info = "Not assigned"
            if board.assigned_bus_id:
                bus = next((b for b in state.fleet if b.bus_id == board.assigned_bus_id), None)
                if bus:
                    fn = bus.fleet_number if bus.fleet_number else "N/A"
                    bus_info = f"Bus {bus.bus_id} ({bus.model}, Fleet No: {fn})"

            print(f"[{i}] {board.name} - {len(board.trips)} trips - {bus_info}")

    print("\nOptions: [V] View Details, [A] Assign Bus, [D] Delete Board, [Q] Return")
    choice = input("> ").strip().lower()

    if choice == 'v':
        view_running_board_details(state)
    elif choice == 'a':
        assign_bus_to_running_board(state)
    elif choice == 'd':
        delete_running_board_interactive(state)
    elif choice == 'q':
        return
    else:
        print("Invalid option.")


def view_running_board_details(state):
    """View detailed information about a specific running board"""
    board_name = input("\nEnter running board name to view: ").strip()
    if not board_name:
        return

    board = load_running_board(board_name)
    if not board:
        print(f"Running board '{board_name}' not found.")
        return

    print(f"\n--- Running Board: {board.name} ---")
    print(f"Total trips: {len(board.trips)}")

    if board.assigned_bus_id:
        bus = next((b for b in state.fleet if b.bus_id == board.assigned_bus_id), None)
        if bus:
            fn = bus.fleet_number if bus.fleet_number else "N/A"
            print(f"Assigned to: Bus {bus.bus_id} ({bus.model}, Fleet No: {fn})")
        else:
            print(f"Assigned to: Bus ID {board.assigned_bus_id} (not found)")
    else:
        print("Assigned to: None")

    print("\nTrips:")
    for i, trip in enumerate(board.trips, 1):
        route = next((r for r in state.routes if r.name == trip.route_name), None)
        route_status = "✓" if route else "✗ (route not found)"
        print(f"  {i}. {trip.departure_time} - {trip.route_name} to {trip.destination} {route_status}")

    total_distance = board.get_total_distance(state.routes)
    print(f"\nEstimated total distance: {total_distance:.1f} km")

    valid, error = board.validate_against_routes(state.routes)
    if not valid:
        print(f"\n⚠ Warning: {error}")


def assign_bus_to_running_board(state):
    """Assign a bus to a running board"""
    if not state.fleet:
        print("\nNo buses available. Buy some first.")
        return

    board_name = input("\nEnter running board name: ").strip()
    if not board_name:
        return

    board = load_running_board(board_name)
    if not board:
        print(f"Running board '{board_name}' not found.")
        return

    print("\nAvailable buses:")
    for bus in state.fleet:
        fn = bus.fleet_number if bus.fleet_number else "N/A"
        # Check if bus is assigned to another running board
        other_boards = []
        for other_name in list_running_boards():
            other = load_running_board(other_name)
            if other and other.assigned_bus_id == bus.bus_id and other.name != board.name:
                other_boards.append(other.name)

        assignment = f" (Assigned to: {', '.join(other_boards)})" if other_boards else ""
        print(f"[{bus.bus_id}] {bus.model} (Fleet No: {fn}){assignment}")

    try:
        bus_id = int(input("\nSelect bus ID (or 0 to unassign): "))
    except ValueError:
        print("Invalid input.")
        return

    if bus_id == 0:
        board.assigned_bus_id = None
        save_running_board(board)
        print(f"Bus unassigned from running board '{board.name}'.")
        return

    bus = next((b for b in state.fleet if b.bus_id == bus_id), None)
    if not bus:
        print("Bus not found.")
        return

    board.assigned_bus_id = bus_id
    save_running_board(board)
    fn = bus.fleet_number if bus.fleet_number else "N/A"
    print(f"Assigned {bus.model} (Fleet No: {fn}) to running board '{board.name}'.")


def delete_running_board_interactive(state):
    """Interactively delete a running board"""
    board_name = input("\nEnter running board name to delete: ").strip()
    if not board_name:
        return

    board = load_running_board(board_name)
    if not board:
        print(f"Running board '{board_name}' not found.")
        return

    if board.assigned_bus_id:
        print(f"Warning: This running board is assigned to Bus ID {board.assigned_bus_id}.")

    confirm = input(f"Are you sure you want to delete '{board_name}'? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_running_board(board_name)
    else:
        print("Deletion cancelled.")
