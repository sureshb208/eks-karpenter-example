

Feature 1 — Cancel a running pipeline
Kill subprocesses server-side; update UI state immediately
Files to change
modify
main.py
Track run_id→process dict; add /cancel/{run_id} endpoint; SIGTERM/SIGKILL subprocess group
modify
index.html
Cancel button per pipeline card; disable on terminal states; WS listener for cancelled event
modify
agents.yaml
No change needed — subprocess group relies on existing structure
Backend — main.py
new
Process registry
import os, signal
# At module level — keyed by run_id
active_runs: dict[str, list[asyncio.subprocess.Process]] = {}

async def run_agent(run_id: str, agent_name: str, cmd: list[str]):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        # Put each agent in its own process group
        start_new_session=True,
    )
    active_runs.setdefault(run_id, []).append(proc)
    # ... existing stream loop ...
    active_runs[run_id].remove(proc)
copy
new
Cancel endpoint
@app.post("/cancel/{run_id}")
async def cancel_run(run_id: str):
    procs = active_runs.pop(run_id, [])
    if not procs:
        raise HTTPException(404, "Run not found or already finished")
    for proc in procs:
        try:
            # Kill the entire process group (catches child shells too)
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass  # already gone
    await asyncio.sleep(0.5)
    for proc in procs:
        if proc.returncode is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
    # Notify all WebSocket clients for this run
    await broadcast(run_id, {"type": "cancelled", "run_id": run_id})
    return {"status": "cancelled", "killed": len(procs)}
copy
WebSocket message types
server→client
Cancel confirmed, pipeline stopped
{"type":"cancelled","run_id":"abc"}
client→server
User clicks Cancel (fallback via fetch POST)
POST /cancel/{run_id}
Frontend — index.html
// Add cancel button to each pipeline card in renderPipelineCard()
function renderPipelineCard(runId, status) {
  const btn = document.createElement('button');
  btn.textContent = 'Cancel';
  btn.disabled = ['done','failed','cancelled'].includes(status);
  btn.onclick = async () => {
    btn.disabled = true;
    btn.textContent = 'Cancelling…';
    await fetch(`/cancel/${runId}`, { method: 'POST' });
  };
  return btn;
}

// In your existing WS message handler:
if (msg.type === 'cancelled') {
  setRunStatus(msg.run_id, 'cancelled');   // grey out the card
  markAllPhasesBlocked(msg.run_id);        // show remaining phases as blocked
  showToast('Pipeline cancelled');
}
copy
Implementation steps
1
Add active_runs dict at module level in main.py
Dict maps run_id → list[Process]. Populated by each run_agent() coroutine.
2
Pass start_new_session=True to every create_subprocess_exec call
This creates a new process group so os.killpg kills agent + any child shells it spawned.
3
Add POST /cancel/{run_id} route — SIGTERM then SIGKILL after 500ms
Always try SIGTERM first (clean shutdown). SIGKILL is the fallback for stuck processes.
4
Broadcast {"type":"cancelled"} over WebSocket after killingAll connected browser tabs for that run receive the message simultaneously.
5
In the frontend, render a Cancel button on each active pipeline card
Disable the button once the run reaches a terminal state (done/failed/cancelled).
Recommended build order for Claude Code CLI:
Start with Feature 3 (history) first because it introduces the run_state.json and run_history.json file helpers that Features 1 and 2 depend on. Then Feature 1 (cancel) because it requires start_new_session=True on every subprocess call — you want that in place before adding retry logic. Then Feature 2 (retry) which builds on the phase state you just set up. Then Feature 4 (queue) which is self-contained. Feature 5 (markdown preview) last — it's purely additive and has no backend coupling to the others.
One thing to watch: your existing run_remediation_pipeline() function likely runs phases in a straight for loop. Before adding retry, refactor it into a run_single_phase(run_id, farm_id, phase_num, ctx) function that you can call both from the main pipeline loop and from the retry endpoint. That's the single biggest structural change — everything else is additive.
Security note for the report endpoint: the Path(agent_name).name call in Feature 5 strips any ../ path traversal. Keep that in place — never pass the raw query parameter directly to REPORTS_DIR / agent_name.