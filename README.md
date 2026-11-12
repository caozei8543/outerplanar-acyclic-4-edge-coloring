# Bichromatic Boundary-State Reduction — CMC final-article reproducibility package

**Canonical article:** *Bichromatic Boundary-State Reduction for Acyclic 4-Edge-Coloring of Outerplanar Graphs with Maximum Degree at Most Four*.

**Canonical source of claims:** `paper/CMC_Condensed_Illustrated_Graphs_FINAL_17p.pdf` (17 pages). Its SHA-256 and pagination are recorded in `docs/MANUSCRIPT_VERSION.json`. The previous 23-page draft, its older figures, and the non-measured illustrative curves have been removed to prevent accidental mixing of versions.

This package supplies an executable, auditable four-color feasibility DP, exactly **649 archived benchmark entries**, per-instance decisions and reconstructed certificates, three-DP node comparisons, seven individual timed repetitions per variant, traced-memory measurements, and data/plots corresponding to **final Figure 6**. The PDF's Section 5.5 and 5.6 examples are mapped explicitly: Q has exact combinatorial certificates, and the labeled Figure 8 topology has been manually transcribed with a separately computed valid four-slot witness. The new witness is **not** asserted to match the particular edge colors printed in the original diagram.

## Definitive figures and claim boundaries

| Final paper claim | Archived evidence |
|---|---|
| 16,384 / 956 / 468 formal counts; 82 symmetry orbits | `data/certificates/formal_state_enumeration.json` and `states.py` |
| Q needs five colors; eight normalized proper four-color cases; all 11 edge deletions support four colors | `data/certificates/paper_certificate_checks.json`, `certificates.py` |
| Table 4: both six-vertex maximal outerplanar four-color certificates | `paper_certificate_checks.json` under `table4_six_vertex_certificates` |
| Table 5: 649 entries = 332 Atlas + 5 maximal + 200 nonmaximal + 100 multiblock + 12 Q-related entries | `data/empirical/benchmark_instances.jsonl`, `data/empirical/full_run/instance_results.csv` |
| Table 5: Atlas 331 YES / 1 NO; obstruction 11 YES / 1 NO, and no DP disagreements/errors | `instance_results.csv`, `node_level_consistency.csv`, `witnesses.jsonl` |
| Figure 6: 60 generated graphs/order; n=192 state reduction 13.68%, memory reduction 13.21%, times 20.68 and 38.09 ms | `aggregate_by_order.csv`, raw timed repetitions, `figures/paper_figure6_plot_values.csv` |
| Figure 7: exact graph Q, four-slot infeasibility, deletions and five-color certificate | `paper_certificate_checks.json`; source graph in `core.py` |
| Figure 8: 71 vertices, 76 edges, Δ=4, six independent cycles, feasible four-slot link schedule | `data/certificates/figure8_transcribed_topology_and_validated_witness.json`, `figure8.py` |

**Limitations:** Figure 8 topology is a documented transcription of the PDF image; it is not recovered from an original field/author-provided edge file. Synthetic examples are not field measurements. Recorded performance is tied to the archive's generator, program version and execution environment; rerun times and traced allocations will vary. The reference SP decomposition constructor may use superlinear preprocessing. Linear time is claimed for the DP **given** suitable linear-size decompositions, exactly as in Proposition 18.

For a full manuscript-to-evidence index, see `docs/ARTICLE_TO_CODE_MAP.md` and `docs/REPRODUCIBILITY_AND_LIMITATIONS.md`.

## Directory map

- `paper/`: exact 17-page final PDF, **not** the pre-revision DOCX.
- `src/outer4aec/`: graph validator, independent coloring oracle, SP decomposition, complete/exposed/dominance DP, certificates, Figure 8 topology transcription.
- `data/empirical/benchmark_instances.jsonl`: 649 individual graph edge lists, labels, SHA-256 hashes and generator metadata.
- `data/empirical/decomposition_trees.jsonl`: one stored two-terminal decomposition forest per graph entry.
- `data/empirical/full_run/`: 649 graph-level rows, 13,629 individual timing records, 72,980 per-node identity checks, 649 graph-level YES/NO witness records, 15 aggregation rows and the original execution manifest.
- `data/certificates/`: fixed integer identities; Q/Table 2–4 certificates; Figure 8 image-transcribed topology plus an independently validated new witness.
- `figures/`: measured-state, time and memory plots, Figure 6 side-by-side rendering and plot-value CSV. **No invented example curves are included.**
- `docs/`: alignment matrix, release verification, provenance, limitations, Chinese publication/reproduction guide.
- `scripts/`: input generation, experiment runner, plotting, release hash check, final manuscript alignment check, figure 8 certificate check.
- `tests/`: focused mathematical and algorithmic tests.

## Install and independently audit (repository root)

Reference environment: Python 3.13.5, NetworkX 3.6.1, matplotlib 3.10.8, pytest 9.0.2. On a new system use Python 3.11+ and install dependencies; results need not have identical timing values.

```bash
python -m pip install -e '.[plot,test]'
python -m pytest -q
python scripts/verify_paper_alignment.py
python scripts/verify_figure8.py
python scripts/verify_release.py
```

`verify_paper_alignment.py` checks all 649 inputs, group counts, CSV metadata, every stored YES witness, serialized SP decomposition leaves, **all 13,629 repeated timing rows versus per-instance medians**, all 72,980 recorded node consistency flags, the aggregate means and reported Figure 6 numbers, paper certificates, Figure 8 topology/witness, and the final-PDF SHA-256. A FAIL stops with an error; it does not silently repair data.

To independently regenerate graph inputs and combinatorial certificates (potentially slower):

```bash
python scripts/generate_data.py --seed 20261106
python scripts/verify_paper_alignment.py
```

To make a **new empirical run** without overwriting archived observations:

```bash
python scripts/run_experiments.py --profile full --warmups 1 --repeats 7 \
  --timeout-s 60 --outdir data/empirical/local_full_run
python scripts/paper_audit.py --results data/empirical/local_full_run/instance_results.csv \
  --output data/empirical/local_full_run/paper_audit.json
python scripts/plot_results.py --input data/empirical/local_full_run/instance_results.csv \
  --outdir data/empirical/local_full_run/figures
```

For a shorter functional run (all 332 Atlas graphs, 12 Q cases, five maximal examples, and 20 random graphs):

```bash
python scripts/run_experiments.py --profile quick --warmups 0 --repeats 1 \
  --outdir data/empirical/local_smoke_run
```

To regenerate final Figure 6 panels from the **archived measured data**:

```bash
python scripts/plot_results.py
python scripts/verify_figure8.py --regenerate
```

If you regenerate Figure 8's witness, regenerate `SHA256SUMS.txt` as part of a **new versioned release**; any data modification invalidates the existing hash manifest.

## Fixed experimental protocol

- Fixed palette `{1,2,3,4}`; colors not required all to be present. Terminal masks are four bits; six pair bits correspond to `12,13,14,23,24,34`.
- Series: check shared terminal-color disjointness and intersect connectivity masks. Parallel: check terminal-color disjointness and no shared exposed pair, then filter the union.
- Inclusion-minimal exposed sets are retained for each ordered terminal color-mask pair. Original color labels stay consistent across a decomposition.
- Graph Atlas: nonempty, maximum degree at most four, outerplanar; 332 selected, 331 YES / 1 NO.
- Synthetic cohorts: orders `{12,24,48,96,192}` with 40 nonmaximal and 20 multiblock graphs per order, seed `20261106`. Five maximal examples and 12 Q/deletion cases complete the 649 entries. The generator is specified in `benchmarks.py`; cross-category overlap is allowed.
- One untimed warm-up and seven timed DP runs per graph/mode; per-graph **median** and then unweighted cross-graph **mean** for each order. Stopwatch measures only the `run_tree` DP, excluding decomposition and checks. Memory is from a separate `tracemalloc` run, decimal MB, not process RSS.
- Three variants use the same decomposition; at each node, `Exposed=project(Full)` and `Dominance=minimize(Exposed)`; independent backtracking covers the 332 Atlas graphs and 12 obstruction cases.

## Public distribution

This package includes a *submission-version PDF solely for reference matching*. The MIT license covers the newly written software/docs, **not automatically the article PDF**; consider omitting the PDF from a public repository if rights or journal policy require it, but preserve its SHA-256 and article citation. See `NOTICE.md`. The archive is not evidence that the author already published this exact release to GitHub.
