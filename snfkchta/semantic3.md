Yes. Based on our discussions and your `investment-ai-pipeline` project, I would give the AI coding tool a **single implementation brief** rather than sending all the previous discussion.

The important point is: **we should reuse the engineering patterns from your project, but not copy the financial-market schema into your existing Snowflake semantic-service project.** Your project demonstrates specialized agents, versioned skills, deterministic SQL/Python execution, auditability, data-quality gates, idempotency, and governed semantic objects. 

Your existing project already follows a similar separation between analytical data and a Semantic View, and the Semantic View is intended as a future AI consumption layer. 

## Copy/paste this into your AI coding tool

```text
# IMPLEMENTATION BRIEF
# Snowflake Semantic Discovery + Context + Semantic View Service

## 1. OBJECTIVE

Enhance the existing Snowflake Semantic Service.

Current system:

Snowflake tables/views
        ↓
Table/column metadata
        ↓
Azure GPT-4o
        ↓
AI-generated table/column descriptions
        ↓
User reviews/edits/approves
        ↓
Semantic YAML
        ↓
CREATE/DEPLOY SEMANTIC VIEW

The current weakness is that metadata alone does not contain enough business meaning.

We need to evolve the system into an evidence-driven semantic discovery and governance platform.

Target:

Business Use Case / Questions
        ↓
Semantic Discovery
        ↓
Evidence / Context Layer
        ↓
Azure GPT-4o reasoning
        ↓
Semantic Candidates
        ↓
Human Review / Approval
        ↓
Semantic YAML
        ↓
Validation
        ↓
Snowflake Semantic View
        ↓
Cortex Analyst
        ↓
Cortex Search
        ↓
Cortex Agent
        ↓
Natural-language business answers

Do NOT rebuild the physical Snowflake data model just to make it AI-friendly.

Use the existing refined/reporting tables and views wherever possible.


--------------------------------------------------
## 2. CORE PRINCIPLE
--------------------------------------------------

Use this principle throughout the implementation:

"AI proposes.
Evidence supports.
Humans approve.
Snowflake executes."

The LLM must NOT become the source of business truth.

The LLM should interpret evidence and propose:

- table purpose
- table grain
- column meaning
- column role
- business terminology
- synonyms/aliases where useful
- dimensions
- measures
- metrics
- filters
- relationships
- candidate business definitions
- verified questions

Human approval is required before business-critical semantics become governed Semantic View definitions.

Never silently invent a business definition.

If evidence is insufficient, mark the candidate as:

UNKNOWN
or
REVIEW_REQUIRED

instead of hallucinating.


--------------------------------------------------
## 3. IMPORTANT DESIGN DECISION
--------------------------------------------------

Do NOT require the existing warehouse to be converted into a traditional:

FACT
DIMENSION
FACT
DIMENSION

model.

The semantic layer should be a VIRTUAL BUSINESS MODEL over the existing physical/refined/reporting objects.

Existing views are valuable sources of business meaning.

For example:

existing reporting view SQL can reveal:

- business-friendly aliases
- joins
- calculated fields
- aggregations
- filters
- metric formulas
- business terminology

Therefore, analyze existing view definitions and SQL before asking the LLM to invent semantics.


--------------------------------------------------
## 4. SEMANTIC DISCOVERY / EVIDENCE LAYER
--------------------------------------------------

Introduce an intermediate layer between Snowflake metadata and Semantic YAML.

Architecture:

Snowflake metadata
        +
Data profiling
        +
View SQL analysis
        +
Query history
        +
Existing semantic views
        +
dbt/SQL transformations if available
        +
BI definitions if available
        +
Bitbucket/Confluence/business documents
        ↓
SEMANTIC CONTEXT / EVIDENCE
        ↓
Azure GPT-4o
        ↓
SEMANTIC CANDIDATES


The evidence layer should capture WHY a semantic candidate was proposed.


--------------------------------------------------
## 5. EVIDENCE SOURCES
--------------------------------------------------

Implement evidence collection from the following sources where technically available.

Priority order:

1. Snowflake metadata
2. Data profiling
3. Existing view definitions / SQL
4. Query history
5. Existing semantic views
6. dbt / transformation SQL
7. BI definitions / metrics
8. Business documentation
9. Bitbucket repository documentation
10. Confluence / other enterprise documentation

Do not require all sources for the first implementation.

Build the system so new evidence sources can be added later.


--------------------------------------------------
## 6. DATA PROFILING
--------------------------------------------------

For selected tables/columns collect deterministic profiling information.

Table-level:

- database
- schema
- table/view name
- row count
- approximate row count if appropriate
- table type
- last modified information if available

Column-level:

- column name
- data type
- nullable
- null count
- null percentage
- distinct count
- distinct ratio
- min
- max
- sample values
- pattern information where useful

Potential semantic clues:

CUSTOMER_ID
→ identifier candidate

REGION
→ dimension candidate

ORDER_DATE
→ time dimension candidate

ORDER_AMOUNT
→ measure candidate

Do not automatically convert these clues into approved business definitions.


--------------------------------------------------
## 7. TABLE GRAIN
--------------------------------------------------

Table grain must become a first-class semantic concept.

For every logical table/view attempt to determine:

"What does one row represent?"

Examples:

customer
customer + transaction
product + day
order
order + order line

Capture:

table_grain
grain_columns
grain_confidence
grain_evidence

If grain cannot be reliably determined:

status = REVIEW_REQUIRED


This is important because downstream metrics and relationships depend on grain.


--------------------------------------------------
## 8. COLUMN ROLE DISCOVERY
--------------------------------------------------

Generate candidate roles such as:

- identifier
- foreign key
- dimension
- measure
- date
- timestamp
- status
- category
- descriptive attribute
- technical field
- audit field
- metric component

Each candidate must include:

candidate_id
object_name
column_name
candidate_type
candidate_value
confidence
evidence
source
status


--------------------------------------------------
## 9. RELATIONSHIP DISCOVERY
--------------------------------------------------

Discover potential relationships using deterministic evidence.

Possible checks:

- same/similar column names
- matching data types
- uniqueness
- value-subset checks
- null patterns
- join frequency in existing SQL
- query history join patterns

Candidate relationship example:

CUSTOMER.customer_id
        ↓
ORDERS.customer_id

Capture:

parent_object
parent_column
child_object
child_column
relationship_type
cardinality
confidence
evidence
status

The AI can suggest relationships.

Human approval must confirm business correctness.

Do not blindly create relationships based only on column-name similarity.


--------------------------------------------------
## 10. METRIC DISCOVERY
--------------------------------------------------

Metric discovery should be evidence-driven.

Look at:

- existing SQL calculations
- reporting views
- BI formulas
- query history
- existing semantic definitions
- business documentation

Examples:

SUM(NET_AMOUNT)
AVG(ORDER_AMOUNT)
COUNT(DISTINCT CUSTOMER_ID)

These can become metric candidates.

Do NOT automatically rename:

NET_AMOUNT → Revenue

unless business evidence supports that definition.

Capture:

metric_name
expression
business_description
source_object
source_columns
evidence
confidence
status


--------------------------------------------------
## 11. QUERY HISTORY MINING
--------------------------------------------------

Query history is an important source of semantic evidence.

Analyze frequently used:

- GROUP BY columns
- WHERE filters
- JOIN columns
- aggregations
- date filters
- metric expressions
- frequently requested business questions

Examples:

frequent GROUP BY REGION
→ REGION is likely a business dimension

frequent SUM(NET_AMOUNT)
→ NET_AMOUNT is likely an important measure

frequent filtering by ORDER_STATUS
→ ORDER_STATUS may be an important business filter

Frequent usage increases confidence, but usage alone does not establish business truth.


--------------------------------------------------
## 12. VIEW / SQL ANALYSIS
--------------------------------------------------

Analyze existing views and transformation SQL.

Extract:

- source tables
- joins
- join keys
- aliases
- calculated columns
- CASE statements
- aggregation logic
- filters
- business labels
- metric formulas

Existing reporting views should be treated as strong semantic evidence because they represent how the organization already consumes the data.


--------------------------------------------------
## 13. BUSINESS KNOWLEDGE
--------------------------------------------------

Support unstructured business knowledge.

Potential sources:

- Bitbucket
- Confluence
- Markdown
- documentation
- runbooks
- business glossary
- metric definitions
- policies
- data dictionaries

Recommended architecture:

Bitbucket / Confluence / documents
        ↓
SOURCE_DOCUMENTS
        ↓
document processing / chunking
        ↓
KNOWLEDGE_CANDIDATES
        ↓
AI extraction
        ↓
Human approval
        ↓
APPROVED_KNOWLEDGE
        ↓
Cortex Search


Cortex Search is a retrieval layer, NOT the master source of truth.


--------------------------------------------------
## 14. CONTEXT / EVIDENCE DATABASE
--------------------------------------------------

Create a persistent evidence layer.

Recommended tables:

SEMANTIC_RUN

Fields:

run_id
run_type
started_at
completed_at
status
model_name
model_version
created_by


SEMANTIC_CONTEXT_EVIDENCE

Fields:

evidence_id
run_id
object_type
object_name
column_name
signal_type
source_system
source_name
evidence_text
evidence_value
authority_score
popularity_score
freshness_score
relevance_score
observed_at
source_updated_at
created_at


SEMANTIC_CANDIDATE

Fields:

candidate_id
run_id
object_type
object_name
column_name
candidate_type
candidate_value
description
confidence
evidence_ids
source_types
status
reviewed_by
reviewed_at
created_at
updated_at


SEMANTIC_CONFLICT

Fields:

conflict_id
object_name
candidate_type
candidate_a
candidate_b
evidence_a
evidence_b
severity
status
resolution
resolved_by
resolved_at


VERIFIED_QUERY

Fields:

verified_query_id
semantic_view
business_question
expected_sql
description
source
status
created_at
updated_at


Optional:

KNOWLEDGE_DOCUMENT
KNOWLEDGE_CANDIDATE
KNOWLEDGE_AUDIT


--------------------------------------------------
## 15. EVIDENCE SCORING
--------------------------------------------------

Use evidence ranking conceptually based on:

- relevance
- authority
- popularity
- freshness

Example:

Business-approved glossary
    > BI governed metric
    > existing semantic definition
    > production reporting SQL
    > frequently used query
    > metadata inference
    > LLM-only inference

Do not hard-code these rankings too aggressively.

Make scoring configurable.

Most importantly, conflicting evidence must be surfaced rather than silently resolved.


--------------------------------------------------
## 16. AZURE GPT-4o ROLE
--------------------------------------------------

The existing Azure GPT-4o-like model has a large context window.

Do NOT send the entire warehouse metadata/context every time.

Large context capacity does not mean all context should be sent.

Use retrieval and targeted context.

Pipeline:

retrieve relevant evidence
        ↓
build focused context package
        ↓
GPT-4o reasoning
        ↓
structured JSON candidate output


The LLM should:

1. interpret evidence
2. identify likely semantic meaning
3. generate candidates
4. assign confidence
5. explain reasoning
6. identify conflicts
7. identify missing evidence

The LLM should NOT:

- directly change Snowflake objects
- invent metrics
- silently resolve conflicting definitions
- calculate authoritative business metrics itself
- approve its own candidates


--------------------------------------------------
## 17. GPT OUTPUT CONTRACT
--------------------------------------------------

Force structured JSON output.

Example:

{
  "table": {
    "name": "ORDERS",
    "purpose": "...",
    "grain": "...",
    "confidence": 0.91,
    "evidence_ids": ["..."]
  },

  "columns": [
    {
      "name": "ORDER_AMOUNT",
      "role": "measure",
      "description": "...",
      "confidence": 0.94,
      "evidence_ids": ["..."]
    }
  ],

  "metrics": [
    {
      "name": "Total Order Amount",
      "expression": "SUM(ORDER_AMOUNT)",
      "confidence": 0.88,
      "evidence_ids": ["..."],
      "status": "REVIEW_REQUIRED"
    }
  ],

  "relationships": [],

  "business_terms": [],

  "conflicts": []
}


No free-form output should be used as the system-of-record semantic definition.


--------------------------------------------------
## 18. HUMAN REVIEW UI
--------------------------------------------------

The existing UI currently allows:

AI description
→ edit
→ approve

Change this to:

AI Semantic Discovery
        ↓
Table Purpose
Table Grain
Column Meaning
Column Role
Business Terms
Dimensions
Measures
Metric Candidates
Relationships
Filters
Evidence
Confidence
Conflicts
        ↓
Human Review
        ↓
Approve / Edit / Reject


Every candidate should show:

"What evidence caused the AI to suggest this?"

Example:

Candidate:
NET_AMOUNT = measure

Confidence:
92%

Evidence:
- Used in VW_SALES_REPORT
- SUM(NET_AMOUNT) appears in 17 queries
- BI report uses "Net Sales"
- Numeric decimal column
- Existing SQL alias = NET SALES


This makes the system explainable.


--------------------------------------------------
## 19. SEMANTIC YAML GENERATION
--------------------------------------------------

Only approved candidates should be converted into Semantic YAML.

Flow:

SEMANTIC_CANDIDATE
        ↓
APPROVED
        ↓
Semantic YAML Generator
        ↓
Validation
        ↓
Git/version control
        ↓
CREATE/ALTER SEMANTIC VIEW


The generated Semantic View should contain only business-relevant objects.

Avoid exposing every technical column.

Semantic View organization should be based on:

business domain
+
business use case
+
how users ask questions

NOT simply:

database/schema/table hierarchy.


--------------------------------------------------
## 20. SEMANTIC VIEW DESIGN
--------------------------------------------------

For an initial POC:

- approximately 5–10 related tables
- one clear business domain
- only relevant columns
- clear table descriptions
- clear column descriptions
- relationships
- dimensions
- measures
- metrics
- filters
- verified queries
- custom instructions where needed

Do not create one huge Semantic View containing the entire enterprise warehouse.

Do not create many tiny views unnecessarily.

Tables that frequently join and belong to the same business domain can be grouped.

Clearly separate domains should have separate Semantic Views.


--------------------------------------------------
## 21. HIGH-CARDINALITY TEXT
--------------------------------------------------

Do not put large high-cardinality text domains entirely into the Semantic View.

Examples:

customer names
product names
large textual descriptions
free-form business content

Use Cortex Search where literal/entity resolution or unstructured retrieval is needed.

Semantic View:
structured business semantics

Cortex Search:
unstructured knowledge + high-cardinality literal retrieval


--------------------------------------------------
## 22. VERIFIED QUESTIONS
--------------------------------------------------

Create a set of verified business questions.

Initial target:

10–20 representative questions.

Examples:

- What were total sales last month?
- What are sales by region?
- Which product category had the highest sales?
- What was the average order value?
- How many active customers do we have?

For every verified question store:

business question
expected SQL
semantic view
description
status

Verified queries become:

- accuracy examples
- regression tests
- evaluation ground truth
- documentation of business meaning


--------------------------------------------------
## 23. EVALUATION LOOP
--------------------------------------------------

Do not stop after creating the Semantic View.

Create continuous evaluation:

Verified Questions
        ↓
Cortex Analyst
        ↓
Generated SQL / Answer
        ↓
Compare against expected result
        ↓
Evaluation
        ↓
Identify semantic gaps
        ↓
Improve Semantic View / Knowledge
        ↓
Re-test


Track:

- SQL correctness
- answer correctness
- missing relationships
- incorrect metric selection
- incorrect filters
- terminology problems
- latency
- regression


--------------------------------------------------
## 24. RUNTIME ARCHITECTURE
--------------------------------------------------

Use Cortex Agent as the orchestration layer.

Runtime:

User question
        ↓
Cortex Agent
        |
        +--------------------+
        |                    |
        ↓                    ↓
Cortex Analyst         Cortex Search
        |                    |
        ↓                    ↓
Semantic View          Business Knowledge
        |                    |
        +---------+----------+
                  ↓
               Answer


Routing principle:

Structured quantitative question
→ Cortex Analyst

Business/document/policy question
→ Cortex Search

Mixed question
→ Cortex Agent uses both


Example:

"What were total sales in 2025?"
→ Analyst

"What is our policy for customer refunds?"
→ Search

"What were refund amounts in 2025 and what is the refund policy?"
→ Analyst + Search


--------------------------------------------------
## 25. CONTINUOUS CONTEXT IMPROVEMENT
--------------------------------------------------

Build two loops.

RUNTIME LOOP:

User
 ↓
Cortex Agent
 ↓
Analyst / Search
 ↓
Answer


IMPROVEMENT LOOP:

Query History
+
View SQL
+
BI usage
+
Business documents
+
Existing semantic views
+
Verified queries
+
User feedback
        ↓
Context Mining
        ↓
Evidence
        ↓
Candidates / Conflicts
        ↓
Human Review
        ↓
Semantic View / Knowledge Update
        ↓
Evaluation


The system should become better based on actual usage.


--------------------------------------------------
## 26. AGENT / SKILL ARCHITECTURE
--------------------------------------------------

Reuse the engineering pattern from the investment-ai-pipeline project.

Agents should have narrow responsibilities.

Skills should be versioned and reusable.

Recommended skills:

discover-table-profile
discover-table-grain
discover-column-role
discover-business-terms
discover-relationships
discover-metric-candidates
discover-filter-candidates
analyze-view-sql
analyze-query-history
extract-business-knowledge
generate-semantic-description
generate-semantic-candidates
detect-semantic-conflicts
validate-semantic-model
generate-semantic-yaml
deploy-semantic-view
generate-verified-query
run-semantic-evaluation


Do not implement everything as one giant agent prompt.


--------------------------------------------------
## 27. DETERMINISTIC EXECUTION
--------------------------------------------------

Follow this pattern:

AI Agent
   ↓
selects skill
   ↓
versioned Python / SQL
   ↓
Snowflake


The LLM decides WHAT should happen.

Deterministic Python/SQL decides HOW the operation executes.

Do not allow the LLM to perform arbitrary calculations when deterministic SQL can do it.

This pattern is directly reusable from the existing project, where agents orchestrate versioned skills while Python/SQL perform deterministic operations. :contentReference[oaicite:2]{index=2}


--------------------------------------------------
## 28. GOVERNANCE
--------------------------------------------------

Keep tool permissions scoped.

Examples:

Read metadata
Profile data
Read query history
Generate candidates

should be separated from:

CREATE SEMANTIC VIEW
ALTER SEMANTIC VIEW
CREATE CORTEX SEARCH SERVICE


DDL deployment should happen only after validation and approval.

Use least-privilege Snowflake roles.

Do not use ACCOUNTADMIN in production.

The existing project explicitly uses permission-scoped MCP access and separates reviewed DDL from other operations; this pattern should be preserved and improved. :contentReference[oaicite:3]{index=3}


--------------------------------------------------
## 29. AUDITABILITY
--------------------------------------------------

Every discovery run should have a run_id.

Track:

- who started the run
- model used
- evidence collected
- candidates generated
- confidence
- approvals
- rejections
- conflicts
- YAML generated
- validation result
- deployment result
- verified query changes
- evaluation result

Never overwrite historical semantic decisions.

Use append-only audit records where appropriate.

The existing project already uses append-only audit logs and run-level tracking; reuse that design principle. :contentReference[oaicite:4]{index=4}


--------------------------------------------------
## 30. IDEMPOTENCY
--------------------------------------------------

All deployment operations must be safe to repeat.

Examples:

CREATE OR REPLACE SEMANTIC VIEW
or equivalent controlled ALTER strategy.

Do not create duplicate semantic objects.

Every deployment should have:

semantic_version
run_id
git_commit
created_at
deployed_by


--------------------------------------------------
## 31. GIT / VERSION CONTROL
--------------------------------------------------

Semantic definitions must be version controlled.

Recommended repository structure:

semantic-service/
│
├── agents/
│   ├── semantic-discovery-agent/
│   ├── semantic-review-agent/
│   └── semantic-deployment-agent/
│
├── skills/
│   ├── discover-table-profile/
│   ├── discover-table-grain/
│   ├── discover-column-role/
│   ├── discover-relationships/
│   ├── discover-metrics/
│   ├── analyze-view-sql/
│   ├── analyze-query-history/
│   ├── validate-semantic-model/
│   ├── generate-semantic-yaml/
│   └── run-semantic-evaluation/
│
├── semantic/
│   ├── candidates/
│   ├── approved/
│   ├── yaml/
│   └── verified_queries/
│
├── sql/
│   ├── metadata/
│   ├── profiling/
│   ├── query_history/
│   ├── evidence/
│   └── deployment/
│
├── knowledge/
│
├── api/
│
├── ui/
│
└── tests/


--------------------------------------------------
## 32. PHASED IMPLEMENTATION
--------------------------------------------------

Do NOT implement everything at once.

PHASE 1 — Semantic Discovery Foundation

Implement:

- metadata extraction
- data profiling
- table grain discovery
- column role discovery
- view SQL analysis
- evidence table
- semantic candidate table
- candidate confidence
- human review UI

Goal:

Improve current "AI descriptions" into evidence-backed semantic discovery.


PHASE 2 — Semantic Intelligence

Add:

- relationship discovery
- metric discovery
- filter discovery
- query-history mining
- conflict detection
- business terminology
- verified queries


PHASE 3 — Business Knowledge

Add:

- Bitbucket ingestion
- document ingestion
- approved knowledge table
- Cortex Search
- business terminology retrieval


PHASE 4 — Governed Deployment

Add:

- semantic YAML generation
- validation
- Git versioning
- deployment pipeline
- audit trail
- rollback/version management


PHASE 5 — Cortex Agent Runtime

Add:

Cortex Agent
 ├── Cortex Analyst
 └── Cortex Search

Use explicit routing instructions.


PHASE 6 — Continuous Improvement

Add:

- production query mining
- evaluation
- user feedback
- semantic gap detection
- conflict detection
- automatic candidate suggestions


--------------------------------------------------
## 33. WHAT NOT TO DO
--------------------------------------------------

Do NOT:

1. Rebuild the entire Snowflake warehouse into fact/dimension tables.

2. Assume every numeric column is a business metric.

3. Assume column names are business definitions.

4. Let GPT invent metric definitions without evidence.

5. Dump all metadata into the 128k LLM context.

6. Put every enterprise table into one Semantic View.

7. Create a separate Semantic View for every physical table.

8. Put large unstructured documents directly into the Semantic View.

9. Treat Cortex Search as the master knowledge repository.

10. Automatically approve AI-generated semantics.

11. Allow an LLM to directly execute arbitrary production DDL.

12. Build business logic as one giant prompt.

13. Remove deterministic SQL/Python calculations and replace them with LLM reasoning.

14. Ignore table grain.

15. Ignore existing reporting views and query history.

16. Create metrics without understanding their business meaning.

17. Treat a high-confidence AI prediction as equivalent to an approved business definition.


--------------------------------------------------
## 34. REUSE FROM THE EXISTING INVESTMENT AI PIPELINE
--------------------------------------------------

Reuse the following architectural patterns from the existing
investment-ai-pipeline project:

- single-responsibility agents
- explicit agent boundaries
- reusable versioned skills
- deterministic Python/SQL execution
- explicit input/output contracts
- idempotent execution
- append-only audit logging
- data-quality gates
- permission-scoped tools
- governed analytical layers
- Semantic View as an AI consumption layer

Do NOT copy:

- Yahoo Finance ingestion
- ticker-specific logic
- investment-specific FACT/DIM tables
- portfolio-specific calculations

The reusable part is the ENGINEERING/ORCHESTRATION pattern, not the financial domain model.

The original project deliberately keeps analytical data at a defined grain and uses reusable Snowflake analytical objects for multiple downstream consumers. That design principle should be applied to semantic discovery as well. :contentReference[oaicite:5]{index=5}


--------------------------------------------------
## 35. FINAL TARGET
--------------------------------------------------

The final system should become:

                 BUSINESS QUESTIONS
                         ↓
                SEMANTIC SERVICE
                         ↓
        +----------------+----------------+
        |                |                |
    Metadata        Query/SQL        Business Docs
    Profiling       History          Bitbucket
        |                |                |
        +----------------+----------------+
                         ↓
                EVIDENCE / CONTEXT
                         ↓
                 Azure GPT-4o
                         ↓
          SEMANTIC CANDIDATES
          + CONFLICTS
          + CONFIDENCE
                         ↓
                  HUMAN REVIEW
                         ↓
              APPROVED SEMANTICS
                         ↓
                 Semantic YAML
                         ↓
                 VALIDATION
                         ↓
               Git / CI/CD
                         ↓
              Snowflake Semantic View
                         ↓
                  CORTEX AGENT
                    /       \
                   /         \
                  ↓           ↓
             ANALYST        SEARCH
                  |           |
                  ↓           ↓
             Structured   Business/
              Analytics   Documents
                   \         /
                    \       /
                     ↓     ↓
                       ANSWER
                         ↓
                    EVALUATION
                         ↓
                 CONTEXT IMPROVEMENT


--------------------------------------------------
## 36. SUCCESS CRITERIA
--------------------------------------------------

The implementation is successful when:

1. AI-generated semantics are backed by evidence.

2. Every important semantic candidate has confidence and evidence.

3. Humans can approve/edit/reject candidates.

4. Approved semantics generate valid Semantic Views.

5. Existing tables/views can be used without physical remodeling.

6. Metrics are traceable to SQL/business evidence.

7. Relationships have evidence and cardinality.

8. Business terminology can come from approved documentation.

9. Cortex Analyst can answer verified business questions reliably.

10. Cortex Search can answer business/document questions.

11. Cortex Agent can route mixed questions to Analyst + Search.

12. Verified queries become regression/evaluation tests.

13. Every semantic change is auditable and version controlled.

14. The system improves using production query history and feedback.

15. The LLM remains a reasoning/proposal component, not the source of truth.


--------------------------------------------------
## 37. IMPLEMENTATION APPROACH
--------------------------------------------------

Before changing the existing code:

1. Inspect the current repository structure.

2. Identify the current:
   - metadata extraction
   - GPT prompt/service
   - semantic description generation
   - review UI
   - YAML generator
   - Snowflake deployment code
   - authentication
   - API layer
   - database tables

3. Do not rewrite working components unnecessarily.

4. Produce a gap analysis:

CURRENT COMPONENT
→ KEEP / MODIFY / EXTEND / REPLACE

5. Implement Phase 1 first.

6. Add automated tests.

7. Preserve backward compatibility with the existing
table-description → approval → YAML workflow.

8. Provide migration steps for existing semantic definitions.

9. Do not make destructive Snowflake changes.

10. Show the implementation plan before making large structural changes.

11. After implementation, provide:
   - files changed
   - database objects added
   - APIs added
   - UI changes
   - configuration changes
   - tests
   - deployment instructions
   - rollback instructions
   - known limitations
```

### The most important idea for the AI tool

If you want the coding agent to understand the **one big architectural change**, it is this:

> **Do not build a better “AI table description generator.” Build an evidence-driven Semantic Discovery and Governance layer.**

Your current flow is:

**Metadata → GPT → Description → Approval → YAML**

The target flow is:

**Metadata + profiling + existing SQL/views + query history + business documentation → Evidence → GPT reasoning → Semantic candidates + conflicts → Human approval → Semantic View → Verified Queries → Evaluation → Continuous improvement.**

That is the real transformation.

Your uploaded project already gives us a good engineering pattern for this: agents orchestrate, reusable skills contain the logic, deterministic SQL/Python performs the actual work, and audit/data-quality controls surround the pipeline. 

### If you want to give the AI tool even less context

Use this as the **one-paragraph master instruction** at the top of the prompt:

```text
Extend the existing Snowflake Semantic Service from a metadata-based AI description generator into an evidence-driven Semantic Discovery and Governance platform. Do not remodel the physical Snowflake warehouse. Discover semantic meaning from metadata, deterministic data profiling, existing view/transformation SQL, query history, existing semantic definitions, and approved business documentation. Store evidence, semantic candidates, confidence, conflicts, approvals, and audit history. Use Azure GPT-4o only to interpret evidence and propose semantics; never let the LLM invent or directly approve business truth. Require human approval before generating Semantic YAML. Generate and validate governed Snowflake Semantic Views, create verified business questions, evaluate Analyst accuracy, and continuously improve semantics from production usage. Add Cortex Search for approved unstructured business knowledge and Cortex Agent as the runtime orchestrator between Cortex Analyst and Cortex Search. Reuse the existing investment-ai-pipeline engineering patterns: specialized agents, versioned reusable skills, deterministic SQL/Python, explicit contracts, idempotency, auditability, data-quality gates, and permission-scoped tools. Implement incrementally, starting with Semantic Discovery + Evidence + Human Review, and preserve the existing working workflow.
```

This is the version I would actually use with **Claude Code / Cursor / Copilot Agent** because it gives the coding agent the **architecture, boundaries, implementation phases, and acceptance criteria** without forcing it to consume all of our previous discussion.
