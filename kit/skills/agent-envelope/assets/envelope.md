# Lane envelope — copy this file, fill every field, keep the rules block verbatim

(Hints in angle brackets are for the parent; delete them as you fill. Everything the lane must know is in this
envelope — the conversation does not travel with it.)

(Parent, before filling: is this a review? Then this file is not the vehicle — Claude → `/code-review`, Codex and
Claude runner → `--review` with the git tree as cwd, agy and Copilot → this file. A cross-model review is each
harness's own review feature on the same tree, never one packet folder for every carrier.)

## Task
- Source: <issue URL or path — the lane opens it itself; never paste its body here>
- Finished form: <one or two lines — what the person sees and does when the whole work is done, at the level people
  customarily expect of a finished one. Not a list of parts: the parts are the lane's to recall and propose. Copy this line
  verbatim into every lane of the same work>
- This lane delivers: <the piece of the finished form this lane builds or measures>
- Ours: <the one or two things that make it ours, if the owner named any — else "find one and propose it in the report">
- Done is judged by: <checks | the owner's eye on drafts — then drafts come before the engine>
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
- Build lanes: the finished form is the bar, not the check — a green check with the form missing is not done. When what
  the person sees is the essence, deliver several drafts before the engine and say which one the owner should look at.
- Probes take the tree as an argument; never hardcode a path.
- Checks you ran: counts, the mutation result (a deliberately wrong specimen went red) and the tree fingerprint (commit or hash).
- Checks you added, if any: for each, which of the four keep-criteria of check-design §1 it meets. If you verified once without adding a check, say so, with the command and its result.
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
⑦ Add a permanent check only when all four keep-criteria of check-design §1 hold (the defect really happened or has a clear path · it is silent or irreversible when it breaks · it harms the user badly · nothing else already catches it); otherwise verify once and report the command and its result. A check and its specimen are one pair — when tightening a check turns a specimen red, fix both in the same pass.
⑧ Lanes share one machine. Run your long checks one at a time, in the background, and wait for the finish notification instead of polling or starting a second copy — overlapping copies slow every run.
⑨ The finished form measures the work, not the letter — within your ownership, whatever a finished one is customarily expected to have, and wherever the best expert in this field would do it better (design, missed cases, how it is measured, the flow the user goes through), build it even if the envelope did not list it, and list every addition with its reason in the report. What stays a proposal is what is not yours to decide — a change of direction, a decision the owner holds, a file you do not own. "New" is not a reason to hold back.
