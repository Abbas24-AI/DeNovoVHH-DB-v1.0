"""Query helpers: server-side filtering, sorting, pagination, Boolean search.
All read-only. Returns ORM objects; serialization happens in serializers.py."""
from sqlalchemy import or_, and_, func, select
from sqlalchemy.orm import selectinload, joinedload
from app.models import (VHH, Sequence, CDR, PhysChemProfile, Target, AntigenConstruct,
                        Structure, AffinityMeasurement, DesignMethod, Study, Publication)

_LOADERS = (
    selectinload(VHH.sequence), selectinload(VHH.cdrs), selectinload(VHH.physchem),
    selectinload(VHH.target), selectinload(VHH.antigen), selectinload(VHH.affinities),
    selectinload(VHH.experiments), selectinload(VHH.specificities),
    selectinload(VHH.structures).selectinload(Structure.chains),
    selectinload(VHH.design_method), selectinload(VHH.provenance_events),
    selectinload(VHH.study).selectinload(Study.publication),
)


def _eager(q):
    return q.options(*_LOADERS)


def filter_vhh(s, *, q=None, target=None, uniprot=None, organism=None,
               design_class=None, quality=None, evidence=None, sdab_type=None,
               has_structure=None, has_affinity=None, is_de_novo=None,
               kd_max=None, kd_min=None, length_min=None, length_max=None,
               cdr3=None, cdr3_len_min=None, cdr3_len_max=None):
    query = s.query(VHH)
    joins = set()

    def j(model, cond):
        if model not in joins:
            nonlocal query
            query = query.join(model, cond)
            joins.add(model)

    if q:
        like = f"%{q}%"
        query = (query.outerjoin(Target, VHH.target_id == Target.id)
                      .outerjoin(Sequence, VHH.id == Sequence.vhh_id))
        joins.update({Target, Sequence})
        query = query.filter(or_(
            VHH.denovovhh_id.ilike(like), VHH.name.ilike(like),
            VHH.andd_source.ilike(like), Target.name.ilike(like),
            Target.uniprot.ilike(like), Sequence.normalized_sequence.ilike(like),
        ))
    if target:
        if Target not in joins:
            query = query.join(Target, VHH.target_id == Target.id); joins.add(Target)
        query = query.filter(Target.name.ilike(f"%{target}%"))
    if uniprot:
        if Target not in joins:
            query = query.join(Target, VHH.target_id == Target.id); joins.add(Target)
        query = query.filter(Target.uniprot == uniprot)
    if organism:
        query = query.filter(VHH.source_organism.ilike(f"%{organism}%"))
    if design_class:
        query = query.join(DesignMethod, VHH.design_method_id == DesignMethod.id)
        joins.add(DesignMethod)
        query = query.filter(DesignMethod.method_class == design_class)
    if quality:
        query = query.filter(VHH.quality_label == quality)
    if evidence:
        query = query.filter(VHH.evidence_flags.contains(evidence))
    if sdab_type:
        query = query.filter(VHH.sdab_type == sdab_type)
    if has_structure is not None:
        query = query.filter(VHH.structure_verified == has_structure)
    if has_affinity is not None:
        query = query.filter(VHH.affinity_verified == has_affinity)
    if is_de_novo is not None:
        query = query.filter(VHH.is_de_novo == is_de_novo)
    if cdr3 or cdr3_len_min or cdr3_len_max:
        query = query.join(CDR, and_(CDR.vhh_id == VHH.id, CDR.region == "CDR3"))
        if cdr3:
            query = query.filter(CDR.sequence.ilike(f"%{cdr3}%"))
        if cdr3_len_min:
            query = query.filter(CDR.length >= cdr3_len_min)
        if cdr3_len_max:
            query = query.filter(CDR.length <= cdr3_len_max)
    if length_min or length_max:
        if Sequence not in joins:
            query = query.join(Sequence, VHH.id == Sequence.vhh_id); joins.add(Sequence)
        if length_min:
            query = query.filter(Sequence.length >= length_min)
        if length_max:
            query = query.filter(Sequence.length <= length_max)
    if kd_max or kd_min:
        query = query.join(AffinityMeasurement, VHH.id == AffinityMeasurement.vhh_id)
        query = query.filter(AffinityMeasurement.kd_M.isnot(None))
        if kd_max:
            query = query.filter(AffinityMeasurement.kd_M <= kd_max)
        if kd_min:
            query = query.filter(AffinityMeasurement.kd_M >= kd_min)
    return query.distinct()


# All four keys are wired in paginate(); "length"/"target" use correlated
# scalar subqueries (see paginate) rather than direct columns.
SORTS = ("id", "length", "quality", "target")


def paginate(query, page, size, sort="id", order="asc"):
    total = query.count()
    if sort == "quality":
        col = VHH.quality_label
    elif sort == "length":
        # correlated scalar subquery avoids join duplication with active filters
        col = select(Sequence.length).where(Sequence.vhh_id == VHH.id).scalar_subquery()
    elif sort == "target":
        col = select(Target.name).where(Target.id == VHH.target_id).scalar_subquery()
    else:
        col = VHH.denovovhh_id
    q = query.order_by(col.desc() if order == "desc" else col.asc())
    q = _eager(q).offset((page - 1) * size).limit(size)
    return total, q.all()


def get_vhh(s, ident):
    q = _eager(s.query(VHH))
    if str(ident).isdigit():
        return q.filter(VHH.id == int(ident)).first()
    return q.filter(VHH.denovovhh_id == ident).first()


def stats(s):
    out = {
        "n_vhh": s.query(VHH).count(),
        "n_with_structure": s.query(VHH).filter(VHH.structure_verified == True).count(),
        "n_with_affinity": s.query(VHH).filter(VHH.affinity_verified == True).count(),
        "n_de_novo": s.query(VHH).filter(VHH.is_de_novo == True).count(),
        "n_with_publication": s.query(VHH).filter(VHH.publication_verified == True).count(),
        "n_targets": s.query(Target).count(),
        "n_structures": s.query(Structure).count(),
        "n_publications": s.query(Publication).count(),
        "n_affinities": s.query(AffinityMeasurement).count(),
        "quality": dict(s.query(VHH.quality_label, func.count()).group_by(VHH.quality_label).all()),
        "design_class": dict(s.query(DesignMethod.method_class, func.count(VHH.id))
                             .join(VHH, VHH.design_method_id == DesignMethod.id)
                             .group_by(DesignMethod.method_class).all()),
    }
    return out
