"""사내 일정 앱(HCL Domino 웹 일정)의 내 일정함을 읽는 손과, 일정을 바꾸는 이름 붙은 손 셋(``register`` · ``edit`` · ``delete``) — 표준
라이브러리와 형제 스킬 ep-login 의 ``ep_session``(세션 파일 → 쿠키 통, 스킬 홈에 나란히 깔린 ``../../ep-login/scripts/``)만 쓴다.
몸은 곁의 모듈 넷(``agenda_shapes`` · ``agenda_rows`` · ``agenda_reader`` · ``agenda_changes``)에 있고 이 모듈은 그 이름을 다 다시 내는
들머리다 — 부르는 쪽은 ``import agenda`` 하나로 싣는다. 막는 까닭과 바꾸는 손의 경계는 ``references/DESIGN.md``, 일정 앱의 주소와 꼴은 ``references/SOURCES.md`` 가 든다.

⚠ ``register`` · ``edit`` · ``delete`` 는 남이 보는 회사 일정을 바꾸고 지운 일정은 되돌릴 손이 없다 — 사람이 그 한 건을 분명히 고른
뒤에만 부른다. 읽는 손은 안 바꾸는 것을 잰 주소 밖을 서버에 닿기 전에 ``ChangeRefused`` 로 막는다(이 앱은 편집 화면 · 고치기 · 지우기도
GET 이다).

어떻게 부르나
    로그인은 이 파일이 하지 않는다. 사내 SSO 세션을 쿠키 파일(Playwright 저장 상태 꼴 ``{"cookies": [...]}``)로 남기는 손이
    따로 있고 — 메일 손과 같은 세션 한 벌이다 — 이 파일은 그 쿠키로 일정 서버에 묻는다::

        import agenda

        r = agenda.Reader(url, cookies_file)            # url — 일정 앱 주소창의 …/calperson<NN>.nsf 까지(그 뒤는 버린다)
        book = r.book()                                 # 내 기본 일정함(kind=PEO · 여럿이면 defaultCalendar)
        for e in r.between(first, last, book):          # 서울 날짜 first ~ last 에 걸친 일정 — 시작 차례
            e.when(), e.title, e.keep_reason, agenda.Seen.of(e).handle
        for b in r.shared_books():                      # 공유받은 일정함(GRW · GRR) — 읽기만 한다
            r.between(first, last, b)                   # 줄마다 e.calendar(그 일정함 이름) · e.private(일정함을 가진 사람이 비공개로 든 것)

        want = agenda.Want("시험 일정", agenda.kst("2026-11-07 14:00"), agenda.kst("2026-11-07 15:00"))
        got = agenda.register(url, cookies_file, want)  # ⚠ 일정을 바꾼다 — 그 한 건을 사람이 확인한 뒤에만
        got.state                                       # added · already · clashed · unsure
        gone = agenda.delete(url, cookies_file, agenda.Seen.parse(handle))   # ⚠ 일정을 바꾼다 — 확인한 뒤에만
        gone.state                                      # deleted · gone · changed · unsure
        done = agenda.edit(url, cookies_file, agenda.Seen.parse(handle), agenda.Change(title="새 제목", place="본관 201"))   # ⚠
        done.state                                      # edited · gone · changed · unsure
        r.detail(e.unid)                                # 한 건 — 장소 · 설명 · 참석자와 응답 · Teams 링크(안 바꾼다)
        r.search(place="지하강당", first=…, last=…) · r.search_text("교육") · r.holidays(first, last)

    ``Reader.from_env()`` 는 환경변수로 세운다 — ``CALENDAR_URL`` · ``MAILBOX_COOKIES`` 둘 다 꼭 준다. 쿠키 파일의 자리는 이 파일이
    정하지 않는다 — 세션을 남기는 손이 정하고, 부르는 쪽이 그 경로를 넘긴다.

무엇을 내나
    시각은 다 시간대가 붙은 UTC 이고, 보이기(``Event.when``)는 서울이다. 시각을 못 읽은 줄은 버리고 ``Reader.unread`` 에 일정함마다
    그 수를 쌓는다. ``Seen`` 은 사람에게 보인 일정 한 줄의 손잡이다 — 그 줄의
    열쇠 · 그 일정의 열쇠(둘 다 사번이 든 일정 열쇠의 해시) · 제목 · 시작 · 끝의 지문 · 서울 날짜를 한 글줄(``handle``)로 들어,
    대화를 건너 지우기에 넘긴다. ``register`` 는 ``Added``, ``delete`` 는 ``Removed`` 를 내고 끝은 다시 읽은 일정이 정한다(``state``).
    ⚠ 공유받은 일정함의 줄이라는 표지는 글줄에 안 실린다 — ``Seen.parse`` 로 되읽은 손잡이는 내 일정함의 줄로 읽혀, 지우기가 내
    일정함에서 그 열쇠를 찾고 없으면 ``gone`` 이다. 공유 줄의 글줄 손잡이를 지우기에 넘기지 않는다.

    예외 — 세션이 끊겼으면 ``SessionExpired``, 막은 주소 · 지우지 않는 줄은 ``ChangeRefused``(까닭은 ``reason``), 등록 화면의 꼴이
    잰 것과 다르면 ``FormChanged``, 쿠키 파일이 없거나 비었으면 ``SessionMissing``(``CalendarConfigError`` 의 갈래), 주소 · 인자가
    틀리면 ``CalendarConfigError``, 그 밖은 ``CalendarError``(다 이것의 갈래다). 무엇을 했는지는 ``logging`` 으로 남긴다(로거 이름은
    이 모듈 이름) — 셈과 방향만 싣고 일정 제목 · 이름 · 사번은 안 싣는다.
"""

from __future__ import annotations

# 일정 손은 모듈 넷으로 선다 — 바탕(agenda_shapes) · 글 꼴 풀기(agenda_rows) · 읽는 손(agenda_reader) · 바꾸는 손(agenda_changes).
# 이 모듈은 부르는 쪽(명령 · 검사)이 이름으로 싣는 자리라 그 이름을 다 다시 낸다.

from agenda_shapes import (  # noqa: F401
    EP_LOGIN_SCRIPTS, log, KST, TIMEOUT_SECONDS, TITLE_MOST, NOTE_MOST, PLACE_MOST, REF_LENGTH, APP_URL, DEFAULT_APP_URL,
    LIST_PATH, EVENTS_PATH, SHARED_EVENTS_PATH, FORM_PATH, SAVE_PATH, DELETE_PATH, DETAIL_PATH, UNID, SEARCH_PATH, FT_SEARCH_PATH,
    SEARCH_KEYS, FT_SEARCH_KEYS, HOLIDAY_RESULT, SAVE_PREV_PATH, MOVE_PATH, AMP_TOKEN, LANG, ALL_DAY_RULE, DELETE_FIXED,
    KIND_MINE, TYPE_DEFAULT, KINDS_SHARED, SHARED_DB, SHARED_HOST, CALLBACK, CHANGES_CALENDAR, FORM_NEEDS, FORM_VALUE, VISIBILITY,
    PRIVATE, CALLBACK_NEW, GUEST_FIELDS, STAMP_FORM, STAMP_ROW, RESPONSE_PENDING, MEETING, TRUE_WORDS, ADDED, ALREADY, UNSURE,
    CLASHED, DELETED, GONE, CHANGED, EDITED, KEEP_INVITE, KEEP_MEETING, KEEP_REPEAT, KEEP_LOCKED, KEEP_ALL_DAY, KEEP_GUESTS,
    KEEP_SHARED, CalendarError, CalendarConfigError, SessionMissing, SessionExpired, ChangeRefused, FormChanged, kst, kst_day,
    _aware, _stamp, Book, Event, Want, whole_days, Seen, Added, Removed, event_key, event_ref, event_ident, event_mark, _clean,
    clean_title, clean_note, same_event, Person, Detail, Change, Edited, clock_span, KEEP_NO_DOC, LOGGER,
)
from agenda_rows import (  # noqa: F401
    _person, _jsonp, _DOC_FIELD, _DUMP_ROW, _plain, _people, parse_detail, _truthy, _at, _edits, _invited, parse_row, _Form,
    parse_rows,
)
from agenda_reader import (  # noqa: F401
    Reader, read_each, labelled, distinct_events,
)
from agenda_changes import (  # noqa: F401
    _span, _side_events, _span_of, register, locate, _agent, edit, delete, row_refusal, doc_refusal, new_times, values_unfit,
    new_title, UNFIT_BACKWARDS, UNFIT_NO_TITLE, already_in,
)
from agenda_shapes import ep_command, ep_session  # noqa: F401,E402 — 형제 스킬 ep-login 의 모듈(바탕이 싣는다)
