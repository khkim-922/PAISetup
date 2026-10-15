"""맡길 곳 조회 — 이 자리에서 어느 도구가 어느 무게를 지나를 맡기기 모델 표에서 찍는다.

    python carriers.py [--site inside|outside] [--table <models.conf>]

읽는 것 — 이 스킬 폴더의 `models.conf` 와 사용자 환경변수 `PAISETUP_SITE`(설치기가 심는다. `--site` 가 이긴다).
내는 것 — 도구마다 한 줄: deep 모델 · errand 모델 · 그 도구의 러너 스킬이 깔린 자리. 칸이 `-` 면 그 도구는
  이 자리에서 그 무게를 못 진다(표에 줄이 없다). 「도구 기본」은 표가 `-` 로 두어 도구 제 설정의 모델로 뜨는 칸이다.
  자리를 모르면 두 자리에 다 있는 칸만 남기고 그렇다고 말한다 — 모를 때 넓게 남기면 계열 선호가 무게를 건너뛴다.
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
# 러너 스킬이 깔리는 자리 — 설치기의 갈 곳 표(tool-homes.conf)가 드는 세 홈과, 이 스킬 곁(저장소의 스킬 폴더)
HOMES = (('Claude 홈', ('.claude', 'skills')), ('Codex 홈', ('.agents', 'skills')), ('agy 홈', ('.gemini', 'config', 'skills')))


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


def runner_homes(tool, here):
    """러너 스킬 폴더가 보이는 자리 이름들 — 없으면 빈 목록."""
    name = RUNNER[tool]
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
        homes = runner_homes(tool, here)
        if tool == 'claude':
            runner = '같은 앱이면 서브에이전트(Agent) · 밖에서는 ' + RUNNER[tool] + (f'({" · ".join(homes)})' if homes else '(없음)')
        else:
            runner = RUNNER[tool] + (f'({" · ".join(homes)})' if homes else '(없음 — 이 자리에서 못 띄운다)')
        print(f'{tool:<8}{deep:<34}{errand:<34}{runner}')
    print('칸이 - 면 그 도구는 이 자리에서 그 무게를 못 진다. 넘길 차례(fallback)는 러너가 스스로 따른다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
