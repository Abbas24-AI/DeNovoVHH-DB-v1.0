"""Server-rendered HTML routes (academic UI). Registered onto the app."""
from fastapi import Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import SessionLocal
from app.models import (VHH, Target, Structure, Publication, DesignMethod, Dataset,
                        AffinityMeasurement, CDR)
from app import repository as repo
from app import serializers as ser
from app.ontology import EVIDENCE_HIERARCHY, DESIGN_TAXONOMY, DATA_STATUS


def register_web(app, templates, db):

    def ctx(request, **kw):
        base = {"request": request, "brand": "DeNovoVHH-DB"}
        base.update(kw)
        return base

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request, s: Session = Depends(db)):
        import math
        st = repo.stats(s)
        featured = (repo._eager(s.query(VHH).filter(VHH.quality_label == "High"))
                    .order_by(VHH.denovovhh_id).limit(6).all())
        top_targets = (s.query(Target, func.count(VHH.id).label("n"))
                       .join(VHH, VHH.target_id == Target.id)
                       .group_by(Target.id).order_by(func.count(VHH.id).desc()).limit(8).all())
        top_targets = [(t.name, t.uniprot, n) for t, n in top_targets]

        # --- Donut: design-provenance distribution (real counts; records with no
        #     design method are shown honestly as "Unknown"), never fabricated. ---
        colors = {"computational": "#6b3fa0", "natural": "#0e7c86", "library": "#2f6fb0",
                  "engineering": "#a86a15", "unknown": "#9aa7b4"}
        dc = dict(st["design_class"])
        classified = sum(dc.values())
        unknown = max(st["n_vhh"] - classified, 0)
        if unknown:
            dc["unknown"] = dc.get("unknown", 0) + unknown
        total = sum(dc.values()) or 1
        R = 52.0
        C = 2 * math.pi * R
        donut, cum = [], 0.0
        for label in ["computational", "natural", "library", "engineering", "unknown"]:
            n = dc.get(label, 0)
            if not n:
                continue
            frac = n / total
            donut.append({
                "label": label, "n": n, "pct": round(frac * 100, 1),
                "color": colors.get(label, "#9aa7b4"),
                "dash": f"{frac * C:.2f} {C - frac * C:.2f}",
                "offset": f"{-cum * C:.2f}",
            })
            cum += frac

        # --- Top-targets max for bar scaling ---
        tt_max = max((n for _, _, n in top_targets), default=1)

        return templates.TemplateResponse(request, "home.html", ctx(
            request, stats=st, featured=[ser.vhh_brief(v) for v in featured],
            top_targets=top_targets, tt_max=tt_max,
            donut=donut, donut_C=round(C, 2)))

    @app.get("/browse", response_class=HTMLResponse)
    def browse(request: Request, s: Session = Depends(db),
               q: str = None, target: str = None, design_class: str = None,
               quality: str = None, evidence: str = None, has_structure: str = None,
               has_affinity: str = None, is_de_novo: str = None,
               page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=200),
               sort: str = "id", order: str = "asc"):
        from app.main import _bool
        params = dict(q=q, target=target, design_class=design_class, quality=quality,
                      evidence=evidence, has_structure=_bool(has_structure),
                      has_affinity=_bool(has_affinity), is_de_novo=_bool(is_de_novo))
        query = repo.filter_vhh(s, **{k: v for k, v in params.items() if v is not None})
        total, rows = repo.paginate(query, page, size, sort, order)
        design_classes = [c for c, in s.query(DesignMethod.method_class).distinct().all()]
        return templates.TemplateResponse(request, "browse.html", ctx(
            request, results=[ser.vhh_brief(v) for v in rows], total=total, page=page,
            size=size, pages=(total + size - 1)//size, params=params,
            design_classes=sorted(design_classes),
            qualities=["High", "Moderate", "Low", "Unresolved"],
            evidences=list(EVIDENCE_HIERARCHY.keys()), sort=sort, order=order))

    @app.get("/search", response_class=HTMLResponse)
    def search(request: Request, s: Session = Depends(db)):
        return templates.TemplateResponse(request, "search.html", ctx(
            request, design_taxonomy=DESIGN_TAXONOMY,
            evidences=EVIDENCE_HIERARCHY, data_status=DATA_STATUS))

    @app.get("/vhh/{ident}", response_class=HTMLResponse)
    def vhh_detail(ident: str, request: Request, s: Session = Depends(db)):
        v = repo.get_vhh(s, ident)
        if not v:
            raise HTTPException(404, "VHH not found")
        return templates.TemplateResponse(request, "vhh_detail.html", ctx(
            request, v=ser.vhh_full(v), evidence_desc=EVIDENCE_HIERARCHY))

    @app.get("/targets", response_class=HTMLResponse)
    def targets(request: Request, s: Session = Depends(db), q: str = None,
                page: int = Query(1, ge=1), size: int = 50):
        query = s.query(Target, func.count(VHH.id).label("n")).outerjoin(
            VHH, VHH.target_id == Target.id).group_by(Target.id)
        if q:
            query = query.filter(Target.name.ilike(f"%{q}%"))
        query = query.order_by(func.count(VHH.id).desc())
        total = query.count()
        rows = query.offset((page-1)*size).limit(size).all()
        return templates.TemplateResponse(request, "targets.html", ctx(
            request, rows=[(t, n) for t, n in rows], total=total, page=page,
            size=size, pages=(total+size-1)//size, q=q or ""))

    @app.get("/target/{tid}", response_class=HTMLResponse)
    def target_detail(tid: int, request: Request, s: Session = Depends(db)):
        t = s.query(Target).filter(Target.id == tid).first()
        if not t:
            raise HTTPException(404, "Target not found")
        vhhs = repo._eager(s.query(VHH).filter(VHH.target_id == tid)).limit(200).all()
        return templates.TemplateResponse(request, "target_detail.html", ctx(
            request, t=t, vhhs=[ser.vhh_brief(v) for v in vhhs], n=len(t.vhhs)))

    @app.get("/structures", response_class=HTMLResponse)
    def structures(request: Request, s: Session = Depends(db), q: str = None,
                   page: int = Query(1, ge=1), size: int = 50):
        query = s.query(Structure)
        if q:
            query = query.filter(Structure.pdb_id.ilike(f"%{q}%") | Structure.title.ilike(f"%{q}%"))
        query = query.order_by(Structure.pdb_id)
        total = query.count()
        rows = query.offset((page-1)*size).limit(size).all()
        return templates.TemplateResponse(request, "structures.html", ctx(
            request, rows=[ser.structure_brief(x) for x in rows], total=total,
            page=page, size=size, pages=(total+size-1)//size, q=q or ""))

    @app.get("/structure/{pdb}", response_class=HTMLResponse)
    def structure_detail(pdb: str, request: Request, s: Session = Depends(db)):
        st = s.query(Structure).filter(Structure.pdb_id == pdb.upper()).first()
        if not st:
            raise HTTPException(404, "Structure not found")
        return templates.TemplateResponse(request, "structure_detail.html", ctx(
            request, st=st, vhhs=[ser.vhh_brief(v) for v in st.vhhs]))

    @app.get("/publications", response_class=HTMLResponse)
    def publications(request: Request, s: Session = Depends(db), q: str = None,
                     page: int = Query(1, ge=1), size: int = 40):
        query = s.query(Publication)
        if q:
            query = query.filter(Publication.title.ilike(f"%{q}%"))
        query = query.order_by(Publication.year.desc().nullslast())
        total = query.count()
        rows = query.offset((page-1)*size).limit(size).all()
        return templates.TemplateResponse(request, "publications.html", ctx(
            request, rows=[ser.publication_brief(p) for p in rows], total=total,
            page=page, size=size, pages=(total+size-1)//size, q=q or ""))

    @app.get("/design-methods", response_class=HTMLResponse)
    def design_methods(request: Request, s: Session = Depends(db)):
        rows = (s.query(DesignMethod, func.count(VHH.id))
                .outerjoin(VHH, VHH.design_method_id == DesignMethod.id)
                .group_by(DesignMethod.id).order_by(func.count(VHH.id).desc()).all())
        return templates.TemplateResponse(request, "design_methods.html", ctx(
            request, rows=[(d, n) for d, n in rows], taxonomy=DESIGN_TAXONOMY))

    @app.get("/statistics", response_class=HTMLResponse)
    def statistics(request: Request, s: Session = Depends(db)):
        st = repo.stats(s)
        # length distribution
        lengths = [r[0] for r in s.query(func.length).all()] if False else None
        return templates.TemplateResponse(request, "statistics.html", ctx(request, stats=st))

    @app.get("/datasets", response_class=HTMLResponse)
    def datasets(request: Request, s: Session = Depends(db)):
        ds = s.query(Dataset).all()
        st = repo.stats(s)
        return templates.TemplateResponse(request, "datasets.html", ctx(request, datasets=ds, stats=st))

    @app.get("/compare", response_class=HTMLResponse)
    def compare(request: Request, s: Session = Depends(db), ids: str = ""):
        idl = [i.strip() for i in ids.split(",") if i.strip()]
        recs = [ser.vhh_full(v) for v in (repo.get_vhh(s, i) for i in idl) if v]
        return templates.TemplateResponse(request, "compare.html", ctx(request, recs=recs, ids=ids))

    @app.get("/help", response_class=HTMLResponse)
    def help_page(request: Request):
        return templates.TemplateResponse(request, "help.html", ctx(
            request, evidence=EVIDENCE_HIERARCHY, data_status=DATA_STATUS))

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request, s: Session = Depends(db)):
        return templates.TemplateResponse(request, "about.html", ctx(request, stats=repo.stats(s)))
