AI Engineering Copilot Platform - Master Architecture (Single Page)

Vision

Build an internal AI Engineering Copilot powered entirely by Claude Code CLI, FastAPI, MCP servers, and specialized agents.

The platform should support:

* Natural language chat
* Multi-agent orchestration
* Repository analysis
* Jira planning
* Security remediation
* PR review
* Incident investigation
* Migration planning
* Documentation generation
* Knowledge retrieval

Everything should be accessible from a single web UI.

⸻

High Level Architecture

User
 │
 ▼
Web UI
 │
 ▼
FastAPI Backend
 │
 ▼
Router Agent
 │
 ├── Chat Requests
 ├── Agent Execution
 ├── Pipeline Execution
 └── MCP Tool Access
 │
 ▼
Claude Code CLI
 │
 ▼
MCP Layer
 │
 ├── Jira MCP
 ├── Bitbucket MCP
 ├── Sourcegraph MCP
 ├── FARM MCP
 ├── FarmGenie MCP
 ├── Confluence MCP
 ├── Splunk MCP
 ├── Dynatrace MCP
 ├── AURA MCP
 ├── Idaho/IAN MCP
 └── V12/CRDB MCP
 │
 ▼
Run Store + Knowledge Store
(Postgres)

⸻

UI Design

Single Page Application

┌──────────────────────────────────────┐
│ AI Engineering Copilot               │
├──────────────────────────────────────┤
│                                      │
│ Chat                                │
│                                      │
│ Agents                              │
│                                      │
│ Pipelines                           │
│                                      │
│ Active Runs                         │
│                                      │
│ Reports / Artifacts                 │
│                                      │
│ Cost Analytics                      │
│                                      │
│ MCP Explorer                        │
│                                      │
└──────────────────────────────────────┘

⸻

Chat Copilot

New endpoint:

/ws/chat

Examples:

Which repo owns this DAG?
Show all Glue jobs writing to Snowflake.
Find all Iceberg tables.
Review PR 123.
Show critical FARM findings.
Create Jira story for Airflow upgrade.
What caused incident INC-12345?

The user should not need to know which agent or MCP is used.

⸻

Router Agent

Purpose:

Determine which specialist agent should handle the request.

Examples:

User:
Show all critical FARM findings
Router:
Security Agent
User:
Create Jira ticket
Router:
Jira Agent
User:
Why did EKS fail yesterday?
Router:
SRE Agent

Router should be lightweight and fast.

⸻

Specialist Agents

Repository Agent

Tools:

* Sourcegraph
* Bitbucket
* Confluence

Responsibilities:

* Code search
* Ownership discovery
* Dependency analysis
* Architecture discovery
* Pattern search

Questions:

Which repo contains this DAG?
Show all MWAA DAGs.
Find Glue jobs using Iceberg.

⸻

Jira Agent

Tools:

* Jira
* Confluence

Responsibilities:

* Create stories
* Sprint analysis
* Release planning
* Ticket updates

Questions:

Create migration story.
Show sprint progress.
Move ticket to In Progress.

⸻

Security Agent

Tools:

* FARM
* FarmGenie
* Sourcegraph

Responsibilities:

* Vulnerability review
* Remediation planning
* Compliance analysis
* Security reporting

Questions:

Show critical vulnerabilities.
Generate fix plan.
Create remediation PR.

⸻

SRE Agent

Tools:

* Dynatrace
* Splunk
* AURA

Responsibilities:

* Incident investigation
* Log analysis
* Performance review
* Availability analysis

Questions:

Why did service fail?
Show latency spikes.
Investigate outage.

⸻

Data Platform Agent

Tools:

* Sourcegraph
* Confluence
* Jira

Responsibilities:

* MWAA
* Airflow
* Glue
* Spark
* Snowflake
* Iceberg

Questions:

Review DAG.
Analyze Iceberg migration.
Find expensive Snowflake queries.

⸻

Migration Agent

Responsibilities:

* Airflow upgrades
* Python upgrades
* Terraform upgrades
* Spark upgrades
* Iceberg migrations

Flow:

Discover
Analyze
Plan
Generate Code
Validate
Create PR

⸻

Documentation Agent

Tools:

* Confluence

Responsibilities:

* Architecture documents
* Runbooks
* RCA reports
* Migration documents

⸻

Knowledge Agent

Purpose:

Reuse previous successful work.

Search:

* Previous audits
* Previous PR reviews
* Previous remediations
* Previous incidents
* Previous Jira stories

This reduces repeated work and improves consistency.

⸻

Worker Agents

Specialists should not directly edit code.

Use workers.

Planner Worker
Code Worker
Test Worker
Validation Worker
Documentation Worker

Example:

Migration Agent
 │
 ├── Planner
 ├── Code Generator
 ├── Test Generator
 ├── Validator
 └── Documentation Writer

⸻

Validation Layer

Every major phase should be validated.

Current:

Planner
 ↓
Coder
 ↓
PR

Recommended:

Planner
 ↓
Plan Validator
 ↓
Coder
 ↓
Code Validator
 ↓
Security Validator
 ↓
PR

Benefits:

* Fewer hallucinations
* Better quality
* Safer changes

⸻

Existing Pipelines

Repository Audit

Current:

5 Auditors
 │
 ├── Glue
 ├── Snowflake
 ├── MWAA
 ├── EKS
 └── Cloud Transfer
 │
 ▼
Summary Agent

Enhancements:

* Dynamic repo discovery
* Security review
* Architecture review
* Cost review

⸻

Jira Plan

Jira Reader
 ↓
Planner
 ↓
Branch Creator
 ↓
Code Generator
 ↓
PR Creator

Add:

Plan Validator
Security Validator
Test Generator

⸻

FARM Remediation

Farm Analyzer
 ↓
Jira Creator
 ↓
Branch Creator
 ↓
Code Fixer
 ↓
PR Creator

Add:

Fix Validator
Security Validator

⸻

PR Review

Current:

PR Reader
 ↓
Reviewer
 ↓
Jira Linker

Replace with:

PR Reader
 ↓
Code Review Agent
 ↓
Security Review Agent
 ↓
Architecture Review Agent
 ↓
Performance Review Agent
 ↓
Summary Agent

⸻

New Pipelines

Incident RCA Pipeline

Incident
 ↓
Splunk Agent
 ↓
Dynatrace Agent
 ↓
AURA Agent
 ↓
Root Cause Agent
 ↓
Confluence Report

⸻

Airflow Upgrade Pipeline

Discover DAGs
 ↓
Compatibility Check
 ↓
Migration Plan
 ↓
Code Generation
 ↓
Tests
 ↓
Validation
 ↓
PR

⸻

Terraform Audit Pipeline

Terraform Discovery
 ↓
Security Review
 ↓
Cost Review
 ↓
Best Practice Review
 ↓
Remediation Plan

⸻

Iceberg Migration Pipeline

External Table Discovery
 ↓
Schema Analysis
 ↓
Migration Plan
 ↓
Validation
 ↓
PR

⸻

Deployment Readiness Pipeline

PR
 ↓
Monitoring Check
 ↓
Alerting Check
 ↓
Runbook Check
 ↓
Rollback Check
 ↓
Readiness Report

⸻

MCP Usage Strategy

Sourcegraph MCP

Use for:

* Code search
* Dependency discovery
* Architecture discovery
* Pattern analysis

⸻

Bitbucket MCP

Use for:

* Branch creation
* PR creation
* File updates
* Commit history

⸻

Jira MCP

Use for:

* Story creation
* Sprint reporting
* Workflow transitions

⸻

Confluence MCP

Use for:

* Architecture docs
* RCA reports
* Runbooks

⸻

FARM MCP

Use for:

* Security findings
* Vulnerability discovery

⸻

FarmGenie MCP

Use for:

* Fix guidance
* Security knowledge base
* Analytics reporting

⸻

Splunk MCP

Use for:

* Log analysis
* Error investigation

⸻

Dynatrace MCP

Use for:

* Golden signals
* Performance issues
* Service health

⸻

AURA MCP

Use for:

* Incidents
* SLI breaches
* Change correlation
* Root cause support

⸻

Critical Architecture Improvements

Tool Isolation

Current:

All agents have all tools.

Required:

agent:
  allowed_tools:
    - sourcegraph
    - jira

Enforce in runtime.

⸻

Persistent State

Replace in-memory tracking.

Use:

Postgres

Tables:

runs
run_steps
agent_outputs
artifacts
costs

Benefits:

* Resume runs
* Audit history
* Cost reporting

⸻

Retry Engine

Support:

retry:
  attempts: 3
  backoff: exponential

Avoid pipeline failures caused by temporary MCP issues.

⸻

Human Approval Gates

Examples:

Plan Generated
 ↓
Human Approval
 ↓
Code Generation
Code Complete
 ↓
Human Approval
 ↓
Create PR

⸻

Dynamic Repository Discovery

Replace:

Hardcoded repositories

With:

Sourcegraph Discovery

Automatically classify:

Terraform
Airflow
Spark
Snowflake
Iceberg
Glue

⸻

Knowledge Store

Use Postgres.

Store:

* Audit results
* RCA reports
* PR reviews
* Security remediations
* Jira plans

Flow:

Question
 ↓
Search Knowledge
 ↓
Search Code
 ↓
Claude
 ↓
Answer

⸻

Cost Analytics

Track:

Input Tokens
Output Tokens
Execution Time
Tool Calls
Pipeline Cost

Dashboard:

Most Expensive Agents
Most Expensive Pipelines
Average Runtime
Success Rate

⸻

Recommended Execution Model

User
↓
Router Agent
↓
Specialist Agent
↓
Worker Agents
↓
Validators
↓
Human Approval
↓
PR / Ticket / Report

This architecture will scale from simple chat queries to full repository audits, incident investigations, migrations, remediations, and engineering automation while remaining entirely powered by Claude Code CLI and your existing MCP ecosystem.

This document can serve as the master blueprint for implementing the platform and feeding into Claude Code for iterative development.