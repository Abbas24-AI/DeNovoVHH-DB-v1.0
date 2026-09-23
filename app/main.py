"""DeNovoVHH-DB FastAPI application: JSON API (/api/v1), downloads, and
server-rendered academic web UI. Run:  uvicorn app.main:app --reload
"""
import os, io, zipfile, datetime
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import (JSONResponse, PlainTextResponse, StreamingResponse,
                               HTMLResponse, Response)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (VHH, Target, Structure, Publication, DesignMethod, Dataset,
                        AffinityMeasurement)
from app import repository as repo
from app import serializers as ser
from app import exports as exp
from app.ontology import EVIDENCE_HIERARCHY, DESIGN_TAXONOMY, DATA_STATUS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = FastAPI(title="DeNovoVHH-DB API", version="1.0",
              description="Academic database of designed & validated single-domain "
                          "antibodies (VHH/nanobodies) with full field-level provenance. "
                          "No values are fabricated; absent data is 'Not reported'.")

templates = Jinja2Templates(directory=os.path.join(ROOT, "app", "templates"))
_static = os.path.join(ROOT, "app", "static")
if os.path.isdir(_static):
    app.mount("/static", StaticFiles(directory=_static), name="static")


def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


# ------------------------ shared filter parsing ------------------------
def _bool(x):
    if x is None:
        return None
    return str(x).lower() in ("1", "true", "yes", "y")


def _collect_filters(**kw):
    return {k: v for k, v in kw.items() if v is not None}


# ============================ JSON API ============================
@app.get("/api/v1/vhh")
def api_vhh_list(
    s: Session = Depends(db),
    q: str = None, target: str = None, uniprot: str = None, organism: str = None,
    design_class: str = None, quality: str = None, evidence: str = None,
    sdab_type: str = None, has_structure: str = None, has_affinity: str = None,
    is_de_novo: str = None, kd_max: float = None, kd_min: float = None,
    length_min: int = None, length_max: int = None, cdr3: str = None,
    cdr3_len_min: int = None, cdr3_len_max: int = None,
    page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=500),
    sort: str = "id", order: str = "asc",
):
    query = repo.filter_vhh(
        s, q=q, target=target, uniprot=uniprot, organism=organism,
        design_class=design_class, quality=quality, evidence=evidence,
        sdab_type=sdab_type, has_structure=_bool(has_structure),
        has_affinity=_bool(has_affinity), is_de_novo=_bool(is_de_novo),
        kd_max=kd_max, kd_min=kd_min, length_min=length_min, length_max=length_max,
        cdr3=cdr3, cdr3_len_min=cdr3_len_min, cdr3_len_max=cdr3_len_max)
    total, rows = repo.paginate(query, page, size, sort, order)
    return {"count": total, "page": page, "size": size,
            "pages": (total + size - 1) // size,
            "results": [ser.vhh_brief(v) for v in rows]}


@app.get("/api/v1/vhh/{ident}")
def api_vhh_detail(ident: str, s: Session = Depends(db)):
    v = repo.get_vhh(s, ident)
    if not v:
        raise HTTPException(404, "VHH not found")
    return ser.vhh_full(v)


@app.get("/api/v1/vhh/{ident}/sequence")
def api_vhh_sequence(ident: str, s: Session = Depends(db)):
    v = repo.get_vhh(s, ident)
    if not v:
        raise HTTPException(404, "VHH not found")
    return PlainTextResponse(exp.to_fasta([v]))


@app.get("/api/v1/vhh/{ident}/provenance")
def api_vhh_prov(ident: str, s: Session = Depends(db)):
    v = repo.get_vhh(s, ident)
    if not v:
        raise HTTPException(404, "VHH not found")
    return ser.vhh_full(v)["provenance"]


@app.get("/api/v1/targets")
def api_targets(s: Session = Depends(db), q: str = None,
                page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=500)):
    query = s.query(Target)
    if q:
        query = query.filter(Target.name.ilike(f"%{q}%"))
    total = query.count()
    rows = query.order_by(Target.name).offset((page-1)*size).limit(size).all()
    return {"count": total, "results": [ser.target_brief(t) for t in rows]}


@app.get("/api/v1/structures")
def api_structures(s: Session = Depends(db), q: str = None,
                   page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=500)):
    query = s.query(Structure)
    if q:
        query = query.filter(Structure.pdb_id.ilike(f"%{q}%") | Structure.title.ilike(f"%{q}%"))
    total = query.count()
    rows = query.order_by(Structure.pdb_id).offset((page-1)*size).limit(size).all()
    return {"count": total, "results": [ser.structure_brief(x) for x in rows]}


@app.get("/api/v1/publications")
def api_publications(s: Session = Depends(db), q: str = None,
                     page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=500)):
    query = s.query(Publication)
    if q:
        query = query.filter(Publication.title.ilike(f"%{q}%"))
    total = query.count()
    rows = query.order_by(Publication.year.desc()).offset((page-1)*size).limit(size).all()
    return {"count": total, "results": [ser.publication_brief(p) for p in rows]}


@app.get("/api/v1/design-methods")
def api_design_methods(s: Session = Depends(db)):
    from sqlalchemy import func
    rows = (s.query(DesignMethod, func.count(VHH.id))
            .outerjoin(VHH, VHH.design_method_id == DesignMethod.id)
            .group_by(DesignMethod.id).all())
    return {"results": [{"method_class": d.method_class, "method_name": d.method_name,
                         "software": d.software, "n_vhh": n} for d, n in rows]}


@app.get("/api/v1/datasets")
def api_datasets(s: Session = Depends(db)):
    return {"results": [{"name": d.name, "slug": d.slug, "release_version": d.release_version,
                         "formats": d.formats, "license": d.license,
                         "description": d.description} for d in s.query(Dataset).all()]}


@app.get("/api/v1/stats")
def api_stats(s: Session = Depends(db)):
    return repo.stats(s)


@app.get("/api/v1/ontology")
def api_ontology():
    return {"evidence_hierarchy": EVIDENCE_HIERARCHY, "design_taxonomy": DESIGN_TAXONOMY,
            "data_status": DATA_STATUS}


# ============================ Downloads ============================
def _filtered(s, params):
    query = repo.filter_vhh(s, **params)
    return repo._eager(query).all()


@app.get("/api/v1/download/{fmt}")
def download(fmt: str, s: Session = Depends(db),
             q: str = None, target: str = None, design_class: str = None,
             quality: str = None, has_structure: str = None, has_affinity: str = None,
             is_de_novo: str = None, limit: int = Query(None, le=30000)):
    params = _collect_filters(q=q, target=target, design_class=design_class, quality=quality,
                              has_structure=_bool(has_structure), has_affinity=_bool(has_affinity),
                              is_de_novo=_bool(is_de_novo))
    query = repo.filter_vhh(s, **params)
    query = repo._eager(query.order_by(VHH.denovovhh_id))
    if limit:
        query = query.limit(limit)
    rows = query.all()
    stamp = f"denovovhh_{exp.RELEASE}_{exp.SNAPSHOT}"
    if fmt == "csv":
        return PlainTextResponse(exp.to_delimited(rows, ","), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename={stamp}.csv"})
    if fmt == "tsv":
        return PlainTextResponse(exp.to_delimited(rows, "\t"), media_type="text/tab-separated-values",
                                 headers={"Content-Disposition": f"attachment; filename={stamp}.tsv"})
    if fmt == "fasta":
        return PlainTextResponse(exp.to_fasta(rows), media_type="text/plain",
                                 headers={"Content-Disposition": f"attachment; filename={stamp}.fasta"})
    if fmt == "json":
        return PlainTextResponse(exp.to_json(rows, full=False), media_type="application/json",
                                 headers={"Content-Disposition": f"attachment; filename={stamp}.json"})
    raise HTTPException(400, f"Unsupported format: {fmt}. Use csv|tsv|fasta|json.")


@app.get("/api/v1/vhh/{ident}/cite.{fmt}")
def cite(ident: str, fmt: str, s: Session = Depends(db)):
    v = repo.get_vhh(s, ident)
    if not v:
        raise HTTPException(404, "VHH not found")
    if fmt == "bib":
        return PlainTextResponse(exp.to_bibtex(v), media_type="application/x-bibtex")
    if fmt == "ris":
        return PlainTextResponse(exp.to_ris(v), media_type="application/x-research-info-systems")
    raise HTTPException(400, "Use bib|ris")


@app.get("/api/v1/vhh/{ident}.json")
def record_json(ident: str, s: Session = Depends(db)):
    v = repo.get_vhh(s, ident)
    if not v:
        raise HTTPException(404, "VHH not found")
    return Response(exp.to_json([v], full=True), media_type="application/json",
                    headers={"Content-Disposition": f"attachment; filename={v.denovovhh_id}.json"})


from app.web import register_web  # noqa: E402
register_web(app, templates, db)
