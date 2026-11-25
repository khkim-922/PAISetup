# 설계의 까닭

`scripts/` 의 주석이 한두 줄로 못 다는 까닭을 파일마다 든다. 코드는 계약과 함정만 적고 여기를 이름으로 가리킨다. 회사 메일함 · 웹메일 화면 ·
중계에서 잰 사실은 [SOURCES.md](SOURCES.md) 「회사에서 잰 꼴」이 든다.

## inbox.py

### inbox.py · 바꾸는 손은 사람이 고른 뒤에만

- 메일함을 바꾸는 손(읽음 · 폴더 · 옮기기 · 휴지통 · 규칙 · 임시저장)은 사람이 그 대상을 보고 고른 뒤에만 부른다 — 회차 · 예약 작업 ·
  모델의 판단이 스스로 부르면 사람이 새 메일을 못 알아본다. 이 파일은 그 확인을 대신하지 않고, 언제 부르나는 부르는 쪽이 정한다
- 규칙은 서버가 그 뒤의 새 메일에 스스로 쓴다 — 사람이 없는 자리에서 메일함을 계속 바꾸는 손이라 넣기 · 고치기 전의 확인이 더 무겁다
- 규칙의 자동전달 칸(남에게 메일이 나가는 길)은 늘 비워 보내고, 자동전달 규칙은 고치지 않는다. 지우기는 된다 — 나가는 길을 닫는 쪽이다
- 손마다 제 주소 꼴만 보내고(`_send_change` · `_send_folder` · `_send_rule` · `_post_memo`), 서버의 `OK` 를 믿지 않고
  보기로 다시 봐서 안 섰으면 `MailboxError` 를 낸다 — 옮기기 · 휴지통 손은 서버가 못 해도 `OK` 나 빈 답을 낸다

### inbox.py · 본문 501 은 「본문 없음」

- 본문 주소에 501 을 내는 메일은 404 와 같이 None 으로 낸다 — 오류로 올리면 메일함을 훑는 회차가 그 한 통에 통째로 진다

## mail.py

### mail.py · 명령의 자세한 꼴

부르는 꼴은 `--help`(명령마다의 한 줄은 `COMMAND_HELP` · `PAIRED_HELP`)가 든다. 각 명령이 내는 줄의 자세한 꼴:

- `list` — 폴더 줄의 보낸 분 주소는 모든편지함에서 채우고(`AllMail`) 못 채운 줄은 그 수를 끝 줄에 댄다. `--since` 는 분까지 주면 그
  분의 0 초부터다. 끝 줄은 가장 늦은 메일의 때 · 번호, 그 시각까지 다 봤나(못 닿은 상자는 이름 · 훑은 수 · 잇는 명령), 어느 상자 보기에도
  없이 모든편지함에만 선 메일의 수를 댄다. 보낸 메일 줄은 「[보냄]」 을 단다. `--unread` · `--from` 은 받은 메일만 거른다.
  `--sent --to` 는 목록의 수신인 열(첫 사람)에 그 말이 들면 거기서 서고, 아니면 그 메일의 받는 사람 칸을 한 통씩 읽는다 — 그래서 한 번에
  훑는 통 수에 상한(`SENT_TO_SCAN`)을 두고, 상한에 막힌 판과 받는 사람 칸을 못 읽은 메일 수를 끝 줄에 댄다. 메일 줄의 받는 분은 그 말이
  든 사람만이다
- `summary` — 폴더는 채운 주소로 묶고 못 채운 줄의 수를 첫 줄에 댄다
- `read` — 받은 메일의 「함께 받은 사람」 은 받는 사람 · 참조를 합친 명단이고, 못 읽으면 그 까닭을 댄다
- `read-many` — 머리 한 줄은 읽음 · 때 · 자리 · 보낸 분 · 제목 · 번호, 본문의 줄바꿈은 한 줄로 편다. 답이 `OUT_BYTES` 를 안 넘는 데까지
  내고 남으면 다음 `--start`(준 번호의 차례)를 댄다. 읽음 표시 · 첨부 받기 · 그림은 안 다룬다 — 앞부분 훑기용이다
- `draft --preview` — 새 메일은 받는 사람을 다 펼쳐 주소록의 이름과 보이고, 편집 화면에서 지을 것은 화면이 채울 것과 바꿀 것을 보인다
- `preview-send` — 지금 판은 사람이 웹메일에서 고친 것까지 든다
- `send-draft` — 쓰는 사람의 탭에 그 메일이 열려 있으면 그 화면에서, 없으면 최소화한 창에서 [보내기]를 누른다. 열쇠는 preview-send ·
  draft(편집 화면에서 지은 것)가 낸 것을 받는다
- `preview-rule` — 메일함 손이 저장 앞에서 막는 규칙(조건이 하나도 없다 · 옮길 폴더가 없다)은 미리 보기에서 먼저 막는다 — 열쇠를
  낸 뒤 실행에서 멈추면 사람이 확인한 판이 안 선다. `preview-move` 가 받을 폴더를 앞에서 보는 것과 같은 자(`folders`)다
- `--html-file` 은 아뜰리에가 지은 메일 지면처럼 서식이 든 글을 싣는 길이다

### mail.py · 바꾸기 짝 — 미리 보기 → 확인 열쇠 → 실행은 한 꼴이다

읽음 · 폴더 · 옮기기 · 휴지통 · 되살리기 · 규칙의 짝은 한 손 둘(`preview_pair` · `apply_pair`)이 짝마다 한 줄(`PAIRS` 의 `Pair` — 계획 ·
이미 그 판인가 · 열쇠 재료 · 미리 보기의 말 · 바꾸기 · 「됐다」의 말)을 받아 선다. 「지금 판의 열쇠가 미리 본 열쇠와 같을 때만 바꾼다」
는 가름은 `refuse_stale` 한 자리라 짝을 더해도 그 가름을 다시 짓지 않는다. 미리 보기는 아무것도 안 바꾸고, 실행은 계획을 처음부터 다시
세워 그 판의 열쇠를 견준다 — 미리 본 뒤 사람이 웹메일에서 바꾼 것이 있으면 열쇠가 달라져 멈춘다.

### mail.py · 임시메일 짓기 — 손가락과 세분의 선

임시메일 짓기는 출발 하나(`DRAFT_STARTS`) × 바꿀 것 아무 조합(`DRAFT_CHANGES`) → 임시저장이다. 인자 · 「그 출발에는 그 손가락이 없다」의
거름 · `--help` 의 지도가 이 두 표에서 선다 — 손가락을 더하거나 빼는 일은 표의 한 줄과 그 일을 하는 손 하나다. 편집 화면에서 짓는
출발(`ON_SCREEN`)은 표의 `on_screen` 칸에서 끌어내고, 화면 손(`draft_send.js` 의 `STARTS`)의 출발과 이름이 같은지는 `check_mail.py` 가
잰다 — 화면 손은 집의 검사에서 대역이라, 한쪽에만 더한 출발은 집에서 초록이고 회사에서 처음 떨어진다. 받지 않는 출발에서 부르면 명령이
그 일을 어디서 하나를 대고 멈춘다. 회사 화면으로 아직 안 돌려 본 몫(재사용의 서식 지키기 · 답장 셋과 재사용의 첨부 붙이기 · 첨부
빼기)은 표의 `unmeasured` 칸에 들고, `--help` 의 지도와 그 손가락을 쓴 판이 「회사에서 안 쟀다」로 낸다 — 잴 것은 SOURCES.md
「회사에서 잴 것」 이 든다. 그 밖의 안 잰 화면 동작은 표에 안 넣는다.

인자의 꼴로 가를 수 있는 것(표에 없는 짝 · 빠진 값 · 없는 파일 · 같은 글로 바꾸기)은 명령마다 단 거름(`check`)이 세션을 받기 전에
막는다 — 세션 뒤에서 막으면 Edge 가 없는 자리에서 종료 3 이 나와 사람을 까닭 없는 로그인으로 보낸다.

어디까지 한 부름에 묶나는 사람이 웹메일에서 누르는 단위와 모델이 한 번 부르는 단위를 나란히 놓고 정했다.

| 사람이 웹메일에서 누르는 단위 | 모델의 한 부름에서 | 까닭 |
|---|---|---|
| 화면 하나를 연다 — [답장] · [전체답장] · [전달] · [재사용] · 임시메일 열기 · 새 쓰기 | 출발 인자 하나 | 화면을 여는 데가 비싸고(편집기 · 받는 사람 칸 · 첨부 칸이 늦게 선다) 화면마다 채우는 것이 달라 고를 손가락이다 |
| 받는 사람 · 제목 · 본문 · 본문 일부를 고친다(손짓 여럿) | 바꿀 것 인자들 — 아무 조합을 한 부름에 | 한 칸씩 부르면 화면을 그만큼 다시 열고, 열린 화면의 상태를 모델이 들고 다닌다 — 못 할 까닭을 다 가린 뒤 한 번에 넣어야 사람 화면에 반쪽 판이 안 남는다 |
| [임시저장] | 부름의 끝 — 늘 | 되돌릴 수 있고 안 나간다 |
| [보내기] | 따로 뗀 부름 — `preview-send` → `send-draft --confirm` | 되돌릴 수 없다 — 사람이 본 판의 열쇠가 맞을 때만 누른다 |
| 웹메일 단추 하나하나 | 내지 않는다 | 사외 주소 · 받은 메일을 편집으로 열기 · 발송 확인 같은 가드가 모델 손으로 샌다 |

### mail.py · 임시메일의 받는 사람 잇기

사람 찾기는 형제 스킬 company-directory 의 찾기가 하고 이 스킬은 그 스킬을 싣지 않는다 — 출처 · 거르기 · 내는 꼴 · 사람 파일과 그 까닭은
그 스킬의 `references/DESIGN.md` 가 든다. 이 명령의 맨 위 `--help` 「안 하는 것」 이 그 자리를 댄다.

- 임시메일의 받는 사람 잇기(`book_people`)는 주소록의 찾기와 한 자(`mail_people.address_people` · `kept_book`)로 주소를 사람에
  잇는다 — 찾기가 파일에 넣은 주소를 저장이 다른 사람으로 세우지 않는다. 그 자는 이 스킬에 살고 주소록이 받아 쓴다(아래 「내주는 조각」)

### 내주는 조각 — 주소록과 함께 쓰는 사실은 이 스킬이 든다

주소록(company-directory)은 사람을 찾는 물음마다 이 스킬의 메일함 손(`inbox.py`)에 묻고, 이 스킬의 본일(찾기 · 읽기 · 첨부 · 폴더 ·
규칙 · 보내기)은 주소록 없이 선다. 그래서 두 스킬이 함께 쓰는 사실의 주인은 아래인 이 스킬이다 — 명령을 멈추는 꼴(`mail_stop`) · 받아
둔 것의 자리와 회사 값과 받아 둔 조직도(`mail_kept`) · 세션으로 메일함 열기(`mail_open`) · 주소를 사람으로 잇는 자와 배포그룹 고르기와
사람 한 줄의 꼴(`mail_people`) · 메일 한 통을 번호로 찾기(`mail_find`) · 메일 한 통의 받는 사람 명단 읽기(`mail_recipients`). 명령
파일(`mail.py`)이 아닌 파일에 두어, 주소록이 명령 파일을 통째로 싣지 않고 그 조각만 싣는다.

- 다른 스킬이 이 폴더에서 싣는 이름은 `scripts/handout.py` 한 자리에 적는다 — 거기 없는 이름은 다른 스킬이 싣지 않는다. 이름을 바꾸거나
  빼면 싣는 스킬을 같은 판에 고친다
- 이 스킬은 주소록을 싣지 않는다 — 기대는 방향은 주소록 → 이 스킬 한쪽이다. 주소록의 지난 메일 출처가 메일함을 읽는 것도 이 스킬이
  내준 조각(`mail_find` · `mail_recipients`)으로 한다
- 주소록의 찾기만 쓰는 사실(출처 · 거르기 · 동명이인 · 사람 파일)은 주소록에, 메일 명령만 쓰는 사실(부서 주소의 꼴 `DEPT_MAIL` · 부서
  주소로 부서 잇기 `dept_book`)은 `mail.py` 에 둔다

### mail.py · 세션

- 세션 손을 부르면 쓰는 사람의 Edge 가 디버깅 포트로 떠 있고 로그인돼 있으면 그 세션을 파일로 받아 사람 손 없이 선다 — 손은 인자 없이
  말없이 부른다(까닭과 바퀴는 `ep_session.session_first`)
- 세션 파일의 자리는 세션 손 한 곳이 정한다 — 이 명령은 손이 표준 출력 끝 줄에 낸 절대 경로를 읽고 자리를 따로 안 든다
- 세션으로 받은 메일함 주소는 그 세션 쿠키의 지문과 함께 받아 두어 같은 로그인 동안 메일 서버 첫 화면에 다시 묻지 않는다. 사람에게도
  묻지 않는다

### mail_find.py · 메일 찾기

- `sweep_views` 는 보기를 통 수와 상관없이 한 번씩만 훑는다 — 여러 통을 한 통씩 따로 찾으면 통마다 같은 보기를 처음부터 다시 받는다
- 받은편지함에서 다 서면 거기서 끝내고, 아니면 남은 보기들을 함께(`inbox.ORG_WORKERS` 만큼) 받는다 — 폴더를 하나씩 차례로 받으면
  폴더 수만큼 기다린다. 첫 판에 못 찾은 것이 있으면 같은 보기들을 끝까지 훑는다
- `first` 를 주면 그 보기를 끝까지 먼저 훑고 남은 것만 나머지 보기에서 찾는다(`sweep_order`) — 한 메일이 두 보기에 함께 설 수 있어
  (폴더로 옮긴 보낸 메일) 어느 보기의 줄로 서나가 뜻인 찾기(주소록의 지난 메일 — 보낸 메일인가)가 쓴다. 그 보기만 따로 찾고 못 찾으면
  다시 찾으면 그 보기를 두 번 훑는다
- `read-many` 가 한 세션 · 한 프로세스로 여러 통을 읽는 것도 같은 까닭이다 — 지울 메일 확인 · 하루치 새 메일 훑기처럼 수십 통을 볼 때
  통마다 프로세스 · 세션을 다시 세우지 않는다

### mail.py · search — 낱말 × 보낸 분 × 날짜 한 부름

사람이 메일을 말할 때는 낱말 · 보낸 분 · 때가 섞여 온다. 셋을 다른 명령에 나눠 두면 모델이 명령 사이를 오가고, 하나만 맞춰 0건을 받으면
그 0건을 「없다」 로 옮긴다. 그래서 `search` 하나가 셋을 아무 조합으로 받는다.

- 웹메일 검색 손은 한 번에 한 칸만 받고(칸을 여럿 주면 다 든 메일만 낸다) 보낸 분 · 날짜 칸이 없다 — 요청의 꼴은 그대로 두고, 칸마다 한 번씩
  묻어 unid 로 합친 뒤 보낸 분 · 날짜를 이 명령이 거른다. 거를 때는 한 쪽을 가득(`SEARCH_PAGE_MOST`) 받아 그 쪽을 다 보고, 서버가 더
  낸 줄이 있으면 끝 줄이 다음 `--page` 를 댄다
- 기본 칸은 제목 · 본문 둘이다(`SEARCH_DEFAULT_FIELDS`) — 사람이 기억하는 낱말은 본문에만 있기 흔하다
- 낱말은 자리 인자 여럿으로 와도 빈칸으로 이은 한 말로 맞춘다(`JoinWords`) — 사람의 말을 따옴표 없이 넘기면 셸이 빈칸마다 갈라, 한
  인자만 받으면 「unrecognized arguments」 로 한 부름을 잃는다
- 보낸 분은 준 말에 더해, 주소록에서 그 이름이 꼭 같은 살아 있는 사람들의 영문 이름 · 주소로도 견준다(`SenderMatch`) — 메일의 보낸 분 칸은
  영문 이름만 들기도 한다. 그 이름이 여럿이면 다 견주고 섞였을 수 있다고 그 사람들을 댄다. 보낸 · 임시 메일은 보낸 분이 쓰는 사람이라
  `--from` 에 안 든다
- 날짜는 서울 날로 가른다 — 검색 손의 시각은 UTC 라 그대로 견주면 서울 새벽 메일이 전날로 밀린다
- 낱말이 없으면 검색 손을 안 쓰고 받은편지함 · 폴더 보기를 보낸 분 · 날짜로 훑는다(`list --since` 와 같은 자 — 상한 · 멈춤 · 「거기까지만
  봤다」)
- 0건 줄은 무엇을 어디서 찾았나와, 좁힌 것을 하나씩 푸는 다음 걸음(`widen_steps`)을 댄다 — 「그 말로 그 칸에서 못 찾았다」 가 사람에게 갈 말이다

### mail.py · 멈춤은 늘 다음 걸음을 든다

0 이 아닌 끝은 다 「다음: …」 을 한 번 든다 — 멈춘 자리가 제 걸음을 대면 그것이, 안 댔으면 종료 값의 걸음(`mail_stop.NEXT_WORDS` · `Stop.said`)이
붙는다. 제 걸음을 댔나는 멈춤을 지은 자리가 `stepped` 로 말한다 — 글에 「다음:」 이 섰나로 가르면 사실만 말하는 글(「세션이 끊겼다」)에
걸음이 두 번 서거나, 옮겨 실은 남의 글에 든 「다음:」 이 이 멈춤의 걸음을 지운다. 형제 스킬 ep-login 의 멈춤(`ep_command.Stop`)도 같은
표시를 들어, 그 멈춤을 다시 싣는 자리(이 스킬 · company-directory)는 표시를 그대로 옮긴다. 멈출 때마다 모델이 걸음을 짐작하면 같은 명령을 되풀이하거나 엉뚱한 명령으로 돌아간다. 웹메일 편집 화면의 손이 멈춘 뒤의 걸음은
종료 값마다 `HAND_NEXT` 가 든다 — 화면에서 멈춘 일은 다시 불러도 같은 자리에서 멈춘다. 보내기만은 다르다 — 손이 [보내기]를 누른 뒤일
수 있는 멈춤(손의 종료 값이 `HAND_UNPRESSED` 밖 · 누른 뒤 보낸편지함에 아직 없음 · 보낸편지함에 섰음)에 `HAND_NEXT` 를 붙이면 그 걸음이
같은 메일을 두 번 내보낸다. 그래서 그 멈춤은 손의 말만(`HandStopped.hand_said`) 옮겨 싣고 「다시 보내지 않는다 · 보낸편지함을 다시 본다」
걸음을 붙인다.

### mail.py · 새 메일의 서명은 저장한 판에서 보인다

새 메일(`draft new`)은 웹메일 설정이 서명을 켰을 때 저장하며 글 아래 서명이 붙고(`inbox.save_draft`), 켰는지는 미리 모른다. 그래서 저장한
뒤 그 임시메일의 본문을 한 번 읽어 넣은 글 뒤에 붙은 것을 보인다(`show_saved_tail`) — 글로 「붙는다」 고만 적으면 꺼진 PC 에서 틀리고, 모델은
서명이 붙나를 몰라 글 끝에 이름을 또 쓴다. `--preview` 는 저장 전이라 붙는 조건만 말한다.

### mail_find.py · 모든편지함으로 채우기

`AllMail` 은 찾는 줄이 있을 때만 모든편지함을 새것부터 `DEEP_PAGE` 줄씩 이어 받고, 다음 가운데 하나면 멈춘다 — 찾는 줄이 다 섰다 ·
보기가 끝났다(빈 쪽) · 서버가 start 를 안 따른다(쪽의 첫 줄이 앞 쪽과 같다) · 받은 줄이 못 찾은 줄보다 다 옛것이 됐다 · `FILL_SCAN`
줄을 받았다. 받은 줄은 명령 하나 동안 들고 있어 폴더의 쪽마다 다시 안 받는다. 보낸 분은 모든편지함 쪽에 주소가 설 때만 바꾼다. 모든편지함
보기가 없는 메일함은 폴더 줄이 다 못 찾은 줄이다. 기대는 꼴은 보기를 정렬 없이 받으면 날짜 내림차순이라는 것이다(SOURCES.md
「inbox.py · 폴더 보기 · 모든편지함」).

### mail.py · list --since

- 상자마다 보기를 새것부터 `SINCE_PAGE` 줄씩 받다가 그 시각보다 옛 줄이 서면 멈춘다 — 보기가 날짜 내림차순이라 그 뒤는 더 옛것이다
- 상자를 안 고른 판은 모든편지함도 그 시각까지 받아(폴더 줄을 채우는 그 장 넘기기 — `AllMail.reach_date`) 어느 상자 보기에도 없는 메일의 수를 댄다 — 상자가
  다 닿았을 때만 센다. 못 닿은 상자가 있으면 못 본 메일이 그 수에 섞이기 때문이다
- 메일을 여는 주소는 안 짓는다 — 읽음이 그대로다

## draft_send.js

- 보내기는 웹메일 화면의 [보내기]를 누르는 길뿐이다 — 그래야 웹메일이 보내기 전에 하는 정책 · 첨부 확인을 다 거치고 보낸편지함에 남는다
- `inspect` 는 본문 HTML 을 그대로 내고 글자는 부르는 쪽이 뽑는다 — 보이는 글을 푸는 손은 `visible.py` 한 벌이다
- 확인 열쇠는 지금 판(받는 사람 · 제목 · 첨부 · 본문) 위에 서서, 사람이 그 화면에서 고친 것까지 든다
- `send` 의 0 은 「발송 확인에 예 하고 저장 답이 왔다」까지다 — 보낸 뒤의 알림 · 늦은 자동저장은 이 손이 못 가려, 나갔나는 부르는 쪽이
  보낸편지함 · 임시보관함으로 가린다
- `EDGE_DEBUG_PORT` 의 기본값은 형제 스킬 ep-login 의 띄우는 손이 여는 포트다
- `edit` 은 화면 하나를 열고 바꿀 것을 다 넣은 뒤 [임시저장]을 한 번 누른다. 화면을 건드리기 전에 못 할 까닭(넣은 글 자리 · 조각 ·
  주소록)을 다 가린다 — 쓰는 사람이 연 화면에 저장 안 된 반쪽 판을 남기지 않으려는 것이다. 출발은 `STARTS` 의 한 줄이다
- 본문은 `rebody` 가 편집기 본문 HTML 을 받아 새 판을 짓고 편집기에는 한 번만 넣는다. 조각 바꾸기는 글자 마디 안의 글자만 바꿔
  태그 · 서식 · 그림을 그대로 두고, 공백은 너그럽게 맞춘다(화면의 빈칸이 `&nbsp;` 일 수 있다). 조각이 둘 이상 · 없음 · 마디를 걸침이면
  고르지 않고 멈춘다 — 짐작으로 고른 자리가 인용 속일 수 있다. 조각을 바꾼 판은 편집기에 선 뒤 보이는 글자를 지은 판과 한 번 더 견준다
- body 태그 없는 본문의 맨 앞 `<style>` 은 파서가 head 로 옮긴다 — `rebody` 가 새 판 앞에 되돌려 싣는다. 안 그러면 저장 뒤 서식이 빠진다

## attachments.py

- 가름이 한 벌이다 — 이 스킬의 명령과 형제 스킬 company-board 가 같은 손을 불러, 한쪽만 고쳐져 어긋나는 일이 없다. 문서함(ECM) 쪽지의
  이름 꼴과 열쇠는 곁의 `inbox` 가 든다(`ECM_ATTACHMENT` · `ecm_note_key`)
- 이름이 겹치면 그 메일 · 글의 첨부 **모두**에 「<번호>-」 를 붙인다 — 번호가 서로 달라 겹치지 않고, 몇 번을 골라 받든 같은 첨부는 같은
  이름이다
- 읽는 손(drm-office-read)이 받는 꼴은 그 스킬이 내주는 값 파일 `scripts/handler.json` 의 `handler` 를 그 자리에서 읽는다(DRM 길잡이 훅과
  그 스킬의 읽는 부품도 같은 값을 읽는다). 여기 따로 적으면 읽는 손이 꼴을 늘리거나 줄인 날 이 말만 낡아, 안 받는 꼴을 그 손으로 넘긴다. 표를 못 읽으면 받는
  꼴을 지어내지 않고 감긴 첨부마다 못 가렸다고 말한다 — 한글은 표와 상관없이 제 말이다

## body_images.py

- 바이트를 답에 싣지 않고 파일로만 남긴다 — 모델은 받은 파일을 그림으로 열고, 그 여는 순간 그림 문(홈 훅 `image-gate`)이 치수를 잰다
- 꼴과 치수는 씨앗의 머리 읽기(`_image_head.py` — 진본은 설정 저장소 `seeds/check/`)가 읽는다. 그림 문이 부르는 그 읽기라, 따로 적으면
  받아 둔 그림과 문이 재는 그림이 다른 치수를 말한다. 그 부품을 못 찾으면 주소도 안 묻고 주소마다 `skipped` 에 까닭을 낸다 — 본문 글자는
  이 손을 안 거치므로 그대로 온다
- 큰 그림은 받자마자 줄인다 — 그림의 값은 치수가 정해, 그림 문이 여는 순간에는 이미 늦다. 줄이는 손은 본문 하나에 `--batch` 로 한 번만
  띄운다 — 장마다 띄우면 해석기와 PIL 을 장마다 싣는다. 눈금 · 줄이는 손 · PIL 이 없거나, 줄이기가 지거나, 시한(장마다
  `SHRINK_SECONDS`)에 끊기면 못 구운 그림은 받은 그대로 남는다
- 줄이는 손은 딴 프로세스로 띄운다 — PIL 이 드는데, 이 파일을 부르는 명령은 격리 모드(`-I`)로 돌아 쓰는 사람 자리에 깐 PIL 을 못 본다.
  그 손은 진 짝의 결과를 안 남기고 다 구운 것만 제 이름으로 옮겨, 끊긴 판에도 반쪽 그림이 결과 이름으로 남지 않는다
- 남기는 그림의 위(`MAX_IMAGES`)는 남긴 장으로 센다 — 차례로 세면 앞의 아이콘이 위를 먹어 뒤의 도표가 빠진다

## visible.py

- 이 손은 모델이 글을 읽기 전에 지나는 자리다 — 사람 눈에는 안 보이는데 모델에게만 읽히는 글(숨긴 지시)이 그대로 넘어가지 않게 한다.
  본문 HTML 을 푸는 손이 한 벌이라, 어느 앱에서 온 글이든 같은 잣대로 걸린다
- 숨긴 요소는 `hidden` 속성 · display:none · visibility · 투명 · 아주 작은 글자 · 넘침을 자른 0 높이 · 화면 밖으로 민 글이다. 잣대는
  쓰는 사람이 메일을 여는 웹메일(브라우저)이라, 그 화면에 그려지는 것(흰 바탕이 아닌 곳의 흰 글씨 같은 것)은 남긴다
- 주석은 어느 메일 프로그램도 안 그리는 글이라 걷기만 하고, 숨긴 덩이로 셀지는 부르는 쪽이 가른다 — Outlook 의 조건부 주석이 거의 모든
  메일에 있어, 세면 모든 메일이 숨긴 글을 든 것으로 읽힌다
- 표 꼴은 표의 한 행이 한 줄이 되게 한다 — 칸 안의 문단 · 줄바꿈은 빈칸이 되고, 숨긴 칸 · 행은 글자만 빠지고 자리는 지켜 열이 안 밀린다.
  글자가 하나도 안 남은 행은 줄을 안 낸다. 표 밖은 블록마다 앞뒤로 줄을 갈라 문단 사이가 빈 줄이고, 마크업 안의 줄바꿈은 그대로 줄바꿈이다
- `invisible` 은 서식 문자 · 제어 문자를 걷는 한 자리다 — 메일 명령은 본문을 읽을 글자로 다듬을 때(`mail.py` 의 `readable`), 첨부 가름은
  파일 이름을 고를 때(윈도 파일 이름에 제어 문자는 못 든다) 부른다. 명령이 내는 모든 줄을 지나는 문은 두지 않는다 — 제목 · 이름 같은
  한 줄 칸은 메일함이 준 글자 그대로다

## directory_survey.py

HAR 받는 법 — 회사 PC 에서 사람이 웹메일 「새 메일」의 받는 사람 고름 창을 열고, Edge 개발자 도구(F12) 네트워크 탭에 「로그 유지」를 켠 채
그 창의 기능을 다 눌러 본 뒤 「HAR 로 모두 저장」한다. 누를 것 — 조직도 펼치기(회사 → 실 → 그룹) · 부서 누르기 · 이름 · 부서 · 직책 찾기 ·
탭마다(개인 주소록 · 그룹 · 배포 목록 · 최근 · 즐겨찾기) 한 번씩. 이 판에 안 눌린 기능의 주소도 받은 스크립트 본문에서 「스크립트에만 보인
주소」로 거둔다.

## 조각의 지도

메일 손은 대화의 명령(`mail.py`)과 메일함의 손(`inbox.py`), 그리고 둘이 함께 기대는 곁 조각들이다 — 다른 스킬이 실어 쓰는 이름은
`handout.py` 가 표로 든다. 파일마다의 까닭은 위 절들이 든다. 브라우저 안의 손(`draft_send.js`)은 이 지도에
안 선다 — 이 손은 파이썬만 읽는다.

아래는 코드에서 뽑은 지도다 — 줄의 문장은 그 조각 머리말의 첫 문장이라, 문장을 고치려면 머리말을 고치고 다시 짓는다.

<!-- drawn:piece-map · 손으로 고치지 않는다 — scripts/skill-map.py 가 짓는다 -->
| 조각 | 맡은 일 | 싣는 곁 조각 | 다른 스킬에서 싣는 것 |
|---|---|---|---|
| `directory_survey.py` · 입구 | 웹메일 주소록 화면이 서버에 무엇을 묻는지를 HAR 하나에서 거둔다 — 주소록의 기능을 한 판에 다 조사하는 손. | `inbox` | — |
| `mail.py` · 입구 | 사내 메일함을 대화에서 다루는 얇은 명령 — 곁의 메일 손(``inbox.py`` · ``draft_send.js``)을 그 자리에서 부른다. | `attachments` · `body_images` · `inbox` · `mail_find` · `mail_kept` · `mail_open` · `mail_people` · `mail_recipients` · `mail_stop` · `mail_token` · `visible` | ep-login 의 `ep_command` · `ep_session` |
| `inbox.py` | 사내 메일함(Lotus Notes · HCL Domino 웹메일)을 읽는 손과, 메일함을 바꾸는 이름 붙은 손들. 표준 라이브러리와 형제 스킬 ep-login 의 ``ep_session``(세션 파일 → 쿠키 통)만 쓴다 — ``../../ep-login/scripts/`` 에서 싣고, 그 자리가 없으면(이 파일만 옮겨 쓸 때) ``ep_session.py`` 와 ``places.json`` 을 이 파일 곁에 둔다. | `mail` | ep-login 의 `ep_session` |
| `mail_recipients.py` | 메일 한 통의 받는 사람 명단 — 받은 메일의 「함께 받은 사람」을 받는 사람 목록 보기에서 꺼내고, 명단 줄의 칸과 한 줄의 말을 정한다. | `inbox` · `mail_people` | — |
| `mail_open.py` | 세션으로 메일함을 연다 — 메일함 주소를 고르고(준 주소 · 같은 로그인에 받아 둔 주소 · 메일 서버 첫 화면) 메일함 손을 세운다. | `inbox` · `mail_kept` · `mail_stop` · `mail_token` | ep-login 의 `ep_command` · `ep_session` |
| `mail_people.py` | 받는 사람 잇기 — 주소를 주소록의 꼭 한 사람으로 잇는 자 · 배포그룹 하나 고르기 · 사람 한 줄의 꼴과 받는 사람 칸의 이름. | `inbox` · `mail_kept` | ep-login 의 `ep_command` |
| `mail_kept.py` | 받아 두는 것 — 받아 둔 것의 자리 · 주소록의 회사 값 · 회사 값마다 받아 둔 조직도(읽기 · 새로 받기 · 남기기). | `attachments` · `inbox` | ep-login 의 `ep_command` |
| `attachments.py` | 첨부 가름 — 받은 첨부 하나를 어떤 이름으로 남기고 무엇으로 읽으라고 이르나를 가른다. | `visible` | — |
| `mail_find.py` | 메일을 번호(unid)로 찾는 자리 — 받은편지함 · 폴더 · 임시보관함 · 보낸편지함의 보기를 훑어 목록 줄을 내고, 폴더 줄의 빈 칸은 모든편지함에서 채운다. | `inbox` · `mail_stop` | ep-login 의 `ep_command` |
| `body_images.py` | 본문 그림 — 메일 · 게시글 본문의 그림을 파일로 받아 둔다. | — | — |
| `handout.py` | 메일 손이 다른 스킬에 내주는 이름의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰는 이름. | — | — |
| `mail_stop.py` | 명령을 멈추는 꼴 — 종료 값과 사람에게 낼 말이고, 0 이 아닌 끝은 늘 다음 걸음을 든다. | — | ep-login 의 `ep_command` |
| `mail_token.py` | 지문 — 부분들을 한 꼴(키를 고른 JSON)로 이은 글의 sha256 앞 ``TOKEN_LENGTH`` 자. | — | — |
| `mailer.py` | 사내 메일 중계로 메일을 보낸다 — 표준 라이브러리만 쓰는 파일 하나. 메일 비서가 깔린 자리에서 싣는 손이고, 스킬의 명령은 안 쓴다(그 명령은 웹메일 화면으로만 보낸다 — draft_send.js). | — | — |
| `visible.py` | 보이는 글 — 사내 앱의 본문 HTML(메일 · 게시글 · 사규)에서 사람 눈에 안 보이는 것을 걷고 읽을 글자로 푼다. | — | — |

**입구에서 내려가는 나무** — 줄마다 조각과 그 머리말 첫 문장. 한 조각은 처음 닿은 자리에서만 펴고 다시 닿으면 `↑` 로 가리킨다. 클래스는 메서드를 그 아래에 든다. `←` 뒤는 그 조각을 부르는 다른 스킬이다. 인스턴스를 거친 부름은 이어지지 않는다.

- `main` — 명령 줄을 받아 HAR 를 읽고 메일함 경로로 읽기 길 목록을 지어 조사 글줄을 찍는다 → 종료 값.
  - `load_har` — HAR 파일을 읽어 요청 · 응답 기록(``log.entries``)을 낸다 — 그 꼴이 아니면 ValueError.
  - `inbox.read_only_patterns` — 읽기 길이 물을 수 있는 주소 꼴(서버 뿌리부터의 경로 · 질의) — 다 읽음을 안 바꾸는 것으로 잰 꼴이다.
  - `survey` — HAR 기록을 (방법, 호스트, 주소)로 묶어 질의 칸 · 답의 꼴 · 읽기 길이 묻나를 사람이 읽는 글줄로 낸다 — 스크립트에만 보인 주소도 끝에 붙인다.
    - `endpoint` — (호스트, 경로 · 명령, 질의 칸, 서버 뿌리부터의 경로+질의). Domino 의 명령(``?OpenAgent``)은 경로에 붙여 한 주소로 본다.
    - `body_text` — HAR 기록 하나의 응답 본문 글 — base64 면 풀고, 못 풀면 빈 글.
    - `shape` — JSON 값의 꼴 — 열쇠와 형, 배열은 길이와 원소 칸의 합. 코드 같은 칸(CODE_KEY)의 값은 ``codes`` 에 모은다.
    - `clip` — 보기 값 하나를 공백을 한 칸으로 접고 SAMPLE_CHARS 글자에서 자른다.
- `main` — 명령줄 한 번 — 출력을 UTF-8 로, 경고 로그를 세우고 ``dispatch`` 로 넘긴다 → 종료 값.
  - `dispatch` — 인자를 풀어 명령 하나를 돌린다 — 명령줄 한 번(``main``)과 serve 의 요청 하나가 같이 지난다.
    - `inbox.is_unid` — 메일 · 폴더 · 규칙의 열쇠(unid — 16진 32자리, 대소문자는 안 가린다)의 꼴인가 — 메일 번호의 꼴은 이 한 자리가 든다.
    - `serve` — ``SERVE_HELP`` 의 꼴로 요청을 받는 대로 답한다 — 표준 입력이 닫히면 0. 표준 오류(경고 · 인자 오류의 말)는 그대로 흐른다.
      - `serve_one` — 요청 한 줄 → (id, 종료 값, 표준 출력의 바이트). 명령은 ``dispatch`` 를 그대로 지난다 — 따로 불렀을 때 프로세스가 졌을 판(잡히지 않은 예외)은 그 요청만 종료 1 로 진다.
        - ↑ `dispatch`
    - `_run` — 명령 한 판 — 인자의 꼴을 세션 앞에서 거르고(명령마다 단 ``check`` · 종료 2) 세션 차례로 명령 손을 돌린다(``run_in_session``). 멈추면 그 말을 내고 그 종료 값이다.
      - `run_in_session` — 명령 손 하나(``args.fn``)를 세션 차례(형제 스킬 ep-login 의 ``session_first``)로 돌린다 — 세션 손 · 메일함 손의 실패는 이 명령의 멈춤으로 옮긴다(``mail_open.stops_from_mail``).
        - `mail_open.given_url` ← company-directory — 사람 · 설정이 준 메일함 주소 — 준 값(``--url``) · ``MAILBOX_URL`` 순. 없으면 빈 글자.
        - `mail_open.stops_from_mail` ← company-directory — 그 안에서 난 세션 손 · 메일함 손의 예외를 멈춤으로 옮긴다 — 세션 손이 못 섰으면(``ep_session.NoSession``) ``no_session``, 메일함 손의 오류면 ``mailbox_stop``. ``failed`` 는 메일함이 답을 안 준 판의 말 꼴(``{why}`` 자리)이다.
          - `no_session` — 세션 손이 못 선 까닭(``ep_session.NoSession`` 의 ``got``)을 이 명령의 멈춤으로 — 종료 값과 말은 사내 앱 명령의 한 자리(형제 스킬 ep-login 의 ``ep_command.no_session``)가 든다.
            - `mail_stop.from_ep` ← company-directory — 형제 스킬 ep-login 의 멈춤(``ep_command.Stop``)을 이 명령의 멈춤으로 — 종료 값 · 글 · 제 걸음을 들었나(``stepped``) 그대로다.
              - `Stop` ← company-directory — 명령을 멈춘다 — ``code`` 가 종료 값, 메시지가 사람에게 낼 글이다.
                - `Stop.said` — 사람에게 낼 글 — 제 걸음을 안 들었으면 종료 값의 걸음을 붙인다.
          - `inbox.MailboxError` ← company-directory — 메일함을 못 읽었다.
          - `mailbox_stop` — 메일함 손의 오류 하나(``inbox.MailboxError`` 의 갈래) → 멈춤 — 세션이 끊겼거나 세션 파일(``session``)을 못 읽었으면 3, 읽기 길이 막은 주소는 1, 설정 · 인자가 틀렸으면 2, 메일함이 답을 안 주면 1(말 꼴은 ``failed``). 글은 사실과 메일함 손이 댄 까닭이고 걸음은 종료 값이 붙인다.
            - `inbox.SessionExpired` ← company-directory — 세션이 끊겼다 — 다시 로그인해 쿠키 파일을 새로 남긴다(스킬 ep-login).
            - ↑ `mail_stop.Stop`
            - `inbox.SessionMissing` — 세션(쿠키) 파일이 없거나 · 못 읽거나 · 쿠키가 하나도 없다 — 주소 · 인자를 고칠 일이 아니라 사내 세션을 다시 받을 일이다(스킬 ep-login).
            - `inbox.ChangeRefused` — 읽기 길이 메일함을 바꿀 주소(또는 읽기 전용으로 잰 꼴 밖의 주소)를 지었다 — 서버에 닿기 전에 막았다.
            - `inbox.MailboxConfigError` ← company-directory — 설정이 틀렸다 — 주소 · 쿠키 파일 · 인자. 묻기 전에 잡힌다.
        - ↑ `inbox.SessionExpired`
        - `file_first` — 세션 파일부터 돌리나 — 읽는 명령과 ``--preview`` 는 파일부터 · 거절되면 손을 띄워 한 번 더, 바꾸는 명령(``MUTATING``)은 늘 손부터 받아 한 번만 돈다(두 번 돌면 메일이 두 번 나가거나 두 번 바뀐다).
      - ↑ `mail_stop.Stop`
  - `parser` — 명령마다의 인자 정의를 지은 명령줄 해석기 — 도움말 끝에 명령 지도를 단다.
    - `top_map` — 맨 위 --help 의 지도 — 묶음마다 명령 한 줄(짝은 한 줄에 둘), 종료 값의 뜻, 안 하는 것. 다 표에서 짓는다.
    - `check_unid_args` — unid 를 받는 명령의 인자 — 준 열쇠마다 꼴을 세션 앞에서 본다.
      - `mail_find.unid_shape` ← company-directory — 메일 · 규칙의 열쇠(unid)의 꼴(``inbox.is_unid``)인가 — 아니면 Stop. 꼴이 아닌 번호의 멈춤 말은 이 한 자리가 든다 — 세션 앞의 거름과 찾는 손(``find_mails`` · 휴지통 찾기)이 같은 말로 멈춘다.
        - ↑ `inbox.is_unid`
        - ↑ `mail_stop.Stop`
    - `cmd_session` — 세션이 살아 있나 묻는다 — 살았으면 메일함 주소를 내고, 끊겼으면 세션 종료 값으로 멈춘다.
      - `open_mailbox` — 이 명령의 메일함 — 인자의 주소 · 세션 파일로 연다(``mail_open.open_mailbox``). 고른 주소는 ``args.mailbox_url`` 에 둔다 — 뒤의 세션 줄 · 화면 손 · 첨부 자리가 읽는다.
        - `mail_open.open_mailbox` ← company-directory — 세션으로 메일함을 연다 — 주소를 골라(``mailbox_url``) 메일함 손을 세운다(``mailbox_hand``). ``url`` 은 사람이 준 주소(``--url`` 값 · 없으면 빈 글자)다.
          - `mailbox_url` — 메일함 주소 — 준 주소 · ``MAILBOX_URL`` 순(``given_url``), 둘 다 없으면 그 세션의 주소(``session_url``).
            - ↑ `given_url`
            - `session_url` — 그 세션의 메일함 주소 — 같은 로그인에 받아 둔 것(``kept_mailbox``)이 있으면 그것, 없으면 메일 서버 첫 화면에 묻는다 (``inbox.discover_mailbox``). 받은 주소는 받아 둔다.
              - `session_mark` — 그 세션이 그 메일 서버에 싣는 쿠키의 지문 — 받아 둔 메일함 주소를 로그인 한 판에 묶는다.
                - `mail_token.token` — 부분들의 지문 — 부분이 같으면 같은 ``TOKEN_LENGTH`` 자, 하나라도 다르면 다른 글자다.
              - `kept_mailbox` — 그 지문으로 받아 둔 메일함 주소 — 없거나 지문이 다르거나 파일이 깨졌으면 빈 글자다.
                - `mail_kept.cache_dir` ← company-directory — 받아 둔 것(조직도 · 메일함 주소)의 자리 — ``MAIL_ORG_CACHE_DIR`` 이 있으면 그 폴더, 없으면 홈 아래 ``ORG_CACHE_DIR``.
              - `inbox.discover_mailbox` — 그 세션에 로그인한 사람의 메일함 주소(``<서버>/<경로>.nsf``)를 메일 서버 첫 화면에서 받는다 — 사람에게 묻지 않는다.
                - ↑ `MailboxConfigError`
                - ↑ `SessionMissing`
                - `_charset` — content-type 의 charset — 없으면 utf-8.
                - ↑ `SessionExpired`
                - ↑ `MailboxError`
              - `keep_mailbox` — 메일함 주소를 그 지문과 함께 받아 둔다 — 쿠키 값은 안 적는다.
                - ↑ `kept_mailbox`
                - ↑ `mail_kept.cache_dir`
              - ↑ `inbox.SessionExpired`
              - ↑ `inbox.SessionMissing`
              - ↑ `mailbox_stop`
              - ↑ `inbox.MailboxConfigError`
              - ↑ `mail_stop.Stop`
            - `mail_server` — 메일 서버 — ``MAIL_SERVER``, 없으면 형제 스킬 ep-login 의 기본 서버(``ep_session.DOMINO_SERVER``).
          - `Opened` — 세션으로 연 메일함 — 고른 주소(``url`` — 세션 줄 · 화면 손 · 첨부 자리 · 사번이 읽는다)와 그 메일함 손(``box`` — ``inbox.Mailbox``).
          - `mailbox_hand` — 그 주소 · 세션 파일의 메일함 손(``inbox.Mailbox``) — 세션 파일을 못 읽으면 Stop(3), 주소 꼴이 틀리면 Stop(2).
            - `inbox.Mailbox` — 메일함 하나. 읽기 길의 손은 다 읽기 전용이다 — 메일함을 바꾸는 손은 머리말 「무엇을 하나」 의 이름 붙은 함수들뿐이다.
              - ↑ `MailboxConfigError`
              - ↑ `SessionMissing`
              - ↑ `read_only_patterns`
              - `Mailbox.from_env` — 환경변수로 세운다(머리말 「환경변수」). 틀린 값이면 MailboxConfigError.
                - ↑ `MailboxConfigError`
              - `Mailbox._get` — 읽기 길의 GET — 메일함 안의 ``path``(``/`` 로 시작한다). 서버 뿌리 아래(주소록 · 세션 확인)는 ``_get_server``.
                - `Mailbox._fetch_read_only` — 서버 뿌리 아래 ``path`` 를 읽기 전용으로 잰 꼴일 때만 묻는다 — 읽음 · 메일함을 바꾸는 주소이거나 잰 꼴 밖이면 묻지 않고 ``ChangeRefused``.
                  - ↑ `ChangeRefused`
                  - `Mailbox._open` — 세션 쿠키로 주소 · 요청 하나를 열어 (본문, content-type) 을 낸다 — 넘김 · 401 · 403 은 ``SessionExpired``, 404 는 ``_Missing``, 501 은 ``_NotServed``, 그 밖은 ``MailboxError``.
                    - ↑ `SessionExpired`
                    - `_Missing` — 그 주소에 아무것도 없다(HTTP 404) — 본문 · 조각이 없는 메일.
                    - `_NotServed` — 서버가 그 주소를 안 준다(HTTP 501) — 본문 주소에 501 을 내는 메일이 있다.
                    - ↑ `MailboxError`
              - `Mailbox._get_server` — 읽기 길의 GET — 메일함 밖, 같은 서버의 ``path``(주소록 · 세션 확인).
                - ↑ `Mailbox._fetch_read_only`
              - ↑ `Mailbox._fetch_read_only`
              - ↑ `Mailbox._open`
              - `Mailbox._view` — 보기 · 폴더 하나의 목록을 ``start`` 자리부터 ``count`` 줄 받아 XML 로 푼다 — XML 이 아니면 끊긴 세션이라 ``SessionExpired``.
                - ↑ `Mailbox._get`
                - ↑ `SessionExpired`
                - ↑ `MailboxError`
              - `Mailbox.list` — 받은편지함을 새것부터 ``count`` 통. ``start`` 는 1 부터 센 자리. 하위 폴더로 옮긴 메일은 안 든다(``list_folder``).
                - ↑ `Mailbox._view`
                - `_entry` — 받은편지함 · 폴더 목록의 한 줄(XML) → ``Entry`` — 폴더 보기면 읽음 열의 HTML 조각에서 class 로 안 읽음을 가른다.
                  - `_column` — 목록 한 줄에서 이름이 ``name`` 인 열의 글을 한 줄로 — 없으면 빈 글.
                    - `one_line` — 목록 한 칸의 글 — 안에 든 줄바꿈 글자를 빈칸 하나로 접는다.
                  - `Entry` — 받은편지함 · 폴더 목록의 한 줄. ``unid`` 가 그 메일의 열쇠다.
                    - `Sender` — 보낸 사람 열 하나를 푼 것. 밖의 메일은 주소만 차고 이름 · 영문 이름이 빈다.
                    - `AttachmentName` — 목록의 첨부 이름 하나. ECM 첨부면 ``ecm`` 이 참이고 원래 이름 · 확장자 · 크기를 이름에서 뽑는다 — 문서는 문서함에 있고 ``Mailbox.ecm_key`` 가 그 열쇠를 꺼낸다.
                  - `parse_sender` — 보낸 사람 열을 푼다 — 사내 ``-=spl=-`` · ``-ENG-`` 꼴, 밖의 주소만, 그 밖의 ``이름 <주소>`` 꼴.
                    - `_spl_part` — 사내 보낸 사람 열의 한쪽(한글 · 영문) → (이름, 주소) — 이름은 ``-=spl=-`` 앞이나 꺾쇠 앞, 주소는 꺾쇠 안이고 없으면 빈 글.
                    - ↑ `Sender`
                    - `parse_person` — 사람 하나 — ``이름 <주소>``(공백 · 탭 · 없음) · ``"이름" <주소>`` · 주소만 · Notes 이름 · ``<ID>(<약칭>)``.
                      - `Recipient` — 받는 사람 목록의 한 사람. 주소 없이 오는 사람은 ``notes`` 가 열쇠다 — Notes 이름(``CN=…/O=…``)이나 ``<ID>(<약칭>)``.
                  - `parse_attachment` — 첨부 이름 하나 — ECM 꼴이면 원래 이름 · 확장자 · 크기를 뽑는다.
                    - ↑ `AttachmentName`
              - `Mailbox.list_sent` — 보낸편지함을 ``count`` 통. 받는 사람은 그 목록의 수신인 열을 푼다.
                - ↑ `Mailbox._view`
                - `SentEntry` — 보낸편지함 목록의 한 줄. 받는 사람은 그 목록의 수신인 열을 푼 것이다.
                  - ↑ `Recipient`
                - ↑ `_column`
                - `parse_people` — 받는 사람 글줄(쉼표로 이은 사람들)을 푼다.
                  - ↑ `parse_person`
              - `Mailbox.sent_people` — 보낸 메일 한 통의 받는 사람 · 참조 · 숨은참조 모두 — 웹메일이 넣은 차례대로, 조직은 조직 하나로(``kind`` 가 ``dept``).
                - ↑ `Recipient`
                - ↑ `Mailbox._get`
                - `_unid` — 메일 · 글자에서 unid 를 꺼낸다 — 그 꼴이 아니면 ``MailboxConfigError``.
                  - ↑ `Entry`
                  - ↑ `is_unid`
                  - ↑ `MailboxConfigError`
                - ↑ `_Missing`
                - ↑ `_NotServed`
                - ↑ `MailboxError`
                - ↑ `_charset`
                - `refuse_login` — 받은 글이 끊긴 세션의 로그인 화면이면(``_looks_like_login``) ``SessionExpired(said)`` — 메일함 손의 묻기가 이 한 자리로 가른다.
                  - `_looks_like_login` — 끊긴 세션이 200 으로 준 SSO 화면인가 — 인증 쿠키를 지우거나 SSO 로그인으로 보내는 스크립트로 가른다.
                  - ↑ `SessionExpired`
                - `parse_sent_people` — 보낸 메일의 받는 사람 칸 글(``<열쇠>-=-ITEM-=-<JSON>`` 을 ``-=-SEP-=-`` 로 이은 것 · HTML 이스케이프)을 푼다.
                  - ↑ `Recipient`
              - `Mailbox._view_list` — 보기 목록(``/api/data/collections``) — 이 메일함 손이 사는 동안 한 번만 받는다.
                - ↑ `Mailbox._get`
                - ↑ `_charset`
                - `json_answer` — JSON 답 하나를 푼다 — 못 풀면 로그인 화면이면 ``SessionExpired``(``LOGIN_INSTEAD`` 의 ``what``), 아니면 ``MailboxError`` (``unread`` 와 까닭).
                  - ↑ `refuse_login`
                  - ↑ `MailboxError`
                - ↑ `MailboxError`
              - `Mailbox.view_unid` — 보기 제목으로 그 보기의 unid 를 찾는다 — 메일함마다 다를 수 있어 보기 목록에서 받는다.
                - ↑ `Mailbox._view_list`
                - `_is_folder` — 보기 목록의 한 줄이 보기가 아니라 폴더인가.
                - ↑ `is_unid`
              - `Mailbox.folders` — 쓰는 사람이 지은 폴더 — 보기 목록의 폴더 가운데 시스템 폴더(제목이 ``(`` 로 시작)를 뺀 것, 경로 차례로.
                - `Folder` — 쓰는 사람이 지은 폴더 하나. ``path`` 는 보기 목록의 제목 그대로(``부모\자식``) — 보기는 ``unid`` 로만 열린다.
                - ↑ `Mailbox._view_list`
                - ↑ `_is_folder`
                - ↑ `is_unid`
                - `folder_order` — 폴더 경로의 차례 — 부모 · 자식 마디마다 견준다(「부모 2」가 「부모」와 「부모\자식」 사이에 끼지 않게).
              - `Mailbox.list_folder` — 그 폴더를 새것부터 ``count`` 통 — 줄마다 ``folder`` 에 그 폴더의 경로를 싣는다.
                - ↑ `is_unid`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._view`
                - ↑ `_entry`
              - `Mailbox.list_sent_mail` — 보낸편지함을 받은편지함과 같은 ``Entry`` 꼴로 — 줄의 ``folder`` 는 ``SENT_FOLDER``, ``sender`` 는 그 보기의 수신인 열 (받는 사람)이다.
                - ↑ `Mailbox._view`
                - ↑ `_entry`
              - `Mailbox.list_trash` — 휴지통(``XML_Trash``)을 ``count`` 통 — 줄의 ``folder`` 는 ``TRASH_FOLDER`` 다.
                - ↑ `Mailbox._view`
                - ↑ `_entry`
              - `Mailbox.list_drafts` — 임시보관함을 새것부터 ``count`` 통 — 줄의 ``folder`` 는 ``(Drafts)`` 다.
                - ↑ `Mailbox.view_unid`
                - ↑ `Mailbox._view`
                - ↑ `_entry`
              - `Mailbox.search` — 웹메일 검색 창과 같은 검색 — ``field``(제목 · 본문 · 첨부 이름) 한 칸에 ``words`` 가 든 메일. 내는 것 — (서버가 센 모두 건수, 이 쪽의 줄). 읽음 표시를 안 바꾼다.
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._get`
                - ↑ `_charset`
                - ↑ `json_answer`
                - ↑ `MailboxError`
                - `_found` — 검색 손의 한 줄(JSON)을 푼다.
                  - `Found` — 검색이 낸 한 줄. ``folder`` 는 검색 손이 준 폴더 이름(``[...]`` 를 벗긴 것 · 받은편지함 · 임시보관함 · 휴지통은 빈 글자 · 보낸편지함은 ``SENT_FOLDER``), ``draft`` 는 임시 저장된 메일이다.
                  - ↑ `one_line`
                - ↑ `is_unid`
              - `Mailbox.list_all` — 모든편지함을 정렬 없이 ``count`` 줄 — 그 꼴이 날짜 내림차순이다.
                - ↑ `Mailbox.view_unid`
                - ↑ `Mailbox._view`
                - `Marks` — 모든편지함 한 줄에서 폴더 보기가 못 드는 칸 — 받는 꼴 · 중요도 · 보낸 분 · 읽음 열 글자 그대로. 시각은 창에서 끊는 데만 쓴다.
                  - ↑ `Sender`
                - ↑ `_column`
                - ↑ `parse_sender`
              - `Mailbox.recipient_lists` — 받는 사람 목록 보기를 날짜 내림차순으로 한 장(``count`` 줄) 받아 unid → 받는 사람 목록을 낸다.
                - ↑ `Mailbox.view_unid`
                - ↑ `Mailbox._view`
                - ↑ `parse_people`
                - ↑ `_column`
              - `Mailbox.body` — 본문 — ``kind`` 는 "html"(기본 · 조각 꼴과 상관없는 한 길) · "text"(평문 조각). 그 꼴의 본문이 없거나 서버가 그 주소를 안 주면(501) None.
                - ↑ `MailboxConfigError`
                - ↑ `_unid`
                - ↑ `Mailbox._get`
                - ↑ `_Missing`
                - ↑ `_NotServed`
                - ↑ `_charset`
                - ↑ `refuse_login`
              - `Mailbox.attachment` — 메일에 바로 붙은 첨부 하나를 바이트 그대로 받는다.
                - ↑ `AttachmentName`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._get`
                - ↑ `_unid`
                - ↑ `refuse_login`
              - `Mailbox.body_image` — 본문 ``<img src>`` 하나를 받는다 — 이 메일 서버의 읽기 전용으로 잰 주소(본문 조각 ``Body/M…?OpenElement`` 등)만 묻는다.
                - ↑ `ChangeRefused`
                - ↑ `Mailbox._fetch_read_only`
                - ↑ `refuse_login`
              - `Mailbox.ecm_key` — ECM 첨부 하나가 가리키는 문서함 문서의 열쇠(16 hex 글자)를 낸다(``ecm_note_key``). ECM 첨부가 아니면 ``MailboxConfigError``, 쪽지에 머리나 열쇠가 없으면 ``MailboxError`` — 꼴이 바뀌었거나 다른 쪽지다.
                - ↑ `AttachmentName`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._get`
                - ↑ `_unid`
                - `ecm_note_key` — ECM 쪽지(첨부 「이름(확장자_NKB).html」의 글) → 문서 열쇠 16 hex 글자. 본문 링크의 ``OBJECTID`` 를 먼저, 없으면 머리의 ``objectId`` 를 낸다 — 둘이 다르면 머리 값으로는 문서가 안 열린다.
                  - `_link_key` — 링크 ``OBJECTID``(ASCII 16진) → 문서 열쇠 16 hex 글자. 풀어서 16 hex 가 아니면 None — 머리 값으로 간다.
                - ↑ `refuse_login`
                - ↑ `MailboxError`
              - `Mailbox.session_alive` — 메일을 안 건드리고 세션이 살아 있나 묻는다 — 웹메일이 수십 초마다 부르는 주소다.
                - ↑ `Mailbox._get_server`
                - ↑ `SessionExpired`
                - ↑ `_Missing`
                - ↑ `_charset`
              - `Mailbox.directory_answer` — 사내 주소록의 답을 그대로 낸다(``{dept, user, total}``) — 주소록에 묻는 한 길이고, 안 잰 꼴을 회사에서 재는 자리다.
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._get_server`
                - ↑ `_charset`
                - ↑ `json_answer`
                - ↑ `MailboxError`
              - `Mailbox.find_people` — 사내 주소록에서 이름 · 메일 · 사번으로 찾는다.
                - ↑ `Mailbox.directory_answer`
                - `_person` — 주소록 답의 한 사람(JSON) → ``DirectoryPerson``.
                  - `DirectoryPerson` — 사내 주소록의 한 사람. ``notes`` 는 Notes 이름(``key``) — 받는 사람 목록에서 그 사람을 알아보는 열쇠다.
                    - `DirectoryPerson.level` — 인사 등급(``P5`` · ``E3`` …) — 직급 코드의 표가 먼저이고, 코드가 표에 없으면 직급 이름의 표를 본다.
              - `Mailbox.find_exact` — 받는 사람 목록 · 보낸 사람의 한 꼴로 그 사람만 찾는다 — 주소면 메일이, Notes 이름이면 ``key`` 의 견줄 꼴이, ID (``<영문ID>(<약칭>)``)면 ``user_id`` 가 같은 사람만 낸다.
                - `directory_query` ← company-directory — 한 꼴 → (주소록에 물을 말, 답 가운데 그 사람을 고르는 자). 못 짓는 꼴(빈 글자)이면 None.
                  - `is_notes_name` ← company-directory — Notes 이름의 꼴인가 — ``CN=`` 으로 시작하거나 「@」 없이 「/」 가 든다.
                  - `notes_key` ← company-directory — Notes 이름의 견줄 꼴 — ``CN=`` · ``OU=`` · ``O=`` 표지를 떼고 대소문자를 접는다(약식 ``이름/OU/O`` 와 같게).
                - ↑ `Mailbox.find_people`
              - `Mailbox._org_json` — 조직도 손 하나에 묻고 JSON 을 낸다.
                - ↑ `Mailbox._get_server`
                - ↑ `_charset`
                - ↑ `json_answer`
              - `Mailbox.org_children` — 그 부서 바로 아래 부서들 — ``dept`` 에 회사 값을 주면 맨 위 부서들이다.
                - ↑ `Mailbox._org_json`
                - ↑ `MailboxError`
                - `Dept` — 조직도의 한 부서. ``code`` 는 ``<코드>(<회사 약칭>)`` 꼴의 열쇠, ``parent`` 는 위 부서의 코드(맨 위 부서는 회사 값)다.
              - `Mailbox.org_members` — 그 부서에 바로 든 사람(하위 부서 사람은 안 든다) — 조직도에서 부서를 누를 때의 명단이다.
                - ↑ `Mailbox._org_json`
                - ↑ `MailboxError`
                - ↑ `_person`
              - `Mailbox.org_snapshot` — 회사 조직 전체 — 나무를 층마다 펼치고 부서마다 구성원을 받는다(``ORG_WORKERS`` 만큼 함께). ``tree`` 는 고름 상자의 type, ``company`` 는 그 나무의 회사 값(그룹사면 맨 위 부서의 코드 — ``poscoinc(77)`` 꼴)이다.
                - ↑ `Dept`
                - ↑ `Mailbox.org_children`
                - `DirectoryGap` — 조직도가 물은 것을 못 줬다 — 회사 값으로 부서가 하나도 안 왔다.
                - ↑ `Mailbox.org_members`
                - `OrgChart` — 회사 조직 한 판. ``depts`` 는 코드 → 부서, ``members`` 는 코드 → 그 부서에 바로 든 사람이다.
                  - `OrgChart.find_depts` — 이름 · 코드(회사 약칭 괄호는 붙여도 떼도 된다)가 그 말과 같은 부서 — 같은 것이 없으면 이름에 그 말이 든 부서다.
                  - `OrgChart.path` — 맨 위 부서부터 그 부서까지.
                  - `OrgChart.subtree` — 그 부서와 그 아래 부서 전부 — 나무 차례(위 부서 먼저).
                  - `OrgChart.people` — 그 부서의 사람(``deep`` 이면 하위 부서까지) — ``code`` 가 없으면 회사 전원. 한 사람은 한 번만, 먼저 만난 부서로 낸다.
                    - ↑ `OrgChart.subtree`
                  - `OrgChart.dept_name` — 부서 코드의 이름 — 모르는 코드면 코드 그대로.
              - `Mailbox.org_groups` — 배포그룹 목록 — ``kind`` 는 ``GROUP_KINDS`` 가운데 하나. (그룹 열쇠, 이름) 을 낸다.
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._org_json`
                - ↑ `MailboxError`
              - `Mailbox.group_members` — 배포그룹 하나의 구성원 — (이름, 직급, 부서, 메일). 답이 ``ok`` 가 아니면 ``MailboxError``.
                - ↑ `Mailbox._org_json`
                - ↑ `MailboxError`
              - `Mailbox.mark_read` — ⚠ 메일함을 바꾼다 — 그 메일 하나를 읽음으로. 읽기 길은 이 손을 부르지 않는다.
                - `Mailbox._send_change` — 메일함을 바꾸는 주소를 부른다 — 위 두 손의 꼴만 받는다.
                  - ↑ `ChangeRefused`
                  - ↑ `Mailbox._open`
                  - ↑ `refuse_login`
                  - ↑ `_charset`
                - ↑ `_unid`
              - `Mailbox.mark_unread` — ⚠ 메일함을 바꾼다 — 그 메일 하나를 안 읽음으로(읽음의 되돌리기). 부르는 자리는 ``mark_read`` 와 같다.
                - ↑ `Mailbox._send_change`
                - ↑ `_unid`
              - ↑ `Mailbox._send_change`
              - `Mailbox.folder_tree` — 폴더 나무 — 쓰는 사람이 지은 폴더마다 열쇠 · 경로 · 부모. 바꾸는 손이 이 열쇠를 쓴다.
                - ↑ `Mailbox._get`
                - ↑ `_charset`
                - ↑ `json_answer`
                - `_json_cell` — JSON 보기의 칸 하나 → 글자. 칸은 ``{"text": {"0": 값}}`` 꼴이다 — 값 묶음이면 첫 값.
                - `FolderNode` — 폴더 나무의 한 마디 — 바꾸는 손(만들기 · 옮기기 · 지우기)이 쓰는 열쇠. ``node`` 는 ``newNode<숫자>`` 꼴이고, ``path`` 는 ``Folder.path`` 와 같은 ``부모\자식`` 경로라 그 폴더의 보기(``Folder``)는 경로로 잇는다.
              - `Mailbox.folder_node` — 경로가 같은 폴더의 마디 — 지금 있는 폴더(``folders``)만. 없으면 None.
                - `Mailbox._fresh_folders` — 보기 목록을 새로 받아 지금의 폴더 — 바꾸는 손 앞뒤에는 받아 둔 목록이 낡는다.
                  - ↑ `Mailbox.folders`
                - ↑ `Mailbox.folder_tree`
                - ↑ `MailboxError`
              - `Mailbox.create_folder` — ⚠ 메일함을 바꾼다 — 폴더 하나를 만든다.
                - `_check_folder_name` — 폴더 이름을 웹메일 화면과 같은 자로 거른다 — 빈 이름 · 막는 글자 · 시스템 폴더 이름(꾸밈까지).
                  - ↑ `MailboxConfigError`
                - ↑ `Mailbox._fresh_folders`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox.folder_node`
                - `Mailbox._send_folder` — 폴더 · 휴지통의 바꾸는 주소를 부른다 — 위 손들의 꼴만 받는다.
                  - ↑ `ChangeRefused`
                  - ↑ `Mailbox._open`
                  - ↑ `_charset`
                  - ↑ `refuse_login`
                  - ↑ `MailboxError`
                - ↑ `MailboxError`
              - `Mailbox.move_mails` — ⚠ 메일함을 바꾼다 — 메일들을 폴더 ``to``(경로)로, ``to`` 가 빈 글자면 받은편지함으로 옮긴다.
                - ↑ `_unid`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox.folder_node`
                - ↑ `Mailbox._send_folder`
                - `Mailbox._landed` — 옮긴 자리(폴더 경로 · 빈 글자는 받은편지함)에 든 ``ids`` — 옛 메일은 새것 창 밖에 서므로 다 찾거나 보기가 끝날 때까지 ``VIEW_PAGE_MOST`` 줄씩 받는다.
                  - ↑ `Mailbox._fresh_folders`
                  - ↑ `Mailbox.list`
                  - ↑ `Mailbox.list_folder`
                  - `Pages` — 보기 하나를 쪽마다 받는 고리 — ``for rows in Pages(fetch, start, size)``. ``fetch(count, start)`` 가 한 쪽의 줄들을, ``size(seen)`` 이 이번 쪽에 받을 줄 수를(받은 줄 수 ``seen`` 을 보고 — 0 이하면 상한) 낸다.
                - ↑ `MailboxError`
              - `Mailbox.delete_folder` — ⚠ 메일함을 바꾼다 — 빈 폴더 하나를 지운다.
                - `Mailbox._deletable` — 지울 폴더의 나무 마디 — 없거나 하위 폴더 · 메일이 들었거나 규칙이 그 폴더로 옮기면 ``MailboxConfigError``(아무것도 안 보냈다).
                  - ↑ `Mailbox.folder_node`
                  - ↑ `MailboxConfigError`
                  - ↑ `Mailbox.folders`
                  - ↑ `Mailbox._view`
                  - `Mailbox.rules` — 메일 규칙 전부 — 목록 보기의 unid 마다 그 규칙 문서를 연다(규칙 문서라 메일의 읽음과 무관하다). 읽기만 한다.
                    - `Mailbox._rule_unids` — 메일 규칙 보기에서 규칙 문서의 unid 를 대문자로 모은다.
                      - ↑ `Mailbox._view`
                      - ↑ `is_unid`
                    - `Mailbox._rule_by_unid` — 규칙 문서의 편집 화면을 받아 푼다 — ``EditDocument`` 는 읽기 길 목록 밖이라, 규칙 목록이 낸 unid 로 이 자리에서만 연다.
                      - ↑ `Mailbox._open`
                      - ↑ `_unid`
                      - ↑ `_charset`
                      - ↑ `refuse_login`
                      - `parse_rule_page` — 규칙 편집 화면 → ``Rule``. 갈래 · 폴더는 화면 머리의 ``new FormJS({…})``, 조건 · 맞춤 · 자동전달은 입력 칸의 값이 든다.
                        - ↑ `MailboxError`
                        - `Rule` — 메일 규칙 하나 — 서버가 들어오는(보내는) 메일에 스스로 적용한다.
                - `Mailbox._send_delete` — ⚠ 메일함을 바꾼다 — 폴더 지우기를 메일함 쪽 · 이전메일함 쪽 짝에 차례로 보낸다(웹메일 화면의 [삭제]와 같은 두 요청).
                  - ↑ `Mailbox._send_folder`
                - `Mailbox._refuse_left` — 지운 폴더가 새로 받은 목록에 아직 있으면 ``MailboxError`` — 서버의 OK 만으로는 지웠다고 안 한다.
                  - ↑ `Mailbox._fresh_folders`
                  - ↑ `MailboxError`
              - ↑ `Mailbox._deletable`
              - ↑ `Mailbox._send_delete`
              - ↑ `Mailbox._refuse_left`
              - `Mailbox.trash_mails` — ⚠ 메일함을 바꾼다 — 메일들을 휴지통으로 보낸다(웹메일 목록의 [삭제]). 받은편지함 · 폴더 · 보낸편지함 · 임시보관함 어디의 메일이든 같고 읽음 표시는 그대로다.
                - ↑ `_unid`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._send_folder`
                - `Mailbox._in_trash` — 휴지통 보기에 든 ``ids`` — 다 찾거나 보기가 끝날 때까지 ``VIEW_PAGE_MOST`` 줄씩(``Pages``).
                  - ↑ `Mailbox._view`
                  - ↑ `Pages`
                - ↑ `MailboxError`
              - ↑ `Mailbox._in_trash`
              - `Mailbox.restore_from_trash` — ⚠ 메일함을 바꾼다 — 휴지통의 메일 하나를 되살린다(받은 메일은 받은편지함으로). 답이 ``result`` 참이 아니면 ``MailboxError``.
                - ↑ `_unid`
                - ↑ `Found`
                - ↑ `Mailbox._send_folder`
                - ↑ `MailboxError`
              - `Mailbox.restore_mails` — ⚠ 메일함을 바꾼다 — 휴지통의 메일들을 한 통씩 ``restore_from_trash`` 로 되살린다.
                - ↑ `_unid`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox.restore_from_trash`
                - ↑ `MailboxError`
                - ↑ `Mailbox._in_trash`
                - ↑ `Mailbox._landed`
              - ↑ `Mailbox.rules`
              - `Mailbox.rule` — 규칙 하나 — 규칙 목록에 없는 unid 면 ``MailboxConfigError``(메일 문서를 규칙으로 열지 않게).
                - ↑ `_unid`
                - ↑ `Mailbox._rule_unids`
                - ↑ `MailboxConfigError`
                - ↑ `Mailbox._rule_by_unid`
              - `Mailbox.save_rule` — ⚠ 메일함을 바꾼다 — 규칙을 넣거나(``unid`` 가 빈 글자) 고친다.
                - `Mailbox._rule_form` — 규칙 → 저장 폼의 칸(fmmailrule.js save). 조건 없는 규칙 · 모르는 칸 · 없는 폴더는 묻기 전에 막는다.
                  - ↑ `MailboxConfigError`
                  - ↑ `Mailbox.folder_node`
                - ↑ `Mailbox.rule`
                - ↑ `MailboxConfigError`
                - ↑ `_unid`
                - `Mailbox._send_rule` — 규칙을 바꾸는 POST — 위 손들의 꼴만 받고, 자동전달 칸이 찬 폼은 보내지 않는다.
                  - ↑ `ChangeRefused`
                  - ↑ `Mailbox._open`
                  - ↑ `_charset`
                  - ↑ `refuse_login`
                  - ↑ `MailboxError`
                - ↑ `Mailbox._rule_unids`
                - ↑ `MailboxError`
              - `Mailbox.delete_rule` — ⚠ 메일함을 바꾼다 — 규칙 하나를 지운다.
                - ↑ `Mailbox.rule`
                - ↑ `Mailbox._send_rule`
                - ↑ `Mailbox._rule_unids`
                - ↑ `MailboxError`
              - ↑ `Mailbox._rule_form`
              - ↑ `Mailbox._send_rule`
              - ↑ `Mailbox._rule_unids`
              - ↑ `Mailbox._rule_by_unid`
              - `Mailbox.save_draft` — ⚠ 메일함을 바꾼다 — 새 임시메일 하나를 임시보관함에 저장하고 그 unid 를 낸다.
                - `refuse_draft` — 임시저장 앞의 거름 — 받는 사람이 없거나 첨부가 웹메일이 드는 수를 넘거나 대용량이면 ``MailboxConfigError``(아무것도 안 물었다).
                  - ↑ `MailboxConfigError`
                - `Mailbox._blank_memo` — 빈 쓰기 화면을 받아 (폼 칸, 저장 주소, 이 쓰기의 unid, 화면 HTML) — 화면이 숨은 칸에 든 기본값을 그대로 물려받는다.
                  - ↑ `Mailbox._open`
                  - ↑ `_charset`
                  - ↑ `refuse_login`
                  - `parse_memo_form` — 쓰기 화면(``Memo?openform``) → (숨은 칸의 기본값, 저장 주소, 이 쓰기의 unid). 폼 ``_Memo`` 가 없으면 ``MailboxError``.
                    - ↑ `MailboxError`
                - `refuse_off_step` — 예약발송 시각의 분이 쓰기 화면(``page``)의 분 눈금에 맞나 — 예약이 없으면 안 본다.
                  - ↑ `MailboxError`
                  - ↑ `MailboxConfigError`
                - `with_signature` — 넣은 글 뒤에 서명을 붙인다 — 웹메일 쓰기 화면이 새 메일에 짓는 차례(빈 줄 · 서명 · 빈 줄)와 같다.
                - `Mailbox._signature` — 쓰는 사람의 서명 — 쓰기 화면의 설정이 서명을 켰으면 서명 문서의 본문을 받아 낸다.
                  - `parse_signature_settings` — 쓰기 화면 → (서명 문서 unid, 서명 앞 빈 줄) — 설정이 서명을 껐거나 서명 문서가 없으면 ``None``. 칸 이름의 철자(signatue)는 웹메일 그대로다.
                  - ↑ `Mailbox._get`
                  - ↑ `MailboxError`
                  - `signature_fragment` — 서명 문서의 본문 HTML → 본문에 넣을 조각. 웹메일 편집기(editor.js)가 서명을 넣을 때 벗기는 것(html · head · title · meta · style · body 태그)을 똑같이 벗긴다 — 서명의 style 이 남으면 메일 전체 글꼴을 덮는다.
                  - ↑ `_charset`
                  - `Signature` — 쓰는 사람의 서명 — ``html`` 은 문서 껍데기(html · head · body)를 벗긴 조각, ``add_line`` 은 서명 앞에 빈 줄을 두라는 설정.
                - `Mailbox._upload_draft_files` — 첨부를 업로드 DB 에 올리고 저장 폼에 실을 칸을 낸다.
                  - `_multipart` — 업로드 한 판의 multipart 몸 — (바이트, 경계). 칸은 업로드 화면이 싣는 것 그대로다.
                  - `Mailbox._open_long` — 첨부처럼 오래 걸리는 요청 — 시한만 길고 ``_open`` 과 같다.
                    - ↑ `Mailbox._open`
                  - ↑ `_charset`
                  - ↑ `refuse_login`
                  - ↑ `MailboxError`
                - `draft_form` — 임시저장 폼의 글 · 저장 칸 — 제목 · 본문(MIME) · 메일속성 · 첨부 이름과 크기. 저장 칸 SaveAgent 는 늘 ``SAVE_AGENT_DRAFT`` 다.
                  - `_mime_html` — 본문 HTML → 쓰기 화면 편집기가 MIMEBody 칸에 싣는 꼴(머리 + 빈 줄 + HTML). Body 칸만 채우면 본문이 비어 저장된다.
                - `people_form` — 임시저장 폼의 받는 사람 칸 — 칸마다 Notes 이름 · 인터넷 주소 꼴, 그리고 받는 사람 칸 글(``people_info``) 두 칸.
                  - `people_info` — 받는 사람 칸(``SENT_PEOPLE_FIELDS``) 하나의 글 — ``fields`` 는 칸(to · cc · bcc) → 받는 사람들. 배포그룹만 싣는다.
                - `Mailbox._landed_draft` — 저장 답의 unid(대문자) — 답에 unid 가 없거나 임시보관함 보기에 그 메일이 안 섰으면 ``MailboxError``. 저장 답이 참이어도 보기에 서야 저장한 것이다.
                  - ↑ `is_unid`
                  - ↑ `MailboxError`
                  - ↑ `Mailbox.list_drafts`
                - `Mailbox._post_memo` — 쓰기 폼의 저장 POST — 쓰기 화면의 저장 주소 꼴만 받는다.
                  - ↑ `ChangeRefused`
                  - ↑ `Mailbox._open_long`
                  - ↑ `_charset`
                  - ↑ `refuse_login`
                  - `parse_save_answer` — 저장 답 → 칸들. 답은 JSON 비슷한 글이라(``message_func`` 칸에 함수가 든다) ``result`` · ``unid`` 만 뽑는다.
                    - ↑ `MailboxError`
              - ↑ `Mailbox._landed_draft`
              - ↑ `Mailbox._blank_memo`
              - ↑ `Mailbox._signature`
              - ↑ `Mailbox._upload_draft_files`
              - ↑ `Mailbox._open_long`
              - ↑ `Mailbox._post_memo`
              - ↑ `Mailbox._fresh_folders`
              - ↑ `Mailbox._landed`
              - ↑ `Mailbox._send_folder`
            - ↑ `inbox.MailboxConfigError`
            - ↑ `mailbox_stop`
      - ↑ `mail_stop.Stop`
    - `cmd_folders` — 쓰는 사람이 지은 폴더의 경로를 한 줄씩 찍고 그 수를 붙인다.
      - ↑ `open_mailbox`
    - `cmd_list` — 목록 — 인자가 고른 갈래 하나로 넘긴다: 그 시각부터(``list_since``) · 보낸편지함 받는 사람 거르기(``list_sent_to``) · 보낸편지함 · 임시보관함 · 안 읽음 · 보낸 분으로 걸러 훑기 · 받은편지함이나 폴더의 창 하나.
      - `list_since` — 그 시각(``since`` · 그 시각 포함)부터 온 메일을 받은편지함 · 폴더 · 보낸편지함에 걸쳐 새것부터 한 목록으로 낸다 — 줄은 답의 크기(``OUT_BYTES``)와 ``--count`` 안에서 ``--start`` 째부터, 남으면 다음 ``--start`` 를 댄다.
        - `since_boxes` — --since 가 훑을 상자 — (사람 말로 그 자리, (count, start) → 줄, 그 자리를 이어 보는 list 의 인자). 상자를 안 고르면 받은편지함 · 쓰는 사람이 지은 폴더 모두 · 보낸편지함이고, ``--folder`` · ``--sent`` 는 그 상자 하나다.
          - `mail_find.user_folder` — 경로가 ``path`` 인 폴더(``folder_of``) — 없으면 Stop(2). 「그런 폴더가 없다」 의 말은 이 한 자리다(메일함 스캔이 그 머리를 읽는다).
            - `folder_of` — 쓰는 사람이 지은 폴더 가운데 경로가 ``path`` 인 것(``inbox.Folder``) — 없으면 None. 폴더 나무를 한 번 묻는다.
            - ↑ `mail_stop.Stop`
        - `mail_find.AllMail` — 폴더 줄에 없는 칸(보낸 분 주소 · 받는 꼴)을 모든편지함 줄에서 unid 로 채운다 — 모든편지함은 찾는 줄이 남은 동안만 새것부터 이어 받는다(``FILL_SCAN`` 까지 · 멈추는 자리는 DESIGN.md 「mail_find.py · 모든편지함으로 채우기」). 받은 줄은 명령 하나 동안 든다 — 한 통 찾기 (``find_mails``)와 목록 · 세기가 함께 쓰고, 그 시각까지 받는 쪽(명령의 ``list --since``)은 ``reach_date`` 로 같은 장을 잇는다.
          - ↑ `inbox.Pages`
          - `AllMail.fill` — 줄들 가운데 폴더 줄의 받는 꼴 · 보낸 분을 채워 같은 차례로 낸다 — 다른 줄은 그대로다.
            - `folder_row` — 쓰는 사람이 지은 폴더의 보기에서 온 줄인가 — 그 보기에는 보낸 분 주소와 받는 꼴 칸이 없다.
            - `AllMail._reach` — 찾는 줄(unid → 시각)이 받은 줄에 아직 없고 더 옛 쪽에 있을 수 있는 동안 모든편지함을 다음 쪽까지 받는다.
              - `AllMail._page_until` — ``done()`` 이 참이 되거나 더 받을 것이 없을 때까지(``ended``) 모든편지함을 한 쪽씩 받는다.
                - `AllMail._page` — 모든편지함의 다음 쪽(``Pages`` — 상한 ``FILL_SCAN`` · 빈 쪽 · 서버가 start 를 안 따름에서 멈춘다)을 받아 든다.
          - ↑ `AllMail._reach`
          - `AllMail.reach_date` — 받은 시각(xdate)이 ``since`` 보다 옛 줄이 설 때까지 이어 받는다 — 그 시각까지 다 받았나(옛 줄이 섰거나 보기 끝)를 낸다.
            - ↑ `AllMail._page_until`
          - ↑ `AllMail._page_until`
          - `AllMail._fetch` — 모든편지함 한 쪽 — 이 메일함에 그 보기가 없으면(``list_all`` 이 None) ``absent`` 를 세우고 빈 쪽으로 끝낸다.
          - ↑ `AllMail._page`
        - `sweep_boxes` — 상자들을 함께(``pool``) 새것부터 훑는다 — 상자마다 ``SWEEP_SCAN`` 줄까지 ``SINCE_PAGE`` 줄씩, ``stop`` 이 참인 줄에서 멈추고 ``keep`` 이 고른 줄을 모은다(``sweep_rows``). 내는 것 — (상자마다 ``sweep_rows`` 의 답, unid 로 합친 줄들, 합친 unid(대문자)). 옮기는 도중 두 상자에 선 메일은 앞 상자(받은편지함)의 줄이 선다.
          - `sweep_rows` — 보기 하나를 ``start`` 줄부터 ``limit`` 줄까지(None 이면 끝까지) ``page`` 줄씩 받아 ``keep`` 이 고른 줄을 모은다 — ``stop`` 이 참인 줄이 서면 그 앞에서 멈춘다.
            - ↑ `inbox.Pages`
          - `mail_find.swept` — unid(32자리 대문자)들의 목록 줄을 찾을 자리의 무리마다(``sweep_order``) 훑는다 — (찾은 unid → 목록 줄, 못 찾은 unid). 앞 무리에서 다 찾으면 뒤 무리는 안 훑는다.
            - `sweep_order` — 찾을 자리(``views_of``)를 훑을 무리로 — ``first`` 를 주면 그 보기 하나가 앞 무리, 나머지가 뒤 무리다.
              - `views_of` — 찾을 자리들 — ``--folder`` 를 안 줬으면(None) ``EVERY_VIEW``, 줬으면 그 폴더(``(Drafts)`` · ``(Sent)`` 도) 하나.
            - `sweep_views` — unid(32자리 대문자)들의 목록 줄을 찾을 자리들(``views`` — ``EVERY_VIEW`` 의 이름 · 쓰는 사람의 폴더 경로)에서 찾는다 — (찾은 unid → 목록 줄, 못 찾은 unid). 폴더 줄은 채우지 않은 채 낸다.
              - ↑ `user_folder`
              - `deep_hit` — 보기 하나를 ``start`` 줄부터 끝까지 ``DEEP_PAGE`` 줄씩 받으며(``inbox.Pages``) ``hit`` 이 참을 낸 쪽에서 그 값을 낸다 — 끝까지 없으면 None.
                - ↑ `inbox.Pages`
        - `filled_newest` — 합친 줄 가운데 받은 메일의 폴더 줄을 모든편지함에서 채워(``AllMail.fill``) 새것부터 세운다 — 보낸 메일 줄은 그대로다.
          - ↑ `inbox.SentEntry`
        - `since_shown` — --unread · --from 으로 거른 줄 — 보낸 메일의 사람 칸은 받는 분이라 받은 메일만 거른다.
          - `sieve` — --unread · --from 이 받은 메일 한 줄을 고르는 자 — 보낸 분은 이름 · 영문 이름 · 주소로 본다(폴더 줄의 주소는 모든편지함에서 채운 것).
          - ↑ `inbox.SentEntry`
        - `since_line` — --since 목록의 한 줄 — 받은 메일은 ``entry_line`` 에 든 자리를, 보낸 메일은 「[보냄]」 · 보낸편지함 · 받는 분을 단다.
          - ↑ `inbox.SentEntry`
          - `sent_to` — 보낸편지함 줄의 받는 분 — 그 보기의 수신인 열은 첫 사람만 든다(모두는 ``read`` · 주소록의 ``find --last``).
          - `entry_line` — 받은편지함 · 폴더 목록의 한 줄 — ``where`` 면 날짜 뒤에 든 자리(받은편지함 · 「폴더 <경로>」)를 단다.
            - `where_word` — 메일이 든 자리를 사람 말로 — 받은편지함 · 보낸편지함 · 임시보관함 · 「폴더 <경로>」.
            - `mark_word` — 메일 한 통의 읽음 칸 — 목록 · 찾기 · 미리 보기 줄이 함께 쓴다.
              - `read_word` — 읽음 · 안읽음의 말 — 읽음 칸의 낱말은 이 한 자리다(``gap`` 을 「안」 뒤에 끼운다 — 「이미 안 읽음이다」).
            - `who_sent` — 메일 한 통의 보낸 분 — ``who`` 와 같되, 폴더 줄인데 보낸 분을 하나도 못 읽었으면(폴더 보기에 주소가 없고 모든편지함에서도 못 채웠다) 「없음」이 아니라 「못 채움」이라 말한다.
              - ↑ `mail_find.folder_row`
              - `who` — 보낸 분 한 사람을 사람 말로 — 이름과 주소가 다 있으면 「이름 <주소>」, 아니면 있는 쪽, 둘 다 없으면 「(보낸 분 없음)」.
        - `fit_lines` — 앞에서부터 낼 줄 수 — ``count`` 줄(None 이면 상한 없음)과 ``room`` 바이트(줄마다 줄바꿈 하나를 더해) 안에서. 첫 줄은 늘 낸다.
        - `word_since_tail` — 그 시각부터의 목록 끝 줄들을 말한다 — 머리(수 · 자리별 · 가장 늦은 메일) · 못 내려간 자리나 다 봤다 · 못 채운 수 · 보낸 메일의 받는 분 · 남은 줄과 다음 ``--start``.
        - `since_tally` — 그 시각부터의 목록 끝 줄이 말할 셈(``SinceTally``) — 자리별 수 · 못 내려간 상자 · 모든편지함에만 있는 메일(상자를 안 골랐고 상자가 다 닿았고 모든편지함도 그 시각까지 받았을 때만 센다).
          - ↑ `inbox.SentEntry`
          - ↑ `mail_find.swept`
          - `SinceTally` — 그 시각부터의 목록 끝 줄이 말할 셈.
          - `sieve_word` — --from · --unread 로 거른 것의 말 — 「보낸 분 '…' · 안 읽음」. 안 걸렀으면 빈 글자.
          - `fill_note` — 폴더 줄 가운데 보낸 분을 못 채운 것의 수와 까닭 — 다 채웠거나 받은편지함이면(``filled`` 가 None) 빈 글자.
        - ↑ `mail_find.swept`
      - ↑ `open_mailbox`
      - `since_time` — --since 의 글 → 보기의 시각 꼴(``YYYY-MM-DD HH:MM:SS`` · 서울). ``SINCE_FORMS`` 꼴이 아니면 짐작하지 않고 멈춘다.
        - ↑ `mail_stop.Stop`
      - `list_sent_to` — 보낸편지함을 받는 사람으로 거른다 — 새것부터 ``--start`` 줄에서 ``SENT_TO_SCAN`` 통까지. 목록의 수신인 열에 그 말이 들면 거기서 서고, 아니면 그 메일의 받는 사람 칸(``sent_people`` — 받는 사람 · 참조 · 숨은참조)을 한 통씩 읽어 본다.
        - `recipient_has` — 받는 사람 한 줄의 이름 · 주소 · 열쇠(Notes 이름 · 조직 코드)에 그 말이 드나 — 대소문자는 안 가린다.
        - ↑ `inbox.SessionExpired`
        - ↑ `inbox.MailboxError`
        - `mail_recipients.person_word` ← company-directory — 받는 사람 줄 하나를 한 줄로 — 조직은 이름 뒤에 표지를, 주소가 없으면 열쇠 그대로.
        - `reach_word` — 훑은 범위를 사람 말로 — 끝까지 못 봤으면 그렇게 말한다.
      - `word_sent_box` — 보낸편지함 목록을 말한다 — 줄마다 때 · 받는 분(그 보기의 수신인 열 — 첫 사람만) · 제목 · 번호, 끝 줄에 받는 사람 모두를 보는 길.
        - ↑ `sent_to`
      - `word_drafts_box` — 임시보관함 목록을 말한다 — 줄마다 때 · 제목 · 번호, 끝 줄에 읽는 길.
      - `drafts_box` — 임시보관함 목록 — 이 메일함에 그 보기가 없으면 Stop(1).
        - ↑ `mail_stop.Stop`
      - `view_fetch` — ``--folder`` 가 가리키는 폴더, 없으면 받은편지함의 보기 — ((count, start) → 줄, 사람 말로 그 자리, 폴더 줄을 채운 자리 · 받은편지함이면 None). 폴더 줄은 받아 오는 쪽마다 모든편지함에서 채운다(``AllMail``) — 보낸 분으로 거르기 · 세기가 채운 주소로 선다.
        - ↑ `mail_find.user_folder`
        - ↑ `mail_find.AllMail`
      - `word_sieved` — 걸러 훑은 목록을 말한다 — 고른 줄 가운데 새것 ``--count`` 통과, 끝 줄에 훑은 범위 · 거른 것 · 수 · 못 채운 폴더 줄.
        - ↑ `mail_find.swept`
        - `print_entry` — 목록 한 줄(``entry_line``)을 찍는다.
          - ↑ `entry_line`
        - ↑ `reach_word`
      - ↑ `sweep_rows`
      - ↑ `sieve`
      - ↑ `sieve_word`
      - ↑ `fill_note`
      - `word_window` — 받은편지함 · 폴더의 창 하나를 말한다 — 줄들과, 끝 줄에 수 · 안 읽음 수 · 그 뒤를 보는 길 · 못 채운 폴더 줄.
        - ↑ `print_entry`
    - `check_list_args` — 목록의 인자가 서나 — 세션 · 메일함에 닿기 전에 가린다(``_run``).
      - ↑ `mail_stop.Stop`
      - ↑ `since_time`
    - `cmd_summary` — 받은편지함 · 폴더 하나를 보낸 분별 · 제목 말머리별로 센다 — 통째로 정리할 때 줄 목록 대신 보는 판이다.
      - ↑ `open_mailbox`
      - ↑ `view_fetch`
      - ↑ `sweep_rows`
      - `word_summary` — 요약을 말한다 — 훑은 범위 · 안 읽음 · 보낸 분별 묶음(가장 새것까지) · 그 밖 · 말머리별 묶음 · 다음 걸음.
        - ↑ `who_sent`
      - ↑ `reach_word`
      - `summary_tally` — 줄들을 보낸 분별 · 제목 말머리별(``HEAD_MIN`` 통 이상)로 묶어 센다 — 큰 묶음부터 ``top`` 개. 줄은 새것부터라 묶음의 첫 줄이 그 묶음의 가장 새 메일이다.
        - ↑ `who_sent`
        - `subject_head` — 제목 머리의 대괄호 말머리(``[주간]``) — 답장 · 전달 머리는 건너뛴다.
        - `Group` — 요약의 묶음 하나 — 통 수 · 안 읽음 수 · 가장 새 메일(목록 줄) · 묶음 이름(말머리 묶음만 — 보낸 분 묶음은 빈 글자).
        - `SummaryTally` — 요약이 말할 셈 — 안 읽음 수 · 보낸 분 묶음(보일 것) · 보낸 분 묶음 수 · 보이지 않은 묶음의 (곳 수, 통 수) · 말머리 묶음(보일 것).
      - ↑ `fill_note`
    - `cmd_search` — 찾기 — 낱말 × 보낸 분 × 날짜를 한 번에. 준비(메일함 · 칸 · 보낸 분 · 날짜 ``search_bounds``) 뒤 낱말이 없으면 받은편지함 · 폴더를 보낸 분 · 날짜로 훑고(``search_views``), 있으면 웹메일 검색의 줄을 거른다(``word_search``) → 줄(``show_search_rows``) → 머리 (``word_search_head``) → 색인 밖 새 메일(``recent_hits`` · ``show_recent``) → 끝(``show_search_end``).
      - ↑ `open_mailbox`
      - `sender_match` — --from → 보낸 분 거르기. 주소가 아니면 주소록에 그 이름을 물어 이름이 꼭 같은 살아 있는 사람들을 함께 견준다 — 못 물으면 준 글자로만 견주고 그 까닭을 든다(못 찾았을 때 다음 걸음이 그 까닭을 댄다).
        - `SenderMatch` — 보낸 분 거르기 — 사람이 준 말(``said``)과, 주소록에서 그 이름이 꼭 같은 사람들의 영문 이름 · 주소를 함께 견준다.
          - `SenderMatch.hits` — 준 칸들의 글에 견줄 말 하나가 들었나 — 대소문자를 안 가리고, 여러 낱말인 말은 낱말 차례도 안 가린다.
          - `SenderMatch.word` — 무엇으로 견줬나 — 사람 말로.
        - `company_of` — 이 명령의 주소록 회사 값 — 준 ``--company``(그 인자가 없는 명령이면 빈 값)를 메일 손의 차례(``mail_kept.company_of``)로 고른다.
          - `mail_kept.company_of` ← company-directory — 주소록의 회사 값 — 준 값(``--company``) · ``MAIL_COMPANY`` · ``DEFAULT_COMPANY`` 순.
        - ↑ `inbox.SessionExpired`
        - ↑ `inbox.MailboxError`
      - `search_bounds` — --since · --until → 보기의 시각 꼴(``bound_time``) — (처음, 끝), 안 준 쪽은 빈 글자. 세션 앞의 거름과 찾기 손이 이 한 자리로 셈한다.
        - `bound_time` — --since · --until 의 글 → 보기의 시각 꼴(``YYYY-MM-DD HH:MM:SS`` · 서울). 날짜만 주면 그날의 처음(``end`` 면 끝)이다.
          - ↑ `mail_stop.from_ep`
          - ↑ `since_time`
          - ↑ `mail_stop.Stop`
      - `search_views` — 낱말 없는 찾기 — 받은편지함 · 폴더를 새것부터 보낸 분 · 날짜로 훑어 한 목록으로 낸다(보기마다 ``SWEEP_SCAN`` 줄까지 · ``--since`` 가 있으면 그보다 옛 줄에서 멈춘다). 상한에 막힌 보기는 「거기까지만 봤다」 로 댄다 — 그 앞을 「없다」 로 읽게 두지 않는다.
        - `sender_boxes` — 낱말 없는 찾기가 훑는 상자 — (사람 말로 그 자리, (count, start) → 줄)들. 받은편지함과 쓰는 사람의 폴더 모두다.
        - `swept_sender_boxes` — 상자들을 함께 훑어(``sweep_boxes``) 보낸 분 · 날짜에 걸린 줄을 모은다 — (폴더 줄을 채워 새것부터 세운 줄들, 상자마다 훑은 결과, 채운 ``AllMail``). ``--since`` 가 있으면 그보다 옛 줄에서 멈춘다.
          - `in_bounds` — 서울 시각 ``stamp``(``YYYY-MM-DD HH:MM:SS``)가 찾는 범위(``search_bounds`` 의 처음 · 끝 — 빈 글자면 그쪽은 열렸다) 안인가. 시각을 모르는 줄(빈 글자)은 늘 든다 — 찾는 사람에게 숨은 메일은 아무도 모르는 해이고, 더 든 한 줄은 보인다.
          - ↑ `sweep_boxes`
          - ↑ `mail_find.AllMail`
          - ↑ `mail_find.swept`
        - ↑ `entry_line`
        - `show_views_end` — 낱말 없는 찾기의 끝 — 걸린 것이 없으면 0건 줄과 넓힐 걸음(``print_zero``), 있으면 무엇을 어디서 몇 통 찾았나 · 덜 보였나 · 동명이인 알림(``homonym_note``).
          - `print_zero` — 0건 줄 — 무엇을 어디서 찾았나와 넓힐 다음 걸음. 「메일이 없다」 가 아니라 「이 말로 이 칸에서 못 찾았다」 로 말하게 한다.
            - `search_reach` — 무엇을 어디서 찾았나 — 끝 줄과 0건 줄이 함께 쓴다.
              - `object_particle` — 목적격 조사 — 마지막 글자에 받침이 있으면 「을」, 없으면 「를」(한글이 아닌 끝은 「을」).
            - `widen_steps` — 못 찾았을 때 넓힐 다음 걸음 — 좁힌 것을 하나씩 푼다.
          - ↑ `search_reach`
          - `homonym_note` — 보낸 분 말이 주소록의 여러 사람에게 맞으면 그 사람들을 대고 한 사람만 보는 길을 이른다 — 동명이인의 메일이 섞인 목록을 한 사람의 것으로 읽지 않게.
            - `mail_people.person_line` ← company-directory — 사람 한 줄 — 이름 · 부서 · 직급(인사 등급) · 직책 · 장 · 근무지 · 담당 업무 · 주소. ``dept`` 가 거짓이면 부서를 뺀다.
        - `swept_where` — 훑은 자리를 사람 말로 — 받은편지함 · 폴더 수, 상한에 막힌 상자가 있으면 「거기까지만 봤다」 와 그 상자마다 훑은 수.
          - ↑ `mail_find.swept`
        - ↑ `mail_find.swept`
        - `show_fill_note` — 못 채운 폴더 줄이 있으면 그 한 줄(``fill_note``).
          - ↑ `fill_note`
      - `settle_word_args` — 낱말 검색의 인자를 다듬는다 — 낱말의 앞뒤 빈칸을 걷고, 보일 수(``--count``)를 검색 손이 한 쪽에 내는 줄의 위 안으로. 그 위로 잘린 쪽을 넘긴 수로 「다음 쪽」을 셈하면 남은 줄이 안 보이고 다음 쪽도 안 댄다.
      - `word_search` — 낱말을 칸마다 · 범위마다 검색해 거른 줄을 모은다 — 범위 all 은 서버의 「전체」에 임시보관함을 더해 unid 로 합친다.
        - `search_kept` — 검색 줄 하나가 거르기에 걸리나 — 보낸 분을 주면 받은 메일만(보낸 · 임시 메일의 보낸 분은 쓰는 사람이다 — 받는 사람으로는 list --sent --to), 날짜를 주면 그 서울 시각이 범위 안인 줄만(``in_bounds``).
          - ↑ `in_bounds`
          - `seoul_stamp` — 검색 줄의 시각(UTC ``YYYYMMDDTHHMMSS,cc Z``)을 서울 시각 ``form`` 꼴로 — 기본은 보기 줄의 정렬 칸(``date_sort``)과 견줄 ``YYYYMMDDTHHMMSS``. 못 읽으면 빈 글자.
        - `WordHits` — 낱말 검색이 받은 것 — 걸린 줄(unid → (범위, 줄) · 먼저 받은 것이 선다) · (칸, 범위, 서버가 센 건수)들 · 쪽마다 받은 줄 수 · 보낸 분 · 날짜로 걸렀나.
      - `show_search_rows` — 걸린 줄을 낸다(``search_line``) — 걸렀으면 새것 ``count`` 줄만. 폴더 이름은 폴더 경로로 푼다(``folder_paths``).
        - `folder_paths` — 검색 줄의 폴더 이름 → 폴더 경로(``folders`` 의 ``부모\자식``) — 검색 손은 하위 폴더를 끝 이름만 준다.
        - `search_line` — 검색 줄 하나 — 읽음 · 날짜 · 보낸 분(영문 이름으로 걸렸으면 함께) · 제목 · 첨부 · 자리 · 번호와 read 에 붙일 ``--folder``.
          - ↑ `mark_word`
          - ↑ `seoul_stamp`
      - `word_search_head` — 낱말 검색의 머리 줄 — 칸 · 범위마다 서버가 센 건수, 걸렀으면 걸린 수와 덜 본 몫, 다음 쪽이 있으면 그 걸음.
        - `counted` — 그 사이 찍은 글을 그대로 내보내고 그 바이트 수를 ``["bytes"]`` 에 든다 — 뒤에 낼 본문의 몫을 재는 자리다.
        - ↑ `search_reach`
      - `recent_hits` — 검색 색인에 아직 안 든 새 메일 가운데 낱말 · 보낸 분 · 날짜에 걸리는 것 — 제목 칸을 찾는 첫 쪽에서, 그 범위가 보기로 훑을 수 있을 때만(``recent_subject_hits`` — 검색이 낸 가장 새 줄보다 새 메일). 아니면 빈 목록.
        - ↑ `seoul_stamp`
        - `recent_subject_hits` — 검색 색인이 아직 안 든 새 메일 가운데 제목에 ``words`` 가 든 것 — 새것부터. 보기마다 새것 ``RECENT_SCAN`` 통을 훑어 ``newest``(검색이 낸 가장 새 줄의 서울 시각 · 0건이면 빈 글자)보다 새 메일만 낸다 — 그보다 옛 메일은 검색의 다음 쪽에 있다.
        - ↑ `in_bounds`
      - `show_recent` — 색인 밖 새 메일의 줄(``recent_line``)과, 있으면 그 까닭 한 줄.
        - `recent_line` — 색인 밖 새 메일 한 줄 — 읽음 · 날짜 · 보낸 분(보낸 메일은 받는 분) · 제목 · 첨부 · 자리 · 번호와 read 에 붙일 ``--folder``.
          - ↑ `who`
          - ↑ `who_sent`
          - ↑ `mark_word`
          - ↑ `where_word`
      - `show_search_end` — 낱말 검색의 끝 — 아무것도 없으면 0건 줄과 넓힐 걸음(``print_zero``), 있으면 동명이인 알림(``homonym_note``). 끝에 맞추기의 꼴.
        - ↑ `print_zero`
        - ↑ `homonym_note`
    - `check_search_args` — 찾기의 인자 — 세션 · 메일함에 닿기 전에 가린다(``_run``).
      - ↑ `mail_stop.Stop`
      - ↑ `search_bounds`
    - `JoinWords` — 자리 낱말 여럿을 빈칸으로 이은 한 말로 둔다 — 사람의 말이 셸에서 빈칸마다 갈라 와도 따옴표로 준 것과 같은 말을 찾는다.
    - `cmd_read` — 메일 한 통을 읽는다 — 머리(``show_read_head``) · 본문 앞의 줄(``show_body_lead`` — 그림 · 숨긴 글 · 본문 시작)을 한 덩이로 센 뒤 남은 크기 안의 본문 한 쪽(``show_body_page``)과 끝 줄(``show_read_end``)을 낸다.
      - ↑ `open_mailbox`
      - `mail_find.find_mail` ← company-directory — unid 한 통의 목록 줄(Entry) — ``find_mails`` 의 한 통 꼴.
        - `find_mails` — unid 들의 목록 줄(Entry)을 준 차례대로 찾는다 — ``--folder`` 를 주면 그 폴더(``(Drafts)`` · ``(Sent)`` 도), 아니면 받은편지함 · 폴더 · 임시보관함 · 보낸편지함 차례로(``sweep_order`` 의 무리마다 ``sweep_views``). ``first`` 는 그 보기들 가운데 끝까지 먼저 훑을 하나다 — 거기서 찾은 메일은 그 보기의 줄로 선다.
          - ↑ `unid_shape`
          - ↑ `swept`
          - `NotFound` — 찾는 메일이 훑은 보기에 없다(``find_mails``) — 부르는 명령이 제 말을 덧붙일 수 있게 가른 Stop.
          - `searched_word` — ``sweep_views`` 가 훑은 자리를 사람 말로 — 훑은 보기만 댄다.
          - `fill_found` — 보기에서 찾은 줄(``sweep_views`` 의 ``got``)을 준 차례(``wanted``)대로 모아 폴더 줄을 모든편지함에서 채운다 — (채운 줄들, 채운 ``AllMail``). 못 찾은 번호는 건너뛴다 — 못 찾음을 멈춤으로 낼지는 부르는 쪽이 채우기 앞에서 가른다(``find_mails``).
            - ↑ `AllMail`
      - ↑ `counted`
      - `show_read_head` — 읽기의 머리 — 제목 · 사람(보낸 메일은 받는 사람 칸, 받은 메일은 보낸 분 · 받으신 칸 · 함께 받은 사람, 임시메일은 보낸 분) · 날짜 · 읽음 · 자리 · 첨부. 받는 사람 명단은 읽는 손가락(``sent_people_of`` · ``together_of``)이 받는다.
        - `show_sent_people` — 보낸 메일 한 통의 받는 사람 칸들을 말한다 — 못 읽었으면 목록의 받는 분(``fallback``)과 그 까닭. 숨은참조가 비면 있었는지 모른다고.
        - `sent_people_of` — 보낸 메일 한 통의 받는 사람 · 참조 · 숨은참조를 읽어 칸마다 보일 꼴로 낸다.
          - ↑ `inbox.SessionExpired`
          - ↑ `inbox.MailboxError`
          - `SentPeople` — 보낸 메일 한 통의 받는 사람 칸들을 보일 꼴 — 칸마다의 ``FieldView`` 와 못 읽은 까닭(읽었으면 빈 글자).
          - `field_views` — 칸 → 명단을 칸마다 보일 꼴(``FieldView``)로 센다 — 조직은 뒤에 있어도 보인다(누구에게 가나를 가르는 줄이다).
            - ↑ `mail_recipients.person_word`
            - `FieldView` — 받는 사람 한 칸을 보일 꼴 — 칸 · 사람 수 · 조직 수 · 보일 줄((차례 번호, 한 줄)들) · 사람을 앞 ``PEOPLE_SHOWN`` 명까지만 보였나.
          - `sent_people_by_field` — 받는 사람을 칸(``to`` · ``cc`` · ``bcc``)별로 — 칸을 모르는 사람은 받는 사람으로 둔다.
            - `mail_recipients.field_of` ← company-directory — 명단 줄 하나가 든 칸 — 칸을 모르는 줄은 받는 사람 칸이다.
        - ↑ `who`
        - ↑ `who_sent`
        - `role_word` — 쓰는 사람이 받은 메일 한 통을 어느 칸으로 받았나 — 받는 꼴 열(``Entry.role`` · 폴더 줄은 ``AllMail`` 이 채운다). 모르면 모른다고 그 까닭과 함께 말한다 — 짐작한 칸을 안 낸다.
          - ↑ `mail_find.folder_row`
        - `show_received_people` — 받은 메일 한 통의 함께 받은 사람을 말한다 — 명단을 못 읽었으면 그 까닭이다.
          - `mail_recipients.together_why` ← company-directory — 함께 받은 사람을 못 읽은 까닭을 사람 말로.
          - ↑ `mail_recipients.person_word`
        - `together_of` — 받은 메일 한 통의 함께 받은 사람 — (``mail_recipients.Together`` · 못 받았으면 None, 못 받은 까닭 · 받았으면 빈 글자). 끊긴 세션은 명령 전체가 다시 세운다 — 「못 읽었다」로 낮추지 않는다.
          - `mail_recipients.received_together` ← company-directory — 받은 메일 한 통의 함께 받은 사람을 받는 사람 목록 보기의 새것 ``RECIPIENT_SCAN`` 줄에서 꺼낸다.
            - `Together` — 받은 메일 한 통의 함께 받은 사람 — 명단 · 못 읽은 꼴(``NO_VIEW`` · ``NOT_IN_VIEW`` · ``EMPTY`` · 읽었으면 빈 글자) · 훑은 줄 수.
          - ↑ `inbox.SessionExpired`
          - ↑ `inbox.MailboxError`
        - ↑ `mark_word`
        - ↑ `where_word`
        - `print_attachments` — 메일 한 통의 첨부를 번호와 함께 한 줄씩 찍는다 — 문서함(ECM) 첨부는 크기와 열쇠를 꺼내는 다음 걸음을 단다.
      - `mail_text` — 메일 한 통의 본문을 글자로 — (글 · 없으면 None, 걷은 숨긴 덩이 수, 그림 주소). HTML 한 길(``box.body``)이 먼저고 없으면 평문 조각이다 — read · read-many 가 함께 쓴다.
        - `readable` — 본문을 읽을 글자로 다듬는 한 자리 — 줄바꿈을 ``\n`` 으로 고르고 찌꺼기 문자(폭 없는 문자 · BOM · soft hyphen 같은 서식 문자와 줄바꿈 · 탭 밖의 제어 문자)를 걷는다.
          - `visible.invisible` — (걷은 글, 걷은 수). 서식 문자(폭 없는 문자 · 방향 뒤집기 · 태그 문자)와 줄바꿈 · 탭 밖의 제어 문자를 걷는다.
        - `body_view` — 메일 HTML → ``visible.Visible`` 통째 — 글(``readable`` 을 지난 것) · 숨긴 덩이 수 · 그림 주소. 그려지는 그림은 글에 「[그림 N]」 으로 선다.
          - `visible.parse` — HTML 한 편 → `Visible`(꼴은 머리말). `numbered` 가 거짓이면 그림 자리가 번호 없는 「[그림]」 이고 주소는 그대로 `images` 에 든다.
            - `_TableParser` — HTML → 표 꼴의 줄. 무엇이 보이나는 `_Parser` 그대로고 줄을 적는 갈고리만 다르다 — 숨긴 요소 안에서도 표의 뼈대는 따라가 열이 안 밀리게 한다.
              - `_Table` — 표 하나 — 행을 칸 목록으로 모아 한 줄씩 낸다.
                - `_Table._fill` — 지금 행의 다음 자리가 위에서 세로로 합친 칸이면 그 글자로 채워 나간다.
                - `_Table.cell` — 칸 하나를 지금 행에 넣는다 — 가로로 합친 수만큼 되풀이하고, 세로로 합쳤으면 아래 행에 채울 글자로 남긴다.
                  - ↑ `_Table._fill`
                - `_Table.close_row` — 지금 행을 닫아 칸을 TABLE_SEP 로 이은 한 줄로 낸다 — 빈 행은 안 내고, 이 행이 안 닿은 세로 합친 칸도 한 행을 센다.
                  - ↑ `_Table._fill`
              - `_TableParser._write` — 글 조각을 열린 칸이 있으면 그 칸에, 없으면 본문에 적는다.
              - `_TableParser._close_cell` — 열린 칸이 있으면 모은 글자를 한 줄로 접어 표에 넣고 닫는다.
              - `_TableParser._close_table` — 맨 안쪽 표를 닫아 그 줄들을 내놓는다 — 칸 안에 든 표면 ROW_SEP 로 이어 그 칸에, 아니면 본문에 줄로 적는다.
                - ↑ `_TableParser._close_cell`
                - ↑ `_TableParser._write`
              - `_TableParser._open` — 여는 태그가 표의 뼈대(표 · 행 · 칸)를 열거나 줄을 가른다 — 안 그리는 태그 안에서는 안 본다.
                - ↑ `_Table`
                - ↑ `_TableParser._close_cell`
                - `_span` — colspan · rowspan 값 — 수가 아니거나 1 보다 작으면 1.
                - ↑ `_TableParser._write`
              - `_TableParser._close` — 닫는 태그가 칸 · 행 · 표를 닫거나 줄을 가른다 — 안 그리는 태그 안에서는 안 본다.
                - ↑ `_TableParser._close_cell`
                - ↑ `_TableParser._close_table`
                - ↑ `_TableParser._write`
              - `_TableParser._image` — 그림 자리 표지를 앞뒤 빈칸과 함께 지금 칸이나 본문에 적는다.
                - ↑ `_TableParser._write`
              - `_TableParser._text` — 보이는 글 한 조각을 적는다 — 표 안 · 칸 밖의 글자(표 제목)는 표의 한 줄로 따로 세운다.
                - ↑ `_TableParser._write`
              - `_TableParser.text` — 다 읽은 뒤의 표 꼴 글 — 안 닫힌 표를 모은 데까지 닫고, 줄마다 겹친 빈칸을 하나로, 잇단 빈 줄을 하나로.
                - ↑ `_TableParser._close_table`
            - `_Parser` — HTML → 보이는 글. 요소마다 (숨김 · 글자색 · 바탕) 을 쌓아 내려 보낸다.
              - `_Parser._break` — 블록 경계 — 글 없이 잇단 경계는 한 줄바꿈이다.
              - `_Parser._line_open` — 지금 쓰는 자리가 줄 머리인가 — 앞에 글 없이 줄바꿈(또는 문서 머리)만 있다.
              - `_Parser._open` — 여는 태그가 긋는 줄 경계.
                - ↑ `_Parser._break`
              - `_Parser._close` — 닫는 태그가 긋는 줄 경계.
                - ↑ `_Parser._break`
              - `_Parser._image` — 그려지는 그림의 자리 표지를 적는다.
              - `_Parser._text` — 보이는 글 한 조각을 적는다.
                - ↑ `_Parser._line_open`
              - `_Parser.text` — 다 읽은 뒤의 글 — 줄마다 겹친 빈칸을 하나로, 잇단 빈 줄을 하나로.
              - `_Parser._top` — 지금 요소의 (숨김, 글자색, 바탕) — 쌓인 것이 없으면 안 숨김 · 색 없음 · 흰 바탕.
              - `_Parser._rules_for` — `<style>` 에서 모은 단순 선택자 규칙 가운데 이 요소(태그 · 클래스 · id)에 걸리는 선언을 합친다.
              - `_Parser.handle_starttag` — 여는 태그 하나 — 안 그리는 태그는 건너뛸 깊이로 세고, 그 밖은 줄 경계와 그림 자리를 적은 뒤 규칙 · 스타일로 가린 (숨김 · 글자색 · 바탕) 을 쌓는다.
                - ↑ `_Parser._open`
                - ↑ `_Parser._top`
                - `_hard_hidden` — 그 요소와 아래가 통째로 안 보이나 — 스타일 · 속성으로 가른다.
                  - `_length` — CSS 길이를 px 로 어림 — 모르는 단위는 None. 0 은 단위와 상관없이 0 이다.
                - ↑ `_Parser._rules_for`
                - `_decls` — 선언 글 → {속성: 값}. 값의 `!important` 는 뗀다 — 남기면 `visibility:hidden !important` 같은 값이 숨김 판정에 안 걸린다.
                - ↑ `_Parser._image`
                - `_color` — CSS 색 값 → (R, G, B) · 「transparent」 · 모르면 None — 이름 몇 · #hex · rgb()/rgba() 만 읽고, 거의 투명한 rgba 는 투명이다.
              - `_Parser.handle_startendtag` — `<tag/>` 꼴 — 여는 태그로 받고, 브라우저가 그 자리에서 닫는 요소만 곧바로 닫는다.
                - ↑ `_Parser.handle_starttag`
                - `_Parser.handle_endtag` — 닫는 태그 하나 — 안 그리는 태그면 건너뛸 깊이를 풀고(`<style>` 이면 모은 규칙을 싣고), 그 밖은 줄 경계를 긋고 그 요소까지 쌓인 것을 걷는다.
                  - `_Parser._load_rules` — `<style>` 글에서 단순 선택자(태그 · .클래스 · #id 와 그 짝)의 규칙만 골라 `rules` 에 더한다.
                    - ↑ `_decls`
                    - `body` — 본문 HTML 한 편 → JSON 으로 답하는 명령이 실을 `Visible` — 표 꼴로 풀고 보이지 않는 문자까지 걷은 글이다.
                      - ↑ `parse`
                      - `Visible` — 본문 HTML 을 푼 결과 — 보이는 글 · 걷은 숨긴 덩이 수 · 주석 글 · 그림 주소(꼴은 머리말).
                      - ↑ `invisible`
                  - ↑ `_Parser._close`
              - ↑ `_Parser.handle_endtag`
              - `_Parser.handle_data` — 글 조각 하나 — 안 그리는 태그 · 숨긴 요소 안이면 버리고, 바탕과 같은 색이면 걷어 숨긴 덩이로 세고, 보이면 적는다.
                - ↑ `_Parser._top`
                - ↑ `_Parser._text`
              - `_Parser.handle_comment` — 빈 주석이 아니면 그 글을 `comments` 에 모으고 본문에는 안 적는다.
              - ↑ `_Parser._load_rules`
            - ↑ `Visible`
          - ↑ `readable`
      - `show_body_lead` — 본문 앞의 줄 — 본문 그림이 있으면 그 줄(``show_body_images``), 걷은 숨긴 글이 있으면 그 수, 그리고 본문 시작 표지.
        - `show_body_images` — 본문 그림의 줄 — ``save`` 면 받아(``save_body_images``) 그림마다 결과를 대고(``word_image``), 아니면 수와 다음 걸음만 댄다.
          - `save_body_images` — 본문 그림들을 곁의 ``body_images`` 로 받아 임시 폴더(``SAVE_ROOT`` / unid / ``IMAGES_DIR``)에 남긴다 — 그림마다의 결과(dict). 그림 한 장을 메일함이 안 주면 그 그림만 안 받은 것으로 서고(``body_images.Refused``), 끊긴 세션은 명령 전체를 멈춘다.
            - ↑ `inbox.SessionExpired`
            - ↑ `inbox.MailboxError`
            - `body_images.Refused` — 앱 손이 그 주소를 안 받는다 — 사내 밖 · 읽기 전용으로 잰 꼴이 아니다 · 서버가 거절했다.
            - `body_images.save` — 그림을 ``out_dir`` 에 ``image-<no>.<확장자>`` 로 남긴다 — 계약은 머리말.
              - `_seed` — (씨앗 폴더, ``_image_head``) — 그 부품을 든 첫 폴더를 ``sys.path`` 앞에 얹고 싣는다.
              - `_data_uri` — base64 data 주소의 바이트를 푼다 — base64 가 아니거나 못 풀면 Refused.
                - ↑ `Refused`
              - ↑ `Refused`
              - `_fit_page` — 씨앗의 눈금 셈 ``_vision.fit_page``, 못 실으면 None. ``_seed()`` 가 자리를 얹은 뒤에 부른다.
              - `_shrink_all` — (원본, 임시 결과) 짝들을 씨앗의 줄이는 손 한 번으로 줄인다 → 못 돌렸거나 시한에 끊었으면 그 까닭, 돌았으면 "". 어느 짝이 구워졌나는 결과 파일이 있나로 가른다 — 그 손은 다 구운 것만 결과 이름으로 옮긴다.
          - `word_image` — 받은 그림 하나의 결과를 한 줄로 — 남긴 자리 · 꼴 · 치수(줄였으면 받은 치수) · 덧말, 앞 그림과 같으면 그 번호, 안 받았으면 그 까닭.
      - `show_body_page` — 본문 한 쪽 — ``start`` 자부터 ``most`` 자 · ``room`` 바이트 안(``fit_body``)을 내고, 다 안 냈으면 어디까지인가와 다음 ``--start`` 를 댄다.
        - `fit_body` — 본문을 start 째 글자부터 most 자까지 내되 room 바이트를 안 넘는 끝 자리 — 한글은 한 자가 3 바이트라 글자 수로는 못 맞춘다.
      - `show_read_end` — 읽기의 끝 줄 — 읽기가 읽음을 안 바꾼다는 것과, 안 읽은 메일이면 그렇다는 것.
    - `cmd_read_many` — 메일 여러 통의 앞부분을 한 세션에 준 차례대로 낸다 — 번호를 세우고(``read_many_order``) 찾아(``read_many_found``) 머리 (``show_read_many_head``) · 통마다 블록(``show_peeks``) · 끝 줄(``read_many_tally`` → ``word_read_many_tail`` → ``end_read_many``)을 낸다.
      - `read_many_order` — read-many 의 번호 차례 — (준 번호들 · 대문자, 겹친 것을 처음 선 자리에 한 번만 둔 차례). ``--max-chars`` 가 1 밑이거나 번호가 없거나 ``--start`` 가 그 차례 밖이면 Stop(2).
        - ↑ `mail_stop.Stop`
        - `read_many_tokens` — read-many 에 준 번호 낱말들 — 인자마다 쉼표 · 빈칸 · 줄바꿈으로 가른 것(빈 것은 뺀다). 세션 앞의 거름과 명령 손이 이 한 자리로 푼다.
      - `read_many_found` — 보일 번호(``rest``) 가운데 번호 꼴인 것의 메일 — (메일함 · 없으면 None, unid → 채운 목록 줄, 채운 ``AllMail`` · 없으면 None). 번호 꼴인 것이 없으면 메일함을 안 연다.
        - ↑ `inbox.is_unid`
        - ↑ `open_mailbox`
        - ↑ `mail_find.fill_found`
        - ↑ `mail_find.swept`
      - `show_read_many_head` — read-many 의 머리 한 줄을 낸다 — 몇 통 가운데 어디부터 · 무엇을 싣나. 낸 바이트 수를 낸다(뒤 블록의 몫을 셈한다).
        - ↑ `counted`
      - `show_peeks` — 번호마다 블록(``peek_block``)을 차례대로 답의 크기(``room``) 안에서 낸다 — 본문은 ``inbox.ORG_WORKERS`` 통씩 함께 받는다 (``peek_text``). (보인 (번호, 메일 줄 · 못 찾았으면 None)들, 크기에 닿아 멈춘 차례 · 다 보였으면 None, 자른 본문이 있나).
        - `peek_text` — read-many 의 한 통 본문 — (글, 걷은 숨긴 덩이 수, 못 받은 까닭 · 받았으면 빈 글자). 그 한 통의 본문만 못 받은 것(서버 오류 · 시한)은 그 통의 줄에 까닭으로 서고 나머지는 계속 읽는다.
          - ↑ `mail_text`
          - ↑ `inbox.SessionExpired`
          - ↑ `inbox.ChangeRefused`
          - ↑ `inbox.MailboxConfigError`
          - ↑ `inbox.MailboxError`
        - `peek_block` — read-many 의 한 통 — (줄들, 본문을 다 보였나). 찾은 메일은 머리 한 줄 · 받으신 칸과 첨부 · 본문 앞 ``most`` 자 세 줄이고, 못 찾은 번호 · 번호 꼴이 아닌 것은 그 까닭 한 줄이다.
          - ↑ `mail_token.token`
          - ↑ `inbox.is_unid`
          - `peek_head` — read-many 의 머리 한 줄 — 읽음 · 때 · 자리 · 보낸 분 · 제목 · 메일 번호. 보낸 메일은 「[보냄]」 과 받는 분(그 보기의 수신인 열 — 첫 사람만), 임시메일은 「[임시]」 다.
            - ↑ `who`
            - ↑ `mark_word`
            - ↑ `where_word`
            - ↑ `who_sent`
          - `peek_marks` — read-many 의 둘째 줄 — 받은 메일은 받으신 칸 · 첨부 수, 보낸 · 임시 메일은 첨부 수다.
            - ↑ `role_word`
          - `one_line` — 본문 조각을 한 줄로 — 줄바꿈(과 빈 줄 · 줄 앞뒤 빈칸)을 ``PEEK_BREAK`` 하나로. 메일의 글이 줄을 열어 다음 메일의 머리처럼 서지 못한다.
          - `peek_end` — 본문을 앞에서 ``most`` 자까지 싣되 한 줄로 편 글이 ``room`` 바이트를 안 넘는 끝 — 한 글자는 늘 싣는다.
            - ↑ `one_line`
          - `lines_bytes` — 줄들이 답에서 차지하는 바이트 — 줄마다 줄바꿈 하나를 더한다.
        - ↑ `mail_token.token`
        - ↑ `lines_bytes`
      - `end_read_many` — 끝 줄을 낸다 — 찾은 메일이 하나도 없으면 그 줄을 멈춤(2 — read 의 못 찾음과 같은 종료 값)으로 낸다.
        - ↑ `mail_stop.Stop`
      - `word_read_many_tail` — read-many 의 끝 줄들 — 셈 한 줄 · 못 찾은 번호 · 번호 꼴 · 자른 본문 · 보낸 메일의 받는 분 · 못 채운 폴더 줄 · 멈춘 자리의 걸음.
        - ↑ `mail_find.searched_word`
        - ↑ `fill_note`
      - `read_many_tally` — 보인 블록(``show_peeks`` 의 줄들)을 셈한다 — 안 읽음은 받은 메일만 센다(보낸 · 임시 메일에는 읽음이 없다).
        - `ReadManyTally` — read-many 의 끝 줄이 말할 셈 — 읽은 · 안 읽은 메일 수 · 못 찾은 번호 수 · 번호 꼴이 아닌 것의 수 · 겹친 번호 수 · 보인 첫 · 끝 차례 · 모두 몇 통 · 크기에 닿아 멈춘 차례(다 보였으면 None) · 자른 본문이 있나 · 보낸 메일이 있나 · 폴더 줄 채우기(없으면 None).
        - ↑ `inbox.is_unid`
    - `check_read_many_args` — read-many 의 인자 — 번호 꼴이 아닌 것은 그 줄에 「아니다」로 서고 나머지는 읽지만, 하나도 번호 꼴이 아니면 세션 앞에서 멈춘다.
      - ↑ `read_many_tokens`
      - ↑ `inbox.is_unid`
      - ↑ `mail_stop.Stop`
    - `cmd_attachment` — 메일 한 통의 첨부를 보이고(``show_attachments``) 고른 것(``attachment_picks``)을 받는다 — 문서함 첨부는 열쇠만 대고 (``show_ecm_keys``) 파일 첨부는 받아 남긴다(``save_attachments``). 첨부가 없거나 ``--save`` 를 안 줬으면 보이기만 한다.
      - ↑ `open_mailbox`
      - ↑ `mail_find.find_mail`
      - `show_attachments` — 첨부 명령의 머리 — 제목 · 보낸 분 줄, 그 아래 첨부 목록(없으면 「첨부가 없다」), ``--save`` 를 안 줬으면 받는 길 한 줄.
        - ↑ `who_sent`
        - ↑ `print_attachments`
      - `attachment_picks` — ``--save`` 값이 고른 첨부 — (첨부 번호, 첨부)들. 번호는 목록이 보인 그 번호(1 부터)이고 ``all`` 은 다다.
        - ↑ `mail_stop.Stop`
      - `show_ecm_keys` — 고른 문서함(ECM) 첨부마다 문서 열쇠를 대고 여는 길을 말한다 — 쪽지라 파일로 안 남긴다.
      - `save_attachments` — 고른 파일 첨부를 받아 폴더(``attachment_dir``)에 남기고 남긴 자리를 댄다.
        - `attachment_dir` — 첨부를 남길 폴더 — ``--out`` 을 줬으면 그 폴더, 아니면 임시 폴더 아래 ``SAVE_ROOT`` / 그 메일의 unid.
        - `attachments.file_names` — 한 메일 · 글에서 파일로 남길 첨부 전부 ``{번호: 서버가 준 이름}`` → ``{번호: 저장할 파일 이름}`` — 계약은 머리말.
          - `safe_name` — 서버가 준 첨부 이름 → 한 폴더 안의 파일 이름. 보이지 않는 문자와 맨 앞의 점은 걷고 금지 글자는 ``_`` 로 바꾼다 — 명령이 내는 경로가 보이지 않는 문자를 걷은 글이라, 여기서도 걷어야 낸 경로와 남긴 파일이 같다.
            - ↑ `visible.invisible`
          - `_same` — 두 파일 이름이 한 파일을 가리키나를 견주는 꼴 — 윈도는 대소문자와 끝의 점 · 빈칸을 안 가린다.
        - `attachments.keep` — 첨부 하나를 ``out_dir / file_name`` 에 남기고(폴더가 없으면 만든다) (경로, ``note``)를 낸다.
          - `note` — 받은 첨부 하나를 무엇으로 읽나 이르는 말 — 머리말의 여섯 가운데 하나.
            - `wrapped` — 감겼으면 참 · 평문이면 거짓, 머리로 못 가르는 확장자면 None.
              - `ext_of` — 이름의 확장자 — 소문자, 점 없이. 없으면 빈 글자.
            - ↑ `ext_of`
            - `reader_exts` — 감긴 문서를 읽는 손이 받는 확장자(소문자, 점 없이). 그 손이 내준 표를 못 읽거나 비었으면 None — 받는 꼴을 모른다.
    - `draft_map` — --help 의 지도 — 두 표에서 짓는다.
      - `Start` — 임시메일 짓기의 출발 하나 — 웹메일의 화면 하나다.
      - `Change` — 임시메일 짓기의 바꿀 것 하나 — 손가락 하나다.
      - `flag_of` — 인자 이름(``dest``)을 명령줄 깃발 꼴(``--a-b``)로.
    - `cmd_draft` — 임시메일을 짓는다 — 출발 하나(DRAFT_STARTS)에 바꿀 것(DRAFT_CHANGES) 아무 조합을 한 번에 얹어 임시보관함에 저장한다.
      - ↑ `open_mailbox`
      - ↑ `Start`
      - `draft_on_screen` — 편집 화면 출발의 길 — 계획을 짓고(``plan_on_screen``) ``--preview`` 면 보이기만, 아니면 화면에서 저장한다(``save_on_screen``).
        - `plan_on_screen` — 편집 화면에서 지을 임시메일 — 저장하지 않는다.
          - `screen_origin` — 편집 화면 출발의 원래 것 — (원래 메일 · 임시메일 고치기면 None, 지금 임시보관함의 unid 들 · 답장 · 전달 · 재사용이면 None). 임시메일 고치기는 그 unid 가 임시보관함에 있어야, 답장 · 전달 · 재사용은 원래 메일이 임시메일이 아니어야(재사용은 보낸 메일이어야) 한다 — 아니면 Stop(2).
            - `draft_unids` — 임시보관함 새것 ``DEEP_PAGE`` 통의 unid 를 대문자로 모은다.
            - ↑ `mail_stop.Stop`
            - ↑ `mail_find.find_mail`
          - `screen_changes` — 편집 화면에 얹을 바꿀 것의 인자 — 메일속성 · 제목 · 글(HTML · 평문) · 바꿀 조각 · 비울 칸 · 붙일 · 뺄 첨부. 받는 사람은 따로 잇는다.
            - `read_body` — 글 파일 — (나갈 HTML, 평문, HTML 파일이었나). 평문은 줄바꿈만 살려 싸고, HTML 조각은 그대로 싣고 평문을 거기서 뽑는다.
              - ↑ `mail_stop.Stop`
              - `floor_text` — 모델이 쓴 글 파일 하나 — 사내 앱 명령의 한 바닥(``ep_command.text_file`` — BOM · 끝 줄바꿈을 걷고 UTF-8 이 아니면 다음 걸음을 댄다)으로 읽어, 그 바닥의 멈춤을 이 명령의 멈춤(종료 2)으로 옮긴다.
                - ↑ `mail_stop.from_ep`
              - `html_to_text` — HTML 을 보이는 글자만으로 — ``body_view`` 의 글.
                - ↑ `body_view`
              - `is_document` — 제 모양을 가진 문서 꼴(``<body>`` 가 든 HTML)인가 — 감싸지 않는 쪽이다.
            - `options_of` — 준 메일속성만 — {칸: 값}. 칸은 ``inbox.DraftOptions`` 의 이름이다.
              - `send_at_of` — --send-at → 저장할 예약 시각(``YYYY-MM-DD HH:MM``) · 빈 글자(예약을 푼다) · None(안 줬다). 꼴 · 지난 시각을 메일함에 닿기 전에 막는다 — 화면은 지난 시각을 [보내기] 때에야 막아, 저장해 둔 예약이 보낼 때 멈춘다.
                - ↑ `mail_stop.Stop`
            - `swaps_of` — 바꿀 조각들 — [옛 글, 새 글]. 파일로 준 것은 BOM · 끝 줄바꿈을 걷는다(편집기 · 파워셸이 붙인 것이라 글이 아니다).
              - ↑ `floor_text`
              - ↑ `mail_stop.Stop`
            - `attach_paths` — 붙일 파일들의 절대 경로 — 없는 파일 · 같은 이름 두 번이면 Stop. 편집 화면에서 붙일 것은 대용량(``inbox.DRAFT_ATTACH_BIG`` 넘음)도 멈춘다 — 웹메일 임시저장이 안 든다.
              - ↑ `Start`
              - ↑ `mail_stop.Stop`
          - `draft_addresses` — 칸(``to`` · ``cc`` · ``bcc``)마다 준 주소 — 앞 칸에 든 주소는 뒤 칸에서 뺀다.
            - `addresses` — ``--to`` 같은 칸의 주소들 — 쉼표 · 줄로 나눈 것도 받고, 파일은 한 줄에 하나(``#`` 뒤는 버린다). 같은 주소는 한 번.
              - ↑ `floor_text`
          - `book_people` — 칸(``to`` · ``cc`` · ``bcc``)마다의 주소를 웹메일 받는 사람으로 잇는다 — (칸 → 사람들, 받아 둔 조직도 판의 날짜). 주소는 사람 찾기와 한 자(``draft_people`` — 받아 둔 조직도부터)로 잇고, 사람으로 안 선 주소 가운데 부서 주소 꼴(``DEPT_MAIL``)은 조직도의 부서로 잇는다(``dept_people`` — 조직도는 처음 걸린 칸에서 한 번 받는다). 칸 안의 차례는 준 주소의 차례다(``in_given_order``). 그래도 안 선 주소가 있으면 멈춘다(``refuse_unbooked`` — ``outside`` 는 사외 주소를 어떻게 하나의 말이다).
            - ↑ `company_of`
            - `mail_people.kept_book` — 받아 둔 조직도의 주소 → 사람들(``chart_book``)과 그 판의 날짜. 받아 둔 판이 없으면 빈 표 · 빈 날짜다 — 전사를 받는 데 오래 걸려 새로 받지 않는다.
              - `mail_kept.cached_org` ← company-directory — 받아 둔 조직도 — ``days`` 안에 받은 판이 있으면 (OrgChart, 받은 시각 글자), 없거나 낡았거나 깨졌으면 None. ``people`` 이면 사람까지 받은 판만, 아니면 사람까지 받은 판과 부서 나무만 받은 판 가운데 나중에 받은 것을 본다 — 나무만 받은 판을 사람이 없는 회사로 읽지 않고, 나무가 낡아 새로 받은 나무를 옛 사람의 판이 가리지 않게. 서버에 묻지 않는다.
                - `org_cache_path` — 고름 · 회사 값 하나의 받아 둔 조직도 파일 — 나의 회사 고름은 ``org-<회사>.json``, 다른 고름은 ``org-<고름>-<회사>.json``, 부서 나무만 받은 판은 그 곁의 ``….tree.json``. 이름에 못 쓰는 글자는 첨부 가름 손(``attachments``)의 자로 바꾼다.
                  - ↑ `cache_dir`
                - `written_at` — 파일을 쓴 시각 — 없으면 0.
                - `_read_org` — 받아 둔 파일 하나를 조직도로 되살린다 — (OrgChart, 받은 시각 글자). 없거나 낡았거나 칸이 안 맞으면 None.
                  - ↑ `inbox.OrgChart`
                  - ↑ `inbox.Dept`
                  - ↑ `inbox.DirectoryPerson`
              - `chart_book` ← company-directory — 조직도 한 판의 주소 → 사람들(퇴직자 빼고) — 주소로 사람을 잇는 표다.
            - `draft_people` — 주소 → 웹메일 받는 사람(``inbox.DraftPerson``). 그 주소의 사람이 꼭 하나일 때만 든다(``address_people``) — 둘째 값이 못 든 주소다.
              - `mail_people.address_people` ← company-directory — 주소 → 그 주소의 주소록 사람(퇴직자 빼고)이 꼭 하나이고 받는 사람으로 서면(``can_receive``) 그 사람, 아니면 None.
                - `can_receive` ← company-directory — 주소록의 한 사람이 받는 사람으로 서나 — 메일 주소와 Notes 이름이 다 있어야 한다(웹메일 화면은 받는 사람을 Notes 이름으로 다시 연다).
              - `inbox.DraftPerson` — 임시메일의 받는 사람 하나 — ``notes`` 는 Notes 이름(SendTo 칸), ``email`` · ``name`` 은 InetSendTo 칸. ``notes`` 를 비우면 웹메일 화면이 다시 열 때 사람으로 안 선다.
            - `dept_book` — 부서 주소 → 그 부서(``inbox.Dept``) — 받아 둔 조직도로, 없으면 ``open_box()`` 의 메일함으로 조직도를 받아 둔 뒤. 조직 하나를 받는 사람으로 넣는 자리다(부서원을 풀지 않는다 — 보내는 순간의 구성원에게 간다).
              - `mail_kept.load_org` ← company-directory — 회사 조직 한 판 — 받아 둔 판(``cached_org``)이 있으면 그것을, 없거나 ``fresh`` 면 조직도에서 새로 받아 남긴다(``fetch_org``). 내는 것 (OrgChart, 받은 시각 글자). ``open_box()`` 가 세션으로 연 메일함이고, 받아 둔 판으로 서면 부르지 않는다.
                - ↑ `cached_org`
                - `fetch_org` — 조직도에서 회사 조직 한 판을 새로 받아 남긴다 — (OrgChart, ``FRESH_WORD``). 못 남겨도 받은 것으로 답한다(``keep_org``).
                  - `keep_org` — 조직도 한 판을 그 고름 · 회사 값의 파일에 남긴다 — 못 남기면 경고 한 줄을 내고 그대로 간다(다음 판이 새로 받는다).
                    - ↑ `org_cache_path`
                    - `org_record` — 조직도 한 판의 받아 두는 꼴 — 꼴 번호 · 회사 · 부서 · 사람(``ORG_CACHE_BLANK`` 칸은 비운다).
            - `dept_people` — 사람으로 안 선 주소(``gone``) 가운데 조직도의 부서 주소(``depts`` — ``dept_book``)를 조직 하나의 받는 사람으로 — (그 받는 사람들, 그래도 안 선 주소들). 부서원을 풀지 않는다 — 보내는 순간의 구성원에게 간다.
              - ↑ `inbox.DraftPerson`
            - `in_given_order` — 받는 사람들을 준 주소(``mails``)의 차례로 — 준 주소에 없는 사람은 뒤에 둔다.
            - `refuse_unbooked` — 받는 사람으로 안 선 주소가 하나라도 있으면 그 주소를 대고 Stop(2) — 말없이 빼고 저장하면 사람이 모르는 채 그 사람 없이 나간다.
              - ↑ `mail_stop.Stop`
          - `group_people` — --to-group · --cc-group · --bcc-group → 칸마다 배포그룹(``inbox.DraftPerson`` · group). 그룹은 갈래마다의 목록에서 이름이 꼭 하나로 서야 든다 — 안 서면 Stop. 구성원을 풀지 않는다(보내는 순간의 구성원에게 간다).
            - `mail_people.split_kind` ← company-directory — 배포그룹 값 앞의 갈래 머리(``직책:`` · ``jobtitle:`` …)를 뗀다 — (찾을 갈래들, 그룹 이름). 머리가 없으면 갈래 셋 다다.
            - `mail_people.group_lists` ← company-directory — 찾을 그룹들(``wants`` — (칸, 갈래들, 이름))이 걸친 갈래마다의 배포그룹 목록 — 갈래 → [(열쇠, 이름)]. 함께 묻는다.
            - ↑ `company_of`
            - `mail_people.one_group` ← company-directory — 갈래들(``kinds``)의 목록에서 이름이 같은 배포그룹 하나 — (갈래, 열쇠, 이름)(``group_hits``). 꼭 하나로 안 서면 그 까닭 글을 낸다(``group_miss``). ``missing_next`` 는 어느 갈래에도 없을 때 부르는 명령이 사실 뒤에 붙이는 제 걸음이다(「 — 」 부터).
              - `group_hits` — 갈래들(``kinds``)의 목록에서 이름이 같은 배포그룹들 — [(갈래, 열쇠, 이름)]. 이름이 꼭 같은 것이 먼저고, 없으면 빈칸 · 괄호를 안 보고(``inbox.squash``) 견준다.
              - `group_miss` — 배포그룹 하나로 안 선 까닭 — 걸린 갈래(``kinds``)가 없으면 「없다」에 부르는 쪽의 걸음(``missing_next``)을, 여럿이면 갈래를 붙여 다시 달라고 한다.
            - ↑ `mail_stop.Stop`
            - ↑ `inbox.DraftPerson`
        - `show_screen_plan` — 편집 화면에서 지을 것을 다 보인다 — 화면이 채울 것과 이 부름이 바꿀 것.
          - ↑ `Start`
          - ↑ `who_sent`
          - ↑ `where_word`
          - `warn_unmeasured` — 회사 화면으로 안 돌려 본 손가락을 썼으면 한 줄로 알린다 — 저장한 판을 사람에게 꼭 보이게.
            - `unmeasured_used` — 이 부름이 쓴 손가락 가운데 이 출발에서 회사 화면으로 아직 안 돌려 본 것의 이름 — 출발 자신의 몫까지.
              - ↑ `Start`
              - ↑ `Change`
              - `given_changes` — 준 손가락 — 그 인자에 값이 하나라도 든 바꿀 것.
                - ↑ `Change`
          - `show_people` — 받는 사람 한 칸을 이름 · 주소로 한 줄씩 보인다 — PEOPLE_SHOWN 명까지, 넘으면 남은 인원을 댄다.
            - `rest_of_people` — 받는 사람 한 칸이 PEOPLE_SHOWN 을 넘으면 남은 인원을 댄다.
          - `show_options` — 메일속성을 보인다 — 새 메일은 켠 칸만, 편집 화면은 바꿀 칸마다 켠다 · 끈다.
          - `show_body` — 지을 메일의 글을 ``word`` 머리 아래 찍는다 — HTML 이면 그대로 나간다는 말과 거기서 뽑은 글자를 낸다.
        - `save_on_screen` — 편집 화면에서 짓고 [임시저장]한다 — 일감(``screen_ops``)을 화면 손에 한 번에 넘기고(``screen_save``) 임시보관함에 섰나를 본 뒤 (``refuse_unsaved``) 저장한 줄 · 갈라짐(``word_screen_saved``) · 판 · 메일속성 · 띄운 창 · 다음 걸음(``word_screen_next``)을 낸다.
          - `screen_save` — 일감을 임시 파일에 써서 화면 손의 edit 를 부른다(``draft_hand``) — 손의 답(JSON). 임시 파일은 부름이 끝나면 지운다.
            - `draft_hand` — 보내는 손(``draft_send.js``)을 부른다 — 쓰는 사람의 Edge 에서 웹메일 편집 화면을 다룬다.
              - ↑ `mail_stop.Stop`
              - `HandStopped` — 보내는 손(``draft_send.js``)이 멈췄다 — ``Stop`` 의 글 · 걸음에 더해 손의 말만(``hand_said`` — 걸음 없이)과 그 멈춤이 [보내기]를 누르기 전이었나(``unpressed`` — 손의 종료 값이 ``HAND_UNPRESSED`` 에 들었나)를 든다.
          - `screen_ops` — 화면 손(draft_send.js edit)에 넘길 일감 — 계획에서 바꿀 것만(빈 칸은 뺀다). 받는 사람은 주소, 부서는 주소 → 이름, 배포그룹은 열쇠 · 이름.
          - ↑ `draft_unids`
          - `refuse_unsaved` — 화면 손이 저장했다고 한 unid 가 임시보관함(``after``)에 없으면 Stop(1) — 손의 말이 아니라 메일이 선 자리로 가린다.
            - ↑ `mail_stop.Stop`
          - `word_screen_saved` — 편집 화면 저장의 첫 줄 — 무엇을 어디에 저장했나, 임시메일 고치기인데 임시보관함에 새 메일이 함께 섰으면 그 경고.
            - ↑ `Start`
          - ↑ `warn_unmeasured`
          - `show_draft_state` — 편집 화면이 든 판 하나를 보인다 — 받는 사람 열쇠를 받아 둔 조직도로 풀고(``screen_names``) 글자를 뽑아(``html_to_text``) 판을 말한다(``word_draft_state``).
            - `word_draft_state` — 편집 화면이 든 판을 말한다 — 칸마다 사람(푼 이름) · 제목 · 글(화면의 HTML 에서 뽑은 글자 ``text`` · 뒤의 확인 열쇠가 한도 안에 들게 끊는다) · 첨부.
              - ↑ `counted`
              - ↑ `rest_of_people`
              - ↑ `fit_body`
            - `screen_names` — 편집 화면 판의 칸마다 (사람 수, 앞 ``PEOPLE_SHOWN`` 명의 ``ScreenName``) — 열쇠(Notes 이름)를 받아 둔 조직도(``got`` — 없으면 None)의 사람 · 부서로 풀고, 배포그룹 열쇠는 그 꼴(``GROUP_KEY``)에서 이름과 갈래를 뽑는다.
              - ↑ `inbox.notes_key`
              - `ScreenName` — 편집 화면이 든 받는 사람 열쇠 하나를 푼 것 — 갈래(``SCREEN_KINDS`` 의 열쇠)와 그 갈래가 말할 조각들.
            - ↑ `mail_kept.cached_org`
            - `screen_files` — 편집 화면 판의 첨부 「이름:바이트」 → (이름, KB) — 1KB 밑도 1 이다.
            - ↑ `html_to_text`
          - ↑ `company_of`
          - `show_saved_options` — 저장한 판의 메일속성 — 켜진 칸만 한 줄로. 하나도 없으면 아무것도 안 낸다(대개의 메일).
          - `show_on_screen` — 저장한 임시메일을 쓰는 사람의 Edge 에 편집 화면으로 띄워 둔다 — 사람이 거기서 바로 확인하고 [보내기]를 누른다.
            - ↑ `draft_hand`
            - ↑ `mail_stop.Stop`
          - `word_screen_next` — 편집 화면 저장 뒤의 걸음 — 받는 사람이 없으면 못 보낸다는 경고와 더하는 길, 있으면 확인 열쇠와 보내기 · 고치기의 길.
      - `draft_new` — 새 메일의 길 — 계획을 짓고(``plan_draft``) ``--preview`` 면 보이기만, 아니면 쓰기 화면의 요청으로 저장하고(``save_new``) 저장한 판 · 서명 · 창 · 다음 걸음을 낸다.
        - `plan_draft` — 저장할 임시메일을 짓는다 — 저장하지 않는다.
          - `mail_parts` — 새 메일의 인자 → 제목 · 글 · 첨부(이름, 바이트) · 받는 사람 셋. 빠진 값 · 없는 파일은 ``check_draft_args`` 가 앞서 막았다.
            - ↑ `read_body`
            - ↑ `attach_paths`
            - ↑ `draft_addresses`
          - ↑ `options_of`
          - `inbox.DraftFile` — 임시메일에 붙일 파일 하나 — 이름과 바이트.
          - ↑ `book_people`
          - ↑ `group_people`
        - `show_draft_plan` — 새 메일 한 통을 다 보인다 — 받는 사람 · 참조 · 숨은참조의 명단 · 제목 · 글 · 첨부.
          - ↑ `show_people`
          - ↑ `show_options`
          - ↑ `show_body`
        - `save_new` — 새 메일 계획을 임시보관함에 저장하고 그 unid 를 낸다 — 첨부 자리는 메일함 주소의 파일 번호(사번)가 정한다(없으면 Stop(2)). 메일함 손이 막은 설정 오류는 그 말로 Stop(2).
          - ↑ `mail_stop.Stop`
          - `marked_text` — 나갈 HTML 조각을 표지 달린 div 로 감싼다 — 임시메일을 다시 고칠 때 그 자리만 갈아 끼우게. 문서 꼴(``<body>`` 가 든 것 · 아뜰리에가 지은 지면)은 손대지 않는다 — body 안을 감싸면 그 문서의 배치 규칙이 어긋날 수 있다.
            - ↑ `is_document`
          - `inbox.DraftOptions` — 임시메일의 메일속성 — 쓰기 화면의 체크 칸. ``send_at`` 은 예약발송 시각(``YYYY-MM-DD HH:MM`` · 분은 쓰기 화면의 눈금 ``SEND_AT_STEP_IN_PAGE`` — ``save_draft`` 가 그 화면에서 읽어 가린다) · 빈 글자면 예약하지 않는다.
            - `DraftOptions.form` — 저장 폼에 실을 칸 — 쓰기 화면의 saveDoc 이 싣는 값 그대로다.
          - ↑ `inbox.MailboxConfigError`
        - `show_saved_tail` — 저장한 새 메일의 글 뒤에 붙은 것(서명)을 저장한 판에서 읽어 보인다 — 서명은 웹메일 설정이 켰을 때 저장하며 붙고, 켰는지는 이 PC 가 미리 모른다.
          - ↑ `inbox.SessionExpired`
          - ↑ `inbox.MailboxError`
          - ↑ `html_to_text`
        - ↑ `show_on_screen`
    - `check_draft_args` — 임시메일 짓기의 인자가 서나 — 세션 · 메일함에 닿기 전에 가린다(``_run``). 출발과 바꿀 것이 표에 맞나, 빠진 값 · 없는 파일 · 같은 글로 바꾸기 같은 인자의 꼴을 다 본다.
      - ↑ `Start`
      - ↑ `mail_stop.Stop`
      - ↑ `mail_find.unid_shape`
      - ↑ `given_changes`
      - ↑ `Change`
      - ↑ `draft_addresses`
      - ↑ `send_at_of`
      - ↑ `read_body`
      - ↑ `swaps_of`
      - ↑ `attach_paths`
    - ↑ `Start`
    - ↑ `object_particle`
    - `cmd_preview_send` — 보낼 임시메일을 웹메일 편집 화면에서 지금 판 그대로 보이고 send-draft 에 줄 확인 열쇠를 낸다 — 안 보낸다.
      - ↑ `open_mailbox`
      - `draft_in_box` — 그 unid 가 지금 임시보관함에 있나 — 보내는 손은 편집으로 여는데, 받은 메일을 편집으로 열면 읽음이 되고 [보내기]가 그 메일을 다시 낸다.
        - ↑ `draft_unids`
      - ↑ `mail_stop.Stop`
      - ↑ `draft_hand`
      - ↑ `show_draft_state`
      - ↑ `company_of`
    - `cmd_send_draft` — 판정은 손의 말이 아니라 메일이 선 자리다 — 보낸편지함에 섰어야 「보냈다」. 손은 뒤에 뜬 알림 · 늦은 자동저장으로 엉뚱한 말을 낼 수 있어, 손이 「안 보냈다」고 해도 보낸편지함에 섰으면 보낸 것으로 알린다 — 다시 보내 두 번 나가지 않게.
      - ↑ `open_mailbox`
      - ↑ `draft_in_box`
      - ↑ `mail_stop.Stop`
      - ↑ `draft_hand`
      - ↑ `HandStopped`
      - `sent_box_has` — 그 unid 가 보낸편지함 새것 ``SENT_CHECK_ROWS`` 통 안에 섰나.
    - `preview_pair` — 미리 보기 — 메일함을 열어 짝(``PAIRS[verb]``)의 계획을 세우고 바뀔 판을 보인다.
      - `Pair` — 바꾸기 짝 하나가 한 꼴(``preview_pair`` · ``apply_pair``)에 대는 것 — 짝마다 다른 조각과 말 몫이다.
        - `unsettled` — 바꿀 것이 늘 있는 짝의 「이미 그 판인가」 — 늘 거짓이다.
      - `folder_change` — 폴더를 만들거나 지운다 — 만든 폴더(메일함 손이 다시 봐서 선 것) · 지웠으면 None.
      - `folder_done` — 폴더를 만들거나 지운 「됐다」 줄.
      - `folder_parts` — 폴더 만들기 · 지우기의 확인 열쇠 재료.
      - `folder_plan` — 폴더 만들기 · 지우기의 계획 — 만들 경로(부모 경로 아래)와 그 폴더가 이미 있나, 지울 폴더는 지금 있는 폴더인가(``user_folder`` — 없으면 Stop). 지울 폴더가 비었나는 메일함 손이 실행에서 다시 본다.
        - `FolderPlan` — 폴더 만들기 · 지우기의 계획 — 만드나(``create``) · 그 경로 · 만들 경로가 이미 있나.
        - ↑ `mail_find.folder_of`
        - ↑ `mail_find.user_folder`
      - `folder_shown` — 폴더 만들기 · 지우기의 미리 보기 줄.
      - `mark_change` — 읽음을 바꾸고 그 메일을 다시 읽는다 — 다시 읽은 판(Entry). 다시 읽어도 안 바뀌었으면 Stop(1).
        - ↑ `mail_find.find_mail`
        - ↑ `mail_stop.Stop`
        - ↑ `mark_word`
      - `mark_done` — 읽음을 바꾼 「됐다」 줄.
        - ↑ `read_word`
      - `mark_parts` — 읽음 바꾸기의 확인 열쇠 재료 — 메일 번호 · 바꿀 쪽 · 제목 · 지금 읽음.
      - `mark_plan` — 읽음 바꾸기의 계획 — 메일 한 통을 찾고(``find_mail``) 바꿀 쪽을 고른다(``--read`` 면 읽음으로).
        - `MarkPlan` — 읽음 바꾸기의 계획 — 그 메일과 바꿀 쪽(참이면 읽음으로).
        - ↑ `mail_find.find_mail`
      - `mark_settled` — 바꿀 쪽이 이미 지금 상태인가 — 읽음으로 바꿀 메일이 이미 읽음 · 안 읽음으로 바꿀 메일이 이미 안 읽음.
      - `mark_shown` — 읽음 바꾸기의 미리 보기 줄 — 메일 머리, 바꿀 것이 있으면 바뀔 판과 폴더 메일의 알림.
        - ↑ `who_sent`
        - ↑ `where_word`
        - ↑ `mark_word`
        - ↑ `read_word`
      - `mark_state` — 이미 바라는 판의 말 — 「이미 읽음이다」 · 「이미 안 읽음이다」.
        - ↑ `read_word`
      - `move_change` — 메일들을 옮긴다 — 메일함 손이 다시 봐서 다 들었나를 본다.
      - `move_done` — 옮긴 「됐다」 줄.
      - `move_parts` — 옮기기의 확인 열쇠 재료 — 받을 자리와 메일마다의 (unid, 지금 자리).
      - `move_plan` — 옮기기의 계획 — 받을 폴더가 지금 있나(``user_folder`` — 받은편지함이면 안 본다)를 먼저 묻고 메일들을 찾는다(``find_mails``).
        - ↑ `mail_find.user_folder`
        - `MovePlan` — 옮기기의 계획 — 받을 폴더 경로(빈 글자면 받은편지함)와 옮길 메일들.
        - ↑ `mail_find.find_mails`
      - `move_shown` — 옮기기의 미리 보기 줄 — 머리와 메일마다 한 줄.
        - `pair_row` — 미리 보기 · 되살린 자리 줄의 메일 한 통 — 읽음 · 제목 · 보낸 분(· 자리) · 번호.
          - ↑ `where_word`
          - ↑ `mark_word`
          - ↑ `who_sent`
      - `restore_change` — 메일들을 되살린다 — 받은편지함이 아닌 자리로 돌아온 메일의 unid(대문자)들. 휴지통에서 다 빠졌나는 메일함 손이 다시 본다.
      - `restore_done` — 되살린 「됐다」 줄 — 받은편지함에 든 수, 다른 자리로 돌아온 메일이 있으면 그 알림과 메일마다 한 줄.
        - ↑ `who_sent`
      - `restore_parts` — 되살리기의 확인 열쇠 재료 — 메일들의 unid.
      - `restore_plan` — 되살리기의 계획 — 휴지통에서 찾은 메일들(``find_trashed``).
        - `find_trashed` — 휴지통에서 unid 들의 줄(Entry)을 준 차례대로 찾는다 — 다 찾거나 보기가 끝날 때까지 ``DEEP_PAGE`` 줄씩. 하나라도 없으면 Stop.
          - ↑ `mail_find.unid_shape`
          - ↑ `inbox.Pages`
          - ↑ `mail_stop.Stop`
      - `restore_shown` — 되살리기의 미리 보기 줄 — 머리 · 메일마다 한 줄 · 돌아올 자리의 알림.
        - ↑ `pair_row`
      - `rule_change` — 규칙을 지우거나 저장한다 — 저장했으면 (그 번호, 다시 읽은 규칙), 지웠으면 None. 지운 규칙이 목록에서 빠졌나는 메일함 손이 다시 본다.
      - `rule_done` — 규칙을 지우거나 저장한 「됐다」 줄 — 저장했으면 다시 읽은 규칙과 그 번호.
        - `rule_line` — 메일 규칙 하나를 사람 말 한 줄로 — 편지함 · 조건(일치 「=」 · 포함 「∋」) · 동작 · 옮길 폴더, 자동전달이면 경고를 붙인다.
      - `rule_parts` — 규칙의 확인 열쇠 재료 — 지우기는 지금 규칙, 넣기 · 고치기는 지금과 바꿀 규칙의 줄과 번호.
        - ↑ `rule_line`
      - `rule_plan` — 규칙 넣기 · 고치기 · 지우기의 계획 — 지우기는 지금 규칙만, 넣기 · 고치기는 칸을 합쳐(``rule_conditions`` · ``rule_folder``) 메일함 손이 저장 앞에서 막을 것을 먼저 막고(``refuse_rule``) 새 규칙을 짓는다(``new_rule``). 자동전달 규칙은 고치지 않는다(``refuse_forwarding``).
        - `RulePlan` — 규칙의 계획 — 지금 규칙(``old`` — 넣기면 None)과 저장할 규칙(``new`` — 지우기면 None).
        - `refuse_forwarding` — 고칠 규칙이 자동전달 규칙이면 Stop(2) — 이 손은 자동전달 칸을 늘 비워 저장하므로 고치면 전달이 말없이 사라진다.
          - ↑ `mail_stop.Stop`
        - ↑ `inbox.Rule`
        - `rule_conditions` — 새 규칙의 조건 — 준 칸만 바꾸고 안 준 칸은 지금 규칙(``base``)의 값을 둔다.
        - `rule_folder` — 새 규칙의 받을 폴더 — 폴더로 옮기는 규칙만 든다(준 값 · 없으면 지금 규칙의 값).
        - `refuse_rule` — 메일함 손(``inbox.Mailbox._rule_form``)이 저장 앞에서 막는 것을 미리 보기에서 먼저 막는다 — 열쇠를 낸 뒤 실행에서 멈추지 않게. 조건이 없으면 · 폴더로 옮기는 규칙에 폴더가 없거나 그런 폴더가 없으면 Stop(2).
          - ↑ `mail_stop.Stop`
          - ↑ `mail_find.folder_of`
        - `new_rule` — 저장할 규칙 — 받는 상자 · 일치 여부는 준 값, 없으면 지금 규칙(``base``)의 값.
          - ↑ `inbox.Rule`
      - `rule_shown` — 규칙의 미리 보기 줄 — 지우기 · 고치기(지금과 바꿀) · 넣기의 줄과 서버가 규칙을 쓰는 법.
        - ↑ `rule_line`
      - `trash_change` — 메일들을 휴지통으로 보낸다 — 메일함 손이 다시 봐서 다 들었나를 본다.
      - `trash_done` — 휴지통으로 보낸 「됐다」 줄.
      - `trash_parts` — 휴지통으로 보내기의 확인 열쇠 재료 — 메일마다의 (unid, 지금 자리).
      - `trash_plan` — 휴지통으로 보내기의 계획 — 보낼 메일들(``find_mails``).
        - ↑ `mail_find.find_mails`
      - `trash_shown` — 휴지통으로 보내기의 미리 보기 줄 — 머리와 메일마다 한 줄.
        - ↑ `pair_row`
      - ↑ `open_mailbox`
      - ↑ `mail_token.token`
      - `show_lines` — 줄들을 차례로 낸다.
      - `word_preview_end` — 미리 보기의 끝 줄 — 이미 그 판이면(``settled``) 그 말 하나, 아니면 열쇠(``key``) 줄과 맺음 줄.
    - `apply_pair` — 실행 — 메일함을 열어 짝(``PAIRS[verb]``)의 계획을 다시 세우고, 이미 그 판이면 그렇다고만 낸다.
      - ↑ `Pair`
      - ↑ `folder_change`
      - ↑ `folder_done`
      - ↑ `folder_parts`
      - ↑ `folder_plan`
      - ↑ `folder_shown`
      - ↑ `mark_change`
      - ↑ `mark_done`
      - ↑ `mark_parts`
      - ↑ `mark_plan`
      - ↑ `mark_settled`
      - ↑ `mark_shown`
      - ↑ `mark_state`
      - ↑ `move_change`
      - ↑ `move_done`
      - ↑ `move_parts`
      - ↑ `move_plan`
      - ↑ `move_shown`
      - ↑ `restore_change`
      - ↑ `restore_done`
      - ↑ `restore_parts`
      - ↑ `restore_plan`
      - ↑ `restore_shown`
      - ↑ `rule_change`
      - ↑ `rule_done`
      - ↑ `rule_parts`
      - ↑ `rule_plan`
      - ↑ `rule_shown`
      - ↑ `trash_change`
      - ↑ `trash_done`
      - ↑ `trash_parts`
      - ↑ `trash_plan`
      - ↑ `trash_shown`
      - ↑ `open_mailbox`
      - ↑ `show_lines`
      - `refuse_stale` — 지금 판의 확인 열쇠 — 미리 본 열쇠(``confirm``)와 다르면 Stop(4 · 아무것도 안 바꿨다). 여섯 짝의 실행이 이 한 자리로 가른다.
        - ↑ `mail_token.token`
        - ↑ `mail_stop.Stop`
    - `cmd_rules` — 메일 규칙을 한 줄씩 unid 와 함께 찍고 그 수를 붙인다.
      - ↑ `open_mailbox`
      - ↑ `rule_line`
    - `check_rule_args` — 규칙 명령의 인자 — 고칠 · 지울 규칙의 열쇠 꼴을 세션 앞에서 본다.
      - ↑ `mail_find.unid_shape`

**다른 스킬이 부르는 조각** — 입구에서 안 닿는 것.

- `inbox.level_at_least` ← company-directory — ``level`` 이 ``floor`` 와 같은 갈래(P · E)이고 그 이상인가. 등급이 없으면 거짓이다.
  - ↑ `MailboxConfigError`
- `mail_kept.tree_newer` ← company-directory — 부서 나무만 받은 판이 사람까지 받은 판보다 나중인가 — 사람까지의 판이 그 사이 낡았다(찾은 사람의 부서가 그 나무에 없어 나무를 새로 받았다). 사람까지 다시 받을 때다.
  - ↑ `written_at`
  - ↑ `org_cache_path`
- `mailer.MailError` ← daily-brief — 메일을 못 보냈다.
- `mailer.MailConfigError` ← daily-brief — 설정이 틀렸다 — 환경변수나 수신자 파일. 보내기 전에 잡힌다.
- `mailer.MailRefused` ← daily-brief — 중계가 수신자를 거절했다.
- `mailer.send` ← daily-brief — 메일 한 통을 보낸다.
  - `settings` — 환경변수를 읽어 발송 설정을 세운다 — 부를 때마다 다시 읽는다.
    - ↑ `MailConfigError`
    - `_check_address` — 주소 하나인가. ``이름 <a@b>`` 꼴도 받는다.
      - ↑ `MailConfigError`
    - `Settings` — 발송 설정 한 벌 — 중계 호스트 · 포트 · TLS 정책 · 시한 · 기본 발신자.
  - `_resolve_sender` — 발신자를 정한다 — 안 주면 설정의 기본 발신자, 둘 다 없거나 주소가 아니면 MailConfigError.
    - ↑ `MailConfigError`
    - ↑ `_check_address`
  - `_address_list` — 주소 목록으로 고른다.
    - ↑ `MailConfigError`
    - ↑ `_check_address`
  - ↑ `MailConfigError`
  - `_domain` — 주소의 도메인 — 없으면 None.
  - `_deliver` — 중계에 이어 정책대로 STARTTLS 를 세우고 봉투의 수신자에게 한 통을 넘긴다 — 한 사람이라도 거절되면 MailRefused.
    - `_connect` — 설정의 중계에 평문으로 이어 EHLO 까지 한 연결을 낸다.
      - `_ehlo_name` — EHLO 에 실을 이 PC 의 이름 — ASCII 여야 한다.
    - `_secure` — 정책대로 STARTTLS 를 세운다.
      - `_close` — 연결을 QUIT 으로 닫고, 그게 안 되면 그냥 끊는다.
      - ↑ `MailError`
      - ↑ `_connect`
    - ↑ `MailRefused`
    - ↑ `_close`

**어디서도 안 닿는 조각** — 표 · 인스턴스를 거쳐 부르거나 아무도 안 부른다.

- `mailer.load_recipients` — 수신자 파일과 발송 설정을 함께 보고 ``send`` 에 풀어 넣을 ``{"sender", "to", "cc", "bcc"}`` 를 낸다 — 틀리면 MailConfigError. ``from`` 이 없으면 ``MAIL_DEFAULT_SENDER`` 로 채운다.
  - ↑ `settings`
  - ↑ `MailConfigError`
  - ↑ `_resolve_sender`
  - ↑ `_address_list`
  - ↑ `_check_address`
- `mailer.notify` — 평문 알림 한 통 — **제 오류를 삼킨다.** 보냈으면 True, 못 보냈으면 False(경고 한 줄). 실패 알림이 본 흐름의 종료 코드 · 마지막 로그를 바꾸면 안 된다.
  - ↑ `settings`
  - ↑ `send`
<!-- /drawn:piece-map -->
