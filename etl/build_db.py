"""Build the DeNovoVHH-DB SQLite database from ANDD (backbone) + RCSB/EuropePMC/
UniProt enrichment caches. Deduplicates by normalized sequence, assigns evidence
flags E0-E6, quality labels and design provenance, and writes field-level
provenance events. No value is invented.

Run:  python -m etl.build_db
Inputs (must exist): data/raw/ANDD_v2.xlsx, data/processed/{rcsb_meta,publications,uniprot_targets}.json
"""
import os, re, json, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import Counter, defaultdict
from app.db import engine, SessionLocal, init_db
from app.models import (Base, VHH, Sequence, CDR, PhysChemProfile, Target, AntigenConstruct,
                        Epitope, Structure, StructureChain, VHHStructure, Experiment,
                        AffinityMeasurement, Specificity, DesignMethod, Study, Publication,
                        Patent, Dataset, ProvenanceEvent)
from app.ontology import DESIGN_METHOD_KEYWORDS, NOT_REPORTED, CALC_TOOLS
from etl.common import (clean_str, normalize_seq, is_protein, checksum, physchem,
                        partition_fr_cdr, parse_kd_to_M, seq_charge, seq_hydrophobicity)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KD = ('Affinity_Kd(M), (the near-physiological conditions, with controlled temperatures '
      '(20-25 °C or 37 °C) and buffered aqueous systems)')
DG = '∆Gbinding(kJ/mol),(the near-equilibrium conditions at constant temperatures (20-25 °C) )'
UP = re.compile(r'^[OPQ][0-9][A-Z0-9]{3}[0-9]$|^[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}$')

DE_NOVO_SOURCES = ("novo", "generat", "paddlepaddle", "diffus")


def pdb_ids(v):
    out = []
    for p in re.split(r'[,;\s]+', str(v).strip().upper()):
        if len(p) == 4 and p.isalnum():
            out.append(p)
    return out


def accs(v):
    return [a for a in re.split(r'[,;\s]+', str(v).strip()) if UP.match(a)]


def design_from(sources, pubhits):
    """Return (class, name, software) from source label + mined publication hits.
    Prefers explicit computational evidence; else source; else Not reported."""
    text = " ".join(sources).lower()
    # publication-mined hits win when computational
    if pubhits:
        comp = [h for h in pubhits if h[0] == "computational"]
        if comp:
            return comp[0][0], comp[0][1], None
        return pubhits[0][0], pubhits[0][1], None
    if any(s in text for s in DE_NOVO_SOURCES):
        return "computational", "sequence-generation model", None
    if "patent" in text:
        return "unknown", NOT_REPORTED, None
    if "sabdab" in text or "sdab" in text or "pdb" in text or "plabdab" in text:
        return "natural", "immune repertoire", None
    return "unknown", NOT_REPORTED, None


def evidence_flags(has_struct, has_kd, has_binder, is_denovo, has_pub):
    f = []
    if is_denovo:
        f.append("E0" if not (has_struct or has_kd or has_binder) else "E1")
    if has_binder or has_kd:
        f.append("E2"); f.append("E3")
    if has_kd:
        f.append("E4")
    if has_struct:
        f.append("E6")
    return sorted(set(f)) or (["E1"] if is_denovo else ["E0"])


def quality(has_struct, has_kd, has_pub, seq_ok):
    if has_struct and has_kd and has_pub:
        return "High"
    if (has_struct or has_kd) and seq_ok:
        return "Moderate"
    if seq_ok:
        return "Low"
    return "Unresolved"


def design_status(has_struct, has_kd, has_binder, is_denovo):
    if has_kd or has_binder:
        return "binder (experimentally validated)"
    if is_denovo:
        return "designed (validation not located)"
    return "reported"


def build(limit=None):
    # fresh DB
    dbp = os.path.join(ROOT, "data", "denovovhh.sqlite")
    if os.path.exists(dbp):
        os.remove(dbp)
    init_db()
    s = SessionLocal()

    rcsb = json.load(open(os.path.join(ROOT, "data/processed/rcsb_meta.json")))
    pubs = json.load(open(os.path.join(ROOT, "data/processed/publications.json")))
    upt = json.load(open(os.path.join(ROOT, "data/processed/uniprot_targets.json")))

    andd = pd.read_excel(os.path.join(ROOT, "data/raw/ANDD_v2.xlsx"), sheet_name="Sheet3")
    nano = andd[andd['Ab_or_Nano'].astype(str).str.contains('nano', case=False, na=False)].copy()

    # --- caches to avoid duplicate rows ---
    target_cache = {}     # key -> Target
    antigen_cache = {}     # (name,acc) -> AntigenConstruct
    structure_cache = {}   # pdb -> Structure
    pub_cache = {}         # pmid -> Publication
    study_cache = {}       # pmid -> Study
    dm_cache = {}          # (class,name) -> DesignMethod

    def get_target(acc, name, organism):
        key = acc or (name and name.lower())
        if not key:
            return None
        if key in target_cache:
            return target_cache[key]
        t = Target(name=name or (upt.get(acc, {}).get("name")) or NOT_REPORTED)
        if acc and acc in upt:
            u = upt[acc]
            t.name = u.get("name") or t.name
            t.gene_symbol = u.get("gene")
            t.uniprot = acc
            t.organism = u.get("organism") or organism
            t.target_class = u.get("family")
            t.function = u.get("function")
        else:
            t.organism = organism
        s.add(t); target_cache[key] = t
        return t

    def get_antigen(name, seq, organism, acc, target):
        key = (name, acc, (seq or "")[:20])
        if key in antigen_cache:
            return antigen_cache[key]
        a = AntigenConstruct(name=name, sequence=seq, source_organism=organism,
                             accession=acc, target=target)
        s.add(a); antigen_cache[key] = a
        return a

    def get_structure(pdb):
        if pdb in structure_cache:
            return structure_cache[pdb]
        m = rcsb.get(pdb)
        st = Structure(pdb_id=pdb, is_experimental=True)
        if m:
            st.experimental_method = m.get("method")
            st.resolution = m.get("resolution")
            st.title = m.get("title")
            st.deposition_date = m.get("deposit_date")
            st.authors = "; ".join(m.get("authors") or []) or None
            st.pdb_pmid = str(m["pmid"]) if m.get("pmid") else None
            st.pdb_doi = m.get("doi")
        s.add(st); structure_cache[pdb] = st
        return st

    def get_pub(pmid):
        pmid = str(pmid)
        if pmid in pub_cache:
            return pub_cache[pmid]
        p = pubs.get(pmid)
        if not p:
            return None
        pub = Publication(pmid=pmid, pmcid=p.get("pmcid"), doi=p.get("doi"),
                          title=p.get("title"), journal=p.get("journal"),
                          year=int(p["year"]) if str(p.get("year") or "").isdigit() else None,
                          authors=p.get("authors"), abstract=p.get("abstract"),
                          disclosure_type="peer-reviewed article")
        s.add(pub); pub_cache[pmid] = pub
        return pub

    def get_study(pmid, pub):
        pmid = str(pmid)
        if pmid in study_cache:
            return study_cache[pmid]
        st = Study(title=pub.title if pub else None, year=pub.year if pub else None, publication=pub)
        s.add(st); study_cache[pmid] = st
        return st

    def get_dm(cls, name, software):
        key = (cls, name)
        if key in dm_cache:
            return dm_cache[key]
        d = DesignMethod(method_class=cls, method_name=name, software=software)
        s.add(d); dm_cache[key] = d
        return d

    # --- group by normalized sequence (dedup) ---
    nano["_seq"] = nano["Ab/Nano H_Chain AA"].map(normalize_seq)
    nano = nano[nano["_seq"].map(is_protein)]
    groups = nano.groupby("_seq", sort=False)
    total = len(groups)
    print(f"unique valid VHH sequences: {total}")

    counter = 0
    for seq, g in groups:
        counter += 1
        if limit and counter > limit:
            break
        rows = g.to_dict("records")
        r0 = rows[0]
        sources = sorted({clean_str(r.get("Source")) for r in rows if clean_str(r.get("Source"))})

        # antigen / target: most frequent non-null antigen name in group
        ag_names = [clean_str(r.get("Ag_Name")) for r in rows if clean_str(r.get("Ag_Name"))]
        primary_ag = Counter(ag_names).most_common(1)[0][0] if ag_names else None
        agrow = next((r for r in rows if clean_str(r.get("Ag_Name")) == primary_ag), r0)
        ag_acc_list = accs(agrow.get("Ag_Accession Code(s)") or "")
        ag_acc = ag_acc_list[0] if ag_acc_list else None
        ag_org = clean_str(agrow.get("Ag_Source Organism"))
        target = get_target(ag_acc, primary_ag, ag_org)
        antigen = get_antigen(primary_ag, clean_str(agrow.get("Ag_Seq")), ag_org, ag_acc, target) if primary_ag else None

        # structures across group
        pdbs = sorted({p for r in rows for p in pdb_ids(r.get("PDB_ID") or "")})
        has_struct = len(pdbs) > 0

        # affinity across group
        aff_specs = []
        for r in rows:
            kdM, kdo = parse_kd_to_M(r.get(KD))
            dgv = clean_str(r.get(DG))
            if kdM or dgv:
                try:
                    dgf = float(dgv) if dgv else None
                except ValueError:
                    dgf = None
                aff_specs.append((kdM, kdo, dgf, clean_str(r.get("Affinity_Method")),
                                  clean_str(r.get("Predicted_or_Not"))))
        # Measured affinity only: a KD counts toward the affinity evidence signal
        # (affinity_verified, quality tier, evidence flags, binder status) only when it
        # is an experimental measurement, never a predicted value. Predicted KDs are
        # still stored as AffinityMeasurement rows (is_predicted=True) and shown, labelled.
        has_kd = any(a[0] for a in aff_specs if (a[4] or "").lower() != "predicted")

        # publication: from any structure PMID in group
        pmid = next((str(rcsb[p]["pmid"]) for p in pdbs if p in rcsb and rcsb[p].get("pmid")), None)
        pub = get_pub(pmid) if pmid else None
        pubhits = pub and pubs.get(pmid, {}).get("design_hits")
        study = get_study(pmid, pub) if pmid else None
        has_pub = pub is not None

        is_denovo = any(any(x in (sc or "").lower() for x in DE_NOVO_SOURCES) for sc in sources)
        cls, dmname, sw = design_from(sources, pubhits)
        if cls == "computational":
            is_denovo = True
        dm = get_dm(cls, dmname, sw)

        predicted = any((a[4] or "").lower() == "predicted" for a in aff_specs)
        has_binder = has_kd
        flags = evidence_flags(has_struct, has_kd, has_binder, is_denovo, has_pub)
        seq_ok = is_protein(seq)

        v = VHH(
            denovovhh_id=f"DNVHH{counter:06d}",
            sdab_type="VHH",
            name=(f"Anti-{primary_ag} VHH" if primary_ag else None),
            source_ids={s_: None for s_ in sources},
            andd_source="; ".join(sources) or None,
            andd_provenance="; ".join(sorted({clean_str(r.get("Provenance")) for r in rows if clean_str(r.get("Provenance"))})) or None,
            source_organism=clean_str(r0.get("Source_Organism")),
            evidence_flags=flags,
            quality_label=quality(has_struct, has_kd, has_pub, seq_ok),
            design_status=design_status(has_struct, has_kd, has_binder, is_denovo),
            is_de_novo=is_denovo,
            predicted_or_experimental=clean_str(r0.get("Predicted_or_Not")),
            sequence_verified=seq_ok, structure_verified=has_struct,
            affinity_verified=has_kd, publication_verified=has_pub,
            target=target, antigen=antigen, design_method=dm, study=study,
        )
        s.add(v)

        # sequence
        v.sequence = Sequence(original_sequence=str(r0.get("Ab/Nano H_Chain AA")).strip(),
                              normalized_sequence=seq, length=len(seq), checksum=checksum(seq),
                              engineered_mutations=clean_str(r0.get("Ab/Nano_Mutation")))

        # CDRs: source (ANDD) + FR partition
        def cdr_clean(x):
            xs = normalize_seq(clean_str(x))
            return xs if (xs and is_protein(xs)) else None
        # pick the first row in the dedup group that actually provides CDRs
        crow = next((r for r in rows if cdr_clean(r.get("Ab/Nano_CDR H3"))), r0)
        c1 = cdr_clean(crow.get("Ab/Nano_CDR H1")); c2 = cdr_clean(crow.get("Ab/Nano_CDR H2")); c3 = cdr_clean(crow.get("Ab/Nano_CDR H3"))
        nomen = clean_str(crow.get("CDR Nomenclature")) or "source"
        for reg, cdr in [("CDR1", c1), ("CDR2", c2), ("CDR3", c3)]:
            if cdr:
                v.cdrs.append(CDR(region=reg, sequence=cdr, length=len(cdr),
                                  numbering_scheme=nomen, source="ANDD"))
        for reg, sub in partition_fr_cdr(seq, c1, c2, c3):
            if reg.startswith("FR") and sub:
                v.cdrs.append(CDR(region=reg, sequence=sub, length=len(sub),
                                  numbering_scheme=nomen, source="derived (substring boundary)"))

        # physchem
        pc = physchem(seq)
        if pc:
            v.physchem = PhysChemProfile(
                length=pc["length"], molecular_weight=pc["molecular_weight"],
                theoretical_pi=pc["theoretical_pi"], net_charge_ph7=pc["net_charge_ph7"],
                aa_composition=pc["aa_composition"], cysteine_count=pc["cysteine_count"],
                aromaticity=pc["aromaticity"], aliphatic_index=pc["aliphatic_index"],
                gravy=pc["gravy"], extinction_coefficient=pc["extinction_coefficient"],
                instability_index=pc["instability_index"],
                cdr3_length=len(c3) if c3 else None,
                cdr3_charge=seq_charge(c3), cdr3_hydrophobicity=seq_hydrophobicity(c3),
                method=pc["method"], calc_version=pc["calc_version"])

        # affinities
        for kdM, kdo, dgf, meth, predflag in aff_specs:
            v.affinities.append(AffinityMeasurement(
                kd_M=kdM, kd_original=kdo, delta_g_kJmol=dgf, unit="M",
                method=meth, is_predicted=(predflag or "").lower() == "predicted",
                source="ANDD"))

        # experiment
        v.experiments.append(Experiment(
            assay=clean_str(agrow.get("Affinity_Method")) or (NOT_REPORTED if not has_kd else "affinity"),
            tested=bool(has_kd or has_binder),
            binder=("Yes" if has_binder else ("Unknown")),
            source="; ".join(sources) or None))

        # specificity (only what is supported)
        v.specificities.append(Specificity(
            on_target=primary_ag or NOT_REPORTED,
            label=NOT_REPORTED, source="ANDD"))

        # structures + chains + complex flag + epitope shell
        for p in pdbs:
            st = get_structure(p)
            strow = next((r for r in rows if p in pdb_ids(r.get("PDB_ID") or "")), r0)
            st.is_complex = bool(strow.get("Complex_Structure"))
            if st not in v.structures:
                v.structures.append(st)
            # chains from ANDD chain mapping (H = VHH, Ag = antigen)
            hchain = clean_str(strow.get("H_Chain Auth Asym ID"))
            agchain = clean_str(strow.get("Ag_Auth Asym ID"))
            if hchain and not any(c.role == "VHH" and c.auth_asym_id == hchain for c in st.chains):
                st.chains.append(StructureChain(auth_asym_id=hchain, asym_id=clean_str(strow.get("H_Chain Asym ID")),
                                                role="VHH", entity_id=clean_str(strow.get("H_Chain Entity ID")),
                                                macromolecule_name=clean_str(strow.get("H_Chain Macromolecule Name"))))
            if agchain and not any(c.role == "antigen" and c.auth_asym_id == agchain for c in st.chains):
                st.chains.append(StructureChain(auth_asym_id=agchain, asym_id=clean_str(strow.get("Ag_Asym ID")),
                                                role="antigen", entity_id=clean_str(strow.get("Ag_Entity ID")),
                                                macromolecule_name=clean_str(strow.get("Ag_Name"))))

        # patents
        for sc in sources:
            if sc and "patent" in sc.lower():
                v.andd_provenance = (v.andd_provenance or "")
                s.add(Patent(patent_number=NOT_REPORTED, title=sc, source=sc))
                break

        # --- field-level provenance events ---
        def prov(field, value, stype, sid, loc, method, status, unit=None, etype=None, eyear=None):
            v.provenance_events.append(ProvenanceEvent(
                entity_type="VHH", field=field, value=(str(value)[:400] if value is not None else None),
                unit=unit, source_type=stype, source_id=sid, source_location=loc,
                extraction_method=method, verification_status=status, event_type=etype, event_year=eyear))

        prov("sequence", seq[:60] + "…", "dataset", "ANDD", "Zenodo:18151718", "download", "Experimental")
        if c3:
            prov("cdr3", c3, "dataset", "ANDD", "Zenodo:18151718", "download", "Curated")
        if pc:
            prov("physchem", "computed", "computed", CALC_TOOLS["physchem"], "in-house", "calculated", "Calculated")
        for p in pdbs:
            m = rcsb.get(p, {})
            prov("structure", p, "structure", p, "RCSB PDB", "api", "Experimental",
                 etype="structure deposited",
                 eyear=int((m.get("deposit_date") or "0")[:4]) if (m.get("deposit_date") or "")[:4].isdigit() else None)
        for kdM, kdo, dgf, meth, predflag in aff_specs:
            if kdM:
                prov("kd_M", kdo, "dataset", "ANDD", "Zenodo:18151718", "download",
                     "Experimental" if (predflag or "").lower() != "predicted" else "Predicted", unit="M")
        if pub:
            prov("publication", pub.pmid, "publication", "PMID:" + str(pub.pmid), "Europe PMC", "api", "Curated",
                 etype="first publication", eyear=pub.year)

        if counter % 2000 == 0:
            s.commit()
            print(f"  loaded {counter}/{total}", flush=True)

    # datasets registry
    s.add(Dataset(name="DeNovoVHH-DB Full", slug="full", release_version="v1.0",
                  description="All curated VHH/nanobody records with field-level provenance.",
                  formats=["csv", "tsv", "json", "fasta", "parquet", "sqlite"],
                  license="CC-BY-4.0 (ANDD-derived) + CC0 (PDB metadata)"))
    s.commit()
    n = s.query(VHH).count()
    print(f"DONE. VHH records: {n}")
    s.close()
    return n


if __name__ == "__main__":
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    build(limit=lim)
