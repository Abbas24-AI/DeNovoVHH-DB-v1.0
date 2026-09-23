"""ORM -> dict serializers. Absent values surface as null; the frontend renders
null as 'Not reported'. Original vs calculated values are kept distinct."""

NR = "Not reported"


def _prov(v):
    return [{
        "field": p.field, "value": p.value, "unit": p.unit,
        "source_type": p.source_type, "source_id": p.source_id,
        "source_location": p.source_location, "extraction_method": p.extraction_method,
        "verification_status": p.verification_status,
        "event_type": p.event_type, "event_year": p.event_year,
    } for p in v.provenance_events]


def vhh_brief(v):
    return {
        "id": v.id,
        "denovovhh_id": v.denovovhh_id,
        "name": v.name,
        "sdab_type": v.sdab_type,
        "target": v.target.name if v.target else None,
        "target_uniprot": v.target.uniprot if v.target else None,
        "organism": v.source_organism,
        "length": v.sequence.length if v.sequence else None,
        "cdr3": next((c.sequence for c in v.cdrs if c.region == "CDR3"), None),
        "evidence_flags": v.evidence_flags,
        "quality_label": v.quality_label,
        "design_status": v.design_status,
        "design_class": v.design_method.method_class if v.design_method else None,
        "is_de_novo": v.is_de_novo,
        "has_structure": v.structure_verified,
        "has_affinity": v.affinity_verified,
        "best_kd_M": min([a.kd_M for a in v.affinities if a.kd_M], default=None),
        "n_structures": len(v.structures),
        "source": v.andd_source,
    }


def vhh_full(v):
    d = vhh_brief(v)
    seq = v.sequence
    d.update({
        "sequence": {
            "original": seq.original_sequence if seq else None,
            "normalized": seq.normalized_sequence if seq else None,
            "length": seq.length if seq else None,
            "checksum_sha1": seq.checksum if seq else None,
            "engineered_mutations": seq.engineered_mutations if seq else None,
        } if seq else None,
        "cdrs": [{"region": c.region, "sequence": c.sequence, "length": c.length,
                  "numbering_scheme": c.numbering_scheme, "source": c.source}
                 for c in sorted(v.cdrs, key=lambda x: x.region)],
        "physchem": ({
            "molecular_weight": v.physchem.molecular_weight,
            "theoretical_pi": v.physchem.theoretical_pi,
            "net_charge_ph7": v.physchem.net_charge_ph7,
            "gravy": v.physchem.gravy,
            "aromaticity": v.physchem.aromaticity,
            "aliphatic_index": v.physchem.aliphatic_index,
            "instability_index": v.physchem.instability_index,
            "extinction_coefficient": v.physchem.extinction_coefficient,
            "cysteine_count": v.physchem.cysteine_count,
            "cdr3_length": v.physchem.cdr3_length,
            "cdr3_charge": v.physchem.cdr3_charge,
            "cdr3_hydrophobicity": v.physchem.cdr3_hydrophobicity,
            "aa_composition": v.physchem.aa_composition,
            "method": v.physchem.method,
            "calc_version": v.physchem.calc_version,
        } if v.physchem else None),
        "target": ({
            "name": v.target.name, "gene_symbol": v.target.gene_symbol,
            "uniprot": v.target.uniprot, "organism": v.target.organism,
            "target_class": v.target.target_class, "function": v.target.function,
        } if v.target else None),
        "antigen": ({
            "name": v.antigen.name, "accession": v.antigen.accession,
            "source_organism": v.antigen.source_organism,
            "has_sequence": bool(v.antigen.sequence),
        } if v.antigen else None),
        "affinities": [{
            "kd_M": a.kd_M, "kd_original": a.kd_original, "unit": a.unit,
            "delta_g_kJmol": a.delta_g_kJmol, "method": a.method,
            "is_predicted": a.is_predicted, "source": a.source,
        } for a in v.affinities],
        "experiments": [{
            "assay": e.assay, "tested": e.tested, "binder": e.binder, "source": e.source,
        } for e in v.experiments],
        "specificities": [{
            "on_target": sp.on_target, "label": sp.label, "source": sp.source,
        } for sp in v.specificities],
        "structures": [{
            "pdb_id": st.pdb_id, "method": st.experimental_method,
            "resolution": st.resolution, "title": st.title,
            "deposition_date": st.deposition_date, "is_complex": st.is_complex,
            "pdb_pmid": st.pdb_pmid, "pdb_doi": st.pdb_doi,
            "authors": st.authors,
            "chains": [{"auth_asym_id": c.auth_asym_id, "role": c.role,
                        "macromolecule_name": c.macromolecule_name} for c in st.chains],
        } for st in v.structures],
        "design_method": ({
            "method_class": v.design_method.method_class,
            "method_name": v.design_method.method_name,
            "software": v.design_method.software,
        } if v.design_method else None),
        "publication": ({
            "pmid": v.study.publication.pmid, "pmcid": v.study.publication.pmcid,
            "doi": v.study.publication.doi, "title": v.study.publication.title,
            "journal": v.study.publication.journal, "year": v.study.publication.year,
            "authors": v.study.publication.authors,
            "disclosure_type": v.study.publication.disclosure_type,
        } if v.study and v.study.publication else None),
        "provenance": _prov(v),
        "andd_provenance": v.andd_provenance,
        "flags": {
            "sequence_verified": v.sequence_verified,
            "structure_verified": v.structure_verified,
            "affinity_verified": v.affinity_verified,
            "publication_verified": v.publication_verified,
            "predicted_or_experimental": v.predicted_or_experimental,
        },
    })
    return d


def target_brief(t):
    return {"id": t.id, "name": t.name, "gene_symbol": t.gene_symbol,
            "uniprot": t.uniprot, "organism": t.organism,
            "target_class": t.target_class, "n_vhh": len(t.vhhs)}


def structure_brief(st):
    return {"pdb_id": st.pdb_id, "method": st.experimental_method,
            "resolution": st.resolution, "title": st.title,
            "is_complex": st.is_complex, "pdb_pmid": st.pdb_pmid, "pdb_doi": st.pdb_doi,
            "n_vhh": len(st.vhhs)}


def publication_brief(p):
    return {"pmid": p.pmid, "doi": p.doi, "title": p.title, "journal": p.journal,
            "year": p.year, "authors": p.authors, "disclosure_type": p.disclosure_type,
            "pmcid": p.pmcid}
