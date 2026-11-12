# Exact mapping: CMC 17-page FINAL manuscript → reproducible artifacts

**Authority:** `paper/CMC_Condensed_Illustrated_Graphs_FINAL_17p.pdf`; SHA-256 is pinned in `docs/MANUSCRIPT_VERSION.json`. Page numbers below are **physical PDF pages (1–17)** and numbering follows the final manuscript, not the removed 23-page draft.

| Final article location | Claim / object | Executable source or verifiable record | Evidence scope |
|---|---|---|---|
| p.3 Lemma 1 | block–cut coloring reduction | `decomposition.decompose_blocks`, `dp.solve_graph`, `core.verify_coloring` | global witness and independent properness/acyclicity check |
| p.3–4 Definitions 2–4; Eq. (1) | full/exposed color masks and terminal-pair connectivity | `states.State`, `states.leaf`, `eligible_mask`, `project` | exact executable definitions |
| p.4–5 Theorem 5; Eqs. (2)–(4) | exact series/parallel transitions | `states.transition`, `dp.run_tree` | all-node consistency and witness checks |
| p.5 Theorem 6 | contextual equivalence, separating path | mathematical proof in final PDF; `states.eligible_mask` | construction compatible with code; **not** mechanically proved by tests |
| p.6–7 Theorem 7 / Corollary 9 | contextual dominance, preserved existential feasibility | `states.minimize`, `dp.run_tree` | tested equality and inclusion-minimality, not automated theorem proving |
| p.7–8 Table 1 / Eq. (7) / Theorem 10 | 60, 48, 120, 16, 12; 16,384, 956, ≤468 | `states.formal_enumeration`, `data/certificates/formal_state_enumeration.json` | exhaustive finite enumeration |
| p.8 Proposition 11 | 82 color-permutation orbits | `states.formal_enumeration` | all 24 permutations counted |
| p.9 Eq. (8), Theorem 12, Table 2 | Q graph, eight normalized proper 4-color cases, forbidden cycles | `core.Q_EDGES`, `certificates.proper_q_cases`, `paper_certificate_checks.json` (`table2_q_proper_cases`) | Q independently exhaustively checked |
| p.10 Table 3 | Q−e: six representative certificate rows, 11 edge deletions | `core.Q_DELETION_CERT`, `paper_certificate_checks.json` (`table3_edge_deletion_certificates`) | all 11 deletions explicitly verified |
| p.10–11 Lemma 13 / Theorem 14 / Table 4 | maximal 7-vertex structure, six-vertex 4-color witnesses | `certificates.TABLE4_SIX_VERTEX_COLORINGS` | both Table 4 instances certified; general proof remains mathematical |
| p.11 Theorem 16 | block-maximal criterion | block decomposition + graph DP | consistency, not a universal enumerative proof |
| p.12 Theorem 17 / Proposition 18 | exact constructive recognition; linear work **given** SP decompositions | `dp.solve_graph`, `dp.reconstruct_tree` | completeness checked against small-graph oracle; constructor not claimed linear |
| p.12–13 Section 5.2, Table 5 | 649 entries: 332/5/200/100/12; 331/1 atlas; zero disagreements | `benchmark_instances.jsonl`, `instance_results.csv`, `node_level_consistency.csv`, `witnesses.jsonl`, `run_manifest.json` | 649 entries, per-node consistency and witnesses checked |
| p.13 Section 5.4, Figure 6 | 60 instances per order; n=192 13.68%, 13.21%, 20.68/38.09 ms | `aggregate_by_order.csv`, `raw_timing_repetitions.csv`, `scripts/plot_results.py`, `figures/paper_figure6_plot_values.csv` | measured data, no illustrative replacement |
| p.13–14 Section 5.5, Figure 7 | Q scheduling example (4 NO, 5 YES, deletion YES) | Q certificates and edge graphs | graph-theoretic claims checked; illustrative campus backdrop not field data |
| p.14–15 Section 5.6, Figure 8 | 71/76 IoT example, Δ=4, four-slot schedule | `src/outer4aec/figure8.py`, `scripts/verify_figure8.py`, `data/certificates/figure8_transcribed_topology_and_validated_witness.json` | manual figure topology transcription + **new independent coloring**, not asserted pixel-identical to pictured slots |

**Empirical scope:** Final Table 5 is a correctness table, not the eight-color-cases or six-vertex certificates table. Formal 468 is a worst-case antichain bound, not the cumulative states plotted in Figure 6. No code test by itself proves research novelty.
