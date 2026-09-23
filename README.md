# DeNovoVHH-DB v1.0

An academic, evidence-graded database and web application for single-domain
antibodies (VHH / nanobodies), spanning natural, library-derived, engineered,
and *de novo* / computationally-designed binders. Built to PDB/UniProt/SAbDab
conventions: compact scientific tables, per-value provenance, evidence badges,
citation blocks, and an embedded Mol* 3D structure viewer.

## Guiding principle — no fabrication

Every value is either measured, curated from a named source, calculated by a
named method, or explicitly marked **Not reported / Not available**. Nothing is
estimated or invented to fill a gap. The database enforces the distinction:

> **designed ≠ tested ≠ binder ≠ functional ≠ therapeutic**

Each record carries an evidence grade (E0–E6), a data-status label per field
(Experimental / Curated / Calculated / Predicted / Inferred / Not reported),
and a field-level provenance trail. Original source values are stored separately
from normalized/calculated values.

## Contents at a glance (v1.0)

| Entity | Count |
|---|---|
| VHH / single-domain antibody records | 24,780 |
| — with experimental 3D structure | 954 |
| — with experimental affinity | 1,033 |
| — computationally designed (*de novo*) | 1,886 |
| — linked to a publication | 860 |
| Antigen targets | 607 |
| PDB structures | 1,300 |
| Publications | 428 |
| Affinity measurements | 1,815 |

Quality labels (honest): High 526 · Moderate 884 · Low 23,370.
Design provenance: natural 2,755 · computational 1,886 · engineering 91 ·
library 38 · unknown 20,010.

## Data sources (all open-access, redistributable)

- **ANDD** (Antibody Numeric Data Database, Nature Sci Data 2026;
  Zenodo 18151718; CC-BY-4.0) — primary sequence + affinity + curated CDRs.
- **RCSB PDB** (GraphQL API) — structure metadata, chains, resolution, linked
  citations (1,288/1,300 entries enriched; 12 obsolete).
- **Europe PMC** — publication metadata + abstracts; design methods mined from
  abstracts (587/589 with abstracts).
- **UniProt** — antigen/target annotation (367 accessions).
- **SAbDab / SAbDab2** — per-PDB structural cross-reference links.

Full provenance is in `docs/01_DATA_SOURCE_AUDIT.md` and
`docs/02_SOURCE_TO_FIELD_INVENTORY.md`; the field-by-field schema is in
`docs/03_DATA_DICTIONARY.md`.

## Run it

```bash
pip install -r requirements.txt   # or use the provided conda env
./run.sh                          # serves at http://127.0.0.1:8000
```

- Web UI: <http://127.0.0.1:8000/>
- Interactive API docs (Swagger): <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

The SQLite database (`data/denovovhh.sqlite`) ships prebuilt. To rebuild it from
the raw sources, see `etl/build_db.py`.

## Web pages

Home · Browse (faceted filters) · Search · VHH detail (tabs, CDR strip, Mol*
viewer, provenance timeline) · Targets · Target detail · Structures · Structure
detail · Publications · Design methods · Statistics · Datasets · Compare · Help ·
About.

## JSON API (versioned, `/api/v1`)

- `GET /api/v1/vhh` — list with filters (target, uniprot, organism,
  design_class, quality, evidence, sdab_type, has_structure, has_affinity,
  is_de_novo, kd_min/kd_max, length/CDR3 filters), pagination, sorting.
- `GET /api/v1/vhh/{id}` — full record (sequence, CDRs, physchem, affinities,
  specificities, structures, design method, provenance).
- `GET /api/v1/vhh/{id}/cite.bib` · `/cite.ris` — citation exports.
- `GET /api/v1/targets` · `/api/v1/stats` · ontology endpoints.
- `GET /api/v1/download/{csv,tsv,fasta,json}` — filtered dataset dumps.

## Notes / limitations

- IMGT numbering (ANARCI/HMMER) could not be installed on this platform;
  framework/CDR boundaries use ANDD's curated CDRs matched by exact substring
  within each sequence rather than forced numbering.
- Physicochemical properties are calculated (Biopython ProtParam) and labelled
  as such; they are not experimental measurements.
- The overwhelming "Low" quality / "unknown" design counts are honest: most ANDD
  records lack structure, affinity, or a resolvable design method, and are
  retained and labelled rather than discarded or embellished.
