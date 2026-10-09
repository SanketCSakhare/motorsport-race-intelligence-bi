import sqlite3
from pathlib import Path


DB = Path(__file__).resolve().parents[1] / "data" / "motorsport_bi.sqlite"


def test_star_schema_grain_and_links():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM fact_result").fetchone()[0]
        distinct = conn.execute("SELECT COUNT(*) FROM (SELECT race_id,driver_id FROM fact_result GROUP BY 1,2)").fetchone()[0]
        assert rows == distinct and rows > 0
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_silverstone_and_metric_bounds():
    with sqlite3.connect(DB) as conn:
        n = conn.execute("SELECT COUNT(*) FROM v_race_performance WHERE circuit_id='silverstone'").fetchone()[0]
        assert n > 0
        assert conn.execute("SELECT COUNT(*) FROM v_race_performance WHERE podium=1 AND (finish_position<1 OR finish_position>3)").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM v_race_performance WHERE retired=1 AND retirement_reason IS NULL").fetchone()[0] == 0

