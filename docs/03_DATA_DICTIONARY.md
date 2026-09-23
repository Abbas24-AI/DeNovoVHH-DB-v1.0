# DeNovoVHH-DB — Data Dictionary (v1.0, auto-generated from schema)

Generated from `app/models.py`. 23 tables. Original source values are stored separately from normalized/calculated values; absent values are `Not reported`.


## `application`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| name | VARCHAR(256) | False |  |
| description | TEXT | True |  |

## `dataset`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| name | VARCHAR(128) | False |  |
| slug | VARCHAR(64) | False |  |
| description | TEXT | True |  |
| release_version | VARCHAR(24) | True |  |
| n_records | INTEGER | True |  |
| formats | JSON | True |  |
| license | VARCHAR(64) | True |  |

## `design_method`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| method_class | VARCHAR(32) | False |  |
| method_name | VARCHAR(128) | False |  |
| software | VARCHAR(128) | True |  |
| version | VARCHAR(64) | True |  |
| description | TEXT | True |  |

## `disease`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| name | VARCHAR(256) | False |  |

## `patent`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| patent_number | VARCHAR(64) | True |  |
| family | VARCHAR(128) | True |  |
| title | TEXT | True |  |
| assignee | TEXT | True |  |
| disclosure_date | VARCHAR(32) | True |  |
| source | VARCHAR(64) | True |  |

## `publication`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| pmid | VARCHAR(16) | True |  |
| pmcid | VARCHAR(16) | True |  |
| doi | VARCHAR(128) | True |  |
| title | TEXT | True |  |
| journal | VARCHAR(256) | True |  |
| year | INTEGER | True |  |
| authors | TEXT | True |  |
| abstract | TEXT | True |  |
| disclosure_type | VARCHAR(48) | True |  |

## `structure`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| pdb_id | VARCHAR(8) | False |  |
| is_experimental | BOOLEAN | False |  |
| experimental_method | VARCHAR(64) | True |  |
| resolution | FLOAT | True |  |
| title | TEXT | True |  |
| deposition_date | VARCHAR(32) | True |  |
| authors | TEXT | True |  |
| is_complex | BOOLEAN | False |  |
| model_source | VARCHAR(64) | True |  |
| model_version | VARCHAR(64) | True |  |
| confidence | FLOAT | True |  |
| chain_mapping | JSON | True |  |
| pdb_pmid | VARCHAR(16) | True |  |
| pdb_doi | VARCHAR(128) | True |  |

## `target`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| name | VARCHAR(256) | False |  |
| gene_symbol | VARCHAR(64) | True |  |
| uniprot | VARCHAR(32) | True |  |
| organism | VARCHAR(128) | True |  |
| target_class | VARCHAR(128) | True |  |
| function | TEXT | True |  |
| disease_association | TEXT | True |  |
| target_sequence | TEXT | True |  |

## `antigen_construct`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| name | VARCHAR(512) | True |  |
| sequence | TEXT | True |  |
| source_organism | VARCHAR(128) | True |  |
| accession | VARCHAR(64) | True |  |
| target_id | INTEGER | True |  FK→target.id |

## `design_run`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| design_method_id | INTEGER | True |  FK→design_method.id |
| n_designed | INTEGER | True |  |
| n_tested | INTEGER | True |  |
| n_validated | INTEGER | True |  |
| input_structure | VARCHAR(64) | True |  |
| constraints | TEXT | True |  |
| filtering | TEXT | True |  |
| ranking | TEXT | True |  |

## `structure_chain`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| structure_id | INTEGER | False |  FK→structure.id |
| asym_id | VARCHAR(8) | True |  |
| auth_asym_id | VARCHAR(8) | True |  |
| role | VARCHAR(24) | True |  |
| entity_id | VARCHAR(8) | True |  |
| macromolecule_name | TEXT | True |  |

## `study`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| title | TEXT | True |  |
| year | INTEGER | True |  |
| publication_id | INTEGER | True |  FK→publication.id |

## `vhh`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| denovovhh_id | VARCHAR(16) | False |  |
| sdab_type | VARCHAR(16) | False |  |
| name | VARCHAR(256) | True |  |
| source_ids | JSON | True |  |
| sabdab_id | VARCHAR(32) | True |  |
| andd_source | VARCHAR(64) | True |  |
| andd_provenance | TEXT | True |  |
| source_organism | VARCHAR(128) | True |  |
| evidence_flags | JSON | True |  |
| quality_label | VARCHAR(16) | True |  |
| design_status | VARCHAR(48) | True |  |
| is_de_novo | BOOLEAN | False |  |
| predicted_or_experimental | VARCHAR(24) | True |  |
| sequence_verified | BOOLEAN | False |  |
| target_verified | BOOLEAN | False |  |
| structure_verified | BOOLEAN | False |  |
| affinity_verified | BOOLEAN | False |  |
| publication_verified | BOOLEAN | False |  |
| target_id | INTEGER | True |  FK→target.id |
| antigen_id | INTEGER | True |  FK→antigen_construct.id |
| design_method_id | INTEGER | True |  FK→design_method.id |
| study_id | INTEGER | True |  FK→study.id |
| derived_from_id | INTEGER | True |  FK→vhh.id |
| created_at | DATETIME | False |  |

## `affinity_measurement`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| kd_M | FLOAT | True |  |
| kd_original | VARCHAR(64) | True |  |
| kon | FLOAT | True |  |
| koff | FLOAT | True |  |
| ic50 | FLOAT | True |  |
| ec50 | FLOAT | True |  |
| ki | FLOAT | True |  |
| delta_g_kJmol | FLOAT | True |  |
| unit | VARCHAR(16) | True |  |
| method | VARCHAR(64) | True |  |
| temperature | VARCHAR(32) | True |  |
| buffer | TEXT | True |  |
| is_predicted | BOOLEAN | False |  |
| source | VARCHAR(64) | True |  |

## `cdr`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| region | VARCHAR(8) | False |  |
| sequence | TEXT | True |  |
| length | INTEGER | True |  |
| numbering_scheme | VARCHAR(24) | True |  |
| source | VARCHAR(32) | True |  |
| imgt_positions | TEXT | True |  |

## `developability_prediction`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| liabilities | JSON | True |  |
| n_glyc_motifs | INTEGER | True |  |
| deamidation_sites | INTEGER | True |  |
| oxidation_sites | INTEGER | True |  |
| unusual_cysteine | BOOLEAN | True |  |
| surface_hydrophobicity | FLOAT | True |  |
| method | VARCHAR(64) | True |  |
| calc_version | VARCHAR(64) | True |  |

## `epitope`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | True |  FK→vhh.id |
| antigen_id | INTEGER | True |  FK→antigen_construct.id |
| residue_range | VARCHAR(128) | True |  |
| residue_list | TEXT | True |  |
| epitope_sequence | TEXT | True |  |
| kind | VARCHAR(24) | True |  |
| evidence | VARCHAR(24) | True |  |
| source | VARCHAR(64) | True |  |

## `experiment`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| assay | VARCHAR(64) | True |  |
| tested | BOOLEAN | True |  |
| binder | VARCHAR(16) | True |  |
| functional | VARCHAR(16) | True |  |
| conditions | TEXT | True |  |
| source | VARCHAR(64) | True |  |

## `physchem_profile`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| length | INTEGER | True |  |
| molecular_weight | FLOAT | True |  |
| theoretical_pi | FLOAT | True |  |
| net_charge_ph7 | FLOAT | True |  |
| aa_composition | JSON | True |  |
| cysteine_count | INTEGER | True |  |
| aromaticity | FLOAT | True |  |
| aliphatic_index | FLOAT | True |  |
| gravy | FLOAT | True |  |
| extinction_coefficient | INTEGER | True |  |
| instability_index | FLOAT | True |  |
| cdr3_length | INTEGER | True |  |
| cdr3_charge | FLOAT | True |  |
| cdr3_hydrophobicity | FLOAT | True |  |
| method | VARCHAR(64) | True |  |
| calc_version | VARCHAR(64) | True |  |

## `provenance_event`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | True |  FK→vhh.id |
| entity_type | VARCHAR(48) | True |  |
| field | VARCHAR(64) | True |  |
| value | TEXT | True |  |
| unit | VARCHAR(16) | True |  |
| source_type | VARCHAR(32) | True |  |
| source_id | VARCHAR(128) | True |  |
| source_location | VARCHAR(128) | True |  |
| extraction_method | VARCHAR(48) | True |  |
| verification_status | VARCHAR(24) | True |  |
| event_type | VARCHAR(48) | True |  |
| event_year | INTEGER | True |  |

## `sequence`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| original_sequence | TEXT | False |  |
| normalized_sequence | TEXT | False |  |
| mature_sequence | TEXT | True |  |
| length | INTEGER | True |  |
| checksum | VARCHAR(40) | True |  |
| engineered_mutations | TEXT | True |  |

## `specificity`
| column | type | nullable | notes |
|---|---|---|---|
| id PK | INTEGER | False |  |
| vhh_id | INTEGER | False |  FK→vhh.id |
| on_target | VARCHAR(32) | True |  |
| off_target | TEXT | True |  |
| cross_reactivity | TEXT | True |  |
| species_specificity | TEXT | True |  |
| label | VARCHAR(24) | True |  |
| source | VARCHAR(64) | True |  |

## `vhh_structure`
| column | type | nullable | notes |
|---|---|---|---|
| vhh_id PK | INTEGER | False |  FK→vhh.id |
| structure_id PK | INTEGER | False |  FK→structure.id |