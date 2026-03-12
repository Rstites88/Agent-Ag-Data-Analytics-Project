#!/usr/bin/env python3
"""Import field boundaries from a GeoJSON file and join with NRCS soil data from CSV."""

import csv
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_FIELDS_GEOJSON = Path("data") / "fields_EPSG4326.geojson"
DEFAULT_SOIL_CSV = Path("data") / "soil_EPSG4326.csv"
DEFAULT_OUTPUT = Path("data") / "fields_with_soil.geojson"

# Required columns for a minimal NRCS soil CSV
_REQUIRED_SOIL_COLUMNS = {"field_id", "soil_type", "ph", "organic_matter"}


def load_field_boundaries(geojson_path: Path) -> dict:
    """
    Load field boundaries from a GeoJSON FeatureCollection file.

    Args:
        geojson_path: Path to the GeoJSON file.

    Returns:
        Parsed GeoJSON dict with a ``features`` list.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid GeoJSON FeatureCollection.
    """
    geojson_path = Path(geojson_path)
    if not geojson_path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

    with open(geojson_path) as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            f"Expected GeoJSON FeatureCollection, got type='{data.get('type')}'"
        )

    features = data.get("features", [])
    logger.info(f"Loaded {len(features)} field boundaries from {geojson_path}")
    return data


def load_nrcs_soil_data(soil_csv_path: Path) -> dict[int, dict]:
    """
    Load NRCS soil survey data from a CSV file.

    Accepts both the minimal four-column format and the richer SSURGO format
    produced by ``scripts/download_soil.py``.  Required columns:
    ``field_id``, ``soil_type``, ``ph``, ``organic_matter``.

    Args:
        soil_csv_path: Path to the soil CSV file.

    Returns:
        Dict mapping ``field_id`` (int) to a soil attribute dict.

    Raises:
        FileNotFoundError: If the CSV does not exist.
        ValueError: If required columns are missing.
    """
    soil_csv_path = Path(soil_csv_path)
    if not soil_csv_path.exists():
        raise FileNotFoundError(f"Soil CSV file not found: {soil_csv_path}")

    soil_by_field: dict[int, dict] = {}

    with open(soil_csv_path, newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"Empty CSV file: {soil_csv_path}")

        missing = _REQUIRED_SOIL_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"Missing required columns in {soil_csv_path}: {missing}"
            )

        for row_num, row in enumerate(reader, start=2):
            try:
                fid = int(row["field_id"])
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Non-integer field_id in row {row_num} of {soil_csv_path}: "
                    f"'{row['field_id']}' — {exc}"
                ) from exc
            # Preserve all columns, coercing numeric fields
            record = dict(row)
            record["field_id"] = fid
            try:
                record["ph"] = float(row["ph"])
                record["organic_matter"] = float(row["organic_matter"])
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Non-numeric value in row {row_num} of {soil_csv_path}: {exc}"
                ) from exc
            if "slope_pct" in record and record["slope_pct"]:
                record["slope_pct"] = float(record["slope_pct"])
            soil_by_field[fid] = record

    logger.info(f"Loaded NRCS soil data for {len(soil_by_field)} fields from {soil_csv_path}")
    return soil_by_field


def merge_soil_into_boundaries(
    geojson_data: dict,
    soil_by_field: dict[int, dict],
    soil_key: str = "nrcs_soil",
) -> dict:
    """
    Merge NRCS soil attributes into GeoJSON feature properties.

    For each feature whose ``field_id`` property matches a key in *soil_by_field*,
    a nested soil object is injected under *soil_key*.  Features without a match
    are kept unchanged.

    Args:
        geojson_data: GeoJSON FeatureCollection dict (mutated in-place).
        soil_by_field: Dict mapping field_id to soil attribute dict.
        soil_key: Property name for the nested soil object (default: ``nrcs_soil``).

    Returns:
        Updated GeoJSON FeatureCollection dict.
    """
    features = geojson_data.get("features", [])
    matched = 0
    for feature in features:
        fid = feature.get("properties", {}).get("field_id")
        if fid is not None and fid in soil_by_field:
            soil = {k: v for k, v in soil_by_field[fid].items() if k != "field_id"}
            feature["properties"][soil_key] = soil
            matched += 1

    logger.info(f"Merged soil data into {matched}/{len(features)} features")
    return geojson_data


def import_fields(
    geojson_path: Path = DEFAULT_FIELDS_GEOJSON,
    soil_csv_path: Path = DEFAULT_SOIL_CSV,
    output_path: Path = DEFAULT_OUTPUT,
) -> str:
    """
    Import field boundaries and NRCS soil data, then write an enriched GeoJSON.

    Steps:
      1. Load field boundaries from *geojson_path*.
      2. Load NRCS soil attributes from *soil_csv_path*.
      3. Merge soil data into each matching feature.
      4. Write the enriched FeatureCollection to *output_path*.

    Args:
        geojson_path: Path to input field boundary GeoJSON.
        soil_csv_path: Path to NRCS soil CSV
            (must contain field_id, soil_type, ph, organic_matter).
        output_path: Path where the enriched GeoJSON will be written.

    Returns:
        Human-readable result string.
    """
    geojson_path = Path(geojson_path)
    soil_csv_path = Path(soil_csv_path)
    output_path = Path(output_path)

    try:
        geojson_data = load_field_boundaries(geojson_path)
        soil_by_field = load_nrcs_soil_data(soil_csv_path)
        enriched = merge_soil_into_boundaries(geojson_data, soil_by_field)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(enriched, f, indent=2)

        n = len(enriched.get("features", []))
        logger.info(f"Wrote {n} enriched features to {output_path}")
        return (
            f"✓ Imported {n} field boundaries with NRCS soil data. "
            f"Saved to {output_path}"
        )

    except (FileNotFoundError, ValueError) as exc:
        logger.error(f"Import failed: {exc}")
        return f"Error: {exc}"
    except Exception as exc:
        logger.error(f"Unexpected error during import: {exc}")
        return f"Error: {exc}"


def main() -> int:
    """Run the default import from the project root."""
    result = import_fields()
    print(result)

    output_path = Path(DEFAULT_OUTPUT)
    if output_path.exists():
        print(f"\n✓ Enriched GeoJSON written: {output_path}")
        print(f"  File size: {output_path.stat().st_size} bytes")
        return 0
    print(f"\n✗ Output file not found: {DEFAULT_OUTPUT}")
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
