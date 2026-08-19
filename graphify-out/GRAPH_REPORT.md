# Graph Report - TRACK2-Day19-2A202601407-PhamQuocThanh  (2026-08-19)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 302 nodes · 514 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ce440a2b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_agent.py
- test_features.py
- filters.py
- Searcher
- SemanticCache
- Embedder
- _setup.py
- main.py
- Result
- container-up.sh script
- amount_vs_avg
- seed_corpus.py
- runtime-check.sh
- gen_spend.py
- feature_views.py
- container-down.sh
- setup-lite.sh
- day19-vector-feature-store-lab

## God Nodes (most connected - your core abstractions)
1. `Searcher` - 27 edges
2. `Embedder` - 18 edges
3. `FilteredIndex` - 17 edges
4. `ToolArgs` - 13 edges
5. `RuleBasedPlanner` - 12 edges
6. `SemanticCache` - 12 edges
7. `RetrievalTool` - 11 edges
8. `leakage_experiment()` - 11 edges
9. `doc_metadata()` - 11 edges
10. `auc()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_planner_keeps_simple_questions_whole()` --calls--> `RuleBasedPlanner`  [EXTRACTED]
  tests/test_agent.py → app/agent.py
- `test_planner_splits_compound_questions()` --calls--> `RuleBasedPlanner`  [EXTRACTED]
  tests/test_agent.py → app/agent.py
- `test_use_filters_false_emits_no_filters()` --calls--> `RuleBasedPlanner`  [EXTRACTED]
  tests/test_agent.py → app/agent.py
- `StarvingPlanner` --uses--> `ToolArgs`  [INFERRED]
  notebooks/06_agent_retrieval.py → app/agent.py
- `main()` --uses--> `FilteredIndex`  [INFERRED]
  scripts/gen_agent_queries.py → app/filters.py

## Import Cycles
- None detected.

## Communities (19 total, 5 thin omitted)

### Community 0 - "test_agent.py"
Cohesion: 0.07
Nodes (28): Any, Agent, AgentResult, build_context(), Planner, Retrieval as a tool + a zero-key planning agent (NB6). Deck reference:…, The executable behind SEARCH_TOOL., The baseline: embed the whole question once, retrieve once. (+20 more)

### Community 1 - "test_features.py"
Cohesion: 0.09
Nodes (42): auc(), frequency_encode(), generate_events(), latest_join(), leakage_experiment(), leaked_row_fraction(), pit_join(), DataFrame (+34 more)

### Community 2 - "filters.py"
Cohesion: 0.10
Nodes (30): access_filter(), combo_filter(), Filtered vector search: the three strategies, measured side by side (NB5). Deck…, Deliberately narrow: ~1/3 x recency. This is where post-filter dies., recent_filter(), tenant_filter(), _digest(), doc_metadata() (+22 more)

### Community 3 - "Searcher"
Cohesion: 0.11
Nodes (19): FilteredIndex, Clone the base collection into a filter-aware one with rich payloads., Path, Holds the BM25 index, Qdrant client, and document metadata. Construction is…, Searcher, SearchHit, Mode, main() (+11 more)

### Community 4 - "SemanticCache"
Cohesion: 0.09
Nodes (20): CacheHit, CacheStats, Semantic cache over Qdrant (NB7). Deck reference: "Semantic Cache: Hien Thuc…, Nearest cached entry + its score, WITHOUT applying threshold or TTL. Lets a…, Move the virtual clock forward (so TTL is testable in a notebook)., SemanticCache, Cách người thật hỏi lại cùng một câu., variants() (+12 more)

### Community 5 - "Embedder"
Cohesion: 0.10
Nodes (18): BackendSpec, describe(), Embedder, ndarray, Pluggable embedding backends, selected by the EMBEDDING_BACKEND env var. Why…, Uniform `.embed(list[str]) -> Iterator[np.ndarray]`, matching fastembed., Guards the EMBEDDING_BACKEND contract. This variable was documented in…, The lite path and every rubric threshold depend on this exact default. (+10 more)

### Community 6 - "_setup.py"
Cohesion: 0.14
Nodes (12): # TODO: implement the embed + upsert loop here., # TODO: implement RRF fusion below., search_hybrid(), search_keyword(), search_semantic(), benchmark_mode(), percentile(), make_item_popularity() (+4 more)

### Community 7 - "main.py"
Cohesion: 0.18
Nodes (15): healthz(), lifespan(), FastAPI service exposing /search?q=...&mode=keyword|semantic|hybrid. Run: `make…, Load the Searcher once at startup. Embedding model + indexing the 1000 docs…, root(), search(), SearchHitOut, SearchResponse (+7 more)

### Community 8 - "Result"
Cohesion: 0.19
Nodes (7): ndarray, Brute-force cosine over the matching subset -- the correct answer., Ask the index for fetch_k, then throw away whatever does not match., Filter first, then scan the survivors exactly. Correct, but no index., Hand the filter to the engine and let it stay inside the index., One strategy's answer for one query., Result

### Community 9 - "container-up.sh script"
Cohesion: 0.43
Nodes (5): port_open(), container-up.sh script, start(), still_running(), setup-docker.sh script

### Community 10 - "amount_vs_avg"
Cohesion: 0.40
Nodes (4): amount_vs_avg(), On-demand feature transformation: the request-time ratio (NB8). Deck reference:…, Ratio of this transaction to the user's own recent baseline. Absolute amount is…, on_demand_feature_view

### Community 11 - "seed_corpus.py"
Cohesion: 0.50
Nodes (4): main(), make_doc(), Generate the lab corpus + golden eval set deterministically. Outputs:…, Build one doc with mixed VN prose + key technical terms.

### Community 12 - "runtime-check.sh"
Cohesion: 0.83
Nodes (3): bold(), row(), runtime-check.sh script

## Knowledge Gaps
- **4 isolated node(s):** `BackendSpec`, `container-down.sh script`, `setup-lite.sh script`, `day19-vector-feature-store-lab`
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Searcher` connect `Searcher` to `test_agent.py`, `filters.py`, `Embedder`, `main.py`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `SemanticCache` connect `SemanticCache` to `test_features.py`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `FilteredIndex` connect `Searcher` to `test_agent.py`, `Result`, `filters.py`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Searcher` (e.g. with `FilteredIndex` and `lifespan()`) actually correct?**
  _`Searcher` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `FilteredIndex` (e.g. with `RetrievalTool` and `Searcher`) actually correct?**
  _`FilteredIndex` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `BackendSpec`, `container-down.sh script`, `setup-lite.sh script` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_agent.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07446808510638298 - nodes in this community are weakly interconnected._