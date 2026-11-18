# 출처

## 견준 표준 — 없다

사내 일정 앱(HCL Domino 웹 일정 · 내 일정함)을 다루는 공개 스킬이나 명세는 없다. 일정 표준(iCalendar · CalDAV)은 이 앱에 안
닿는다 — 일정 파일 가져오기 메뉴가 없고 웹 CalDAV 는 `PROPFIND` 가 다 405 다(mail-secretary 이슈 #28 「C. 일정」 둘째 코멘트).
그래서 참조 없이 세웠다.

## 이 스킬이 기대는 자리

- 손과 잰 꼴 — 아래 「사내 일정 앱에서 잰 것」. 그 줄들의 원본(잰 셈 · 못 잰 까닭)은 mail-secretary 의
  `docs/company-facts.md` 「일정」과 회사 확인 대장(그 저장소 이슈 #28 「C. 일정」 코멘트 둘 — 줄 C1 ~ C7 · 「코드로 등록 · 지우기」)이고,
  읽는 손 · 넣는 손 · 지우는 손은 그 앱의 `secretary/agenda.py`(68ad771)에서 옮겨 왔다. 공유 일정함의 묻는 꼴은 회사 PC 에서 공유 셋
  (다른 서버 둘 · 같은 서버 하나)으로 쟀다(2026-11-06)
- 검사의 가짜 일정 앱 — 설정 저장소 `_check/skills/company-calendar/check_agenda.py` 의 흉내는 그 앱의 `_check/_fake_agenda.py`(68ad771)에서 옮겨 왔다
- 넣기 · 지우기의 경계(누름에서만 · 참석자 비움 · 손수 든 단건만 · 다시 읽어 가림) — mail-secretary 결정 0026 · 0027(68ad771).
  그 앱의 「로컬 화면의 확인 POST」 자리를 이 스킬에서는 「대화에서 그 한 건을 확인받은 뒤」가 든다
- 범위 — claude-config 이슈 #240 「갈래」 3 · 「경계」

## 사내 일정 앱에서 잰 것 — 어기면 조용히 망가진다

꼴이 바뀌면 이 절과 `scripts/agenda.py` 를 함께 고친다.

- 일정은 메일함 밖의 따로 선 앱이다 — `http://pcfca0N.posco.net/02/cal/calperson<NN>.nsf`. 서버 · 번호가 사람마다 다르다 — 잰
  기본(`DEFAULT_APP_URL`)으로 내 일정함이 안 읽히는 사람은 Edge 에서 메일 → 일정을 열어 주소창에서 받는다
- 일정함 목록 `GET agGetCalendar?OpenAgent&calltype=GNB` → JSON 배열(`text/html` 로 온다). 내 것은 `kind=PEO` 이고(기본 일정함 하나 — 사람에 따라 `TeamsCalendar` 가 같은 `owner` 로 하나 더),
  공유받은 일정함(`GRW` 쓰기 공유 · `GRR` 읽기 공유)은 줄마다 서버(`calhost`) · DB(`caldbpath`)가 제각각이고, 일정함을 가진 사람은
  `sourceowner`(`owner` 는 보는 사람이다) · 이름은 `subject` 다. 그 값은 다 목록이 들어 사람마다 다른 것을 여기 안 적는다
- 공유 일정함의 일정 `GET http://<calhost>/<caldbpath>/getcalendarevent?readform&callback&calendarId&username=<sourceowner>&start
  &end&kind=<GRW|GRR>` → 내 일정과 같은 JSONP. 줄의 `visibility` 가 `private` 면 일정함을 가진 사람이 비공개로 든 것이고 제목이 그대로 온다.
  `editable` 은 빈 글자다. 일정 화면(`fmcal_mainframe.js`)이 같은 꼴로 묻는다 — 공유 일정함이 다른 서버에 있어도 같은 서버에
  있어도 같다. 사내 도메인(읽는 손 주소의 첫 이름표를 뗀 나머지) 밖 서버는 묻지 않는다 — 세션 쿠키를 밖에 안 싣는다
- 일정 `GET getcalendareventMe?readform&callback&calendarId&username&start&end&kind=PEO` → JSONP. 줄은 두 배열 — `data` 반복
  일정(날짜마다 한 줄로 풀려 같은 `eventId` 가 여러 날에 선다) · `data2` 단건. 칸 이름은 철자 그대로(`attRsponseStatus`) ·
  `title` 은 HTML 엔티티(`[` → `&#91;`) · `timeZone` 은 대개 빈 글자(서울) · 더러 `+09:00`. 장소 · 참석자 칸은 없다
- ⚠ **줄의 `url` 은 편집 화면(`vweventprev/<unid>?editdocument`)이고, 지우기도 GET 이다** — 읽는 손은 세 JSON 주소의 꼴만
  짓는다
- 넣기는 `GET Eventquick?OpenForm` 의 폼을 기본값째 싣고 `CalendarID · Subject · Description · StartDate · EndDate
  (YYYY-MM-DD HH:MM 서울) · EventArea · visibility · callback=new` 을 바꿔 `POST Eventquick?OpenForm&Seq=1` 하면 선다(이 손은
  참석자 · 참조 칸 `att*` · `ref*` 도 비워 보낸다 — 손님 수 칸은 폼 그대로) — 쓰는
  사람 몫(`Editors` · `calEditors`)과 고정 값 칸은 폼이 채운다. 답은 창을 닫는 스크립트라 성공을 못 가린다. 넣은 줄은 단건에
  `eventId=<사번>_<만든 시각>` · `eventtype` 빈 · `attRsponseStatus` 빈으로 선다
- 넣은 일정은 공개 범위 `public` 으로 들어간다 — 폼이 비워 둔 값을 사람이 넣은 판의 값으로 채운다. 남이 제목을 볼 수 있다
- 지우기는 `GET (wEventDelete)?openagent&calendarId&eventId&ownerId&userName&alim=&msgtitle=&isediter=true&SAResponse=json&lang=kor
  &allimTarget=` 하나로 선다 — 화면이 앞에 부르는 `(agCheckDoc)` · `?editdocument` · `confirmDelForNomalEvent` 는 없어도 된다.
  답은 늘 `{"RETURN" : "" }` 이라 성공을 못 가린다
- 세션은 메일함과 한 벌이다 — 회사 쿠키는 다 `.posco.net` 이라 메일 서버에 실리는 쿠키로 일정이 다 온다. 쿠키 없이 부르면
  **200 에 SSO 로 넘기는 HTML** 을 준다 — 상태 코드로는 못 가려, JSON · JSONP 가 아니면 끊긴 세션으로 읽는다. 리다이렉트는
  따라가지 않는다 — 따라가면 쿠키가 SSO 에 실린다
- 내 일정 줄의 `editable` 은 칸은 있되 늘 빈 글자다 — 고칠 수 있는 사람은 `editors`(`CN=…/OU=…/OU=02/O=posconet,` 꼴로 이은
  Notes 이름)가 든다. 내 일정함의 줄은 회의든 단건이든 `Owner` · `owner` · `editors` 에 쓰는 사람이 든다
- 회의실 예약 앱(스킬 company-meeting-room)으로 잡은 회의는 **Teams 일정함**에 제목 앞 「[회의실 예약] 」을 달고 예약과 같은 시각으로
  저절로 든다(기본 일정함에는 안 든다). 예약을 취소하면 거기서도 사라진다. `show` 는 Teams 일정함 줄이라 `handle` 없이 낸다(2026-11-19)
- 안 잰 것 — 반복 일정 · 하루 종일 일정의 지우기(반복은 그날 하나만 걷는지 줄 전체를 걷는지 모른다) · 하루 종일 ·
  여러 날 일정의 줄 꼴 · 일정 조회의 `end` 가 그날을 드는지

## 회사에서 잴 것 — 아직 없는 손가락을 세우려면

잰 판이 서면 `scripts/company_calendar.py` 의 표에 한 줄과 그 일을 하는 손 하나로 더한다(`DESIGN.md` 「명령의 손가락은 표다」).

- 일정 고치기 — 편집 화면(`vweventprev/<unid>?editdocument`)의 폼을 싣고 칸을 바꿔 저장하는 주소 · `Seq` · 바꿀 수 있는 칸, 회의 줄을
  고치면 참석하실 분께 알림이 가는지
- 일정 한 건 읽기 — 장소 · 참석자 · 설명을 바꾸지 않고 읽는 주소(편집 화면이 아닌 문서 보기가 있는지)
- 비공개로 넣기 — 사람이 등록 화면에서 비공개를 고른 판의 `visibility` 값
- 하루 종일로 넣기 — 등록 화면의 하루 종일 칸 이름과 값
- `EventArea` 가 무엇을 가르는 칸인지(장소인가 갈래인가)
- 회사의 근무 시간 · 점심 시간 — 모두 비는 때(`show --free`)의 기본 구간(`WORK_HOURS`)은 짐작이고 점심을 안 뺀다
- 하루 종일 · 여러 날 일정의 줄 꼴(위 「안 잰 것」) — 재 오면 모두 비는 때의 `busy_of` 가 짐작(`assumed`) 없이 센다
- 거절한 초대가 내 일정 줄에 남는지와 그 `attRsponseStatus` 값 — 지금은 줄에 선 초대를 다 바쁜 때로 센다
- 참석 답(수락 · 거절)을 보내는 주소와 그 알림
