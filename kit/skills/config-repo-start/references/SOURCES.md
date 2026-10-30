# 출처

| 원문 | 어디 | 받은 판 | 라이선스 | 가져온 것 |
|---|---|---|---|---|
| `chezmoi-concepts.md` | twpayne/chezmoi `assets/chezmoi.io/docs/reference/concepts.md` | master `cdbbdc0`(2026-10-30) | MIT(`chezmoi-LICENSE`) | 홈(destination)과 원본(source state)을 가르고, 원하는 상태는 원본이 든다 |
| `chezmoi-command-overview.md` | 같은 저장소 `assets/chezmoi.io/docs/user-guide/command-overview.md` | 같음 | 같음 | 홈의 파일을 원본으로 들이기(`add`) · 적용하면 무엇이 바뀌나 미리 보기(`status` · `diff`) · 적용(`apply`) · 저장소 받기(`init`) · 커밋과 밀기는 보통의 git |

## 표준과 갈린 자리

- **원본이 둘이다** — chezmoi 는 원본 하나를 홈에 적용한다. 우리는 제작자 층(짐 → `~/.paisetup/standard/`)과 개인 층(설정
  저장소 → `~/.paisetup/personal/`)이 있고 항목마다 개인 층이 이긴다(결정 0112). 그래서 「들이기」가 둘로 갈린다 — 더하기는
  더하는 항목(결정 0187)에, 바꾸기 · 빼기는 항목째 가져오기에
- **적용은 우리 손이 한다** — `apply` 자리는 설정 저장소의 `deploy.ps1` 과 설치 · 세션 훅이 부르는 놓는 손이고, 미리 보기는 그
  손의 `--dry-run` · `check` 다
- **원격 고르기를 사람에게 묻는다** — chezmoi 는 GitHub 을 기본으로 둔다. 우리는 비영속 VDI 와 계정 없이 쓰려는 영속 PC 를 함께
  받아 둘을 내놓고 대가를 말한다(이슈 220)

## 본 후보와 탈락

- 웹 검색 한 번(2026-10-30 · 「SKILL.md · dotfiles · chezmoi」)에서 「설정 저장소를 세우고 홈의 고침을 옮기는」 스킬은 안
  나왔다. 개인 dotfiles 저장소가 chezmoi 로 `~/.claude/CLAUDE.md` · 스킬을 다루는 예만 나왔고(rednafi.com/misc/chezmoi ·
  github.com/mizchi/chezmoi-dotfiles — 「한 파일은 한 층만 든다」), 개인 저장소라 표준으로 안 센다. 등록소(skills.sh 따위)는 안 뒤졌다
