# Ranking experiments against the paraphrase groups (2026-11-09)

Index: transcribed snapshot (7,936 passages). Each hypothesis was tested alone with an
in-process harness that reproduced the committed baseline exactly, against all five sets.
"Groups" = paraphrase groups whose worst phrasing is in the top 5 (of 27);
h@1 / h@5 count phrasings (of 110). Q, App = questions / sewage-appendices MRR at k=5;
Rank@1 = search-ranking.yaml at k=1; Ver = verified-transcriptions top-1 count (of 64).

| Variant | Q | App | Rank@1 | Ver t1 | Groups | worst MRR | h@1 | h@5 |
|---|---|---|---|---|---|---|---|---|
| Baseline | 0.84 | 0.92 | 12/12 | 53 | 13 | 0.29 | 55 | 87 |
| H1 title weight 3 (from 6) | 0.83 | 0.90 | 12/12 | 53 | 12 | 0.28 | 56 | 86 |
| H1 title weight 10 | 0.84 | 0.92 | 12/12 | 53 | 13 | 0.30 | 55 | 88 |
| H1 handle weight 0 or 2 (from 4) | 0.84 | 0.92 | 12/12 | 53 | 13 | 0.29 | 55 | 87 |
| H1 body weight 2 (from 1) | 0.86 | 0.89 | 12/12 | 53 | 11 | 0.29 | 58 | 83 |
| H1 chunks 800 chars (re-chunked index) | 0.78 (26/27) | 0.91 | 12/12 | 52 | 13 | 0.31 | 56 | 89 |
| H1 chunks 1000 chars | 0.81 (26/27) | 0.92 | 12/12 | 53 | 13 | 0.32 | 54 | 88 |
| H1 chunks 3000 chars | 0.84 (26/27) | 0.91 | 12/12 | 53 | 12 | 0.32 | 59 | 87 |
| H1 no breadcrumb titles | 0.84 | 0.96 | 12/12 | 53 | 13 | 0.27 | 59 | 85 |
| Synonym phrases off | 0.81 (25/27) | 0.92 | 6/12 | 53 | 11 | 0.29 | 57 | 87 |
| H2 appendix/annexure x0.8 (skipped for data queries) | 0.82 (26/27) | 0.82 (12/13) | 12/12 | 53 | 13 | 0.29 | 55 | 86 |
| H2 appendix/annexure/example x0.7 | 0.81 (25/27) | 0.73 (10/13) | 12/12 | 53 | 12 | 0.29 | 55 | 85 |
| H3 query-bigram bonus 0.1 | 0.85 | 0.91 | 12/12 | 54 | 12 | 0.28 | 60 | 87 |
| H3 query-bigram bonus 0.5 | 0.79 (26/27) | 0.91 | 10/12 | 54 | 11 | 0.23 | 55 | 83 |
| H3 query-term coverage ^0.5 | 0.89 | 0.84 | 12/12 | 54 | 12 | 0.27 | 59 | 85 |
| H3 query-term coverage ^1 | 0.80 (26/27) | 0.83 (12/13) | 10/12 | 54 | 10 | 0.25 | 58 | 83 |
| **Heading coverage x(1 + 0.6 * share of heading words in query), KEPT** | **0.88** | **0.95** | **12/12** | **53** | **16** | **0.29** | **61** | **93** |
| + H4 bge-small dense only | 0.77 (24/27) | 0.81 (12/13) | 3/12 | 50 | 11 | 0.23 | 48 | 85 |
| + H4 RRF k=60, dense weight 1 | 0.90 | 0.89 | 8/12 | 52 | 13 | 0.38 | 68 | 94 |
| + H4 RRF k=60, dense weight 0.5 | 0.91 | 0.91 | 9/12 | 53 | 14 | 0.36 | 68 | 96 |
| + H4 RRF, domain hint +0.03 on dense | 0.90 | 0.89 | 8/12 | 52 | 15 | 0.39 | 68 | 96 |
| + H4 RRF, BM25 top hit kept first | 0.88 | 0.95 | 12/12 | 53 (63/64 top5) | 16 | 0.31 | 61 | 97 |
| + H4 RRF, BM25 top 2 kept first | 0.88 | 0.94 | 12/12 | 53 | 16 | 0.28 | 61 | 96 |

Notes
- Chunk size, breadcrumbs and field weights move results by about one either way; the
  long-OR-query problem is not mainly a chunking problem. Appendix and table chunks do
  win some long queries (P01), but down-weighting them breaks appendix questions that
  carry no "data" words ("How can I size clarifiers in activated sludge treatment?").
- Synonym phrases are needed (the ranking set falls from 12/12 to 6/12 without them),
  though single ones cost a little: "water supply" -> "water consumption" pulls in
  sections whose breadcrumb is "Measures to Minimise Water Consumption". Not changed, to
  avoid tuning on individual groups.
- The heading-coverage boost uses unstemmed words. A crude-stemmed version scored
  slightly lower and cost one verified top-1.
- The grit question (P02 review phrasing) went from rank 9 to 4 with the heading boost:
  "grit" and "removal" both appear in the query and in "Grit Removal".

Embedding cost (BAAI/bge-small-en-v1.5 via fastembed / ONNX Runtime, CPU only)
- Build: 897 s on 16 threads for 7,936 passages (long passages truncate at 512 tokens).
- Storage: 12 MB float32 vectors (384-d) + 65 MB model files.
- Query: 8.4 ms to embed a query, 3.2 ms for the dense ranking; about 340 MB peak RSS in
  the eval process.
- Dependencies: about 120 MB on top of the current environment (onnxruntime 65 MB,
  pillow 20 MB, tokenizers 12 MB, huggingface_hub/hf-xet 15 MB); numpy is already present.
- Deterministic on a given machine and thread count; float differences across CPUs could
  reorder near ties.
