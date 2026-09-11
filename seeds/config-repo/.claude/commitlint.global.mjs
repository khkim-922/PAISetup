// 커밋 메시지 형식 규칙 — **우리 제목 문체가 낳는 오탐.** 어느 저장소에서도 같다.
//
// 진본은 claude-config/.claude/commitlint.global.mjs 다. 각 저장소의 것은 deploy.ps1 이
// 뿌린 배포본이다 — 배포본을 고치면 다음 배포에 덮인다.
//
// 실제 강제는 커밋 게이트(.githooks/gates.d/commit-format.sh)가 부른다. 저장소가 제
// 규칙을 더하려면 뿌리에 `commitlint.config.mjs` 를 두면 되고, 조각이 그쪽을 먼저 본다.
//
// 낱말 목록(type-enum)은 여기 안 적는다 — `@commitlint/config-conventional` 이 명세대로
// 든다(규범 [Conventional Commits]). 우리가 쓴 적 없다고 빼지 않는다: 이력에 맞춰 좁히면
// 앞으로 쓸 멀쩡한 커밋을 막는다.
//
// ⚠ 확장자가 `.mjs` 인 까닭 — commitlint 21 은 ESM 이고, 저장소 `package.json` 에 `type`
//   이 없으면 `.js` 는 CJS 로 읽힌다. `.mjs` 는 그 모호함이 없다.
// ⚠ `extends` 가 `@commitlint/config-conventional` 을 **저장소 기준으로** 푼다. 전역
//   설치는 저장소 밖이라, 도구 선언의 `wiring = node-link` 가 그 자리를 이어야 선다 —
//   그 짝이 빠지면 commitlint 는 실행되고 설정을 못 읽어 **제 규칙 없이 통과한다.**

export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // subject-case — 한국어 제목이 영어 고유명사(README · LEAN …)로 시작하면 규칙이
    //   그것을 sentence-case 위반으로 본다. **규칙이 오작동한 게 아니라 제대로 작동했는데
    //   우리한테 쓸모가 없는** 자리다 — 우리 제목 문체가 그렇게 자주 시작한다.
    //   형제 저장소가 전체 이력에 돌려 세운 판정이다: 위반 42건이 전부 영문자로 시작하는
    //   제목이었고, 한글로 시작하는 제목은 한 건도 안 걸렸다.
    //   ⚠ 상류에 비라틴 문자 회귀 버그가 따로 있지만(conventional-changelog/commitlint#4620,
    //     20.4.0 이후 키릴 소문자 제목 거부) 그 42건은 그 버그가 아니다. 고쳐져도 안 바뀐다.
    'subject-case': [0],
  },
};
