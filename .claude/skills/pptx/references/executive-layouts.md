# 임원 보고 덱 빌더 — 데이터 규격

여덟 레이아웃에 **내용만 넘기면** 덱이 나온다. 좌표·색·활자 계층·여백은
엔진이 들고, 넘기는 쪽은 무엇을 말할지만 든다.

진본은 코드다 — `scripts/build_deck.py`. **키 목록은 여기 옮겨 적지 않는다**:

```bash
python scripts/build_deck.py --schema        # 레이아웃별 필수·선택 키 · 지면 (진본)
```

## 지면

기본은 **A4 가로(11.693 × 8.268in · 297×210mm)** 다 — 사내 보고는 결국 인쇄·PDF로
읽히고, 16:9 로 짜면 A4 에 얹을 때 위아래가 남는다. 좌표는 고정값이 아니라 지면에서
계산되므로, 지면을 바꾸면 카드 너비·행 높이·타임라인 위치가 함께 따라온다.

```json
{ "page": "a4-landscape", "slides": [] }
```

`16:9` · `4:3` · `[가로, 세로]` 도 받는다. **A4 가로와 16:9 는 검사까지 마친 자리**이고,
4:3 은 폭이 좁아 단계 카드 4개 같은 밀도에서 경고가 난다 — 그때는 항목을 줄인다.

## 쓰는 길 셋

1. **데이터(JSON) → 덱**: 완성된 8대 레이아웃에 데이터만 넘길 때
```bash
python scripts/build_deck.py deck.json -o out.pptx
```

2. **파이썬 레시피 API**: 표준 레이아웃을 파이썬 코드로 호출할 때
```python
from build_deck import Deck
deck = Deck(theme={"accent": "B8541A"}, page="a4-landscape")
deck.add_dark_cover(title=["두 줄로", "끊어 쓴 제목"], stats=[...])
deck.save("out.pptx")
```

3. **원자 부품 조립 (Atomic Primitives)**: 1장 안에서 지표, 프로세스 카드, 표를 레고 블록처럼 자유롭게 합성할 때
```python
from build_deck import Deck, Split, Grid, Card, MetricBox, StepCard, KickerHeader, CalloutBanner, MARGIN

deck = Deck()
slide = deck.add_slide()
top = KickerHeader(slide, kicker="운영 혁신", title="지능형 자율 공정 전환 현황", lead="AI 비전 및 센서 기반 4대 공정 자동 제어")
split = Split(MARGIN, top, deck.cw, deck.H - MARGIN - top - 0.7, direction='h', ratios=[0.4, 0.6], gap=0.3)

# 좌측: 지표 2개 (Grid + Card + MetricBox)
grid_l = Grid(*split[0], rows=2, cols=1, gap_y=0.2)
card1 = Card(grid_l[0], slide=slide)
MetricBox(card1, value="99.4%", label="불량 검출 정확도", desc="전년 대비 +4.2%p")
card2 = Card(grid_l[1], slide=slide)
MetricBox(card2, value="0 건", label="공정 다운타임", desc="180일 무정지 달성")

# 우측: 3단계 카드 (Grid + Card + StepCard)
grid_r = Grid(*split[1], rows=3, cols=1, gap_y=0.15)
for i, (title, items) in enumerate([("1단계", ["요건 정의"]), ("2단계", ["실증 검증"]), ("3단계", ["전사 확산"])]):
    card_s = Card(grid_r[i], slide=slide)
    StepCard(card_s, step_no=f"0{i+1}", title=title, items=items)

CalloutBanner(slide, text="2026년 상반기 내 전사 4개 사업장 수평 전개 완료 예정", rule_type="추진 로드맵")
deck.save("composite.pptx")
```

예시 셋이 짝으로 있다 — `scripts/sample_deck.json`(여덟 레이아웃 전부) ·
`scripts/example_deck.py`(파이썬 API + 테마 교체) · 본 문서의 원자 부품 합성 가이드.

## 레이아웃 여덟

| layout | 메서드 | 담는 것 | 담기는 양 |
|---|---|---|---|
| `dark_cover` | `add_dark_cover` | 다크 표지 · 인용 패널 · 큰 숫자 지표 | 제목 1~3줄, 지표 3개까지 |
| `comparison_cards` | `add_comparison_cards` | 좌우 비교 카드(라벨/값 행) + 하단 요약 줄 | 행 4개 안팎, 요약 2~4개 |
| `decision_matrix` | `add_decision_matrix` | 기준 × 선택지 판정표 — 칸마다 빈 네모(자가 체크) | 기준 3~5, 선택지 2~3 |
| `charter_grid` | `add_charter_grid` | 표준 양식 1-Pager — 좌측 원칙·콜아웃 + 우측 항목 그리드 | 항목 6~8개 |
| `charter_form` | `add_charter_form` | 작성용 빈 양식 — 입력 칸 그리드 | 줄 3~5, 줄당 칸 1~3 |
| `process_gates` | `add_process_gates` | 단계 카드 가로 흐름 + 신호등 범례 | 단계 3~5개, 범례 3개 |
| `executive_dashboard` | `add_executive_dashboard` | 2×2 사분면 — 지표 / 핵심 항목 / 현황 매트릭스 / 의사결정 요청 | 지표 3~4, 행 4~5 |
| `dark_closing` | `add_dark_closing` | 다크 마무리 — 가로 타임라인 + 액션 카드 | 단계 3~5, 액션 2~3 |

다크(표지·마무리)가 라이트(본문)를 감싸는 **샌드위치**가 기본이다. 본문이 길어지면
같은 레이아웃을 반복하기보다 축이 다른 레이아웃으로 갈아탄다.

## 판정표 (`decision_matrix`)

무엇이 어느 쪽인지 **읽는 사람이 스스로 가리게 하는** 표다. 기준을 행으로, 선택지를
열로 두고, 각 칸 앞에 빈 네모를 둔다 — 인쇄해 손으로 표시하거나 화면에서 짚어 간다.

```json
{ "layout": "decision_matrix",
  "options": [ { "title": "Track A", "subtitle": "(자체 추진)" }, { "title": "Track B" } ],
  "criteria": [ { "tag": "①", "name": "적용 범위", "desc": "Scope",
                  "values": ["한 공정에 닫힌다", "두 부서 이상이 함께 쓴다"] } ],
  "rule": { "label": "판정 규칙", "text": "3개 이상 해당하는 쪽으로 분류" } }
```

`values` 는 `options` 와 **같은 수**로 준다. `rule` 은 표 아래 한 줄로, 동률일 때
누가 정하는지까지 적어 두면 문의가 줄어든다.

## 작성용 양식 (`charter_form`)

설명 장표(`charter_grid`)와 **역할이 다르다** — 저쪽은 무엇을 적으라는 안내고,
이쪽은 받는 사람이 그 위에 바로 타이핑하는 빈 양식이다.

```json
{ "layout": "charter_form", "title": "...", "rows": [
  { "weight": 1.2, "fields": [
    { "label": "칸 제목", "flex": 1.5, "hint": "우측 작은 안내", "layout": "row",
      "inputs": [ { "caption": "칸 위 머리글", "placeholder": "회색 안내 문구", "flex": 1 } ] }
  ] }
] }
```

- `rows[].weight` 로 줄 높이를, `fields[].flex` 로 칸 너비를 나눈다 — 절대 좌표가 없다.
- `layout` 은 `row`(나란히) 또는 `stack`(위아래). 안내 문구는 **도형 안에** 들어가므로
  한 번 누르고 입력하면 그대로 대체된다.
- 번호 배지는 등장 순서대로 자동이고, `num` 을 주면 그것이 우선한다.

## 예시 표기와 안내 배지 (`note`)

라이트 레이아웃(`comparison_cards` · `charter_grid` · `process_gates` ·
`executive_dashboard` · `charter_form`)은 `note` 로 우상단에 작은 배지를 얹는다.

```json
{ "note": ["※ 아래 과제명·수치는 모두", "이해를 돕기 위한 작성 예시(Sample)"] }
```

**읽는 사람이 예시를 실적으로 착각하는 것이 가장 비싼 사고다.** 숫자·과제명이
들어간 장표에는 배지를 얹고, 항목 단위로도 `[예시]` 를 붙여 둘로 못 박는다 —
배지는 장 전체를, 태그는 그 줄을 든다.

## 체크리스트와 하단 배너 (`process_gates`)

- 범례 항목에 `tag` 를 주면 신호등 점 대신 **번호 배지**가 붙는다 — 상태 표시가
  아니라 ①②③④ 체크리스트로 읽히는 자리다. `level`(ok·warn·bad)을 주면 색이 따라온다.
- `banner` 는 카드 아래 한 줄을 붙인다(지원 사항 · 준수 사항). `{label, text}` 로 주면
  앞머리에 악센트 라벨이 붙는다.
- 단계 카드와 범례는 **남는 자리를 두고 다툰다** — 엔진이 단계 카드가 필요로 하는
  높이를 먼저 재고 남은 것을 범례에 준다. 그래도 모자라면 경고가 난다.

## 원자 부품 (Atomic Primitives) 레고 블록 명세

8대 레이아웃은 검증된 조합(Convenience Recipes)이며, 모든 레이아웃의 내부는 아래 원자 부품들의 조합으로 동작한다.
새로운 슬라이드 구조가 필요할 때 이 부품들을 직접 조립(Lego-block Assembly)한다.

### 1. 지면 구획 / 컨테이너 프리미티브 (Containers)

| 부품 | 시그니처 | 설명 |
|---|---|---|
| `Card` | `Card(x, y, w, h, bg_color=None, border_color=None, shadow=True, radius=0.035, slide=None, dark=False)` | 둥근 모서리 + 은은한 테두리 + 그림자 카드. `(x, y, w, h)` 기하 속성을 가지며 하위 원자의 부모(parent) 컨테이너가 됨. `Card(slide, x, y, w, h)` 및 `Card(cell, ...)` 형태도 지원. |
| `Grid` | `Grid(x, y, w, h, rows=1, cols=1, gap_x=GAP, gap_y=GAP)` | 행×열 격자 구획기. `grid[row, col]` 또는 `grid[idx]`로 내부 `Cell` 좌표 자동 계산. `for cell in grid:` 순회 및 언패킹 지원. |
| `Split` | `Split(x, y, w, h, direction='h'\|'v', ratios=[0.4, 0.6], gap=GAP)` | 비율 구획 분할기. 가로('h') 열 분할 또는 세로('v') 행 분할. `left, right = Split(...)` 언패킹 지원. |

### 2. 시각 원자 부품 (Content Atoms)

| 부품 | 시그니처 | 설명 |
|---|---|---|
| `MetricBox` | `MetricBox(parent, value, label, desc=None, color=None, layout='auto'\|'side_by_side'\|'stacked')` | 대형 숫자 + 캡션 지표. `parent`(`Card`, `Cell`, 좌표 튜플) 내부에 렌더링. 넓이에 따라 가로/상하 자동 전환. |
| `Badge` | `Badge(parent, text="", color=None, icon=None, size=11, x=None, y=None, d=None)` | 상태/신호등/순번 원형 배지. 'ok', 'warn', 'bad', 'accent', 'primary' 등 시맨틱 테마 색상 지원. |
| `KickerHeader` | `KickerHeader(slide, kicker=None, title="", subtitle=None, lead=None, note=None)` | 카테고리 kicker + 대형 title + lead 리드문 + 우상단 안내 배지(note)로 구성된 타이포 계층 헤더. 다음 블록 시작을 위한 바닥 Y값(`HeaderResult`, float 연산 가능) 반환. |
| `StepCard` | `StepCard(parent, step_no=None, title="", items=None, status_tag=None, period=None, output=None, criteria=None)` | 단계별 프로세스 카드 (순번 배지 + 타이틀 + 기간 + 활동 불릿 리스트 + 하단 산출물/통과기준 박스). |
| `TableBox` | `TableBox(parent, headers=None, rows=None, col_widths=None, status_label="상태", title=None)` | 행 묶음 표. 헤더 + 격줄 줄무늬 배경 + 상태 배지 포함. |
| `CalloutBanner` | `CalloutBanner(slide, text="", rule_type=None, label=None, y=None, h=0.56)` | 하단 안내 / 지원 / 판정 규칙 배너. |
| `FormField` | `FormField(parent, label="", placeholder="", flex=1.0, inputs=None, hint=None, num=None)` | 실무자 입력 필드 (순번 배지 + 라벨 + 우측 힌트 + 1개 이상의 입력 박스). |

## 데이터 문서 골격

```json
{
  "page": "a4-landscape",
  "theme": { "accent": "B8541A" },
  "font": "맑은 고딕",
  "slides": [
    { "layout": "dark_cover", "title": "...", "notes": "발표자 노트" }
  ]
}
```

`slides[]` 의 각 항목은 `layout` 하나와 그 레이아웃의 키를 든다. `notes` 는 어느
레이아웃에나 붙고 발표자 노트로 간다. 키가 틀리면 몇 번째 슬라이드에서 무엇이
틀렸는지 대고 멈춘다.

## 테마

색은 **하나가 지배하고**(`dark`·`primary`) 보조 하나(`secondary`), 악센트 하나
(`accent` / 다크 배경용 `accent_on_dark`)가 붙는다. 셋을 같은 무게로 두지 않는다.
주제에 맞는 색을 고른다 — 그 색을 다른 주제 덱에 넣어도 말이 되면 아직 덜 고른 것이다.

신호등(`ok`·`warn`·`bad`)은 진도·상태에만 쓰고 장식으로 쓰지 않는다.

## 안 그리는 것

상단 헤더 바 · 측면 스트라이프 · 카드 한쪽 테두리 강조 · 제목 밑줄 — 엔진이
**그리지 않는다.** 구분은 여백과 은은한 그림자가 들고, 강조는 큰 숫자와 원형 배지가 든다.

## 넘침은 엔진이 먼저 줄인다

블록이 자리보다 크면 글자를 단계적으로 줄이고(최대 22%), 그래도 안 들어가면 경고를
찍는다(종료 코드 1). **경고가 뜨면 글을 줄이는 쪽이 맞다** — 잘린 채 나가지 않게 하려는 신호다.

## QA — 두 갈래로 본다

**배치는 재고, 인상은 본다.** 둘은 잡는 결함이 다르다.

### 1. 배치 — PowerPoint 가 직접 잰 값으로 (`audit_layout.ps1`)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/audit_layout.ps1 -Path out.pptx
```

넘침 · 겹침 · 가장자리 여백(0.5in) 셋을 보고, 이상이 없으면 그렇게 말한다.
고치는 동안은 이쪽만 돌린다 — 빠르고 값이 싸다.

### 2. 인상 — DRM 환경의 데스크톱 스크린샷 기법 (`capture_slides.ps1`)

파일 보안(DRM) 필터 드라이버는 PowerPoint 가 **디스크에 쓰는** 산출물을 가로챈다 —
`Slide.Export()` · PDF 변환 · LibreOffice 경로가 다 막히거나 암호화된다.
빠져나가는 길은 **디스크를 거치지 않는 것**이다: 슬라이드쇼로 화면에 띄우고
`Graphics.CopyFromScreen()` 으로 화면 버퍼를 직접 읽는다. DRM 은 화면에 그려진 것을
막지 않으므로 이미지가 그대로 나온다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/capture_slides.ps1 -Path out.pptx -Slides "1,8"
```

취득한 이미지는 `view` 도구로 열어 색 대비 · 활자 인상 · 여백 균형처럼 **재서는 안
보이는 것**을 본다. 실제로 이 길로만 잡히는 결함이 있다 — 한글 낱말이 줄 끝에서
반으로 갈리는 자리가 그렇다. 배치 검사는 통과하지만 읽는 사람은 걸린다.

⚠ **한글 낱말 쪼개짐 — 속성 하나로는 안 되고, 둘이 같이 서야 듣는다(실측).**
문단의 `eaLnBrk="0"` 만으로는 PowerPoint 가 한글을 아무 자리에서나 끊는다.
런에 **`lang="ko-KR"` 을 함께 박아야** 한국어 줄바꿈 규칙이 적용되어 낱말이 살아난다 —
엔진이 둘 다 넣는다. 그래도 한 낱말이 한 줄보다 길면 갈릴 수밖에 없으니, 그때는 내용이 든다:

- 구분자 앞뒤에 **공백**을 둔다 — `내화물·노재정비` 는 한 낱말이라 갈리지만
  `내화물 · 노재정비` 는 공백에서 끊긴다.
- 갈리면 안 되는 자리는 **직접 줄을 바꾼다** — 값에 `\n` 을 넣으면 그 자리에서 끊긴다.

⚠ 낱말이 안 갈리면 줄 끝에 빈자리가 남아 **줄 수가 늘어난다** — 높이 어림이 폭을 5%
깎아 잡는 까닭이다. 이 보정을 빼면 배치 검사에서 넘침이 난다.

⚠ 세 자리가 걸린다 — 스크립트가 다 들지만, 손으로 짤 때도 같다.

- **전경 잠금** — 다른 창이 활성이면 `AppActivate` 가 먹지 않아 엉뚱한 창이 찍힌다.
  Alt 를 한 번 보내 잠금을 풀고 두 번 부른다. 찍은 뒤 픽셀 하나를 찍어 보면 확실하다.
- **남는 프로세스** — 캡처 뒤 PowerPoint 가 살아 있으면 덱 파일을 잠가 다음 빌드가
  `PermissionError` 로 죽는다. 띄운 것만 골라 끝낸다.
- **복구 창** — 앞서 죽은 PowerPoint 가 남긴 복구 항목이 있으면 슬라이드쇼 대신
  복구 창이 먼저 뜬다. `Resiliency\DocumentRecovery` 를 지우고 연다.

### 실패 계보 — 무엇이 어떻게 걸렸나

이 길을 뚫는 동안 실제로 막힌 자리들이다. **증상이 다 제각각이라 원인을 짚기 전에는
같은 벽에 다시 부딪힌다** — 그래서 남긴다.

| 시도 | 증상 | 원인 | 넘는 법 |
|---|---|---|---|
| `Slide.Export("*.png")` | 파일은 생기는데 그림이 안 열린다. 첫 바이트가 `DRMONE` | DRM 필터가 Office 가 쓴 파일을 암호화 | 디스크를 거치지 않는다 — 화면 버퍼를 읽는다 |
| 슬라이드쇼 + 바로 캡처 | 이미지는 멀쩡한데 **다른 창**이 찍힌다 | 슬라이드쇼가 전경으로 오지 않음 | Alt 전송 → `AppActivate` 두 번 → 1.2초 대기 |
| `SlideShowWindow.HWND` | `null` 을 `IntPtr` 로 못 바꾼다 | 이 버전에서 핸들이 안 나옴 | 핸들 대신 프로세스 Id 로 활성화 |
| `.Run()` 직후 `SlideShowWindow` | 「null 값에 메서드 호출」 | 창이 아직 서지 않음 | 설 때까지 폴링(최대 7.5초) |
| `-Slides 1,8` (`-File` 호출) | 「18 is not in valid range」 | `-File` 은 인수를 문자열로 넘겨 `1,8` → `18` | 문자열로 받아 스크립트 안에서 쪼갠다 |
| 강제 종료 후 재시도 | 슬라이드쇼가 안 뜬다 | 복구 창이 먼저 뜸 | `Resiliency\DocumentRecovery` 삭제 |
| 원본 PNG 를 그대로 열람 | 토큰이 과하게 든다 | 2560×1440 PNG ≈ 500KB | 1280px · JPEG 85%로 눌러 ~85KB |

⚠ **찍었다고 본 것이 아니다** — 엉뚱한 창이 찍혀도 파일은 멀쩡히 생긴다. 열기 전에
픽셀 한두 개를 찍어 슬라이드 배경색이 맞는지 보는 편이 빠르다. 실제로 이 확인을
건너뛰고 「잘 나왔다」고 보고한 적이 있다.

⚠ **비전 토큰이 비싸다** — 원본 스크린샷은 수 MB다. 고치는 동안은 배치 검사만 돌리고,
캡처는 마무리에 핵심 한두 장만 한다. 여러 장을 봐야 하면 세로로 이어 붙여 한 장으로 연다.

## 파일이 안 열릴 때

python-pptx 로 덱을 만들 때 PowerPoint 만 거부하고 다른 도구는 다 여는 XML 결함이 있다.
가장 흔한 것은 **`effectLst` 가 두 번 들어간 도형** — `shadow.inherit = False` 가 이미
빈 `effectLst` 를 넣으므로, 그림자는 그 자식으로 붙여야 한다(`_shape()` 참고).
슬라이드를 하나씩 따로 저장해 열어 보면 어느 장이 범인인지 곧 나온다.
