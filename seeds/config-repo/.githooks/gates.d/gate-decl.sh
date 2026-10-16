#!/bin/sh
# 층 — 만드는 사람의 흐름
# 걷는 조건 — 층과 깨우는 길을 조각 머리말이 대는 꼴(#170 설계안 L4)로 옮겨 선언의 [layer] · [always] 절이 사라지거나, 러너가 선언을 읽으며 같은 것을 스스로 막으면 걷는다
#
# 조각 — **게이트 선언이 켠 조각마다 층과 깨우는 길을 대나.** 선언(`.githooks/gates.conf`) 한 장만 읽는다(결정 0148 ·
#   스킬 check-design 3 · 4 · 7 절). 형제 저장소도 제 선언에 켤 수 있는 공유 조각이다.
#
# 왜 있나 — 검사를 지을 때 「어느 층이고 언제 깨나」를 묻는 자리가 없으면 무거운 검사가 커밋 문에 하나씩 붙는다. 남길지 ·
#   어느 층인가의 판단은 스킬이 들고, 기계가 잴 수 있는 것만 여기서 막는다.
#
# 무엇을 막나 — 켠 조각([pre-commit] · [commit-msg] · [pre-push] 에 적힌 이름)마다
#   · [layer] 에 층 하나 — 아래 LAYERS 의 셋 가운데 하나다. 판정마다 층이 갈리는 조각은 「늦어도」가 가장 이른 층을 댄다
#   · [when] 의 글롭이나 [always] 의 까닭 가운데 **하나만** — 둘 다 대면 [always] 가 거짓이다(러너는 [when] 으로 고른다)
#   · 검사의 검사는 막는 문 어디에도 못 선다 — 그 층은 정기적으로 돌고 막지 않고 알린다(3 절). 게이트의 문은 셋 다 막는다
#   · 네 절([layer] · [when] · [always] · [alone])에 적힌 이름은 다 켠 조각이다 — 오타면 선언한 사람만 속는다
#   · [when] 의 글롭과 [always] 의 까닭은 비지 않는다 — 러너는 빈 [when] 을 「늘 돈다」로 읽는다
#
# ⚠ **못 재는 것** — 층 이름이 맞나(조각이 정말 그 층인가)와 무게(잰 시간)다. 층만으로는 무거운 조각이 커밋 문에 서는 것을
#   못 가린다 — 러너 꼬리의 조각별 시간이 그 증거고, 문을 고르는 판단은 스킬 4 절이 든다. [when] 이 조각의 문보다 넓은가는
#   조각을 실제로 띄워 보는 `scripts/check-gate-gatekeeper.sh` 가 잰다.
# ⚠ **선언은 러너의 파서로 읽는다**(`_gates_conf`) — 파서를 두 벌 두면 이 조각과 러너가 다른 선언을 읽는다. 러너는 이 조각
#   곁(`../gates-run.sh`)에 서고, [layer] · [always] 는 모르는 절로 건너뛴다. 곁에 러너가 없으면 「못 쟀다」다.
#
# 손으로 부를 때 — `PROJECT_DIR=<저장소> sh .githooks/gates.d/gate-decl.sh`(PROJECT_DIR 이 없으면 지금 자리의 저장소).
# 종료코드 계약은 다른 조각과 같다 — 0 맞다 · 1 어긋났다 · 2 못 쟀다.
set -u

# 층 — 스킬 check-design 3 절의 표가 진본이다. 그 표의 이름이 바뀌면 여기도 고친다.
LAYERS='쓰는 사람의 계약|만드는 사람의 흐름|검사의 검사'
# 막는 문에 못 서는 층
NO_BLOCK='검사의 검사'

root="${PROJECT_DIR:-}"
[ -n "$root" ] || root="$(git rev-parse --show-toplevel 2>/dev/null)" || root=''
[ -n "$root" ] || { printf '· 게이트 선언 — 저장소 자리를 몰라(PROJECT_DIR · git) 못 쟀다.\n' >&2; exit 2; }
conf="$root/.githooks/gates.conf"
# 러너는 선언이 없으면 조각을 안 띄운다 — 여기 오는 것은 손으로 부른 자리다.
[ -f "$conf" ] || { printf '· 게이트 선언이 없다(%s) — 잴 것이 없다.\n' "$conf" >&2; exit 0; }

runner="$(dirname "$0")/../gates-run.sh"
[ -f "$runner" ] || { printf '· 게이트 선언 — 이 조각 곁에 러너가 없어(%s) 선언을 못 읽었다 · 못 쟀다.\n' "$runner" >&2; exit 2; }
# shellcheck source=.githooks/gates-run.sh
. "$runner"
command -v _gates_conf >/dev/null 2>&1 ||
    { printf '· 게이트 선언 — 곁의 러너(%s)에 선언 파서가 없다 · 못 쟀다.\n' "$runner" >&2; exit 2; }

# 줄마다 「절 이름 + 빈칸 + 본문」 — 선언 절은 본문이 「이름 = 값」으로 다듬어져 온다.
found="$(_gates_conf "$conf" "pre-commit commit-msg pre-push layer when always alone" 1 |
    awk -v layers="$LAYERS" -v noblock="$NO_BLOCK" '
        BEGIN { n = split(layers, L, "|"); for (i = 1; i <= n; i++) known[L[i]] = 1 }
        {
            sec = $1; rest = substr($0, length(sec) + 2)
            if (sec == "pre-commit" || sec == "commit-msg" || sec == "pre-push") {
                if (!(rest in on)) order[++k] = rest
                on[rest] = on[rest] "[" sec "]"
                next
            }
            p = index(rest, " = ")
            if (p) { name = substr(rest, 1, p - 1); val = substr(rest, p + 3) } else { name = rest; val = "" }
            sub(/ +$/, "", name); sub(/ +$/, "", val)
            if ((sec, name) in val_of) { dup = add(dup, "[" sec "] " name); next }
            val_of[sec, name] = val; decl[++m] = sec SUBSEP name
        }
        function add(s, x) { return s " " x }
        END {
            for (i = 1; i <= k; i++) {
                g = order[i]
                if (!(("layer", g) in val_of)) nolayer = add(nolayer, g)
                else {
                    v = val_of["layer", g]
                    if (!(v in known)) badlayer = add(badlayer, g "(" (v == "" ? "빈 값" : v) ")")
                    else if (v == noblock) blocked = add(blocked, g on[g])
                }
                w = (("when", g) in val_of); a = (("always", g) in val_of)
                if (w && val_of["when", g] == "") emptywhen = add(emptywhen, g)
                if (a && val_of["always", g] == "") emptyalways = add(emptyalways, g)
                if (!w && !a) noway = add(noway, g)
                else if (w && a) both = add(both, g)
            }
            for (j = 1; j <= m; j++) {
                split(decl[j], kk, SUBSEP)
                if (!(kk[2] in on)) stray = add(stray, "[" kk[1] "] " kk[2])
            }
            if (nolayer != "")     print "[layer] 가 없다:" nolayer
            if (badlayer != "")    print "모르는 층:" badlayer " — 스킬 check-design 3 절의 셋(" layers ") 가운데 하나를 댄다"
            if (blocked != "")     print "검사의 검사가 막는 문에 섰다:" blocked " — 그 층은 정기적으로 돌고 막지 않는다(3 절)"
            if (noway != "")       print "[when] 도 [always] 도 없다:" noway " — 지키는 경로를 [when] 에, 경로로 못 고르는 까닭을 [always] 에 댄다"
            if (both != "")        print "[when] 과 [always] 를 둘 다 댔다:" both " — 러너는 [when] 으로 고르므로 [always] 가 거짓이다"
            if (emptywhen != "")   print "[when] 의 글롭이 비었다:" emptywhen " — 러너는 빈 값을 「늘 돈다」로 읽는다"
            if (emptyalways != "") print "[always] 의 까닭이 비었다:" emptyalways
            if (stray != "")       print "켠 조각이 아닌 이름:" stray " — 오타거나 걷은 조각의 남은 줄이다"
            if (dup != "")         print "같은 절에 같은 이름이 두 줄이다:" dup " — 러너는 첫 줄만 읽으므로 덧붙인 줄은 아무것도 안 바꾼다"
        }')" || { printf '· 게이트 선언 — 선언을 못 읽었다(%s) · 못 쟀다.\n' "$conf" >&2; exit 2; }

[ -n "$found" ] || exit 0
printf '✖ 게이트 선언(.githooks/gates.conf)이 켠 조각의 층 · 깨우는 길을 다 대지 않았다 —\n' >&2
printf '%s\n' "$found" | sed 's/^/    · /' >&2
printf '  뜻과 문법은 선언 머리말과 이 조각(gates.d/gate-decl.sh) 머리말이 든다.\n' >&2
exit 1
