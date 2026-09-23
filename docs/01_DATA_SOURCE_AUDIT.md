# DeNovoVHH-DB — Literature & Data-Source Audit (v1.0)

**Audit date:** 2026-09-15
**Auditor:** Claude Science (automated API/availability probes + primary-literature checks)
**Scope:** Verify current availability, versions, access mechanism, licensing and
redistribution terms of every external source before ingestion, per the master
specification (§3, §30, §59 Phase 1, §61).

---

## 1. Executive summary

All core open scientific APIs required for a no-fabrication provenance chain are
**live and reachable**: RCSB PDB (Search + Data APIs), UniProt REST, Europe
PMC, and Crossref. The specialized nanobody resources named in the spec were
each checked individually; the landscape has **changed since the spec was
written** and two findings materially affect the build (see §4).

The v1.0 data backbone is:

1. **ANDD** (Zenodo, CC-BY-4.0) — primary tabular backbone: real VHH/nanobody
   sequences, CDRs, antigens, PDB links, **experimental KD/ΔG**, provenance.
2. **RCSB PDB** — authoritative structural layer + primary-citation linkage
   (enrichment of every ANDD record that carries a PDB ID).
3. **Europe PMC / Crossref** — publication metadata and abstracts (design-method
   mining, first-disclosure dating).
4. **UniProt** — target protein identifiers / annotations.

---

## 2. Sources verified LIVE and used

| Source | Endpoint | Status | Access | License / redistribution |
|---|---|---|---|---|
| RCSB PDB Search API | `search.rcsb.org/rcsbsearch/v2/query` | 200 | Open REST/JSON | CC0 — metadata & coordinates public domain; redistribution permitted |
| RCSB PDB Data API | `data.rcsb.org/rest/v1/core/*` + GraphQL | 200 | Open REST/GraphQL | CC0 |
| UniProt REST | `rest.uniprot.org/uniprotkb/*` | 200 | Open REST/JSON | CC-BY-4.0 |
| Europe PMC | `ebi.ac.uk/europepmc/webservices/rest/*` | 200 | Open REST/JSON | Metadata open; abstracts per publisher |
| Crossref | `api.crossref.org/works/*` | 200 | Open REST/JSON | Metadata open (CC0-like facts) |
| ANDD dataset | `zenodo.org/records/18151718` | 200 | Open download (grant approved) | **CC-BY-4.0 — redistribution permitted with attribution** |
| bioRxiv API | `api.biorxiv.org/details/*` | 200 | Open REST/JSON | Preprint metadata open |

### RCSB structural counts (full-text, entries), probed 2026-09-15
- `nanobody` → **1,774**
- `VHH` → **478**
- `single domain antibody` → **2,801**
- `camelid antibody` → **172**

### ANDD content (Zenodo record 18151718, "ANDD v2")
- `Antibody and Nanobody Design Dataset (ANDD)_v2.xlsx` — 13.35 MB, 48,800 rows (**used**)
- `ANDD_pdb.zip` — 2.23 GB structures (**not ingested**; structures pulled from RCSB directly to avoid redundant 2 GB redistribution)
- `Data_dictionary.csv`, `Data_quality_control_report.pdf` (**used as reference**)
- Nanobody/VHH rows: **30,119**; with PDB ID: 3,178; with experimental KD: 1,724; complexes: 4,480.
- ANDD itself integrates 15 upstream sources incl. SabDab_nano, sdAB-DB, PLAbDab-nano, INDI patents, and a generative de-novo-design study — providing source-level provenance we preserve.

---

## 3. Sources checked — access-restricted or superseded

| Source | Finding | Decision for v1.0 |
|---|---|---|
| **SAbDab2** (`opig.stats.ox.ac.uk`) | Now **SAbDab2 v2.1.0**, a single-page web app; the legacy flat-file `summary/all/` TSV export is **deprecated** (returns the SPA shell). Bulk export requires the new interactive backend (not publicly documented for programmatic bulk pull). | Use as **per-PDB cross-reference link** source, not bulk ingest. Structural layer fully covered by RCSB; SAbDab annotations reach us indirectly via ANDD (`SabDab_nano` source rows). |
| **sdAb-DB** (`sdab-db.ca`) | Reachable only behind allowlist; canonical curated sdAb resource. | Reached indirectly — ANDD ingests `sdAB-DB` (3,047 rows) with source provenance preserved. Direct link retained as cross-reference. |
| **NanoLAS** (`nanolas.cn`) | Outside allowlist; integrative nanobody DB. | Cross-reference link; not bulk-ingested for v1.0. |
| figshare / Zenodo search | figshare blocked; Zenodo grant approved for the specific ANDD record. | ANDD obtained. |

---

## 4. New findings (landscape changed since spec was written)

1. **SAbDab → SAbDab2 migration (v2.1.0).** The spec (§3.1) assumed the legacy
   SAbDab flat-file summary. That download path is gone; SAbDab2 is a React SPA.
   This is why the design implication "ingest/cross-reference SAbDab rather than
   duplicate" is honored via **cross-reference links** plus ANDD's SabDab_nano rows.

2. **AVIDbase (2026)** — *"AVIDbase: A biologically accurate structural dataset
   of nanobody-antigen complexes"* (Protein Science 2026, DOI 10.1002/pro.70773).
   A curated nanobody–antigen structural dataset **not named in the master spec**.
   Flagged as a candidate v1.1 cross-reference / benchmark comparator source.

3. **ANDD supersedes several planned separate ingests.** Because ANDD v2 already
   integrates sdAb-DB, SabDab-nano, PLAbDab-nano, INDI patents and a generative
   de-novo study with per-row `Source`/`Provenance`, ingesting ANDD + enriching
   via RCSB/EuropePMC yields the required provenance chain without separately
   scraping each upstream DB — consistent with the spec's "do not duplicate an
   existing database unnecessarily" (§61) and "do not scrape when an official
   dataset exists."

---

## 5. No-fabrication guarantee

Every ingested value is copied from a verified source and stored with
field-level provenance (`source_type`, `source_id`, `source_location`,
`extraction_method`, `verification_status`). Values computed by us (physchem,
CDR numbering) are labeled `Calculated`/`Predicted` with software+version.
Absent values are stored as `Not reported` / `Not available` — never invented.
See `02_SOURCE_TO_FIELD_INVENTORY.md` for the field-level mapping.
