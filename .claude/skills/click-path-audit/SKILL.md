---
name: click-path-audit
description: "사용자에게 보이는 버튼/터치포인트를 전체 상태 변화 순서로 추적해, 함수 각각은 동작하지만 서로 상쇄되거나 최종 상태가 잘못되거나 UI가 불일치 상태로 남는 버그를 찾습니다. 체계적 디버깅에서는 버그가 안 보이는데 사용자는 버튼이 고장났다고 할 때, 또는 공유 상태 저장소를 건드린 대형 리팩터링 뒤에 사용합니다."
origin: community
---

# /click-path-audit — 동작 흐름 감사

정적 코드 읽기로는 놓치는 버그를 찾습니다. 상태 상호작용 부작용, 순차 호출 간 레이스 컨디션, 서로를 조용히 되돌리는 핸들러를 추적합니다.

## 이 스킬이 해결하는 문제

전통적인 디버깅은 보통 다음을 확인합니다.
- 함수가 존재하는가? (배선 누락)
- 크래시가 나는가? (런타임 오류)
- 올바른 타입을 반환하는가? (데이터 흐름)

하지만 다음은 놓칩니다.
- **최종 UI 상태가 버튼 라벨이 약속하는 동작과 일치하는가?**
- **함수 B가 함수 A가 방금 만든 상태를 조용히 되돌리는가?**
- **공유 상태(Zustand/Redux/context)의 부작용이 의도한 동작을 상쇄하는가?**

실제 예시: `"New Email"` 버튼이 `setComposeMode(true)`를 호출한 뒤 `selectThread(null)`를 호출했습니다. 둘 다 개별적으로는 정상 동작했지만, `selectThread`에 `composeMode: false`로 초기화하는 부작용이 있었습니다. 결과적으로 버튼은 아무 일도 하지 않았습니다. 체계적 디버깅으로 54개 버그를 찾았지만, 이 버그는 놓쳤습니다.

---

## 동작 방식

대상 영역의 **모든 인터랙티브 터치포인트**에 대해 다음을 수행합니다.

```
1. 핸들러 식별 (onClick, onSubmit, onChange 등)
2. 핸들러 안의 모든 함수 호출을 순서대로 추적
3. 각 함수 호출마다:
   a. 어떤 상태를 READ 하는가?
   b. 어떤 상태를 WRITE 하는가?
   c. 공유 상태에 SIDE EFFECT가 있는가?
   d. 부작용으로 어떤 상태를 reset/clear 하는가?
4. 뒤쪽 호출이 앞쪽 호출의 상태 변화를 UNDO 하는지 확인
5. 최종 상태가 버튼 라벨이 암시하는 사용자 기대와 일치하는지 확인
6. 레이스 컨디션이 있는지 확인 (async 호출이 잘못된 순서로 resolve 되는가?)
```

---

## 실행 단계

### 1단계: 상태 저장소 매핑

어떤 터치포인트를 감사하기 전에, 모든 상태 저장소 액션의 side-effect 맵을 만듭니다.

```
범위 안의 각 Zustand store / React context에 대해:
  각 action/setter마다:
    - 어떤 필드를 set 하는가?
    - 다른 필드를 SIDE EFFECT로 RESET 하는가?
    - 문서화: actionName → {sets: [...], resets: [...]}
```

이게 핵심 레퍼런스입니다. `"New Email"` 버그도 `selectThread`가 `composeMode`를 reset한다는 사실을 먼저 알아야만 보였습니다.

**출력 형식:**
```
STORE: emailStore
  setComposeMode(bool) → sets: {composeMode}
  selectThread(thread|null) → sets: {selectedThread, selectedThreadId, messages, drafts, selectedDraft, summary} RESETS: {composeMode: false, composeData: null, redraftOpen: false}
  setDraftGenerating(bool) → sets: {draftGenerating}
  ...

DANGEROUS RESETS (actions that clear state they don't own):
  selectThread → resets composeMode (owned by setComposeMode)
  reset → resets everything
```

### 2단계: 각 터치포인트 감사

대상 영역의 각 버튼/토글/폼 submit에 대해:

```
TOUCHPOINT: [Button label] in [Component:line]
  HANDLER: onClick → {
    call 1: functionA() → sets {X: true}
    call 2: functionB() → sets {Y: null} RESETS {X: false}  ← CONFLICT
  }
  EXPECTED: User sees [description of what button label promises]
  ACTUAL: X is false because functionB reset it
  VERDICT: BUG — [description]
```

다음 버그 패턴을 각각 점검합니다.

#### 패턴 1: 순차적 상쇄(Sequential Undo)
```
handler() {
  setState_A(true)     // sets X = true
  setState_B(null)     // side effect: resets X = false
}
// Result: X is false. First call was pointless.
```

#### 패턴 2: 비동기 레이스(Async Race)
```
handler() {
  fetchA().then(() => setState({ loading: false }))
  fetchB().then(() => setState({ loading: true }))
}
// Result: final loading state depends on which resolves first
```

#### 패턴 3: Stale Closure
```
const [count, setCount] = useState(0)
const handler = useCallback(() => {
  setCount(count + 1)  // captures stale count
  setCount(count + 1)  // same stale count — increments by 1, not 2
}, [count])
```

#### 패턴 4: 상태 전이 누락(Missing State Transition)
```
// Button says "Save" but handler only validates, never actually saves
// Button says "Delete" but handler sets a flag without calling the API
// Button says "Send" but the API endpoint is removed/broken
```

#### 패턴 5: 조건 분기 사망 경로(Conditional Dead Path)
```
handler() {
  if (someState) {        // someState is ALWAYS false at this point
    doTheActualThing()    // never reached
  }
}
```

#### 패턴 6: useEffect 간섭(useEffect Interference)
```
// Button sets stateX = true
// A useEffect watches stateX and resets it to false
// User sees nothing happen
```

### 3단계: 보고

발견한 각 버그는 다음 형식으로 보고합니다.

```
CLICK-PATH-NNN: [severity: CRITICAL/HIGH/MEDIUM/LOW]
  Touchpoint: [Button label] in [file:line]
  Pattern: [Sequential Undo / Async Race / Stale Closure / Missing Transition / Dead Path / useEffect Interference]
  Handler: [function name or inline]
  Trace:
    1. [call] → sets {field: value}
    2. [call] → RESETS {field: value}  ← CONFLICT
  Expected: [what user expects]
  Actual: [what actually happens]
  Fix: [specific fix]
```

---

## 범위 제어

이 감사는 비용이 큽니다. 적절한 범위로 제한해야 합니다.

- **앱 전체 감사:** 출시 전이나 대규모 리팩터링 후 사용. 페이지별 병렬 에이전트가 적합합니다.
- **단일 페이지 감사:** 새 페이지를 만든 뒤나 사용자가 고장난 버튼을 신고했을 때
- **스토어 중심 감사:** Zustand store 액션을 수정한 뒤, 그 액션을 쓰는 모든 consumer를 점검할 때

### 전체 앱 기준 권장 에이전트 분할

```
Agent 1: 모든 상태 저장소 매핑 (Step 1) — 다른 에이전트가 공유하는 선행 컨텍스트
Agent 2: Dashboard (Tasks, Notes, Journal, Ideas)
Agent 3: Chat (DanteChatColumn, JustChatPage)
Agent 4: Emails (ThreadList, DraftArea, EmailsPage)
Agent 5: Projects (ProjectsPage, ProjectOverviewTab, NewProjectWizard)
Agent 6: CRM (all sub-tabs)
Agent 7: Profile, Settings, Vault, Notifications
Agent 8: Management Suite (all pages)
```

Agent 1이 먼저 끝나야 합니다. 그 출력이 나머지 에이전트의 입력입니다.

---

## 사용 시점

- 체계적 디버깅에서는 `"문제 없음"`인데 사용자는 UI가 고장났다고 할 때
- Zustand store 액션을 수정한 뒤 모든 호출부를 확인할 때
- 공유 상태를 건드린 리팩터링 이후
- 릴리스 전, 핵심 사용자 흐름에 대해
- 버튼이 `"아무것도 안 한다"`고 느껴질 때

## 사용하지 말아야 할 때

- API 레벨 버그(응답 형식 오류, 엔드포인트 누락) — `systematic-debugging`
- 스타일/레이아웃 문제 — 시각 점검
- 성능 문제 — 프로파일링 도구

---

## 다른 스킬과의 연계

- `/superpowers:systematic-debugging` 이후 실행 — 다른 54개 유형의 버그를 먼저 찾음
- `/superpowers:verification-before-completion` 이전 실행 — 수정이 실제로 작동하는지 검증하기 전
- `/superpowers:test-driven-development`로 연결 — 여기서 찾은 버그마다 테스트를 추가해야 함

---

## 예시: 이 스킬의 출발점이 된 버그

**ThreadList.tsx의 `"New Email"` 버튼:**
```
onClick={() => {
  useEmailStore.getState().setComposeMode(true)   // ✓ sets composeMode = true
  useEmailStore.getState().selectThread(null)      // ✗ RESETS composeMode = false
}}
```

스토어 정의:
```
selectThread: (thread) => set({
  selectedThread: thread,
  selectedThreadId: thread?.id ?? null,
  messages: [],
  drafts: [],
  selectedDraft: null,
  summary: null,
  composeMode: false,     // ← THIS silent reset killed the button
  composeData: null,
  redraftOpen: false,
})
```

**체계적 디버깅이 놓친 이유**
- 버튼에 onClick 핸들러가 있음 (dead 아님)
- 두 함수 모두 존재함 (wiring 누락 아님)
- 둘 다 크래시가 없음 (runtime error 아님)
- 데이터 타입이 맞음 (type mismatch 아님)

**Click-path audit가 잡는 이유**
- 1단계에서 `selectThread`가 `composeMode`를 reset한다는 사실을 매핑
- 2단계에서 핸들러를 추적: 첫 호출이 true로 set, 두 번째 호출이 false로 reset
- 결론: Sequential Undo — 최종 상태가 버튼 의도와 모순
