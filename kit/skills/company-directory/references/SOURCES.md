# 출처

이 스킬이 기대는 회사에서 잰 사실을 든다. 스킬은 `SKILL.md` 본문만으로 돈다 — 여기는 대조하고 고치기 전에 여는 자리다. 밖의 표준은
빌리지 않았다 — 사내 주소록은 사내 메일 서버(HCL Domino)의 웹메일 받는 사람 고름 창이 부르는 손이라 공개 스킬 · 명세가 없다.

## 회사에서 잰 꼴

아래 사실은 회사 PC 에서 실물에 대어 잰 것이고, **회사 PC 에서 다시 재기 전에는 바꾸지 않는다** — 바꾸면 집에서 도는 검사는 초록인 채
실물에서 조용히 깨진다. 묻는 손은 형제 스킬 company-mail 의 `scripts/inbox.py`(`Mailbox` 의 주소록 · 조직도 손 · `DirectoryPerson` ·
`OrgChart` · `GRADE_LEVELS`)이고, 이 스킬의 `scripts/directory.py` 는 그 손이 낸 사람을 찾고 거르고 넘긴다. 집의 가짜는 설정 저장소의
`_check/skills/company-mail/check_inbox.py`(`FakeDomino`)가 이 꼴을 흉내 낸다 — 실물에서 꼴이 달라졌으면 가짜를 먼저 맞추고 손을 고친다.

### 주소록 · 조직도 · 배포그룹

- 주소록 `/common/profile.nsf/ag_org_search_json?OpenAgent` 는 이름 · 메일 · 사번으로 찾고 밖의 주소는 0건이다. 답은
  `{dept, user, total}` 이다. `company` 는 조직도 고름 상자의 값(`<회사>(<코드>)`)이고 메일함마다 다르다. `dbpath` 는 그 세션의
  메일함 경로다 — 그래서 주소록을 물으려면 메일함을 연다. `key` 가 그 사람의 Notes 이름이다 — 주소로 찾든 `CN=` 이름으로 찾든 같다.
  부서 이름을 `search_key` 로 주면 사람은 0 명이고 이름이 든 부서들만 `dept` 에 온다. 직급 · 직책 이름으로는 0 건이다. `category` 는
  웹메일이 빈 값으로 보내는 칸이다(무엇을 가르나는 안 쟀다)
- 이름 찾기의 답에는 이름이 같은 다른 사람과 이름에 그 글자가 든 사람이 섞여 온다(`inbox.find_exact` · `directory.resolve` 가 거른다)
- 조직도는 웹메일 받는 사람 고름 창의 손 둘이다(`orgtree.js`). `ag_tree_dept_json` 은 `dept=<부서 코드>` 의 바로 아래
  부서들(`result[]` · `key` 가 코드 · `depth` · `has_child` · 부서 메일 주소)이고 `dept` 에 회사 값을 주면 맨 위 부서다.
  `ag_tree_user_json` 은 그 부서에 바로 든 사람이다(하위 부서는 안 든다 · 칸은 주소록 찾기와 같고 `dept_code` · 퇴직 칸이 없다 ·
  비면 `type` 이 `nothing` 인 한 줄). 본부장은 「임원」과 제 본부에 함께 든다
- 배포그룹은 `ag_org_search_json` 의 `type=group` · `group_type`(직책 · 직급 · 지역)이 목록(`group[]` · `key` 는
  `[02:직책]리더(02)` 꼴)을, `/common/lib_f.nsf/agGetDistribute?openagent&groupname=<key>` 가 구성원(`memberlist[]` —
  이름 · 직급 · 부서 · 메일)을 준다. 개인 주소록은 `type=private` 이다(잰 메일함은 비었다)
- 조직도의 부서 주소는 `dept_<회사>_<부서 코드>@` 꼴이다(`directory.DEPT_MAIL`)
- 회사 값의 기본은 `poscochem(02)` 이다(`directory.DEFAULT_COMPANY`)
- 메일함 파일 번호는 그 메일함을 쓰는 사람의 사번이다(`…/<사번>.nsf` — `directory.MAILFILE_NUMBER`) — 「나」 는 그 사번으로 주소록에 묻는다

### 직급 등급

- `inbox.GRADE_LEVELS` 의 원본은 회사의 인사 등급표(직급명 · 직책명 · 직급명칭명)이고, 코드와의 짝은 전사 조직도의 직급명칭명 · 직책
  구성이 표와 맞는 것으로 맞췄다. 29 · 30(둘 다 「임원」)과 34 · 35(둘 다 「과장」)의 차례는 직책 구성과 코드 차례로 고른 것이다
- 등급을 안 주는 직급 — 연구직(45–49) · 외주직은 등급이 없는 것이 맞다(빈칸이 아니라 사실이다). 소장(44)은 연구소장이면 임원급이고
  현장의 소장이면 아니라 직급만으로는 모른다. 이사(10)는 사외이사로 보여 회사의 위아래 밖이다
- `inbox.GRADE_NAME_LEVELS` — 고문은 퇴임을 앞두고 고문으로 있는 임원이라 임원급이다. 고문의 직급 코드와, 주소록이 직급 이름을 「고문」
  그대로 주는지는 안 쟀다 — 다른 글자로 오면 등급 없이 선다

### 걸리는 시간

- 조직도 전사를 받는 데 십수 초(15 초쯤)가 든다 — `ORG_CACHE_DAYS` 동안 받아 둔 판을 쓰고, 메일의 임시메일 받는 사람 잇기
  (`kept_book`)는 받아 둔 판이 없으면 새로 받지 않는 까닭이다

### 전화 — 사규 앱의 사람 창

- 형제 스킬 company-regulation 의 `references/SOURCES.md` 「화면에 있는데 손가락이 없던 것」 이 든다 — `/cmmn/ajax/getEmpInfo.do`(empcd)의
  `empInfo` 에 회사 전화(`officePhone`) · 휴대 전화(`handpon`)가 오고, 퇴사자 · 없는 사번은 빈다. 이 스킬은 그 손(`cbsop.App.person`)을
  주소록의 사번으로 부른다 — 요청의 꼴은 그 스킬이 잰 그대로다

## 회사에서 잴 것

- **주소록의 사번(`empno`)이 사규 앱의 사번(`empcd`)과 같은 값인가** — 전화(`--phone`)가 이 짝에 기댄다. 회사 PC 에서
  `python -X utf8 -I directory.py find --me --phone` 을 돌려 쓰는 사람 자신의 회사 · 휴대 전화가 서면 같은 값이다(「사람 창이 비었다」 면
  다르다 — 그때는 사번 꼴을 견주고 `phone_book` 이 그 꼴로 바꾼다)
- 주소록 찾기 답의 `dept_code` 가 조직도 나무의 부서 코드(`<코드>(<회사 약칭>)`)와 같은 꼴인가 — 집의 가짜는 괄호 없는 꼴을 낸다.
  내 부서 · 윗사람(`home_dept`)은 두 꼴을 다 받는다
- 메일 조직도의 부서 코드(`Dept.code`)가 문서함(ECM) 조직의 부서 코드와 같은 값인가 — 같으면 사람 파일에 조직을 넣을 수 있다. 지금은
  조직을 안 넣고 「안 넣은 것」 으로 댄다
- 일정함을 공유하지 않은 사람의 빈 때 — 실마리는 스킬 company-calendar 의 `SOURCES.md` 의 `agGetUserCalendarDBInfo` 줄이다

## 본 후보와 탈락

- 공개 스킬 — Domino 웹메일을 다루는 공개 스킬은 없다(스킬 company-mail 의 `references/SOURCES.md` 「본 후보와 탈락」)
- 주소록 손(`inbox.py` 의 주소록 · 조직도 손)을 이 스킬로 옮기는 길 — 그 손은 메일 서버에 묻는 길 · 읽기 길의 막기(`read_only_patterns`) ·
  세션 · 메일함 경로를 메일 손과 함께 써서, 옮기면 묻는 길이 두 벌이 되거나 두 손이 서로를 싣는다. 그래서 묻는 손은 메일 쪽에 두고
  찾기 · 거르기 · 넘기기만 여기 둔다
