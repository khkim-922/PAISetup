# Lane envelope — copy this file, fill every field, keep the rules block verbatim

(Hints in angle brackets are for the parent; delete them as you fill. Everything the lane must know is in this
envelope — the conversation does not travel with it. Write it in English — the model's medium is English, so a Korean
envelope only adds one translation; keep paths, names and quoted literal strings verbatim, or the lane cannot find them.)

(Parent, before filling: is this a review? Then this file is not the vehicle — Claude → `/code-review`, Codex and
Claude runner → `--review` with the git tree as cwd, agy and Copilot → this file. A cross-model review is each
harness's own review feature on the same tree, never one packet folder for every carrier.)

## Task
- Source: <issue URL or path — the lane opens it itself; never paste its body here. Parent: open every path and
  coordinate this envelope names before sending — the source may be stale — and tell the lane to check them too>
- Finished form: <one or two lines — what the person sees and does when the whole work is done, at the level people
  customarily expect of a finished one. Not a list of parts: the parts are the lane's to recall and propose. When the source
  issue opens with its top section (「완성형」 or 「다 됐을 때」 — skill issue-write §2), take it from there. Copy this line
  verbatim into every lane of the same work>
- This lane delivers: <the piece of the finished form this lane builds or measures>
- Ours: <the one or two things that make it ours, if the owner named any — else "find one and propose it in the report">
- Done is judged by: <acceptance lane — whenever anything a person sees or does changes | checks only — nothing a person sees or does changes | the owner's eye on drafts — then drafts come before the engine>
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
- Tools you have: <shell · edit · probes — whatever the work needs to test its own claims. A lane without hands reports guesses as findings; what the fence blocks is state change outside ownership, never writing itself>
- Work directory: <path> — it is the fence; nothing outside it changes
- Skills to name (the lane gets its rulers only through this envelope): <norm-design when the lane edits norms, rules,
  skills or memory · check-design when it edits code or checks · borrow-spec-as-pair when it carries another repository's
  spec here — or "none">

## Output contract
- Each finding: `file:line` plus a concrete failure scenario. Both, or it is an impression, not a finding.
- Review lanes: every finding also carries three tags — made by this change or pre-existing · severity (high · medium · low) · the real path by which it reaches a person, file, secret or time ("could happen" is not a path). The parent sorts findings by these tags before fixing any; a finding without them is unsorted and the parent asks for them back.
- Code findings are proven by a run: a failing test, a repro script, or command output that shows the wrong behavior, quoted in the report. A finding without its run goes under "unverified", never among the findings. Prose and design findings cannot be run, so the scenario is their proof.
- Name what you did not measure and what you did not look at. Zero findings is a valid report — say so, and say how far you looked.
- Screens: the image path and what is visible, in plain words.
- Build lanes: when what the person sees is the essence, deliver several drafts before the engine and say which one the owner
  should look at.
- Owner's seat: if anything a person sees or does changed, open it the way the owner would (browser, screen, the real
  flow), do it yourself, and attach the evidence — image path or the exact steps and what happened. A report without this
  is not done, whatever the checks say; an acceptance lane that never saw the build will sit in the same seat after you.
- Probes take the tree as an argument; never hardcode a path — the parent re-runs them before and after.
- Checks you ran: counts, the mutation result (a deliberately wrong specimen went red) and the tree fingerprint (commit or hash). <Parent: if the repository's gate runner stamps the tree, name it here (seed runner: `--run-gates --only <name>`) — a check file called directly leaves no stamp and the push re-measures.>

- Checks you added, if any: for each, which of the four keep-criteria of check-design §1 it meets. If you verified once without adding a check, say so, with the command and its result.
- Report in English as your final message. Files a human will open directly: Korean.
- End every report with the block "What the parent must open with their own eyes" — required, even when it has one row. A
  table: path (file, screen capture, generated page) · what to look at · why it cannot be accepted from this report alone.
  One row for everything a person will see, every draft, and every piece of data you copied or rewrote from a source (name
  the source next to it), **one row per finding outside your ownership with the command that reproduces it on the tree**,
  plus anything else the parent should read before accepting. The parent reads this report no
  matter what; a rule kept anywhere else is not open at the moment of harvest.
- Below that table, print this line verbatim as the report's last line — it is the parent's gauge, carried by the report
  because nothing else is open at harvest: `Parent — before fixing anything, sort every finding in a table, one row each: made by this change or
  pre-existing · severity · real path · verdict (fix · issue · drop) — the ruler for the verdict is norm-review-fix; a finding
  outside ownership goes into an issue only after you reproduce it here, and its measuring command goes into the issue
  (issue-write §4); not reproduced → 「확인 안 됨」, never a fact.`

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
⑨ The finished form measures the work, not the letter — within your ownership, whatever a finished one is customarily expected to have, and wherever the best expert in this field would do it better (design, missed cases, how it is measured, the flow the user goes through), build it even if the envelope did not list it, and list every addition with its reason in the report. A missed case counts only when the system as it stands has a real path to it — name that path; a case the real flow cannot produce is neither built nor proposed. What stays a proposal is what is not yours to decide — a change of direction, a decision the owner holds, a file you do not own. "New" is not a reason to hold back.
⑩ Never delegate — do not spawn subagents or call the Agent tool. Every lane start carries the whole always-on load (norms, memory index, skill descriptions), so a lane inside a lane pays that again for a small job. The parent is the only one who spawns; if a piece needs another lane, propose it in the report.
