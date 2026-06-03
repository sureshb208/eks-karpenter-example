# AI Orchestration Portal - Architecture & Roadmap

## Current System

### Backend

- FastAPI (Python)
- WebSocket for real-time streaming
- Claude CLI subprocess execution

bash claude -p --dangerously-skip-permissions --output-format text --model claude-sonnet-4-6 

- Agents defined in agents.yaml
- Uses asyncio.to_thread() for subprocess execution
- Inter-agent communication via JSON files in output/

---

## Frontend

- Vanilla HTML
- CSS
- JavaScript
- WebSocket client

### Existing UI

- Left Sidebar
  - Project List
  - Agent List

- Top Navigation
  - Dashboard
  - Runs
  - Instructions
  - Remediation
  - Jira Plan

- Main Content
  - Real-time log stream
  - Color coded agent badges
  - Clickable URLs

---

# Existing Pipelines

---

## Pipeline 1 - Audit Pipeline

### Phase 1 (Parallel)

Runs using:

python asyncio.gather(...) 

Agents:

1. Glue Auditor
2. Snowflake Auditor
3. MWAA Auditor
4. EKS Auditor
5. Cloud Data Transfer Auditor

Outputs:

text output/   glue.md   snowflake.md   mwaa.md   eks.md   transfer.md 

### Phase 2

Summary Agent

Consumes all audit reports and generates:

text executive_summary.md 

---

## Pipeline 2 - FARM Remediation Pipeline

### Phase 1

Fetch FARM finding using MCP.

Tasks:

- Retrieve finding
- Locate Terraform file
- Find git repo root

bash git rev-parse --show-toplevel 

Output:

json analysis.json 

### Phase 2

Create Jira Story

Project:

text WHCOREANALYTICS 

Output:

text jira.txt 

### Phase 3

Create Git Branch

bash git checkout -b feature/... 

### Phase 4

Apply Terraform Fix

Modify:

text *.tf 

files.

### Phase 5

Commit

bash git commit -m "JIRA-123 fix terraform version" 

Push

bash git push 

Output:

text Pull Request URL 

---

## Pipeline 3 - Jira Plan Pipeline

### Phase 1

Read Jira Ticket

Using MCP.

Output:

json analysis.json 

### Phase 2

Generate Implementation Plan

Creates:

markdown implementation_plan.md 

Contains:

- Approach
- File Changes
- Testing Strategy
- Rollback Plan
- Estimated Effort

### Phase 3

Create Feature Branch

### Phase 4

Apply Code Changes

### Phase 5

Commit + Push

Output:

text PR URL 

---

# Current Limitations

## 1. No Subprocess Control

Problem:

No ability to stop running Claude process.

Current:

python asyncio.to_thread(...) 

Solution:

Create:

python ProcessManager 

Features:

- Start Process
- Track PID
- Kill Process
- Status

Store:

python {   run_id: {     agent_id: pid   } } 

API:

http POST /runs/{run_id}/cancel 

---

## 2. No Retry Capability

Problem:

If Phase 4 fails:

Entire pipeline restarts.

Solution:

http POST /runs/{run_id}/retry/{agent_id} 

Store phase state.

Example:

json {   "completed": [     "phase1",     "phase2",     "phase3"   ] } 

Resume only failed phase.

---

## 3. Run History Lost

Problem:

Stored in memory only.

Current:

python runs = {} 

Solution:

text output/runs/ 

Store:

json run.json 

API:

http GET /history 

---

## 4. No Validation

Problem:

Invalid FARM ID.

Invalid Jira ID.

Pipeline fails later.

Solution:

http GET /validate/farm/{id}  GET /validate/jira/{id} 

Validate before execution.

---

## 5. Brittle File Passing

Problem:

Missing JSON breaks downstream agents.

Solution:

Use Pydantic.

Example:

python class FarmAnalysis(BaseModel):     farm_id: str     repo: str     file_path: str 

Validate on write and read.

---

## 6. WebSocket Dependency

Problem:

Browser refresh loses logs.

Solution:

Persist logs.

Structure:

text output/   runs/     RUN001/       logs.txt 

API:

http GET /runs/{run_id}/logs 

Replay logs.

---

## 7. Unstructured Outputs

Problem:

Markdown parsed by agents.

Solution:

Generate both:

json structured.json 

and

markdown report.md 

Machine uses JSON.

Humans use Markdown.

---

## 8. Single Model

Current:

All agents use:

text claude-sonnet-4-6 

Solution:

Add model field.

Example:

yaml agents:    jira_reader:     model: claude-haiku    planner:     model: claude-opus    remediation:     model: claude-sonnet 

---

## 9. No Cost Tracking

Capture:

- Start Time
- End Time
- Duration

Display:

text Agent Duration Pipeline Duration 

Future:

- Token Usage
- Cost Estimation

---

## 10. Manual YAML Editing

Current:

yaml agents.yaml 

edited manually.

Future:

UI editor.

API:

http PATCH /agents/{id}/prompt 

---

# Recommended Architecture

## Current

text UI  ↓ FastAPI  ↓ Claude Process 

---

## Target

text UI  ↓ FastAPI  ↓ Run Manager  ↓ Pipeline Manager  ↓ Agent Manager  ↓ Process Manager  ↓ Claude CLI 

---

# Backend Components

text backend/    app.py    managers/      run_manager.py      process_manager.py      pipeline_manager.py      queue_manager.py      history_manager.py    models/      run.py      agent.py      pipeline.py    storage/      history.json      queue.json    pipelines/      audit.py      remediation.py      jira_plan.py 

---

# Stage 1 (Build First)

Goal:

Production Ready System

### Build

1. Run Manager
2. Process Manager
3. Artifact Store
4. Retry Failed Phase
5. Queue Manager

---

## Run Manager

Responsibilities:

python create_run() update_run() cancel_run() retry_run() get_run() list_runs() 

---

## Process Manager

Responsibilities:

python start() kill() status() 

Tracks:

python run_id agent_id pid 

---

## Artifact Store

Structure:

text output/    runs/      RUN001/        logs/        artifacts/        metadata.json      RUN002/ 

---

## Retry Failed Phase

Endpoint:

http POST /runs/{run_id}/retry 

Allows restarting failed phase only.

---

## Queue Manager

Queue multiple FARM IDs.

Example:

text FARM-100 FARM-101 FARM-102 

Process sequentially.

---

# Stage 2

Goal:

Manage Agents Through UI

---

## Agent Registry

UI:

text Agents  + Create Agent  Name Prompt Model Pipeline MCP Access 

Save to:

yaml agents.yaml 

---

## Skills Registry

Structure:

text skills/    terraform_audit.md    jira_planner.md    security_review.md 

Agent references skills.

Example:

yaml skills:   - terraform_audit   - security_review 

---

## MCP Registry

UI:

text MCP Servers  GitHub Jira Filesystem Terraform 

Display:

- Status
- Permissions
- Assigned Agents

---

## Run History UI

Display:

text RUN001  SUCCESS  RUN002  FAILED 

Click:

- Logs
- Artifacts
- Output
- Metrics

---

# Stage 3

Goal:

Intelligent Orchestration

---

## Supervisor Agent

Instead of user selecting pipeline.

User:

text Fix FARM-123 

Supervisor decides:

text FARM Agent Jira Agent Terraform Agent 

Runs required agents automatically.

---

# Future UI Layout

text ------------------------------------------------ Dashboard ------------------------------------------------  Pipelines   Audit  FARM Remediation  Jira Planning  ------------------------------------------------ Agents ------------------------------------------------   Glue Auditor  Snowflake Auditor  MWAA Auditor  EKS Auditor  Summary Agent  ------------------------------------------------ Runs ------------------------------------------------   RUN001  RUN002  RUN003  ------------------------------------------------ Queue ------------------------------------------------   Queued  Running  Completed  ------------------------------------------------ Artifacts ------------------------------------------------   Markdown  JSON  PR URLs  ------------------------------------------------ Settings ------------------------------------------------   Agents  Skills  MCP  Models 

---

# Agent YAML Future Structure

Current:

yaml agents:   - name: mwaa_auditor 

Future:

yaml agents:    - id: mwaa_auditor      model:       claude-sonnet-4-6      skills:       - mwaa_audit       - terraform_review      mcps:       - github       - filesystem      timeout:       1800      retries:       2 

---

# Build Order For Claude Code

Sprint 1

- Run Manager
- Process Manager
- Artifact Store
- Retry Failed Phase
- Queue Manager

Sprint 2

- Agent Registry UI
- Skills Registry UI
- MCP Registry UI
- Run History UI

Sprint 3

- Supervisor Agent
- Dynamic Agent Selection
- Approval Workflows
- Policy Engine

---

# Final Recommendation

Do NOT build:

- LangGraph
- Vector Database
- RBAC
- Complex Workflow Builder
- Multi-Tenant Architecture

yet.

First make the existing platform reliable.

Priority:

1. Run Manager
2. Process Manager
3. Artifact Store
4. Retry
5. Queue
6. Agent Registry
7. Skills Registry
8. MCP Registry
9. Run History
10. Supervisor Agent

Once those are complete, the platform will be stable, maintainable, and ready for future enhancements.