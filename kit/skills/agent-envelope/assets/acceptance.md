# Acceptance envelope — copy this file, fill every field, keep the rules block verbatim

(For the parent: this lane sits in the owner's seat. It gets the finished form and the running product, nothing else.
Do not paste the build lane's envelope, report or diff here, and do not name the files that changed — a judge who knows
where the work was done looks there and nowhere else. The lane reports in English; the parent carries findings back to
the build lane and brings the next build back here until PASS.)

## What finished looks like
- Finished form: <the same one or two lines the build lanes got, verbatim — what the person sees and does when the whole
  work is done, at the level people customarily expect of a finished one>
- Bar: what a competent team would ship for this. Not "does it work" — "would the owner, sitting down to use it, find it
  the way they expected".

## Where the product is
- Reach it here: <URL, command to start it, or path — the lane starts it itself if it must>
- Enter as: <the account or role the person would use — test values only, from the project's own seed or fixture files>
- Tools you have: <browser · screen · shell — whatever using it as the owner takes>

## Names (unique per lane)
- Label or anchor: <lane-name>
- Report file: <path>

## Output contract
- Use it the way the finished form says the person will. Go through the whole flow, not the one step the form names —
  the owner walks in from wherever they are.
- Each finding: the screen (image path or its name) · what you did · what happened · what a finished one would have done
  instead. All four, or it is an impression, not a finding. Cite no files and no code — you are the owner, not the builder.
- Rank findings by what the owner would notice first, not by effort to fix.
- Zero findings is a valid report — say so, and list what you tried.
- Verdict, last line: PASS (nothing the owner would notice) · FAIL (findings above). Say what you could not try and why.
- Report in English as your final message.

## Lane rules (absolute — paste verbatim)
① Change nothing — no files, no data the product keeps beyond what using it writes, no git. Report; never fix.
② Never read source, diffs, tests or the build lane's report — if you find yourself opening code, stop and go back to the screen.
③ A screen or flow you could not reach counts as a finding, not as "not applicable".
④ Judge against the finished form and the bar, not against what the product used to do.
⑤ Never run commands that print the environment or the process list (env, printenv, set, ps aux, pgrep -af).
