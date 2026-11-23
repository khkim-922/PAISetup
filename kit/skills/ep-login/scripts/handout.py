"""로그인 스킬이 다른 스킬에 내주는 이름의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰거나 읽는 이름.

다른 스킬은 이 폴더의 코드 · 값 파일에서 여기 적힌 이름만 싣고 읽는다 — 파일을 통째로 실어 그 안의 다른 하나를 꺼내 쓰지 않는다.
이름을 더하거나 빼거나 꼴(받는 것 · 내는 것)을 바꾸면 그 이름을 싣는 스킬을 같은 판에 고친다. 명령(입구 ``ep_login.js`` 와 그 껍데기
``login.sh`` · 받는 손 ``edge_session.js``)은 이름이 아니라 명령으로 내준다 — 부르는 꼴 · 종료 값 · 끝 줄은 그 파일의 머리말이 든다.
값 파일 ``places.json`` 의 열쇠는 그 파일을 곁에서 바로 읽는 스킬에 내주는 이름이다 — 파이썬 손은 ``ep_session`` 이 낸 이름으로 받는다.

``Person.label`` 은 ``ep_command.people_of`` · ``distinct`` 가 낸 사람에서 부르는 메서드다. ``Person`` 의 칸(사람 파일의 칸 그대로와
``where``), ``run_hand`` 가 내는 ``Ran`` 의 칸(``code`` · ``answer`` · ``said``), ``NoSession.got`` 이 드는 ``Attached`` 의 칸(``code`` ·
``said``), ``Redirected.location`` · ``Stop`` 의 ``code`` · ``kind`` 는 내준 이름이 내는 답의 꼴이라 그 칸이 약속이다 — 다른 스킬이 지어
넘기는 ``Start`` · ``Change`` · ``NotYet`` 의 칸도 같다. 이 파일은 표만 든다 — 아무 코드도 싣지 않고 아무 명령 · 검사도 이 파일을 싣지 않는다.
"""

HANDED_OUT = {
    "ep_command.py": ("Change", "DATE_FORM", "DAY_HELP", "DAY_SECONDS", "EXIT_ARGS", "EXIT_CLASSIFIED", "EXIT_DEFAULT_APP", "EXIT_OK",
                      "EXIT_SESSION", "EXIT_STALE", "EXIT_TOOL", "EXIT_URL", "NEXT_EP_LOGIN", "NotYet", "OUT_BYTES", "PEOPLE_FLAG",
                      "PEOPLE_FORMAT", "PEOPLE_HELP", "PEOPLE_KEYS", "SEOUL", "STAMP_FORM", "STAMP_HELP", "Start", "Stop", "WEEKDAYS", "add_people_file", "change_lines",
                      "date_of", "day_of", "distinct", "exit_legend", "fingerprint", "finish", "fit_text", "gaps_of", "given", "keep", "kept",
                      "load", "no_session", "not_yet_lines", "notes_key", "people_of", "pick_start", "refuse_foreign", "refuse_missing",
                      "refuse_not_yet", "size", "stamp", "stamp_of", "text_file", "today_word", "weeks_word",
                      "Person.label"),
    "ep_session.py": ("DEFAULT_FILE", "DOMINO_SERVER", "ECM_HANDOFF", "ECM_MAIN_PAGE", "ECM_URL", "NOT_LOGGED_IN", "NO_EDGE", "NoNode",
                      "NoSession", "OK", "ORDINARY_MISSING", "ORDINARY_STOOD", "OUT_BYTES", "Redirected", "SessionFileError", "TimedOut",
                      "load_jar", "opener", "ordinary_login", "run_hand", "session_first", "squash", "sso_form"),
    "edge_cdp.js": ("edgeLine", "framesOf", "sleep", "waitFor"),
    "places.json": ("session_file",),
}
