#!/usr/bin/env python3
"""Generates listings.db for the agent-building exercise.

Deterministic — running it again produces identical data. Stdlib only.
Do not edit this script; treat the data as what production actually holds.
"""
import os
import random
import sqlite3
from datetime import datetime, timedelta

random.seed(17)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")

SCHEMA = """
CREATE TABLE buildings (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip TEXT NOT NULL
);
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    building_id INTEGER NOT NULL REFERENCES buildings(id),
    unit_number TEXT NOT NULL,
    beds INTEGER NOT NULL,
    baths REAL NOT NULL,
    rent INTEGER,              -- NULL = price not on file (this matters!)
    available_from TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL REFERENCES units(id),
    tour_at TEXT NOT NULL,
    client_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

CITIES = [("Chicago", "IL", "606"), ("Dallas", "TX", "752"),
          ("Austin", "TX", "787"), ("Houston", "TX", "770")]
NAME_A = ["Maple", "Lakeview", "Halsted", "Greenville", "Brazos", "Heights",
          "Union", "Parkside", "Riverline", "Stonewall", "Kessler", "Monarch"]
NAME_B = ["Commons", "Lofts", "Residences", "Flats", "Court", "Place",
          "Apartments", "Station"]
STREETS = ["Main St", "Clark St", "Lake Ave", "Oak Blvd", "Elm St",
           "Madison Ave", "State St", "Lamar Blvd", "Fannin Dr"]

now = datetime.now()

if os.path.exists(DB):
    os.remove(DB)
conn = sqlite3.connect(DB)
conn.executescript(SCHEMA)

unit_id = 100
null_rent = inactive = 0
for b_id in range(1, 41):
    city, state, zip3 = random.choice(CITIES)
    name = f"{random.choice(NAME_A)} {random.choice(NAME_B)}"
    addr = f"{random.randint(100, 4999)} {random.choice(STREETS)}"
    conn.execute(
        "INSERT INTO buildings (id, name, address, city, state, zip) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (b_id, name, addr, city, state, zip3 + f"{random.randint(1, 99):02d}"),
    )
    for _ in range(random.randint(3, 8)):
        unit_id += 1
        beds = random.choice([0, 1, 1, 2, 2, 2, 3])
        baths = random.choice([1.0, 1.0, 1.5, 2.0, 2.5])
        rent = None if random.random() < 0.25 else 900 + 25 * random.randint(0, 100)
        active = 0 if random.random() < 0.10 else 1
        avail = (now + timedelta(days=random.randint(-20, 45))).date().isoformat()
        conn.execute(
            "INSERT INTO units (id, building_id, unit_number, beds, baths, rent, "
            "available_from, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (unit_id, b_id, f"{random.randint(1, 29)}{random.choice('ABCDEF')}",
             beds, baths, rent, avail, active),
        )
        null_rent += rent is None
        inactive += active == 0

conn.commit()
n_units = conn.execute("SELECT COUNT(*) FROM units").fetchone()[0]
conn.close()

print(f"Built {os.path.basename(DB)}: 40 buildings, {n_units} units "
      f"({null_rent} with no rent on file, {inactive} inactive). tours table is empty.")
