"""DeNovoVHH-DB controlled vocabularies, evidence hierarchy and provenance ontology.

Single source of truth for the enumerations defined in the master specification
(sections 4, 5, 6, 28, 53). Imported by models, ETL and the API/frontend.
"""

# --- sdAb type (spec §4) ---
SDAB_TYPES = ["VHH", "VNAR", "VH", "VL", "other_sdAb", "unknown"]

# --- Evidence hierarchy (spec §5) ---
# Records may carry multiple flags, e.g. E4+E5+E6.
EVIDENCE_LEVELS = {
    "E0": "Computational only; no experimental validation located",
    "E1": "Design documented; experimental validation not located",
    "E2": "Experimentally tested; outcome available",
    "E3": "Binding experimentally validated",
    "E4": "Quantitative affinity/potency experimentally available",
    "E5": "Functional effect experimentally demonstrated",
    "E6": "Experimental VHH-target structure available",
}

# --- Design / discovery taxonomy (spec §6) ---
DESIGN_TAXONOMY = {
    "natural": [
        "immunized camelid", "naturally occurring", "immune repertoire", "natural binder",
    ],
    "library": [
        "phage display", "yeast display", "ribosome display", "mRNA display",
        "synthetic library", "naive library", "immune library",
    ],
    "engineering": [
        "affinity maturation", "CDR engineering", "framework engineering",
        "humanization", "grafting", "stability engineering", "specificity engineering",
    ],
    "computational": [
        "structure-guided design", "docking-guided design", "Rosetta design",
        "diffusion-based design", "sequence-generation model", "ProteinMPNN-assisted design",
        "RFdiffusion/RFantibody-type design", "structure-model-guided design",
        "hybrid computational design",
    ],
    "hybrid": [
        "computational design + experimental screening",
        "computational redesign + experimental maturation",
        "computational ranking + experimental validation",
    ],
    "unknown": ["Not reported"],
}

# Keyword -> (class, canonical method) for literature/source mining. Case-insensitive.
DESIGN_METHOD_KEYWORDS = {
    "rfdiffusion": ("computational", "RFdiffusion/RFantibody-type design"),
    "rfantibody": ("computational", "RFdiffusion/RFantibody-type design"),
    "proteinmpnn": ("computational", "ProteinMPNN-assisted design"),
    "rosetta": ("computational", "Rosetta design"),
    "diffusion model": ("computational", "diffusion-based design"),
    "generative": ("computational", "sequence-generation model"),
    "de novo design": ("computational", "structure-guided design"),
    "de novo": ("computational", "structure-guided design"),
    "language model": ("computational", "sequence-generation model"),
    "deep learning": ("computational", "sequence-generation model"),
    "computational design": ("computational", "hybrid computational design"),
    "docking": ("computational", "docking-guided design"),
    "alphafold": ("computational", "structure-model-guided design"),
    "affinity matur": ("engineering", "affinity maturation"),
    "humaniz": ("engineering", "humanization"),
    "phage display": ("library", "phage display"),
    "yeast display": ("library", "yeast display"),
    "ribosome display": ("library", "ribosome display"),
    "synthetic librar": ("library", "synthetic library"),
    "immuniz": ("natural", "immunized camelid"),
    "llama": ("natural", "immunized camelid"),
    "alpaca": ("natural", "immunized camelid"),
    "camelid": ("natural", "immunized camelid"),
}

# --- Data status labels (spec §53) ---
DATA_STATUS = ["Experimental", "Curated", "Calculated", "Predicted", "Inferred", "Not reported"]

# --- Data quality labels (spec §28) ---
QUALITY_LABELS = ["High", "Moderate", "Low", "Unresolved"]

# --- Binding assays (spec §15) ---
BINDING_ASSAYS = ["SPR", "BLI", "ITC", "MST", "ELISA", "flow cytometry",
                  "yeast display", "cell-binding assay", "other"]
FUNCTIONAL_ASSAYS = ["neutralization", "inhibition", "receptor blocking", "agonism",
                     "internalization", "signaling modulation", "diagnostic detection", "other"]

# --- Disclosure types (spec §8.3) ---
DISCLOSURE_TYPES = ["peer-reviewed article", "preprint", "patent",
                    "database deposition", "supplementary information", "thesis", "other"]

# --- Provenance source types (spec §27) ---
PROVENANCE_SOURCE_TYPES = ["publication", "patent", "database", "structure",
                           "computed", "dataset", "cross-reference"]

# Sentinels — never fabricate; use these when evidence is absent (spec §52)
NOT_REPORTED = "Not reported"
NOT_AVAILABLE = "Not available"

# Software/version stamps for calculated fields (spec §11, §53)
CALC_TOOLS = {
    "physchem": "Biopython.SeqUtils.ProtParam",
    "imgt": "ANARCI (IMGT scheme)",
    "checksum": "hashlib.sha1",
}

# Alias used by API/web layers
EVIDENCE_HIERARCHY = EVIDENCE_LEVELS
