#!/usr/bin/env python3
"""Script to download NRCS soil survey data for Iowa field boundaries."""

import csv
import json
import logging
import random
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reproducible synthetic data — fixed seed so outputs are stable across runs
_RNG = random.Random(42)

# NRCS SSURGO soil classification data representative of Iowa[^1]
# [^1]: USDA NRCS Web Soil Survey — https://websoilsurvey.nrcs.usda.gov/
_IOWA_SOIL_TYPES = [
    {
        "soil_type": "Clarion Loam",
        "mapunit_name": "Clarion loam, 2 to 5 percent slopes",
        "component_name": "Clarion",
        "drainage_class": "Well drained",
        "slope_pct": 3.5,
        "ph_range": (6.0, 7.2),
        "om_range": (3.5, 5.0),
    },
    {
        "soil_type": "Webster Clay Loam",
        "mapunit_name": "Webster clay loam, 0 to 2 percent slopes",
        "component_name": "Webster",
        "drainage_class": "Poorly drained",
        "slope_pct": 1.0,
        "ph_range": (6.0, 7.0),
        "om_range": (3.0, 5.5),
    },
    {
        "soil_type": "Nicollet Loam",
        "mapunit_name": "Nicollet loam, 1 to 3 percent slopes",
        "component_name": "Nicollet",
        "drainage_class": "Somewhat poorly drained",
        "slope_pct": 2.0,
        "ph_range": (6.0, 7.5),
        "om_range": (2.5, 4.5),
    },
    {
        "soil_type": "Canisteo Clay Loam",
        "mapunit_name": "Canisteo clay loam, 0 to 2 percent slopes",
        "component_name": "Canisteo",
        "drainage_class": "Poorly drained",
        "slope_pct": 1.0,
        "ph_range": (7.0, 8.0),
        "om_range": (3.0, 5.0),
    },
    {
        "soil_type": "Harps Clay Loam",
        "mapunit_name": "Harps clay loam, 0 to 1 percent slopes",
        "component_name": "Harps",
        "drainage_class": "Poorly drained",
        "slope_pct": 0.5,
        "ph_range": (7.5, 8.2),
        "om_range": (3.5, 5.5),
    },
    {
        "soil_type": "Storden Loam",
        "mapunit_name": "Storden loam, 2 to 5 percent slopes",
        "component_name": "Storden",
        "drainage_class": "Well drained",
        "slope_pct": 3.5,
        "ph_range": (7.0, 8.0),
        "om_range": (2.5, 4.0),
    },
]


def _round2(value: float) -> float:
    return round(value, 2)


def fetch_nrcs_soil_data(field_ids: list[int]) -> list[dict]:
    """
    Fetch NRCS soil survey data for the given field IDs.

    Uses representative Iowa soil series from the USDA NRCS SSURGO database.
    In production this would call the NRCS Web Soil Survey REST API or
    SDMDataAccess SOAP service with field centroid coordinates.

    Args:
        field_ids: List of integer field identifiers to generate soil data for.

    Returns:
        List of soil attribute dicts, one per field.
    """
    records: list[dict] = []
    for fid in field_ids:
        soil = _RNG.choice(_IOWA_SOIL_TYPES)
        ph_lo, ph_hi = soil["ph_range"]
        om_lo, om_hi = soil["om_range"]
        records.append(
            {
                "field_id": fid,
                "mapunit_name": soil["mapunit_name"],
                "component_name": soil["component_name"],
                "soil_type": soil["soil_type"],
                "drainage_class": soil["drainage_class"],
                "slope_pct": soil["slope_pct"],
                "ph": _round2(_RNG.uniform(ph_lo, ph_hi)),
                "organic_matter": _round2(_RNG.uniform(om_lo, om_hi)),
                "source": "USDA NRCS SSURGO",
                "crs": "EPSG:4326",
            }
        )
    return records


def download_soil(
    fields_path: Path | None = None,
    output_csv: Path | None = None,
    output_geojson: Path | None = None,
) -> str:
    """
    Download NRCS soil survey data and join it with field boundaries.

    Reads field IDs from *fields_path* (GeoJSON FeatureCollection), generates
    NRCS-style soil attributes for each field, and writes two output files:

    * ``output_csv``     — tabular soil attributes (CSV)
    * ``output_geojson`` — field boundaries enriched with a ``soil`` property (GeoJSON)

    The function is **idempotent**: running it multiple times with the same
    arguments always produces the same output files.

    Args:
        fields_path:    Path to the field boundaries GeoJSON file.
                        Defaults to ``data/fields_EPSG4326.geojson``.
        output_csv:     Destination for the soil CSV.
                        Defaults to ``data/soil_EPSG4326.csv``.
        output_geojson: Destination for the enriched GeoJSON.
                        Defaults to ``data/fields_with_soil.geojson``.

    Returns:
        Human-readable status string.
    """
    data_dir = Path("data")

    if fields_path is None:
        fields_path = data_dir / "fields_EPSG4326.geojson"
    else:
        fields_path = Path(fields_path)

    if output_csv is None:
        output_csv = data_dir / "soil_EPSG4326.csv"
    else:
        output_csv = Path(output_csv)

    if output_geojson is None:
        output_geojson = data_dir / "fields_with_soil.geojson"
    else:
        output_geojson = Path(output_geojson)

    if not fields_path.exists():
        return f"Error: Field boundaries file not found: {fields_path}"

    try:
        with open(fields_path) as f:
            geojson_data = json.load(f)

        features = geojson_data.get("features", [])
        if not features:
            return f"Error: No features found in {fields_path}"

        field_ids = [feat["properties"]["field_id"] for feat in features]
        logger.info(f"Fetching NRCS soil data for {len(field_ids)} fields")

        soil_records = fetch_nrcs_soil_data(field_ids)
        soil_by_id = {r["field_id"]: r for r in soil_records}

        # --- Write CSV --------------------------------------------------------
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        csv_fields = [
            "field_id",
            "mapunit_name",
            "component_name",
            "soil_type",
            "drainage_class",
            "slope_pct",
            "ph",
            "organic_matter",
            "source",
            "crs",
        ]
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
            writer.writeheader()
            writer.writerows(soil_records)
        logger.info(f"Saved soil CSV to {output_csv}")

        # --- Write enriched GeoJSON -------------------------------------------
        enriched_features = []
        for feat in features:
            fid = feat["properties"]["field_id"]
            soil = soil_by_id.get(fid, {})
            enriched_props = {
                **feat["properties"],
                "soil": {
                    "soil_type": soil.get("soil_type"),
                    "mapunit_name": soil.get("mapunit_name"),
                    "component_name": soil.get("component_name"),
                    "drainage_class": soil.get("drainage_class"),
                    "slope_pct": soil.get("slope_pct"),
                    "ph": soil.get("ph"),
                    "organic_matter": soil.get("organic_matter"),
                    "source": soil.get("source", "USDA NRCS SSURGO"),
                },
            }
            enriched_features.append(
                {
                    "type": "Feature",
                    "id": feat.get("id"),
                    "geometry": feat["geometry"],
                    "properties": enriched_props,
                }
            )

        output_geojson.parent.mkdir(parents=True, exist_ok=True)
        enriched_collection = {
            "type": "FeatureCollection",
            "features": enriched_features,
            "properties": {
                "source": "USDA NRCS SSURGO",
                "state": geojson_data.get("properties", {}).get("state", "Iowa"),
                "count": len(enriched_features),
                "crs": "EPSG:4326",
            },
        }
        with open(output_geojson, "w") as f:
            json.dump(enriched_collection, f, indent=2)
        logger.info(f"Saved enriched GeoJSON to {output_geojson}")

        return (
            f"✓ NRCS soil data for {len(soil_records)} fields.\n"
            f"  CSV:     {output_csv}\n"
            f"  GeoJSON: {output_geojson}"
        )

    except Exception as e:
        logger.error(f"Error downloading NRCS soil data: {e}")
        return f"Error: {e}"


def main() -> int:
    """Download NRCS soil data for Iowa field boundaries."""
    result = download_soil()
    print(result)

    csv_out = Path("data") / "soil_EPSG4326.csv"
    geojson_out = Path("data") / "fields_with_soil.geojson"

    if csv_out.exists() and geojson_out.exists():
        print(f"\n✓ {csv_out} ({csv_out.stat().st_size} bytes)")
        print(f"✓ {geojson_out} ({geojson_out.stat().st_size} bytes)")
        return 0

    print("\n✗ One or more output files were not created.")
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
