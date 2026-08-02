# ADR 0001: Initial Data Sources

## Status

Approved

## Energy source

IESO Hourly Demand data.

Initial fields will include:

- Date and hour
- Ontario demand
- Market demand, when available

## Weather source

Environment and Climate Change Canada hourly weather observations.

The first version will use one Toronto-area weather station.

Initial fields will include:

- Observation timestamp
- Temperature
- Relative humidity
- Wind speed
- Precipitation, when available

## Reason

Both are official Canadian public data sources. Starting with one energy dataset and one weather station keeps the first pipeline small enough to understand and test.

## Future changes

Additional IESO datasets and Ontario weather stations may be added after the first pipeline is reliable.