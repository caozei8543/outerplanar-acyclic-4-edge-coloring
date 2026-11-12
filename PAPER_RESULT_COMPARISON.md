# Final CMC article ↔ archived actual benchmark measurements

**Reference:** 17-page final PDF (see `MANUSCRIPT_VERSION.json`), **not** the removed 23-page draft. This file is an alignment report, not a comparison to earlier discarded manuscript figures.

The archived outputs were obtained by an implementation run recorded in `data/empirical/full_run/run_manifest.json`: Python 3.13.5, NetworkX 3.6.1, random seed `20261106`, one warm-up, seven measured runs, separate traced-memory execution. The run manifest records a Linux environment, whereas the final article Section 5.2 describes a **Core i9-14900HX laptop with 32 GB RAM**. The public archive **does not independently verify that laptop hardware**: the supplied runtime manifest does not include CPU model/RAM. This potential platform-provenance difference cannot be fixed by rewriting metadata.

## Final Table 5 exact correspondence

| Category | Entries | Independent oracle where applicable | DP disagreements | Invalid certificates |
|---|---:|---|---:|---:|
| Graph Atlas | 332 | 331 YES / 1 NO | 0 | 0 |
| Obstruction/deletion tests | 12 | 11 YES / 1 NO | 0 | 0 |
| Five maximal + 200 nonmaximal + 100 multiblock | 305 | no exhaustive per-instance reference claimed | 0 | 0 |
| **Total** | **649** |  | **0** | **0** |

The atlas filter used here is: at least one edge, maximum degree at most four, and outerplanar (tested via planarity after adding a universal apex), on NetworkX 3.6.1's Graph Atlas. `G840` is the NO instance. Category totals refer to **benchmark entries**; instances may coincide up to isomorphism **between different groups**. Each synthetic random group/order is checked for within-group nonisomorphic instances. The 649 graph edges are individually stored and hashed, not inferred from an image.

The CSVs contain 72,980 node identities and 13,629 measured individual timing rows (649 instances × 3 variants × 7 repeats). A `TRUE` flag in CSV is backed by rerunnable verification code; execute `python scripts/verify_paper_alignment.py` to validate every stored witness and compare raw timing medians to reported per-instance values.

## Final Figure 6 pooled synthetic-graph results (60 graphs/order)

All means are **unweighted across 60 individual graphs** (40 nonmaximal + 20 multiblock). Per graph, timing is the median of seven DP-only timed repetitions. Memory is the mean of separately captured per-graph `tracemalloc` allocation peaks in decimal MB, not total process RSS.

| n | Full states | Exposed states | Dominance states | Dominance state reduction | Full time (ms) | Dominance time (ms) | Full peak traced memory (MB) | Dominance peak traced memory (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 490.35 | 443.50 | 404.60 | 17.49% | 1.98 | 3.23 | 0.077 | 0.077 |
| 24 | 886.98 | 847.68 | 776.78 | 12.42% | 3.12 | 5.78 | 0.142 | 0.135 |
| 48 | 1739.70 | 1657.15 | 1484.95 | 14.64% | 5.86 | 10.79 | 0.276 | 0.243 |
| 96 | 3251.37 | 3090.63 | 2773.03 | 14.71% | 11.46 | 21.26 | 0.529 | 0.453 |
| 192 | 6053.87 | 5786.35 | 5225.52 | **13.68%** | **20.68** | **38.09** | **1.056** | **0.917** |

At n=192, the **unrounded** memory reduction equals `100 * (1 - 0.9169312666666667 / 1.0564480333333333) = 13.2062...%`, displayed as **13.21%** in the PDF. Dominance reduces retained states and traced memory but **increases elapsed DP-only time** in the recorded implementation. Do not recast this as a runtime acceleration.

**Experimental provenance:** The benchmark graphs in this package are created by `src/outer4aec/benchmarks.py`; they are part of this reference implementation. The archived run manifest is the actual measurement provenance. A future run on different hardware, OS or Python environment will not reproduce the same number of milliseconds or bytes exactly.

**Residual source-history caveat:** A final PDF and an archived dataset matching its numerical results do not independently demonstrate the time/place of the original experiment or verify a stated CPU brand. If the editorial office requests machine provenance, supply original machine logs or accurately clarify which environment produced Figure 6.
