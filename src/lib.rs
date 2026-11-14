use serde::{de, Deserialize, Deserializer, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Serialize)]
pub struct Stop {
    pub name: String,
    pub minutes_from_prev: i64,
}

impl<'de> Deserialize<'de> for Stop {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = Value::deserialize(deserializer)?;
        let name = value
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| de::Error::missing_field("name"))?
            .to_owned();
        let minutes_from_prev = if let Some(minutes) = value.get("minutes_from_prev") {
            minutes
                .as_i64()
                .ok_or_else(|| de::Error::custom("minutes_from_prev must be an integer"))?
        } else {
            (value
                .get("distance_from_prev_km")
                .and_then(Value::as_f64)
                .unwrap_or(0.0)
                * 2.0) as i64
        };
        Ok(Self {
            name,
            minutes_from_prev,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Route {
    pub name: String,
    #[serde(default)]
    pub stops: Vec<Stop>,
    pub base_schedule_minutes: i64,
    pub current_schedule_minutes: i64,
    #[serde(default)]
    pub assigned_bus_id: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Bus {
    pub bus_id: u64,
    pub model: String,
    pub capacity: u32,
    pub fuel_capacity: f64,
    pub fuel_level: f64,
    pub fuel_efficiency: f64,
    #[serde(default)]
    pub assigned_route: Option<String>,
    #[serde(default = "default_health")]
    pub health: u32,
    #[serde(default)]
    pub purchase_price: f64,
    #[serde(default)]
    pub fleet_number: Option<String>,
    #[serde(default)]
    pub dlc_source: Option<String>,
    #[serde(default = "default_livery")]
    pub livery: String,
}

fn default_health() -> u32 {
    100
}

fn default_livery() -> String {
    "Standard".to_owned()
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManagerState {
    #[serde(default = "legacy_save_version")]
    pub save_version: u32,
    pub company_name: String,
    #[serde(default)]
    pub routes: Vec<Route>,
    #[serde(default)]
    pub fleet: Vec<Bus>,
    #[serde(default = "default_money")]
    pub money: f64,
    #[serde(default = "default_reputation")]
    pub reputation: f64,
    #[serde(default = "default_day")]
    pub day: u64,
    #[serde(default = "default_next_bus_id")]
    pub next_bus_id: u64,
    #[serde(default)]
    pub use_running_boards: bool,
    #[serde(default = "default_fuel_price")]
    pub fuel_price: f64,
}

fn default_money() -> f64 {
    2_500_000.0
}
fn default_reputation() -> f64 {
    50.0
}
fn default_day() -> u64 {
    1
}
fn default_next_bus_id() -> u64 {
    1
}
fn default_fuel_price() -> f64 {
    1.60
}
fn current_save_version() -> u32 {
    2
}
fn legacy_save_version() -> u32 {
    1
}

impl ManagerState {
    pub fn new(company_name: String) -> Self {
        Self {
            save_version: current_save_version(),
            company_name,
            routes: Vec::new(),
            fleet: Vec::new(),
            money: default_money(),
            reputation: default_reputation(),
            day: default_day(),
            next_bus_id: default_next_bus_id(),
            use_running_boards: false,
            fuel_price: default_fuel_price(),
        }
    }
}

pub mod game;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trip {
    pub route_name: String,
    pub destination: String,
    pub departure_time: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunningBoard {
    pub name: String,
    #[serde(default)]
    pub trips: Vec<Trip>,
    #[serde(default)]
    pub assigned_bus_id: Option<u64>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_legacy_distance_stops_as_minutes() {
        let stop: Stop =
            serde_json::from_str(r#"{"name":"Market","distance_from_prev_km":3.5}"#).unwrap();
        assert_eq!(stop.minutes_from_prev, 7);
        assert_eq!(serde_json::to_value(stop).unwrap()["minutes_from_prev"], 7);
    }

    #[test]
    fn loads_saves_with_missing_optional_fields() {
        let state: ManagerState = serde_json::from_str(r#"{
            "company_name":"Example",
            "routes":[],
            "fleet":[{"bus_id":1,"model":"Bus","capacity":40,"fuel_capacity":100.0,"fuel_level":90.0,"fuel_efficiency":0.25}],
            "money":1000.0,"reputation":50.0,"day":2
        }"#).unwrap();
        assert_eq!(state.next_bus_id, 1);
        assert_eq!(state.fleet[0].livery, "Standard");
        assert_eq!(state.save_version, 1);
        assert_eq!(ManagerState::new("New".to_owned()).save_version, 2);
    }
}
