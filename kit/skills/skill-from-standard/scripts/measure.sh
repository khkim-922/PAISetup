#!/usr/bin/env bash
# 스킬을 잰다 — 같은 물음을 스킬이 있을 때와 없을 때로 claude -p 에 돌려 「걸리나 · 달라지나」를 본다(스킬 skill-from-standard 「잰다」).
#
#     bash measure.sh <결과 폴더> <물음 tsv> <스킬 폴더>...
#
# 물음 tsv — 한 줄에 「열쇠 <탭> 걸려야 할 스킬 이름 <탭> 물음」. 결과 폴더에 runs/<열쇠>.<with|without>.jsonl 과 곁의 extract.py 가 뽑은
# .txt(연 스킬 · 읽은 파일 · 끝 글)가 남고 끝에 한 줄 요약을 찍는다. 판정은 사람이 미리 적어 둔 기준에 .txt 를 대 보는 것이다.
# 두 팔은 따로 세운 설정 폴더(CLAUDE_CONFIG_DIR — 홈의 스킬이 안 섞이게)로 돌고, 명령을 실행하는 도구는 막는다 — 계획과 할 말을 잰다.
# 손잡이 — MEASURE_MODEL(기본 sonnet — 배포본의 가장 약한 독자 쪽) · MEASURE_JOBS(기본 4) · MEASURE_PROJ(작업 폴더 · 기본은 빈 proj) ·
# MEASURE_LOGIN_MARGIN(분 · 기본 30). 종료 4 — 이 자리에서는 못 잰다(로그인 파일 없음 · 곧 만료 · 작업 폴더에 .claude 설정).
# ⚠ 홈의 전역 CLAUDE.md 는 두 팔에 다 실린다 — 그 글이 가리키는 자리에 스킬의 옛 사본이 있으면 「없을 때」 팔은 「옛 판 대 새 판」으로 읽는다.
set -eu
OUT="$(cd "$(mkdir -p "$1" && echo "$1")" && pwd)"; TSV="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PROJ="${MEASURE_PROJ:-$OUT/proj}"; mkdir -p "$OUT/home-with/skills" "$OUT/home-without" "$PROJ" "$OUT/runs"
if [ -e "$PROJ/.claude/skills" ] || [ -e "$PROJ/.claude/settings.json" ]; then
  echo "작업 폴더에 .claude/skills 나 .claude/settings.json 이 있다 — 두 팔에 다 실려 재기가 안 선다: $PROJ" >&2; exit 4
fi
[ -f "$HOME_DIR/.credentials.json" ] || { echo "로그인 파일이 없다($HOME_DIR/.credentials.json) — 이 자리에서는 못 잰다" >&2; exit 4; }
# ⚠ 도는 중에 한 팔이 토큰을 갱신하면 원본과 다른 사본이 죽는다 — 곧 만료될 토큰으로는 안 돌리고, 끝에 새 사본을 되돌린다(곁의 login.py)
LEFT="$(python -X utf8 -I "$HERE/login.py" left "$HOME_DIR/.credentials.json")" || { echo "로그인 파일에서 토큰 만료 시각을 못 읽었다 — 이 자리에서는 못 잰다" >&2; exit 4; }
if [ "$LEFT" -lt "${MEASURE_LOGIN_MARGIN:-30}" ]; then
  echo "로그인 토큰이 ${LEFT} 분 뒤 만료된다 — 도는 중에 갱신되면 이 PC 의 로그인이 끊긴다. 만료 뒤 claude 를 한 번 열어 갱신한 다음 돌린다" >&2; exit 4
fi
for s in "$@"; do rm -rf "$OUT/home-with/skills/$(basename "$s")"; cp -r "$s" "$OUT/home-with/skills/"; done
find "$OUT/home-with/skills" -name __pycache__ -type d -prune -exec rm -rf {} +
# 로그인 사본과 계정 정보가 든 홈을 통째로 걷는다 — 복사보다 먼저 건다. 걷기 전에 갱신된 사본이 있으면 원본에 되돌린다
trap 'python -X utf8 -I "$HERE/login.py" keep "$HOME_DIR/.credentials.json" "$OUT/home-with/.credentials.json" "$OUT/home-without/.credentials.json"; rm -rf "$OUT/home-with" "$OUT/home-without"' EXIT
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
