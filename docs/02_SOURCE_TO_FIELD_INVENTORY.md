# DeNovoVHH-DB — Source-to-Field Inventory (v1.0)

Maps every populated database field to the external source that supplies it and
the evidence/status label applied. Fields not covered by a source in v1.0 are
stored as `Not reported`. "ANDD col" is the exact ANDD v2 column name.

## Legend — data status (spec §53)
`Experimental` · `Curated` · `Calculated` · `Predicted` · `Inferred` · `Not reported`

---

## VHH / Sequence

| DB field | Source | ANDD col / API field | Status |
|---|---|---|---|
| `denovovhh_id` | DeNovoVHH-DB | generated `DNVHH######` | Curated |
| `sdab_type` | ANDD | `Ab_or_Nano` → VHH/other | Curated |
| `original_sequence` | ANDD | `Ab/Nano H_Chain AA` | Experimental (as-disclosed) |
| `normalized_sequence` | DeNovoVHH-DB | uppercased, whitespace-stripped | Calculated |
| `sequence_length` | DeNovoVHH-DB | len(normalized) | Calculated |
| `sequence_checksum` | DeNovoVHH-DB | SHA-1 of normalized | Calculated |
| `engineered_mutations` | ANDD | `Ab/Nano_Mutation` | Curated |
| `source_organism` | ANDD | `Source_Organism` | Curated |

## CDR

| DB field | Source | ANDD col / API field | Status |
|---|---|---|---|
| `cdr1/2/3_seq (source)` | ANDD | `Ab/Nano_CDR H1/H2/H3` | Curated |
| `cdr_nomenclature (source)` | ANDD | `CDR Nomenclature` | Curated |
| `imgt_numbering`, `fr1..fr4`, IMGT CDRs | DeNovoVHH-DB | ANARCI (IMGT scheme) | Calculated |
| `cdr*_length`, `cdr3_charge/hydrophobicity` | DeNovoVHH-DB | derived | Calculated |

## Target / AntigenConstruct / Epitope

| DB field | Source | field | Status |
|---|---|---|---|
| `antigen_name` | ANDD | `Ag_Name` | Curated |
| `antigen_sequence` | ANDD | `Ag_Seq` | Experimental |
| `antigen_source_organism` | ANDD | `Ag_Source Organism` | Curated |
| `antigen_accession` | ANDD → UniProt | `Ag_Accession Code(s)` + UniProt REST | Curated/Experimental |
| target name/gene/function/class | UniProt | REST `/uniprotkb/{acc}` | Curated |
| epitope residues/interface | RCSB (interface) / ANDD | computed where structure present | Calculated/Not reported |

## Structure / StructureChain

| DB field | Source | field | Status |
|---|---|---|---|
| `pdb_id` | ANDD/RCSB | `PDB_ID` | Experimental |
| `experimental_method` | RCSB/ANDD | Data API `exptl.method` / `Experimental_Method` | Experimental |
| `resolution` | RCSB | `rcsb_entry_info.resolution_combined` | Experimental |
| `structure_title` | RCSB/ANDD | `struct.title` / `Structure_Title` | Experimental |
| `deposition_date` | RCSB | `rcsb_accession_info.deposit_date` | Experimental |
| `authors` | RCSB | `audit_author` | Experimental |
| chain mapping (H/Ag asym) | ANDD/RCSB | `*_Asym ID`, `*_Auth Asym ID` | Experimental |
| `is_complex` | ANDD | `Complex_Structure` | Experimental |

## Experiment / AffinityMeasurement

| DB field | Source | field | Status |
|---|---|---|---|
| `kd_M` | ANDD | `Affinity_Kd(M)…` | Experimental |
| `delta_g_kJmol` | ANDD | `∆Gbinding(kJ/mol)…` | Experimental |
| `affinity_method` | ANDD | `Affinity_Method` | Experimental |
| `predicted_or_experimental` | ANDD | `Predicted_or_Not` | Curated |

## DesignMethod / DesignRun

| DB field | Source | field | Status |
|---|---|---|---|
| `design_method_class` | ANDD `Source` + EuropePMC abstract mining | keyword taxonomy (§6) | Inferred (source-linked) |
| `software/model/version` | Literature | abstract/title text | Curated / Not reported |

## Study / Publication / Patent

| DB field | Source | field | Status |
|---|---|---|---|
| `pmid` / `pmcid` | RCSB → EuropePMC | `rcsb_primary_citation.pdbx_database_id_PubMed` | Curated |
| `doi` | RCSB / Crossref | `rcsb_primary_citation.pdbx_database_id_DOI` | Curated |
| `title/journal/year/authors` | EuropePMC / Crossref | REST | Curated |
| `abstract` | EuropePMC | REST | Curated |
| `patent_id` / `patent_family` | ANDD | `Source`=INDI_patent, `Provenance` | Curated / Not reported |
| `first_public_disclosure*` | derived | earliest of {pub year, patent, deposition} | Inferred |

## Provenance (field-level, spec §27)
Every value above is stored in `provenance_event` with `source_type`,
`source_id`, `source_location`, `extraction_method`, `verification_status`.
