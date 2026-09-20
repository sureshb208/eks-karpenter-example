Yes. Based on all four use cases you shared, I would implement this as a **Snowflake-native enterprise search/RAG capability**, not as another FAISS/BM25 application.

The target should be:

```text
                         EXISTING DATA PLATFORM
                                  │
                                  ▼
                                 S3
                                  │
                         Existing ingestion
                                  │
                  ┌───────────────┴────────────────┐
                  │                                │
                  ▼                                ▼
          Structured data                    PDF/Documents
                  │                                │
                  ▼                                ▼
             RAW/TRUSTED                    PARSE_DOCUMENT
                  │                                │
                  ▼                                ▼
       Existing Cortex Analyst              Markdown/Text
          Semantic View                         │
                  │                             ▼
                  │                    SPLIT_TEXT_MARKDOWN_HEADER
                  │                             │
                  │                             ▼
                  │                    DOCUMENT_CHUNKS
                  │                             │
                  │                             ▼
                  │                    CORTEX SEARCH SERVICE
                  │                       │      │      │
                  │                       │      │      │
                  │                    Vector  Keyword Reranking
                  │                       │      │      │
                  └──────────────┬────────┴──────┘
                                 ▼
                          CORTEX AGENT
                                 │
                                 ▼
                     Snowflake Intelligence
                                 │
                                 ▼
                              User
```

Snowflake currently supports Cortex Search as a managed hybrid search service, with vector and keyword retrieval, and supports connecting Cortex Search directly to Cortex Agents. :chatgpt-content-reference{index="0"}

For your first implementation, I would use **Option 2b** from the deployment repo:

> **Consumer-owned data + local Cortex Search + Cortex Agent + Snowflake Intelligence**

Then consider CKE/Native App only if you later need to distribute the search capability to another Snowflake account.

---

# Recommended implementation plan

### Phase 1 — Understand the existing platform

Do **not** create a parallel ingestion system.

The implementation AI should first discover:

- existing S3 buckets/stages
- existing `COPY INTO`
- RAW/TRUSTED tables
- document-related tables
- existing Cortex Analyst semantic view
- Terraform structure
- Snowflake roles/warehouses
- existing deployment conventions
- existing CI/CD

### Phase 2 — Document processing

Create:

```text
DOCUMENT_CONTROL
DOCUMENT_RAW
DOCUMENT_CHUNKS
DOCUMENT_PROCESSING_LOG
```

Flow:

```text
S3 / existing stage
       ↓
DIRECTORY
       ↓
DOCUMENT_CONTROL
       ↓
AI_PARSE_DOCUMENT
       ↓
Markdown/layout
       ↓
SPLIT_TEXT_MARKDOWN_HEADER
       ↓
DOCUMENT_CHUNKS
```

Snowflake's current PDF chatbot tutorial follows essentially this pattern: parse PDFs, preserve layout, then use `SPLIT_TEXT_MARKDOWN_HEADER` to create chunks. :chatgpt-content-reference{index="1"}

### Phase 3 — Cortex Search

Create a dedicated Search service.

Initially:

```text
CHUNK_TEXT
```

as the main search column.

Metadata/attributes:

```text
DOCUMENT_ID
DOCUMENT_TYPE
DOCUMENT_NUMBER
YEAR
LANGUAGE
SOURCE_SYSTEM
```

Use a dedicated warehouse for Search refreshes; Snowflake recommends a dedicated warehouse for each Cortex Search service. :chatgpt-content-reference{index="2"}

### Phase 4 — Search evaluation

Before introducing an Agent, test:

- exact document number
- terminology search
- natural-language question
- semantic query
- year filter
- document-type filter
- multilingual query if required
- source/citation information
- top-5 retrieval quality
- latency

Cortex Search can be queried through SQL `SEARCH_PREVIEW`, Python, or REST. :chatgpt-content-reference{index="3"}

### Phase 5 — Cortex Agent

Connect:

```text
Existing Cortex Analyst Semantic View
+
New Cortex Search Service
```

to one Cortex Agent.

Cortex Agents can use Cortex Analyst for structured data and Cortex Search for unstructured data. :chatgpt-content-reference{index="4"}

### Phase 6 — Snowflake Intelligence

Use Snowflake Intelligence as the user-facing experience where available in your environment.

### Phase 7 — Optional external application

Only if you need a custom UI:

```text
Web/Streamlit
      ↓
Cortex Agent API
      ↓
Cortex Agent
```

Snowflake provides APIs for integrating agents into applications. :chatgpt-content-reference{index="5"}

### Phase 8 — CKE / Native App

Only after the local implementation works:

```text
Provider
   ↓
Cortex Search
   ↓
CKE
   ↓
Private Listing / Marketplace
   ↓
Consumer
   ↓
Agent / Intelligence
```

---

# Important design decision

I would **not immediately use multi-index Cortex Search**.

Start with:

```text
ON CHUNK_TEXT
```

and metadata attributes.

Once testing shows that exact identifiers such as:

```text
Circular 015/2024
Resolution 203/2024
Article 17
Policy ABC-123
```

need stronger lexical treatment, evaluate the newer multi-index capability.

Snowflake now supports separate text and vector indexes, including combinations where one column is used for lexical search and another for vector search. :chatgpt-content-reference{index="6"}

Also, don't blindly use the embedding model from the example repo. Your multilingual requirement needs to be explicitly evaluated against the models available in your Snowflake region. Snowflake's current documentation lists multiple embedding options and notes model/context considerations. :chatgpt-content-reference{index="7"}

---

# Master prompt for your internal project AI

You can paste the following as **one implementation prompt**. I deliberately made it tell the AI to **inspect the existing project first and not invent infrastructure**.


# Implement Enterprise Document Search and RAG using Snowflake Cortex Search

## Objective

Implement a production-oriented, Snowflake-native document search and RAG capability in the existing enterprise data platform.

The goal is to add document search to the existing Snowflake environment without rebuilding the existing S3 ingestion, COPY INTO pipelines, RAW/TRUSTED data model, or Cortex Analyst implementation.

The target architecture is:

```text
Existing S3 / document source
        |
        v
Existing Snowflake ingestion/stage
        |
        v
Document processing
        |
        +--> AI_PARSE_DOCUMENT
        |
        +--> SPLIT_TEXT_MARKDOWN_HEADER
        |
        v
DOCUMENT_CHUNKS
        |
        v
CORTEX SEARCH SERVICE
        |
        +--> Vector retrieval
        +--> Keyword retrieval
        +--> Semantic ranking
        |
        v
Cortex Agent
        |
        +----------------------+
        |                      |
        v                      v
Cortex Analyst          Cortex Search
(existing semantic      (new document
 view)                   retrieval)
        |                      |
        +----------+-----------+
                   |
                   v
              Final answer
                   |
                   v
          Snowflake Intelligence
          or application UI
```

The initial deployment model must be:

**Consumer-owned data + local Cortex Search + Cortex Agent + Snowflake Intelligence/application.**

Do NOT implement Cortex Knowledge Extension, Marketplace, or Native App distribution in the first phase unless the existing repository already requires it.

Those should be treated as a future provider/consumer distribution phase.

---

# 1. First inspect the existing repository

Before changing any code, inspect the entire repository and identify:

1. Repository structure.
2. Existing Terraform modules.
3. Snowflake database/schema configuration.
4. Existing Snowflake roles.
5. Existing warehouses.
6. Existing S3 buckets.
7. Existing Snowflake stages.
8. Existing COPY INTO processes.
9. Existing RAW tables.
10. Existing TRUSTED tables.
11. Existing document-related tables.
12. Existing stored procedures/tasks/streams.
13. Existing Cortex Analyst semantic views.
14. Existing Cortex Agent objects, if any.
15. Existing CI/CD/deployment mechanism.
16. Environment separation such as DEV/UAT/PROD.
17. Existing naming conventions.
18. Existing secrets-management approach.
19. Existing monitoring/audit patterns.
20. Existing Terraform state/workspace conventions.

Do not create duplicate infrastructure if an existing object can safely be reused.

Do not invent database names, schema names, warehouse names, stages, buckets, roles, or table names.

Create an implementation discovery document first containing:

```text
Existing architecture
Existing ingestion path
Existing Snowflake objects
Existing Cortex Analyst objects
Existing deployment process
Objects that can be reused
Objects that must be created
Objects requiring clarification
```

If something critical is missing, mark it as:

`REQUIRES_INPUT`

instead of inventing a value.

---

# 2. Preserve the existing ingestion architecture

The existing data flow is conceptually:

```text
S3
 |
 v
COPY INTO
 |
 v
RAW
 |
 v
TRUSTED
```

Do not replace this with a new standalone PDF upload application.

The Cortex Search implementation must integrate with the existing ingestion architecture.

If documents already arrive through S3, continue using S3 as the source.

If an existing Snowflake stage already points to the required document location, reuse it where appropriate.

If a new document-specific stage is required, explain why before creating it.

---

# 3. Create document-control metadata

Design a document-control table that tracks the lifecycle of every searchable document.

Minimum conceptual fields:

```text
DOCUMENT_ID
FILE_NAME
RELATIVE_PATH
FILE_SIZE
FILE_LAST_MODIFIED
DOCUMENT_TYPE
DOCUMENT_NUMBER
YEAR
LANGUAGE
SOURCE_SYSTEM
STATUS
PROCESSING_STARTED_AT
PROCESSING_COMPLETED_AT
ERROR_MESSAGE
TOTAL_CHUNKS
CREATED_AT
UPDATED_AT
```

Adapt the actual names and types to the existing Snowflake standards.

The table must support:

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

and safe reprocessing.

The implementation must be idempotent.

Processing the same document twice must not create uncontrolled duplicate chunks.

---

# 4. Parse PDF documents using Snowflake-native functionality

Use Snowflake Cortex document parsing where supported by the existing account/version.

Preferred conceptual flow:

```text
Snowflake stage
      |
      v
AI_PARSE_DOCUMENT / supported Cortex document parsing
      |
      v
Markdown/layout-aware extracted text
```

Preserve document structure whenever possible.

For PDFs containing:

- headings
- sections
- tables
- page information
- document identifiers

retain that information where practical.

Do not immediately flatten all document information into plain text.

The implementation must preserve enough metadata to provide useful citations/source references later.

---

# 5. Chunk documents using structure-aware chunking

Use:

```text
SNOWFLAKE.CORTEX.SPLIT_TEXT_MARKDOWN_HEADER
```

where the extracted document is Markdown-compatible.

Preserve heading information such as:

```text
header_1
header_2
header_3
```

where useful.

The resulting chunk should contain both:

1. The actual text.
2. The document/section context.

Conceptual searchable content:

```text
Document: <document title>
Document Number: <document number>
Section: <section hierarchy>

<chunk text>
```

Do not blindly concatenate all document metadata into the search text.

Keep filterable metadata as separate columns.

Use chunk sizes appropriate for Cortex Search retrieval.

Start with a conservative chunk size and validate retrieval quality rather than assuming one fixed value is universally optimal.

Snowflake currently recommends relatively small chunks for Cortex Search retrieval, with approximately 512 tokens as a general recommendation for the standard embedding path.

---

# 6. Create DOCUMENT_CHUNKS

Create a durable chunk table.

Minimum conceptual structure:

```text
CHUNK_ID
DOCUMENT_ID
DOCUMENT_TITLE
DOCUMENT_NUMBER
DOCUMENT_TYPE
YEAR
LANGUAGE
SOURCE_SYSTEM
SOURCE_FILE
SOURCE_PATH
PAGE_NUMBER
SECTION_PATH
CHUNK_SEQUENCE
CHUNK_TEXT
CREATED_AT
UPDATED_AT
```

Adapt this to the existing enterprise naming standards.

Important:

`CHUNK_ID` must be deterministic.

For example, it may be based on:

```text
DOCUMENT_ID + CHUNK_SEQUENCE
```

so reprocessing can be handled safely.

The table must retain enough metadata to trace every search result back to the source document.

---

# 7. Build the Cortex Search source

Use DOCUMENT_CHUNKS as the primary source unless the existing architecture requires a view.

If a view is better, create:

```text
DOCUMENT_SEARCH_SOURCE
```

and keep the underlying chunk table separate.

The searchable field should contain the chunk context plus the actual text where beneficial.

Example conceptual structure:

```text
SEARCH_TEXT =
    document title
    + document number
    + section path
    + chunk text
```

Do not assume this exact SQL; adapt it to the actual schema.

---

# 8. Create Cortex Search Service

Create a dedicated Cortex Search Service over the document chunks.

Initial design:

```text
Search column:
    SEARCH_TEXT or CHUNK_TEXT

Primary key:
    CHUNK_ID

Attributes:
    DOCUMENT_ID
    DOCUMENT_TYPE
    DOCUMENT_NUMBER
    YEAR
    LANGUAGE
    SOURCE_SYSTEM
```

Use a dedicated Snowflake warehouse for Cortex Search refreshes if appropriate.

Configure:

```text
TARGET_LAG
WAREHOUSE
EMBEDDING_MODEL
REFRESH_MODE
```

according to the existing environment and current Snowflake capabilities.

Do not hard-code an embedding model without checking:

1. Current Snowflake-supported models.
2. Current account/region availability.
3. Language requirements.
4. Expected document language.
5. Context-window requirements.
6. Cost/quality implications.

If documents are multilingual, explicitly evaluate a supported multilingual embedding model.

Do not assume `snowflake-arctic-embed-m-v1.5` is appropriate for multilingual content.

---

# 9. Do not recreate FAISS/BM25/RRF

Do NOT introduce:

```text
FAISS
BM25
RRF
custom embedding indexes
custom vector database
custom semantic reranker
```

The purpose of this implementation is to use managed Snowflake Cortex Search.

The old custom RAG architecture can remain as an evaluation/reference implementation, but it must not become part of the new production retrieval path unless a concrete requirement cannot be fulfilled by Cortex Search.

The conceptual replacement is:

```text
FAISS
+
BM25
+
RRF
+
custom reranker
```

becomes:

```text
Cortex Search
```

Cortex Search provides managed hybrid retrieval and ranking.

---

# 10. Create search test cases

Before integrating Cortex Agent, create a repeatable search evaluation suite.

Include at least:

## Exact keyword

```text
Search for a known document number.
```

Example:

```text
Circular 015/2024
```

## Semantic query

```text
What are the requirements for EPS habilitation?
```

## Synonym query

Use a query where the user's terminology differs from the document terminology.

## Section-specific query

Ask about a known section.

## Metadata-filtered query

Example:

```text
Query:
requirements for EPS

Filter:
YEAR = 2024
```

## Document-type filter

Example:

```text
DOCUMENT_TYPE = CIRCULAR
```

## Multilingual query

If the corpus is multilingual, test queries in each important language.

---

# 11. Capture search evaluation metrics

Build a small evaluation dataset:

```text
QUERY
EXPECTED_DOCUMENT
EXPECTED_CHUNK
EXPECTED_METADATA
LANGUAGE
```

Evaluate:

```text
Precision@K
Recall@K
MRR
NDCG@K
Latency
```

At minimum compare:

```text
Top 1
Top 3
Top 5
```

Do not claim the search is production-ready until representative queries have been evaluated.

---

# 12. Validate filters and security

Document search must respect enterprise data governance.

Identify whether documents require:

```text
department
business_unit
region
country
security_classification
source_system
tenant
```

If required, design appropriate metadata attributes and filters.

Do not expose sensitive document metadata unnecessarily.

Do not put sensitive information into metadata merely for convenience.

Review Snowflake's current Cortex Search metadata/security requirements before implementation.

---

# 13. Connect Cortex Search to Cortex Agent

After search quality is validated, create/configure a Cortex Agent.

The Agent must have:

### Tool 1

Existing Cortex Analyst semantic view.

Purpose:

```text
Structured business data
```

### Tool 2

New Cortex Search Service.

Purpose:

```text
Unstructured documents
```

Configure useful:

```text
Search service description
ID column
Title column
Searchable columns
Filterable attributes
Column descriptions
Maximum result count
```

The agent instructions should explicitly explain when to use each tool.

Example:

```text
Use Cortex Analyst for questions requiring structured
business metrics, calculations, aggregations, trends,
counts, dimensions, or SQL-based analysis.

Use Cortex Search for questions asking about document
content, policies, regulations, explanations, definitions,
requirements, procedures, or textual evidence.

When a question requires both structured data and document
knowledge, use both tools and combine the results.
```

---

# 14. Configure source citations

Search responses must preserve document provenance.

Where possible, return:

```text
DOCUMENT_TITLE
DOCUMENT_NUMBER
SOURCE_FILE
SOURCE_PATH
PAGE_NUMBER
SECTION_PATH
CHUNK_ID
```

The Agent should provide citations/source references rather than presenting document-derived information as unsupported text.

If the Cortex Search Service is based on staged files and the current Snowflake Agent capabilities support source-file hyperlinks, configure the relevant ID/source path columns appropriately.

---

# 15. Test Cortex Agent routing

Create tests for:

### Analyst-only

```text
How many transactions failed in 2025?
```

Expected:

```text
Cortex Analyst
```

### Search-only

```text
What does the policy say about failed transactions?
```

Expected:

```text
Cortex Search
```

### Combined

```text
How many transactions failed in 2025 and what
policy requirements apply to those failures?
```

Expected:

```text
Cortex Analyst
+
Cortex Search
```

### Ambiguous question

Verify that the Agent selects the appropriate tool based on the configured descriptions/instructions.

---

# 16. Evaluate analytical search if applicable

If the document use case requires questions such as:

```text
How many documents mention X?

Which regulations mention X most frequently?

How many incidents are described across these documents?

What are the trends across the document collection?
```

evaluate Cortex Agent's analytical search capability.

Do not enable it blindly.

First determine whether the business use case requires aggregation across a document collection rather than normal top-K retrieval.

If enabled, document why it is required and test its additional cost/latency.

---

# 17. Snowflake Intelligence integration

Once the Agent works correctly:

```text
Cortex Agent
      |
      v
Snowflake Intelligence
```

Validate:

1. User authentication.
2. Agent visibility.
3. Role permissions.
4. Search permissions.
5. Analyst permissions.
6. Source citations.
7. Conversation context.
8. Error handling.

Do not build a custom chat UI until the native Agent/Intelligence workflow has been validated.

---

# 18. Optional custom application

If a custom UI is required after the native Snowflake workflow is proven:

```text
Streamlit / Web UI
       |
       v
Cortex Agent API
       |
       v
Cortex Agent
       |
       +--> Cortex Analyst
       |
       +--> Cortex Search
```

Do not build custom FAISS, BM25, embedding, or RAG orchestration in the application.

The application should primarily handle:

```text
authentication
conversation UI
file/source presentation
feedback
application-specific UX
```

and delegate AI orchestration to Snowflake.

---

# 19. Terraform and deployment

If the repository uses Terraform, implement infrastructure using the existing Terraform conventions.

Before adding Terraform:

1. Inspect current Snowflake provider version.
2. Check whether required Cortex Search/Agent resources are supported by that provider version.
3. If native Terraform resources are unavailable, use the existing approved deployment mechanism rather than inventing unsafe workarounds.
4. Keep SQL object creation version-controlled.
5. Separate environment-specific configuration from reusable modules.

Recommended conceptual structure:

```text
terraform/
  snowflake/
    database/
    schemas/
    roles/
    warehouses/
    stages/
    document_processing/
    cortex_search/
    cortex_agent/
```

But adapt this to the repository's existing structure.

Do not create a new repository structure if an established one already exists.

---

# 20. CI/CD

All objects must be deployable through the existing CI/CD process.

The deployment must support:

```text
DEV
UAT
PROD
```

where those environments already exist.

Do not require manual Snowsight changes for production deployment if the existing platform follows infrastructure-as-code.

Any unavoidable manual step must be explicitly documented.

---

# 21. Monitoring

Implement operational monitoring for:

```text
documents discovered
documents processed
documents failed
documents reprocessed
chunk counts
processing duration
search refresh status
search service health
Agent failures
query latency
```

Create useful audit queries/views.

At minimum expose:

```text
document processing status
last successful processing
last failure
failure reason
chunk count
```

---

# 22. Cost controls

Document:

1. Cortex parsing cost.
2. Cortex AI enrichment cost if used.
3. Cortex Search refresh cost.
4. Cortex Search warehouse usage.
5. Cortex Agent consumption.
6. Cortex Analyst consumption.
7. Optional analytical search cost.

Do not introduce `CORTEX.COMPLETE` metadata enrichment unless there is a demonstrated business need.

Prefer deterministic metadata extraction where possible.

---

# 23. Do not over-engineer the first release

The first production candidate should contain only:

```text
Existing S3 ingestion
        ↓
Document control
        ↓
PDF parsing
        ↓
Structure-aware chunking
        ↓
DOCUMENT_CHUNKS
        ↓
Cortex Search
        ↓
Search evaluation
        ↓
Cortex Agent
        ↓
Existing Cortex Analyst
        ↓
Snowflake Intelligence
```

Do NOT initially add:

```text
Native App
Marketplace
CKE
FAISS
BM25
MongoDB
custom vector database
custom LLM orchestration
custom reranker
custom embedding service
```

unless the existing requirements specifically demand them.

---

# 24. Future provider/consumer architecture

After the local consumer-owned implementation is stable, document how it could evolve into:

```text
PROVIDER ACCOUNT

Documents
   ↓
Cortex Search
   ↓
Cortex Knowledge Extension
   ↓
Private Listing / Marketplace
   ↓
CONSUMER ACCOUNT
   ↓
Cortex Agent
   ↓
Snowflake Intelligence
```

This is a future phase.

Do not implement this phase unless requested.

---

# 25. Required deliverables

Produce the following implementation artifacts.

## A. Architecture document

Create:

```text
docs/cortex-search-architecture.md
```

Include:

- current architecture
- target architecture
- data flow
- search flow
- Agent flow
- Analyst integration
- security
- monitoring
- deployment
- future CKE architecture

Include Mermaid diagrams where useful.

## B. Data model

Create documentation for:

```text
DOCUMENT_CONTROL
DOCUMENT_RAW
DOCUMENT_CHUNKS
DOCUMENT_PROCESSING_LOG
```

using the actual names selected from the existing repository.

## C. SQL

Create version-controlled SQL for:

```text
tables
stages if required
procedures/functions if required
Cortex Search Service
Agent configuration if SQL is supported
test queries
monitoring queries
```

Use the repository's existing SQL conventions.

## D. Terraform

Implement required infrastructure through the existing Terraform architecture where supported.

## E. Search evaluation

Create:

```text
docs/cortex-search-evaluation.md
```

with test cases and measured results.

## F. Agent evaluation

Create:

```text
docs/cortex-agent-evaluation.md
```

with:

```text
question
expected tool
actual tool
expected answer/source
actual result
status
```

## G. Runbook

Create:

```text
docs/cortex-search-runbook.md
```

covering:

- deployment
- document ingestion
- reprocessing
- failures
- search refresh
- validation
- rollback
- monitoring

---

# 26. Acceptance criteria

The implementation is considered successful only when:

### Data

- Existing S3 ingestion continues to work.
- Documents can be discovered and processed.
- PDF text is extracted.
- Documents are chunked.
- Chunks are traceable to source documents.
- Processing is idempotent.

### Search

- Cortex Search Service is created successfully.
- Semantic searches work.
- Exact keyword searches work.
- Metadata filters work.
- Source metadata is returned.
- Search latency is measured.
- Search quality is evaluated.

### Agent

- Cortex Search is available as an Agent tool.
- Existing Cortex Analyst remains available.
- Structured questions route to Analyst.
- Document questions route to Search.
- Combined questions can use both.
- Citations/source references are preserved.

### Operations

- Terraform/SQL deployment is repeatable.
- DEV/UAT/PROD configuration is separated.
- Processing failures are visible.
- Search refreshes are monitored.
- Costs are documented.
- No manual production-only configuration is introduced unnecessarily.

---

# 27. Important implementation rules

Follow these rules throughout the implementation:

1. Inspect before modifying.
2. Reuse existing infrastructure.
3. Do not invent existing object names.
4. Do not rebuild the S3/COPY INTO pipeline.
5. Do not build FAISS.
6. Do not build BM25.
7. Do not build a custom vector database.
8. Do not build a custom reranker unless a documented requirement cannot be met by Cortex Search.
9. Do not assume the default embedding model is appropriate for multilingual data.
10. Verify current Snowflake feature availability in the target account/region.
11. Do not expose sensitive document metadata unnecessarily.
12. Preserve document provenance.
13. Make document processing idempotent.
14. Keep infrastructure and SQL version-controlled.
15. Do not introduce Native App/CKE/Marketplace in the first implementation phase.
16. Prefer Cortex Analyst for structured data.
17. Prefer Cortex Search for unstructured document retrieval.
18. Use Cortex Agent for orchestration between structured and unstructured tools.
19. Validate search quality before optimizing or expanding the architecture.
20. Do not claim production readiness without test evidence.

---

# 28. Final implementation report

At the end, provide:

```text
1. Existing architecture discovered
2. Changes made
3. New Snowflake objects
4. New Terraform objects
5. New SQL
6. Cortex Search configuration
7. Embedding model selected and why
8. Chunking strategy
9. Search attributes/filters
10. Cortex Agent configuration
11. Cortex Analyst integration
12. Security model
13. Test results
14. Performance results
15. Cost considerations
16. Known limitations
17. Manual steps, if any
18. Rollback procedure
19. Future CKE/Native App architecture
20. Recommended next steps
```

Do not simply provide generic instructions.

Inspect the actual repository and produce implementation changes that fit its existing architecture and conventions.

---

## One thing I would add to that prompt for your environment

Because your existing platform is already heavily **Terraform + Snowflake + AWS/S3**, I would make the internal AI follow this priority:

```text
Existing Terraform
       ↓
Existing S3 ingestion
       ↓
Existing Snowflake RAW/TRUSTED
       ↓
Existing Cortex Analyst
       ↓
NEW:
Document chunks
       ↓
Cortex Search
       ↓
Cortex Agent
```

rather than allowing it to create a standalone `salud-cortex-search` style demo environment.

Also, don't let it automatically convert everything to a new application. Snowflake's current Cortex Search APIs already support SQL, Python, and REST querying, and Cortex Search can be directly attached to Cortex Agents. :chatgpt-content-reference{index="8"}

### The final target I would use

```text
                 ┌─────────────────────────┐
                 │      S3 / Documents     │
                 └────────────┬────────────┘
                              │
                              ▼
                    Existing ingestion
                              │
                              ▼
                       RAW / TRUSTED
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
             Existing data       Document processing
                    │                   │
                    ▼                   ▼
             Semantic View       DOCUMENT_CHUNKS
                    │                   │
                    ▼                   ▼
            Cortex Analyst       Cortex Search
                    │                   │
                    └────────┬──────────┘
                             ▼
                       Cortex Agent
                             │
                             ▼
                  Snowflake Intelligence
                             │
                             ▼
                           User
```

This gives you **one governed Snowflake AI layer for both structured and unstructured data**, rather than maintaining separate Analyst, RAG, vector DB, and chatbot stacks. Snowflake's current Agent architecture explicitly supports combining Cortex Analyst and Cortex Search in this way. :chatgpt-content-reference{index="9"}

And for the first version, I'd keep **CKE/Native App as Phase 2**, because those solve **distribution across accounts**, not the core search problem.