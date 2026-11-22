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
- **일정 한 건 읽기** — `GET vweventprev/<unid>?opendocument`(unid 는 줄 `url` 의 32 자리 16진). 답은 HTML 이고 둘이 든다 — 칸 목록 표
  (줄마다 첫 칸이 값 · 셋째 칸이 칸 이름: `Subject` · `EventArea`=장소 · `Description`=설명)와 스크립트 `var EventDoc = {…}`(`attDisplayName` ·
  `attEmail` · `attRsponseStatus` · `attComment` · `attAadditionalGuests`=참석자 수 · `ref…` 참조자 · `attowner`=초대한 사람 · `PcMeetingUrl` ·
  `visibility` · `modified`). 쉼표로 이은 칸은 사람 차례가 같다. 두 번 열어도 `modified` 가 같다 — 안 바꾼다. 없는 unid 는 HTTP 404.
  ⚠ `?editdocument` 는 편집 화면이라 읽지 않는다(2026-11-19)
- **찾기** — 상세검색 `GET (agSearchCalendarEvent)?openagent&callback&username&calendarId&textColor&colorId&color&eventTitle&from&to(YYYY.MM.DD)
  &desc&eventArea&attend&file` → JSONP(`text/plain`) `data[]` 가 일정 줄 꼴이고 **끝이 시작과 같게 온다**. 조건은 다 함께 걸린다. 본문 찾기
  `GET (agFTSearchCalendarEvent)?openagent&callback&calendarId&username&searchStr&textColor&colorId&color` → 같은 꼴에 끝 시각이 오고 기간 없이
  지난 해까지 걸린다. 양성 · 음성 대조 — 장소 「지하강당」 1 · 없는 장소 0, 본문 「교육」 6 · 없는 낱말 0, 참석자 없는 이름 0(2026-11-19).
  Teams 일정함은 이 두 찾기에 0 건이라 기본 일정함만 묻는다 — `find` 는 Teams 일정함을 위 「일정」 읽기(겹침을 볼 때와 같은 꼴)로
  기간째 읽어 제목으로 거른다
- **공휴일** — 같은 서버의 `GET /<회사 코드>/cal/calpublic.nsf/vwHolidays?searchView&query=[startDate]>=YYYY-MM-DD AND [startDate]<=YYYY-MM-DD`
  → HTML 안의 `<RESULT>[{"start","title","description"}…,{"end":true}]</RESULT>`. 해를 넘는 기간도 한 번에(12-25 · 01-01), 없는 달은
  `[{"end":true}]` 하나. 회사 지정 휴일(`POSCO_HOLLIDAY` · `POSCO_ANNIVERSARY`)은 2026 년 0 줄이라 안 묻는다(2026-11-19)
- **비공개 · 하루 종일 · 장소로 넣기** — 빠른 등록에 `visibility=private` · `EventArea=<장소>` 를 실으면 선다(줄의 `visibility` 가
  `private`, 한 건 읽기의 장소가 「&」 까지 그대로). 하루 종일은 `RRULE=ALLDAY` 와 시각 없는 `StartDate` · `EndDate`(끝날도 든다) — 하루짜리
  줄은 `allDay=true` · `00:00:30` ~ `23:59:59` 로 선다. 그 줄도 `(wEventDelete)` 하나로 지워진다. `Importance=true` 를 실으면 줄의
  `Importance` 가 `true` 로 선다(2026-11-19 · 시험 일정 넷)
- **고치기** — 제목 · 장소는 미리 보기 [저장] `GET (agSavePrevMe)?openagent&callback&calendarId&eventId&subject&eventarea(「&」 는
  `1qazxsw21qazxsw2`)&updatetype=current&cdate=&attOwner&owner&username&MailTitle=&attRsponseMe=&attComment=&attAadditionalGuests=0`, 시각은
  끌어 옮기기 `GET (agSetEventDate)?OpenAgent&callback&lang=kor&eventid&drag_start&drag_end(옛 시각)&event_start&event_end(새 시각 · 서울
  YYYY-MM-DD HH:MM)&eventowner&username` — 둘 다 다시 읽어 선 것을 봤다(참석자 없는 시험 일정 · 장소는 시각을 옮겨도 남는다). 답은
  JSONP `notice` 로 참석자에게 알릴까를 묻는다(참석자 없는 판은 안 물었다). ⚠ **[저장] 뒤 내가 든 일정의 줄에 `attRsponseStatus=accepted`
  가 선다** — 응답 칸으로 받은 초대를 가르면 내 일정이 초대로 읽힌다. 받은 초대는 줄의 `attOwner` 가 남(초대한 사람)이고 내가 든 일정은
  빈 글자다(올해 60 줄 · 2026-11-19)
- 안 잰 것 — 반복 일정의 지우기(그날 하나만 걷는지 줄 전체를 걷는지 모른다) · 여러 날 하루 종일 일정의 줄 꼴 · 일정 조회의 `end` 가
  그날을 드는지 · 시각 크기 조절(`agSetEventDateTime` — 끝만 바꾸는 부름도 `agSetEventDate` 로 보낸다) · 참석자가 든 일정의 고치기 알림

## Teams 회의 예약 창 — 문서와 회사 밖에서 잰 것

- 꼴 — Microsoft Learn 「Deep links for workflows in Teams app」(https://learn.microsoft.com/en-us/microsoftteams/platform/concepts/build-and-test/deep-link-workflow ·
  그 판의 원본 커밋 `5751bb46`)의 「Deep link to open a meeting scheduling dialog」: `https://teams.microsoft.com/l/meeting/new?subject=&startTime=&endTime=&content=&attendees=`.
  칸은 다 고를 수 있고, 참석자는 쉼표로 이은 UserPrincipalName(대개 메일 주소)이며 링크를 연 사람이 주관자다. 시각은 시간대(UTC 차이)가 붙은
  ISO 8601 이어야 한다. 그 문서는 빈칸에 `+` 를 안 받는다며 이렇게 쓴다 — "Ensure your URI encoding code returns `%20` for spaces".
  장소는 못 채운다. 링크가 여는 것은 예약 창이고, 문서는 회의가 저절로 선다고 하지 않는다
- 넘기는 주소와 길이 한도 — 회사 밖에서 로그인 없이 지어낸 값만 실어 잰 것(2026-11-22). `teams.microsoft.com/l/meeting/new?…` 는 302 로
  `/dl/launcher/launcher.html?url=<경로부터를 한 번 더 인코딩한 글>&type=meeting&deeplinkId=<36 자>&directDl=true&msLaunch=true&enableMobilePage=true`
  로 넘기고, 손의 셈(`teams_relayed`)이 그 길이와 세 링크(한글 · 기호 · 짧은 글)에서 글자 하나 안 틀리고 맞았다. 넘긴 주소가 8,188 자면 200 ·
  8,189 자면 404 — 첫 주소 쪽도 8,188 자까지만 302 다. 손이 지은 시험 회의 링크(한글 제목 · `&` `#` `+` 따옴표 든 설명 · 참석자 셋)는 302 → 200 이었다
- 보낸 회의가 Teams 일정과 회사 일정 화면에 함께 보인다는 것은 사용자의 말이다(Teams 로 넘어가는 시기라 기존 일정과 Teams 일정 둘이 있다).
  손이 읽는 Teams 일정함(`TeamsCalendar`)에 회의실 예약이 저절로 서는 것은 쟀지만(위 「사내 일정 앱에서 잰 것」), Teams 에서 바로 잡은 회의가
  거기 서는지는 안 쟀다 — 아래 「회사에서 잴 것」
- 안 잰 것 — 로그인한 Teams 가 예약 창을 열고 칸을 채우는지(앱 · 웹 어느 쪽에 뜨나) · 참석자에 나를 넣으면 어떻게 되나 · 끝 없이 시작만 준
  창의 끝 · 회사망(프록시)이 이 길이를 그대로 넘기나

## 화면에 있는데 손가락이 없는 것 — 잰 것과 코드로 읽은 것

일정 화면(`mainframe` · `Event` · `Eventquick` · `quickRegistration` · `copyEvent2` · `ProfileTab` 폼과 `fmcal_mainframe.js` ·
`fmcal_event.js` · `fmcal_event_addform.js` · `event_attend.js` · `event_repeat.js` · `fmcal_profile.js` · `common.js` ·
`tokenInput_c.js` · `orgtree_cal.js`)에서 뽑았다(#292 조사 · 2026-11-19). 「잰 것」은 GET 으로 불러 답을 본 것, 「코드로 읽은 것」은 부르지
않고 화면 스크립트에서 칸 이름만 읽은 것이다 — 바꾸는 요청은 하나도 안 불렀다. 안 짓는 까닭은 `--help` 의 「아직 없는 손가락」이 든다.

- **손가락이 따로 필요 없는 것** — 월 · 주 · 일 · 목록 보기는 같은 읽기(`getcalendareventMe`)의 그림이다. 시간 찾기(`CAL_TIME_SEARCH`)는
  상세 화면에서 주석 처리돼 화면에 없다 — 함께 비는 때는 `show --free` 가 든다. 인쇄(`calendarWeekPrint?openform`) · 미니 달력 · 스킨 ·
  색 고르기는 화면 모양이다. 이 계정 화면 설정의 `useGPTBooking` · `use_nexteptask` · `useChatbot` 은 0 이라 P-GPT 예약 · 태스크 · 챗봇
  단추가 안 켜진다
- **한 달 설명 한꺼번에(엑셀)** — 잰 것: `GET agGetEventForExcel?openAgent&start=YYYY-MM-DD&end=YYYY-MM-DD&calendarid=<id>^<id>` →
  `application/vnd.ms-excel` 꼴의 HTML 표(일자 · 시간 · 일정함 · 제목 · 설명 · 음력 · 절기). 장소 · 참석자는 없다 — `show` + `event` 가 다
  들어 따로 안 짓는다
- **음력 · 절기** — 잰 것: 공휴일과 같은 꼴의 `vwSolarToLunar?searchView&query=[SolarDate]>=… AND [SolarDate]<=…`. 대화가 물을 일이 드물어
  안 짓는다
- **알림 팝업** — 화면은 `(getAllAlimData)` 로 알림 큐(`calAllimQuePath`)를 40 초마다 읽는다. 읽기가 큐를 소비하는지 안 쟀다 — 부르지 않는다
- **찾기의 첨부 조건** — 상세검색의 `file=true` 는 첨부 있는 일정만이다. 이 계정 올해 0 건이라 양성 대조가 없어 `find` 에 안 실었다
- **공유 일정함의 한 건 읽기 · 찾기** — 화면은 그 일정함의 서버로 `http://<calhost>/<caldbpath>/…` 같은 꼴을 부른다. 안 쟀다 —
  `EventPrev?openform&calserver=…` 는 HTTP 500(칸을 잘못 준 듯 · 안 팠다)
- **반복 회차 한 건 읽기** — 반복은 회차마다 줄이 선다. 회차 하나를 읽을 때 `vweventprev/<unid>?opendocument&cdate=` 의 `cdate` 가 드는지
  안 쟀다
- **알림 걸기** — 코드로 읽은 것: 값은 분 `0 · 5 · 10 · 15 · 30 · 60 · 120 · 180 · 720 · 1440 · 2880 · 10080`, 최대 셋(`CAL_EVENT_ALERTALLIMSET`).
  빠른 등록 폼에도 `reminders` 칸은 있으나 화면에 입력이 없다
- **반복 넣기 · 지우기** — 코드로 읽은 것: 넣기는 상세 화면에만 있다(빠른 등록에 없다). `RRULE=REPEAT[,ALLDAY] · FREQ=DAILY|WEEKLY|MONTHLY|YEARLY ·
  INTERVAL · BYDAY(1=일 … 7=토 · 쉼표) · BYWEEKNO · RSTART · RUNTIL(빈 글자=끝 없음) · originalTimeZone`. 지우기는 전체가 `(wEventDelete)`,
  회차 · 이후는 `(wDeleteRepeatEvent)?openagent&calendarId&eventId&ownerId&userName&alim&msgtitle&isediter&deleteType(current|dayafter|all)&cdate
  &SAResponse=json&lang&allimTarget`. 반복의 미리 보기 저장은 `(agSavePrevMeRepeat)`, 끌어 옮기기는 `recurringModifyResize` 화면이 범위를 묻는다
- **전체 고치기(상세 화면)** — 코드로 읽은 것: `0/<unid>?editdocument` 폼을 싣고 `POST 0/<unid>?EditDocument&Seq=1`(multipart). `SaveAgent` 가
  `(wEventUpdate)`(전체) · `(agUpdateRepeatEvent)`(반복 · `updatetype`≠all) · `(wEventMove)`(일정함을 바꿀 때)로 갈린다. 비공개면 `calReaders` ·
  `Readers` 를 비운다. 첨부는 xam 업로더다. ⚠ 편집 화면을 여는 것도 문서를 잡을 수 있어 읽기로 안 연다
- **참석 답** — 코드로 읽은 것: 미리 보기 `(agSaveAttendPrev)?openagent` · 상세 화면 `(agSaveAttend)?openagent`, 칸 `calendarId · eventId ·
  updatetype=current · cdate · attOwner(초대한 사람) · writer · userName · MailTitle(일정초대회신-참석|불참|미정) · attRsponseMe=accepted|declined|
  tentative · attComment · attAadditionalGuests · lang`. 답은 JSONP. 이 계정 올해 초대 대부분이 `needsAction` 이다
- **복사** — 코드로 읽은 것: 대화창 `copyEvent2?openform&calendarId&EventId&owner`(대상 일정함 + 참석자 · 참조자 옮김 체크 · 열기만 잼) →
  `(wEventCopy)?OpenAgent&s_cal&eventId&s_owner&t_cal&t_owner&username&c_obj=att,ref` 가 **저장 전 복사본 문서를 서버에 만들고** 새 등록 화면을
  연다. 대화의 「같은 걸 또 넣어 줘」는 `preview` → `add` 로 선다
- **여러 건 · 지난 일정 한꺼번에 지우기** — 코드로 읽은 것: `POST (agDelSelectEvent)?OpenAgent` 의 `delkey=<calendarId>^<eventId>^<YYYYMMDD>`
  를 `` {` `` 로 이은 것 · `delkind=select` · `ppoint`(초대 · 회의 · Teams 줄은 화면이 체크 칸을 끈다), `POST (agDelBeforDateEvent)?OpenAgent` 의
  `cdate=YYYYMMDD · delkind=befor`(되돌릴 수 없는 대량 지우기 · 자동 삭제 30 · 60 · 90 일은 환경설정)
- **참석자 · 참조자 부르기 · 메일 알림 · PC 영상회의** — 코드로 읽은 것: 상세 화면의 `attId · attEmail · attDisplayName · attDeptName ·
  attAadditionalGuests · attRsponseStatus` 와 `ref…` 칸, 사람 찾기 `/common/profile.nsf/ag_org_search_json` · 조직도 `ag_tree_dept_json` ·
  `ag_tree_user_json` · `(agGetUserCalendarDBInfo)`. 참석자가 든 저장 · 고치기는 확인창(`confirmSave` · `confirmModify`) 뒤 `(agNotice)?openagent&
  eventId&calendarId&calendarDB&owner&action&mailTitle&msgtitle&SAResponse=json&lang&allimTarget=att,ref` 가 메일을 보낸다. 알림 글 보기는
  `(agGetNoticeBodyHtml)`(안 불렀다). 영상회의는 `(agGetVideoMeet)` 가 `PcMeetingUrl · PcMeetingId` 를 내며 참석자가 들고 반복 · 하루 종일이
  아닌 일정에만 선다. 남에게 메일이 가는 일이라 회의실 손(스킬 company-meeting-room)이 든다
- **화면 설정** — 코드로 읽은 것: 일정함 보임 `agSetCalendarSelected` · 색 `agSetCalendarColor`, 공유 일정함 더하기 `agAddShareCalendarQuick` ·
  `agAddShareCalendar` · 그룹 `agAddCalendarGroup` · 빼기 `agDelCalendar`, 환경설정 `POST Profile?OpenForm`(`SaveAgent=wCalProfileSave`) ·
  Teams Sync `POST /swpmail/ifmobile_teams.nsf/CALService?OpenForm`. 일정 내용이 아니라 사람의 화면이 바뀐다

## 회사에서 잴 것 — 아직 없는 손가락을 세우려면

잰 판이 서면 `scripts/company_calendar.py` 의 표에 한 줄과 그 일을 하는 손 하나로 더한다(`DESIGN.md` 「명령의 손가락은 표다」).

- 설명 · 알림 · 반복 · 중요 · 공개 범위 고치기 — 위 「전체 고치기」의 저장이 서는지 · 편집 화면을 열고 안 저장하면 문서가 잠기는지.
  지금 손은 제목 · 장소 · 시각만 고친다
- 알림 걸기 — 상세 화면의 `reminders="email^30,popup^10"` · `reminders_mail` · `reminders_pop`(분)이 서는지 — 울리는 것은 그 시각이 와야 잰다
- 반복 넣기 · 회차 지우기 — 위 「반복 넣기 · 지우기」의 칸으로 시험 반복 하나를 넣고 `deleteType=current` 가 그 회차만 걷는지
- 회사의 근무 시간 · 점심 시간 — 모두 비는 때(`show --free`)의 기본 구간(`WORK_HOURS`)은 짐작이고 점심을 안 뺀다
- 여러 날 하루 종일 · 여러 날 일정의 줄 꼴(위 「안 잰 것」) — 재 오면 모두 비는 때의 `busy_of` 가 짐작(`assumed`) 없이 센다
- 거절한 초대가 내 일정 줄에 남는지와 그 `attRsponseStatus` 값 — 지금은 줄에 선 초대를 다 바쁜 때로 센다
- 공유 일정함 줄의 `sourceowner` 가 주소록의 Notes 이름(사람 파일의 `notes`)과 같은 꼴로 오나 — `show --people-file` 이 둘을 견줘 사람을
  일정함에 잇는다(마디의 「CN=」 따위는 떼고 견준다). 어긋나면 공유받은 분도 `unseen` 으로 선다. `calendars` 의 목록과 주소록의 한
  분을 견준다
- 일정함을 공유하지 않은 동료의 빈 때 — 잰 길이 없다(실마리는 위 「참석자 · 참조자 부르기」 줄의 `(agGetUserCalendarDBInfo)`). 그래서
  `--people-file` 은 그분을 셈에 안 넣고 이름으로 댄다
- Teams 일정함을 `find` 의 기본 기간(오늘 앞뒤 1 년)째 한 번에 읽는 판 — 그렇게 긴 기간의 일정 읽기는 안 쟀다. 답이 늦거나 잘리면 기간을
  나눈다
- Teams 회의 예약 창(`teams-meeting`) — 회사 PC 의 Edge 주소창에 시험 링크 하나를 붙여 연다:
  `https://teams.microsoft.com/l/meeting/new?subject=%EC%8B%9C%ED%97%98%20%E2%80%94%20%EC%97%B4%EB%A6%AC%EB%8A%94%EC%A7%80%EB%A7%8C%20%EB%B4%85%EB%8B%88%EB%8B%A4&startTime=2026-11-24T15%3A00%3A00%2B09%3A00&endTime=2026-11-24T15%3A30%3A00%2B09%3A00&content=%EB%B3%B4%EB%82%B4%EC%A7%80%20%EB%A7%90%EA%B3%A0%20%EB%8B%AB%EC%95%84%20%EC%A3%BC%EC%84%B8%EC%9A%94`
  (제목 「시험 — 열리는지만 봅니다」 · 2026-11-24 15:00–15:30 · 설명 「보내지 말고 닫아 주세요」 · 참석자 없음). Teams(앱이든 웹이든)에 새 회의
  예약 창이 떠 제목 · 날 · 시각 · 설명이 그대로 찼으면 선다 — 보내지 말고 닫는다. 창 대신 다른 화면(로그인 · 오류 · 빈 창)이 뜨면 그 화면을 적어 온다.
  더 볼 것 하나 — 참석자 한 분(본인)을 넣은 회의를 한 번 보내 보고, 다음 날 `show <그날>` 에 그 회의가 Teams 일정함 줄(`calendar`)로 서는지 본다
- 참석 답(수락 · 거절) — 위 「참석 답」의 칸. 부르면 초대한 분께 알림이 가서
  남이 든 초대로는 못 잰다 — 사용자 본인이 연 시험 회의(참석자 = 본인)에 본인이 답해 알림 메일이 서는지를 본 뒤 손가락을 짓는다
