"""DeNovoVHH-DB relational schema (SQLAlchemy 2.0 declarative).

Postgres-compatible: uses portable column types only (String/Text/Integer/Float/
Boolean/DateTime/JSON). Ships on SQLite for the v1.0 self-contained release; the
same models create an identical schema on PostgreSQL by swapping the engine URL.

Implements the entity set of master spec §26 and the field-level provenance
model of §27. Original source values are preserved separately from
normalized/calculated values throughout.
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import (String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Index)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------- #
#  Core hub: VHH
# --------------------------------------------------------------------------- #
class VHH(Base):
    __tablename__ = "vhh"
    id: Mapped[int] = mapped_column(primary_key=True)
    denovovhh_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)  # DNVHH000001
    sdab_type: Mapped[str] = mapped_column(String(16), default="VHH", index=True)
    name: Mapped[str | None] = mapped_column(String(256))  # Anti-<target> VHH

    # cross-reference identifiers (spec §9 Identity)
    source_ids: Mapped[dict | None] = mapped_column(JSON)   # {source: id}
    sabdab_id: Mapped[str | None] = mapped_column(String(32))
    andd_source: Mapped[str | None] = mapped_column(String(64), index=True)
    andd_provenance: Mapped[str | None] = mapped_column(Text)
    source_organism: Mapped[str | None] = mapped_column(String(128))

    # evidence & quality (spec §5, §28)
    evidence_flags: Mapped[list | None] = mapped_column(JSON)   # ["E4","E6"]
    quality_label: Mapped[str | None] = mapped_column(String(16), index=True)
    design_status: Mapped[str | None] = mapped_column(String(48), index=True)  # designed/tested/binder/...
    is_de_novo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    predicted_or_experimental: Mapped[str | None] = mapped_column(String(24))

    # verification flags (spec §28)
    sequence_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    target_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    structure_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    affinity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    publication_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # FKs
    target_id: Mapped[int | None] = mapped_column(ForeignKey("target.id"), index=True)
    antigen_id: Mapped[int | None] = mapped_column(ForeignKey("antigen_construct.id"))
    design_method_id: Mapped[int | None] = mapped_column(ForeignKey("design_method.id"), index=True)
    study_id: Mapped[int | None] = mapped_column(ForeignKey("study.id"))
    derived_from_id: Mapped[int | None] = mapped_column(ForeignKey("vhh.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    sequence: Mapped["Sequence"] = relationship(back_populates="vhh", uselist=False, cascade="all,delete")
    cdrs: Mapped[list["CDR"]] = relationship(back_populates="vhh", cascade="all,delete")
    physchem: Mapped["PhysChemProfile"] = relationship(back_populates="vhh", uselist=False, cascade="all,delete")
    developability: Mapped["DevelopabilityPrediction"] = relationship(back_populates="vhh", uselist=False, cascade="all,delete")
    target: Mapped["Target"] = relationship(back_populates="vhhs")
    antigen: Mapped["AntigenConstruct"] = relationship()
    design_method: Mapped["DesignMethod"] = relationship(back_populates="vhhs")
    study: Mapped["Study"] = relationship(back_populates="vhhs")
    affinities: Mapped[list["AffinityMeasurement"]] = relationship(back_populates="vhh", cascade="all,delete")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="vhh", cascade="all,delete")
    specificities: Mapped[list["Specificity"]] = relationship(back_populates="vhh", cascade="all,delete")
    structures: Mapped[list["Structure"]] = relationship(secondary="vhh_structure", back_populates="vhhs")
    epitopes: Mapped[list["Epitope"]] = relationship(back_populates="vhh", cascade="all,delete")
    provenance_events: Mapped[list["ProvenanceEvent"]] = relationship(cascade="all,delete")


class Sequence(Base):
    __tablename__ = "sequence"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    original_sequence: Mapped[str] = mapped_column(Text)          # exactly as disclosed (spec §8.6)
    normalized_sequence: Mapped[str] = mapped_column(Text, index=True)
    mature_sequence: Mapped[str | None] = mapped_column(Text)
    length: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(40), index=True)
    engineered_mutations: Mapped[str | None] = mapped_column(Text)
    vhh: Mapped["VHH"] = relationship(back_populates="sequence")


class CDR(Base):
    __tablename__ = "cdr"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    region: Mapped[str] = mapped_column(String(8))   # FR1/CDR1/FR2/CDR2/FR3/CDR3/FR4
    sequence: Mapped[str | None] = mapped_column(Text)
    length: Mapped[int | None] = mapped_column(Integer)
    numbering_scheme: Mapped[str | None] = mapped_column(String(24))   # IMGT / source
    source: Mapped[str | None] = mapped_column(String(32))            # ANDD / ANARCI
    imgt_positions: Mapped[str | None] = mapped_column(Text)
    vhh: Mapped["VHH"] = relationship(back_populates="cdrs")


class PhysChemProfile(Base):
    __tablename__ = "physchem_profile"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    length: Mapped[int | None] = mapped_column(Integer)
    molecular_weight: Mapped[float | None] = mapped_column(Float)
    theoretical_pi: Mapped[float | None] = mapped_column(Float)
    net_charge_ph7: Mapped[float | None] = mapped_column(Float)
    aa_composition: Mapped[dict | None] = mapped_column(JSON)
    cysteine_count: Mapped[int | None] = mapped_column(Integer)
    aromaticity: Mapped[float | None] = mapped_column(Float)
    aliphatic_index: Mapped[float | None] = mapped_column(Float)
    gravy: Mapped[float | None] = mapped_column(Float)
    extinction_coefficient: Mapped[int | None] = mapped_column(Integer)
    instability_index: Mapped[float | None] = mapped_column(Float)
    cdr3_length: Mapped[int | None] = mapped_column(Integer)
    cdr3_charge: Mapped[float | None] = mapped_column(Float)
    cdr3_hydrophobicity: Mapped[float | None] = mapped_column(Float)
    method: Mapped[str | None] = mapped_column(String(64))
    calc_version: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="physchem")


class DevelopabilityPrediction(Base):
    __tablename__ = "developability_prediction"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    liabilities: Mapped[dict | None] = mapped_column(JSON)   # motif -> count
    n_glyc_motifs: Mapped[int | None] = mapped_column(Integer)
    deamidation_sites: Mapped[int | None] = mapped_column(Integer)
    oxidation_sites: Mapped[int | None] = mapped_column(Integer)
    unusual_cysteine: Mapped[bool | None] = mapped_column(Boolean)
    surface_hydrophobicity: Mapped[float | None] = mapped_column(Float)
    method: Mapped[str | None] = mapped_column(String(64))
    calc_version: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="developability")


class Target(Base):
    __tablename__ = "target"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    gene_symbol: Mapped[str | None] = mapped_column(String(64))
    uniprot: Mapped[str | None] = mapped_column(String(32), index=True)
    organism: Mapped[str | None] = mapped_column(String(128))
    target_class: Mapped[str | None] = mapped_column(String(128))
    function: Mapped[str | None] = mapped_column(Text)
    disease_association: Mapped[str | None] = mapped_column(Text)
    target_sequence: Mapped[str | None] = mapped_column(Text)
    vhhs: Mapped[list["VHH"]] = relationship(back_populates="target")


class AntigenConstruct(Base):
    __tablename__ = "antigen_construct"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String(512))
    sequence: Mapped[str | None] = mapped_column(Text)
    source_organism: Mapped[str | None] = mapped_column(String(128))
    accession: Mapped[str | None] = mapped_column(String(64))
    target_id: Mapped[int | None] = mapped_column(ForeignKey("target.id"))
    target: Mapped["Target"] = relationship()


class Epitope(Base):
    __tablename__ = "epitope"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int | None] = mapped_column(ForeignKey("vhh.id"), index=True)
    antigen_id: Mapped[int | None] = mapped_column(ForeignKey("antigen_construct.id"))
    residue_range: Mapped[str | None] = mapped_column(String(128))
    residue_list: Mapped[str | None] = mapped_column(Text)
    epitope_sequence: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(String(24))   # linear/conformational
    evidence: Mapped[str | None] = mapped_column(String(24))  # experimental/computational
    source: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="epitopes")


class Structure(Base):
    __tablename__ = "structure"
    id: Mapped[int] = mapped_column(primary_key=True)
    pdb_id: Mapped[str] = mapped_column(String(8), index=True)
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=True)
    experimental_method: Mapped[str | None] = mapped_column(String(64))
    resolution: Mapped[float | None] = mapped_column(Float)
    title: Mapped[str | None] = mapped_column(Text)
    deposition_date: Mapped[str | None] = mapped_column(String(32))
    authors: Mapped[str | None] = mapped_column(Text)
    is_complex: Mapped[bool] = mapped_column(Boolean, default=False)
    model_source: Mapped[str | None] = mapped_column(String(64))   # for predicted
    model_version: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    chain_mapping: Mapped[dict | None] = mapped_column(JSON)
    pdb_pmid: Mapped[str | None] = mapped_column(String(16))
    pdb_doi: Mapped[str | None] = mapped_column(String(128))
    vhhs: Mapped[list["VHH"]] = relationship(secondary="vhh_structure", back_populates="structures")
    chains: Mapped[list["StructureChain"]] = relationship(back_populates="structure", cascade="all,delete")


class StructureChain(Base):
    __tablename__ = "structure_chain"
    id: Mapped[int] = mapped_column(primary_key=True)
    structure_id: Mapped[int] = mapped_column(ForeignKey("structure.id"), index=True)
    asym_id: Mapped[str | None] = mapped_column(String(8))
    auth_asym_id: Mapped[str | None] = mapped_column(String(8))
    role: Mapped[str | None] = mapped_column(String(24))    # VHH / antigen / light
    entity_id: Mapped[str | None] = mapped_column(String(8))
    macromolecule_name: Mapped[str | None] = mapped_column(Text)
    structure: Mapped["Structure"] = relationship(back_populates="chains")


class VHHStructure(Base):
    __tablename__ = "vhh_structure"
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), primary_key=True)
    structure_id: Mapped[int] = mapped_column(ForeignKey("structure.id"), primary_key=True)


class Experiment(Base):
    __tablename__ = "experiment"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    assay: Mapped[str | None] = mapped_column(String(64))
    tested: Mapped[bool | None] = mapped_column(Boolean)
    binder: Mapped[str | None] = mapped_column(String(16))   # Yes/No/Unknown
    functional: Mapped[str | None] = mapped_column(String(16))
    conditions: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="experiments")


class AffinityMeasurement(Base):
    __tablename__ = "affinity_measurement"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    kd_M: Mapped[float | None] = mapped_column(Float)
    kd_original: Mapped[str | None] = mapped_column(String(64))   # as-reported string
    kon: Mapped[float | None] = mapped_column(Float)
    koff: Mapped[float | None] = mapped_column(Float)
    ic50: Mapped[float | None] = mapped_column(Float)
    ec50: Mapped[float | None] = mapped_column(Float)
    ki: Mapped[float | None] = mapped_column(Float)
    delta_g_kJmol: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(16))
    method: Mapped[str | None] = mapped_column(String(64))
    temperature: Mapped[str | None] = mapped_column(String(32))
    buffer: Mapped[str | None] = mapped_column(Text)
    is_predicted: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="affinities")


class Specificity(Base):
    __tablename__ = "specificity"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int] = mapped_column(ForeignKey("vhh.id"), index=True)
    on_target: Mapped[str | None] = mapped_column(String(32))
    off_target: Mapped[str | None] = mapped_column(Text)
    cross_reactivity: Mapped[str | None] = mapped_column(Text)
    species_specificity: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(24))   # Strong/Weak/Negative/Not reported
    source: Mapped[str | None] = mapped_column(String(64))
    vhh: Mapped["VHH"] = relationship(back_populates="specificities")


class DesignMethod(Base):
    __tablename__ = "design_method"
    id: Mapped[int] = mapped_column(primary_key=True)
    method_class: Mapped[str] = mapped_column(String(32), index=True)  # computational/library/...
    method_name: Mapped[str] = mapped_column(String(128), index=True)
    software: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    vhhs: Mapped[list["VHH"]] = relationship(back_populates="design_method")


class DesignRun(Base):
    __tablename__ = "design_run"
    id: Mapped[int] = mapped_column(primary_key=True)
    design_method_id: Mapped[int | None] = mapped_column(ForeignKey("design_method.id"))
    n_designed: Mapped[int | None] = mapped_column(Integer)
    n_tested: Mapped[int | None] = mapped_column(Integer)
    n_validated: Mapped[int | None] = mapped_column(Integer)
    input_structure: Mapped[str | None] = mapped_column(String(64))
    constraints: Mapped[str | None] = mapped_column(Text)
    filtering: Mapped[str | None] = mapped_column(Text)
    ranking: Mapped[str | None] = mapped_column(Text)


class Study(Base):
    __tablename__ = "study"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    publication_id: Mapped[int | None] = mapped_column(ForeignKey("publication.id"))
    publication: Mapped["Publication"] = relationship()
    vhhs: Mapped[list["VHH"]] = relationship(back_populates="study")


class Publication(Base):
    __tablename__ = "publication"
    id: Mapped[int] = mapped_column(primary_key=True)
    pmid: Mapped[str | None] = mapped_column(String(16), index=True)
    pmcid: Mapped[str | None] = mapped_column(String(16))
    doi: Mapped[str | None] = mapped_column(String(128), index=True)
    title: Mapped[str | None] = mapped_column(Text)
    journal: Mapped[str | None] = mapped_column(String(256))
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    authors: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    disclosure_type: Mapped[str | None] = mapped_column(String(48))


class Patent(Base):
    __tablename__ = "patent"
    id: Mapped[int] = mapped_column(primary_key=True)
    patent_number: Mapped[str | None] = mapped_column(String(64), index=True)
    family: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str | None] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(Text)
    disclosure_date: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str | None] = mapped_column(String(64))


class Disease(Base):
    __tablename__ = "disease"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)


class Application(Base):
    __tablename__ = "application"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)


class Dataset(Base):
    __tablename__ = "dataset"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    release_version: Mapped[str | None] = mapped_column(String(24))
    n_records: Mapped[int | None] = mapped_column(Integer)
    formats: Mapped[list | None] = mapped_column(JSON)
    license: Mapped[str | None] = mapped_column(String(64))


class ProvenanceEvent(Base):
    """Field-level provenance (spec §27) and chronological timeline events (§19)."""
    __tablename__ = "provenance_event"
    id: Mapped[int] = mapped_column(primary_key=True)
    vhh_id: Mapped[int | None] = mapped_column(ForeignKey("vhh.id"), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(48))
    field: Mapped[str | None] = mapped_column(String(64))
    value: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(16))
    source_type: Mapped[str | None] = mapped_column(String(32))
    source_id: Mapped[str | None] = mapped_column(String(128))
    source_location: Mapped[str | None] = mapped_column(String(128))
    extraction_method: Mapped[str | None] = mapped_column(String(48))
    verification_status: Mapped[str | None] = mapped_column(String(24))
    event_type: Mapped[str | None] = mapped_column(String(48))    # for timeline
    event_year: Mapped[int | None] = mapped_column(Integer)


Index("ix_vhh_target_evidence", VHH.target_id, VHH.quality_label)
