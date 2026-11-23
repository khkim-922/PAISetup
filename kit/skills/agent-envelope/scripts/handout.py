"""일 맡기는 스킬이 다른 스킬에 내주는 것의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰는 이름, 그리고 다른 스킬의
본문이 모델에게 읽으라고 가리키는 글.

다른 스킬은 이 스킬의 코드에서 여기 적힌 이름만 싣고, 이 스킬의 글은 ``GUIDES`` 에 적힌 것만 가리킨다 — 파일을 통째로 실어 그 안의 다른
하나를 꺼내 쓰지 않는다. 이름을 더하거나 빼거나 꼴(받는 것 · 내는 것)을 바꾸면, 또는 안내 글을 옮기거나 그 절을 바꾸면 그것을 쓰는
스킬을 같은 판에 고친다. ``HANDED_OUT`` 의 자리는 이 폴더(``scripts/``)이고 ``GUIDES`` 의 자리는 스킬 뿌리다. 이 파일은 표만 든다 — 아무
코드도 싣지 않고 아무 명령 · 검사도 이 파일을 싣지 않는다.
"""

HANDED_OUT = {
    "runner_common.py": ("CLAUDE_DROP_ENV", "CLAUDE_MODEL_RE", "CREATE_NO_WINDOW", "DEFAULT_TIMEOUT_SEC", "POLL_SEC", "PROMPT_ENCODINGS",
                         "STDERR_TAIL_CHARS", "base_parser", "claude_head", "claude_quota", "config_dir", "exit_table", "footer_line",
                         "kill_tree", "loopback_proxy", "main", "npm_head", "read_prompt", "remove", "watch", "wrap_up", "write",
                         "write_answer"),
}

GUIDES = (
    "app-lanes.md",   # 회사 일의 긴 읽기를 하위 에이전트에 맡기는 법
    "models.conf",    # 맡기기 모델 표 — 자리 · 도구 · 무게마다의 모델
)
