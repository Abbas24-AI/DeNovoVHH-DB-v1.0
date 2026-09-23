"""Shared ETL helpers: sequence normalization, physicochemical calculation,
CDR/FR partitioning by substring, affinity parsing, evidence assignment.

No value is invented. Calculated fields are labeled with tool+version. Absent
inputs yield None / 'Not reported' downstream.
"""
import re, hashlib
from Bio.SeqUtils.ProtParam import ProteinAnalysis
import Bio

AA = set("ACDEFGHIKLMNPQRSTVWY")
NOT_REPORTED = "Not reported"


def clean_str(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "\\", "\\\\", "nan", "NaN", "None", "-"):
        return None
    return s


def normalize_seq(s):
    if s is None:
        return None
    s = re.sub(r"\s+", "", str(s)).upper()
    s = s.replace("*", "")
    return s or None


def is_protein(s):
    if not s:
        return False
    letters = set(s)
    return len(letters - AA - {"X", "B", "Z", "U", "O"}) == 0 and len(s) >= 5


def checksum(s):
    return hashlib.sha1(s.encode()).hexdigest() if s else None


def physchem(seq):
    """Biopython ProtParam. Returns dict or None. X/nonstandard residues stripped
    for the analysis but original length preserved."""
    if not seq:
        return None
    clean = re.sub(r"[^ACDEFGHIKLMNPQRSTVWY]", "", seq)
    if len(clean) < 5:
        return None
    try:
        pa = ProteinAnalysis(clean)
        aa_pct = pa.amino_acids_percent
        return {
            "length": len(seq),
            "molecular_weight": round(pa.molecular_weight(), 2),
            "theoretical_pi": round(pa.isoelectric_point(), 2),
            "net_charge_ph7": round(pa.charge_at_pH(7.0), 2),
            "aa_composition": {k: round(v, 4) for k, v in aa_pct.items()},
            "cysteine_count": clean.count("C"),
            "aromaticity": round(pa.aromaticity(), 4),
            "instability_index": round(pa.instability_index(), 2),
            "gravy": round(pa.gravy(), 4),
            "aliphatic_index": round(_aliphatic_index(aa_pct), 2),
            "extinction_coefficient": pa.molar_extinction_coefficient()[1],  # cystines reduced->oxidized[1]
            "method": "Biopython.SeqUtils.ProtParam",
            "calc_version": f"biopython-{Bio.__version__}",
        }
    except Exception:
        return None


def _aliphatic_index(aa_pct):
    # Ikai 1980: AI = X_Ala + 2.9*X_Val + 3.9*(X_Ile+X_Leu), mole% scale.
    # Biopython.amino_acids_percent already returns mole-% (sums to 100), so use directly.
    return (aa_pct.get("A", 0) + 2.9*aa_pct.get("V", 0)
            + 3.9*(aa_pct.get("I", 0) + aa_pct.get("L", 0)))


KYTE = dict(A=1.8, R=-4.5, N=-3.5, D=-3.5, C=2.5, Q=-3.5, E=-3.5, G=-0.4, H=-3.2,
            I=4.5, L=3.8, K=-3.9, M=1.9, F=2.8, P=-1.6, S=-0.8, T=-0.7, W=-0.9,
            Y=-1.3, V=4.2)


def seq_charge(seq):
    if not seq:
        return None
    try:
        return round(ProteinAnalysis(re.sub(r"[^ACDEFGHIKLMNPQRSTVWY]", "", seq)).charge_at_pH(7.0), 2)
    except Exception:
        return None


def seq_hydrophobicity(seq):
    if not seq:
        return None
    vals = [KYTE[a] for a in seq if a in KYTE]
    return round(sum(vals)/len(vals), 3) if vals else None


def partition_fr_cdr(full_seq, cdr1, cdr2, cdr3):
    """Locate CDR substrings within the full VHH sequence to derive FR1..FR4.
    Deterministic; returns list of (region, seq) or [] if CDRs are not clean
    substrings (then only source CDRs are stored). No numbering is forced."""
    if not full_seq:
        return []
    parts = []
    cursor = 0
    ok = True
    for name, cdr in [("CDR1", cdr1), ("CDR2", cdr2), ("CDR3", cdr3)]:
        if not cdr:
            ok = False
            break
        i = full_seq.find(cdr, cursor)
        if i < 0:
            ok = False
            break
        parts.append((f"FR{len(parts)//2 + 1}", full_seq[cursor:i]))
        parts.append((name, cdr))
        cursor = i + len(cdr)
    if not ok:
        return []
    parts.append(("FR4", full_seq[cursor:]))
    return [(r, s) for r, s in parts if s is not None]


AFFINITY_UNIT_RE = re.compile(r"([\d.]+)\s*[eE]?\s*([-+]?\d+)?\s*(pM|nM|uM|µM|mM|M)?")


def parse_kd_to_M(raw):
    """Parse an ANDD KD cell (already in M as float or scientific string) to float M.
    Returns (float_M, original_string). Never coerces an unparseable value."""
    if raw is None:
        return None, None
    orig = str(raw).strip()
    if orig in ("", "\\", "\\\\", "nan"):
        return None, None
    try:
        val = float(orig)
        if val > 0:
            return val, orig
    except ValueError:
        pass
    return None, orig
