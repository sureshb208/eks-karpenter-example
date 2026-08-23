Yes — with your actual architecture, I would not introduce a new Fact/Dimension physical layer just for Semantic Views. Your existing refined tables and business views can become the foundation of the semantic layer.

From what you described, your flow is essentially:

Ingestion Tables
      ↓
Transformations
      ↓
Refined Tables
      ↓
Business / Repository Views
      ↓
Consumers

Your goal should be:

Ingestion Tables
      ↓
Transformations
      ↓
Refined Tables
      ↓
Business / Repository Views
      ↓
Semantic Modeling
      ↓
Snowflake Semantic Views
      ↓
Cortex Analyst / Natural Language
1. Don't build Semantic Views directly on ingestion tables

I would keep the ingestion layer completely out of the semantic-modeling process.

For example:

ING_CUSTOMER
ING_ORDER
ING_PRODUCT

These are technical/source-oriented tables.

Instead, start from your refined layer or business views, because those already contain your organization's transformation logic.

2. Your existing views are actually a good starting point

Suppose you currently have:

REFINED_ORDERS
REFINED_CUSTOMERS
REFINED_PRODUCTS


VW_SALES
VW_CUSTOMER
VW_PRODUCT

Your Semantic View can be created on top of the appropriate refined/business objects.

Think of it as:

Physical Data Layer
        ↓
Refined Tables
        ↓
Business Logic Layer
        ↓
Semantic Layer
        ↓
AI / Analytics

The semantic layer should describe the business meaning of your existing data, not replace your transformation layer.

3. Your biggest challenge is metadata

This is where I would focus your implementation.

You already have:

table names
column names
data types
transformation logic
existing views
SQL definitions

But you may not have:

business descriptions
dimension/measure classification
metric definitions
relationships
synonyms
business terminology
grain
calculation definitions

So your API can automatically collect these.

For each selected table/view:

Table
 ├── Description
 ├── Grain
 ├── Business purpose
 │
 └── Columns
      ├── Name
      ├── Type
      ├── Description
      ├── Dimension?
      ├── Measure?
      ├── Identifier?
      ├── Date?
      └── Synonyms

Then let the user review the AI-generated information.

4. Don't ask users to create Fact/Dimension from scratch

This is important for your use case.

Instead, let your system suggest the semantic role.

For example:

VW_SALES


ORDER_ID          → Identifier
CUSTOMER_ID       → Dimension / Relationship
PRODUCT_ID        → Dimension / Relationship
ORDER_DATE        → Time Dimension
REGION            → Dimension
QUANTITY          → Measure
NET_AMOUNT        → Measure
DISCOUNT_AMOUNT   → Measure

The user can modify it:

AI Suggestion → User Review → Approved Metadata

That is much safer than automatically assuming that CUSTOMER_ID or AMOUNT means something specific.

5. Use your transformation SQL as an important AI input

This is probably the most valuable improvement I would make to your current process.

If you have:

CREATE VIEW VW_SALES AS
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    p.product_name,
    o.amount - o.discount AS net_sales
FROM refined_orders o
JOIN refined_products p
  ON o.product_id = p.product_id;

Don't send only the column names to the AI.

Give the metadata engine:

Table/View definition
+
Column names/types
+
Column comments
+
Transformation SQL
+
Sample values/statistics

Then the AI has much more evidence to determine:

net_sales
    ↓
Business meaning:
Net sales after discount


Type:
Measure


Suggested aggregation:
SUM


Possible synonym:
Revenue / Net Sales

This is much better than:

NET_SALES = Numeric column

6. Introduce "Business Grain"

For every semantic table/view, I would make grain mandatory.

For example:

VW_SALES


Grain:
One row represents one order line.

Or:

VW_CUSTOMER_MONTHLY


Grain:
One row represents one customer for one calendar month.

This becomes extremely important for AI-generated SQL.

Otherwise, an agent may incorrectly aggregate a monthly snapshot or duplicate data through joins.

7. Build relationships from your existing model

You don't necessarily need formal PK/FK constraints today.

Your system can identify candidates from:

Existing SQL joins
+
Column names
+
Data types
+
Value overlap
+
Existing constraints

Example:

VW_SALES.CUSTOMER_ID
        ↓
REFINED_CUSTOMER.CUSTOMER_ID

AI suggests:

Possible relationship: CUSTOMER_ID

Then the user approves it.

That relationship becomes part of your semantic metadata.

8. Your current UI workflow is actually very good

I would evolve it into:

1. Select Tables / Views
          ↓
2. Profile Data
          ↓
3. Read Existing SQL
          ↓
4. AI Generates Metadata
          ↓
5. AI Suggests:
   • descriptions
   • dimensions
   • measures
   • relationships
   • grain
   • synonyms
          ↓
6. User Reviews / Edits
          ↓
7. Validate Semantic Model
          ↓
8. Generate Semantic View
          ↓
9. Test Natural Language Questions
          ↓
10. Deploy

The user approval step is important because your metadata isn't currently reliable.

9. I would also add a "Question Test" before deployment

This could make your application much more useful.

After generating the semantic view, automatically test questions such as:

What were total sales last month?


What are the top 10 products by revenue?


Which region generated the highest revenue?


How many customers placed orders last quarter?


What was the average order value?

Then show:

Question
   ↓
Generated SQL
   ↓
Execution
   ↓
Result
   ↓
Expected / Reviewed?

This gives you a semantic model validation loop.

The architecture I would recommend for your environment
                    SNOWFLAKE
┌─────────────────────────────────────────────┐
│                                             │
│  INGESTION                                  │
│  ──────────                                 │
│  Raw/source tables                          │
│             │                               │
│             ▼                               │
│  TRANSFORMATION                             │
│  ──────────────                             │
│  Spark / SQL / existing pipelines           │
│             │                               │
│             ▼                               │
│  REFINED                                    │
│  ───────                                    │
│  Refined tables                             │
│             │                               │
│             ▼                               │
│  BUSINESS / REPOSITORY VIEWS                │
│  ──────────────────────────                 │
│             │                               │
└─────────────┼───────────────────────────────┘
              │
              ▼
       ┌───────────────────┐
       │ Metadata Profiler │
       │                   │
       │ Schema            │
       │ SQL definition    │
       │ Statistics        │
       │ Samples           │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ AI Metadata       │
       │ Generator         │
       │                   │
       │ Descriptions      │
       │ Dimensions        │
       │ Measures          │
       │ Relationships     │
       │ Grain             │
       │ Synonyms          │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Human Review      │
       │                   │
       │ Accept / Edit     │
       │ Reject / Add      │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Semantic Model    │
       │                   │
       │ Business entities │
       │ Metrics           │
       │ Dimensions        │
       │ Relationships     │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Generate          │
       │ Semantic View     │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Cortex Analyst /  │
       │ Natural Language  │
       └───────────────────┘
The key principle

Don't redesign your existing warehouse to make AI work.

Instead:

Use your refined tables/business views as the data foundation and build a semantic metadata layer on top of them.

That gives you a much more realistic migration path.

And because you're generating the Semantic Views through APIs rather than manually through the UI, I'd make the metadata definition your version-controlled source of truth:

Metadata
   ↓
Validation
   ↓
Semantic View SQL
   ↓
Deploy to Snowflake
   ↓
Test questions
   ↓
Promote

That will make your solution much easier to maintain as the number of tables and semantic views grows.