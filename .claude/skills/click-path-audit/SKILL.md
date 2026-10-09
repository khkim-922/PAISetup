---
name: click-path-audit
description: "사용자에게 보이는 모든 버튼/터치포인트를 상태가 바뀌는 전 과정에 걸쳐 추적해, 함수 하나하나는 동작하는데 서로를 상쇄하거나, 최종 상태를 틀리게 만들거나, UI를 어긋난 상태로 남기는 버그를 찾습니다. 체계적 디버깅으로는 버그가 안 나오는데 사용자는 버튼이 고장 났다고 할 때, 또는 공유 상태 저장소를 건드린 큰 리팩터링 뒤에 사용합니다."
origin: community
---

# /click-path-audit — 동작 흐름 감사

코드를 정적으로 읽어서는 놓치는 버그를 찾습니다. 상태끼리 얽혀 생기는 부작용, 차례로 부른 호출 사이의 레이스 컨디션, 서로가 한 일을 소리 없이 되돌리는 핸들러 같은 것들입니다.

## 이 스킬이 해결하는 문제

전통적인 디버깅은 다음을 확인합니다.
- 함수가 존재하는가? (연결 누락)
- 크래시가 나는가? (런타임 오류)
- 올바른 타입을 반환하는가? (데이터 흐름)

하지만 다음은 확인하지 **않습니다**.
- **최종 UI 상태가 버튼 라벨이 약속하는 바와 맞는가?**
- **함수 A가 방금 한 일을 함수 B가 소리 없이 되돌리는가?**
- **공유 상태(Zustand/Redux/context)에 의도한 동작을 상쇄하는 부작용이 있는가?**

실제 사례: "New Email" 버튼이 `setComposeMode(true)`를 호출한 다음 `selectThread(null)`를 호출했습니다. 둘 다 따로 놓고 보면 정상 동작했지만, `selectThread`에는 `composeMode: false`로 초기화하는 부작용이 있었습니다. 버튼은 아무 일도 하지 않았습니다. 체계적 디버깅으로 버그 54개를 찾았지만 이 버그는 놓쳤습니다.

---

## 동작 방식

대상 영역에 있는 **모든** 인터랙티브 터치포인트마다 다음을 합니다.

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

터치포인트를 하나라도 감사하기 전에, 모든 상태 저장소 액션의 부작용 맵을 만듭니다.

```
범위 안의 각 Zustand store / React context에 대해:
  각 action/setter마다:
    - 어떤 필드를 set 하는가?
    - 다른 필드를 SIDE EFFECT로 RESET 하는가?
    - 문서화: actionName → {sets: [...], resets: [...]}
```

이 맵이 가장 중요한 참고 자료입니다. "New Email" 버그는 `selectThread`가 `composeMode`를 초기화한다는 사실을 모르면 보이지 않았습니다.

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

대상 영역의 버튼/토글/폼 제출마다:

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

**다음 버그 패턴을 하나씩 점검합니다.**

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

#### 패턴 3: 낡은 클로저(Stale Closure)
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

#### 패턴 5: 조건부 죽은 경로(Conditional Dead Path)
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

찾은 버그마다 다음 형식으로 보고합니다.

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

이 감사는 비용이 큽니다. 범위를 알맞게 잡습니다.

- **앱 전체 감사:** 출시할 때나 큰 리팩터링 뒤에 씁니다. 페이지마다 에이전트를 병렬로 띄웁니다.
- **단일 페이지 감사:** 새 페이지를 만든 뒤, 또는 사용자가 고장 난 버튼을 신고한 뒤에 씁니다.
- **스토어 중심 감사:** Zustand store를 고친 뒤에 씁니다. 바뀐 액션을 쓰는 곳을 모두 감사합니다.

### 앱 전체 감사용 권장 에이전트 분할

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

Agent 1이 반드시 먼저 끝나야 합니다. 그 출력이 다른 모든 에이전트의 입력입니다.

---

## 사용 시점

- 체계적 디버깅은 "버그 없음"이라고 하는데 사용자는 UI가 고장 났다고 할 때
- Zustand store 액션을 하나라도 고친 뒤 (호출부를 모두 확인)
- 공유 상태를 건드린 리팩터링을 한 뒤
- 릴리스 전, 핵심 사용자 흐름을 점검할 때
- 버튼이 "아무것도 안 한다"고 할 때 — 바로 이럴 때 쓰는 도구입니다

## 사용하지 말아야 할 때

- API 수준 버그(응답 형태가 틀림, 엔드포인트 없음) — `systematic-debugging`을 씁니다
- 스타일/레이아웃 문제 — 눈으로 점검합니다
- 성능 문제 — 프로파일링 도구를 씁니다

---

## 다른 스킬과의 연계

- `/superpowers:systematic-debugging` **뒤에** 실행합니다 (그쪽이 나머지 54가지 유형의 버그를 찾습니다)
- `/superpowers:verification-before-completion` **앞에** 실행합니다 (그쪽이 수정이 실제로 먹히는지 검증합니다)
- `/superpowers:test-driven-development`로 이어집니다 — 여기서 찾은 버그마다 테스트를 붙여야 합니다

---

## 예시: 이 스킬의 출발점이 된 버그

**ThreadList.tsx의 "New Email" 버튼:**
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
- 버튼에 onClick 핸들러가 있음 (죽은 버튼 아님)
- 두 함수 모두 존재함 (연결 누락 아님)
- 어느 함수도 크래시하지 않음 (런타임 오류 아님)
- 데이터 타입이 맞음 (타입 불일치 아님)

**Click-path audit가 잡아내는 이유**
- 1단계에서 `selectThread`가 `composeMode`를 초기화한다는 사실이 맵에 드러남
- 2단계에서 핸들러를 추적: 첫 호출은 true로 설정하고, 두 번째 호출이 false로 초기화함
- 판정: Sequential Undo — 최종 상태가 버튼의 의도와 어긋남
