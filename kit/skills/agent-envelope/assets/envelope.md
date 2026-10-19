# Lane envelope — copy this file, fill every field, keep the rules block verbatim

(Hints in angle brackets are for the parent; delete them as you fill. Everything the lane must know is in this
envelope — the conversation does not travel with it.)

(Parent, before filling: is this a review? Then this file is not the vehicle — Claude → `/code-review`, Codex and
Claude runner → `--review` with the git tree as cwd, agy and Copilot → this file. A cross-model review is each
harness's own review feature on the same tree, never one packet folder for every carrier.)

## Task
- Source: <issue URL or path — the lane opens it itself; never paste its body here>
- Goal in one line: <what the lane must deliver>
- Weight: <deep | errand>
- Carrier · model: <e.g. Claude subagent · sonnet | agy | Codex --write — a review goes to /code-review or --review, see the line above>

## Ownership (writing lanes only — finding and measuring lanes get the goal and the criteria, not a fence)
- Files or areas you may edit: <paths>
- Resources you hold while running: <automation server · port · golden · shared check — or "none">
- Reference docs derived from those files, to update in the same pass: <paths — or "none">
- Do NOT look at: <paths another lane owns>

## Names (unique per lane — identical names overwrite each other)
- Label or anchor: <lane-name>
- Output or report file: <path>

## Materials · tools
- Open these: <paths or URLs the lane can reach. Anything it cannot reach is copied into the work directory: <path>>
- Tools you have: <shell · edit · probes — whatever the work needs to test its own claims>
- Work directory: <path> — it is the fence; nothing outside it changes

## Output contract
- Each finding: `file:line` plus a concrete failure scenario. Both, or it is an impression, not a finding.
- Name what you did not measure and what you did not look at. Zero findings is a valid report — say so, and say how far you looked.
- Screens: the image path and what is visible, in plain words.
- Probes take the tree as an argument; never hardcode a path.
- Checks you ran: counts, the mutation result (a deliberately wrong specimen went red) and the tree fingerprint (commit or hash).
- Report in English as your final message. Files a human will open directly: Korean.

## This run only
<instructions that apply to this envelope alone — never rules for every lane; those go into the block below>

## Lane rules (absolute — paste verbatim)
① Edit only what you own — reading anywhere is fine; another lane may be editing next to you. Report defects outside your ownership; do not fix them.
② A "could not measure" mark counts as red — never say "done" while one stands.
③ Never change state through git. The parent commits — leave changes uncommitted in the worktree.
④ Never derive expected values from what you measured, and never bless goldens or snapshots — a human approves those. Write why the value must be what it is; if the measurement differs, report it.
⑤ Before reporting "absent", run a positive control — first ask whether the specimen really has that shape.
⑥ Never run commands that print the environment or the process list (env, printenv, set, ps aux, pgrep -af) — they write secrets into the transcript.
⑦ A check and its specimen are one pair — when tightening a check turns a specimen red, fix both in the same pass.
⑧ Lanes share one machine. Run your long checks one at a time, in the background, and wait for the finish notification instead of polling or starting a second copy — overlapping copies slow every run.
