# DeNovoVHH-DB — Benchmark splits (v1.0)

Fixed, leakage-controlled train / validation / test splits for VHH modelling.

## Cohort

Only records with **real experimental evidence** are included: a record must
have an experimental 3D structure and/or an experimental affinity measurement.
Calculated-only or unlabelled records are excluded from the benchmark (they
remain in the full database).

- Total benchmark records: **1,410** (954 with experimental structure, 984 with measured affinity).

## Leakage-control rule

Splits are assigned at the level of **antigen target groups**, not individual
records. The grouping key is:

1. the antigen target name, when present; otherwise
2. the exact normalized sequence (identical sequences share a group); otherwise
3. the record id.

Whole groups are assigned to a single split, so **no antigen target and no
identical sequence ever appears in more than one split**. This prevents the
trivial leakage of testing on an antigen (or a duplicate sequence) the model
already saw in training.

Groups are placed largest-first into the split currently furthest below its
quota (70 / 15 / 15 by record count). The assignment is deterministic
(size-ordered, hash tie-broken) and reproducible.

## Resulting splits

| Split | Records | % | Disjoint targets | w/ structure | w/ affinity | de novo |
|---|---:|---:|---:|---:|---:|---:|
| train | 987 | 70.0 | 114 | 544 | 746 | 435 |
| validation | 212 | 15.0 | 99 | 211 | 121 | 11 |
| test | 211 | 15.0 | 98 | 199 | 117 | 7 |

Target sets across splits are fully disjoint by construction.

## Files

- `benchmark_splits.csv` — all 1,410 records with id, target, uniprot,
  evidence flags, quality, group key, and split assignment.
- `split_train.csv`, `split_validation.csv`, `split_test.csv` — per-split id lists.

## Caveats

- The cohort is small (evidence-backed records only) and target-imbalanced;
  report per-target as well as pooled metrics.
- Splitting is by antigen target, not by structural epitope or CDR-cluster;
  cross-reactive antibodies to related antigens could still share epitope
  features across splits. Sequence-identity clustering was not applied beyond
  exact-duplicate grouping (no ANARCI/CD-HIT available on this platform).
