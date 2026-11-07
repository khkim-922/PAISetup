#!/usr/bin/env bash
# 스킬을 잰다 — 같은 물음을 스킬이 있을 때와 없을 때로 claude -p 에 돌려 「걸리나 · 달라지나」를 본다(스킬 skill-from-standard 「잰다」).
#
#     bash measure.sh <결과 폴더> <물음 tsv> <스킬 폴더>...
#
# 물음 tsv — 한 줄에 「열쇠 <탭> 걸려야 할 스킬 이름 <탭> 물음」. 결과 폴더에 runs/<열쇠>.<with|without>.jsonl 과, 곁의 extract.py 가
# 뽑은 .txt(연 스킬 · 읽은 파일 · 끝 글)가 남고 끝에 한 줄 요약을 찍는다. 판정은 사람이 미리 적어 둔 기준에 .txt 를 대 보는 것이다.
#
# 두 팔은 따로 세운 설정 폴더(CLAUDE_CONFIG_DIR)로 돈다 — 홈에 깔린 스킬이 「없을 때」 팔에 섞이지 않게. 로그인 파일(.credentials.json)을
# 그 폴더에 복사했다가 끝에 지운다. 명령을 실행하는 도구(Bash · 쓰기)는 막는다 — 실제 손은 안 돌고 계획과 사람에게 할 말을 재는 것이다.
# ⚠ 홈의 전역 CLAUDE.md 는 두 팔에 다 실린다 — 그 글이 가리키는 자리에 스킬의 옛 사본이 있으면 「없을 때」 팔의 모델이 찾아 읽는다.
#   그런 판은 바닥이 아니라 「옛 판 대 새 판」으로 읽는다(.txt 의 「읽음」 줄이 그것을 보인다).
# 모델은 MEASURE_MODEL(기본 sonnet — 배포본을 받는 가장 약한 독자에 가깝게), 동시 수는 MEASURE_JOBS(기본 4). 두 팔이 서는 작업 폴더는
# MEASURE_PROJ(기본은 결과 폴더의 빈 proj) — 물음이 저장소의 파일을 가리키면 그 파일들을 둔 폴더를 준다. ⚠ 그 폴더에 `.claude/skills` ·
# `.claude/settings.json` 이 있으면 설정 폴더와 무관하게 두 팔에 다 실려(프로젝트 스킬 · 훅) 「없을 때」 팔이 안 선다 — 그런 폴더는 거절한다.
# 저장소를 재려면 `.claude/` 없는 사본을 준다. 로그인 파일이 없는 자리(게이트웨이 PC)에서는 이 손이 안 돈다.
set -eu
OUT="$(cd "$(mkdir -p "$1" && echo "$1")" && pwd)"; TSV="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PROJ="${MEASURE_PROJ:-$OUT/proj}"; mkdir -p "$OUT/home-with/skills" "$OUT/home-without" "$PROJ" "$OUT/runs"
if [ -e "$PROJ/.claude/skills" ] || [ -e "$PROJ/.claude/settings.json" ]; then
  echo "작업 폴더에 .claude/skills 나 .claude/settings.json 이 있다 — 두 팔에 다 실려 재기가 안 선다: $PROJ" >&2; exit 4
fi
[ -f "$HOME_DIR/.credentials.json" ] || { echo "로그인 파일이 없다($HOME_DIR/.credentials.json) — 이 자리에서는 못 잰다" >&2; exit 4; }
for s in "$@"; do rm -rf "$OUT/home-with/skills/$(basename "$s")"; cp -r "$s" "$OUT/home-with/skills/"; done
find "$OUT/home-with/skills" -name __pycache__ -type d -prune -exec rm -rf {} +
trap 'rm -rf "$OUT/home-with" "$OUT/home-without"' EXIT      # 로그인 사본과 계정 정보가 든 홈을 통째로 걷는다 — 복사보다 먼저 건다
cp "$HOME_DIR/.credentials.json" "$OUT/home-with/"; cp "$HOME_DIR/.credentials.json" "$OUT/home-without/"
SYS='이 자리는 회사 PC 가 아니고 명령을 실행할 도구가 없다. 그래도 실제로 하듯이 일하라 — 무엇을 어떤 차례로 부르고(명령 줄 그대로), 사람에게 무엇을 묻거나 알릴지(그 말 그대로)를 적고, 사람의 답이 필요한 자리에서 멈춘다. 스킬이 있으면 그 스킬대로.'
one() {   # $1 열쇠 · $2 팔
  local prompt; prompt="$(awk -F'\t' -v k="$1" '$1==k{print $3}' "$TSV")"
  ( cd "$PROJ" && CLAUDE_CONFIG_DIR="$OUT/home-$2" timeout 600 claude -p "$prompt" --model "${MEASURE_MODEL:-sonnet}" \
      --output-format stream-json --verbose \
      --allowedTools Read Glob Grep Skill --disallowedTools Bash PowerShell Write Edit NotebookEdit Agent WebFetch WebSearch \
      --append-system-prompt "$SYS" > "$OUT/runs/$1.$2.jsonl" 2> "$OUT/runs/$1.$2.err" ) || true
  echo "$1.$2 끝"
}
export -f one; export OUT PROJ TSV SYS MEASURE_MODEL="${MEASURE_MODEL:-sonnet}"
awk -F'\t' 'NF>=3{print $1" with"; print $1" without"}' "$TSV" | xargs -P "${MEASURE_JOBS:-4}" -n 2 bash -c 'one "$@"' _
python -X utf8 -I "$HERE/extract.py" "$OUT"
