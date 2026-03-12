# Issue-00000006: Import Field Boundaries (GeoJSON) and NRCS Soil Data

| Field              | Value                                                                                      |
| ------------------ | ------------------------------------------------------------------------------------------ |
| **Issue**          | #6                                                                                         |
| **Type**           | ✨ Feature request                                                                         |
| **Priority**       | P2                                                                                         |
| **Requester**      | Human                                                                                      |
| **Assignee**       | AI agent                                                                                   |
| **Date requested** | 2026-03-12                                                                                 |
| **Status**         | **Resolved** — implemented in this PR                                                      |
| **Target release** | Sprint W11 2026                                                                            |
| **Shipped in**     | PR on branch `copilot/import-field-boundaries-nrcs-data`                                   |

---

## 📋 Summary

### Problem statement

The repository contains a `scripts/download_fields.py` script that generates
Iowa field boundary GeoJSON, but there is no corresponding script or tool to
fetch NRCS (Natural Resources Conservation Service) soil survey data for those
fields. As a result, downstream analysis and mapping notebooks cannot access
soil attributes (type, pH, organic matter, drainage class, slope) alongside
field geometry.

### Proposed solution

1. Add `scripts/download_soil.py` — an idempotent script that reads
   `data/fields_EPSG4326.geojson`, generates NRCS SSURGO–style soil attributes
   for each field, and writes:
   - `data/soil_EPSG4326.csv` — tabular soil data
   - `data/fields_with_soil.geojson` — field boundaries enriched with a `soil`
     property
2. Add `.crewai/tools/nrcs_soil_tool.py` — a `BaseTool` that CrewAI agents can
   invoke to fetch and persist soil data, mirroring the existing
   `FieldBoundariesTool`.

### User story

> As a **data analyst or AI agent** working with Iowa agricultural fields, I
> want **NRCS soil survey data joined to field boundaries** so that I can
> **analyse soil-crop interactions and generate soil-aware maps** without
> manually fetching and joining data.

---

## 🎯 Acceptance Criteria

- [x] `scripts/download_soil.py` is executable and idempotent
- [x] Running the script produces `data/soil_EPSG4326.csv` with columns:
      `field_id`, `mapunit_name`, `component_name`, `soil_type`,
      `drainage_class`, `slope_pct`, `ph`, `organic_matter`, `source`, `crs`
- [x] Running the script produces `data/fields_with_soil.geojson` where each
      feature contains a nested `soil` property
- [x] `.crewai/tools/nrcs_soil_tool.py` exports a `NRCSSoilTool` that CrewAI
      agents can instantiate and call
- [x] Soil series are drawn from representative Iowa SSURGO data
      (Clarion, Webster, Nicollet, Canisteo, Harps, Storden)
- [x] Synthetic data uses a fixed random seed (42) so outputs are reproducible

---

## 🔍 Investigation Log

| Date       | Action                                                                                   |
| ---------- | ---------------------------------------------------------------------------------------- |
| 2026-03-12 | Confirmed `data/soil_EPSG4326.csv` absent from root `data/` dir (only in `assignment-02/`) |
| 2026-03-12 | Reviewed `scripts/download_fields.py` and `field_boundaries_tool.py` for patterns       |
| 2026-03-12 | Selected six representative Iowa soil series from NRCS SSURGO documentation             |
| 2026-03-12 | Implemented `download_soil.py` and `nrcs_soil_tool.py`; generated output files          |

---

## 📎 References

- USDA NRCS Web Soil Survey — <https://websoilsurvey.nrcs.usda.gov/>
- NRCS SSURGO database — <https://www.nrcs.usda.gov/resources/data-and-reports/ssurgo>
- Related script: [`scripts/download_fields.py`](../../../scripts/download_fields.py)
- Related tool: [`.crewai/tools/field_boundaries_tool.py`](../../../.crewai/tools/field_boundaries_tool.py)
