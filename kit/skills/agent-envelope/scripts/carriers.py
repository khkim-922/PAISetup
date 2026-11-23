"""맡길 곳 조회 — 이 자리에서 어느 도구가 어느 무게를 지나를 맡기기 모델 표에서 찍는다.

    python carriers.py [--site inside|outside] [--table <models.conf>]

읽는 것 — 이 스킬 폴더의 `models.conf` 와 사용자 환경변수 `PAISETUP_SITE`(설치기가 심는다. `--site` 가 이긴다).
내는 것 — 도구마다 한 줄: deep 모델 · errand 모델 · 그 도구의 러너 스킬이 깔린 자리, 그리고 도구마다 셸과 울타리(고르기에 드는
  차이 — FENCE)와 리뷰를 부르는 법(이 PC · 이 자리에서 되는 것만 — `review_lines`). 칸이 `-` 면 그 도구는
  이 자리에서 그 무게를 못 진다(표에 줄이 없다). 「도구 기본」은 표가 `-` 로 두어 도구 제 설정의 모델로 뜨는 칸이다.
  자리를 모르면 두 자리에 다 있는 칸만 남기고 그렇다고 말한다 — 모를 때 넓게 남기면 그 자리에서 무게를 못 지는 칸을 고르게 된다.
종료 — 0 찍었다 · 2 표를 못 읽었다(꼴에 안 맞는 줄은 번호와 까닭을 댄다) · 4 부르는 법이 틀렸다.

표의 꼴 검사는 설치기(`Read-ModelTable`)와 같은 규칙이다 — 한 줄이라도 틀리면 표 전체를 버린다. 틀린 줄만 빼고 읽으면
남은 줄이 다른 무게의 모델을 그 자리에 대어, 설치기는 안 심은 값을 여기서는 있는 것처럼 보인다.
"""
import argparse
import os
import sys
from pathlib import Path

SITES = ('inside', 'outside')
TOOLS = ('claude', 'agy', 'codex')
WEIGHTS = ('deep', 'errand', 'fallback')
NONE = '-'
# 도구마다 그 도구에게 맡기는 러너 스킬 — Claude 는 같은 앱 안에서는 서브에이전트(Agent 도구)라 러너가 없다
RUNNER = {'claude': 'claude-background', 'agy': 'agy-background', 'codex': 'codex-copilot-background'}
# 셸 · 제 격리 워크트리가 드는 레인을 `claude -p` 로 띄우는 러너 — 어느 도구가 맡기든 받는 쪽은 Claude 다
CLAUDE_LANE = 'claude-lane'
# 고르기에 드는 차이 둘 — 셸(제 주장을 재 볼 손)과 울타리(상태 변화를 막는 것). 띄우는 법 · 플래그 · 한도는 러너 스킬이 든다
FENCE = {'claude': '같은 앱의 서브에이전트: 셸 ○ · 격리 워크트리 · 세션의 한도를 같이 쓴다. 러너(claude-background): 셸 × · 허락 + 작업 자리. '
                   f'-p 레인({CLAUDE_LANE}): 셸 ○ · 제 격리 워크트리 · 자동 모드 · push 막음 · 결제는 구독이나 API 키',
         'agy': '셸 ○ · 묻지 않고 작업 자리 밖에도 쓴다 — 막는 울타리가 없다(작업 자리는 출발점)',
         'codex': '셸 ○ · OS 샌드박스(읽기 레인은 읽기 전용 · 고치기 레인은 작업 자리만 쓰기). Copilot 이 받으면 셸 ×'}
# 리뷰 — 도구마다 제 리뷰 기능을 부르는 법. 리뷰는 봉투가 아니라 이것으로 맡긴다. 띄우는 깃발 · 대상의 꼴은 러너 스킬이 든다
REVIEW_CLAUDE = '같은 앱이면 `/code-review`(레인이 제 트리를 리뷰하면 대상은 작업 트리 경로로 준다) · 러너는 `--review [대상]`'
REVIEW_CODEX = {'inside': 'Codex 가 리뷰한다', 'outside': 'Codex 가 리뷰하고 한도면 Copilot 의 내장 리뷰 에이전트가 받는다',
                None: 'Codex 가 리뷰한다(사외는 한도면 Copilot 의 내장 리뷰 에이전트가 받는다)'}
REVIEW_COPILOT_SESSION = 'Copilot 세션 안에서는 `/review`'
# agy 는 내장 리뷰가 없어 우리가 놓은 사용자 에이전트로 리뷰한다 — 그 파일이 이 PC 의 agy 홈에 놓였을 때만 된다
AGY_REVIEW_AGENT = 'change-review'
AGY_AGENTS = ('.gemini', 'config', 'agents')
# 러너 스킬이 깔리는 자리 — 설치기의 갈 곳 표(tool-homes.conf)가 맡기기 러너를 놓는 스킬 홈과, 이 스킬 곁(저장소의 스킬 폴더)
HOMES = (('Claude 홈', ('.claude', 'skills')), ('Codex 홈', ('.agents', 'skills')), ('agy 홈', ('.gemini', 'config', 'skills')),
         ('Copilot 홈', ('.copilot', 'skills')))


class BadTable(Exception):
    pass


def read_table(path):
    """표 → {(자리, 도구, 무게): 모델}. 꼴이 틀리면 BadTable(줄 번호와 까닭)."""
    try:
        lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    except OSError as e:
        raise BadTable(f'표를 못 읽었다 — {e}') from e
    cell, rows = {}, {s: 0 for s in SITES}
    for n, raw in enumerate(lines, 1):
        t = raw.strip()
        if not t or t.startswith('#'):
            continue
        parts = t.split(None, 3)
        if len(parts) != 4:
            raise BadTable(f'{n} 줄 — 칸이 넷이 아니다')
        site, tool, weight, model = parts[0], parts[1], parts[2], parts[3].strip()
        if site not in SITES:
            raise BadTable(f'{n} 줄 — 모르는 자리 {site}')
        if tool not in TOOLS:
            raise BadTable(f'{n} 줄 — 모르는 도구 {tool}')
        if weight not in WEIGHTS:
            raise BadTable(f'{n} 줄 — 모르는 무게 {weight}')
        if ';' in model:
            raise BadTable(f'{n} 줄 — 모델 이름에 ; 가 든다')
        rows[site] += 1
        if weight == 'fallback':
            if tool != 'agy':
                raise BadTable(f'{n} 줄 — 넘길 차례는 agy 만 든다')
            if model == NONE:
                raise BadTable(f'{n} 줄 — 넘길 차례에 - 가 든다')
            continue   # 넘김은 러너가 스스로 따른다 — 고르는 자리에는 안 보인다
        key = (site, tool, weight)
        if key in cell:
            raise BadTable(f'{n} 줄 — {site} {tool} {weight} 가 두 줄이다')
        cell[key] = model
    for s in SITES:
        if not rows[s]:
            raise BadTable(f'자리 {s} 의 줄이 없다')
    return cell


def runner_homes(name, here):
    """러너 스킬 `name` 의 폴더가 보이는 자리 이름들 — 없으면 빈 목록."""
    found = []
    if (here.parent / name / 'SKILL.md').is_file():
        found.append('이 스킬 곁')
    home = Path(os.path.expanduser('~'))
    for label, parts in HOMES:
        if (home.joinpath(*parts) / name / 'SKILL.md').is_file():
            found.append(label)
    return found


def shown(model):
    if model is None:
        return NONE
    return '도구 기본' if model == NONE else model


def review_lines(site, home=None):
    """도구마다 리뷰를 부르는 법 — 이 PC(`home` 의 agy 홈)와 이 자리(`site` — 모르면 None)에서 되는 것만. 리뷰 기능이 없는 도구는
    그렇다고 적는다 — 그 도구의 리뷰만 봉투로 맡긴다."""
    home = Path(home or os.path.expanduser('~'))
    has_agent = (home.joinpath(*AGY_AGENTS) / f'{AGY_REVIEW_AGENT}.md').is_file()
    agy = (f'리뷰 에이전트 `{AGY_REVIEW_AGENT}` 를 이름으로 부르게 한다' if has_agent
           else f'리뷰 기능 없음(리뷰 에이전트 `{AGY_REVIEW_AGENT}` 가 이 PC 의 agy 홈에 없다) — 리뷰는 봉투로 맡긴다')
    return [f'claude: {REVIEW_CLAUDE}', f'agy: {agy}',
            f'codex: {RUNNER["codex"]} `--review [대상]` — {REVIEW_CODEX[site]}', REVIEW_COPILOT_SESSION]


def main():
    ap = argparse.ArgumentParser(add_help=True, description='이 자리에서 어느 도구가 어느 무게를 지나를 맡기기 모델 표에서 찍는다')
    ap.add_argument('--site', choices=SITES, help='자리 — 없으면 PAISETUP_SITE, 그것도 없으면 두 자리의 교집합')
    ap.add_argument('--table', help='모델 표 — 없으면 이 스킬 폴더의 models.conf')
    try:
        a = ap.parse_args()
    except SystemExit as e:
        return 0 if e.code == 0 else 4
    here = Path(__file__).resolve().parent.parent
    table = Path(a.table) if a.table else here / 'models.conf'
    try:
        cell = read_table(table)
    except BadTable as e:
        print(f'✗ 맡기기 모델 표를 버렸다 — {e} ({table})')
        return 2
    site = a.site or os.environ.get('PAISETUP_SITE', '').strip() or None
    if site and site not in SITES:
        print(f'· PAISETUP_SITE={site} 는 모르는 자리다 — 두 자리의 교집합으로 본다')
        site = None

    def model(tool, weight):
        if site:
            return cell.get((site, tool, weight))
        a_, b_ = cell.get(('inside', tool, weight)), cell.get(('outside', tool, weight))
        if a_ is None or b_ is None:
            return None
        return a_ if a_ == b_ else '(자리마다 다르다)'

    print(f'자리 {site} (PAISETUP_SITE)' if site else '자리를 모른다 — 두 자리에 다 있는 칸만 남겼다. 설치기가 PAISETUP_SITE 를 심는다')
    print(f'{"도구":<8}{"deep":<34}{"errand":<34}러너')
    for tool in TOOLS:
        deep, errand = shown(model(tool, 'deep')), shown(model(tool, 'errand'))
        homes = runner_homes(RUNNER[tool], here)
        if tool == 'claude':
            lane = runner_homes(CLAUDE_LANE, here)
            runner = ('같은 앱이면 서브에이전트(Agent) · 밖에서는 ' + RUNNER[tool] + (f'({" · ".join(homes)})' if homes else '(없음)')
                      + f' · 셸 레인 {CLAUDE_LANE}' + (f'({" · ".join(lane)})' if lane else '(없음)'))
        else:
            runner = RUNNER[tool] + (f'({" · ".join(homes)})' if homes else '(없음 — 이 자리에서 못 띄운다)')
        print(f'{tool:<8}{deep:<34}{errand:<34}{runner}')
    print('칸이 - 면 그 도구는 이 자리에서 그 무게를 못 진다. 넘길 차례(fallback)는 러너가 스스로 따른다.')
    print('셸 · 울타리 — ' + ' / '.join(f'{tool}: {FENCE[tool]}' for tool in TOOLS))
    print('리뷰 — ' + ' / '.join(review_lines(site)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
