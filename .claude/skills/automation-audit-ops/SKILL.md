---
name: automation-audit-ops
description: ECC의 근거 우선 자동화 인벤토리 및 중복 감사 워크플로입니다. 무엇이 살아 있고, 무엇이 깨졌고, 무엇이 중복되며, 무엇이 비어 있는지 고치기 전에 먼저 알고 싶을 때 사용합니다.
origin: ECC
---

# Automation Audit Ops

사용자가 어떤 자동화가 실제로 살아 있는지, 어떤 작업이 깨졌는지, 어디에 중복이 있는지, 어떤 도구와 커넥터가 지금 실제 가치를 내고 있는지 묻는다면 이 스킬을 사용합니다.

이것은 감사 우선 운영자 스킬입니다. 무엇이든 다시 쓰기 전에 근거 기반 인벤토리와 keep / merge / cut / fix-next 권고 세트를 만드는 것이 목적입니다.

## 스킬 스택

관련 시 다음 ECC 네이티브 스킬을 조합합니다.

- `workspace-surface-audit`
- `knowledge-ops`
- `github-ops`
- `ecc-tools-cost-audit`
- `research-ops`
- `verification-loop`

## 사용 시점

- 사용자가 "내 자동화가 뭐가 있지", "뭐가 살아 있지", "뭐가 깨졌지", "뭐가 겹치지"라고 물을 때
- 작업이 cron, GitHub Actions, local hooks, MCP servers, connectors, wrappers, app integrations를 가로지를 때
- 다른 에이전트 시스템에서 이식된 것과 ECC 내부에서 다시 만들어야 할 것을 구분하고 싶을 때
- 같은 일을 하는 여러 경로가 쌓여서 하나의 canonical lane으로 정리하고 싶을 때

## 가드레일

- 사용자가 수정까지 명시하지 않는 한 read-only로 시작합니다
- 다음을 분리합니다
  - configured
  - authenticated
  - recently verified
  - stale or broken
  - missing entirely
- skill이나 config가 참조한다는 이유만으로 live라고 주장하지 않습니다
- evidence table이 생기기 전에는 겹치는 표면을 병합하거나 삭제하지 않습니다

## 워크플로

### 1. 실제 표면 인벤토리

현재 live 표면을 먼저 읽습니다.

- repo hooks and local hook scripts
- GitHub Actions and scheduled workflows
- MCP configs and enabled servers
- connector- or app-backed integrations
- wrapper scripts and repo-specific automation entrypoints

다음 표면별로 묶습니다.

- local runtime
- repo CI / automation
- connected external systems
- messaging / notifications
- billing / customer operations
- research / monitoring

### 2. 각 항목 live state 분류

각 자동화에 대해 다음을 표시합니다.

- configured
- authenticated
- recently verified
- stale or broken
- missing

그리고 문제 유형도 분류합니다.

- active breakage
- auth outage
- stale status
- overlap or redundancy
- missing capability

### 3. 증명 경로 추적

중요한 주장은 다음 같은 구체적 소스로 뒷받침합니다.

- file path
- workflow run
- hook log
- config entry
- recent command output
- exact failure signature

현재 상태가 모호하면 감사가 완결된 척하지 말고 그대로 말합니다.

### 4. keep / merge / cut / fix-next로 마무리

겹치거나 의심스러운 표면마다 하나의 판정을 반환합니다.

- keep
- merge
- cut
- fix next

가치는 역사적 경로를 모두 보존하는 데 있지 않고, 소음 많은 자동화를 하나의 canonical ECC lane으로 접는 데 있습니다.

## 출력 형식

```text
CURRENT SURFACE
- automation
- source
- live state
- proof

FINDINGS
- active breakage
- overlap
- stale status
- missing capability

RECOMMENDATION
- keep
- merge
- cut
- fix next

NEXT ECC MOVE
- exact skill / hook / workflow / app lane to strengthen
```

## 함정

- live inventory를 읽을 수 있는데 기억으로 답하지 않습니다
- "config에 있음"을 "동작 중"으로 간주하지 않습니다
- 깨진 고신호 경로를 말하기 전에 저가치 중복부터 손대지 않습니다
- 사용자가 inventory를 먼저 원했는데 저장소 재작성으로 넓히지 않습니다

## 검증

- 중요한 주장은 live proof path를 인용한다
- 각 자동화는 명확한 live-state 카테고리를 가진다
- 최종 권고는 keep / merge / cut / fix-next를 구분한다
