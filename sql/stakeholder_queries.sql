-- Q1. Which constructors gained the most positions at Silverstone since 2015?
SELECT constructor_name, COUNT(*) AS driver_results,
       ROUND(AVG(positions_gained), 2) AS avg_positions_gained,
       SUM(points) AS points
FROM v_race_performance
WHERE circuit_id = 'silverstone' AND positions_gained IS NOT NULL
GROUP BY constructor_name
ORDER BY avg_positions_gained DESC;

-- Q2. Which recent seasons had the highest recorded retirement rate?
SELECT season, COUNT(*) AS driver_results, SUM(retired) AS retirements,
       ROUND(100.0 * SUM(retired) / COUNT(*), 1) AS retirement_pct
FROM v_race_performance
GROUP BY season
ORDER BY retirement_pct DESC;

-- Q3. Which drivers combine podiums with reliability at Silverstone?
SELECT driver_name, COUNT(*) AS starts, SUM(podium) AS podiums,
       SUM(retired) AS retirements, ROUND(SUM(points), 1) AS points
FROM v_race_performance
WHERE circuit_id = 'silverstone'
GROUP BY driver_name
HAVING starts >= 3
ORDER BY podiums DESC, points DESC;

