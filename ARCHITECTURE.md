# Architecture & System Design

## Pipeline Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    SKILL EXTRACTION & NORMALIZATION PIPELINE               │
└────────────────────────────────────────────────────────────────────────────┘

INPUT LAYER
═══════════════════════════════════════════════════════════════════════════════
                              Raw Job Description Text
                                      ↓
                         "Senior Python developer needed.
                          Django backend experience required.
                          JavaScript and React for frontend.
                          Must know Node.js and Docker."


STAGE 1: NAMED ENTITY RECOGNITION (NER)
═══════════════════════════════════════════════════════════════════════════════
                                      ↓
    ┌──────────────────────────────────────────────────────────────┐
    │                    SkillNERExtractor                          │
    ├──────────────────────────────────────────────────────────────┤
    │ • Pattern-based entity extraction                             │
    │ • Multiple entity types support                               │
    │ • Context window extraction                                   │
    │ • Span indexing                                               │
    └──────────────────────────────────────────────────────────────┘
                                      ↓
        [("Python", PROGRAMMING_LANGUAGE, 7, 13),
         ("Django", FRAMEWORK, 25, 31),
         ("JavaScript", PROGRAMMING_LANGUAGE, 45, 56),
         ("React", FRAMEWORK, 61, 66),
         ("Node.js", FRAMEWORK, 85, 92),
         ("Docker", TOOL, 97, 103)]


STAGE 2: ENTITY LINKING
═══════════════════════════════════════════════════════════════════════════════
                                      ↓
    ┌──────────────────────────────────┬──────────────────────────────────┐
    │   ESCO Taxonomy Lookup           │   DBpedia Spotlight Client       │
    ├──────────────────────────────────┼──────────────────────────────────┤
    │ • Exact string matching          │ • Resource annotation            │
    │ • Alias resolution               │ • URI retrieval                  │
    │ • Fuzzy matching (0.8 threshold) │ • Metadata extraction            │
    │ • Hierarchy retrieval            │ • Type classification            │
    └──────────────────────────────────┴──────────────────────────────────┘
                                      ↓
    For "Python": ✓ Found in ESCO        For "Python": ✓ Found in DBpedia
    For "Django": ✓ Found in ESCO        For "Django": ✓ Found in DBpedia
    For "React":  ✓ Found in ESCO        For "React":  ✓ Found in DBpedia
    ...


STAGE 3: HIERARCHICAL PRIORITY LOGIC (Conflict Resolution)
═══════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────┐
    │  RESOLUTION DECISION TREE                                            │
    └─────────────────────────────────────────────────────────────────────┘
                                      ↓
                        ┌─────────────┴────────────────┐
                        │                              │
                  [ESCO Found?]                   [ESCO NOT Found]
                   /    |    \                          │
                Yes    No    Both                        ↓
                 │      │      │                  ┌──────────────┐
                 │      │      │                  │DBpedia Found?│
                 │      │      │                  └────┬──────┬──┘
                 │      │      │                      Yes    No
                 │      │      │                       │      │
                 ↓      │      │                       ↓      ↓
            PRIMARY    │      │                  FALLBACK  UNRESOLVED
            MAPPING    │      │                  ENRICHMENT
            (0.95)     │      │                  (0.75)     (0.0)
                       │      │
                       │      └──→ HYBRID CONFLICT (0.95 + DBpedia)
                       │
                       └──→ [Check DBpedia]
                            │
                            ├─→ Found: DBPEDIA_ENRICHMENT (0.75)
                            └─→ Not Found: UNRESOLVED (0.0)


STAGE 4: KNOWLEDGE BASE NORMALIZATION
═══════════════════════════════════════════════════════════════════════════════
                                      ↓
    ┌──────────────────────────────────────────────────────────────┐
    │         KnowledgeBaseNormalizer                               │
    ├──────────────────────────────────────────────────────────────┤
    │ • Surface form variation resolution                           │
    │   "Node.js" ↔ "NodeJS" ↔ "nodejs" → "Node.js" (canonical)  │
    │   "C++" ↔ "CPP" → "C++" (canonical)                          │
    │                                                               │
    │ • Confidence scoring:                                        │
    │   ESCO Primary:         0.95                                 │
    │   Hybrid Conflict:      0.95 + enrichment                    │
    │   DBpedia Enrichment:   0.75                                 │
    │   Unresolved:           0.0                                  │
    │                                                               │
    │ • Metadata enrichment from both sources                       │
    │ • Context window preservation                                │
    └──────────────────────────────────────────────────────────────┘
                                      ↓
    SkillEntity objects created with:
    ├─ Canonical name
    ├─ ESCO URI + Hierarchy
    ├─ DBpedia URI + Metadata
    ├─ Confidence Score
    └─ Resolution Method


STAGE 5: RESULT AGGREGATION & STATISTICS
═══════════════════════════════════════════════════════════════════════════════
                                      ↓
    ┌──────────────────────────────────────────────────────────────┐
    │         Job-Level Statistics                                  │
    ├──────────────────────────────────────────────────────────────┤
    │ • Total mentions: 6                                           │
    │ • Unique skills: 5 (after deduplication)                     │
    │ • ESCO mapped: 5                                              │
    │ • DBpedia mapped: 5                                           │
    │ • Avg confidence: 0.93                                        │
    └──────────────────────────────────────────────────────────────┘
                                      ↓
    ┌──────────────────────────────────────────────────────────────┐
    │         Batch-Level Aggregation (if multiple jobs)            │
    ├──────────────────────────────────────────────────────────────┤
    │ • Jobs processed: N                                           │
    │ • Total skills: M                                             │
    │ • Unique canonical skills: K                                  │
    │ • Top skills ranking                                          │
    │ • Entity type distribution                                    │
    │ • KB coverage metrics                                         │
    └──────────────────────────────────────────────────────────────┘


OUTPUT LAYER: MULTIPLE EXPORT FORMATS
═══════════════════════════════════════════════════════════════════════════════
                                      ↓
    ┌────────────────────────────────────────────────────────────────┐
    │ 1. JSON Format              2. CSV Format      3. JSONL         │
    ├────────────────────────────────────────────────────────────────┤
    │ {                           job_id,canonical, ...job_001,{"sur" │
    │   "job_id": "job_001",      job_001,Python,... job_002,{"sur"  │
    │   "skills": [               job_001,Django,... job_003,{"sur"  │
    │     {                                                           │
    │       "surface_form":       4. Database Schema                 │
    │         "Python",           CREATE TABLE skills (              │
    │       "canonical_name":       skill_id VARCHAR(255),           │
    │         "Python",             job_id VARCHAR(255),             │
    │       "esco_uri": "...",      canonical_name VARCHAR(255),     │
    │       "confidence": 0.95,     esco_uri VARCHAR(500),           │
    │       ...                     dbpedia_uri VARCHAR(500)         │
    │     }                       );                                  │
    │   ]                                                             │
    │ }                                                               │
    └────────────────────────────────────────────────────────────────┘


QUALITY METRICS & ANALYTICS
═══════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────┐
    │ Coverage Analysis                                            │
    ├─────────────────────────────────────────────────────────────┤
    │ ├─ ESCO Coverage:        83.3% (5/6 skills)                │
    │ ├─ DBpedia Coverage:     83.3% (5/6 skills)                │
    │ ├─ Hybrid Coverage:      83.3% (both KBs)                  │
    │ └─ Unresolved:           16.7% (1/6 skills)                │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ Confidence Statistics (Batch)                                │
    ├─────────────────────────────────────────────────────────────┤
    │ ├─ Mean:                 0.92                               │
    │ ├─ Median:               0.95                               │
    │ ├─ Min:                  0.0                                │
    │ ├─ Max:                  0.95                               │
    │ └─ Std Dev:              0.18                               │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ Deduplication Effectiveness                                  │
    ├─────────────────────────────────────────────────────────────┤
    │ ├─ Unique Canonical:     12 skills                          │
    │ ├─ Surface Variants:     18 forms                           │
    │ ├─ Avg Variants/Skill:   1.5                                │
    │ └─ Most Ambiguous:       Node.js (3 variants)               │
    └─────────────────────────────────────────────────────────────┘
```

## Class Dependency Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SkillExtractionPipeline                            │
│                      (Main Orchestrator)                             │
└──────────────┬────────────────────────────────────┬─────────────────┘
               │                                    │
        ┌──────▼─────┐                    ┌────────▼────────┐
        │ SkillNEREx. │                    │ KnowledgeBase   │
        │             │                    │ Normalizer      │
        └──────┬─────┘                    └────────┬────────┘
               │                                    │
               │         ┌────────────────────────┘
               │         │
               │    ┌────▼────────────┐
               │    │  ESCOTaxonomy   │
               │    │  (ESCO lookups) │
               │    └─────────────────┘
               │
               ├────────────────────────┐
               │                        │
        ┌──────▼──────────┐   ┌────────▼──────────┐
        │ DBpediaSpot...  │   │ SkillEntity (DC)  │
        │                 │   │                   │
        └─────────────────┘   └───────────────────┘


Batch Processing:
SkillExtractionPipeline ──→ process_batch() ──→ ResultAggregator
                                              ├─→ QualityMetrics
                                              └─→ ExportManager
                                                  ├─ to_json()
                                                  ├─ to_csv()
                                                  ├─ to_jsonl()
                                                  └─ to_database_schema()
```

## Data Flow Diagram

```
Job Description (Text)
        ↓
        ├─→ Preprocessing (tokenization, normalization)
        │
        ↓
NER Extraction
        ├─→ Pattern Matching (5+ entity types)
        ├─→ Confidence Scoring
        └─→ Context Window Extraction
        ↓
[("Python", TYPE, 0, 6), ("Django", TYPE, 25, 31), ...]
        ↓
        ├─→ ESCO Lookup (exact + fuzzy)
        ├─→ DBpedia Annotation
        └─→ Metadata Retrieval
        ↓
{uri, hierarchy, metadata, confidence}
        ↓
Hierarchical Priority Logic
        ├─→ ESCO Primary? → Assign ESCO URI (0.95)
        ├─→ Add DBpedia? → Enrich metadata (HYBRID)
        ├─→ DBpedia Only? → Use DBpedia (0.75)
        └─→ Nothing? → Mark UNRESOLVED (0.0)
        ↓
Surface Form Resolution
        ├─→ Normalize "Node.js"/"NodeJS" → "Node.js"
        ├─→ Normalize "C++"/"CPP" → "C++"
        └─→ Map to canonical form
        ↓
SkillEntity Objects
        ├─ {surface_form, canonical_name, esco_uri, dbpedia_uri, confidence, ...}
        └─ Sorted by confidence score
        ↓
Statistics Computation
        ├─ Mention count
        ├─ Unique skills
        ├─ Coverage metrics
        └─ Entity type distribution
        ↓
Export
        ├─→ JSON (structured)
        ├─→ CSV (flattened)
        ├─→ JSONL (streaming)
        └─→ Database Schema (SQL)
```

## Configuration Architecture

```
PipelineConfig
├─ NER Settings
│  ├─ ner_model: str
│  ├─ ner_confidence_threshold: float
│  ├─ enable_fuzzy_matching: bool
│  └─ fuzzy_match_threshold: float
│
├─ Entity Linking Settings
│  ├─ dbpedia_confidence_threshold: float
│  └─ use_dbpedia_enrichment: bool
│
├─ Normalization Settings
│  ├─ use_esco_primary: bool
│  ├─ use_dbpedia_fallback: bool
│  └─ resolve_surface_forms: bool
│
├─ Output Settings
│  ├─ output_format: str
│  ├─ include_context_window: bool
│  └─ context_window_size: int
│
└─ Processing Settings
   ├─ batch_size: int
   ├─ max_workers: int
   └─ log_level: str
```

## Scalability Architecture

```
For Increased Volume:

Single Job Processing
        ↓
    ~100-200ms

Batch Processing (100 jobs)
        ├─→ Sequential: ~10-20s
        └─→ Parallel (4 workers): ~5-8s
        
Large-Scale Processing:
        ├─→ Job Queue (Celery/RQ)
        ├─→ Distributed NER
        ├─→ Cached KB Lookups
        └─→ Result Streaming (JSONL)

Database Integration:
        ├─→ Direct SQL INSERT
        ├─→ Bulk Loading
        └─→ Index Creation
```

## Integration Points

```
External Systems:

                    ┌──────────────────┐
                    │  Job Posting API  │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │  Pipeline Input   │
                    │  (Text, CSV, etc) │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │    PIPELINE       │
                    └────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐        ┌─────▼──┐
   │Database  │         │Data      │        │Export  │
   │(SQL)     │         │Warehouse │        │(JSON,  │
   │          │         │          │        │ CSV)   │
   └──────────┘         └──────────┘        └────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼──────────┐
                    │  Analytics/Viz    │
                    │  (Dashboard, BI)  │
                    └───────────────────┘
```

---

**Architecture Version**: 1.0  
**Last Updated**: May 2024  
**Status**: Production-Ready
