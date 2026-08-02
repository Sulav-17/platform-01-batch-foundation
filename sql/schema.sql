CREATE TABLE IF NOT EXISTS ingestion_runs (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    source_file TEXT,
    content_hash CHAR(64),
    rows_received INTEGER NOT NULL DEFAULT 0 CHECK (rows_received >= 0),
    rows_loaded INTEGER NOT NULL DEFAULT 0 CHECK (rows_loaded >= 0),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS energy_demand_hourly (
    demand_date DATE NOT NULL,
    hour_ending SMALLINT NOT NULL CHECK (hour_ending BETWEEN 1 AND 24),
    market_demand_mw NUMERIC(12, 2) NOT NULL CHECK (market_demand_mw > 0),
    ontario_demand_mw NUMERIC(12, 2) NOT NULL CHECK (ontario_demand_mw > 0),
    source_file TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (demand_date, hour_ending)
);

CREATE TABLE IF NOT EXISTS weather_hourly (
    station_id TEXT NOT NULL,
    station_name TEXT NOT NULL,
    utc_timestamp TIMESTAMPTZ NOT NULL,
    local_timestamp TIMESTAMP NOT NULL,
    temperature_c NUMERIC(8, 2),
    relative_humidity_pct NUMERIC(5, 2)
        CHECK (relative_humidity_pct BETWEEN 0 AND 100),
    wind_speed_kmh NUMERIC(8, 2)
        CHECK (wind_speed_kmh >= 0),
    precipitation_mm NUMERIC(8, 2)
        CHECK (precipitation_mm >= 0),
    weather_description TEXT,
    source_file TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (station_id, utc_timestamp)
);
