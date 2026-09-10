---
name: architecture-doc
description: 설계도(아키텍처 문서)를 쓰거나 고칠 때 부른다. "설계도 써줘"·"아키텍처 문서 만들자"·"설계도 정리해줘"·"구조 문서가 너무 길어"·"설계도 다시 그리자". 시스템 구조를 문서로 남기는 이야기면 낱말이 달라도 부른다.
---

# 설계도 작성

**절 골격 — arc42 열둘, 이 순서대로**:

> 1 Introduction and Goals → 2 Architecture Constraints → 3 Context and Scope →
> 4 Solution Strategy → 5 Building Block View → 6 Runtime View → 7 Deployment View →
> 8 Crosscutting Concepts → 9 Architecture Decisions → 10 Quality Requirements →
> 11 Risks and Technical Debt → 12 Glossary

이 파일의 나머지는 셋을 든다 — **어느 선택 절을 켜나** · 표준을 **덮어쓰는 자리** · 표준에 **없어서 더하는 것**.

- **근거 원칙** — 규범 **[Diátaxis Axis]** · **[Docs-as-Code · State Only]** · **[Single Source · Point or Derive]**

## 선택 절을 켜고 끄는 프로파일

arc42 가 **선택으로 둔 여섯 절**만 여기서 정한다. 필수 절(1~6)은 그대로 쓰므로 적을 것이 없다.

| arc42 절 | 우리 | 왜 |
|---|---|---|
| 7 Deployment View | **배포가 목표면 켠다** | 목표인데 뷰가 없으면 끝을 아무도 안 그린 것이다 |
| 8 Crosscutting Concepts | 켠다 | 여러 절에 흩어질 판단이 여기 모인다 |
| 9 Architecture Decisions | **좌표만** | 본문은 결정 기록 폴더가 든다 — 아래 덮어쓰기 |
| 10 Quality Requirements | 재는 기준이 있을 때만 | 못 재는 품질 목표는 문장만 남는다 |
| 11 Risks & Technical Debt | 켠다 | 아는 위험을 적는 자리 |
| 12 Glossary | **되물을 낱말이 다섯을 넘으면** 켠다 | 용어집은 사전이 아니라 한 낱말이 한 자리만 가리키게 하는 장치다(전역 **[Cognitive Anchoring]**) |

## 표준을 덮어쓰는 자리 셋

| arc42 | 우리 | 왜 |
|---|---|---|
| 9절을 **본문에 쓸지 블록 안에 쓸지 열어 둔다** | **닫는다** — 9절은 좌표만, 본문은 결정 기록 폴더(`adr-and-source-together`) | 둘 다 쓰면 한쪽만 갱신된다 |
| 템플릿이 **열두 절을 다 싣는다** | **안 쓰는 절은 지운다** | 빈 절은 채워야 할 빚으로 읽힌다 |
| 절을 **번호로 가리킨다** (*"Refer to section 4"*) | **이름으로 가리킨다** | `doc-coordinate-audit` §4 |

⚠ 첫째 자리에는 원문에 `// OVERRIDE …` 표식을 박아 뒀다. 나머지 둘은 특정 절이 아니라
**문서 전체에 걸리는 규칙**이라 표식을 못 박는다 — 여기서만 걸린다.

## 표준에 없어서 더하는 것 셋

### 1. 1장은 못 흔드는 층이다

arc42 는 1장을 맨 앞 필수로 두지만 **못 흔든다고까지는 안 한다.** 우리는 그렇게 표시한다 —
여기가 바뀌면 개정이 아니라 **다른 프로젝트**다.

*"무엇을 만드는가"* 한 문단이 안 나오면 설계도를 더 쓰지 말고 그것부터 세운다.
안 서면 나머지 절은 **무엇에 대한 설명인지 모르는 채로 자란다.**

### 2. 한눈에 안 들어오면 그것이 결함이다

안 읽히면 아무도 안 열고, 안 열면 낡는 줄도 모른다.
이유는 대개 셋이고 **눈으로는 안 보인다 — 세어야 보인다.**

| 증상 | 어떻게 재나 | 무엇을 뜻하나 |
|---|---|---|
| 목차가 없다 | 절 수를 센다 | 절이 늘 때마다 목차 생각이 안 났다 |
| 번호가 음수·0 으로 시작한다 | 첫 절의 번호를 본다 | 앞에 층을 끼워 넣은 흔적. **재편할 때다** — 번호가 *순서*와 *순서 밖* 둘을 뜻하고 있다 |
| 옛 축 서술이 섞여 있다 | *예전에는·옛·이관·뒤집·폐기* 를 세고 **어느 절에 몰렸는지** 본다 | 넷 이상 몰린 절이 여러 번 갈아엎힌 자리다. 거기부터 다시 쓴다 |

### 3. 좌표를 검사한다

설계도는 가장 많이 인용되는 문서라 **낡으면 가장 널리 틀린다.**
`doc-coordinate-audit` 스킬을 돌린다 — 특히 박힌 개수와 절 번호 인용.

## 갈리는 자리

| 갈리는 자리 | 어느 쪽 |
|---|---|
| 뷰를 무엇으로 그릴까 | arc42 가 열어 둔 자리다. **집 문체가 정한다** — 그 문서가 이미 무엇으로 나르고 있는지를 따른다 |
| 안 도는 것을 근거로 들까 | *"진본이다"·"강제한다"* 의 주어 자리에는 **살아 있는 것만** 온다 |
| 설계도가 코드와 어긋난다 | 실물이 이긴다 — 예외는 `doc-rederive-from-source` §2. 어긋남이 판단이면 결정 기록을 남긴다 |

---

## 참조 — 표준 원문

`references/arc42/` 는 arc42 템플릿 **영어 원문 그대로**, 상류와 같은 12개 파일이다.
각 파일이 그 절의 *담는 것 · 이유 · 형식*을 든다.

원본 `arc42/arc42-template` 저장소 `EN/adoc/` · **CC BY-SA 4.0** · 받은 시점 2026-08

손댄 것은 하나뿐이다 — `09_architecture_decisions.adoc` 에 `// OVERRIDE` 한 줄.
그 줄만 걸러내면 열둘 다 상류와 대조된다.

```bash
B=https://raw.githubusercontent.com/arc42/arc42-template/master/EN/adoc
for f in references/arc42/*.adoc; do
  curl -sL "$B/$(basename "$f")" | diff -q - <(grep -v '^// OVERRIDE' "$f") >/dev/null || echo "DIFF $f"
done
```
