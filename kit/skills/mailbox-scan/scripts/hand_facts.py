"""메일함 스캔이 기대는 형제 스킬의 사실 — 회사 메일 손의 자리 · 종료 값 · 시한, 로그인이 사는 스킬,
사내 세션의 답 낱말, 세션이 끊겼을 때 사람에게 이를 다음 걸음.

이 파일의 원본은 스킬 mailbox-scan 의 `scripts/hand_facts.py` 다 — 같은 몸이 필요한 위 스킬은 이 파일을 바이트째 베껴 들고(스킬끼리 코드를
싣지 않는다), 원본 스킬은 누가 베끼는지 모른다. 원본만 고치고 베낀다. 읽는 쪽은 제 값 파일이 다시 내보낸
이름으로 읽는다.
"""

HAND_SKILL = "company-mail"              # 회사 메일 손이 사는 스킬 — 명령으로만 부른다(손의 코드를 싣지 않는다)
HAND_SCRIPT = ("scripts", "mail.py")
HAND_EXIT_OK, HAND_EXIT_FAIL, HAND_EXIT_CONFIG, HAND_EXIT_SESSION = 0, 1, 2, 3   # 손의 종료 값(그 손 mail.py 머리말 「무엇을 내나」)
HAND_TIMEOUT_S = 240     # 손 한 번의 시한 — 손 안의 세션 받기 시한(스킬 ep-login 의 `ep_session.py` `TIMEOUT_SECONDS`)보다 길어야 손이 제 판을 끝낸다
SESSION_SKILL = "ep-login"               # 로그인 입구 · 세션 파일의 자리가 사는 스킬 — 회사 메일 손과 같은 스킬 뿌리에 선다
# 사내 세션의 답 — 살았다 · 없다. 스캔의 `status --json` 이 마지막 판의 세션 답으로 이 낱말을 낸다 — 그 답을 읽는 프로그램이 이 낱말로 가른다
SESSION_LIVE, SESSION_LOST = "live", "lost"
NEXT_LOGIN = "대화에서 스킬 ep-login 으로 EP 로그인을"      # 세션이 끊겼을 때의 다음 걸음 — 뒤에 「한다 · 하시면 … · 하신 뒤 …」가 붙는다
