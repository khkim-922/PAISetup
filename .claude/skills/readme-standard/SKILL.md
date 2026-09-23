---
name: readme-standard
description: README를 쓰거나 고칠 때 부른다. "리드미 써줘"·"README 정리해줘"·"저장소 첫 화면 손보자"·"README가 실물이랑 안 맞아"·"새 저장소 열었어". 저장소 소개 문서 이야기면 낱말이 달라도 부른다.
---

# README 작성

**절 골격 — 이 순서대로, ★ 는 명세 필수다**:

> Title★ → Banner → Badges → Short Description★(120자 미만) → Long Description →
> Table of Contents★(100줄 미만이면 선택) → Security → Background → Install★ → Usage★ →
> Extra Sections → API → Maintainer(s) → Thanks → Contributing★ → License★(마지막)
>
> Install·Usage 는 명세가 **문서 저장소**에 한해 선택으로 풀어 둔다.

이 파일의 나머지는 셋을 든다 — **어느 선택 절을 켜나** · 표준을 **덮어쓰는 자리** · 표준에 **없어서 더하는 것**.

- **근거 원칙** — 규범 **[Single Source · Point or Derive]** · **[Diátaxis Axis]**
- 명세에는 린터와 제너레이터가 딸려 있다.

## 0. 저장소 성격을 먼저 가른다

아래 프로파일과 덮어쓰기가 **이 판정에서 갈린다.** 먼저 정하지 않으면 나머지를 정할 수 없다.

| 성격 | 달라지는 것 |
|---|---|
| **실행되는 것** (앱·스크립트·서비스) | Install·Usage 가 살아난다 |
| **보관하는 것** (문서·자산·프롬프트) | Install 을 뺀다 — 명세가 *문서 저장소*로 이미 열어둔 자리다 |
| **남이 쓰는 것** (공개·사내 배포) | **아래 덮어쓰기 둘이 풀린다** — Contributing·License 를 되살리고 Maintainers 를 켠다 |

## 선택 절을 켜고 끄는 프로파일

명세가 **선택으로 둔 절**만 여기서 정한다. 필수 절(Title·Short Description·Table of Contents·Install·Usage)은 그대로 쓰므로 적을 것이 없다.

| 명세의 선택 절 | 우리 | 왜 |
|---|---|---|
| Banner · Long Description · Thanks | 뺀다 | |
| Badges | 대개 뺀다 | 사내 저장소 |
| Security | **키·자격증명을 다루면 켠다** | |
| Background | **늘 켠다** | 사내 도구는 *존재 이유*가 사용법보다 먼저 궁금하다. *무엇을 하는가*는 Short Description 이 이미 했으니 여기는 **무엇이 불편해서 이게 생겼나**다 |
| Extra Sections | 필요하면 켠다 | 절 이름은 그 절의 내용으로 단다 |
| API · Maintainers | 뺀다 | 라이브러리가 아니고, 혼자다 |

## 표준을 덮어쓰는 자리 둘

| 명세 | 우리 | 왜 |
|---|---|---|
| **Contributing 은 필수** | 뺀다 | 혼자다 — 받을 기여가 없다 |
| **License 는 필수이고 마지막 절** | **공개 저장소만** | 비공개 개인 저장소 |

⚠ 이 둘은 **선택 절을 안 쓴 게 아니라 명세가 필수로 둔 것을 뺀 것이다.**
저장소가 공개되거나 사람이 늘면 **가장 먼저 되살릴 자리**이므로, 뺄 때는 *"지금 없다"*이지 *"영영 없다"*가 아니다(위 0의 셋째 줄).
원문의 해당 절에 `<!-- OVERRIDE … -->` 표식을 박아 뒀다.

## 표준에 없어서 더하는 것 셋

### 1. 낡을 것을 넣지 않는다

명세는 *무엇을 담나*를 들지만 **무엇이 먼저 썩나**는 안 든다 — 룰 doc-discipline(개수·경로·
폴더 트리)과 규범 [Layer Triage](절차는 스킬) 그대로. README 가 대신 드는 것은 **무엇의
진본이 어디인가**와 진행 상태의 좌표(작업큐 · `roadmap-doc`)다.

### 2. 돌려보지 않은 명령을 넣지 않는다

명세는 Usage 에 *"흔한 사용을 보여주는 코드블록"*을 요구하지만 **그게 실제로 도는지**는 안 묻는다.
설명하지 말고 **복사해서 돌아가는 것**을 넣는다.

### 3. 한 줄이 안 나오면 정체가 안 잡힌 것이다

명세는 Short Description 을 120자 미만으로 제한한다. 우리가 더하는 것은 **그 한계가 뜻하는 바**다 —
한 줄이 안 나오면 **README 를 더 쓰지 말고 그것부터 세운다.** 넘치면 두 가지가 섞여 있다.

## 갈리는 자리

| 갈리는 자리 | 어느 쪽 |
|---|---|
| 다른 저장소를 베낄까 | `awesome-readme` 류는 예시 모음이지 명세가 아니다. 베낄 것은 **구조**다 |
| 링크가 살아 있나 | 명세가 *"깨진 링크가 없어야 한다"*고 요구한다. 재는 것은 `doc-coordinate-audit` 스킬 |

---

## 참조 — 표준 원문

`references/standard-readme-spec.md` 는 standard-readme 명세 **영어 원문 그대로**다.
전역 요구(파일명·다국어·절 순서·제목·깨진 링크·코드 린트)와 절 열여섯의 상태·요구·제안을 든다.

원본 `RichardLitt/standard-readme` 저장소 `spec.md` · MIT · 받은 시점 2026-08

손댄 것은 하나뿐이다 — 덮어쓰는 두 절에 `<!-- OVERRIDE -->` 한 줄씩. 그 줄은 대조하는 자가 거른다 — 저장소 뿌리에서:

```bash
sh scripts/check-upstream.sh https://raw.githubusercontent.com/RichardLitt/standard-readme/main/spec.md .claude/skills/readme-standard/references/standard-readme-spec.md
```
