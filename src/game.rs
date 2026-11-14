use crate::{Bus, ManagerState, Route, RunningBoard, Stop, Trip};
use rand::Rng;
use serde::Deserialize;
use serde_json::json;
use std::collections::{BTreeMap, HashSet};
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

const LIVERIES: &[&str] = &[
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
];

#[derive(Debug, Clone)]
struct Vehicle {
    model: String,
    capacity: u32,
    fuel_capacity: f64,
    fuel_efficiency: f64,
    price: f64,
    dlc_source: Option<String>,
}

#[derive(Deserialize)]
struct DlcFile {
    dlc_name: String,
    vehicles: Vec<DlcVehicle>,
}

#[derive(Deserialize)]
struct DlcVehicle {
    model: String,
    capacity: u32,
    fuel_capacity: f64,
    fuel_efficiency: f64,
    #[serde(alias = "purchase_price")]
    price: f64,
}

fn root_dir() -> PathBuf {
    let executable_dir = std::env::current_exe()
        .ok()
        .and_then(|path| path.parent().map(Path::to_path_buf));
    let current_dir = std::env::current_dir().ok();
    if let Some(path) = executable_dir.as_ref() {
        if path.join("dlcs_and_mods").exists() || path.join("saves").exists() {
            return path.clone();
        }
    }
    if let Some(path) = current_dir.as_ref() {
        if path.join("dlcs_and_mods").exists() || path.join("saves").exists() {
            return path.clone();
        }
    }
    executable_dir
        .or(current_dir)
        .unwrap_or_else(|| PathBuf::from("."))
}

fn input(prompt: &str) -> String {
    print!("{prompt}");
    let _ = io::stdout().flush();
    let mut value = String::new();
    match io::stdin().read_line(&mut value) {
        Ok(0) | Err(_) => std::process::exit(0),
        Ok(_) => value.trim().to_owned(),
    }
}

fn number(prompt: &str) -> Option<i64> {
    input(prompt).parse().ok()
}

fn confirm(prompt: &str) -> bool {
    input(prompt).eq_ignore_ascii_case("y")
}

fn safe_name(value: &str) -> String {
    value
        .chars()
        .map(|ch| {
            if ch.is_alphanumeric() || matches!(ch, ' ' | '_' | '-') {
                ch
            } else {
                '_'
            }
        })
        .collect()
}

fn log_action(message: &str) {
    let path = root_dir().join("running_boards").join("activity.log");
    if let Some(parent) = path.parent() {
        let _ = fs::create_dir_all(parent);
    }
    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(path) {
        let _ = writeln!(file, "{message}");
    }
}

pub fn run() {
    println!("Welcome to City Bus Manager!");
    let company = input("Please enter your company name (or leave blank to load a game): ");
    let mut state = if company.is_empty() {
        load_game().unwrap_or_else(|| {
            println!("Starting a new company.");
            ManagerState::new("My Bus Company".to_owned())
        })
    } else {
        ManagerState::new(company)
    };
    println!(
        "\nWelcome, {}! You start with £{:.2}.",
        state.company_name, state.money
    );

    loop {
        let mode = if state.use_running_boards {
            "Running Boards"
        } else {
            "Static Routes"
        };
        println!(
            "\n===== City Bus Manager - {} [Mode: {}] =====",
            state.company_name, mode
        );
        println!("Fuel Price: £{:.2}/L\n1) View Information\n2) Route Management\n3) Fleet Management\n4) Operations\n5) Game Management\n6) Quit", state.fuel_price);
        match input("> ").as_str() {
            "1" => information_menu(&mut state),
            "2" => route_menu(&mut state),
            "3" => fleet_menu(&mut state),
            "4" => operations_menu(&mut state),
            "5" => game_menu(&mut state),
            "6" => {
                println!(
                    "Exiting City Bus Manager. Thanks for playing, {}!",
                    state.company_name
                );
                break;
            }
            _ => println!("Invalid option, try again."),
        }
    }
}

fn information_menu(state: &mut ManagerState) {
    loop {
        println!("\n--- VIEW INFORMATION ---\n1) View Routes\n2) View Fleet\n3) View Company Status\n4) View Fuel Price Details\n5) Back");
        match input("> ").as_str() {
            "1" => view_routes(state),
            "2" => view_fleet(state),
            "3" => view_status(state),
            "4" => println!("Current fuel price: £{:.2}/L", state.fuel_price),
            "5" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn route_menu(state: &mut ManagerState) {
    loop {
        println!("\n--- ROUTE MANAGEMENT ---\n1) Assign Bus to Route\n2) Change Route Schedule\n3) Add New Route\n4) Delete Route\n5) Back");
        match input("> ").as_str() {
            "1" => assign_route(state),
            "2" => change_schedule(state),
            "3" => add_route(state),
            "4" => delete_route(state),
            "5" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn fleet_menu(state: &mut ManagerState) {
    loop {
        println!("\n--- FLEET MANAGEMENT ---\n1) Buy New Bus\n2) Import Fleet from CSV\n3) Back");
        match input("> ").as_str() {
            "1" => buy_bus(state),
            "2" => import_fleet(state),
            "3" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn operations_menu(state: &mut ManagerState) {
    loop {
        println!(
            "\n--- OPERATIONS ---\n1) Run Day Simulation\n2) Running Board Management\n3) Back"
        );
        match input("> ").as_str() {
            "1" => simulate_day(state),
            "2" => board_menu(state),
            "3" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn game_menu(state: &mut ManagerState) {
    loop {
        println!("\n--- GAME MANAGEMENT ---\n1) Save Game\n2) Load Game\n3) Toggle Assignment Mode\n4) Export Visualization Data\n5) Back");
        match input("> ").as_str() {
            "1" => save_game(state),
            "2" => {
                if let Some(loaded) = load_game() {
                    *state = loaded
                }
            }
            "3" => {
                let next_mode = !state.use_running_boards;
                if confirm(if next_mode {
                    "Switch to Running Boards mode? (y/n): "
                } else {
                    "Switch to Static Routes mode? (y/n): "
                }) {
                    state.use_running_boards = next_mode;
                }
            }
            "4" => export_visualization(state),
            "5" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn view_routes(state: &ManagerState) {
    if state.routes.is_empty() {
        println!("No routes available yet.");
        return;
    }
    for (index, route) in state.routes.iter().enumerate() {
        let bus = route
            .assigned_bus_id
            .and_then(|id| state.fleet.iter().find(|bus| bus.bus_id == id))
            .map(|bus| bus.model.as_str())
            .unwrap_or("None");
        println!(
            "[{}] {} | Journey: {} mins | Schedule: {} mins | Bus: {}",
            index + 1,
            route.name,
            route_minutes(route),
            route.current_schedule_minutes,
            bus
        );
    }
}

fn view_fleet(state: &mut ManagerState) {
    loop {
        if state.fleet.is_empty() {
            println!("No buses in fleet yet.");
            return;
        }
        for bus in &state.fleet {
            let route = bus.assigned_route.as_deref().unwrap_or("None");
            println!("[{}] {} (Fleet No: {}) | Livery: {} | Capacity: {} | Fuel: {:.1}L | Health: {} | Route: {}",
                bus.bus_id, bus.model, bus.fleet_number.as_deref().unwrap_or("N/A"), bus.livery,
                bus.capacity, bus.fuel_level, bus.health, route);
        }
        match input("Options: [E] Edit Fleet Number, [L] Change Livery, [Q] Return: ")
            .to_lowercase()
            .as_str()
        {
            "e" => edit_fleet_number(state),
            "l" => change_livery(state),
            "q" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn edit_fleet_number(state: &mut ManagerState) {
    let Some(id) = number("Bus ID (0 to cancel): ") else {
        println!("Invalid ID.");
        return;
    };
    if id == 0 {
        return;
    }
    let Some(index) = state.fleet.iter().position(|bus| bus.bus_id == id as u64) else {
        println!("Bus not found.");
        return;
    };
    let value = input("New fleet number: ");
    if value.is_empty() {
        println!("Cancelled.");
        return;
    }
    if state
        .fleet
        .iter()
        .enumerate()
        .any(|(i, bus)| i != index && bus.fleet_number.as_deref() == Some(&value))
    {
        println!("Fleet number already in use.");
        return;
    }
    state.fleet[index].fleet_number = Some(value);
}

fn change_livery(state: &mut ManagerState) {
    let Some(id) = number("Bus ID (0 to cancel): ") else {
        println!("Invalid ID.");
        return;
    };
    let Some(index) = state.fleet.iter().position(|bus| bus.bus_id == id as u64) else {
        println!("Bus not found.");
        return;
    };
    for (i, livery) in LIVERIES.iter().enumerate() {
        println!("[{}] {}", i + 1, livery);
    }
    let Some(choice) = number("Livery number: ") else {
        println!("Invalid number.");
        return;
    };
    if !(1..=LIVERIES.len() as i64).contains(&choice) {
        println!("Cancelled.");
        return;
    }
    if state.money < 500.0 {
        println!("Not enough money.");
        return;
    }
    state.fleet[index].livery = LIVERIES[(choice - 1) as usize].to_owned();
    state.money -= 500.0;
}

fn assign_route(state: &mut ManagerState) {
    if state.use_running_boards {
        println!("Switch to static mode to assign buses to routes.");
        return;
    }
    if state.fleet.is_empty() || state.routes.is_empty() {
        println!("You need at least one bus and one route.");
        return;
    }
    for bus in &state.fleet {
        println!("[{}] {}", bus.bus_id, bus.model);
    }
    let Some(bus_id) = number("Bus ID: ") else {
        println!("Invalid ID.");
        return;
    };
    let Some(bus_index) = state
        .fleet
        .iter()
        .position(|bus| bus.bus_id == bus_id as u64)
    else {
        println!("Bus not found.");
        return;
    };
    for (i, route) in state.routes.iter().enumerate() {
        println!("[{}] {}", i + 1, route.name);
    }
    let Some(route_index) =
        number("Route number: ").and_then(|value| usize::try_from(value - 1).ok())
    else {
        println!("Invalid route.");
        return;
    };
    if route_index >= state.routes.len() {
        println!("Route not found.");
        return;
    }
    let selected_id = state.fleet[bus_index].bus_id;
    for route in &mut state.routes {
        if route.assigned_bus_id == Some(selected_id) {
            route.assigned_bus_id = None;
        }
    }
    let route_name = state.routes[route_index].name.clone();
    state.routes[route_index].assigned_bus_id = Some(selected_id);
    state.fleet[bus_index].assigned_route = Some(route_name);
}

fn change_schedule(state: &mut ManagerState) {
    for (i, route) in state.routes.iter().enumerate() {
        println!(
            "[{}] {} | {} mins",
            i + 1,
            route.name,
            route.current_schedule_minutes
        );
    }
    let Some(index) = number("Route number: ").and_then(|value| usize::try_from(value - 1).ok())
    else {
        println!("Invalid route.");
        return;
    };
    if index >= state.routes.len() {
        println!("Route not found.");
        return;
    }
    let Some(minutes) = number("New schedule minutes: ") else {
        println!("Invalid time.");
        return;
    };
    if minutes < state.routes[index].base_schedule_minutes / 2 {
        println!("Schedule is too short.");
        return;
    }
    state.routes[index].current_schedule_minutes = minutes;
}

fn add_route(state: &mut ManagerState) {
    let name = input("Route name: ");
    if name.is_empty() {
        println!("Route name cannot be empty.");
        return;
    }
    let mut stops = Vec::new();
    loop {
        let stop_name = input("Stop name (or done): ");
        if stop_name.eq_ignore_ascii_case("done") {
            break;
        }
        if stop_name.is_empty() {
            continue;
        }
        let Some(minutes) = number("Minutes from previous stop: ") else {
            println!("Invalid time.");
            continue;
        };
        if minutes < 0 {
            println!("Time cannot be negative.");
            continue;
        }
        stops.push(Stop {
            name: stop_name,
            minutes_from_prev: minutes,
        });
    }
    if stops.len() < 2 {
        println!("A route needs at least two stops.");
        return;
    }
    let cost = 500.0 * stops.len() as f64;
    if state.money < cost
        || !confirm(&format!(
            "Creating this route costs £{cost:.2}. Confirm? (y/n): "
        ))
    {
        println!("Cancelled or insufficient funds.");
        return;
    }
    let total = stops
        .iter()
        .skip(1)
        .map(|stop| stop.minutes_from_prev)
        .sum::<i64>();
    let schedule = (total as f64 * 1.2) as i64;
    state.routes.push(Route {
        name,
        stops,
        base_schedule_minutes: schedule,
        current_schedule_minutes: schedule,
        assigned_bus_id: None,
    });
    state.money -= cost;
}

fn delete_route(state: &mut ManagerState) {
    for (i, route) in state.routes.iter().enumerate() {
        println!(
            "[{}] {}{}",
            i + 1,
            route.name,
            if route.assigned_bus_id.is_some() {
                " (assigned)"
            } else {
                ""
            }
        );
    }
    let Some(index) = number("Route number: ").and_then(|value| usize::try_from(value - 1).ok())
    else {
        println!("Invalid route.");
        return;
    };
    if index >= state.routes.len() {
        println!("Route not found.");
        return;
    }
    if state.routes[index].assigned_bus_id.is_some() {
        println!("Unassign the bus first.");
        return;
    }
    if confirm("Delete this route? (y/n): ") {
        state.routes.remove(index);
    }
}

fn route_minutes(route: &Route) -> i64 {
    route
        .stops
        .iter()
        .skip(1)
        .map(|stop| stop.minutes_from_prev)
        .sum()
}

fn simulate_day(state: &mut ManagerState) {
    if state.use_running_boards {
        simulate_boards(state);
    } else {
        simulate_static(state);
    }
}

fn simulate_static(state: &mut ManagerState) {
    if state.routes.is_empty() || state.fleet.is_empty() {
        println!("You need routes and buses to operate.");
        return;
    }
    let mut rng = rand::thread_rng();
    let (mut earnings, mut fuel_cost, mut reputation_change) = (0.0, 0.0, 0.0);
    for index in 0..state.routes.len() {
        let route = state.routes[index].clone();
        let Some(bus_id) = route.assigned_bus_id else {
            println!("Route '{}' has no assigned bus.", route.name);
            reputation_change -= 5.0;
            continue;
        };
        let Some(bus_index) = state.fleet.iter().position(|bus| bus.bus_id == bus_id) else {
            reputation_change -= 5.0;
            continue;
        };
        let total_time = route_minutes(&route);
        let avg_demand = (total_time * 3 / 2).max(0) as u32;
        let passengers = rng
            .gen_range(avg_demand.saturating_sub(5)..=avg_demand.saturating_add(5))
            .min(state.fleet[bus_index].capacity);
        let income = passengers as f64 * 2.5;
        let fuel_used = consume_fuel(&mut state.fleet[bus_index], total_time, 30.0);
        let cost = fuel_used * state.fuel_price;
        if rng.gen_bool(0.2) {
            println!("Event: service disruption on {} (£200).", route.name);
            state.money -= 200.0;
            reputation_change -= 3.0;
        } else {
            reputation_change += 1.0;
        }
        if route.current_schedule_minutes < route.base_schedule_minutes && rng.gen_bool(0.3) {
            reputation_change -= 2.0;
        } else {
            reputation_change += 1.0;
        }
        earnings += income;
        fuel_cost += cost;
        println!(
            "{}: {passengers} passengers, £{income:.2} fares, {fuel_used:.2}L fuel.",
            route.name
        );
    }
    finish_day(state, earnings, fuel_cost, reputation_change);
}

fn simulate_boards(state: &mut ManagerState) {
    let boards = list_boards();
    let boards: Vec<_> = boards
        .into_iter()
        .filter_map(|name| load_board(&name))
        .filter(|board| board.assigned_bus_id.is_some())
        .collect();
    if boards.is_empty() {
        println!("No running boards with assigned buses.");
        return;
    }
    let mut rng = rand::thread_rng();
    let (mut earnings, mut fuel_cost, mut reputation_change) = (0.0, 0.0, 0.0);
    for board in boards {
        let Some(bus_id) = board.assigned_bus_id else {
            continue;
        };
        let Some(bus_index) = state.fleet.iter().position(|bus| bus.bus_id == bus_id) else {
            println!("Invalid bus on board '{}'.", board.name);
            continue;
        };
        for trip in &board.trips {
            let Some(route) = state
                .routes
                .iter()
                .find(|route| route.name == trip.route_name)
            else {
                println!("Route '{}' not found; skipping trip.", trip.route_name);
                reputation_change -= 2.0;
                continue;
            };
            let total_time = route_minutes(route);
            let fuel_estimate =
                total_time as f64 / 60.0 * 30.0 * state.fleet[bus_index].fuel_efficiency;
            if state.fleet[bus_index].fuel_level < fuel_estimate {
                println!("{}: insufficient fuel; trip cancelled.", trip.route_name);
                reputation_change -= 5.0;
                continue;
            }
            let average_demand = (total_time * 3 / 2).max(0) as u32;
            let passengers = rng
                .gen_range(average_demand.saturating_sub(5)..=average_demand.saturating_add(5))
                .min(state.fleet[bus_index].capacity);
            let income = passengers as f64 * 2.5;
            let used = consume_fuel(&mut state.fleet[bus_index], total_time, 30.0);
            earnings += income;
            fuel_cost += used * state.fuel_price;
            if rng.gen_bool(0.1) {
                reputation_change -= 1.0;
            } else {
                reputation_change += 0.5;
            }
            println!(
                "{} - {} to {}: {passengers} passengers, £{income:.2}.",
                trip.departure_time, trip.route_name, trip.destination
            );
        }
    }
    finish_day(state, earnings, fuel_cost, reputation_change);
}

fn consume_fuel(bus: &mut Bus, minutes: i64, speed: f64) -> f64 {
    let distance = minutes.max(0) as f64 / 60.0 * speed;
    let used = distance * bus.fuel_efficiency * speed / 50.0;
    bus.fuel_level = (bus.fuel_level - used).max(0.0);
    used
}

fn finish_day(state: &mut ManagerState, earnings: f64, fuel_cost: f64, reputation_change: f64) {
    let profit = earnings - fuel_cost;
    state.money += profit;
    state.reputation = (state.reputation + reputation_change).clamp(0.0, 100.0);
    let mut rng = rand::thread_rng();
    state.fuel_price = (state.fuel_price + rng.gen_range(-0.05..=0.05)).clamp(1.25, 2.0);
    println!("Day {} summary: fares £{earnings:.2}, fuel £{fuel_cost:.2}, net £{profit:.2}, reputation {:.1}, balance £{:.2}", state.day, state.reputation, state.money);
    state.day += 1;
}

fn base_vehicles() -> Vec<Vehicle> {
    let entries = [
        ("ADL Enviro200", 40, 160.0, 0.26, 90000.0),
        ("ADL Enviro200 MMC", 40, 160.0, 0.25, 95000.0),
        ("ADL Enviro400", 80, 240.0, 0.38, 135000.0),
        ("ADL Enviro400 MMC", 80, 240.0, 0.38, 140000.0),
        ("ADL Enviro400 City", 80, 240.0, 0.37, 145000.0),
        ("Wright Streetlite DF", 40, 150.0, 0.25, 72000.0),
        ("Wright Streetlite WF", 40, 150.0, 0.24, 73000.0),
        ("Wright Streetdeck Ultroliner", 75, 220.0, 0.35, 130000.0),
        ("Wright Eclipse Urban", 40, 150.0, 0.26, 70000.0),
        ("Wright Eclipse Urban 2", 40, 150.0, 0.25, 72000.0),
        ("Wright Eclipse Gemini", 80, 230.0, 0.37, 130000.0),
        ("Wright Eclipse Gemini 2", 80, 230.0, 0.36, 132000.0),
        ("Wright Eclipse Gemini 3", 80, 230.0, 0.35, 135000.0),
        ("Scania N94UD Omnidekka", 80, 240.0, 0.40, 138000.0),
        ("Scania N270UD Omnicity", 80, 230.0, 0.38, 140000.0),
        ("Scania N230UD Enviro400", 80, 240.0, 0.37, 137000.0),
        ("Scania N250UD Enviro400 MMC", 80, 240.0, 0.36, 142000.0),
        ("Scania L94UB Wright Solar", 40, 150.0, 0.26, 72000.0),
        ("Optare Solo", 30, 120.0, 0.22, 60000.0),
        ("Optare Solo SR", 30, 120.0, 0.22, 62000.0),
        ("Dennis Trident Optare Olympus", 75, 230.0, 0.38, 125000.0),
        ("Volvo B7TL Plaxton President", 80, 230.0, 0.39, 130000.0),
        ("Dennis Dart MPD", 35, 140.0, 0.24, 65000.0),
    ];
    entries
        .into_iter()
        .map(
            |(model, capacity, fuel_capacity, fuel_efficiency, price)| Vehicle {
                model: format!("{model} [Base Game]"),
                capacity,
                fuel_capacity,
                fuel_efficiency,
                price,
                dlc_source: None,
            },
        )
        .collect()
}

fn shop_vehicles() -> Vec<Vehicle> {
    let mut vehicles = base_vehicles();
    let folder = root_dir().join("dlcs_and_mods");
    let Ok(entries) = fs::read_dir(folder) else {
        return vehicles;
    };
    for entry in entries
        .flatten()
        .filter(|entry| entry.path().extension().is_some_and(|ext| ext == "json"))
    {
        let Ok(contents) = fs::read_to_string(entry.path()) else {
            continue;
        };
        let Ok(dlc) = serde_json::from_str::<DlcFile>(&contents) else {
            println!("Skipping invalid DLC file {}.", entry.path().display());
            continue;
        };
        println!(
            "Loaded DLC: {} ({} vehicles)",
            dlc.dlc_name,
            dlc.vehicles.len()
        );
        vehicles.extend(dlc.vehicles.into_iter().map(|vehicle| Vehicle {
            model: vehicle.model,
            capacity: vehicle.capacity,
            fuel_capacity: vehicle.fuel_capacity,
            fuel_efficiency: vehicle.fuel_efficiency,
            price: vehicle.price,
            dlc_source: Some(dlc.dlc_name.clone()),
        }));
    }
    vehicles
}

fn buy_bus(state: &mut ManagerState) {
    let shop = shop_vehicles();
    for (index, vehicle) in shop.iter().enumerate() {
        println!(
            "[{}] {}{} | Capacity: {} | Price: £{:.0}",
            index + 1,
            vehicle.model,
            vehicle
                .dlc_source
                .as_ref()
                .map(|name| format!(" [{name}]"))
                .unwrap_or_default(),
            vehicle.capacity,
            vehicle.price
        );
    }
    println!("Balance: £{:.2}", state.money);
    let Some(choice) = number("Bus number (0 cancels): ") else {
        println!("Invalid number.");
        return;
    };
    if choice == 0 {
        return;
    }
    let Some(vehicle) = usize::try_from(choice - 1)
        .ok()
        .and_then(|index| shop.get(index))
        .cloned()
    else {
        println!("Invalid choice.");
        return;
    };
    if state.money < vehicle.price {
        println!("Not enough money.");
        return;
    }
    let fleet_number = choose_fleet_number(state);
    if fleet_number.is_none() {
        return;
    }
    state.fleet.push(Bus {
        bus_id: state.next_bus_id,
        model: vehicle.model,
        capacity: vehicle.capacity,
        fuel_capacity: vehicle.fuel_capacity,
        fuel_level: vehicle.fuel_capacity,
        fuel_efficiency: vehicle.fuel_efficiency,
        assigned_route: None,
        health: 100,
        purchase_price: vehicle.price,
        fleet_number,
        dlc_source: vehicle.dlc_source,
        livery: "Standard".to_owned(),
    });
    state.next_bus_id += 1;
    state.money -= vehicle.price;
    println!("Bus purchased.");
}

fn choose_fleet_number(state: &ManagerState) -> Option<String> {
    let entered = input("Fleet number (blank for auto-assignment): ");
    assign_fleet_number(state, &entered)
}

fn assign_fleet_number(state: &ManagerState, entered: &str) -> Option<String> {
    let existing: HashSet<_> = state
        .fleet
        .iter()
        .filter_map(|bus| bus.fleet_number.clone())
        .collect();
    let value = if entered.trim().is_empty() {
        let mut number = 1;
        while existing.contains(&number.to_string()) {
            number += 1;
        }
        number.to_string()
    } else {
        entered.trim().to_owned()
    };
    if existing.contains(&value) {
        println!("Fleet number already in use.");
        None
    } else {
        Some(value)
    }
}

fn import_fleet(state: &mut ManagerState) {
    let name = input("CSV filename in the game folder (0 cancels): ");
    if name == "0" {
        return;
    }
    let path = root_dir().join(if name.ends_with(".csv") {
        name
    } else {
        format!("{name}.csv")
    });
    let mut reader = match csv::Reader::from_path(&path) {
        Ok(reader) => reader,
        Err(error) => {
            println!("Could not read CSV: {error}");
            return;
        }
    };
    let headers = match reader.headers() {
        Ok(headers) => headers.clone(),
        Err(error) => {
            println!("Invalid CSV headers: {error}");
            return;
        }
    };
    for required in ["model", "capacity", "fuel_capacity", "fuel_efficiency"] {
        if !headers.iter().any(|header| header == required) {
            println!("CSV is missing required column '{required}'.");
            return;
        }
    }
    let mut imported = 0;
    let mut skipped = 0;
    let mut cost = 0.0;
    for (row_index, result) in reader.records().enumerate() {
        let Ok(row) = result else {
            skipped += 1;
            continue;
        };
        let field = |key: &str| {
            headers
                .iter()
                .position(|header| header == key)
                .and_then(|index| row.get(index))
                .unwrap_or("")
                .trim()
        };
        let parsed = (
            field("model").to_owned(),
            field("capacity").parse::<u32>(),
            field("fuel_capacity").parse::<f64>(),
            field("fuel_efficiency").parse::<f64>(),
        );
        let (model, Ok(capacity), Ok(fuel_capacity), Ok(fuel_efficiency)) = parsed else {
            println!("Row {} skipped.", row_index + 2);
            skipped += 1;
            continue;
        };
        if model.is_empty() || capacity == 0 || fuel_capacity <= 0.0 || fuel_efficiency <= 0.0 {
            skipped += 1;
            continue;
        }
        let purchase_price = field("purchase_price").parse::<f64>().unwrap_or(0.0);
        let supplied_number = field("fleet_number").to_owned();
        if !supplied_number.is_empty()
            && state
                .fleet
                .iter()
                .any(|bus| bus.fleet_number.as_deref() == Some(&supplied_number))
        {
            skipped += 1;
            continue;
        }
        let fleet_number = if supplied_number.is_empty() {
            assign_fleet_number(state, &supplied_number).unwrap_or_default()
        } else {
            supplied_number
        };
        if fleet_number.is_empty() {
            skipped += 1;
            continue;
        }
        let supplied_livery = field("livery");
        let livery = if LIVERIES.contains(&supplied_livery) {
            supplied_livery
        } else {
            "Standard"
        };
        state.fleet.push(Bus {
            bus_id: state.next_bus_id,
            model,
            capacity,
            fuel_capacity,
            fuel_level: fuel_capacity,
            fuel_efficiency,
            assigned_route: None,
            health: 100,
            purchase_price,
            fleet_number: Some(fleet_number),
            dlc_source: None,
            livery: livery.to_owned(),
        });
        state.next_bus_id += 1;
        imported += 1;
        cost += purchase_price;
    }
    if state.money >= cost {
        state.money -= cost;
    } else {
        println!("Warning: buses were imported but payment was not deducted (insufficient funds).");
    }
    println!("Imported {imported} buses; skipped {skipped}; total cost £{cost:.2}.");
}

fn save_game(state: &ManagerState) {
    let name = input("Save filename: ");
    if name.is_empty() || name.contains('/') || name.contains('\\') {
        println!("Invalid filename.");
        return;
    }
    let filename = if name.ends_with(".json") {
        name
    } else {
        format!("{name}.json")
    };
    let folder = root_dir().join("saves");
    if let Err(error) = fs::create_dir_all(&folder) {
        println!("Cannot create saves folder: {error}");
        return;
    }
    let result = serde_json::to_vec_pretty(state)
        .map_err(|error| error.to_string())
        .and_then(|data| fs::write(folder.join(filename), data).map_err(|error| error.to_string()));
    match result {
        Ok(()) => println!("Game saved."),
        Err(error) => println!("Save failed: {error}"),
    }
}

fn load_game() -> Option<ManagerState> {
    let folder = root_dir().join("saves");
    let mut files: Vec<_> = fs::read_dir(&folder)
        .ok()?
        .flatten()
        .filter(|entry| entry.path().extension().is_some_and(|ext| ext == "json"))
        .map(|entry| entry.file_name().to_string_lossy().to_string())
        .collect();
    files.sort();
    if files.is_empty() {
        println!("No saved games found.");
        return None;
    }
    for (index, file) in files.iter().enumerate() {
        println!("[{}] {}", index + 1, file);
    }
    let choice = input("Save number, filename, or 0 to cancel: ");
    if choice == "0" {
        return None;
    }
    let filename = choice
        .parse::<usize>()
        .ok()
        .and_then(|index| index.checked_sub(1))
        .and_then(|index| files.get(index).cloned())
        .or_else(|| {
            let filename = if choice.ends_with(".json") {
                choice.clone()
            } else {
                format!("{choice}.json")
            };
            files.contains(&filename).then_some(filename)
        });
    let Some(filename) = filename else {
        println!("Save not found.");
        return None;
    };
    let result = fs::read(folder.join(filename))
        .map_err(|error| error.to_string())
        .and_then(|bytes| {
            serde_json::from_slice::<ManagerState>(&bytes).map_err(|error| error.to_string())
        });
    match result {
        Ok(state) => {
            println!("Loaded save version {}.", state.save_version);
            Some(state)
        }
        Err(error) => {
            println!("Could not load save: {error}");
            None
        }
    }
}

fn export_visualization(state: &ManagerState) {
    let routes: Vec<_> = state.routes.iter().map(|route| json!({
        "name": route.name,
        "stops": route.stops.iter().map(|stop| json!({"name": stop.name, "minutes_from_prev": stop.minutes_from_prev})).collect::<Vec<_>>(),
        "base_schedule_minutes": route.base_schedule_minutes,
        "current_schedule_minutes": route.current_schedule_minutes,
        "assigned_bus_id": route.assigned_bus_id,
    })).collect();
    let fleet: Vec<_> = state.fleet.iter().map(|bus| json!({
        "id": bus.bus_id, "bus_id": bus.bus_id, "model": bus.model, "capacity": bus.capacity,
        "status": if bus.assigned_route.is_some() {"active"} else {"idle"}, "route": bus.assigned_route,
        "health": bus.health, "fuel_level": bus.fuel_level, "fuel_capacity": bus.fuel_capacity,
    })).collect();
    let stats = json!({
        "routes": state.routes.len(), "stops": state.routes.iter().map(|route| route.stops.len()).sum::<usize>(),
        "buses": state.fleet.len(), "active_buses": state.fleet.iter().filter(|bus| bus.assigned_route.is_some()).count(),
        "money": state.money, "reputation": state.reputation, "day": state.day,
    });
    let data = json!({"company_name": state.company_name, "routes": routes, "fleet": fleet, "stats": stats});
    let result = serde_json::to_vec_pretty(&data)
        .map_err(|error| error.to_string())
        .and_then(|bytes| {
            fs::write(root_dir().join("web_data.json"), bytes).map_err(|error| error.to_string())
        });
    match result {
        Ok(()) => println!("Visualization data exported to web_data.json."),
        Err(error) => println!("Export failed: {error}"),
    }
}

fn view_status(state: &ManagerState) {
    println!(
        "{} | Day {} | £{:.2} | Reputation {:.1}/100 | {} buses | {} routes | Fuel £{:.2}/L",
        state.company_name,
        state.day,
        state.money,
        state.reputation,
        state.fleet.len(),
        state.routes.len(),
        state.fuel_price
    );
    if state.use_running_boards {
        println!("{} running boards available.", list_boards().len());
    }
}

fn board_folder() -> PathBuf {
    root_dir().join("running_boards")
}

fn board_path(name: &str) -> PathBuf {
    board_folder().join(format!("{}.json", safe_name(name)))
}

fn list_boards() -> Vec<String> {
    let Ok(entries) = fs::read_dir(board_folder()) else {
        return Vec::new();
    };
    let mut names: Vec<_> = entries
        .flatten()
        .filter(|entry| entry.path().extension().is_some_and(|ext| ext == "json"))
        .filter_map(|entry| fs::read_to_string(entry.path()).ok())
        .filter_map(|contents| serde_json::from_str::<RunningBoard>(&contents).ok())
        .map(|board| board.name)
        .collect();
    names.sort();
    names
}

fn load_board(name: &str) -> Option<RunningBoard> {
    let contents = fs::read_to_string(board_path(name)).ok()?;
    serde_json::from_str(&contents).ok()
}

fn save_board(board: &RunningBoard) -> bool {
    if fs::create_dir_all(board_folder()).is_err() {
        return false;
    }
    let result = serde_json::to_vec_pretty(board)
        .map_err(|error| error.to_string())
        .and_then(|data| {
            fs::write(board_path(&board.name), data).map_err(|error| error.to_string())
        });
    match result {
        Ok(()) => true,
        Err(error) => {
            println!("Could not save board: {error}");
            false
        }
    }
}

fn board_menu(state: &ManagerState) {
    loop {
        println!("\n--- RUNNING BOARD MANAGEMENT ---\n1) Create board\n2) View boards\n3) Assign bus\n4) Board details\n5) Delete board\n6) Create boards from CSV\n7) Batch create interactively\n8) View activity log\n9) Return");
        match input("> ").as_str() {
            "1" => create_board(state),
            "2" => view_boards(state),
            "3" => assign_board_bus(state),
            "4" => board_details(state),
            "5" => delete_board(),
            "6" => boards_from_csv(),
            "7" => batch_create_boards(state),
            "8" => view_log(),
            "9" => break,
            _ => println!("Invalid option."),
        }
    }
}

fn batch_create_boards(state: &ManagerState) {
    loop {
        create_board(state);
        if !confirm("Create another board? (y/n): ") {
            break;
        }
    }
}

fn create_board(state: &ManagerState) {
    let name = input("Running board name: ");
    if name.is_empty() {
        println!("Name cannot be empty.");
        return;
    }
    if load_board(&name).is_some() && !confirm("Board exists. Overwrite? (y/n): ") {
        return;
    }
    let mut trips = Vec::new();
    loop {
        let route_name = input("Route name (or done): ");
        if route_name.eq_ignore_ascii_case("done") {
            break;
        }
        if route_name.is_empty() {
            continue;
        }
        if !state.routes.iter().any(|route| route.name == route_name)
            && !confirm("Route not found. Add anyway? (y/n): ")
        {
            continue;
        }
        let destination = input("Destination: ");
        if destination.is_empty() {
            continue;
        }
        let departure_time = loop {
            let value = input("Departure time (HH:MM): ");
            if valid_time(&value) {
                break value;
            }
            println!("Enter a valid 24-hour time.");
        };
        trips.push(Trip {
            route_name,
            destination,
            departure_time,
        });
    }
    if trips.is_empty() {
        println!("No trips entered.");
        return;
    }
    let board = RunningBoard {
        name: name.clone(),
        trips,
        assigned_bus_id: None,
    };
    if save_board(&board) {
        log_action(&format!("Created board: {name}"));
        println!("Board saved.");
    }
}

fn valid_time(value: &str) -> bool {
    let Some((hours, minutes)) = value.split_once(':') else {
        return false;
    };
    match (hours.parse::<u32>(), minutes.parse::<u32>()) {
        (Ok(hours), Ok(minutes)) => {
            hours < 24
                && minutes < 60
                && hours.to_string().len() <= 2
                && minutes.to_string().len() <= 2
        }
        _ => false,
    }
}

fn view_boards(state: &ManagerState) {
    let boards = list_boards();
    if boards.is_empty() {
        println!("No running boards.");
        return;
    }
    for name in boards {
        if let Some(board) = load_board(&name) {
            let bus = board
                .assigned_bus_id
                .and_then(|id| state.fleet.iter().find(|bus| bus.bus_id == id))
                .map(|bus| format!("Bus {} ({})", bus.bus_id, bus.model))
                .unwrap_or_else(|| "Not assigned".to_owned());
            println!("{} - {} trips - {}", board.name, board.trips.len(), bus);
        }
    }
}

fn board_details(state: &ManagerState) {
    let name = input("Board name: ");
    let Some(board) = load_board(&name) else {
        println!("Board not found.");
        return;
    };
    println!("{} ({} trips)", board.name, board.trips.len());
    for trip in &board.trips {
        println!(
            "{} - {} to {}{}",
            trip.departure_time,
            trip.route_name,
            trip.destination,
            if state
                .routes
                .iter()
                .any(|route| route.name == trip.route_name)
            {
                ""
            } else {
                " (route missing)"
            }
        );
    }
    let total: i64 = board
        .trips
        .iter()
        .filter_map(|trip| {
            state
                .routes
                .iter()
                .find(|route| route.name == trip.route_name)
        })
        .map(route_minutes)
        .sum();
    println!("Estimated travel time: {total} minutes");
}

fn assign_board_bus(state: &ManagerState) {
    if state.fleet.is_empty() {
        println!("Buy a bus first.");
        return;
    }
    let name = input("Board name: ");
    let Some(mut board) = load_board(&name) else {
        println!("Board not found.");
        return;
    };
    for bus in &state.fleet {
        println!(
            "[{}] {} ({})",
            bus.bus_id,
            bus.model,
            bus.fleet_number.as_deref().unwrap_or("N/A")
        );
    }
    let Some(id) = number("Bus ID (0 unassigns): ") else {
        println!("Invalid ID.");
        return;
    };
    if id == 0 {
        board.assigned_bus_id = None;
    } else if state.fleet.iter().any(|bus| bus.bus_id == id as u64) {
        board.assigned_bus_id = Some(id as u64);
    } else {
        println!("Bus not found.");
        return;
    }
    let board_name = board.name.clone();
    if save_board(&board) {
        log_action(&format!("Updated assignment for board: {board_name}"));
        println!("Assignment saved.");
    }
}

fn delete_board() {
    let name = input("Board name to delete: ");
    if !confirm("Delete this board? (y/n): ") {
        return;
    }
    match fs::remove_file(board_path(&name)) {
        Ok(()) => {
            log_action(&format!("Deleted board: {name}"));
            println!("Board deleted.");
        }
        Err(error) => println!("Could not delete board: {error}"),
    }
}

fn boards_from_csv() {
    let filename = input("CSV filename in game folder: ");
    let path = root_dir().join(filename);
    let mut reader = match csv::Reader::from_path(path) {
        Ok(reader) => reader,
        Err(error) => {
            println!("Could not read CSV: {error}");
            return;
        }
    };
    let headers = match reader.headers() {
        Ok(headers) => headers.clone(),
        Err(error) => {
            println!("Invalid CSV: {error}");
            return;
        }
    };
    let find = |name: &str| headers.iter().position(|header| header == name);
    let (Some(board_col), Some(route_col), Some(destination_col), Some(time_col)) = (
        find("board_name"),
        find("route_name"),
        find("destination"),
        find("departure_time"),
    ) else {
        println!("CSV needs board_name, route_name, destination, departure_time columns.");
        return;
    };
    let mut grouped: BTreeMap<String, Vec<Trip>> = BTreeMap::new();
    for record in reader.records().flatten() {
        let board_name = record.get(board_col).unwrap_or("").trim();
        let route_name = record.get(route_col).unwrap_or("").trim();
        let destination = record.get(destination_col).unwrap_or("").trim();
        let departure_time = record.get(time_col).unwrap_or("").trim();
        if board_name.is_empty()
            || route_name.is_empty()
            || destination.is_empty()
            || !valid_time(departure_time)
        {
            continue;
        }
        grouped
            .entry(board_name.to_owned())
            .or_default()
            .push(Trip {
                route_name: route_name.to_owned(),
                destination: destination.to_owned(),
                departure_time: departure_time.to_owned(),
            });
    }
    let mut saved = 0;
    for (name, trips) in grouped {
        if save_board(&RunningBoard {
            name,
            trips,
            assigned_bus_id: None,
        }) {
            saved += 1;
        }
    }
    println!("Created {saved} running boards from CSV.");
}

fn view_log() {
    match fs::read_to_string(board_folder().join("activity.log")) {
        Ok(contents) if !contents.is_empty() => print!("{contents}"),
        _ => println!("No activity logged yet."),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn blank_fleet_number_uses_first_available_number() {
        let mut state = ManagerState::new("Test".to_owned());
        state.fleet.push(Bus {
            bus_id: 1,
            model: "Bus".to_owned(),
            capacity: 40,
            fuel_capacity: 100.0,
            fuel_level: 100.0,
            fuel_efficiency: 0.25,
            assigned_route: None,
            health: 100,
            purchase_price: 0.0,
            fleet_number: Some("1".to_owned()),
            dlc_source: None,
            livery: "Standard".to_owned(),
        });
        assert_eq!(assign_fleet_number(&state, ""), Some("2".to_owned()));
        assert_eq!(
            assign_fleet_number(&state, "FL-002"),
            Some("FL-002".to_owned())
        );
        assert_eq!(assign_fleet_number(&state, "1"), None);
    }

    #[test]
    fn validates_board_departure_times() {
        assert!(valid_time("09:38"));
        assert!(!valid_time("24:00"));
        assert!(!valid_time("09:60"));
        assert!(!valid_time("not-a-time"));
    }
}
