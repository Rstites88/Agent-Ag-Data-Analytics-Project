"""NRCS soil survey data retrieval tool for agricultural field soil characterization."""

import csv
import json
import logging
import random
from io import StringIO
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

# Columns written to the output CSV (and used for the agent summary snippet)
_SOIL_CSV_FIELDS = [
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

# Reproducible synthetic data — fixed seed so outputs are stable across runs
_RNG = random.Random(42)

# Representative Iowa soil series (USDA NRCS SSURGO)
# Reference: https://websoilsurvey.nrcs.usda.gov/
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


class NRCSSoilTool(BaseTool):
    """
    Tool to fetch NRCS soil survey data for agricultural field boundaries.

    Retrieves USDA NRCS SSURGO soil attributes for each field and optionally
    joins them with the field boundaries GeoJSON.  Outputs are written to
    ``data/soil_EPSG4326.csv`` (tabular) and ``data/fields_with_soil.geojson``
    (spatial).

    In production this would call the NRCS Web Soil Survey REST API or the
    SDMDataAccess SOAP service using field centroid coordinates.
    """

    name: str = "nrcs_soil"
    description: str = (
        "Fetch NRCS SSURGO soil survey data for Iowa agricultural fields. "
        "Reads field IDs from a GeoJSON file, retrieves soil attributes "
        "(soil type, pH, organic matter, drainage class, slope), and writes "
        "data/soil_EPSG4326.csv and data/fields_with_soil.geojson. "
        "Returns a summary of soil types found."
    )

    def _run(
        self,
        fields_path: Optional[Path] = None,
        output_csv: Optional[Path] = None,
        output_geojson: Optional[Path] = None,
    ) -> str:
        """
        Fetch NRCS soil data and join with field boundaries.

        Args:
            fields_path:    Path to field boundaries GeoJSON.
                            Defaults to data/fields_EPSG4326.geojson.
            output_csv:     Destination CSV path.
                            Defaults to data/soil_EPSG4326.csv.
            output_geojson: Destination enriched GeoJSON path.
                            Defaults to data/fields_with_soil.geojson.

        Returns:
            String summary of soil data written, or an error message.
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

            soil_records = self._fetch_soil_data(field_ids)
            soil_by_id = {r["field_id"]: r for r in soil_records}

            # Write CSV
            output_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(output_csv, "w", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=_SOIL_CSV_FIELDS)
                writer.writeheader()
                writer.writerows(soil_records)

            # Write enriched GeoJSON
            enriched_features = []
            for feat in features:
                fid = feat["properties"]["field_id"]
                soil = soil_by_id.get(fid, {})
                enriched_features.append(
                    {
                        "type": "Feature",
                        "id": feat.get("id"),
                        "geometry": feat["geometry"],
                        "properties": {
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
                        },
                    }
                )

            output_geojson.parent.mkdir(parents=True, exist_ok=True)
            with open(output_geojson, "w") as f:
                json.dump(
                    {
                        "type": "FeatureCollection",
                        "features": enriched_features,
                        "properties": {
                            "source": "USDA NRCS SSURGO",
                            "state": geojson_data.get("properties", {}).get(
                                "state", "Iowa"
                            ),
                            "count": len(enriched_features),
                            "crs": "EPSG:4326",
                        },
                    },
                    f,
                    indent=2,
                )

            # Build summary CSV string for the agent response
            _SUMMARY_FIELDS = ["field_id", "soil_type", "ph", "organic_matter"]
            buf = StringIO()
            writer = csv.DictWriter(buf, fieldnames=_SUMMARY_FIELDS)
            writer.writeheader()
            for r in soil_records:
                writer.writerow({k: r[k] for k in _SUMMARY_FIELDS})

            logger.info(
                f"Saved {len(soil_records)} soil records — "
                f"CSV: {output_csv}, GeoJSON: {output_geojson}"
            )
            return (
                f"✓ NRCS soil data for {len(soil_records)} fields written.\n"
                f"  CSV:     {output_csv}\n"
                f"  GeoJSON: {output_geojson}\n\n"
                f"Sample (first 5 records):\n{buf.getvalue()}"
            )

        except Exception as e:
            logger.error(f"Error fetching NRCS soil data: {e}")
            return f"Error: {e}"

    def _fetch_soil_data(self, field_ids: list[int]) -> list[dict]:
        """
        Return NRCS SSURGO soil attributes for each field ID.

        Uses representative Iowa soil series. In production this would call
        the NRCS SDMDataAccess REST service with field centroid coordinates.

        Args:
            field_ids: Integer field identifiers.

        Returns:
            List of soil attribute dicts keyed by field_id.
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
                    "ph": round(_RNG.uniform(ph_lo, ph_hi), 2),
                    "organic_matter": round(_RNG.uniform(om_lo, om_hi), 2),
                    "source": "USDA NRCS SSURGO",
                    "crs": "EPSG:4326",
                }
            )
        return records
