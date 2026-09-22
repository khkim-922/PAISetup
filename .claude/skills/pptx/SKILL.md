---
name: pptx
description: "Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates (.potx), layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward. If a .pptx or .potx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX creation, editing, and analysis

A `.pptx` is a ZIP archive of XML files. Choose your approach by task:

| Task | Approach |
|---|---|
| **Create** a new deck | Write a `pptxgenjs` script — see gotchas below |
| **Create** a Korean executive report deck (A4 landscape by default, python-pptx) | Feed JSON to `scripts/build_deck.py` — see [임원 보고 덱 빌더](#임원-보고-덱-빌더-로컬-추가) |
| **Edit** an existing deck, or build from a template | unzip → edit `ppt/slides/slideN.xml` → zip |
| **Read** content | `markitdown deck.pptx` (one block per slide under `<!-- Slide number: N -->` markers); visual grid: `python scripts/thumbnail.py deck.pptx` |

## Scripts

Paths are relative to this skill's directory. Everything else is plain Python, `node`, or shell.

| Script | What it does |
|---|---|
| `scripts/thumbnail.py deck.pptx [prefix]` | Labeled grid of every slide, for picking template layouts. `.pptx` only. Pass `prefix` — it defaults to `thumbnails`, which overwrites the grids of any other deck done in the same directory |
| `scripts/add_slide.py unpacked/ slide2.xml [--after slideN.xml]` | Duplicate a slide (or a `slideLayoutN.xml`) with all the package bookkeeping. Also takes a `.pptx` directly with `-o out.pptx` |
| `scripts/clean.py unpacked/` | Delete slides, media, and rels no longer referenced. Run **after** `<p:sldIdLst>` is final |
| `scripts/office/validate.py deck.pptx [--original src.pptx]` | Schema, relationship, content-type, chart and slide checks; each failure names its fix. Pass `--original` for any template-derived deck — it baselines the schema checks against the template, so the template's own XSD errors don't read as yours |
| `scripts/office/soffice.py --headless --convert-to pdf deck.pptx` | LibreOffice wrapper — bare `soffice` hangs in this sandbox |
| `scripts/build_deck.py data.json -o out.pptx` | 로컬 추가 — 데이터(JSON)만 넘기면 임원 보고용 덱(기본 A4 가로)이 나온다. `--schema` 로 레이아웃·키·지면 목록 |
| `scripts/audit_layout.ps1 -Path deck.pptx` | 로컬 추가 — PowerPoint 가 직접 잰 글 높이로 넘침·겹침·여백을 검사한다 (고치는 동안 돌리는 검사) |
| `scripts/capture_slides.ps1 -Path deck.pptx -Slides "1,8"` | 로컬 추가 — DRM 환경에서 슬라이드쇼를 화면 캡처해 육안 QA용 이미지를 만든다. 줄이기는 씨앗 부품 `_check/_shrink.py` 가 든다 — 이 스킬은 제 사본을 안 든다 |

## 임원 보고 덱 빌더 (로컬 추가)

`pptxgenjs` 가 없거나 한국어 임원 보고서를 python-pptx 로 짜야 하는 자리에 쓴다.
여덟 레이아웃에 **내용만 넘기면** 좌표·색·활자 계층·여백은 엔진이 든다.
지면 기본값은 **A4 가로(11.693 × 8.268in)** — 사내 보고는 결국 인쇄·PDF로 읽힌다.
`page` 로 `16:9` · `4:3` · `[가로, 세로]` 를 줄 수 있고, 좌표는 지면에 맞춰 다시 계산된다.

```bash
python scripts/build_deck.py --schema                     # 레이아웃·키·지면 (진본)
python scripts/build_deck.py scripts/sample_deck.json -o out.pptx
powershell -ExecutionPolicy Bypass -File scripts/audit_layout.ps1 -Path out.pptx
```

| layout | 담는 것 |
|---|---|
| `dark_cover` | 다크 표지 · 인용 패널 · 큰 숫자 지표 콜아웃 |
| `comparison_cards` | 좌우 비교 카드 + 하단 요약 줄 (2-Track · 전후 비교) |
| `decision_matrix` | **판정표** — 기준 × 선택지, 칸마다 빈 네모로 자가 체크 |
| `charter_grid` | 표준 양식 1-Pager — 좌측 원칙·콜아웃 + 우측 항목 그리드 |
| `charter_form` | **작성용 빈 양식** — 칸을 누르고 바로 타이핑하는 입력 그리드 |
| `process_gates` | 단계 카드 가로 흐름 + 신호등 범례 |
| `executive_dashboard` | 2×2 사분면 — 지표 / 핵심 항목 / 현황 매트릭스 / 의사결정 요청 |
| `dark_closing` | 다크 마무리 — 가로 타임라인 + 액션 카드 |

- 다크(표지·마무리)가 라이트(본문)를 감싸는 샌드위치가 기본이고, 헤더 바·측면
  스트라이프·제목 밑줄은 엔진이 **그리지 않는다.**
- 라이트 레이아웃은 `note` 로 우상단에 **안내 배지**를 얹는다 — 예시(Sample) 표기,
  기준일, 출처처럼 「이건 진짜가 아니다 · 이때 기준이다」를 대는 자리다.
- `process_gates` 는 `banner` 로 하단에 지원·안내 한 줄을 붙이고, 범례 항목에 `tag` 를
  주면 신호등 점 대신 번호 배지가 붙어 **체크리스트**로 읽힌다.
- 블록이 넘치면 글자를 먼저 줄이고, 그래도 안 들어가면 경고를 찍는다(종료 코드 1)
  — 경고가 뜨면 글을 줄이는 쪽이 맞다.
- 색·데이터 규격·파일이 안 열릴 때의 진단은 `references/executive-layouts.md` 가 든다.
  예시는 `scripts/sample_deck.json`(여덟 레이아웃) · `scripts/example_deck.py`(파이썬 API).

### ⚠ Anti-Anchoring — 레고 블록이지 완성된 성이 아니다

`scripts/build_deck.py`와 `sample_deck.json`은 보일러플레이트(좌표 계산, 여백, 폰트 축소, 오버플로우 감사)를 아끼는 **원자적 레이아웃 부품(Primitives)**을 제공하며, 8대 레이아웃은 이를 조립한 상위 편의 레시피(Convenience Helpers)다. 모든 덱이 따라야 할 **정형화된 틀(템플릿)이 아니다.**

- **[원자 부품(Atomic Primitives) API]**:
  - **지면 구획 / 컨테이너**: `Card(x, y, w, h, bg_color, border_color, shadow=True)`, `Grid(x, y, w, h, rows, cols, gap_x, gap_y)`, `Split(x, y, w, h, direction='h'|'v', ratios=[0.4, 0.6], gap=0.3)`
  - **시각 원자 부품**: `MetricBox(parent, value, label, desc)`, `Badge(parent, text, color, icon)`, `KickerHeader(slide, kicker, title, subtitle, lead)`, `StepCard(parent, step_no, title, items, status_tag)`, `TableBox(parent, headers, rows, col_widths)`, `CalloutBanner(slide, text, rule_type)`, `FormField(parent, label, placeholder, flex)`
- **[사안의 본질이 양식을 호출한다]** — 덱의 스토리라인, 슬라이드 구성 및 장수는 사용자의 목적(전략 제안, 기술 보고, 킥오프, 교육 등)에 따라 **먼저 자유롭게 기획**한다. 엔진에 있는 8개 레시피에 억지로 끼워 맞추지 않는다.
- **[블록 합성 규약]** — 8개 레이아웃은 선택지 중 하나다. "좌측 지표 2개 + 우측 3단계 카드", 와이드 타임라인, 다축 매트릭스 등 새로운 레이아웃이 필요하면 `Card`, `Grid`, `Split`, `MetricBox`, `StepCard` 등의 원자 부품을 파이썬 코드로 레고 블록처럼 자유롭게 조합·합성하여 생성한다.
- **[테마 다양성 보장]** — 네이비 샌드위치가 유일한 답이 아니다. 주제에 맞춰 아래 [Color Palettes]의 10대 추천 팔레트(Ocean Teal, Sage Calm, Charcoal Minimal 등)와 명암 구성을 능동적으로 선택한다.

## Creating with pptxgenjs — gotchas

`pptxgenjs` is preinstalled — do not run `npm install` first; write the script and `require('pptxgenjs')` directly. Only if that require fails: `npm install pptxgenjs`. The model knows the API; these are the footguns:

- **Standard Canvas is A4 Landscape (A4 가로 표준).** 사내 보고·인쇄·PDF 열람 기본 표준은 **A4 가로** (29.7cm × 21.0cm / 11.693" × 8.268")다.
  - python-pptx: `prs.slide_width = Inches(11.693)`, `prs.slide_height = Inches(8.268)` (또는 PPT A4 프리셋 10.833" × 7.5").
  - pptxgenjs: `pres.defineLayout({ name: 'A4_LANDSCAPE', width: 11.693, height: 8.268 }); pres.layout = 'A4_LANDSCAPE';`.
  - 사용자가 16:9 와이드스크린을 명시적으로 요구하지 않는 한, 슬라이드 캔버스는 A4 가로를 기본 규격으로 적용한다.
- **Hex colors: never `#`, never 8 digits.** `color: "FF0000"`. Both `"#FF0000"` and alpha baked into the hex (`"00000020"`) **corrupt the file**. For translucency: `transparency: 0-100` on fills and images, `opacity: 0.0-1.0` on shadows — each is silently ignored on the other.
- **pptxgenjs mutates option objects in place** (converts values to EMU on first use). Never share one `shadow`/options object across two `add*` calls — build a fresh object each time.
- **Shadow `offset` must be ≥ 0** — a negative offset corrupts the file. To cast a shadow upward, use `angle: 270` with a positive offset.
- **`letterSpacing` is silently ignored** — the real option is `charSpacing`.
- **Lists:** `bullet: true` on each item, never a literal `•` (renders double bullets). Set `breakLine: true` on every array item except the last. Space bulleted paragraphs with `paraSpaceAfter`, not `lineSpacing` (huge gaps).
- **One `new pptxgen()` per output file** — never reuse an instance.
- **`rectRadius` only works on `ROUNDED_RECTANGLE`**, not `RECTANGLE`.
- **Gradient fills aren't supported** — use a gradient image as the background instead.
- **Text boxes have built-in internal padding** — set `margin: 0` whenever text must align with a shape, line, or icon at the same x.
- **Speaker notes go in `slide.addNotes("...")`** (plain text, once per slide), never in a text box on the slide.
- **Keep charts native.** Use `addChart()` for everything PowerPoint can chart (pass an array of `{type, data, options}` for combos). For PowerPoint-native features the library doesn't expose (trendlines, error bars), compute the extra series yourself or post-process the generated OOXML — do not fall back to a rendered image. Only chart types PowerPoint has no native form for (Sankey, network, chord) go in as images.
- **Default charts render bare** — no title, no data labels, dated palette. Set `showTitle` + `title`, `showValue: true` + `dataLabelPosition`, `chartColors: [...]` from your palette, and quiet the frame (`catAxisLabelColor`/`valAxisLabelColor`, `valGridLine: { color, size }`, `catGridLine: { style: "none" }`, `showLegend: false` for a single series).
- **On a stacked bar or column chart, `dataLabelPosition` must be `ctr`, `inEnd`, or `inBase`.** `outEnd` **corrupts the file**.
- **A combo series using `secondaryValAxis`/`secondaryCatAxis` needs both `valAxes` and `catAxes` on the chart options, two entries each.** Without them pptxgenjs writes axis *ids* it never declares, and PowerPoint **discards that chart** and reports the file as corrupt. Supplying only `valAxes` is not enough.
- **After `writeFile()`, run `python scripts/office/validate.py deck.pptx`.** It reports the two chart faults above and the slide-XML defects PowerPoint refuses, and names the fix for each. Fix them in your generator, not by hand-editing the packed XML.
- **Never reorder the children of `<p:presentation>`.** pptxgenjs writes `<p:notesMasterIdLst>` right after `<p:sldIdLst>` and points both masters at one theme part. PowerPoint reads that happily — move the element and the same deck becomes unopenable.
- **Icons:** render `react-icons` to SVG (`ReactDOMServer.renderToStaticMarkup`), rasterize with `sharp` at ≥256px, and insert via `addImage({ data: "image/png;base64," + buf.toString("base64") })` — the `image/png;base64,` prefix is required (`react-icons`, `react`, `react-dom`, and `sharp` are preinstalled — `npm install react-icons react react-dom sharp` only if a require fails).

## Editing existing decks and templates

Pick layouts first: `python scripts/thumbnail.py template.pptx template-thumbs` writes a labeled grid of every slide and prints the file(s) it created — `template-thumbs.jpg`, split into `template-thumbs-N.jpg` past 12 slides. **Always pass that second argument, named after the deck.** It defaults to `thumbnails`, so two decks thumbnailed in one directory silently overwrite each other's grids — the first deck's are simply gone (template analysis only — visual QA needs the full-resolution renders from [Converting to Images](#converting-to-images); it only accepts `.pptx`, so copy a `.potx` to a `.pptx` name first). Use it with `markitdown` to map each content section onto a template slide, and vary the layouts — don't put every section on the same title-and-bullets slide.

```bash
python -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall('unpacked')" deck.pptx
python scripts/add_slide.py unpacked/ slide2.xml --after slide2.xml   # duplicate a slide (or slideLayoutN.xml); prints the new slide's path
# reorder / delete slides = edit <p:sldIdLst> in ppt/presentation.xml
python scripts/clean.py unpacked/                                     # after deletions: removes orphaned slides, media, rels
# edit slide content in ppt/slides/slideN.xml
(cd unpacked && rm -f ../out.pptx && zip -Xr ../out.pptx .)           # zip from INSIDE the dir; rm first or deleted parts survive
python scripts/office/validate.py out.pptx --original deck.pptx
```

- **Do all structural work — add, delete, reorder — before editing any slide's content.** `add_slide.py` copies a slide file verbatim, so duplicating after you edit clones the edited content; and `clean.py` deletes any slide missing from `<p:sldIdLst>`, including one you just wrote.
- **Never copy a slide file by hand** — `add_slide.py` does every registration a new slide needs and reports what it made (`Created ppt/slides/slide17.xml from slide2.xml`). It also works directly on a file: `add_slide.py deck.pptx slide2.xml -o out.pptx` — **pass `-o`, or it rewrites the input deck in place.** A duplicated slide still *references* its source's chart/SmartArt/embedded-object parts rather than cloning them, so editing one slide's chart changes the other's.
- **If you use `python-pptx`**, three things it won't do: duplicate a slide (its only entry point is `add_slide(layout)`), preserve formatting through `text_frame.text = "..."` (that collapses the paragraph to a single unstyled run — assign `run.text` instead), or read the SVG/EMF most template art uses (`add_picture` raises `UnidentifiedImageError`).
- Legacy `.ppt` must be converted first: `python scripts/office/soffice.py --headless --convert-to pptx file.ppt`. `.potx` templates unpack and pack identically — keep the `.potx` extension on the output.
- To reuse a template icon or image, duplicate a slide or layout that already contains it.

When filling in a template:

- If you script an XML transform, parse with `defusedxml.minidom` — round-tripping OOXML through `xml.etree.ElementTree` rewrites namespace prefixes and corrupts the deck.
- **Template slots ≠ source items.** If the template shows 4 team members and you have 3, delete the 4th member's entire group (image + text boxes), not just its text — then check for orphaned visuals in QA.
- One `<a:p>` per list item — never concatenate items into a single paragraph. Copy the sibling `<a:pPr>` to preserve spacing, and put `b="1"` on the `<a:rPr>` of titles, section headers, and inline labels (`Status:`, `Owner:`).
- Let bullets inherit from the layout; only add `<a:buChar>`, `<a:buAutoNum>` (numbered), or `<a:buNone>` to override — never a literal `•` in the text.
- Text with leading or trailing spaces needs `xml:space="preserve"` on its `<a:t>`.

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles. Carry it across every slide. **Do not use a color bar or accent stripe as your motif** (see Avoid list).

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Font names you write into the .pptx are rendered by the user's PowerPoint, not by this environment.** Your visual QA renders via LibreOffice, which substitutes fonts it doesn't have — and for some fonts the substitute has different widths, so your QA preview can show text overflow (or fit) that the real deck won't have. To keep your QA trustworthy:

- **Safe fonts** (render true-to-width in QA *and* ship with Office): **Arial, Calibri, Cambria, Times New Roman, Courier New, Bookman Old Style, Century Schoolbook**. Use these for body text and anything where fit matters.
- **Headers with personality at zero QA risk**: pair a safe-list serif header (Cambria, Bookman Old Style, Century Schoolbook) with a safe-list sans body (Calibri or Arial). You get visual contrast without giving up reliable overflow checks.
- **If the user asks for a font outside the safe list** (e.g. Georgia or Trebuchet MS): use it where the user asked, but size those containers with extra slack (~10%) and don't trust QA text-fit on those elements — the preview of that font is approximate. If the user hasn't specified, prefer safe-list fonts for body text.
- **QA-unreliable fonts** (substitute has different widths — overflow checks can be wrong): Georgia, Trebuchet MS, Impact, Arial Black, Garamond, Consolas, Palatino Linotype. Calibri Light substitution varies by environment; treat as QA-unreliable. Fine for titles/accents with slack; don't trust QA text-fit on these.
- **Never default to Aptos** — Office's post-2023 default has no metric-compatible substitute here *and* is missing from older Office installs, so it's unreliable on both ends.

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead
- **NEVER add decorative color bars or accent stripes** — this includes: header/footer bars spanning the slide width, vertical sidebar stripes down one edge of the slide, thin accent stripes along one edge of a card or content block, and "single-side borders" on rectangles. These read as AI-generated filler. If you want to set a card apart, use a subtle background tint, a drop shadow, or an icon — not an edge stripe.
- **Don't default to cream/beige backgrounds** — when no background is specified, use white (`FFFFFF`) or the user's brand palette; avoid warm-neutral defaults like `F5F5DC`, `FAF0E6`, `FAEBD7`, `FFF8E1`
- **Don't ship text that overflows its shape** — if text doesn't fit, reduce font size, split across slides, or enlarge the container; never leave content cut off or spilling past bounds

## QA (Required)

Your first render usually has a few real issues — overlaps, overflow, misalignment. Find and fix those, re-render only the slides you changed, and stop.

### Content QA

```bash
markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
markitdown output.pptx | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### File QA (required)

```bash
python scripts/office/validate.py output.pptx                      # built from scratch
python scripts/office/validate.py output.pptx --original src.pptx  # built from a template
```

**If the deck came from a template, always pass `--original`.** A template may itself
contain parts the XSD rejects, so a bare run can report failures you never caused — and
a genuine regression can hide among them. `--original` baselines
the schema and slide checks against the template, suppressing errors it already had.
The structural checks — relationships, content types, charts — ignore `--original` and
report template-inherited problems either way, so read those on their own merits.

pptxgenjs emits chart XML PowerPoint refuses to open, and every other tool
accepts: python-pptx opens those decks, LibreOffice renders them, the XSD
passes them. Every failure names its fix. Fix it in the generator and rebuild.

### Visual QA

Convert the slides to images (see [Converting to Images](#converting-to-images)) and inspect every one. After staring at the generating code you tend to see what you expect rather than what rendered, so look at the images fresh (a subagent works well for this if you have one). User-visible defects to look for:

- **Text overflow or text cut off at a box or slide boundary — check this first.** It is the most common defect and always user-visible. (For a font the previewer renders unreliably per Typography, the preview is approximate: trust the ~10% slack you left, not its apparent fit.)
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Template decoration mispositioned after text replacement — e.g., a title underline positioned for one line, but the replaced title wrapped to two
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

## Converting to Images

Convert presentations to individual slide images for visual inspection.

⚠ **해상도를 먼저 고른다 — 다 찍어 놓고 누르면 늦다.** 비전 토큰은 치수가 정하고
(`⌈가로/28⌉ × ⌈세로/28⌉`) 바이트도 압축률도 값을 한 푼도 안 줄인다. A4 가로 기준
`-r 100` 은 한 장에 약 1,260 토큰, `-r 150` 은 약 2,835 다. **글자가 읽히는 가장 낮은 값**을
고르고, 이미 큰 그림을 받은 자리는 씨앗 `_check/_shrink.py` 가 줄인다.

⚠ **사내 게이트웨이를 지나는 자리는 프록시가 서야 그림이 보인다.** 그 게이트웨이는 `tool_result`
안의 그림을 200 에 조용히 버리는데 그림 읽는 도구가 바로 그 자리에 싣는다 — **오류 없이 빈 결과가
와서, 안 보고 지나가는 줄도 모른다.** 로컬 프록시가 그것을 비켜가고(`posco/pgpt-proxy` · 판 `17.6`
이상), 옛 판을 든 기계는 아래 절차를 그대로 밟아도 한 장도 못 본다. 판은 `/health` 가 댄다.
까닭과 재는 법은 `posco/ENV-posco.md` 의 그림 ⚠ 절이 든다.

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 100 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

⚠ **리눅스 컨테이너에는 이 도구들이 빠져 있을 수 있다.** 넷 다 대체가 서 있다.

| 없는 것 | 증상 | 대신 |
|---|---|---|
| `libreoffice-impress` | `soffice` 는 도는데 **`Error: source file could not be loaded`** — 덱이 멀쩡해도 이 말이 난다. 파일을 의심하게 만드는 자리다 | `apt-get update && apt-get install -y libreoffice-impress` (인덱스가 낡으면 `update` 가 먼저다) |
| `pdftoppm` | `command not found` | `pip install pymupdf` 뒤 `pymupdf.open(pdf)[i].get_pixmap(dpi=100).save(...)` |
| `markitdown` · `python-pptx` | `ModuleNotFoundError` | 글자만 뽑는 자리는 표준 라이브러리로 족하다 — `zipfile` 로 `ppt/slides/slideN.xml` 을 열어 `<a:t>` 를 모은다 |
| `defusedxml` · `lxml` | `validate.py` 가 임포트에서 죽는다 | `pip install defusedxml lxml` |

⚠ **글꼴이 없으면 넘침 판정이 한쪽으로 기운다.** 맑은 고딕이 없는 자리는 대체 글꼴이 더 넓게
잡혀 — **「안 넘쳤다」는 믿어도 되고 「넘쳤다」는 거짓 경보일 수 있다.** 그 판정을 근거로 글을
줄이기 전에 실물에서 한 번 본다.

**Pass the absolute paths printed above directly to the view tool.** The `rm` clears stale images from prior runs. `pdftoppm` zero-pads based on page count: `slide-1.jpg` for decks under 10 pages, `slide-01.jpg` for 10-99, `slide-001.jpg` for 100+.

**After fixes, rerun all four commands above** — the PDF must be regenerated from the edited `.pptx` before `pdftoppm` can reflect your changes.

### ⚠ DRM 환경에서의 육안 QA 우회 기법 (화면 캡처 방식)

사내 Fasoo DRM 환경에서는 백그라운드 프로세스가 생성한 이미지 파일이나 PDF 변환본이 암호화되거나 내보내기(`Slide.Export`)가 차단되어, 위의 일반 변환 파이프라인(`soffice`, `pdftoppm`)이 동작하지 않는다.

**검증된 우회 해법**:
파워포인트를 창 모드(`WithWindow = $true`) 또는 슬라이드쇼로 띄우고, `.NET`의 데스크톱 화면 캡처(`System.Drawing.Graphics.CopyFromScreen`)를 수행하면 파수의 디스크 파일 암호화 간섭 없이 깨끗한 슬라이드 이미지를 얻을 수 있다.

```powershell
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open((Resolve-Path "deck.pptx").Path, $true, $false, $true)
$pres.SlideShowSettings.Run()
Start-Sleep -Milliseconds 800

# 화면 캡처
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bmp.Save("$PWD\qa_slide.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $pres.SlideShowWindow.View.Exit(); $pres.Close(); $ppt.Quit()
```

생성된 `qa_slide.png`는 `view` 도구로 직접 열어 시각적 품질(색 대비, 타이포 인상, 여백 균형)을 육안으로 검증한다.

**한 줄로 쓰려면** — 위 절차(전경 잠금 해제 · 복구 창 제거 · 프로세스 정리 · 압축)를 그대로 담은 스크립트가 있다:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/capture_slides.ps1 -Path deck.pptx -Slides "1,8"
```

**검증된 호출 패턴** — 순서가 곧 함정 회피다. 손으로 짤 때도 이 차례를 지킨다.

1. `Resiliency\DocumentRecovery` 삭제 → 복구 창이 슬라이드쇼를 가로채지 못하게
2. `Presentations.Open($full, $true, $false, $true)` — 4번째 인수 `WithWindow=$true`
3. `SlideShowSettings.Run()` 후 **`SlideShowWindow` 가 설 때까지 폴링** (바로 물으면 `null`)
4. `View.GotoSlide($n)` → `SendKeys('%')` → `AppActivate($pid)` **두 번** → 1.2초 대기
5. `Graphics.CopyFromScreen()` 으로 화면 버퍼 캡처 → PNG 저장
6. 픽셀 한두 개를 찍어 **슬라이드가 맞는지 확인** 후 열람 (엉뚱한 창이 찍혀도 파일은 생긴다)
7. 이 스크립트가 띄운 PowerPoint 프로세스만 종료 (남으면 덱 파일이 잠겨 다음 빌드가 죽는다)

⚠ **자주 걸리는 함정** — `Slide.Export()` 는 DRM 이 암호화해 열리지 않는다(첫 바이트 `DRMONE`) · `SlideShowWindow.HWND` 는 `null` 이 오므로 창 핸들 대신 프로세스 Id 로 활성화한다 · `powershell -File` 로 `-Slides 1,8` 을 넘기면 `18` 로 붙는다(문자열로 받아 쪼갠다). 전체 실패 계보와 원인은 `references/executive-layouts.md` 의 [QA] 절이 든다.

⚠ **고치는 동안은 `audit_layout.ps1`(배치 실측)만 돌리고, 캡처는 마무리에 핵심 한두 장만 한다** — 값이 어디서 매겨지나는 위 [Converting to Images](#converting-to-images) 가 든다. 배치 검사는 통과하는데 눈으로만 잡히는 결함(한글 낱말이 줄 끝에서 반으로 갈리는 자리 등)이 있으므로, 마지막 한 번은 반드시 본다.

## Dependencies

`pptxgenjs` (npm, preinstalled — install only if `require('pptxgenjs')` fails) · `markitdown[pptx]`, `Pillow`, `defusedxml`, `lxml` (pip — text dump, thumbnail, clean, validate) · LibreOffice (`soffice`, auto-configured for sandboxed environments via `scripts/office/soffice.py`) · `pdftoppm` (Poppler)
