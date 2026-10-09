# Power BI report specification

Import `data/csv/*.csv` into Power BI Desktop. Use the relationships and DAX in `measures.dax`.

## Page 1 — Race overview

- Slicers: `dim_race[season]`, `dim_circuit[circuit_name]`, `dim_constructor[constructor_name]`.
- Cards: Grand Prix Races, Race Starts, Race Points, Podiums, Retirement Rate.
- Bar chart: constructor by Race Points; tooltip Wins, Podiums, Race Starts.
- Line chart: season by Retirement Rate.
- Table: race date, race name, driver, constructor, grid, finish, points, retirement reason.

## Page 2 — Silverstone focus

- Page filter: `dim_circuit[circuit_id] = "silverstone"`.
- Trends by season: results, retirement rate, points and podiums.
- Scatter: grid vs finish, coloured by constructor; remove blank positions.
- Drillthrough from constructor to driver results.

## Performance and accessibility

Use import mode for this small mart; use single-direction relationships and hide surrogate keys from report view. Sort seasons numerically. Put units and denominator definitions in tooltips. Test keyboard navigation, colour contrast and alt text before publication. Save as a `.pbip` from Desktop for Git diffing. The repository provides the model-ready CSVs and DAX; it does not claim a tested `.pbip` or Fabric deployment.

