"""Export services: FASTA, CSV, TSV, JSON, BibTeX, RIS, and full-dataset dumps.
Provenance and data-status are preserved in tabular exports."""
import io, csv, json, datetime
from app.models import VHH, Sequence, Structure, AffinityMeasurement
from app.serializers import vhh_full, vhh_brief

RELEASE = "v1.0"
SNAPSHOT = datetime.date.today().isoformat()

FLAT_COLUMNS = [
    "denovovhh_id", "name", "sdab_type", "sequence", "length", "cdr1", "cdr2", "cdr3",
    "cdr3_length", "target", "target_uniprot", "target_organism", "antigen",
    "molecular_weight", "theoretical_pi", "net_charge_ph7", "gravy",
    "best_kd_M", "affinity_method", "affinity_status",
    "design_class", "design_method", "design_status", "is_de_novo",
    "evidence_flags", "quality_label", "has_structure", "pdb_ids",
    "publication_pmid", "publication_doi", "source", "andd_provenance",
]


def _flat_row(v):
    cdrs = {c.region: c.sequence for c in v.cdrs}
    kd = min([a.kd_M for a in v.affinities if a.kd_M], default=None)
    aff = next((a for a in v.affinities if a.kd_M == kd), None) if kd else None
    return {
        "denovovhh_id": v.denovovhh_id, "name": v.name or "", "sdab_type": v.sdab_type,
        "sequence": v.sequence.normalized_sequence if v.sequence else "",
        "length": v.sequence.length if v.sequence else "",
        "cdr1": cdrs.get("CDR1", ""), "cdr2": cdrs.get("CDR2", ""), "cdr3": cdrs.get("CDR3", ""),
        "cdr3_length": len(cdrs["CDR3"]) if cdrs.get("CDR3") else "",
        "target": v.target.name if v.target else "Not reported",
        "target_uniprot": (v.target.uniprot if v.target else "") or "",
        "target_organism": (v.target.organism if v.target else "") or "",
        "antigen": v.antigen.name if v.antigen else "",
        "molecular_weight": v.physchem.molecular_weight if v.physchem else "",
        "theoretical_pi": v.physchem.theoretical_pi if v.physchem else "",
        "net_charge_ph7": v.physchem.net_charge_ph7 if v.physchem else "",
        "gravy": v.physchem.gravy if v.physchem else "",
        "best_kd_M": kd if kd else "",
        "affinity_method": (aff.method if aff else "") or "",
        "affinity_status": ("Predicted" if aff and aff.is_predicted else ("Experimental" if aff else "Not reported")),
        "design_class": v.design_method.method_class if v.design_method else "",
        "design_method": v.design_method.method_name if v.design_method else "Not reported",
        "design_status": v.design_status or "", "is_de_novo": v.is_de_novo,
        "evidence_flags": "|".join(v.evidence_flags or []),
        "quality_label": v.quality_label or "",
        "has_structure": v.structure_verified,
        "pdb_ids": ";".join(sorted(st.pdb_id for st in v.structures)),
        "publication_pmid": (v.study.publication.pmid if v.study and v.study.publication else "") or "",
        "publication_doi": (v.study.publication.doi if v.study and v.study.publication else "") or "",
        "source": v.andd_source or "", "andd_provenance": v.andd_provenance or "",
    }


def to_delimited(vhhs, delim=","):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FLAT_COLUMNS, delimiter=delim, extrasaction="ignore")
    w.writeheader()
    for v in vhhs:
        w.writerow(_flat_row(v))
    return buf.getvalue()


def to_fasta(vhhs):
    out = []
    for v in vhhs:
        if not v.sequence:
            continue
        tgt = v.target.name if v.target else "Not reported"
        out.append(f">{v.denovovhh_id} | {v.name or 'VHH'} | target={tgt} | "
                   f"evidence={'|'.join(v.evidence_flags or [])} | quality={v.quality_label}")
        seq = v.sequence.normalized_sequence
        for i in range(0, len(seq), 60):
            out.append(seq[i:i+60])
    return "\n".join(out) + "\n"


def to_json(vhhs, full=False):
    fn = vhh_full if full else vhh_brief
    payload = {
        "database": "DeNovoVHH-DB", "release": RELEASE, "snapshot_date": SNAPSHOT,
        "license": "CC-BY-4.0 (ANDD-derived data) + CC0 (PDB metadata); see docs",
        "citation": "DeNovoVHH-DB v1.0. Derived from ANDD (Zenodo 18151718, CC-BY-4.0), "
                    "RCSB PDB, UniProt, Europe PMC. See docs/CITATION.",
        "count": len(vhhs), "records": [fn(v) for v in vhhs],
    }
    return json.dumps(payload, indent=2, default=str)


def to_bibtex(v):
    p = v.study.publication if v.study else None
    if not p:
        return f"% No publication on record for {v.denovovhh_id}\n"
    key = (p.authors or "Anon").split(",")[0].split()[0] + str(p.year or "")
    return ("@article{" + key + ",\n"
            f"  title = {{{p.title or 'Not reported'}}},\n"
            f"  author = {{{p.authors or 'Not reported'}}},\n"
            f"  journal = {{{p.journal or 'Not reported'}}},\n"
            f"  year = {{{p.year or 'Not reported'}}},\n"
            f"  doi = {{{p.doi or ''}}},\n"
            f"  pmid = {{{p.pmid or ''}}}\n}}\n")


def to_ris(v):
    p = v.study.publication if v.study else None
    if not p:
        return f"TY  - GEN\nTI  - No publication on record for {v.denovovhh_id}\nER  -\n"
    lines = ["TY  - JOUR", f"TI  - {p.title or 'Not reported'}"]
    for a in (p.authors or "").split(", "):
        if a:
            lines.append(f"AU  - {a}")
    lines += [f"JO  - {p.journal or ''}", f"PY  - {p.year or ''}",
              f"DO  - {p.doi or ''}", f"AN  - {p.pmid or ''}", "ER  -"]
    return "\n".join(lines) + "\n"
