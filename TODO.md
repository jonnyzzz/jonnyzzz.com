# TODO

## Debugger skill research: sub-agent launch notes
- Claude Code CLI
  - Verify: `which claude`, `claude --version`
  - Run (stdin prompt, full tools): `echo "<prompt>" | claude -p --tools default --permission-mode dontAsk 2>&1`
  - Structured output: add `--output-format json`
  - Parallel pattern: `... > /tmp/out1.txt 2>&1 &` then `wait`
- Codex CLI
  - Verify: `which codex`, `codex --help`, `codex exec --help`
  - Recommended non-interactive: `codex -a never -s workspace-write -C /path/to/repo --add-dir /path/to/other/repo exec -m gpt-5.2-codex`
  - If you want low-friction approvals: use `--full-auto` (alias for `-a on-request --sandbox workspace-write`)
  - Save output: `-o /tmp/last.txt` or use shell redirection
- RLM guidance
  - Run independent sub-agents in parallel and aggregate outputs
  - Keep prompts focused; include exact paths and expected output format

## Codex instance parameters (recommended)
- Minimal non-interactive run:
  - `codex -a never -s workspace-write -C /Users/jonnyzzz/Work/intellij-mcp-steroids --add-dir /Users/jonnyzzz/Work/intellij exec -m gpt-5.2-codex`
- Include prompt via stdin:
  - `cat <<'PROMPT' | codex -a never -s workspace-write -C /Users/jonnyzzz/Work/intellij-mcp-steroids --add-dir /Users/jonnyzzz/Work/intellij exec -m gpt-5.2-codex
<your prompt>
PROMPT`
- Capture last message to file:
  - add `-o /tmp/codex-last.txt`
- Stream JSON events (machine-readable logs):
  - add `--json`
- Output schema (force shape of final response):
  - add `--output-schema /path/to/schema.json`
- If you prefer automatic approvals:
  - add `--full-auto` (alias for `-a on-request --sandbox workspace-write`)

## Sub-agent prompt hygiene (debugger workflows)
- Remind agents exec_code is stateful: prefer multiple short calls over one long call with sleeps.
- Timebox each call; poll session state across calls instead of waiting.
