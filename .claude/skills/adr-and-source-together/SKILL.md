---
name: adr-and-source-together
description: 결정을 기록할 때 부른다. "ADR 써줘"·"결정 기록 남기자"·"이렇게 가기로 하자"·"이 결정 뒤집자"·"왜 이렇게 했는지 남겨두자". 대화에서 판정이 서면 파일을 안 만들어도 부른다.
---

# 결정 기록과 진본을 함께 옮긴다

**문서 골격 — MADR, 이 순서대로**:

> 머리말 — `status`(`proposed | rejected | accepted | deprecated | superseded by ADR-NNNN`) · `date`
> `# 제목(문제와 해법이 보이게)` → Context and Problem Statement(두세 문장, 물음 꼴 권장) →
> Decision Drivers → Considered Options → Decision Outcome(*Chosen option: …, because …*) →
> Consequences(Good/Bad 목록) → Confirmation → Pros and Cons of the Options → More Information

이 파일의 나머지는 셋을 든다 — **어느 선택 요소를 쓰나** · 표준을 **덮어쓰는 자리** · 표준이 **아예 안 드는 것**.

⚠ **셋째가 이 스킬의 전부다.** MADR 은 결정 문서 *한 장*을 든다. 그 결정이 **틀리게 만든 자리**는 안 든다 —
결정 문서만 움직이면 다음 세션은 진본을 읽고 옛 상태로 일한다.

- **파일명·폴더** — `NNNN-title-with-dashes.md`, `decisions/` 아래.
  (MADR 규약이지만 번들한 것은 템플릿뿐이라 이 한 줄은 여기 둔다)
- **근거 원칙** — 전역 **[ADR One-File]** · **[Root Cause Fix]** · **[Single Source · Point or Derive]**

## MADR 선택 요소 — 무엇을 쓰나

템플릿이 선택으로 둔 것만 정한다. 나머지(문제 서술·선택지·결정 결과)는 그대로 쓴다.

| 선택 요소 | 우리 | 왜 |
|---|---|---|
| `decision-makers` · `consulted` · `informed` | **안 쓴다** | 혼자다 — 셋 다 같은 사람이라 칸만 남는다 |
| `status` · `date` | 쓴다 | 뒤집힘을 추적하는 유일한 칸이다 |
| Decision Drivers | 쓴다 | |
| Consequences | 쓴다 | |
| Pros and Cons of the Options | 필요하면 | Drivers·Consequences 와 겹친다. 선택지가 셋 이상일 때만 |
| More Information | 쓴다 — **좌표를 여기 단다** | 아래 *더하는 것* 4 |

## 표준을 덮어쓰는 자리 하나

| MADR | 우리 | 왜 |
|---|---|---|
| **Confirmation 은 선택** (*"많은 ADR에 들어 있다"* 고만 한다) | **필수** | **지켜졌는지 재는 법이 안 써지면 그 결정은 아직 안 선 것이다.** 재는 법 없는 판정은 다음에 그냥 안 지켜진다 |

⚠ 원문의 해당 절에 `<!-- OVERRIDE … -->` 표식을 박아 뒀다.

## 표준에 없어서 더하는 것 — 사슬

### 1. 쓰기 전에 사슬을 센다

*"이 결정이 지금 무엇을 틀리게 만드는가"*를 묻고 고칠 자리를 목록으로 만든다.

| 자리 | 무엇이 틀려지나 | 어떻게 찾나 |
|---|---|---|
| 결정 색인 | 새 결정이 목록에 없다 | 생성물이면 다시 돌린다(아래 2) |
| Reference 진본 | 설계도·규약이 옛 상태를 말한다 | 그 결정의 주제어로 진본을 훑는다 |
| 그 결정을 인용하던 곳 | 뒤집힌 결정을 근거로 든 문장이 남는다 | 옛 결정 번호·핵심 낱말로 저장소를 훑는다 |
| 딸린 산출물 | 결정이 만든 파일·예시가 낡는다 | 결정이 *"무엇을 만들라"*고 했으면 그 산출물 |

없으면 없다고 적고 넘어가되 **안 세고 넘어가지 않는다.**

### 2. 같은 커밋에서 그 목록을 전부 움직인다

커밋을 나누지 않는다. 나누면 하나가 남고, 남은 하나가 다음 세션을 잘못 출발시킨다.
결정이 여럿이면 **하나 쓰고 하나 반영한다.**

색인은 손으로 고치지 말고 **다시 생성한다** — 결정 파일들이 진본이고 색인은 파생물이다.
아직 생성물이 아니면 이번에 그렇게 만든다.

### 3. 닫기 전 확인한다

목록의 각 자리를 **열어서** 새 상태가 적혀 있는지 본다. 기억이 아니라 파일로 확인한다.

### 4. 좌표를 달고, 그때의 수치는 박는다

- **좌표** — 이 판정이 **진본 어디에 섰나**. 사실은 진본에 두고 결정 기록은 가리키기만 한다
- **수치** — 그때의 개수·상태는 박아 둔다(굳는 문서 — 규범 **[Docs-as-Code · State Only]** 의 예외)

## 갈리는 자리

| 갈리는 자리 | 어느 쪽 |
|---|---|
| 목록은 갱신했는데 설계도를 안 열었다 | 목록은 눈에 띄고 설계도는 길다. **설계도가 진본이다** |
| 진본만 고치고 결정 기록을 안 썼다 | 반대 방향의 같은 실패다 — *무엇*은 남고 *왜*가 사라진다 |

---

## 참조 — 표준 원문

`references/madr-template.md` 는 MADR 템플릿 **영어 원문 그대로**다.
골격은 위 머리에 인라인했다 — 원문의 실값은 **각 절을 무엇으로 채우나의 서술 지침**이다.

원본 `adr/madr` 저장소 `template/adr-template.md` · 받은 시점 2026-08

⚠ **번들한 것은 템플릿 한 장뿐이다.** 파일명 규약·폴더 규약은 MADR 문서 사이트 쪽에 있고 여기 없다 —
위 머리에 한 줄로 적어 둔 이유다.

손댄 것은 하나 — `### Confirmation` 에 `<!-- OVERRIDE -->` 한 줄. 그 줄만 걸러내면 상류와 대조된다.

```bash
curl -sL https://raw.githubusercontent.com/adr/madr/main/template/adr-template.md \
  | diff - <(grep -v '^<!-- OVERRIDE' references/madr-template.md)
```
