CREATE VIEW v_race_performance AS
SELECT r.season,r.round,r.race_date,r.race_name,c.circuit_name,c.circuit_id,
       d.driver_name,t.constructor_name,f.driver_id,f.constructor_id,
       f.finish_position,f.grid_position,f.points,f.laps_completed,
       f.retirement_reason,f.pit_stops,f.fastest_lap,
       CASE WHEN f.finish_position=1 THEN 1 ELSE 0 END AS win,
       CASE WHEN f.finish_position BETWEEN 1 AND 3 THEN 1 ELSE 0 END AS podium,
       CASE WHEN f.retirement_reason IS NOT NULL THEN 1 ELSE 0 END AS retired,
       CASE WHEN f.grid_position IS NOT NULL AND f.finish_position IS NOT NULL
            THEN f.grid_position-f.finish_position END AS positions_gained
FROM fact_result f
JOIN dim_race r ON r.race_id=f.race_id
JOIN dim_circuit c ON c.circuit_id=r.circuit_id
JOIN dim_driver d ON d.driver_id=f.driver_id
JOIN dim_constructor t ON t.constructor_id=f.constructor_id;

