"""Build a reproducible Formula 1 race-results star schema from F1DB."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RELEASE = "v2026.16.1"
SOURCE_URL = f"https://github.com/f1db/f1db/releases/download/{RELEASE}/f1db-sqlite.zip"
ARCHIVE_SHA256 = "1cf00790b2e334d71a69da4b9b0738feef1e3a15262e661389bf803dd97a0f4d"


def source_database() -> Path:
    raw = DATA / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / "f1db-sqlite.zip"
    database = raw / "f1db.db"
    if not archive.exists():
        print(f"Downloading {SOURCE_URL}")
        urllib.request.urlretrieve(SOURCE_URL, archive)
    actual_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual_hash != ARCHIVE_SHA256:
        raise ValueError(f"F1DB archive checksum mismatch: {actual_hash}")
    if not database.exists():
        with zipfile.ZipFile(archive) as z:
            z.extract("f1db.db", raw)
    return database


def export_csv(conn: sqlite3.Connection, table: str, destination: Path) -> None:
    cursor = conn.execute(f"SELECT * FROM {table}")
    with destination.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([d[0] for d in cursor.description])
        writer.writerows(cursor)


def check(conn: sqlite3.Connection) -> dict[str, int]:
    checks = {
        "races": "SELECT COUNT(*) FROM dim_race",
        "results": "SELECT COUNT(*) FROM fact_result",
        "drivers": "SELECT COUNT(*) FROM dim_driver",
        "constructors": "SELECT COUNT(*) FROM dim_constructor",
        "circuits": "SELECT COUNT(*) FROM dim_circuit",
        "duplicate_result_keys": "SELECT COUNT(*) FROM (SELECT race_id,driver_id,COUNT(*) n FROM fact_result GROUP BY 1,2 HAVING n>1)",
        "orphan_results": "SELECT COUNT(*) FROM fact_result f LEFT JOIN dim_race r ON f.race_id=r.race_id LEFT JOIN dim_driver d ON f.driver_id=d.driver_id LEFT JOIN dim_constructor c ON f.constructor_id=c.constructor_id WHERE r.race_id IS NULL OR d.driver_id IS NULL OR c.constructor_id IS NULL",
        "invalid_points": "SELECT COUNT(*) FROM fact_result WHERE points<0 OR points IS NULL",
        "future_races": "SELECT COUNT(*) FROM dim_race WHERE race_date>date('now')",
    }
    result = {name: conn.execute(sql).fetchone()[0] for name, sql in checks.items()}
    for name in ("duplicate_result_keys", "orphan_results", "invalid_points", "future_races"):
        if result[name]:
            raise ValueError(f"Data quality failure: {name}={result[name]}")
    if result["races"] == 0 or result["results"] == 0:
        raise ValueError("Empty mart")
    return result


def build(source: Path, start_year: int, end_year: int, pinned_release: bool = True) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as src:
        src.row_factory = sqlite3.Row
        src.execute("PRAGMA query_only=ON")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        mart_path = DATA / "motorsport_bi.sqlite"
        if mart_path.exists():
            mart_path.unlink()
        with sqlite3.connect(mart_path) as mart:
            mart.execute("PRAGMA foreign_keys=ON")
            mart.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
            races = src.execute("""SELECT r.id,r.year,r.round,r.date,r.official_name,r.circuit_id,
                c.name AS circuit_name,c.country_id
                FROM race r JOIN circuit c ON c.id=r.circuit_id
                WHERE r.year BETWEEN ? AND ? AND r.date <= date('now')
                ORDER BY r.date,r.round""", (start_year, end_year)).fetchall()
            race_ids = {r[0] for r in races}
            if not race_ids:
                raise ValueError("No completed races in selected years")
            mart.executemany("INSERT INTO dim_circuit VALUES (?,?,?)", sorted({(r[5],r[6],r[7]) for r in races}))
            mart.executemany("INSERT INTO dim_race VALUES (?,?,?,?,?,?)", [(r[0],r[1],r[2],r[3],r[4],r[5]) for r in races])
            # Only race results: practice, qualifying, sprint and pit-stop records have a different grain.
            results = src.execute("""SELECT race_id,driver_id,constructor_id,position_number,
                race_grid_position_number,COALESCE(race_points,0),race_laps,
                race_reason_retired,COALESCE(race_pit_stops,0),race_fastest_lap
                FROM race_data WHERE type='RACE_RESULT'""").fetchall()
            results = [r for r in results if r[0] in race_ids and r[1] and r[2]]
            driver_ids = {r[1] for r in results}
            constructor_ids = {r[2] for r in results}
            drivers = src.execute("SELECT id,full_name,nationality_country_id FROM driver").fetchall()
            constructors = src.execute("SELECT id,name,country_id FROM constructor").fetchall()
            mart.executemany("INSERT INTO dim_driver VALUES (?,?,?)", [tuple(r) for r in drivers if r[0] in driver_ids])
            mart.executemany("INSERT INTO dim_constructor VALUES (?,?,?)", [tuple(r) for r in constructors if r[0] in constructor_ids])
            mart.executemany("INSERT INTO fact_result VALUES (?,?,?,?,?,?,?,?,?,?)", [tuple(r) for r in results])
            mart.executescript((ROOT / "sql" / "views.sql").read_text(encoding="utf-8"))
            counts = check(mart)
            csv_dir = DATA / "csv"
            csv_dir.mkdir(exist_ok=True)
            for table in ("dim_circuit", "dim_race", "dim_driver", "dim_constructor", "fact_result"):
                export_csv(mart, table, csv_dir / f"{table}.csv")
    manifest = {"source": SOURCE_URL if pinned_release else str(source.resolve()),
                "source_version": RELEASE if pinned_release else "user-provided",
                "archive_sha256": ARCHIVE_SHA256 if pinned_release else None,
                "source_sha256": source_hash,
                "years": [start_year, end_year], "built_at_utc": datetime.now(timezone.utc).isoformat(),
                "quality_checks": counts}
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="Local F1DB SQLite file; otherwise download pinned release")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2025)
    args = parser.parse_args()
    print(json.dumps(build(args.source or source_database(), args.start_year, args.end_year,
                           pinned_release=args.source is None), indent=2))

