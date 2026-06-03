I have a FastAPI + WebSocket multi-agent orchestration portal (main.py + index.html + agents.yaml).
Here are 4 specific improvements to implement end-to-end. Do them in this exact order:

── STEP 1: Input validation ──
Add GET /validate/farm/{farm_id} and GET /validate/jira/{ticket_id} endpoints in main.py.
Each calls the relevant MCP tool in read-only mode to check the ID exists.
Returns {"valid": bool, "reason": str, "summary": str}.
In index.html, before opening a WebSocket for remediation or jira-plan pipelines,
call the relevant endpoint. Show an inline error and block the run if valid is false.

── STEP 2: Pydantic inter-agent schemas ──
Create schemas.py with Pydantic models for every JSON file passed between agents:
- FarmAnalysis (phase 1 → 2): farm_id, title, severity, terraform_file, git_root,
  affected_resource, current_version, target_version
- JiraCreated (phase 2 → 3+): jira_key, jira_url, farm_id, terraform_file
- JiraAnalysis (jira phase 1 → 2): ticket_id, title, description, comments list, repo_path
- CodePlan (jira phase 2 → 3): approach, files_to_change list, test_strategy, effort_days
- CodeChangeApplied (phase 4 → 5): files_modified list, branch_name, jira_key, commit_message
Add write_agent_output(run_id, phase, model) and read_agent_output(run_id, phase, model_cls)
helpers that mkdir output/runs/{run_id}/ and validate on both write and read.
Replace all raw json.dumps/json.loads inter-agent file I/O in main.py with these helpers.

── STEP 3: Cancel pipeline ──
In main.py: add active_procs: dict[str, list] = defaultdict(list) at module level.
Pass start_new_session=True to every asyncio.create_subprocess_exec call.
Register each Process in active_procs[run_id] on start; remove it when done.
Add POST /runs/{run_id}/cancel: SIGTERM all procs for that run_id, wait 400ms,
SIGKILL any still alive, broadcast {"type":"cancelled"} over WebSocket, return {"killed": N}.
In index.html: add a Cancel button to each active pipeline card. On click, POST to the endpoint.
On receiving {"type":"cancelled"} over WS, grey out all pending phase cards.

── STEP 4: Persist logs + reconnect ──
In main.py: for every log line streamed from a subprocess, also append a JSON entry to
output/runs/{run_id}/logs.jsonl in the format:
{"ts": ISO8601, "phase": int, "agent": str, "text": str}
Modify GET /ws/{run_id}: on new WebSocket connection, first replay all lines from logs.jsonl
(send each as the raw JSON string), then switch to live streaming.
Add GET /runs/{run_id}/logs that returns the JSONL file as a text/plain response.
In index.html: on ws.onclose, if the run is still active (check a local runStatus map),
auto-reconnect after 2 seconds using the same connectWS(runId) function.

Do not change any existing pipeline logic, agent prompts, or YAML structure.
Add the new code as extensions. Use existing patterns in the file for style consistency.
After each step write a one-line comment in the code: # Fix #N implemented