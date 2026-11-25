"""메일 손이 다른 스킬에 내주는 이름의 한 자리 — 이 폴더의 파일 → 다른 스킬이 그 파일에서 실어 쓰는 이름.

다른 스킬은 이 폴더의 코드에서 여기 적힌 이름만 싣는다 — 파일을 통째로 실어 그 안의 다른 하나를 꺼내 쓰지 않는다. 이름을 더하거나
빼거나 꼴(받는 것 · 내는 것)을 바꾸면 그 이름을 싣는 스킬을 같은 판에 고친다. 명령(``mail.py`` 의 하위 명령과 그 답)은 이름이 아니라
명령으로 내준다 — 그 꼴은 ``mail.py --help`` 가 든다. 스킬이 아닌 앱이 이 폴더를 싣는 꼴은 ``README.md`` 「앱에서 쓰기」 가 든다.

``Mailbox.<메서드>`` 는 열린 메일함 손(``mail_open.open_mailbox`` 가 낸 ``Opened`` 의 ``box``)에서 부르는 메서드다. ``Opened`` 의 칸
(``url`` · ``box``)도 약속이다. 내준 함수는 인자 묶음이 아니라 값을 받는다 — 칸 이름으로 맺은 약속은 기본값 탓에 어긋나도 조용하다. ``OrgChart`` · ``Dept`` ·
``DirectoryPerson`` 은 내준 함수(``load_org`` · ``cached_org`` · ``address_people`` · ``Mailbox.find_people`` …)가 내는 답의 꼴이라 그 칸과
메서드가 약속이다 — ``find_mail`` 이 내는 목록 줄(``inbox.Entry``)과 ``Mailbox.sent_people`` · ``received_together`` 가 내는 받는 사람
줄(``inbox.Recipient`` · ``mail_recipients.Together``)도 같다. 이 파일은 표만 든다 — 아무 코드도 싣지 않고 아무 명령 · 검사도 이 파일을 싣지 않는다.
"""

HANDED_OUT = {
    "mail_stop.py": ("Stop", "from_ep"),
    "mail_kept.py": ("DEFAULT_COMPANY", "cache_dir", "cached_org", "company_of", "load_org", "tree_newer"),
    "mail_open.py": ("MAILFILE_NUMBER", "given_url", "open_mailbox", "stops_from_mail"),
    "mail_find.py": ("DEFAULT_SCAN", "DRAFTS", "NotFound", "SENT", "find_mail", "unid_shape"),
    "mail_recipients.py": ("BCC_UNKNOWN", "field_of", "person_word", "received_together", "together_why"),
    "mail_people.py": ("DEPT_WORD", "DRAFT_AS_IS", "FIELD_WORDS", "GROUP_KIND_WORDS", "SHOWN", "address_people", "can_receive", "chart_book",
                       "group_lists", "kept_book", "one_group", "person_line", "split_kind"),
    "inbox.py": ("ChangeRefused", "DEPT_TYPE", "Dept", "DirectoryPerson", "ECM_ATTACHMENT", "EMAIL_TYPE", "MailboxConfigError",
                 "MailboxError", "ORG_TREE_TYPE", "ORG_WORKERS", "OrgChart", "SessionExpired", "directory_query", "ecm_note_key", "is_notes_name",
                 "level_at_least", "notes_key", "squash",
                 "Mailbox.directory_answer", "Mailbox.find_exact", "Mailbox.find_people", "Mailbox.group_members", "Mailbox.list",
                 "Mailbox.list_sent", "Mailbox.org_children", "Mailbox.org_groups", "Mailbox.sent_people"),
    "visible.py": ("TABLE_SEP", "body", "invisible"),
    "attachments.py": ("UNSAFE_NAME", "file_names", "keep"),
    "body_images.py": ("MAX_IMAGES", "Refused", "save"),
    "mailer.py": ("MailConfigError", "MailError", "MailRefused", "send"),
    "draft_send.js": ("rebody",),
}
