# 사내 코딩 기준 씨앗

**회사가 마련한 FastAPI 코딩 기준 한 벌이다.** 우리가 쓴 글이 아니라 **회사가 쓴 글**이고,
진본은 사내 GitLab 에 있다. 이 폴더는 그 진본에서 뽑은 것이다.

- **진본** — 사내 GitLab 의 `vibecoding-template`. 주소는 뽑는 자
  `scripts/pull-vibecoding.sh` 의 `REMOTE` 한 줄이 든다(여기 또 적으면 주소가 옮겨진 날
  한쪽이 낡는다).
- **뽑는 자** — `scripts/pull-vibecoding.sh`. 사내망에서만 돈다.
- **어느 판인가** — 곁의 `.version` 한 줄(`<짧은 해시> <원본 커밋 날짜>`).

## 이 폴더를 손으로 고치지 않는다

**여기 든 것은 전부 생성물이다.** 다음 뽑기가 폴더를 비우고 다시 채우므로, 손으로 고친 것은
그때 사라진다. 고칠 일이 있으면 두 갈래다.

| 무엇을 고치려는가 | 어디서 |
|---|---|
| 회사 기준 자체가 틀렸다 | 회사에 말한다 — 우리가 그 저장소의 주인이 아니다 |
| 우리 세션에 어떻게 걸리나 | 굽는 자 `scripts/pull-vibecoding.sh` — 룰은 그 자가 굽는 생성물이다 |

## 어떻게 우리 세션에 걸리나

**본문은 여기 살고, 걸리는 자는 룰층에 있다.** 둘을 가른 까닭이 있다 — 회사 문서는 Continue
확장의 문법(`alwaysApply` · `globs`)으로 쓰여 있어서 Claude Code 가 그대로는 안 읽는다.
뽑는 자가 그 문법만 우리 룰층의 `paths` 로 바꿔 `continue-rules/` 의 규약마다 룰 한 장을
**굽는다** — 본문은 회사 원본 그대로다. 설치본에서는 `~/.claude/rules/futurem-*.md` 에 선다
(진본 자리는 claude-config 의 `.claude/rules.global/`).

| 룰 | 원본 규약 | 언제 걸리나 |
|---|---|---|
| `futurem-vibe-coding-standards.md` | `vibe-coding-standards.md` | `main.py` · 레이어 폴더 넷 · `.futurem-prompts/` 를 만질 때 |
| `futurem-routers.md` | `futurem-routers.md` | `routers/` 를 만질 때 |
| `futurem-services.md` | `futurem-services.md` | `services/` 를 만질 때 |
| `futurem-repositories.md` | `futurem-repositories.md` | `repositories/` 를 만질 때 |
| `futurem-adapters.md` | `futurem-adapters.md` | `adapters/` 를 만질 때 |

**손으로 옮기지 않고 굽는다.** 손으로 옮긴 룰은 회사가 원본을 고친 날 씨앗만 새 판이 되고 룰은
옛 판에 남는데, 파일은 멀쩡히 읽히므로 그 낡음은 조용하다. 사람이 정한 것은 공통 규약
(`alwaysApply: true`)을 어느 경로로 좁히나 하나뿐이고, 그 값은 뽑는 자가 든다.

⚠ **걸리는 경로는 흔한 이름이다** — `main.py` · `services/` 는 사내 앱이 아닌 프로젝트에도 있다.
그래서 구운 룰은 머리에 「사내 앱이 아니면 무시한다」와 그 표지를 같이 든다.

⚠ **파일이 아직 없는 자리는 룰이 못 든다.** 새 앱을 처음 세우는 순간에는 걸릴 파일이 없어서,
그 자리는 이 문서와 `posco/README.md` 의 좌표가 맡는다 — 사내 앱을 시작할 때 여기를 먼저 읽는다.

## 새 사내 앱을 시작할 때

1. 이 폴더의 `README.md`(회사가 쓴 것)와 `continue-rules/vibe-coding-standards.md` 를 읽는다 —
   고정된 기술 스택과 금지 목록이 거기 있다.
2. 구조를 세운다 — `router → service → repository` 와 `adapters/`. 그 폴더가 생기는 순간부터
   룰 다섯이 자동으로 걸린다.
3. 하려는 일에 맞는 상세 가이드를 `docs/guides/` 에서 고른다. 좌표 표는
   `continue-rules/vibe-coding-standards.md` 끝(「상세 가이드 참조」)에 있다.

⚠ **설치본에는 SSO 참고 문서 둘이 없다** — `docs/references/futurem-sso-guide.md` ·
`futurem-sso-auth-guide-ko.md`. 사내 SSO 서버 주소가 본문에 들어 공개 배포본에 안 싣는다(회사가
정리한 `docs/guides/futurem-sso.md` 는 같은 주소를 가려 적는다). SSO 를 붙일 때는 그 가이드를
따르고, 실제 주소는 사내 GitLab 원문이나 SSO 담당자에게서 받아 환경변수에 넣는다.

⚠ **회사 zip 을 따로 받아 쓰지 않는다.** 바탕화면에 풀린 폴더는 설치 매체라 지워지고, 그 판이
어느 판인지 말하는 자가 없다. 이 폴더는 `.version` 으로 판을 말하고 뽑는 자로 갱신된다.

## Continue 도 함께 쓴다면

**원본의 설치기(`install.bat` · `install.ps1`)는 안 뽑는다.** 그 둘은 프로젝트 폴더에
`.continue/rules/` 를 까는 자라 VS Code 의 Continue 확장을 쓰는 자리에서만 뜻이 있고, Claude
Code 세션에는 아무 영향이 없다(우리 쪽은 위의 룰 다섯이 맡는다). 이 씨앗이 들이는 것은
**기준 본문**이다.

그리고 담을 수도 없다 — 회사 `install.ps1` 은 한글이 가득한데 BOM 이 없어서, 담긴 판에 BOM 을
요구하는 우리 규율에 걸린다(회사는 그것을 알고 `install.bat` 이 실행 시점에 붙이는 방식으로
다룬다). 우리가 붙이면 회사 파일을 고치는 것이고 다음 뽑기에 그 손질이 사라진다.

Continue 로도 쓰려면 **원본을 직접 받는다** — 그쪽이 그 도구의 진본이다.

⚠ 원본의 `.continue/` 폴더도 안 뽑는다 — 그것은 원본이 `continue-rules/` 에서 구운 사본이라,
사본을 사본으로 받으면 어느 쪽이 진본인지 여기서 안 갈린다.
