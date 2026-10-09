CREATE TABLE dim_circuit (
  circuit_id TEXT PRIMARY KEY, circuit_name TEXT NOT NULL, country_id TEXT
);
CREATE TABLE dim_race (
  race_id INTEGER PRIMARY KEY, season INTEGER NOT NULL, round INTEGER NOT NULL,
  race_date TEXT NOT NULL, race_name TEXT NOT NULL,
  circuit_id TEXT NOT NULL REFERENCES dim_circuit(circuit_id)
);
CREATE TABLE dim_driver (
  driver_id TEXT PRIMARY KEY, driver_name TEXT NOT NULL, nationality_country_id TEXT
);
CREATE TABLE dim_constructor (
  constructor_id TEXT PRIMARY KEY, constructor_name TEXT NOT NULL, country_id TEXT
);
CREATE TABLE fact_result (
  race_id INTEGER NOT NULL REFERENCES dim_race(race_id),
  driver_id TEXT NOT NULL REFERENCES dim_driver(driver_id),
  constructor_id TEXT NOT NULL REFERENCES dim_constructor(constructor_id),
  finish_position INTEGER, grid_position INTEGER, points REAL NOT NULL,
  laps_completed INTEGER, retirement_reason TEXT, pit_stops INTEGER,
  fastest_lap INTEGER,
  PRIMARY KEY (race_id, driver_id)
);
CREATE INDEX idx_race_season ON dim_race(season);
CREATE INDEX idx_race_circuit ON dim_race(circuit_id);
CREATE INDEX idx_result_constructor ON fact_result(constructor_id);

