"""
scraper.py - Fetches confirmed exoplanet data from the NASA Exoplanet Archive.

Uses the Archive's free TAP (Table Access Protocol) service to download the
composite planet parameters table (pscomppars).  This table contains one row
per confirmed exoplanet using the best available parameters from all published
studies - making it the most reliable single source for bulk analysis.

The scraper saves data as a timestamped CSV so we have a historical record of
each yearly pull.  It also writes a 'latest.csv' that the rest of the project
always reads from, so other modules never need to care about dates.

NASA Exoplanet Archive TAP docs:
https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html

Author: Rory
"""

import csv
import os
import urllib.request
import urllib.parse
from datetime import datetime


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Base URL for the NASA Exoplanet Archive TAP synchronous endpoint.
# TAP lets us send SQL-like queries and get back CSV, JSON, etc.
TAP_BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# The table we query.  'pscomppars' = Planetary Systems Composite Parameters.
# NASA picks the best value for each parameter from all published papers,
# so we get one clean row per planet rather than dozens of conflicting entries.
TABLE = "pscomppars"

# The columns we actually need.  Pulling every column (~200) is slow and mostly
# useless for habitability work.  This list covers the key physical properties.
COLUMNS = [
    "pl_name",          # Planet name, e.g. "Kepler-442 b"
    "hostname",         # Host star name
    "sy_dist",          # Distance from Earth in parsecs
    "pl_rade",          # Planet radius in Earth radii
    "pl_masse",         # Planet mass in Earth masses
    "pl_orbper",        # Orbital period in days
    "pl_orbsmax",       # Semi-major axis in AU (distance from its star)
    "pl_eqt",           # Equilibrium temperature in Kelvin
    "st_teff",          # Stellar effective temperature in Kelvin
    "st_lum",           # Stellar luminosity (log, solar units)
    "st_rad",           # Stellar radius in solar radii
    "st_mass",          # Stellar mass in solar masses
    "st_age",           # Stellar age in gigayears
    "st_spectype",      # Stellar spectral type e.g. "G2V"
    "discoverymethod",  # How the planet was found, e.g. "Transit"
    "disc_year",        # Year of discovery
    "pl_controv_flag",  # 1 if the planet's existence is disputed
]

# Directory where data files are saved, relative to this script.
DATA_DIR = "data"

# The file that always points to the most recent download.
LATEST_FILENAME = "latest.csv"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def build_query_url(columns: list[str], table: str) -> str:
    """Build the full TAP query URL for the given columns and table.

    Constructs a SELECT query asking for our chosen columns from the given
    table.  The query is URL-encoded so it can be sent as a GET request.

    :param columns: List of column names to retrieve.
    :param table: The TAP table name to query.
    :return: A fully-formed URL string ready to pass to urllib.
    """
    # Join the column names into a comma-separated string for the SELECT clause
    column_string = ", ".join(columns)

    # Build the ADQL (Astronomical Data Query Language) query.
    # WHERE pl_controv_flag = 0 excludes disputed planets so our data is clean.
    query = f"SELECT {column_string} FROM {table} WHERE pl_controv_flag = 0"

    # urllib.parse.urlencode turns a dict into a URL query string, and
    # quote_via=urllib.parse.quote ensures spaces become %20 not +, which
    # the TAP service requires.
    params = urllib.parse.urlencode(
        {"query": query, "format": "csv"},
        quote_via=urllib.parse.quote
    )

    # Combine the base URL with the encoded parameters
    return f"{TAP_BASE_URL}?{params}"


def fetch_data(url: str) -> bytes:
    """Download the content at the given URL and return it as raw bytes.

    Uses Python's built-in urllib so there are no external dependencies.
    Sets a browser-like User-Agent header because some servers reject the
    default Python urllib agent.

    :param url: The URL to fetch.
    :return: The response body as bytes.
    :raises urllib.error.URLError: If the request fails.
    """
    print(f"  Contacting NASA Exoplanet Archive...")

    # Create a Request object so we can set custom headers
    req = urllib.request.Request(url)

    # Set a descriptive User-Agent so NASA knows what's hitting their API
    req.add_header("User-Agent", "ExoHabitability-Scraper/1.0")

    # urlopen sends the request and returns a response object.
    # We use it as a context manager so the connection is closed automatically.
    with urllib.request.urlopen(req, timeout=120) as response:
        # Read all response bytes into memory
        data = response.read()

    return data


def parse_csv_bytes(raw_bytes: bytes) -> list[dict]:
    """Parse raw CSV bytes into a list of dictionaries.

    Decodes the bytes as UTF-8 and splits into lines, then uses csv.DictReader
    to parse so each row becomes a dict keyed by column name.

    :param raw_bytes: Raw bytes from the HTTP response.
    :return: A list of dicts, one per planet row.
    """
    # Decode bytes to a string using UTF-8
    text = raw_bytes.decode("utf-8")

    # Split on newlines so csv can work line by line.
    # splitlines() handles \r\n and \n uniformly.
    lines = text.splitlines()

    # DictReader uses the first row as the header and maps each subsequent
    # row's values to those header keys automatically.
    reader = csv.DictReader(lines)

    # Convert the reader iterator to a plain list so we can work with it freely
    return list(reader)


def save_csv(rows: list[dict], filepath: str) -> None:
    """Write a list of dicts to a CSV file at the given path.

    Creates the directory if it doesn't exist yet.  Uses the keys of the
    first row as the CSV header.

    :param rows: List of dicts to write.  All dicts must have the same keys.
    :param filepath: Full path (including filename) to write to.
    """
    if not rows:
        # Nothing to write - bail out early rather than creating an empty file
        print("  Warning: no rows to save.")
        return

    # Create the directory tree if it doesn't exist yet (like mkdir -p)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Open the file for writing in UTF-8.  newline='' is required by the
    # csv module on Windows to prevent it adding extra blank lines.
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        # DictWriter needs the field names upfront so it can write the header
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())

        # writeheader() writes the column names as the first row
        writer.writeheader()

        # writerows() writes all the data rows in one go
        writer.writerows(rows)


def run_scrape() -> list[dict]:
    """Run a full scrape: fetch, parse, save timestamped + latest files.

    This is the main entry point for the scraper.  It orchestrates all the
    steps in order and prints progress so you can see what's happening.

    :return: The list of planet dicts that was saved.
    """
    print("=== NASA Exoplanet Archive Scraper ===")
    print(f"  Table  : {TABLE}")
    print(f"  Columns: {len(COLUMNS)}")

    # Step 1: Build the query URL from our column list and table name
    url = build_query_url(COLUMNS, TABLE)

    # Step 2: Download the data from NASA
    raw = fetch_data(url)
    print(f"  Downloaded {len(raw):,} bytes")

    # Step 3: Parse the CSV bytes into a list of dicts
    planets = parse_csv_bytes(raw)
    print(f"  Parsed {len(planets):,} confirmed exoplanets")

    # Step 4: Build a timestamped filename so we never overwrite old data.
    # strftime formats the current date as YYYY-MM-DD e.g. "2026-05-11"
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    timestamped_path = os.path.join(DATA_DIR, f"exoplanets_{date_stamp}.csv")

    # Step 5: Save the timestamped archive copy
    save_csv(planets, timestamped_path)
    print(f"  Saved archive copy -> {timestamped_path}")

    # Step 6: Also save as 'latest.csv' so other modules always know where
    # to look without caring about dates
    latest_path = os.path.join(DATA_DIR, LATEST_FILENAME)
    save_csv(planets, latest_path)
    print(f"  Saved latest copy  -> {latest_path}")

    print("=== Scrape complete ===")

    # Return the data so callers can use it immediately if they want
    return planets


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # When run directly (python scraper.py), just do a scrape.
    # GitHub Actions will call this once a year via cron.
    planets = run_scrape()

    # Print a quick preview of the first three planets as a sanity check
    print("\nSample rows:")
    for planet in planets[:3]:
        print(f"  {planet['pl_name']:30s}  radius={planet['pl_rade']} Re  "
              f"temp={planet['pl_eqt']} K  dist={planet['sy_dist']} pc")
